"""Interface en ligne de commande pour CLM Reader."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .parsers.contract_parser import ContractParser
from .parsers.invoice_parser import InvoiceParser
from .models.contract import Contract
from .models.invoice import Invoice

console = Console()


def print_contract(contract: Contract, format_output: str = "table"):
    """Affiche les informations d'un contrat."""
    if format_output == "json":
        console.print_json(json.dumps(contract.to_dict(), ensure_ascii=False, default=str))
        return

    if format_output == "text":
        console.print(contract.summary())
        return

    # Format tableau (par défaut)
    table = Table(title="Contrat", show_header=True, header_style="bold blue")
    table.add_column("Champ", style="cyan", width=25)
    table.add_column("Valeur", style="white")

    fields = [
        ("Fichier source", contract.fichier_source),
        ("Société Émettrice", contract.societe_emettrice),
        ("Société Réceptrice", contract.societe_receptrice),
        ("Désignation", contract.designation),
        ("Objet", contract.objet),
        ("Signataire", contract.signataire),
        ("Prix HT", f"{contract.prix_ht} EUR" if contract.prix_ht else None),
        ("Quantité", contract.quantite),
        ("Engagement", contract.engagement),
        ("Date signature", str(contract.date_signature) if contract.date_signature else None),
        ("Date début", str(contract.date_debut) if contract.date_debut else None),
        ("Date fin", str(contract.date_fin) if contract.date_fin else None),
        ("Confiance", f"{contract.confiance}%"),
    ]

    for field_name, value in fields:
        if value:
            table.add_row(field_name, str(value))
        else:
            table.add_row(field_name, Text("Non trouvé", style="dim"))

    console.print(table)


