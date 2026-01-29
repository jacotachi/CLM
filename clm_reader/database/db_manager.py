"""Module de base de données pour la persistance des contrats et factures."""

import sqlite3
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from pathlib import Path

from ..models.contract import Contract
from ..models.invoice import Invoice


def get_default_db_path() -> str:
    """Retourne le chemin par défaut de la base de données."""
    # Utiliser le dossier AppData sur Windows, sinon le home
    if os.name == 'nt':  # Windows
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        db_dir = os.path.join(app_data, 'CLMReader')
    else:
        db_dir = os.path.join(os.path.expanduser('~'), '.clm_reader')

    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, 'clm_data.db')


class Database:
    """Gestionnaire de base de données SQLite pour CLM Reader."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialise la connexion à la base de données.

        Args:
            db_path: Chemin vers le fichier de base de données
        """
        self.db_path = db_path or get_default_db_path()
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Établit la connexion à la base de données."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # Activer les clés étrangères
        self.conn.execute("PRAGMA foreign_keys = ON")

    def _create_tables(self):
        """Crée les tables si elles n'existent pas."""
        cursor = self.conn.cursor()

        # Table des sociétés
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS societes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL UNIQUE,
                siret TEXT,
                adresse TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table des contrats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contrats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                societe_emettrice_id INTEGER,
                societe_receptrice_id INTEGER,
                designation TEXT,
                objet TEXT,
                signataire TEXT,
                prix_ht REAL,
                quantite TEXT,
                engagement TEXT,
                date_signature DATE,
                date_debut DATE,
                date_fin DATE,
                fichier_source TEXT,
                confiance INTEGER DEFAULT 0,
                date_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                actif INTEGER DEFAULT 1,
                FOREIGN KEY (societe_emettrice_id) REFERENCES societes(id),
                FOREIGN KEY (societe_receptrice_id) REFERENCES societes(id)
            )
        ''')

        # Table des factures
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS factures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contrat_id INTEGER,
                societe_emettrice_id INTEGER,
                societe_destinatrice_id INTEGER,
                numero_facture TEXT,
                designation_prestation TEXT,
                prix_ht REAL,
                tva REAL,
                prix_ttc REAL,
                quantite TEXT,
                date_facture DATE,
                date_paiement_max DATE,
                duree_prestation TEXT,
                fichier_source TEXT,
                confiance INTEGER DEFAULT 0,
                date_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payee INTEGER DEFAULT 0,
                date_paiement DATE,
                notes TEXT,
                FOREIGN KEY (contrat_id) REFERENCES contrats(id),
                FOREIGN KEY (societe_emettrice_id) REFERENCES societes(id),
                FOREIGN KEY (societe_destinatrice_id) REFERENCES societes(id)
            )
        ''')

        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contrats_societe_em ON contrats(societe_emettrice_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contrats_societe_rec ON contrats(societe_receptrice_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_factures_contrat ON factures(contrat_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_factures_date ON factures(date_facture)')

        self.conn.commit()

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()

    # === Gestion des sociétés ===

    def get_or_create_societe(self, nom: str, siret: Optional[str] = None) -> int:
        """
        Récupère ou crée une société.

        Args:
            nom: Nom de la société
            siret: Numéro SIRET (optionnel)

        Returns:
            ID de la société
        """
        if not nom:
            return None

        cursor = self.conn.cursor()

        # Chercher si la société existe
        cursor.execute('SELECT id FROM societes WHERE nom = ?', (nom,))
        row = cursor.fetchone()

        if row:
            return row['id']

        # Créer la société
        cursor.execute(
            'INSERT INTO societes (nom, siret) VALUES (?, ?)',
            (nom, siret)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_all_societes(self) -> List[dict]:
        """Retourne toutes les sociétés."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.*,
                   COUNT(DISTINCT c.id) as nb_contrats,
                   COUNT(DISTINCT f.id) as nb_factures,
                   COALESCE(SUM(f.prix_ttc), 0) as total_facture
            FROM societes s
            LEFT JOIN contrats c ON s.id = c.societe_emettrice_id OR s.id = c.societe_receptrice_id
            LEFT JOIN factures f ON s.id = f.societe_emettrice_id OR s.id = f.societe_destinatrice_id
            GROUP BY s.id
            ORDER BY s.nom
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def get_societe(self, societe_id: int) -> Optional[dict]:
        """Récupère une société par son ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM societes WHERE id = ?', (societe_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # === Gestion des contrats ===

    def save_contract(self, contract: Contract, societe_emettrice_id: Optional[int] = None,
                      societe_receptrice_id: Optional[int] = None) -> int:
        """
        Sauvegarde un contrat dans la base de données.

        Args:
            contract: Objet Contract à sauvegarder
            societe_emettrice_id: ID de la société émettrice (si déjà connu)
            societe_receptrice_id: ID de la société réceptrice (si déjà connu)

        Returns:
            ID du contrat créé
        """
        # Créer ou récupérer les sociétés
        if societe_emettrice_id is None and contract.societe_emettrice:
            societe_emettrice_id = self.get_or_create_societe(contract.societe_emettrice)

        if societe_receptrice_id is None and contract.societe_receptrice:
            societe_receptrice_id = self.get_or_create_societe(contract.societe_receptrice)

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO contrats (
                societe_emettrice_id, societe_receptrice_id, designation, objet,
                signataire, prix_ht, quantite, engagement, date_signature,
                date_debut, date_fin, fichier_source, confiance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            societe_emettrice_id,
            societe_receptrice_id,
            contract.designation,
            contract.objet,
            contract.signataire,
            float(contract.prix_ht) if contract.prix_ht else None,
            contract.quantite,
            contract.engagement,
            contract.date_signature.isoformat() if contract.date_signature else None,
            contract.date_debut.isoformat() if contract.date_debut else None,
            contract.date_fin.isoformat() if contract.date_fin else None,
            contract.fichier_source,
            contract.confiance
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_all_contrats(self) -> List[dict]:
        """Retourne tous les contrats avec les noms des sociétés."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.*,
                   se.nom as societe_emettrice_nom,
                   sr.nom as societe_receptrice_nom,
                   COUNT(f.id) as nb_factures,
                   COALESCE(SUM(f.prix_ttc), 0) as total_facture
            FROM contrats c
            LEFT JOIN societes se ON c.societe_emettrice_id = se.id
            LEFT JOIN societes sr ON c.societe_receptrice_id = sr.id
            LEFT JOIN factures f ON f.contrat_id = c.id
            GROUP BY c.id
            ORDER BY c.date_import DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def get_contrats_by_societe(self, societe_id: int) -> List[dict]:
        """Retourne les contrats d'une société."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.*,
                   se.nom as societe_emettrice_nom,
                   sr.nom as societe_receptrice_nom,
                   COUNT(f.id) as nb_factures,
                   COALESCE(SUM(f.prix_ttc), 0) as total_facture
            FROM contrats c
            LEFT JOIN societes se ON c.societe_emettrice_id = se.id
            LEFT JOIN societes sr ON c.societe_receptrice_id = sr.id
            LEFT JOIN factures f ON f.contrat_id = c.id
            WHERE c.societe_emettrice_id = ? OR c.societe_receptrice_id = ?
            GROUP BY c.id
            ORDER BY c.date_signature DESC
        ''', (societe_id, societe_id))
        return [dict(row) for row in cursor.fetchall()]

    def get_contrat(self, contrat_id: int) -> Optional[dict]:
        """Récupère un contrat par son ID."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.*,
                   se.nom as societe_emettrice_nom,
                   sr.nom as societe_receptrice_nom
            FROM contrats c
            LEFT JOIN societes se ON c.societe_emettrice_id = se.id
            LEFT JOIN societes sr ON c.societe_receptrice_id = sr.id
            WHERE c.id = ?
        ''', (contrat_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_contrat(self, contrat_id: int, **kwargs) -> bool:
        """Met à jour un contrat."""
        if not kwargs:
            return False

        fields = ', '.join(f'{k} = ?' for k in kwargs.keys())
        values = list(kwargs.values()) + [contrat_id]

        cursor = self.conn.cursor()
        cursor.execute(f'UPDATE contrats SET {fields} WHERE id = ?', values)
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_contrat(self, contrat_id: int) -> bool:
        """Supprime un contrat."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM contrats WHERE id = ?', (contrat_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # === Gestion des factures ===

    def save_invoice(self, invoice: Invoice, contrat_id: Optional[int] = None,
                     societe_emettrice_id: Optional[int] = None,
                     societe_destinatrice_id: Optional[int] = None) -> int:
        """
        Sauvegarde une facture dans la base de données.

        Args:
            invoice: Objet Invoice à sauvegarder
            contrat_id: ID du contrat associé (optionnel)
            societe_emettrice_id: ID de la société émettrice
            societe_destinatrice_id: ID de la société destinatrice

        Returns:
            ID de la facture créée
        """
        # Créer ou récupérer les sociétés
        if societe_emettrice_id is None and invoice.societe_emettrice:
            societe_emettrice_id = self.get_or_create_societe(invoice.societe_emettrice)

        if societe_destinatrice_id is None and invoice.societe_destinatrice:
            societe_destinatrice_id = self.get_or_create_societe(invoice.societe_destinatrice)

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO factures (
                contrat_id, societe_emettrice_id, societe_destinatrice_id,
                numero_facture, designation_prestation, prix_ht, tva, prix_ttc,
                quantite, date_facture, date_paiement_max, duree_prestation,
                fichier_source, confiance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            contrat_id,
            societe_emettrice_id,
            societe_destinatrice_id,
            invoice.numero_facture,
            invoice.designation_prestation,
            float(invoice.prix_ht) if invoice.prix_ht else None,
            float(invoice.tva) if invoice.tva else None,
            float(invoice.prix_ttc) if invoice.prix_ttc else None,
            invoice.quantite,
            invoice.date_facture.isoformat() if invoice.date_facture else None,
            invoice.date_paiement_max.isoformat() if invoice.date_paiement_max else None,
            invoice.duree_prestation,
            invoice.fichier_source,
            invoice.confiance
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_all_factures(self) -> List[dict]:
        """Retourne toutes les factures."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT f.*,
                   se.nom as societe_emettrice_nom,
                   sd.nom as societe_destinatrice_nom,
                   c.designation as contrat_designation
            FROM factures f
            LEFT JOIN societes se ON f.societe_emettrice_id = se.id
            LEFT JOIN societes sd ON f.societe_destinatrice_id = sd.id
            LEFT JOIN contrats c ON f.contrat_id = c.id
            ORDER BY f.date_facture DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def get_factures_by_contrat(self, contrat_id: int) -> List[dict]:
        """Retourne les factures d'un contrat."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT f.*,
                   se.nom as societe_emettrice_nom,
                   sd.nom as societe_destinatrice_nom
            FROM factures f
            LEFT JOIN societes se ON f.societe_emettrice_id = se.id
            LEFT JOIN societes sd ON f.societe_destinatrice_id = sd.id
            WHERE f.contrat_id = ?
            ORDER BY f.date_facture DESC
        ''', (contrat_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_factures_by_societe(self, societe_id: int) -> List[dict]:
        """Retourne les factures d'une société."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT f.*,
                   se.nom as societe_emettrice_nom,
                   sd.nom as societe_destinatrice_nom,
                   c.designation as contrat_designation
            FROM factures f
            LEFT JOIN societes se ON f.societe_emettrice_id = se.id
            LEFT JOIN societes sd ON f.societe_destinatrice_id = sd.id
            LEFT JOIN contrats c ON f.contrat_id = c.id
            WHERE f.societe_emettrice_id = ? OR f.societe_destinatrice_id = ?
            ORDER BY f.date_facture DESC
        ''', (societe_id, societe_id))
        return [dict(row) for row in cursor.fetchall()]

    def get_facture(self, facture_id: int) -> Optional[dict]:
        """Récupère une facture par son ID."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT f.*,
                   se.nom as societe_emettrice_nom,
                   sd.nom as societe_destinatrice_nom,
                   c.designation as contrat_designation
            FROM factures f
            LEFT JOIN societes se ON f.societe_emettrice_id = se.id
            LEFT JOIN societes sd ON f.societe_destinatrice_id = sd.id
            LEFT JOIN contrats c ON f.contrat_id = c.id
            WHERE f.id = ?
        ''', (facture_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_facture(self, facture_id: int, **kwargs) -> bool:
        """Met à jour une facture."""
        if not kwargs:
            return False

        fields = ', '.join(f'{k} = ?' for k in kwargs.keys())
        values = list(kwargs.values()) + [facture_id]

        cursor = self.conn.cursor()
        cursor.execute(f'UPDATE factures SET {fields} WHERE id = ?', values)
        self.conn.commit()
        return cursor.rowcount > 0

    def mark_facture_payee(self, facture_id: int, date_paiement: Optional[date] = None) -> bool:
        """Marque une facture comme payée."""
        if date_paiement is None:
            date_paiement = date.today()

        return self.update_facture(
            facture_id,
            payee=1,
            date_paiement=date_paiement.isoformat()
        )

    def delete_facture(self, facture_id: int) -> bool:
        """Supprime une facture."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM factures WHERE id = ?', (facture_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # === Statistiques et rapports ===

    def get_evolution_by_societe(self, societe_id: int) -> List[dict]:
        """
        Retourne l'évolution des factures par mois pour une société.

        Args:
            societe_id: ID de la société

        Returns:
            Liste avec mois, total HT, total TTC, nombre de factures
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                strftime('%Y-%m', date_facture) as mois,
                SUM(prix_ht) as total_ht,
                SUM(prix_ttc) as total_ttc,
                COUNT(*) as nb_factures
            FROM factures
            WHERE (societe_emettrice_id = ? OR societe_destinatrice_id = ?)
              AND date_facture IS NOT NULL
            GROUP BY strftime('%Y-%m', date_facture)
            ORDER BY mois
        ''', (societe_id, societe_id))
        return [dict(row) for row in cursor.fetchall()]

    def get_evolution_by_contrat(self, contrat_id: int) -> List[dict]:
        """Retourne l'évolution des factures par mois pour un contrat."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT
                strftime('%Y-%m', date_facture) as mois,
                SUM(prix_ht) as total_ht,
                SUM(prix_ttc) as total_ttc,
                COUNT(*) as nb_factures
            FROM factures
            WHERE contrat_id = ? AND date_facture IS NOT NULL
            GROUP BY strftime('%Y-%m', date_facture)
            ORDER BY mois
        ''', (contrat_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_factures_impayees(self) -> List[dict]:
        """Retourne les factures impayées et en retard."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT f.*,
                   se.nom as societe_emettrice_nom,
                   sd.nom as societe_destinatrice_nom,
                   julianday('now') - julianday(date_paiement_max) as jours_retard
            FROM factures f
            LEFT JOIN societes se ON f.societe_emettrice_id = se.id
            LEFT JOIN societes sd ON f.societe_destinatrice_id = sd.id
            WHERE f.payee = 0
              AND f.date_paiement_max IS NOT NULL
              AND f.date_paiement_max < date('now')
            ORDER BY f.date_paiement_max
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def get_stats_globales(self) -> dict:
        """Retourne les statistiques globales."""
        cursor = self.conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM societes')
        nb_societes = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM contrats')
        nb_contrats = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM factures')
        nb_factures = cursor.fetchone()[0]

        cursor.execute('SELECT COALESCE(SUM(prix_ttc), 0) FROM factures')
        total_facture = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM factures WHERE payee = 0 AND date_paiement_max < date("now")')
        nb_impayees = cursor.fetchone()[0]

        return {
            'nb_societes': nb_societes,
            'nb_contrats': nb_contrats,
            'nb_factures': nb_factures,
            'total_facture': total_facture,
            'nb_factures_impayees': nb_impayees
        }

    def link_facture_to_contrat(self, facture_id: int, contrat_id: int) -> bool:
        """Lie une facture à un contrat."""
        return self.update_facture(facture_id, contrat_id=contrat_id)

    def search(self, query: str) -> dict:
        """
        Recherche dans les sociétés, contrats et factures.

        Args:
            query: Terme de recherche

        Returns:
            Dictionnaire avec les résultats par catégorie
        """
        pattern = f'%{query}%'
        cursor = self.conn.cursor()

        # Recherche sociétés
        cursor.execute(
            'SELECT * FROM societes WHERE nom LIKE ? OR siret LIKE ?',
            (pattern, pattern)
        )
        societes = [dict(row) for row in cursor.fetchall()]

        # Recherche contrats
        cursor.execute('''
            SELECT c.*, se.nom as societe_emettrice_nom, sr.nom as societe_receptrice_nom
            FROM contrats c
            LEFT JOIN societes se ON c.societe_emettrice_id = se.id
            LEFT JOIN societes sr ON c.societe_receptrice_id = sr.id
            WHERE c.designation LIKE ? OR c.objet LIKE ? OR se.nom LIKE ? OR sr.nom LIKE ?
        ''', (pattern, pattern, pattern, pattern))
        contrats = [dict(row) for row in cursor.fetchall()]

        # Recherche factures
        cursor.execute('''
            SELECT f.*, se.nom as societe_emettrice_nom, sd.nom as societe_destinatrice_nom
            FROM factures f
            LEFT JOIN societes se ON f.societe_emettrice_id = se.id
            LEFT JOIN societes sd ON f.societe_destinatrice_id = sd.id
            WHERE f.numero_facture LIKE ? OR f.designation_prestation LIKE ?
                  OR se.nom LIKE ? OR sd.nom LIKE ?
        ''', (pattern, pattern, pattern, pattern))
        factures = [dict(row) for row in cursor.fetchall()]

        return {
            'societes': societes,
            'contrats': contrats,
            'factures': factures
        }
