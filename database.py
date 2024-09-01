import os
import sqlite3

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
                        character_name TEXT,
                        user_id INTEGER
                    )
                ''')
            conn.commit()

def add_crafter(db_path, character_name, category, item_name, item_link, user_id):
    """Añade un artesano a la base de datos.
       Devuelve True si el artesano fue añadido, False si ya estaba registrado."""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('''
                SELECT character_name FROM crafters
                WHERE category = ? AND item_name = ? AND item_link = ? AND user_id = ?
            ''', (category, item_name, item_link, user_id))

        if c.fetchone() is None:
            c.execute('''
                    INSERT INTO crafters (category, item_name, item_link, character_name, user_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (category, item_name, item_link, character_name, user_id))
            conn.commit()
            return True
        else:
            return False

def get_crafters(db_path, category, item_name):
    """Obtiene los artesanos y el enlace del objeto en una categoría.
       Permite búsquedas parciales en el nombre del objeto."""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        if ' ' in item_name:
            c.execute('''
                    SELECT character_name, item_link FROM crafters
                    WHERE category = ? AND item_name = ?
                ''', (category, item_name))
            results = [(item_name, c.fetchall())]
        else:
            c.execute('''
                    SELECT DISTINCT item_name FROM crafters
                    WHERE category = ? AND item_name LIKE ?
                ''', (category, f'%{item_name}%'))
            item_names = c.fetchall()

            results = []
            for (item_name,) in item_names:
                c.execute('''
                        SELECT character_name, item_link FROM crafters
                        WHERE category = ? AND item_name = ?
                    ''', (category, item_name))
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
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('''
                SELECT user_id FROM crafters
                WHERE character_name = ? AND category = ? AND item_name = ? AND item_link = ?
            ''', (character_name, category, item_name, item_link))
        result = c.fetchone()

        if result is None:
            return 'not_found'
        elif result[0] != user_id:
            return 'no_permission'
        else:
            c.execute('''
                    DELETE FROM crafters
                    WHERE character_name = ? AND category = ? AND item_name = ? AND item_link = ? AND user_id = ?
                ''', (character_name, category, item_name, item_link, user_id))
            conn.commit()
            return 'deleted'
