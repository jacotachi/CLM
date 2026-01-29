# CLM Reader - Lecteur de Contrats et Factures

Outil Python pour extraire automatiquement les informations structurees des contrats et factures au format PDF ou DOCX, avec **interface graphique Windows** et **suivi dans le temps**.

## Fonctionnalites principales

- **Interface graphique Windows** (tkinter) - Pas de console requise
- **Base de donnees SQLite** - Persistance locale des donnees
- **Suivi des societes** - Vue centralisee par societe
- **Evolution dans le temps** - Historique des factures par mois
- **Liaison contrats/factures** - Suivi des paiements par contrat
- **Detection automatique** - Identification automatique du type de document
- **Export JSON** - Export des donnees pour integration

## Informations extraites

### Pour les Contrats
| Champ | Description |
|-------|-------------|
| Societe Emettrice | Societe qui emet le contrat |
| Societe Receptrice | Societe qui recoit le contrat |
| Designation | Titre ou reference du contrat |
| Objet | Description detaillee |
| Signataire | Nom du signataire |
| Prix HT | Montant hors taxes |
| Quantite | Quantite concernee |
| Engagement | Duree de l'engagement |

### Pour les Factures
| Champ | Description |
|-------|-------------|
| Societe Emettrice | Emetteur de la facture |
| Societe Destinatrice | Destinataire |
| Prix HT / TVA / TTC | Montants |
| Quantite | Quantite facturee |
| Date de Facture | Date d'emission |
| Date de Paiement Max | Echeance |
| Duree de Prestation | Periode couverte |
| Designation | Description du service |

## Installation

### Installation basique
```bash
pip install -r requirements.txt
```

### Lancer l'application graphique
```bash
python run_app.py
```

### Creer un executable Windows (.exe)
```bash
python build_windows.py
```
L'executable sera cree dans le dossier `dist/CLMReader.exe`

## Utilisation de l'interface graphique

### Vue principale
- **Panel gauche** : Liste des societes avec nombre de contrats/factures et total
- **Panel droit** : Onglets Contrats, Factures, Evolution

### Import de documents
1. Menu **Fichier > Importer Contrat** (Ctrl+O)
2. Menu **Fichier > Importer Facture** (Ctrl+I)
3. Menu **Fichier > Import Multiple** pour plusieurs fichiers

### Suivi par societe
1. Cliquer sur une societe dans la liste
2. Voir les contrats et factures associes
3. Onglet **Evolution** : historique mensuel des factures

### Gestion des factures
- **Marquer payee** : Indique qu'une facture a ete reglee
- **Lier a un contrat** : Associe une facture a un contrat existant
- Les factures en retard sont colorees en rouge

### Raccourcis clavier
| Raccourci | Action |
|-----------|--------|
| Ctrl+O | Importer un contrat |
| Ctrl+I | Importer une facture |
| F5 | Rafraichir les donnees |

## Utilisation en ligne de commande

```bash
# Analyser un contrat
clm-reader contrat document.pdf

# Analyser une facture
clm-reader facture facture.pdf --format json

# Traitement par lot
clm-reader batch ./documents/ --output resultats.json

# Detection automatique
clm-reader detect document.pdf
```

## Utilisation en Python

```python
from clm_reader import ContractParser, InvoiceParser, Database

# Analyser et sauvegarder un contrat
parser = ContractParser()
contrat = parser.parse("contrat.pdf")

db = Database()
db.save_contract(contrat)

# Recuperer l'evolution d'une societe
evolution = db.get_evolution_by_societe(societe_id=1)
for mois in evolution:
    print(f"{mois['mois']}: {mois['total_ttc']} EUR")

# Factures impayees
impayees = db.get_factures_impayees()
print(f"{len(impayees)} factures en retard")
```

## Structure du Projet

```
clm_reader/
├── __init__.py
├── cli.py                    # Interface ligne de commande
├── gui/
│   ├── __init__.py
│   └── main_window.py        # Interface graphique Windows
├── database/
│   ├── __init__.py
│   └── db_manager.py         # Gestion base de donnees SQLite
├── models/
│   ├── contract.py           # Modele Contrat
│   └── invoice.py            # Modele Facture
├── parsers/
│   ├── contract_parser.py    # Parser de contrats
│   └── invoice_parser.py     # Parser de factures
├── extractors/
│   └── document_extractor.py # Extraction PDF/DOCX
└── utils/
    └── text_utils.py         # Utilitaires texte
```

## Base de donnees

Les donnees sont stockees localement dans un fichier SQLite:
- **Windows**: `%APPDATA%/CLMReader/clm_data.db`
- **Linux/Mac**: `~/.clm_reader/clm_data.db`

### Tables
- `societes` : Liste des societes
- `contrats` : Contrats avec liens vers societes
- `factures` : Factures avec liens vers societes et contrats

## Score de Confiance

Chaque extraction inclut un score de confiance (0-100%):
- **80-100%** : Extraction fiable
- **50-79%** : Extraction partielle, verification recommandee
- **0-49%** : Document difficile a analyser

## Dependances

- `pdfplumber` : Extraction de texte PDF
- `PyPDF2` : Lecture PDF (fallback)
- `python-docx` : Lecture fichiers Word
- `pydantic` : Validation des donnees
- `tkinter` : Interface graphique (inclus avec Python)
- `sqlite3` : Base de donnees (inclus avec Python)
- `click` + `rich` : Interface CLI
- `pyinstaller` : Creation executable Windows

## Licence

MIT License
