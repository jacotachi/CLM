"""Parser pour l'extraction des données des factures."""

import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Tuple, List

from ..models.invoice import Invoice
from ..extractors.document_extractor import DocumentExtractor
from ..utils.text_utils import (
    clean_text,
    extract_amount,
    extract_date,
    normalize_company_name,
    extract_siren_siret,
    extract_tva_number,
)


class InvoiceParser:
    """
    Parser pour extraire les informations structurées des factures.

    Cette classe analyse le texte d'une facture et extrait les informations
    clés comme les montants, les dates, les parties, etc.
    """

    # Mots-clés pour identifier les sections
    KEYWORDS = {
        'emetteur': [
            'de:', 'émetteur', 'fournisseur', 'vendeur', 'prestataire',
            'notre société', 'notre entreprise'
        ],
        'destinataire': [
            'à:', 'destinataire', 'client', 'facturé à', 'adressé à',
            'acheteur', 'bénéficiaire'
        ],
        'montants': [
            'total', 'montant', 'sous-total', 'net à payer', 'ht', 'ttc',
            'tva', 'taxes', 'remise', 'escompte'
        ],
        'dates': [
            'date', 'facture du', 'émise le', 'date d\'émission',
            'échéance', 'date limite', 'paiement avant le', 'à payer avant'
        ],
        'prestation': [
            'désignation', 'description', 'libellé', 'prestation',
            'service', 'produit', 'article', 'référence'
        ]
    }

    def __init__(self, use_ocr: bool = False):
        """
        Initialise le parser.

        Args:
            use_ocr: Utiliser l'OCR pour les PDF scannés
        """
        self.extractor = DocumentExtractor(use_ocr=use_ocr)

    def parse(self, file_path: str) -> Invoice:
        """
        Parse un fichier de facture et extrait les informations.

        Args:
            file_path: Chemin vers le fichier de facture

        Returns:
            Objet Invoice avec les informations extraites
        """
        # Extraire le texte
        text = self.extractor.extract(file_path)
        text_clean = clean_text(text)

        # Extraire les différentes informations
        societe_emettrice = self._extract_emetteur(text_clean)
        societe_destinatrice = self._extract_destinataire(text_clean)
        prix_ht, tva, prix_ttc = self._extract_montants(text_clean)
        quantite = self._extract_quantite(text_clean)
        date_facture = self._extract_date_facture(text_clean)
        date_paiement_max = self._extract_date_paiement(text_clean, date_facture)
        duree_prestation = self._extract_duree_prestation(text_clean)
        designation_prestation = self._extract_designation(text_clean)
        numero_facture = self._extract_numero_facture(text_clean)

        # Calculer le score de confiance
        confiance = self._calculate_confidence(
            societe_emettrice, societe_destinatrice, prix_ht,
            date_facture, designation_prestation, numero_facture
        )

        return Invoice(
            societe_emettrice=societe_emettrice,
            societe_destinatrice=societe_destinatrice,
            prix_ht=prix_ht,
            tva=tva,
            prix_ttc=prix_ttc,
            quantite=quantite,
            date_facture=date_facture,
            date_paiement_max=date_paiement_max,
            duree_prestation=duree_prestation,
            designation_prestation=designation_prestation,
            numero_facture=numero_facture,
            fichier_source=file_path,
            confiance=confiance,
        )

    def parse_text(self, text: str, source_name: str = "texte") -> Invoice:
        """
        Parse du texte brut de facture.

        Args:
            text: Texte de la facture
            source_name: Nom de la source

        Returns:
            Objet Invoice avec les informations extraites
        """
        text_clean = clean_text(text)

        societe_emettrice = self._extract_emetteur(text_clean)
        societe_destinatrice = self._extract_destinataire(text_clean)
        prix_ht, tva, prix_ttc = self._extract_montants(text_clean)
        quantite = self._extract_quantite(text_clean)
        date_facture = self._extract_date_facture(text_clean)
        date_paiement_max = self._extract_date_paiement(text_clean, date_facture)
        duree_prestation = self._extract_duree_prestation(text_clean)
        designation_prestation = self._extract_designation(text_clean)
        numero_facture = self._extract_numero_facture(text_clean)

        confiance = self._calculate_confidence(
            societe_emettrice, societe_destinatrice, prix_ht,
            date_facture, designation_prestation, numero_facture
        )

        return Invoice(
            societe_emettrice=societe_emettrice,
            societe_destinatrice=societe_destinatrice,
            prix_ht=prix_ht,
            tva=tva,
            prix_ttc=prix_ttc,
            quantite=quantite,
            date_facture=date_facture,
            date_paiement_max=date_paiement_max,
            duree_prestation=duree_prestation,
            designation_prestation=designation_prestation,
            numero_facture=numero_facture,
            fichier_source=source_name,
            confiance=confiance,
        )

    def _extract_emetteur(self, text: str) -> Optional[str]:
        """
        Extrait la société émettrice de la facture.

        Args:
            text: Texte de la facture

        Returns:
            Nom de la société émettrice
        """
        # Les factures commencent souvent par les coordonnées de l'émetteur
        # Chercher en haut du document

        # Prendre les premières lignes
        lines = text.split('\n')[:20]
        header_text = '\n'.join(lines)

        # Patterns pour identifier l'émetteur
        patterns = [
            # Nom de société avec forme juridique
            r'^([A-Z][A-Za-zÀ-ÿ\s\-&\.]+?)\s*(?:SAS|SARL|SA|SNC|EURL|SASU|SCI|SCOP)',
            # "La société X"
            r'(?:la\s+)?soci[ée]t[ée]\s+([A-Z][A-Za-zÀ-ÿ\s\-&\.]+?)(?:\s|,|$)',
            # Première ligne en majuscules (souvent le nom)
            r'^([A-Z][A-Z\s\-&\.]{3,})$',
        ]

        for pattern in patterns:
            match = re.search(pattern, header_text, re.MULTILINE | re.IGNORECASE)
            if match:
                nom = match.group(1).strip()
                if len(nom) > 2:
                    return normalize_company_name(nom)

        # Fallback: chercher près du SIRET/TVA
        siret_match = re.search(r'SIRET\s*[:\s]*\d+.*\n(.+)', text, re.IGNORECASE)
        if siret_match:
            # Ligne précédente pourrait être le nom
            idx = text.find('SIRET')
            if idx > 0:
                before_siret = text[:idx].split('\n')
                for line in reversed(before_siret[-5:]):
                    line = line.strip()
                    if line and not re.match(r'^[\d\s\-]+$', line):
                        return normalize_company_name(line)

        return None

    def _extract_destinataire(self, text: str) -> Optional[str]:
        """
        Extrait la société destinataire de la facture.

        Args:
            text: Texte de la facture

        Returns:
            Nom de la société destinataire
        """
        patterns = [
            # "Client : X"
            r'client\s*[:\s]+([A-Za-zÀ-ÿ\s\-&\.]+?)(?:\n|,|$)',
            # "Facturé à : X"
            r'factur[ée]\s+[àa]\s*[:\s]*([A-Za-zÀ-ÿ\s\-&\.]+?)(?:\n|,|$)',
            # "Destinataire : X"
            r'destinataire\s*[:\s]+([A-Za-zÀ-ÿ\s\-&\.]+?)(?:\n|,|$)',
            # "À l'attention de X" ou "À : X"
            r'[àa]\s+(?:l\'attention\s+de\s+)?[:\s]*([A-Za-zÀ-ÿ\s\-&\.]+?)(?:\n|,|$)',
            # Bloc après "Adresse de facturation"
            r'adresse\s+de\s+facturation\s*[:\s]*\n\s*([A-Za-zÀ-ÿ\s\-&\.]+?)(?:\n|,|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nom = match.group(1).strip()
                # Filtrer les faux positifs
                if len(nom) > 2 and not re.match(r'^[\d\s]+$', nom):
                    return normalize_company_name(nom)

        return None

    def _extract_montants(self, text: str) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
        """
        Extrait les montants HT, TVA et TTC.

        Args:
            text: Texte de la facture

        Returns:
            Tuple (prix_ht, tva, prix_ttc)
        """
        prix_ht = None
        tva = None
        prix_ttc = None

        # Patterns pour le montant HT
        patterns_ht = [
            r'(?:total|montant|sous-total)\s*(?:hors\s*taxes?|HT)\s*[:\s]*(\d[\d\s\.,]*)\s*(?:€|EUR)?',
            r'(\d[\d\s\.,]*)\s*(?:€|EUR)?\s*(?:hors\s*taxes?|HT)',
            r'HT\s*[:\s]*(\d[\d\s\.,]*)',
            r'net\s*HT\s*[:\s]*(\d[\d\s\.,]*)',
        ]

        for pattern in patterns_ht:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                prix_ht = extract_amount(match.group(1))
                if prix_ht and prix_ht > 0:
                    break

        # Patterns pour la TVA
        patterns_tva = [
            r'(?:montant\s+)?TVA\s*(?:\d+\s*%)?\s*[:\s]*(\d[\d\s\.,]*)\s*(?:€|EUR)?',
            r'TVA\s+(\d+)\s*%\s*[:\s]*(\d[\d\s\.,]*)',
            r'taxe[s]?\s*[:\s]*(\d[\d\s\.,]*)',
        ]

        for pattern in patterns_tva:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Prendre le dernier groupe (montant)
                tva = extract_amount(match.group(match.lastindex))
                if tva and tva > 0:
                    break

        # Patterns pour le montant TTC
        patterns_ttc = [
            r'(?:total|montant|net\s+[àa]\s+payer)\s*(?:toutes\s*taxes\s*comprises?|TTC)\s*[:\s]*(\d[\d\s\.,]*)\s*(?:€|EUR)?',
            r'(\d[\d\s\.,]*)\s*(?:€|EUR)?\s*(?:toutes\s*taxes\s*comprises?|TTC)',
            r'TTC\s*[:\s]*(\d[\d\s\.,]*)',
            r'net\s+[àa]\s+payer\s*[:\s]*(\d[\d\s\.,]*)',
            r'total\s+[àa]\s+payer\s*[:\s]*(\d[\d\s\.,]*)',
        ]

        for pattern in patterns_ttc:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                prix_ttc = extract_amount(match.group(1))
                if prix_ttc and prix_ttc > 0:
                    break

        # Si on a HT et TVA mais pas TTC, calculer
        if prix_ht and tva and not prix_ttc:
            prix_ttc = prix_ht + tva

        # Si on a TTC et TVA mais pas HT, calculer
        if prix_ttc and tva and not prix_ht:
            prix_ht = prix_ttc - tva

        return prix_ht, tva, prix_ttc

    def _extract_quantite(self, text: str) -> Optional[str]:
        """
        Extrait la quantité facturée.

        Args:
            text: Texte de la facture

        Returns:
            Quantité
        """
        patterns = [
            # "Quantité : X"
            r'quantit[ée]\s*[:\s]*(\d+(?:\s*\w+)?)',
            # "Qté : X"
            r'qt[ée]\s*[:\s]*(\d+)',
            # Dans un tableau: "X unités"
            r'(\d+)\s*(unit[ée]s?|pi[èe]ces?|articles?)',
            # Colonne quantité
            r'\bqt[ée]?\b.*?(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.lastindex == 1 else ' '.join(g for g in match.groups() if g).strip()

        return None

    def _extract_date_facture(self, text: str) -> Optional[date]:
        """
        Extrait la date de la facture.

        Args:
            text: Texte de la facture

        Returns:
            Date de la facture
        """
        patterns = [
            # "Date de facture : X"
            r'date\s+(?:de\s+)?(?:la\s+)?facture\s*[:\s]*([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            # "Facture du X"
            r'facture\s+du\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            # "Émise le X"
            r'[ée]mise?\s+le\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            # "Date d'émission : X"
            r'date\s+d\'[ée]mission\s*[:\s]*([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            # "Date : X" en début de facture
            r'^date\s*[:\s]*([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            # Format "Le JJ/MM/AAAA"
            r'\ble\s+([\d\/\-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                date_result = extract_date(match.group(1))
                if date_result:
                    return date_result

        # Fallback: chercher la première date dans le document
        date_pattern = r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})'
        match = re.search(date_pattern, text)
        if match:
            return extract_date(match.group(1))

        return None

    def _extract_date_paiement(self, text: str, date_facture: Optional[date] = None) -> Optional[date]:
        """
        Extrait la date limite de paiement.

        Args:
            text: Texte de la facture
            date_facture: Date de la facture (pour calcul si délai)

        Returns:
            Date limite de paiement
        """
        patterns = [
            # "Date limite de paiement : X"
            r'date\s+limite\s+(?:de\s+)?paiement\s*[:\s]*([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            # "Échéance : X"
            r'[ée]ch[ée]ance\s*[:\s]*([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            # "À payer avant le X"
            r'[àa]\s+payer\s+(?:avant\s+)?le\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            # "Paiement avant le X"
            r'paiement\s+(?:avant\s+)?le\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            # "Date d'échéance : X"
            r'date\s+d\'[ée]ch[ée]ance\s*[:\s]*([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_result = extract_date(match.group(1))
                if date_result:
                    return date_result

        # Chercher un délai de paiement (30 jours, 60 jours, etc.)
        delai_patterns = [
            r'(?:paiement|règlement)\s+[àa]\s+(\d+)\s+jours?',
            r'(\d+)\s+jours?\s+(?:fin\s+de\s+mois|net)',
            r'd[ée]lai\s+(?:de\s+)?paiement\s*[:\s]*(\d+)\s+jours?',
        ]

        for pattern in delai_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                delai_jours = int(match.group(1))
                if date_facture:
                    return date_facture + timedelta(days=delai_jours)
                else:
                    # Utiliser aujourd'hui si pas de date facture
                    return date.today() + timedelta(days=delai_jours)

        return None

    def _extract_duree_prestation(self, text: str) -> Optional[str]:
        """
        Extrait la durée/période de la prestation.

        Args:
            text: Texte de la facture

        Returns:
            Durée de la prestation
        """
        patterns = [
            # "Période : janvier 2024"
            r'p[ée]riode\s*[:\s]*([A-Za-zÀ-ÿ]+\s+\d{4})',
            # "Période du X au Y"
            r'p[ée]riode\s+du\s+([\d\/\-]+)\s+au\s+([\d\/\-]+)',
            # "Du X au Y"
            r'\bdu\s+([\d\/\-]+\s*(?:\w+\s+\d{4})?)\s+au\s+([\d\/\-]+\s*(?:\w+\s+\d{4})?)',
            # "Mois de janvier 2024"
            r'mois\s+(?:de\s+)?([A-Za-zÀ-ÿ]+\s+\d{4})',
            # "Pour le mois de X"
            r'pour\s+(?:le\s+)?mois\s+(?:de\s+)?([A-Za-zÀ-ÿ]+(?:\s+\d{4})?)',
            # "Année 2024"
            r'ann[ée]e\s+(\d{4})',
            # "Trimestre X 2024"
            r'((?:\d(?:er)?|premier|deuxième|troisième|quatrième)\s+trimestre\s+\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.lastindex and match.lastindex > 1:
                    return f"du {match.group(1)} au {match.group(2)}"
                return match.group(1).strip()

        return None

    def _extract_designation(self, text: str) -> Optional[str]:
        """
        Extrait la désignation de la prestation.

        Args:
            text: Texte de la facture

        Returns:
            Désignation de la prestation
        """
        patterns = [
            # "Désignation : X"
            r'd[ée]signation\s*[:\s]+(.+?)(?:\n|$)',
            # "Description : X"
            r'description\s*[:\s]+(.+?)(?:\n|$)',
            # "Prestation : X"
            r'prestation\s*[:\s]+(.+?)(?:\n|$)',
            # "Libellé : X"
            r'libell[ée]\s*[:\s]+(.+?)(?:\n|$)',
            # "Objet : X"
            r'objet\s*[:\s]+(.+?)(?:\n|$)',
            # Après "désignation" dans un tableau
            r'd[ée]signation.*?\n\s*(.+?)(?:\d|\n\n)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                designation = match.group(1).strip()
                # Nettoyer
                designation = re.sub(r'\s+', ' ', designation)
                # Limiter la longueur
                if len(designation) > 200:
                    designation = designation[:200] + '...'
                if len(designation) > 3:
                    return designation

        return None

    def _extract_numero_facture(self, text: str) -> Optional[str]:
        """
        Extrait le numéro de facture.

        Args:
            text: Texte de la facture

        Returns:
            Numéro de facture
        """
        patterns = [
            # "Facture N° X" ou "Facture n° X"
            r'facture\s*n[°o]?\s*[:\s]*([A-Z0-9\-\/]+)',
            # "N° facture : X"
            r'n[°o]?\s*(?:de\s+)?facture\s*[:\s]*([A-Z0-9\-\/]+)',
            # "Réf. : X"
            r'r[ée]f(?:[ée]rence)?\.?\s*[:\s]*([A-Z0-9\-\/]+)',
            # "Invoice number: X"
            r'invoice\s*(?:number|no?\.?)\s*[:\s]*([A-Z0-9\-\/]+)',
            # Format FAC-2024-001
            r'\b(FAC[\-\/]?\d{4}[\-\/]?\d+)\b',
            # Format F2024001
            r'\b(F\d{7,})\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                numero = match.group(1).strip()
                if len(numero) >= 3:
                    return numero.upper()

        return None

    def _calculate_confidence(
        self,
        societe_emettrice: Optional[str],
        societe_destinatrice: Optional[str],
        prix_ht: Optional[Decimal],
        date_facture: Optional[date],
        designation_prestation: Optional[str],
        numero_facture: Optional[str]
    ) -> int:
        """
        Calcule un score de confiance pour l'extraction.

        Args:
            Les différents champs extraits

        Returns:
            Score de confiance entre 0 et 100
        """
        score = 0
        max_score = 6  # Nombre de champs vérifiés

        if societe_emettrice:
            score += 1
        if societe_destinatrice:
            score += 1
        if prix_ht is not None:
            score += 1
        if date_facture:
            score += 1
        if designation_prestation:
            score += 1
        if numero_facture:
            score += 1

        return int((score / max_score) * 100)
