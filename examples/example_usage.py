#!/usr/bin/env python3
"""
Exemple d'utilisation de CLM Reader.

Ce script montre comment utiliser les differentes fonctionnalites
de CLM Reader pour analyser des contrats et factures.
"""

import json
from pathlib import Path

# Import des modules CLM Reader
from clm_reader import ContractParser, InvoiceParser, Contract, Invoice


def exemple_analyse_contrat():
    """Exemple d'analyse d'un contrat."""
    print("=" * 60)
    print("EXEMPLE: Analyse d'un contrat")
    print("=" * 60)

    # Creer le parser
    parser = ContractParser()

    # Texte d'exemple (normalement on utiliserait parser.parse("fichier.pdf"))
    texte_contrat = """
    CONTRAT DE PRESTATION DE SERVICES INFORMATIQUES

    Entre les soussignes:

    La societe TECH SOLUTIONS SAS, au capital de 50 000 EUR,
    dont le siege social est situe au 15 rue de l'Innovation, 75001 Paris,
    immatriculee au RCS de Paris sous le numero 123 456 789,
    representee par Monsieur Pierre Martin, en qualite de Directeur General,
    ci-apres denommee "le Prestataire",

    d'une part,

    Et la societe ACME INDUSTRIE SA, au capital de 1 000 000 EUR,
    dont le siege social est situe au 42 avenue des Entreprises, 69001 Lyon,
    representee par Madame Sophie Durand, en qualite de PDG,
    ci-apres denommee "le Client",

    d'autre part.

    Il a ete convenu ce qui suit:

    ARTICLE 1 - OBJET DU CONTRAT
    Le present contrat a pour objet de definir les conditions dans lesquelles
    le Prestataire fournira au Client des services de developpement logiciel
    et de maintenance applicative.

    ARTICLE 2 - DUREE
    Le present contrat est conclu pour une duree de 24 mois a compter du 1er janvier 2024,
    renouvelable par tacite reconduction.

    ARTICLE 3 - PRIX ET MODALITES DE PAIEMENT
    Le montant total de la prestation est fixe a 150 000,00 EUR HT.
    Ce montant sera facture mensuellement a raison de 6 250,00 EUR HT par mois.

    Fait a Paris, le 15 decembre 2023
    En deux exemplaires originaux.

    Pierre Martin                    Sophie Durand
    Directeur General               PDG
    TECH SOLUTIONS SAS              ACME INDUSTRIE SA
    """

    # Parser le texte
    contrat = parser.parse_text(texte_contrat, source_name="exemple_contrat.txt")

    # Afficher le resume
    print("\nResume du contrat:")
    print(contrat.summary())

    # Acces aux champs individuels
    print("\n\nDetails extraits:")
    print(f"  Emetteur: {contrat.societe_emettrice}")
    print(f"  Recepteur: {contrat.societe_receptrice}")
    print(f"  Designation: {contrat.designation}")
    print(f"  Objet: {contrat.objet[:100]}..." if contrat.objet else "  Objet: Non trouve")
    print(f"  Signataire: {contrat.signataire}")
    print(f"  Prix HT: {contrat.prix_ht} EUR")
    print(f"  Engagement: {contrat.engagement}")
    print(f"  Score de confiance: {contrat.confiance}%")

    # Export JSON
    print("\n\nExport JSON:")
    print(json.dumps(contrat.to_dict(), indent=2, ensure_ascii=False, default=str))


