"""Utilitaires pour le traitement et l'extraction de texte."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, List

from dateutil import parser as date_parser


def clean_text(text: str) -> str:
    """
    Nettoie le texte extrait d'un document.

    Args:
        text: Texte brut à nettoyer

    Returns:
        Texte nettoyé
    """
    if not text:
        return ""

    # Remplacer les retours à la ligne multiples
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Supprimer les espaces multiples
    text = re.sub(r' {2,}', ' ', text)

    # Supprimer les espaces en début et fin de ligne
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    return text.strip()


def extract_amount(text: str) -> Optional[Decimal]:
    """
    Extrait un montant monétaire d'une chaîne de texte.

    Supporte les formats:
    - 1234.56
    - 1234,56
    - 1 234,56
    - 1.234,56
    - 1,234.56

    Args:
        text: Texte contenant un montant

    Returns:
        Montant en Decimal ou None si non trouvé
    """
    if not text:
        return None

    # Patterns pour les montants
    patterns = [
        # Format européen avec espaces: 1 234,56 ou 1 234.56
        r'(\d{1,3}(?:\s\d{3})*[,\.]\d{2})',
        # Format avec points comme séparateurs de milliers: 1.234,56
        r'(\d{1,3}(?:\.\d{3})*,\d{2})',
        # Format avec virgules comme séparateurs de milliers: 1,234.56
        r'(\d{1,3}(?:,\d{3})*\.\d{2})',
        # Format simple: 1234.56 ou 1234,56
        r'(\d+[,\.]\d{2})',
        # Format entier
        r'(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            amount_str = match.group(1)

            # Nettoyer et normaliser
            # Supprimer les espaces
            amount_str = amount_str.replace(' ', '')

            # Déterminer le format
            if ',' in amount_str and '.' in amount_str:
                # Format mixte, déterminer lequel est le séparateur décimal
                if amount_str.rfind(',') > amount_str.rfind('.'):
                    # Virgule est le séparateur décimal (format européen)
                    amount_str = amount_str.replace('.', '').replace(',', '.')
                else:
                    # Point est le séparateur décimal (format US)
                    amount_str = amount_str.replace(',', '')
            elif ',' in amount_str:
                # Vérifier si c'est un séparateur de milliers ou décimal
                parts = amount_str.split(',')
                if len(parts[-1]) == 2:
                    # C'est un séparateur décimal
                    amount_str = amount_str.replace(',', '.')
                else:
                    # C'est un séparateur de milliers
                    amount_str = amount_str.replace(',', '')

            try:
                return Decimal(amount_str)
            except InvalidOperation:
                continue

    return None


def extract_date(text: str) -> Optional[date]:
    """
    Extrait une date d'une chaîne de texte.

    Supporte de nombreux formats de dates français et internationaux.

    Args:
        text: Texte contenant une date

    Returns:
        Date ou None si non trouvée
    """
    if not text:
        return None

    # Patterns de dates courants
    date_patterns = [
        # JJ/MM/AAAA ou JJ-MM-AAAA
        r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
        # JJ/MM/AA
        r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2})',
        # AAAA-MM-JJ (ISO)
        r'(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})',
        # JJ mois AAAA (français)
        r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
        # mois AAAA
        r'((?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
    ]

    # Mapping des mois français
    mois_fr = {
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
    }

    text_lower = text.lower()

    for pattern in date_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            date_str = match.group(1)

            # Essayer de parser avec dateutil
            try:
                # Remplacer les mois français
                for mois, num in mois_fr.items():
                    if mois in date_str:
                        date_str = date_str.replace(mois, str(num))
                        break

                parsed = date_parser.parse(date_str, dayfirst=True)
                return parsed.date()
            except (ValueError, TypeError):
                continue

    return None


def normalize_company_name(name: str) -> str:
    """
    Normalise un nom de société.

    Args:
        name: Nom de société brut

    Returns:
        Nom normalisé
    """
    if not name:
        return ""

    # Supprimer les espaces multiples
    name = re.sub(r'\s+', ' ', name)

    # Supprimer les caractères spéciaux en début/fin
    name = name.strip(' .,;:-')

    # Capitaliser correctement
    # Garder les acronymes en majuscules
    words = name.split()
    normalized_words = []

    for word in words:
        # Si le mot est tout en majuscules et court, c'est probablement un acronyme
        if word.isupper() and len(word) <= 5:
            normalized_words.append(word)
        else:
            normalized_words.append(word.capitalize())

    return ' '.join(normalized_words)


def extract_siren_siret(text: str) -> Optional[str]:
    """
    Extrait un numéro SIREN ou SIRET du texte.

    Args:
        text: Texte contenant potentiellement un SIREN/SIRET

    Returns:
        Numéro SIREN/SIRET ou None
    """
    if not text:
        return None

    # SIRET: 14 chiffres, SIREN: 9 chiffres
    patterns = [
        r'SIRET\s*[:\s]*(\d{3}\s*\d{3}\s*\d{3}\s*\d{5})',
        r'SIREN\s*[:\s]*(\d{3}\s*\d{3}\s*\d{3})',
        r'(\d{14})',  # SIRET sans espaces
        r'(\d{9})',   # SIREN sans espaces
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return re.sub(r'\s', '', match.group(1))

    return None


def extract_tva_number(text: str) -> Optional[str]:
    """
    Extrait un numéro de TVA intracommunautaire.

    Args:
        text: Texte contenant potentiellement un numéro de TVA

    Returns:
        Numéro de TVA ou None
    """
    if not text:
        return None

    # Format: FR XX XXX XXX XXX
    pattern = r'(?:TVA|N°\s*TVA)[^A-Z]*([A-Z]{2}\s*\d{2}\s*\d{3}\s*\d{3}\s*\d{3})'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return re.sub(r'\s', '', match.group(1)).upper()

    # Essayer un format plus simple
    pattern = r'([A-Z]{2}\d{11})'
    match = re.search(pattern, text)
    if match:
        return match.group(1)

    return None


def find_between_markers(text: str, start_marker: str, end_marker: str) -> Optional[str]:
    """
    Trouve le texte entre deux marqueurs.

    Args:
        text: Texte source
        start_marker: Marqueur de début
        end_marker: Marqueur de fin

    Returns:
        Texte entre les marqueurs ou None
    """
    if not text:
        return None

    pattern = f'{re.escape(start_marker)}(.+?){re.escape(end_marker)}'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(1).strip()

    return None


def extract_all_amounts(text: str) -> List[Decimal]:
    """
    Extrait tous les montants d'un texte.

    Args:
        text: Texte contenant des montants

    Returns:
        Liste des montants trouvés
    """
    amounts = []

    # Pattern global pour trouver tous les nombres qui ressemblent à des montants
    pattern = r'(\d{1,3}(?:[\s\.,]\d{3})*(?:[,\.]\d{2})?)\s*(?:€|EUR|euros?)?'

    for match in re.finditer(pattern, text, re.IGNORECASE):
        amount = extract_amount(match.group(1))
        if amount is not None and amount > 0:
            amounts.append(amount)

    return amounts