def print_invoice(invoice: Invoice, format_output: str = "table"):
    """Affiche les informations d'une facture."""
    if format_output == "json":
        console.print_json(json.dumps(invoice.to_dict(), ensure_ascii=False, default=str))
        return

    if format_output == "text":
        console.print(invoice.summary())
        return

    # Format tableau (par défaut)
    table = Table(title="Facture", show_header=True, header_style="bold green")
    table.add_column("Champ", style="cyan", width=25)
    table.add_column("Valeur", style="white")

    fields = [
        ("Fichier source", invoice.fichier_source),
        ("Numéro facture", invoice.numero_facture),
        ("Société Émettrice", invoice.societe_emettrice),
        ("Société Destinatrice", invoice.societe_destinatrice),
        ("Désignation prestation", invoice.designation_prestation),
        ("Prix HT", f"{invoice.prix_ht} EUR" if invoice.prix_ht else None),
        ("TVA", f"{invoice.tva} EUR" if invoice.tva else None),
        ("Prix TTC", f"{invoice.prix_ttc} EUR" if invoice.prix_ttc else None),
        ("Quantité", invoice.quantite),
        ("Date facture", str(invoice.date_facture) if invoice.date_facture else None),
        ("Date paiement max", str(invoice.date_paiement_max) if invoice.date_paiement_max else None),
        ("Durée prestation", invoice.duree_prestation),
        ("Confiance", f"{invoice.confiance}%"),
    ]

    for field_name, value in fields:
        if value:
            # Colorer la date de paiement si en retard
            if field_name == "Date paiement max" and invoice.is_overdue():
                table.add_row(field_name, Text(str(value) + " (EN RETARD)", style="bold red"))
            else:
                table.add_row(field_name, str(value))
        else:
            table.add_row(field_name, Text("Non trouvé", style="dim"))

    console.print(table)

    # Avertissement si facture en retard
    if invoice.is_overdue():
        console.print(Panel(
            f"[bold red]ATTENTION:[/bold red] Cette facture est en retard de paiement !",
            border_style="red"
        ))


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    CLM Reader - Outil de lecture de contrats et factures.

    Extrait automatiquement les informations structurées des documents
    PDF et DOCX.
    """
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', '-f', 'format_output', type=click.Choice(['table', 'json', 'text']),
              default='table', help='Format de sortie')
@click.option('--ocr', is_flag=True, help='Utiliser OCR pour les PDF scannés')
@click.option('--output', '-o', type=click.Path(), help='Fichier de sortie (JSON)')
def contrat(file_path: str, format_output: str, ocr: bool, output: Optional[str]):
    """
    Analyse un contrat et extrait les informations.

    FILE_PATH: Chemin vers le fichier de contrat (PDF ou DOCX)
    """
    try:
        parser = ContractParser(use_ocr=ocr)

        with console.status(f"[bold blue]Analyse du contrat: {file_path}..."):
            contract = parser.parse(file_path)

        print_contract(contract, format_output)

        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(contract.to_dict(), f, ensure_ascii=False, indent=2, default=str)
            console.print(f"\n[green]Résultat sauvegardé dans: {output}[/green]")

    except FileNotFoundError:
        console.print(f"[red]Erreur: Fichier non trouvé: {file_path}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erreur lors de l'analyse: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', '-f', 'format_output', type=click.Choice(['table', 'json', 'text']),
              default='table', help='Format de sortie')
@click.option('--ocr', is_flag=True, help='Utiliser OCR pour les PDF scannés')
@click.option('--output', '-o', type=click.Path(), help='Fichier de sortie (JSON)')
def facture(file_path: str, format_output: str, ocr: bool, output: Optional[str]):
    """
    Analyse une facture et extrait les informations.

    FILE_PATH: Chemin vers le fichier de facture (PDF ou DOCX)
    """
    try:
        parser = InvoiceParser(use_ocr=ocr)

        with console.status(f"[bold green]Analyse de la facture: {file_path}..."):
            invoice = parser.parse(file_path)

        print_invoice(invoice, format_output)

        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(invoice.to_dict(), f, ensure_ascii=False, indent=2, default=str)
            console.print(f"\n[green]Résultat sauvegardé dans: {output}[/green]")

    except FileNotFoundError:
        console.print(f"[red]Erreur: Fichier non trouvé: {file_path}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erreur lors de l'analyse: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--type', '-t', 'doc_type', type=click.Choice(['contrat', 'facture', 'auto']),
              default='auto', help='Type de document')
@click.option('--format', '-f', 'format_output', type=click.Choice(['table', 'json', 'text']),
              default='table', help='Format de sortie')
@click.option('--ocr', is_flag=True, help='Utiliser OCR pour les PDF scannés')
@click.option('--output', '-o', type=click.Path(), help='Fichier de sortie (JSON)')
def batch(directory: str, doc_type: str, format_output: str, ocr: bool, output: Optional[str]):
    """
    Analyse tous les documents d'un répertoire.

    DIRECTORY: Répertoire contenant les documents
    """
    contract_parser = ContractParser(use_ocr=ocr)
    invoice_parser = InvoiceParser(use_ocr=ocr)

    # Trouver tous les fichiers PDF et DOCX
    path = Path(directory)
    files = list(path.glob('**/*.pdf')) + list(path.glob('**/*.docx'))

    if not files:
        console.print(f"[yellow]Aucun fichier PDF ou DOCX trouvé dans: {directory}[/yellow]")
        return

    results = {
        'contrats': [],
        'factures': [],
        'erreurs': []
    }

    with console.status(f"[bold]Analyse de {len(files)} fichiers...") as status:
        for i, file_path in enumerate(files, 1):
            status.update(f"[bold]Analyse de {file_path.name} ({i}/{len(files)})...")

            try:
                file_str = str(file_path)

                # Détection automatique ou forcée
                if doc_type == 'auto':
                    # Heuristique simple basée sur le nom du fichier
                    filename_lower = file_path.name.lower()
                    if 'facture' in filename_lower or 'invoice' in filename_lower:
                        is_invoice = True
                    elif 'contrat' in filename_lower or 'contract' in filename_lower:
                        is_invoice = False
                    else:
                        # Par défaut, essayer les deux et prendre le meilleur score
                        contract = contract_parser.parse(file_str)
                        invoice = invoice_parser.parse(file_str)
                        is_invoice = invoice.confiance > contract.confiance
                else:
                    is_invoice = (doc_type == 'facture')

                if is_invoice:
                    invoice = invoice_parser.parse(file_str)
                    results['factures'].append(invoice.to_dict())
                    if format_output != 'json':
                        print_invoice(invoice, format_output)
                        console.print()
                else:
                    contract = contract_parser.parse(file_str)
                    results['contrats'].append(contract.to_dict())
                    if format_output != 'json':
                        print_contract(contract, format_output)
                        console.print()

            except Exception as e:
                results['erreurs'].append({
                    'fichier': str(file_path),
                    'erreur': str(e)
                })
                console.print(f"[red]Erreur avec {file_path.name}: {e}[/red]")

    # Résumé
    console.print(Panel(
        f"[bold]Résumé du traitement:[/bold]\n"
        f"  Contrats analysés: {len(results['contrats'])}\n"
        f"  Factures analysées: {len(results['factures'])}\n"
        f"  Erreurs: {len(results['erreurs'])}",
        title="Batch terminé"
    ))

    # Sauvegarder si demandé
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        console.print(f"\n[green]Résultats sauvegardés dans: {output}[/green]")

    if format_output == 'json':
        console.print_json(json.dumps(results, ensure_ascii=False, default=str))


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--ocr', is_flag=True, help='Utiliser OCR pour les PDF scannés')
def detect(file_path: str, ocr: bool):
    """
    Détecte automatiquement le type de document (contrat ou facture).

    FILE_PATH: Chemin vers le fichier à analyser
    """
    contract_parser = ContractParser(use_ocr=ocr)
    invoice_parser = InvoiceParser(use_ocr=ocr)

    with console.status(f"[bold]Analyse du document: {file_path}..."):
        contract = contract_parser.parse(file_path)
        invoice = invoice_parser.parse(file_path)

    console.print(Panel(
        f"[bold]Résultats de la détection:[/bold]\n\n"
        f"  Score Contrat: {contract.confiance}%\n"
        f"  Score Facture: {invoice.confiance}%\n\n"
        f"  [bold green]Type détecté: {'FACTURE' if invoice.confiance > contract.confiance else 'CONTRAT'}[/bold green]",
        title="Détection de type"
    ))


def main():
    """Point d'entrée principal."""
    cli()


if __name__ == '__main__':
    main()