def exemple_analyse_facture():
    """Exemple d'analyse d'une facture."""
    print("\n" + "=" * 60)
    print("EXEMPLE: Analyse d'une facture")
    print("=" * 60)

    # Creer le parser
    parser = InvoiceParser()

    # Texte d'exemple
    texte_facture = """
    TECH SOLUTIONS SAS
    15 rue de l'Innovation
    75001 Paris
    SIRET: 123 456 789 00012
    TVA: FR 12 345 678 901

    FACTURE

    Facture N° FAC-2024-0042
    Date: 15/01/2024
    Echeance: 15/02/2024

    Adresse de facturation:
    ACME INDUSTRIE SA
    42 avenue des Entreprises
    69001 Lyon

    Designation                           Quantite    Prix Unit. HT    Total HT
    -------------------------------------------------------------------------
    Developpement module comptabilite     1           6 250,00 EUR     6 250,00 EUR

    Periode: Janvier 2024

    -------------------------------------------------------------------------
    Sous-total HT:                                                    6 250,00 EUR
    TVA 20%:                                                          1 250,00 EUR
    -------------------------------------------------------------------------
    TOTAL TTC:                                                        7 500,00 EUR

    Conditions de paiement: 30 jours fin de mois
    RIB: FR76 1234 5678 9012 3456 7890 123
    """

    # Parser le texte
    facture = parser.parse_text(texte_facture, source_name="exemple_facture.txt")

    # Afficher le resume
    print("\nResume de la facture:")
    print(facture.summary())

    # Acces aux champs individuels
    print("\n\nDetails extraits:")
    print(f"  Numero: {facture.numero_facture}")
    print(f"  Emetteur: {facture.societe_emettrice}")
    print(f"  Destinataire: {facture.societe_destinatrice}")
    print(f"  Prestation: {facture.designation_prestation}")
    print(f"  Prix HT: {facture.prix_ht} EUR")
    print(f"  TVA: {facture.tva} EUR")
    print(f"  Prix TTC: {facture.prix_ttc} EUR")
    print(f"  Date facture: {facture.date_facture}")
    print(f"  Date paiement max: {facture.date_paiement_max}")
    print(f"  Periode: {facture.duree_prestation}")
    print(f"  Score de confiance: {facture.confiance}%")

    # Verification du retard
    if facture.date_paiement_max:
        jours_restants = facture.days_until_payment()
        if jours_restants is not None:
            if jours_restants < 0:
                print(f"\n  ATTENTION: Facture en retard de {abs(jours_restants)} jours!")
            elif jours_restants == 0:
                print("\n  ATTENTION: Facture a payer aujourd'hui!")
            else:
                print(f"\n  Jours restants pour payer: {jours_restants}")


def exemple_creation_modeles():
    """Exemple de creation manuelle de modeles."""
    print("\n" + "=" * 60)
    print("EXEMPLE: Creation manuelle de modeles")
    print("=" * 60)

    from datetime import date
    from decimal import Decimal

    # Creer un contrat manuellement
    contrat = Contract(
        societe_emettrice="Ma Societe SAS",
        societe_receptrice="Client SA",
        designation="Contrat de maintenance",
        objet="Maintenance annuelle des equipements",
        signataire="Jean Dupont",
        prix_ht=Decimal("24000.00"),
        quantite="1 an",
        engagement="12 mois renouvelable",
        date_signature=date(2024, 1, 1),
        date_debut=date(2024, 1, 1),
        date_fin=date(2024, 12, 31),
        confiance=100
    )

    print("\nContrat cree:")
    print(contrat.summary())

    # Creer une facture manuellement
    facture = Invoice(
        societe_emettrice="Ma Societe SAS",
        societe_destinatrice="Client SA",
        numero_facture="FAC-2024-001",
        prix_ht=Decimal("2000.00"),
        tva=Decimal("400.00"),
        prix_ttc=Decimal("2400.00"),
        quantite="1",
        date_facture=date(2024, 1, 15),
        date_paiement_max=date(2024, 2, 15),
        duree_prestation="Janvier 2024",
        designation_prestation="Maintenance mensuelle",
        confiance=100
    )

    print("\nFacture creee:")
    print(facture.summary())


if __name__ == "__main__":
    exemple_analyse_contrat()
    exemple_analyse_facture()
    exemple_creation_modeles()

    print("\n" + "=" * 60)
    print("Exemples termines!")
    print("=" * 60)
