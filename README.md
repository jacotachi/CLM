# CLM Reader - Lecteur de Contrats et Factures

Outil Python pour extraire automatiquement les informations structurees des contrats et factures au format PDF ou DOCX.

## Fonctionnalites

### Pour les Contrats
- **Societe Emettrice** : Identification de la societe qui emet le contrat
- **Societe Receptrice** : Identification de la societe qui recoit le contrat
- **Designation** : Titre ou reference du contrat
- **Objet** : Description detaillee de l'objet du contrat
- **Signataire** : Nom du signataire
- **Prix HT** : Montant hors taxes
- **Quantite** : Quantite concernee
- **Engagement** : Duree ou nature de l'engagement

### Pour les Factures
- **Societe Emettrice** : Emetteur de la facture
- **Societe Destinatrice** : Destinataire de la facture
- **Prix HT** : Montant hors taxes
- **TVA** : Montant de la TVA
- **Prix TTC** : Montant toutes taxes comprises
- **Quantite** : Quantite facturee
- **Date de Facture** : Date d'emission
- **Date de Paiement Max** : Echeance de paiement
- **Duree de Prestation** : Periode couverte
- **Designation de la Prestation** : Description du service/produit

## Installation

### Installation basique
```bash
pip install -e .
```

### Avec support OCR (pour PDF scannes)
```bash
pip install -e ".[ocr]"
```

### Pour le developpement
```bash
pip install -e ".[dev]"
```

## Utilisation

### Ligne de commande

#### Analyser un contrat
```bash
clm-reader contrat document.pdf
clm-reader contrat document.pdf --format json
clm-reader contrat document.pdf --output resultat.json
```

#### Analyser une facture
```bash
clm-reader facture facture.pdf
clm-reader facture facture.pdf --format json
clm-reader facture facture.pdf --output resultat.json
```

#### Traitement par lot
```bash
clm-reader batch ./documents/
clm-reader batch ./documents/ --type contrat
clm-reader batch ./documents/ --output resultats.json
```

#### Detection automatique du type
```bash
clm-reader detect document.pdf
```

### En Python

```python
from clm_reader import ContractParser, InvoiceParser

# Analyser un contrat
parser = ContractParser()
contrat = parser.parse("contrat.pdf")
print(contrat.summary())
print(f"Societe emettrice: {contrat.societe_emettrice}")
print(f"Prix HT: {contrat.prix_ht} EUR")

# Analyser une facture
parser = InvoiceParser()
facture = parser.parse("facture.pdf")
print(facture.summary())
print(f"Total TTC: {facture.prix_ttc} EUR")
print(f"En retard: {facture.is_overdue()}")

# Exporter en JSON
import json
print(json.dumps(contrat.to_dict(), indent=2, ensure_ascii=False))
```

## Options CLI

| Option | Description |
|--------|-------------|
| `--format, -f` | Format de sortie: `table`, `json`, `text` |
| `--ocr` | Activer l'OCR pour les PDF scannes |
| `--output, -o` | Fichier de sortie JSON |
| `--type, -t` | Type de document (pour batch): `contrat`, `facture`, `auto` |

## Structure du Projet

```
clm_reader/
├── __init__.py
├── cli.py                    # Interface ligne de commande
├── models/
│   ├── __init__.py
│   ├── contract.py          # Modele de donnees Contrat
│   └── invoice.py           # Modele de donnees Facture
├── parsers/
│   ├── __init__.py
│   ├── contract_parser.py   # Parser de contrats
│   └── invoice_parser.py    # Parser de factures
├── extractors/
│   ├── __init__.py
│   └── document_extractor.py # Extraction PDF/DOCX
└── utils/
    ├── __init__.py
    └── text_utils.py         # Utilitaires de traitement texte
```

## Score de Confiance

Chaque extraction inclut un score de confiance (0-100%) indiquant la qualite de l'extraction:
- **80-100%** : Extraction fiable
- **50-79%** : Extraction partielle, verification recommandee
- **0-49%** : Document difficile a analyser

## Dependances

- `pdfplumber` : Extraction de texte PDF
- `PyPDF2` : Lecture PDF (fallback)
- `python-docx` : Lecture fichiers Word
- `pydantic` : Validation des donnees
- `click` : Interface CLI
- `rich` : Affichage console
- `python-dateutil` : Parsing de dates

## Licence

MIT License
