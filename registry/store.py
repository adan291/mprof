import os
import sqlite3
import unicodedata


def normalize_text(text):
    """Normaliza el texto eliminando tildes y pasando a minúsculas."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()


class RegistryStore:
    """Registro genérico de entradas: cada entrada tiene una categoría,
    un nombre, un enlace y un proveedor (con su user_id de Discord)."""

    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()
        self._migrate_from_crafters()
        self._migrate_from_legacy_file()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self._connect() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    category      TEXT NOT NULL,
                    name          TEXT NOT NULL,
                    link          TEXT NOT NULL,
                    norm_category TEXT NOT NULL,
                    norm_name     TEXT NOT NULL,
                    provider      TEXT NOT NULL,
                    user_id       INTEGER NOT NULL
                )
            ''')
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_entries_cat_name '
                'ON entries (norm_category, norm_name)'
            )
            conn.commit()

    def _migrate_from_crafters(self):
        """Copia datos de la tabla antigua 'crafters' si existe y 'entries' está vacía."""
        with self._connect() as conn:
            has_old = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='crafters'"
            ).fetchone()
            if not has_old:
                return
            count = conn.execute('SELECT COUNT(*) FROM entries').fetchone()[0]
            if count > 0:
                return
            rows = conn.execute(
                'SELECT category, item_name, item_link, normalized_category, '
                'normalized_item_name, character_name, user_id FROM crafters'
            ).fetchall()
            conn.executemany(
                'INSERT INTO entries (category, name, link, norm_category, norm_name, provider, user_id) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                rows
            )
            conn.commit()
            print(f"Migradas {len(rows)} entradas desde la tabla 'crafters'.")

    def _migrate_from_legacy_file(self):
        """Migra desde un archivo antiguo 'crafters_db.sqlite' en el mismo directorio,
        si existe y 'entries' está vacía."""
        legacy_path = os.path.join(os.path.dirname(self.db_path), "crafters_db.sqlite")
        if not os.path.exists(legacy_path):
            return
        with self._connect() as conn:
            count = conn.execute('SELECT COUNT(*) FROM entries').fetchone()[0]
            if count > 0:
                return
        try:
            with sqlite3.connect(legacy_path) as legacy:
                has_old = legacy.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='crafters'"
                ).fetchone()
                if not has_old:
                    return
                rows = legacy.execute(
                    'SELECT category, item_name, item_link, normalized_category, '
                    'normalized_item_name, character_name, user_id FROM crafters'
                ).fetchall()
            with self._connect() as conn:
                conn.executemany(
                    'INSERT INTO entries (category, name, link, norm_category, norm_name, provider, user_id) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)',
                    rows
                )
                conn.commit()
            print(f"Migradas {len(rows)} entradas desde '{legacy_path}'.")
        except sqlite3.Error as e:
            print(f"No se pudo migrar desde el archivo antiguo: {e}")

    def add(self, provider, category, name, link, user_id):
        """Añade una entrada. Devuelve True si se añadió, False si ya existía."""
        norm_category = normalize_text(category)
        norm_name = normalize_text(name)
        with self._connect() as conn:
            exists = conn.execute(
                'SELECT 1 FROM entries WHERE norm_category = ? AND norm_name = ? '
                'AND link = ? AND user_id = ?',
                (norm_category, norm_name, link, user_id)
            ).fetchone()
            if exists:
                return False
            conn.execute(
                'INSERT INTO entries (category, name, link, norm_category, norm_name, provider, user_id) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (category, name, link, norm_category, norm_name, provider, user_id)
            )
            conn.commit()
            return True

    def search(self, category, name):
        """Busca entradas por categoría y nombre (coincidencia parcial).
        Devuelve [(name, link, [providers...]), ...]."""
        norm_category = normalize_text(category)
        norm_name = normalize_text(name)
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT name, link, GROUP_CONCAT(provider, ", ") '
                'FROM entries WHERE norm_category = ? AND norm_name LIKE ? '
                'GROUP BY name, link',
                (norm_category, f'%{norm_name}%')
            ).fetchall()
        return [(r[0], r[1], r[2].split(", ")) for r in rows]

    def list_all(self):
        """Lista todas las entradas agrupadas. Devuelve [(category, name, link, [providers...]), ...]."""
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT category, name, link, GROUP_CONCAT(provider, ", ") '
                'FROM entries GROUP BY category, name, link ORDER BY category, name'
            ).fetchall()
        return [(r[0], r[1], r[2], r[3].split(", ")) for r in rows]

    def delete(self, provider, category, name, link, user_id):
        """Elimina una entrada propia. Devuelve 'deleted', 'not_found' o 'no_permission'."""
        norm_category = normalize_text(category)
        norm_name = normalize_text(name)
        with self._connect() as conn:
            row = conn.execute(
                'SELECT user_id FROM entries WHERE provider = ? AND norm_category = ? '
                'AND norm_name = ? AND link = ?',
                (provider, norm_category, norm_name, link)
            ).fetchone()
            if row is None:
                return 'not_found'
            if row[0] != user_id:
                return 'no_permission'
            conn.execute(
                'DELETE FROM entries WHERE provider = ? AND norm_category = ? '
                'AND norm_name = ? AND link = ? AND user_id = ?',
                (provider, norm_category, norm_name, link, user_id)
            )
            conn.commit()
            return 'deleted'
