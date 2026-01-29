"""
CLM Reader - Outil de lecture de contrats et factures

Ce module permet d'extraire les informations structurées des contrats
et factures au format PDF ou DOCX, avec interface graphique Windows
et persistance des données.
"""

__version__ = "1.0.0"

from .models.contract import Contract
from .models.invoice import Invoice
from .parsers.contract_parser import ContractParser
from .parsers.invoice_parser import InvoiceParser
from .extractors.document_extractor import DocumentExtractor
from .database.db_manager import Database

__all__ = [
    "Contract",
    "Invoice",
    "ContractParser",
    "InvoiceParser",
    "DocumentExtractor",
    "Database",
]
