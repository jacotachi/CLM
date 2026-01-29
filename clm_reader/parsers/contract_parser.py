"""Parser pour l'extraction des données des contrats."""

import re
from decimal import Decimal
from typing import Optional, List, Tuple

from ..models.contract import Contract
from ..extractors.document_extractor import DocumentExtractor
from ..utils.text_utils import (
    clean_text,
    extract_amount,
    extract_date,
    normalize_company_name,
    extract_siren_siret,
)


class ContractParser:
    """
    Parser pour extraire les informations structurées des contrats.

    Cette classe analyse le texte d'un contrat et extrait les informations
    clés comme les parties, les montants, les dates, etc.
    """

    # Mots-clés pour identifier les sections
    KEYWORDS = {
        'parties': [
            'entre les soussignés', 'entre', 'parties', 'd\'une part', 'd\'autre part',
            'ci-après dénommé', 'le client', 'le prestataire', 'le fournisseur',
            'la société', 'représenté par', 'dont le siège'
        ],
        'objet': [
            'objet', 'objet du contrat', 'article 1', 'préambule', 'a pour objet',
            'le présent contrat a pour objet', 'concerne'
        ],
        'prix': [
            'prix', 'montant', 'rémunération', 'honoraires', 'tarif', 'coût',
            'hors taxes', 'ht', 'ttc', 'euros', '€', 'facturation'
        ],
        'duree': [
            'durée', 'engagement', 'période', 'à compter du', 'jusqu\'au',
            'pour une durée de', 'renouvelable', 'tacite reconduction',
            'résiliation', 'préavis'
        ],
        'signataire': [
            'fait à', 'signature', 'signé', 'le soussigné', 'représentant',
            'mandataire', 'gérant', 'directeur', 'président'
        ]
    }

    def __init__(self, use_ocr: bool = False):
        """
        Initialise le parser.

        Args:
            use_ocr: Utiliser l'OCR pour les PDF scannés
        """
        self.extractor = DocumentExtractor(use_ocr=use_ocr)

    def parse(self, file_path: str) -> Contract:
        """
        Parse un fichier de contrat et extrait les informations.

        Args:
            file_path: Chemin vers le fichier de contrat

        Returns:
            Objet Contract avec les informations extraites
        """
        # Extraire le texte
        text = self.extractor.extract(file_path)
        text_clean = clean_text(text)

        # Extraire les différentes informations
        societe_emettrice, societe_receptrice = self._extract_parties(text_clean)
        designation = self._extract_designation(text_clean)
        objet = self._extract_objet(text_clean)
        signataire = self._extract_signataire(text_clean)
        prix_ht = self._extract_prix(text_clean)
        quantite = self._extract_quantite(text_clean)
        engagement = self._extract_engagement(text_clean)
        date_signature, date_debut, date_fin = self._extract_dates(text_clean)

        # Calculer le score de confiance
        confiance = self._calculate_confidence(
            societe_emettrice, societe_receptrice, designation, objet,
            signataire, prix_ht, engagement
        )

        return Contract(
            societe_emettrice=societe_emettrice,
            societe_receptrice=societe_receptrice,
            designation=designation,
            objet=objet,
            signataire=signataire,
            prix_ht=prix_ht,
            quantite=quantite,
            engagement=engagement,
            date_signature=date_signature,
            date_debut=date_debut,
            date_fin=date_fin,
            fichier_source=file_path,
            confiance=confiance,
        )

    def parse_text(self, text: str, source_name: str = "texte") -> Contract:
        """
        Parse du texte brut de contrat.

        Args:
            text: Texte du contrat
            source_name: Nom de la source

        Returns:
            Objet Contract avec les informations extraites
        """
        text_clean = clean_text(text)

        societe_emettrice, societe_receptrice = self._extract_parties(text_clean)
        designation = self._extract_designation(text_clean)
        objet = self._extract_objet(text_clean)
        signataire = self._extract_signataire(text_clean)
        prix_ht = self._extract_prix(text_clean)
        quantite = self._extract_quantite(text_clean)
        engagement = self._extract_engagement(text_clean)
        date_signature, date_debut, date_fin = self._extract_dates(text_clean)

        confiance = self._calculate_confidence(
            societe_emettrice, societe_receptrice, designation, objet,
            signataire, prix_ht, engagement
        )

        return Contract(
            societe_emettrice=societe_emettrice,
            societe_receptrice=societe_receptrice,
            designation=designation,
            objet=objet,
            signataire=signataire,
            prix_ht=prix_ht,
            quantite=quantite,
            engagement=engagement,
            date_signature=date_signature,
            date_debut=date_debut,
            date_fin=date_fin,
            fichier_source=source_name,
            confiance=confiance,
        )

    def _extract_parties(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrait les parties du contrat (émetteur et récepteur).

        Args:
            text: Texte du contrat

        Returns:
            Tuple (société émettrice, société réceptrice)
        """
        emetteur = None
        recepteur = None

        # Patterns pour identifier les sociétés
        patterns_societe = [
            # Pattern "La société X, ..."
            r'(?:la\s+)?soci[ée]t[ée]\s+([A-Z][A-Za-zÀ-ÿ\s\-&\.]+?)(?:,|\s+(?:SAS|SARL|SA|SNC|EURL|SASU|SCI))',
            # Pattern avec forme juridique
            r'([A-Z][A-Za-zÀ-ÿ\s\-&\.]+?)\s*(?:SAS|SARL|SA|SNC|EURL|SASU|SCI)',
            # Pattern "dénommée X"
            r'(?:ci-après\s+)?d[ée]nomm[ée]e?\s+["\"]?([A-Z][A-Za-zÀ-ÿ\s\-&\.]+?)["\"]?(?:\s|,|$)',
        ]

        societes_trouvees = []

        for pattern in patterns_societe:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                nom = normalize_company_name(match)
                if nom and len(nom) > 2 and nom not in societes_trouvees:
                    societes_trouvees.append(nom)

        # Essayer de déterminer qui est l'émetteur et le récepteur
        text_lower = text.lower()

        if len(societes_trouvees) >= 2:
            # Chercher des indices contextuels
            for i, societe in enumerate(societes_trouvees[:2]):
                societe_lower = societe.lower()

                # Chercher le contexte autour du nom
                idx = text_lower.find(societe_lower)
                if idx != -1:
                    contexte = text_lower[max(0, idx-100):idx+100]

                    # Indices pour l'émetteur (prestataire, fournisseur)
                    if any(kw in contexte for kw in ['prestataire', 'fournisseur', 'd\'une part', 'émetteur']):
                        emetteur = societe
                    # Indices pour le récepteur (client, bénéficiaire)
                    elif any(kw in contexte for kw in ['client', 'bénéficiaire', 'd\'autre part', 'destinataire']):
                        recepteur = societe

            # Si pas d'indices contextuels, utiliser l'ordre d'apparition
            if not emetteur and len(societes_trouvees) >= 1:
                emetteur = societes_trouvees[0]
            if not recepteur and len(societes_trouvees) >= 2:
                recepteur = societes_trouvees[1]

        elif len(societes_trouvees) == 1:
            emetteur = societes_trouvees[0]

        return emetteur, recepteur

    def _extract_designation(self, text: str) -> Optional[str]:
        """
        Extrait la désignation/titre du contrat.

        Args:
            text: Texte du contrat

        Returns:
            Désignation du contrat
        """
        patterns = [
            # Titre en début de document
            r'^[\s\n]*([A-Z][A-Z\s\-\']+(?:CONTRAT|CONVENTION|ACCORD)[A-Z\s\-\']*)',
            # Pattern "CONTRAT DE ..."
            r'(CONTRAT\s+(?:DE\s+)?[A-Z\s\-\']+)',
            # Pattern "CONVENTION DE ..."
            r'(CONVENTION\s+(?:DE\s+)?[A-Z\s\-\']+)',
            # Pattern avec numéro de contrat
            r'(?:contrat|convention)\s*(?:n[°o]?\s*)?[:\s]*([A-Z0-9\-\/]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                designation = match.group(1).strip()
                # Nettoyer et limiter la longueur
                designation = ' '.join(designation.split())
                if len(designation) > 100:
                    designation = designation[:100] + '...'
                return designation

        return None

    def _extract_objet(self, text: str) -> Optional[str]:
        """
        Extrait l'objet du contrat.

        Args:
            text: Texte du contrat

        Returns:
            Objet du contrat
        """
        patterns = [
            # Section "Objet" explicite
            r'(?:objet|objet\s+du\s+contrat)\s*[:\-]?\s*(.+?)(?:\n\n|article\s+\d|\d+[\.°])',
            # "Le présent contrat a pour objet..."
            r'(?:le\s+présent\s+contrat|la\s+présente\s+convention)\s+a\s+pour\s+objet\s+(?:de\s+)?(.+?)(?:\.|$)',
            # "a pour objet..."
            r'a\s+pour\s+objet\s+(?:de\s+)?(.+?)(?:\.|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                objet = match.group(1).strip()
                # Nettoyer
                objet = re.sub(r'\s+', ' ', objet)
                # Limiter la longueur
                if len(objet) > 500:
                    objet = objet[:500] + '...'
                return objet

        return None

    def _extract_signataire(self, text: str) -> Optional[str]:
        """
        Extrait le nom du signataire.

        Args:
            text: Texte du contrat

        Returns:
            Nom du signataire
        """
        patterns = [
            # "représenté par M./Mme X"
            r'représent[ée]\s+par\s+(?:M\.?|Mme\.?|Monsieur|Madame)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)+)',
            # "signé par M./Mme X"
            r'sign[ée]\s+par\s+(?:M\.?|Mme\.?|Monsieur|Madame)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)+)',
            # "M./Mme X, en qualité de..."
            r'(?:M\.?|Mme\.?|Monsieur|Madame)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)+),?\s+(?:en\s+)?(?:sa\s+)?qualit[ée]\s+de',
            # Après "Fait à X, le DATE"
            r'fait\s+[àa]\s+[A-Za-zÀ-ÿ\-\s]+,?\s+le\s+[\d\/\-]+\s*\n+\s*([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                signataire = match.group(1).strip()
                return normalize_company_name(signataire)

        return None

    def _extract_prix(self, text: str) -> Optional[Decimal]:
        """
        Extrait le prix HT du contrat.

        Args:
            text: Texte du contrat

        Returns:
            Prix HT en Decimal
        """
        patterns = [
            # "montant HT : X €"
            r'(?:montant|prix|total|somme)\s*(?:hors\s*taxes?|HT)\s*[:\s]*(\d[\d\s\.,]*)\s*(?:€|EUR|euros?)',
            # "X € HT"
            r'(\d[\d\s\.,]*)\s*(?:€|EUR|euros?)\s*(?:hors\s*taxes?|HT)',
            # "HT : X"
            r'HT\s*[:\s]*(\d[\d\s\.,]*)',
            # Montant avec "hors taxes" proche
            r'(\d[\d\s\.,]*)\s*(?:€|EUR|euros?).*?hors\s*taxes?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = extract_amount(match.group(1))
                if amount and amount > 0:
                    return amount

        # Fallback: chercher le montant le plus important mentionné
        all_amounts = []
        for match in re.finditer(r'(\d[\d\s\.,]*)\s*(?:€|EUR|euros?)', text, re.IGNORECASE):
            amount = extract_amount(match.group(1))
            if amount and amount > 0:
                all_amounts.append(amount)

        if all_amounts:
            # Prendre le montant le plus élevé (souvent le total)
            return max(all_amounts)

        return None

    def _extract_quantite(self, text: str) -> Optional[str]:
        """
        Extrait la quantité du contrat.

        Args:
            text: Texte du contrat

        Returns:
            Quantité
        """
        patterns = [
            # "quantité : X"
            r'quantit[ée]\s*[:\s]*(\d+(?:\s*\w+)?)',
            # "nombre de X : Y"
            r'nombre\s+(?:de\s+)?(\w+)\s*[:\s]*(\d+)',
            # "X unités/jours/heures"
            r'(\d+)\s*(unit[ée]s?|jours?|heures?|mois|ans?|prestations?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return ' '.join(match.groups()).strip()

        return None

    def _extract_engagement(self, text: str) -> Optional[str]:
        """
        Extrait la durée d'engagement du contrat.

        Args:
            text: Texte du contrat

        Returns:
            Durée d'engagement
        """
        patterns = [
            # "durée de X mois/ans"
            r'(?:dur[ée]e|engagement)\s*(?:de|:)?\s*(\d+\s*(?:mois|ans?|ann[ée]es?|jours?|semaines?))',
            # "pour une durée de X"
            r'pour\s+une\s+dur[ée]e\s+(?:de\s+)?(\d+\s*(?:mois|ans?|ann[ée]es?|jours?|semaines?))',
            # "engagement de X"
            r'engagement\s+(?:de\s+)?(\d+\s*(?:mois|ans?|ann[ée]es?|jours?|semaines?))',
            # "renouvelable par tacite reconduction"
            r'(renouvelable\s+(?:par\s+)?tacite\s+reconduction)',
            # "durée indéterminée"
            r'(dur[ée]e\s+ind[ée]termin[ée]e)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_dates(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extrait les dates du contrat.

        Args:
            text: Texte du contrat

        Returns:
            Tuple (date_signature, date_debut, date_fin)
        """
        date_signature = None
        date_debut = None
        date_fin = None

        # Date de signature
        patterns_signature = [
            r'fait\s+[àa]\s+[A-Za-zÀ-ÿ\-\s]+,?\s+le\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            r'sign[ée]\s+le\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            r'en\s+date\s+du\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
        ]

        for pattern in patterns_signature:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_signature = extract_date(match.group(1))
                break

        # Date de début
        patterns_debut = [
            r'(?:à\s+compter|prend\s+effet)\s+(?:du|le)\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            r'date\s+(?:de\s+)?d[ée]but\s*[:\s]*([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            r'(?:débute?|commence)\s+le\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
        ]

        for pattern in patterns_debut:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_debut = extract_date(match.group(1))
                break

        # Date de fin
        patterns_fin = [
            r'(?:jusqu\'?au?|prend\s+fin\s+le)\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            r'date\s+(?:de\s+)?fin\s*[:\s]*([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
            r'(?:expire?|se\s+termine)\s+le\s+([\d\/\-]+(?:\s+\w+\s+\d{4})?)',
        ]

        for pattern in patterns_fin:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_fin = extract_date(match.group(1))
                break

        return date_signature, date_debut, date_fin

    def _calculate_confidence(
        self,
        societe_emettrice: Optional[str],
        societe_receptrice: Optional[str],
        designation: Optional[str],
        objet: Optional[str],
        signataire: Optional[str],
        prix_ht: Optional[Decimal],
        engagement: Optional[str]
    ) -> int:
        """
        Calcule un score de confiance pour l'extraction.

        Args:
            Les différents champs extraits

        Returns:
            Score de confiance entre 0 et 100
        """
        score = 0
        max_score = 7  # Nombre de champs vérifiés

        if societe_emettrice:
            score += 1
        if societe_receptrice:
            score += 1
        if designation:
            score += 1
        if objet:
            score += 1
        if signataire:
            score += 1
        if prix_ht is not None:
            score += 1
        if engagement:
            score += 1

        return int((score / max_score) * 100)
