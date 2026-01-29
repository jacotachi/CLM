"""Modèle de données pour les contrats."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class Contract(BaseModel):
    """
    Modèle représentant un contrat commercial.

    Attributes:
        societe_emettrice: Société qui émet/rédige le contrat
        societe_receptrice: Société qui reçoit/accepte le contrat
        designation: Désignation ou titre du contrat
        objet: Objet ou description détaillée du contrat
        signataire: Nom du signataire du contrat
        prix_ht: Prix hors taxes du contrat
        quantite: Quantité concernée par le contrat
        engagement: Durée ou nature de l'engagement contractuel
        date_signature: Date de signature du contrat
        date_debut: Date de début du contrat
        date_fin: Date de fin du contrat
        fichier_source: Chemin vers le fichier source
        confiance: Score de confiance de l'extraction (0-100)
    """

    # Parties du contrat
    societe_emettrice: Optional[str] = Field(
        default=None,
        description="Société qui émet/rédige le contrat"
    )
    societe_receptrice: Optional[str] = Field(
        default=None,
        description="Société qui reçoit/accepte le contrat"
    )

    # Identification du contrat
    designation: Optional[str] = Field(
        default=None,
        description="Désignation ou titre du contrat"
    )
    objet: Optional[str] = Field(
        default=None,
        description="Objet ou description détaillée du contrat"
    )

    # Signataire
    signataire: Optional[str] = Field(
        default=None,
        description="Nom du signataire du contrat"
    )

    # Conditions financières
    prix_ht: Optional[Decimal] = Field(
        default=None,
        description="Prix hors taxes du contrat"
    )
    quantite: Optional[str] = Field(
        default=None,
        description="Quantité concernée par le contrat"
    )

    # Engagement
    engagement: Optional[str] = Field(
        default=None,
        description="Durée ou nature de l'engagement contractuel"
    )

    # Dates
    date_signature: Optional[date] = Field(
        default=None,
        description="Date de signature du contrat"
    )
    date_debut: Optional[date] = Field(
        default=None,
        description="Date de début du contrat"
    )
    date_fin: Optional[date] = Field(
        default=None,
        description="Date de fin du contrat"
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
        """Convertit le contrat en dictionnaire."""
        return self.model_dump(exclude_none=True)

    def summary(self) -> str:
        """Retourne un résumé du contrat."""
        lines = ["=== CONTRAT ==="]

        if self.designation:
            lines.append(f"Désignation: {self.designation}")
        if self.societe_emettrice:
            lines.append(f"Émetteur: {self.societe_emettrice}")
        if self.societe_receptrice:
            lines.append(f"Destinataire: {self.societe_receptrice}")
        if self.objet:
            lines.append(f"Objet: {self.objet}")
        if self.signataire:
            lines.append(f"Signataire: {self.signataire}")
        if self.prix_ht is not None:
            lines.append(f"Prix HT: {self.prix_ht} EUR")
        if self.quantite:
            lines.append(f"Quantité: {self.quantite}")
        if self.engagement:
            lines.append(f"Engagement: {self.engagement}")
        if self.date_signature:
            lines.append(f"Date signature: {self.date_signature}")
        if self.date_debut:
            lines.append(f"Début: {self.date_debut}")
        if self.date_fin:
            lines.append(f"Fin: {self.date_fin}")

        lines.append(f"Confiance: {self.confiance}%")

        return "\n".join(lines)
