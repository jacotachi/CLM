"""Fenêtre principale de l'application CLM Reader."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import date
from typing import Optional, Callable

from ..database.db_manager import Database
from ..parsers.contract_parser import ContractParser
from ..parsers.invoice_parser import InvoiceParser


class MainWindow:
    """Fenêtre principale de l'application."""

    def __init__(self):
        """Initialise la fenêtre principale."""
        self.root = tk.Tk()
        self.root.title("CLM Reader - Gestion Contrats & Factures")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)

        # Initialiser la base de données
        self.db = Database()

        # Parsers
        self.contract_parser = ContractParser()
        self.invoice_parser = InvoiceParser()

        # Variables
        self.current_societe_id = None
        self.current_contrat_id = None

        # Configuration du style
        self._setup_style()

        # Créer l'interface
        self._create_menu()
        self._create_main_layout()

        # Charger les données initiales
        self._refresh_all()

    def _setup_style(self):
        """Configure le style de l'application."""
        style = ttk.Style()

        # Essayer d'utiliser un thème moderne
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes:
            style.theme_use('vista')

        # Personnalisation
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'))
        style.configure('Subtitle.TLabel', font=('Segoe UI', 11, 'bold'))
        style.configure('Stats.TLabel', font=('Segoe UI', 10))
        style.configure('Warning.TLabel', foreground='red')
        style.configure('Success.TLabel', foreground='green')

        # Style pour les Treeview
        style.configure('Treeview', rowheight=25)
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))

    def _create_menu(self):
        """Crée la barre de menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Importer Contrat...", command=self._import_contrat, accelerator="Ctrl+O")
        file_menu.add_command(label="Importer Facture...", command=self._import_facture, accelerator="Ctrl+I")
        file_menu.add_command(label="Import Multiple...", command=self._import_multiple)
        file_menu.add_separator()
        file_menu.add_command(label="Exporter...", command=self._export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit, accelerator="Alt+F4")

        # Menu Affichage
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        view_menu.add_command(label="Rafraichir", command=self._refresh_all, accelerator="F5")
        view_menu.add_command(label="Factures impayees", command=self._show_factures_impayees)

        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="A propos", command=self._show_about)

        # Raccourcis clavier
        self.root.bind('<Control-o>', lambda e: self._import_contrat())
        self.root.bind('<Control-i>', lambda e: self._import_facture())
        self.root.bind('<F5>', lambda e: self._refresh_all())

    def _create_main_layout(self):
        """Crée la disposition principale."""
        # Frame principale avec PanedWindow
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel gauche : Liste des sociétés
        self._create_left_panel()

        # Panel droit : Détails
        self._create_right_panel()

        # Barre de statut
        self._create_status_bar()

    def _create_left_panel(self):
        """Crée le panel gauche avec la liste des sociétés."""
        left_frame = ttk.Frame(self.main_paned, width=350)
        self.main_paned.add(left_frame, weight=1)

        # Titre et stats
        header_frame = ttk.Frame(left_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(header_frame, text="Societes", style='Title.TLabel').pack(side=tk.LEFT)

        # Bouton d'import rapide
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="+ Contrat", command=self._import_contrat, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="+ Facture", command=self._import_facture, width=10).pack(side=tk.LEFT, padx=2)

        # Barre de recherche
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._filter_societes())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, side=tk.LEFT, expand=True)
        ttk.Button(search_frame, text="X", width=3, command=lambda: self.search_var.set('')).pack(side=tk.RIGHT)

        # Liste des sociétés
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('nom', 'contrats', 'factures', 'total')
        self.societes_tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')

        self.societes_tree.heading('nom', text='Societe')
        self.societes_tree.heading('contrats', text='Contrats')
        self.societes_tree.heading('factures', text='Factures')
        self.societes_tree.heading('total', text='Total EUR')

        self.societes_tree.column('nom', width=150)
        self.societes_tree.column('contrats', width=60, anchor='center')
        self.societes_tree.column('factures', width=60, anchor='center')
        self.societes_tree.column('total', width=80, anchor='e')

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.societes_tree.yview)
        self.societes_tree.configure(yscrollcommand=scrollbar.set)

        self.societes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.societes_tree.bind('<<TreeviewSelect>>', self._on_societe_select)
        self.societes_tree.bind('<Double-1>', self._on_societe_double_click)

        # Stats globales
        self.stats_frame = ttk.LabelFrame(left_frame, text="Statistiques")
        self.stats_frame.pack(fill=tk.X, padx=5, pady=5)

        self.stats_labels = {}
        for i, (key, label) in enumerate([
            ('nb_societes', 'Societes:'),
            ('nb_contrats', 'Contrats:'),
            ('nb_factures', 'Factures:'),
            ('total_facture', 'Total:'),
            ('nb_factures_impayees', 'Impayees:')
        ]):
            ttk.Label(self.stats_frame, text=label).grid(row=i//2, column=(i%2)*2, sticky='w', padx=5, pady=2)
            self.stats_labels[key] = ttk.Label(self.stats_frame, text="0", style='Stats.TLabel')
            self.stats_labels[key].grid(row=i//2, column=(i%2)*2+1, sticky='e', padx=5, pady=2)

    def _create_right_panel(self):
        """Crée le panel droit avec les détails."""
        right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(right_frame, weight=3)

        # Notebook pour les onglets
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Onglet Contrats
        self._create_contrats_tab()

        # Onglet Factures
        self._create_factures_tab()

        # Onglet Evolution
        self._create_evolution_tab()

    def _create_contrats_tab(self):
        """Crée l'onglet des contrats."""
        contrats_frame = ttk.Frame(self.notebook)
        self.notebook.add(contrats_frame, text="Contrats")

        # Toolbar
        toolbar = ttk.Frame(contrats_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        self.contrat_societe_label = ttk.Label(toolbar, text="Tous les contrats", style='Subtitle.TLabel')
        self.contrat_societe_label.pack(side=tk.LEFT)

        ttk.Button(toolbar, text="Voir tout", command=self._show_all_contrats).pack(side=tk.RIGHT, padx=2)

        # Liste des contrats
        list_frame = ttk.Frame(contrats_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('id', 'designation', 'emetteur', 'recepteur', 'prix_ht', 'engagement', 'date', 'factures')
        self.contrats_tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')

        self.contrats_tree.heading('id', text='ID')
        self.contrats_tree.heading('designation', text='Designation')
        self.contrats_tree.heading('emetteur', text='Emetteur')
        self.contrats_tree.heading('recepteur', text='Client')
        self.contrats_tree.heading('prix_ht', text='Prix HT')
        self.contrats_tree.heading('engagement', text='Engagement')
        self.contrats_tree.heading('date', text='Date')
        self.contrats_tree.heading('factures', text='Factures')

        self.contrats_tree.column('id', width=40, anchor='center')
        self.contrats_tree.column('designation', width=200)
        self.contrats_tree.column('emetteur', width=120)
        self.contrats_tree.column('recepteur', width=120)
        self.contrats_tree.column('prix_ht', width=80, anchor='e')
        self.contrats_tree.column('engagement', width=100)
        self.contrats_tree.column('date', width=80, anchor='center')
        self.contrats_tree.column('factures', width=60, anchor='center')

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.contrats_tree.yview)
        self.contrats_tree.configure(yscrollcommand=scrollbar.set)

        self.contrats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.contrats_tree.bind('<<TreeviewSelect>>', self._on_contrat_select)
        self.contrats_tree.bind('<Double-1>', self._on_contrat_double_click)

        # Détails du contrat sélectionné
        details_frame = ttk.LabelFrame(contrats_frame, text="Details du contrat")
        details_frame.pack(fill=tk.X, padx=5, pady=5)

        self.contrat_detail_text = tk.Text(details_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.contrat_detail_text.pack(fill=tk.X, padx=5, pady=5)

    def _create_factures_tab(self):
        """Crée l'onglet des factures."""
        factures_frame = ttk.Frame(self.notebook)
        self.notebook.add(factures_frame, text="Factures")

        # Toolbar
        toolbar = ttk.Frame(factures_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        self.facture_filter_label = ttk.Label(toolbar, text="Toutes les factures", style='Subtitle.TLabel')
        self.facture_filter_label.pack(side=tk.LEFT)

        ttk.Button(toolbar, text="Voir tout", command=self._show_all_factures).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Impayees", command=self._show_factures_impayees).pack(side=tk.RIGHT, padx=2)

        # Liste des factures
        list_frame = ttk.Frame(factures_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('id', 'numero', 'emetteur', 'destinataire', 'date', 'prix_ttc', 'echeance', 'statut')
        self.factures_tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')

        self.factures_tree.heading('id', text='ID')
        self.factures_tree.heading('numero', text='Numero')
        self.factures_tree.heading('emetteur', text='Emetteur')
        self.factures_tree.heading('destinataire', text='Destinataire')
        self.factures_tree.heading('date', text='Date')
        self.factures_tree.heading('prix_ttc', text='TTC')
        self.factures_tree.heading('echeance', text='Echeance')
        self.factures_tree.heading('statut', text='Statut')

        self.factures_tree.column('id', width=40, anchor='center')
        self.factures_tree.column('numero', width=100)
        self.factures_tree.column('emetteur', width=120)
        self.factures_tree.column('destinataire', width=120)
        self.factures_tree.column('date', width=80, anchor='center')
        self.factures_tree.column('prix_ttc', width=80, anchor='e')
        self.factures_tree.column('echeance', width=80, anchor='center')
        self.factures_tree.column('statut', width=80, anchor='center')

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.factures_tree.yview)
        self.factures_tree.configure(yscrollcommand=scrollbar.set)

        self.factures_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.factures_tree.bind('<Double-1>', self._on_facture_double_click)

        # Tags pour la coloration
        self.factures_tree.tag_configure('impayee', background='#ffcccc')
        self.factures_tree.tag_configure('payee', background='#ccffcc')

        # Détails de la facture
        details_frame = ttk.LabelFrame(factures_frame, text="Details de la facture")
        details_frame.pack(fill=tk.X, padx=5, pady=5)

        self.facture_detail_text = tk.Text(details_frame, height=5, wrap=tk.WORD, state=tk.DISABLED)
        self.facture_detail_text.pack(fill=tk.X, padx=5, pady=5)

        # Boutons d'action
        action_frame = ttk.Frame(details_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(action_frame, text="Marquer payee", command=self._mark_facture_payee).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Lier a un contrat", command=self._link_facture_to_contrat).pack(side=tk.LEFT, padx=2)

    def _create_evolution_tab(self):
        """Crée l'onglet d'évolution."""
        evolution_frame = ttk.Frame(self.notebook)
        self.notebook.add(evolution_frame, text="Evolution")

        # Label d'information
        info_label = ttk.Label(
            evolution_frame,
            text="Selectionnez une societe pour voir l'evolution des factures",
            style='Subtitle.TLabel'
        )
        info_label.pack(pady=20)

        # Frame pour le tableau d'évolution
        self.evolution_tree_frame = ttk.Frame(evolution_frame)
        self.evolution_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('mois', 'nb_factures', 'total_ht', 'total_ttc')
        self.evolution_tree = ttk.Treeview(self.evolution_tree_frame, columns=columns, show='headings')

        self.evolution_tree.heading('mois', text='Mois')
        self.evolution_tree.heading('nb_factures', text='Nb Factures')
        self.evolution_tree.heading('total_ht', text='Total HT')
        self.evolution_tree.heading('total_ttc', text='Total TTC')

        self.evolution_tree.column('mois', width=100, anchor='center')
        self.evolution_tree.column('nb_factures', width=80, anchor='center')
        self.evolution_tree.column('total_ht', width=100, anchor='e')
        self.evolution_tree.column('total_ttc', width=100, anchor='e')

        scrollbar = ttk.Scrollbar(self.evolution_tree_frame, orient=tk.VERTICAL, command=self.evolution_tree.yview)
        self.evolution_tree.configure(yscrollcommand=scrollbar.set)

        self.evolution_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Résumé
        self.evolution_summary = ttk.Label(evolution_frame, text="", style='Stats.TLabel')
        self.evolution_summary.pack(pady=10)

    def _create_status_bar(self):
        """Crée la barre de statut."""
        self.status_bar = ttk.Label(self.root, text="Pret", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _set_status(self, message: str):
        """Met à jour la barre de statut."""
        self.status_bar.config(text=message)
        self.root.update_idletasks()

    # === Chargement des données ===

    def _refresh_all(self):
        """Rafraîchit toutes les données."""
        self._set_status("Chargement...")
        self._load_societes()
        self._load_contrats()
        self._load_factures()
        self._update_stats()
        self._set_status("Pret")

    def _load_societes(self):
        """Charge la liste des sociétés."""
        # Vider la liste
        for item in self.societes_tree.get_children():
            self.societes_tree.delete(item)

        # Charger les sociétés
        societes = self.db.get_all_societes()
        self.societes_data = {s['id']: s for s in societes}

        for s in societes:
            total = f"{s['total_facture']:.2f}" if s['total_facture'] else "0.00"
            self.societes_tree.insert('', tk.END, iid=s['id'], values=(
                s['nom'],
                s['nb_contrats'],
                s['nb_factures'],
                total
            ))

    def _filter_societes(self):
        """Filtre les sociétés selon la recherche."""
        query = self.search_var.get().lower()

        for item in self.societes_tree.get_children():
            societe = self.societes_data.get(int(item))
            if societe:
                if query in societe['nom'].lower():
                    self.societes_tree.reattach(item, '', tk.END)
                else:
                    self.societes_tree.detach(item)

    def _load_contrats(self, societe_id: Optional[int] = None):
        """Charge les contrats."""
        for item in self.contrats_tree.get_children():
            self.contrats_tree.delete(item)

        if societe_id:
            contrats = self.db.get_contrats_by_societe(societe_id)
            societe = self.db.get_societe(societe_id)
            self.contrat_societe_label.config(text=f"Contrats - {societe['nom']}" if societe else "Contrats")
        else:
            contrats = self.db.get_all_contrats()
            self.contrat_societe_label.config(text="Tous les contrats")

        for c in contrats:
            date_str = c['date_signature'][:10] if c['date_signature'] else ''
            prix = f"{c['prix_ht']:.2f}" if c['prix_ht'] else ''
            self.contrats_tree.insert('', tk.END, iid=c['id'], values=(
                c['id'],
                c['designation'] or '(Sans titre)',
                c['societe_emettrice_nom'] or '',
                c['societe_receptrice_nom'] or '',
                prix,
                c['engagement'] or '',
                date_str,
                c['nb_factures']
            ))

    def _load_factures(self, societe_id: Optional[int] = None, contrat_id: Optional[int] = None):
        """Charge les factures."""
        for item in self.factures_tree.get_children():
            self.factures_tree.delete(item)

        if contrat_id:
            factures = self.db.get_factures_by_contrat(contrat_id)
            contrat = self.db.get_contrat(contrat_id)
            self.facture_filter_label.config(text=f"Factures - {contrat['designation']}" if contrat else "Factures")
        elif societe_id:
            factures = self.db.get_factures_by_societe(societe_id)
            societe = self.db.get_societe(societe_id)
            self.facture_filter_label.config(text=f"Factures - {societe['nom']}" if societe else "Factures")
        else:
            factures = self.db.get_all_factures()
            self.facture_filter_label.config(text="Toutes les factures")

        today = date.today().isoformat()

        for f in factures:
            date_str = f['date_facture'][:10] if f['date_facture'] else ''
            echeance = f['date_paiement_max'][:10] if f['date_paiement_max'] else ''
            prix = f"{f['prix_ttc']:.2f}" if f['prix_ttc'] else ''

            # Déterminer le statut
            if f['payee']:
                statut = "Payee"
                tag = 'payee'
            elif f['date_paiement_max'] and f['date_paiement_max'] < today:
                statut = "EN RETARD"
                tag = 'impayee'
            else:
                statut = "A payer"
                tag = ''

            self.factures_tree.insert('', tk.END, iid=f['id'], values=(
                f['id'],
                f['numero_facture'] or '',
                f['societe_emettrice_nom'] or '',
                f['societe_destinatrice_nom'] or '',
                date_str,
                prix,
                echeance,
                statut
            ), tags=(tag,))

    def _load_evolution(self, societe_id: int):
        """Charge l'évolution pour une société."""
        for item in self.evolution_tree.get_children():
            self.evolution_tree.delete(item)

        evolution = self.db.get_evolution_by_societe(societe_id)

        total_ht = 0
        total_ttc = 0
        total_factures = 0

        for e in evolution:
            ht = e['total_ht'] or 0
            ttc = e['total_ttc'] or 0
            total_ht += ht
            total_ttc += ttc
            total_factures += e['nb_factures']

            self.evolution_tree.insert('', tk.END, values=(
                e['mois'],
                e['nb_factures'],
                f"{ht:.2f} EUR",
                f"{ttc:.2f} EUR"
            ))

        self.evolution_summary.config(
            text=f"Total: {total_factures} factures | {total_ht:.2f} EUR HT | {total_ttc:.2f} EUR TTC"
        )

    def _update_stats(self):
        """Met à jour les statistiques."""
        stats = self.db.get_stats_globales()

        self.stats_labels['nb_societes'].config(text=str(stats['nb_societes']))
        self.stats_labels['nb_contrats'].config(text=str(stats['nb_contrats']))
        self.stats_labels['nb_factures'].config(text=str(stats['nb_factures']))
        self.stats_labels['total_facture'].config(text=f"{stats['total_facture']:.2f} EUR")

        # Colorer en rouge si factures impayées
        if stats['nb_factures_impayees'] > 0:
            self.stats_labels['nb_factures_impayees'].config(
                text=str(stats['nb_factures_impayees']),
                style='Warning.TLabel'
            )
        else:
            self.stats_labels['nb_factures_impayees'].config(
                text="0",
                style='Success.TLabel'
            )

    # === Événements ===

    def _on_societe_select(self, event):
        """Gère la sélection d'une société."""
        selection = self.societes_tree.selection()
        if selection:
            self.current_societe_id = int(selection[0])
            self._load_contrats(self.current_societe_id)
            self._load_factures(self.current_societe_id)
            self._load_evolution(self.current_societe_id)

    def _on_societe_double_click(self, event):
        """Double-clic sur une société."""
        self._on_societe_select(event)
        self.notebook.select(0)  # Aller à l'onglet Contrats

    def _on_contrat_select(self, event):
        """Gère la sélection d'un contrat."""
        selection = self.contrats_tree.selection()
        if selection:
            contrat_id = int(selection[0])
            self.current_contrat_id = contrat_id
            contrat = self.db.get_contrat(contrat_id)

            if contrat:
                prix_str = f"{contrat['prix_ht']:.2f} EUR" if contrat['prix_ht'] else 'N/A'
                details = f"""Designation: {contrat['designation'] or 'N/A'}
Emetteur: {contrat['societe_emettrice_nom'] or 'N/A'}
Client: {contrat['societe_receptrice_nom'] or 'N/A'}
Objet: {contrat['objet'] or 'N/A'}
Signataire: {contrat['signataire'] or 'N/A'}
Prix HT: {prix_str}
Engagement: {contrat['engagement'] or 'N/A'}
Confiance: {contrat['confiance']}%"""

                self.contrat_detail_text.config(state=tk.NORMAL)
                self.contrat_detail_text.delete('1.0', tk.END)
                self.contrat_detail_text.insert('1.0', details)
                self.contrat_detail_text.config(state=tk.DISABLED)

    def _on_contrat_double_click(self, event):
        """Double-clic sur un contrat : affiche les factures liées."""
        selection = self.contrats_tree.selection()
        if selection:
            contrat_id = int(selection[0])
            self._load_factures(contrat_id=contrat_id)
            self.notebook.select(1)  # Aller à l'onglet Factures

    def _on_facture_double_click(self, event):
        """Double-clic sur une facture."""
        selection = self.factures_tree.selection()
        if selection:
            facture_id = int(selection[0])
            facture = self.db.get_facture(facture_id)

            if facture:
                prix_ht = f"{facture['prix_ht']:.2f} EUR" if facture['prix_ht'] else 'N/A'
                tva = f"{facture['tva']:.2f} EUR" if facture['tva'] else 'N/A'
                prix_ttc = f"{facture['prix_ttc']:.2f} EUR" if facture['prix_ttc'] else 'N/A'

                details = f"""Numero: {facture['numero_facture'] or 'N/A'}
Emetteur: {facture['societe_emettrice_nom'] or 'N/A'}
Destinataire: {facture['societe_destinatrice_nom'] or 'N/A'}
Prestation: {facture['designation_prestation'] or 'N/A'}
Prix HT: {prix_ht} | TVA: {tva} | TTC: {prix_ttc}
Periode: {facture['duree_prestation'] or 'N/A'}
Contrat lie: {facture['contrat_designation'] or 'Aucun'}"""

                self.facture_detail_text.config(state=tk.NORMAL)
                self.facture_detail_text.delete('1.0', tk.END)
                self.facture_detail_text.insert('1.0', details)
                self.facture_detail_text.config(state=tk.DISABLED)

    # === Actions ===

    def _import_contrat(self):
        """Importe un contrat depuis un fichier."""
        filetypes = [
            ('Documents PDF', '*.pdf'),
            ('Documents Word', '*.docx'),
            ('Tous les fichiers', '*.*')
        ]
        filepath = filedialog.askopenfilename(
            title="Importer un contrat",
            filetypes=filetypes
        )

        if filepath:
            try:
                self._set_status(f"Analyse du contrat: {os.path.basename(filepath)}...")
                contract = self.contract_parser.parse(filepath)
                contrat_id = self.db.save_contract(contract)

                messagebox.showinfo(
                    "Import reussi",
                    f"Contrat importe avec succes!\n\n"
                    f"Designation: {contract.designation or 'N/A'}\n"
                    f"Emetteur: {contract.societe_emettrice or 'N/A'}\n"
                    f"Client: {contract.societe_receptrice or 'N/A'}\n"
                    f"Prix HT: {contract.prix_ht or 'N/A'} EUR\n"
                    f"Confiance: {contract.confiance}%"
                )

                self._refresh_all()

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import:\n{str(e)}")
            finally:
                self._set_status("Pret")

    def _import_facture(self):
        """Importe une facture depuis un fichier."""
        filetypes = [
            ('Documents PDF', '*.pdf'),
            ('Documents Word', '*.docx'),
            ('Tous les fichiers', '*.*')
        ]
        filepath = filedialog.askopenfilename(
            title="Importer une facture",
            filetypes=filetypes
        )

        if filepath:
            try:
                self._set_status(f"Analyse de la facture: {os.path.basename(filepath)}...")
                invoice = self.invoice_parser.parse(filepath)
                facture_id = self.db.save_invoice(invoice)

                messagebox.showinfo(
                    "Import reussi",
                    f"Facture importee avec succes!\n\n"
                    f"Numero: {invoice.numero_facture or 'N/A'}\n"
                    f"Emetteur: {invoice.societe_emettrice or 'N/A'}\n"
                    f"Destinataire: {invoice.societe_destinatrice or 'N/A'}\n"
                    f"Prix TTC: {invoice.prix_ttc or 'N/A'} EUR\n"
                    f"Confiance: {invoice.confiance}%"
                )

                self._refresh_all()

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import:\n{str(e)}")
            finally:
                self._set_status("Pret")

    def _import_multiple(self):
        """Importe plusieurs fichiers."""
        filetypes = [
            ('Documents PDF', '*.pdf'),
            ('Documents Word', '*.docx'),
            ('Tous les fichiers', '*.*')
        ]
        filepaths = filedialog.askopenfilenames(
            title="Importer des documents",
            filetypes=filetypes
        )

        if filepaths:
            imported = 0
            errors = 0

            for filepath in filepaths:
                try:
                    self._set_status(f"Analyse: {os.path.basename(filepath)}...")

                    # Détection automatique
                    filename_lower = os.path.basename(filepath).lower()
                    if 'facture' in filename_lower or 'invoice' in filename_lower:
                        invoice = self.invoice_parser.parse(filepath)
                        self.db.save_invoice(invoice)
                    elif 'contrat' in filename_lower or 'contract' in filename_lower:
                        contract = self.contract_parser.parse(filepath)
                        self.db.save_contract(contract)
                    else:
                        # Essayer les deux et prendre le meilleur
                        contract = self.contract_parser.parse(filepath)
                        invoice = self.invoice_parser.parse(filepath)

                        if invoice.confiance > contract.confiance:
                            self.db.save_invoice(invoice)
                        else:
                            self.db.save_contract(contract)

                    imported += 1

                except Exception as e:
                    errors += 1

            messagebox.showinfo(
                "Import termine",
                f"Import termine!\n\n"
                f"Documents importes: {imported}\n"
                f"Erreurs: {errors}"
            )

            self._refresh_all()
            self._set_status("Pret")

    def _mark_facture_payee(self):
        """Marque la facture sélectionnée comme payée."""
        selection = self.factures_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Selectionnez une facture")
            return

        facture_id = int(selection[0])
        if messagebox.askyesno("Confirmation", "Marquer cette facture comme payee?"):
            self.db.mark_facture_payee(facture_id)
            self._refresh_all()

    def _link_facture_to_contrat(self):
        """Lie une facture à un contrat."""
        selection = self.factures_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Selectionnez une facture")
            return

        facture_id = int(selection[0])

        # Fenêtre de sélection du contrat
        dialog = tk.Toplevel(self.root)
        dialog.title("Lier a un contrat")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Selectionnez le contrat:").pack(pady=10)

        # Liste des contrats
        contrats = self.db.get_all_contrats()

        listbox = tk.Listbox(dialog, width=50, height=10)
        listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        for c in contrats:
            label = f"{c['id']} - {c['designation'] or 'Sans titre'} ({c['societe_emettrice_nom'] or 'N/A'})"
            listbox.insert(tk.END, label)

        def confirm():
            sel = listbox.curselection()
            if sel:
                contrat_id = contrats[sel[0]]['id']
                self.db.link_facture_to_contrat(facture_id, contrat_id)
                dialog.destroy()
                self._refresh_all()
                messagebox.showinfo("Succes", "Facture liee au contrat")

        ttk.Button(dialog, text="Confirmer", command=confirm).pack(pady=10)

    def _show_all_contrats(self):
        """Affiche tous les contrats."""
        self.current_societe_id = None
        self._load_contrats()

    def _show_all_factures(self):
        """Affiche toutes les factures."""
        self._load_factures()

    def _show_factures_impayees(self):
        """Affiche les factures impayées."""
        for item in self.factures_tree.get_children():
            self.factures_tree.delete(item)

        factures = self.db.get_factures_impayees()
        self.facture_filter_label.config(text=f"Factures impayees ({len(factures)})")

        for f in factures:
            date_str = f['date_facture'][:10] if f['date_facture'] else ''
            echeance = f['date_paiement_max'][:10] if f['date_paiement_max'] else ''
            prix = f"{f['prix_ttc']:.2f}" if f['prix_ttc'] else ''
            jours = int(f['jours_retard']) if f['jours_retard'] else 0

            self.factures_tree.insert('', tk.END, iid=f['id'], values=(
                f['id'],
                f['numero_facture'] or '',
                f['societe_emettrice_nom'] or '',
                f['societe_destinatrice_nom'] or '',
                date_str,
                prix,
                echeance,
                f"{jours}j retard"
            ), tags=('impayee',))

        self.notebook.select(1)  # Onglet Factures

    def _export_data(self):
        """Exporte les données."""
        filepath = filedialog.asksaveasfilename(
            title="Exporter les donnees",
            defaultextension=".json",
            filetypes=[('JSON', '*.json'), ('Tous les fichiers', '*.*')]
        )

        if filepath:
            import json

            data = {
                'societes': self.db.get_all_societes(),
                'contrats': self.db.get_all_contrats(),
                'factures': self.db.get_all_factures(),
                'stats': self.db.get_stats_globales()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            messagebox.showinfo("Export", f"Donnees exportees vers:\n{filepath}")

    def _show_about(self):
        """Affiche la boîte À propos."""
        messagebox.showinfo(
            "A propos",
            "CLM Reader v1.0.0\n\n"
            "Outil de lecture et suivi des contrats et factures.\n\n"
            "Fonctionnalites:\n"
            "- Import de contrats et factures (PDF, DOCX)\n"
            "- Extraction automatique des informations\n"
            "- Suivi des paiements\n"
            "- Evolution par societe/contrat\n\n"
            "2024"
        )

    def run(self):
        """Lance l'application."""
        self.root.mainloop()

    def close(self):
        """Ferme proprement l'application."""
        self.db.close()
        self.root.destroy()


def main():
    """Point d'entrée de l'application GUI."""
    app = MainWindow()
    try:
        app.run()
    finally:
        app.close()


if __name__ == '__main__':
    main()
