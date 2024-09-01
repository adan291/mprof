# database.py

import os
import sqlite3
import unicodedata
from profesiones import VALID_CATEGORIES

def normalize_text(text):
    """Normaliza el texto eliminando acentos y caracteres especiales y hace todo minúscula."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def create_db(db_path):
    """Crea la base de datos y la tabla si no existen"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if not os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS crafters (
                    category TEXT,
                    item_name TEXT,
                    item_link TEXT,
                    normalized_item_name TEXT,
                    normalized_category TEXT,
                    character_name TEXT,
                    user_id INTEGER
                )
            ''')
            conn.commit()

def add_crafter(db_path, character_name, category, item_name, item_link, user_id):
    """Añade un artesano a la base de datos.
       Devuelve True si el artesano fue añadido, False si ya estaba registrado."""
    normalized_category = normalize_text(category)
    normalized_item_name = normalize_text(item_name)

    if normalized_category not in VALID_CATEGORIES:
        return False

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT character_name FROM crafters
            WHERE normalized_category = ? AND normalized_item_name = ? AND item_link = ? AND user_id = ?
        ''', (normalized_category, normalized_item_name, item_link, user_id))

        if c.fetchone() is None:
            c.execute('''
                INSERT INTO crafters (category, item_name, item_link, normalized_item_name, normalized_category, character_name, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (category, item_name, item_link, normalized_item_name, normalized_category, character_name, user_id))
            conn.commit()
            return True
        else:
            return False

def get_crafters(db_path, category, item_name):
    """Obtiene los artesanos y el enlace del objeto en una categoría.
       Permite búsquedas parciales en el nombre del objeto."""
    normalized_category = normalize_text(category)
    normalized_item_name = normalize_text(item_name)

    if normalized_category not in VALID_CATEGORIES:
        return []

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        if ' ' in item_name:
            c.execute('''
                SELECT character_name, item_link FROM crafters
                WHERE normalized_category = ? AND normalized_item_name = ?
            ''', (normalized_category, normalized_item_name))
            results = [(item_name, c.fetchall())]
        else:
            c.execute('''
                SELECT DISTINCT item_name FROM crafters
                WHERE normalized_category = ? AND normalized_item_name LIKE ?
            ''', (normalized_category, f'%{normalized_item_name}%'))
            item_names = c.fetchall()

            results = []
            for (item_name,) in item_names:
                normalized_item_name = normalize_text(item_name)
                c.execute('''
                    SELECT character_name, item_link FROM crafters
                    WHERE normalized_category = ? AND normalized_item_name = ?
                ''', (normalized_category, normalized_item_name))
                results.append((item_name, c.fetchall()))

        return results

def list_all_crafters(db_path):
    """Obtiene una lista de todos los artesanos y objetos registrados."""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT category, item_name, item_link, GROUP_CONCAT(character_name, ', ') as crafters
            FROM crafters
            GROUP BY category, item_name, item_link
        ''')
        return c.fetchall()

def delete_crafter(db_path, character_name, category, item_name, item_link, user_id):
    """Elimina un artesano de la base de datos.
       Devuelve 'deleted', 'not_found' o 'no_permission' según corresponda."""
    normalized_category = normalize_text(category)
    normalized_item_name = normalize_text(item_name)

    if normalized_category not in VALID_CATEGORIES:
        return 'not_found'

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT user_id FROM crafters
            WHERE character_name = ? AND normalized_category = ? AND normalized_item_name = ? AND item_link = ?
        ''', (character_name, normalized_category, normalized_item_name, item_link))
        result = c.fetchone()

        if result is None:
            return 'not_found'
        elif result[0] != user_id:
            return 'no_permission'
        else:
            c.execute('''
                DELETE FROM crafters
                WHERE character_name = ? AND normalized_category = ? AND normalized_item_name = ? AND item_link = ? AND user_id = ?
            ''', (character_name, normalized_category, normalized_item_name, item_link, user_id))
            conn.commit()
            return 'deleted'
