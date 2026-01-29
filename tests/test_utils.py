"""Tests pour les utilitaires de traitement de texte."""

from datetime import date
from decimal import Decimal

import pytest

from clm_reader.utils.text_utils import (
    clean_text,
    extract_amount,
    extract_date,
    normalize_company_name,
    extract_siren_siret,
    extract_tva_number,
    find_between_markers,
)


class TestCleanText:
    """Tests pour clean_text."""

    def test_clean_multiple_spaces(self):
        """Test nettoyage espaces multiples."""
        assert clean_text("Hello    world") == "Hello world"

    def test_clean_multiple_newlines(self):
        """Test nettoyage retours a la ligne multiples."""
        result = clean_text("Line1\n\n\n\n\nLine2")
        assert "\n\n\n" not in result

    def test_clean_empty_string(self):
        """Test avec chaine vide."""
        assert clean_text("") == ""
        assert clean_text(None) == ""


class TestExtractAmount:
    """Tests pour extract_amount."""

    def test_simple_amount(self):
        """Test montant simple."""
        assert extract_amount("1234.56") == Decimal("1234.56")
        assert extract_amount("1234,56") == Decimal("1234.56")

    def test_amount_with_spaces(self):
        """Test montant avec espaces."""
        assert extract_amount("1 234,56") == Decimal("1234.56")

    def test_european_format(self):
        """Test format europeen."""
        assert extract_amount("1.234,56") == Decimal("1234.56")

    def test_us_format(self):
        """Test format americain."""
        assert extract_amount("1,234.56") == Decimal("1234.56")

    def test_integer_amount(self):
        """Test montant entier."""
        assert extract_amount("1000") == Decimal("1000")

    def test_empty_string(self):
        """Test chaine vide."""
        assert extract_amount("") is None
        assert extract_amount(None) is None


class TestExtractDate:
    """Tests pour extract_date."""

    def test_french_format(self):
        """Test format francais JJ/MM/AAAA."""
        result = extract_date("15/01/2024")
        assert result == date(2024, 1, 15)

    def test_iso_format(self):
        """Test format ISO AAAA-MM-JJ."""
        result = extract_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_french_text_format(self):
        """Test format texte francais."""
        result = extract_date("15 janvier 2024")
        assert result == date(2024, 1, 15)

    def test_empty_string(self):
        """Test chaine vide."""
        assert extract_date("") is None
        assert extract_date(None) is None


class TestNormalizeCompanyName:
    """Tests pour normalize_company_name."""

    def test_simple_name(self):
        """Test nom simple."""
        assert normalize_company_name("acme corp") == "Acme Corp"

    def test_acronym_preservation(self):
        """Test preservation des acronymes."""
        assert normalize_company_name("IBM france") == "IBM France"
        assert normalize_company_name("SAS dupont") == "SAS Dupont"

    def test_cleanup_punctuation(self):
        """Test nettoyage ponctuation."""
        assert normalize_company_name("  Test Corp.  ") == "Test Corp"

    def test_empty_string(self):
        """Test chaine vide."""
        assert normalize_company_name("") == ""
        assert normalize_company_name(None) == ""


class TestExtractSirenSiret:
    """Tests pour extract_siren_siret."""

    def test_siret_with_label(self):
        """Test SIRET avec label."""
        text = "SIRET: 123 456 789 00012"
        result = extract_siren_siret(text)
        assert result == "12345678900012"

    def test_siren_with_label(self):
        """Test SIREN avec label."""
        text = "SIREN: 123 456 789"
        result = extract_siren_siret(text)
        assert result == "123456789"

    def test_siret_no_label(self):
        """Test SIRET sans label."""
        text = "Numero: 12345678900012"
        result = extract_siren_siret(text)
        assert result == "12345678900012"


class TestExtractTvaNumber:
    """Tests pour extract_tva_number."""

    def test_french_tva(self):
        """Test numero TVA francais."""
        text = "TVA: FR12345678901"
        result = extract_tva_number(text)
        assert result == "FR12345678901"

    def test_tva_with_spaces(self):
        """Test TVA avec espaces."""
        text = "N° TVA FR 12 345 678 901"
        result = extract_tva_number(text)
        assert result == "FR12345678901"


class TestFindBetweenMarkers:
    """Tests pour find_between_markers."""

    def test_find_between(self):
        """Test extraction entre marqueurs."""
        text = "Debut [IMPORTANT] texte important [FIN] suite"
        result = find_between_markers(text, "[IMPORTANT]", "[FIN]")
        assert result == "texte important"

    def test_no_markers(self):
        """Test sans marqueurs."""
        text = "Texte sans marqueurs"
        result = find_between_markers(text, "[START]", "[END]")
        assert result is None
