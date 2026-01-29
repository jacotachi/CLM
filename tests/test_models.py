"""Tests pour les modeles de donnees."""

from datetime import date
from decimal import Decimal

import pytest

from clm_reader.models.contract import Contract
from clm_reader.models.invoice import Invoice


class TestContract:
    """Tests pour le modele Contract."""

    def test_create_empty_contract(self):
        """Test creation d'un contrat vide."""
        contract = Contract()
        assert contract.societe_emettrice is None
        assert contract.confiance == 0

    def test_create_full_contract(self):
        """Test creation d'un contrat complet."""
        contract = Contract(
            societe_emettrice="ACME Corp",
            societe_receptrice="Client SA",
            designation="Contrat de service",
            objet="Prestation de conseil",
            signataire="Jean Dupont",
            prix_ht=Decimal("10000.00"),
            quantite="12 mois",
            engagement="1 an renouvelable",
            date_signature=date(2024, 1, 15),
            confiance=85
        )
        assert contract.societe_emettrice == "ACME Corp"
        assert contract.prix_ht == Decimal("10000.00")
        assert contract.confiance == 85

    def test_contract_to_dict(self):
        """Test conversion en dictionnaire."""
        contract = Contract(
            societe_emettrice="Test Corp",
            prix_ht=Decimal("5000.00")
        )
        data = contract.to_dict()
        assert "societe_emettrice" in data
        assert data["societe_emettrice"] == "Test Corp"

    def test_contract_summary(self):
        """Test generation du resume."""
        contract = Contract(
            societe_emettrice="Test Corp",
            prix_ht=Decimal("5000.00"),
            confiance=70
        )
        summary = contract.summary()
        assert "CONTRAT" in summary
        assert "Test Corp" in summary
        assert "5000" in summary


class TestInvoice:
    """Tests pour le modele Invoice."""

    def test_create_empty_invoice(self):
        """Test creation d'une facture vide."""
        invoice = Invoice()
        assert invoice.societe_emettrice is None
        assert invoice.confiance == 0

    def test_create_full_invoice(self):
        """Test creation d'une facture complete."""
        invoice = Invoice(
            societe_emettrice="Fournisseur SA",
            societe_destinatrice="Client SARL",
            prix_ht=Decimal("1000.00"),
            tva=Decimal("200.00"),
            prix_ttc=Decimal("1200.00"),
            date_facture=date(2024, 1, 1),
            date_paiement_max=date(2024, 1, 31),
            numero_facture="FAC-2024-001",
            confiance=90
        )
        assert invoice.societe_emettrice == "Fournisseur SA"
        assert invoice.prix_ttc == Decimal("1200.00")

    def test_invoice_is_overdue(self):
        """Test detection facture en retard."""
        # Facture en retard
        invoice_overdue = Invoice(
            date_paiement_max=date(2020, 1, 1)
        )
        assert invoice_overdue.is_overdue() is True

        # Facture pas en retard
        invoice_ok = Invoice(
            date_paiement_max=date(2030, 12, 31)
        )
        assert invoice_ok.is_overdue() is False

    def test_invoice_days_until_payment(self):
        """Test calcul jours restants."""
        invoice = Invoice(
            date_paiement_max=date.today()
        )
        assert invoice.days_until_payment() == 0

    def test_invoice_to_dict(self):
        """Test conversion en dictionnaire."""
        invoice = Invoice(
            numero_facture="FAC-001",
            prix_ht=Decimal("100.00")
        )
        data = invoice.to_dict()
        assert "numero_facture" in data
        assert data["numero_facture"] == "FAC-001"
