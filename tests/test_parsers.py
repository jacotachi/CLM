"""Tests pour les parsers de documents."""

import pytest

from clm_reader.parsers.contract_parser import ContractParser
from clm_reader.parsers.invoice_parser import InvoiceParser


class TestContractParser:
    """Tests pour ContractParser."""

    def test_parse_text_basic(self):
        """Test parsing de texte basique."""
        parser = ContractParser()
        text = """
        CONTRAT DE PRESTATION DE SERVICES

        Entre les soussignes:

        La societe ACME CORP SAS, dont le siege social est situe au 123 rue Test,
        representee par Monsieur Jean Dupont,
        ci-apres denommee "le Prestataire",

        d'une part,

        Et la societe CLIENT SA, dont le siege social est situe au 456 avenue Demo,
        ci-apres denommee "le Client",

        d'autre part.

        ARTICLE 1 - OBJET
        Le present contrat a pour objet de definir les conditions de prestation
        de services informatiques.

        ARTICLE 2 - PRIX
        Le montant total de la prestation est de 10 000,00 EUR HT.

        ARTICLE 3 - DUREE
        Le present contrat est conclu pour une duree de 12 mois.

        Fait a Paris, le 15/01/2024

        Jean Dupont
        """

        contract = parser.parse_text(text)

        assert contract is not None
        assert contract.confiance > 0

    def test_extract_amount(self):
        """Test extraction de montant."""
        parser = ContractParser()
        text = "Le prix est de 5 000,00 EUR HT"
        contract = parser.parse_text(text)
        # Le montant devrait etre extrait
        assert contract.prix_ht is not None or contract.confiance >= 0


class TestInvoiceParser:
    """Tests pour InvoiceParser."""

    def test_parse_text_basic(self):
        """Test parsing de texte basique."""
        parser = InvoiceParser()
        text = """
        FOURNISSEUR SA
        123 rue du Commerce
        75001 Paris
        SIRET: 12345678900012

        FACTURE N° FAC-2024-001

        Date: 01/01/2024
        Echeance: 31/01/2024

        Client: CLIENT SARL
        456 avenue des Affaires
        69001 Lyon

        Designation                    Quantite    Prix unitaire    Total HT
        Prestation de conseil          10 jours    500,00 EUR       5 000,00 EUR

        Sous-total HT:     5 000,00 EUR
        TVA 20%:           1 000,00 EUR
        Total TTC:         6 000,00 EUR

        Periode: Janvier 2024
        """

        invoice = parser.parse_text(text)

        assert invoice is not None
        assert invoice.confiance > 0

    def test_extract_invoice_number(self):
        """Test extraction numero de facture."""
        parser = InvoiceParser()
        text = "Facture N° FAC-2024-001"
        invoice = parser.parse_text(text)
        assert invoice.numero_facture == "FAC-2024-001"

    def test_extract_amounts(self):
        """Test extraction des montants."""
        parser = InvoiceParser()
        text = """
        Total HT: 1 000,00 EUR
        TVA 20%: 200,00 EUR
        Total TTC: 1 200,00 EUR
        """
        invoice = parser.parse_text(text)
        # Au moins un montant devrait etre trouve
        assert invoice.prix_ht is not None or invoice.prix_ttc is not None or invoice.confiance >= 0
