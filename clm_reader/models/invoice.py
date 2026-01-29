"""Modèle de données pour les factures."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class Invoice(BaseModel):
    """
    Modèle représentant une facture commerciale.

    Attributes:
        societe_emettrice: Société qui émet la facture
        societe_destinatrice: Société qui reçoit la facture
        prix_ht: Montant hors taxes de la facture
        tva: Montant de la TVA
        prix_ttc: Montant toutes taxes comprises
        quantite: Quantité facturée
        date_facture: Date d'émission de la facture
        date_paiement_max: Date limite de paiement
        duree_prestation: Durée pour laquelle on paie
        designation_prestation: Désignation de la prestation
        numero_facture: Numéro de la facture
        fichier_source: Chemin vers le fichier source
        confiance: Score de confiance de l'extraction (0-100)
    """

    # Parties de la facture
    societe_emettrice: Optional[str] = Field(
        default=None,
        description="Société qui émet la facture"
    )
    societe_destinatrice: Optional[str] = Field(
        default=None,
        description="Société qui reçoit la facture"
    )

    # Montants
    prix_ht: Optional[Decimal] = Field(
        default=None,
        description="Montant hors taxes de la facture"
    )
    tva: Optional[Decimal] = Field(
        default=None,
        description="Montant de la TVA"
    )
    prix_ttc: Optional[Decimal] = Field(
        default=None,
        description="Montant toutes taxes comprises"
    )

    # Quantité
    quantite: Optional[str] = Field(
        default=None,
        description="Quantité facturée"
    )

    # Dates
    date_facture: Optional[date] = Field(
        default=None,
        description="Date d'émission de la facture"
    )
    date_paiement_max: Optional[date] = Field(
        default=None,
        description="Date limite de paiement"
    )

    # Prestation
    duree_prestation: Optional[str] = Field(
        default=None,
        description="Durée pour laquelle on paie (ex: 'Janvier 2024', '1 mois')"
    )
    designation_prestation: Optional[str] = Field(
        default=None,
        description="Désignation de la prestation facturée"
    )

    # Identification
    numero_facture: Optional[str] = Field(
        default=None,
        description="Numéro de la facture"
    )

    # Métadonnées
    fichier_source: Optional[str] = Field(
        default=None,
        description="Chemin vers le fichier source"
    )
    confiance: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Score de confiance de l'extraction (0-100)"
    )

    class Config:
        """Configuration Pydantic."""
        json_encoders = {
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
        }

    def to_dict(self) -> dict:
        """Convertit la facture en dictionnaire."""
        return self.model_dump(exclude_none=True)

    def summary(self) -> str:
        """Retourne un résumé de la facture."""
        lines = ["=== FACTURE ==="]

        if self.numero_facture:
            lines.append(f"Numéro: {self.numero_facture}")
        if self.societe_emettrice:
            lines.append(f"Émetteur: {self.societe_emettrice}")
        if self.societe_destinatrice:
            lines.append(f"Destinataire: {self.societe_destinatrice}")
        if self.designation_prestation:
            lines.append(f"Prestation: {self.designation_prestation}")
        if self.prix_ht is not None:
            lines.append(f"Prix HT: {self.prix_ht} EUR")
        if self.tva is not None:
            lines.append(f"TVA: {self.tva} EUR")
        if self.prix_ttc is not None:
            lines.append(f"Prix TTC: {self.prix_ttc} EUR")
        if self.quantite:
            lines.append(f"Quantité: {self.quantite}")
        if self.date_facture:
            lines.append(f"Date facture: {self.date_facture}")
        if self.date_paiement_max:
            lines.append(f"Paiement max: {self.date_paiement_max}")
        if self.duree_prestation:
            lines.append(f"Période: {self.duree_prestation}")

        lines.append(f"Confiance: {self.confiance}%")

        return "\n".join(lines)

    def days_until_payment(self) -> Optional[int]:
        """Calcule le nombre de jours restants avant la date limite de paiement."""
        if self.date_paiement_max:
            delta = self.date_paiement_max - date.today()
            return delta.days
        return None

    def is_overdue(self) -> bool:
        """Vérifie si la facture est en retard de paiement."""
        days = self.days_until_payment()
        return days is not None and days < 0
