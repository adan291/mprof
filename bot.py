import discord
import sqlite3
import os


class CraftingBot(discord.Client):
    def __init__(self, intents, allowed_channel_id, db_path="crafters_db.sqlite"):
        super().__init__(intents=intents)
        self.allowed_channel_id = allowed_channel_id
        self.db_path = db_path
        self.create_db()

    def create_db(self):
        """Crea la base de datos y la tabla si no existen"""
        if not os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    CREATE TABLE IF NOT EXISTS crafters (
                        category TEXT,
                        item_name TEXT,
                        item_link TEXT,
                        crafter TEXT
                    )
                ''')
                conn.commit()

    def add_crafter(self, category, item_name, item_link, crafter):
        """Añade un artesano para un objeto en una categoría en la base de datos.
           Devuelve True si el artesano fue añadido, False si ya estaba registrado."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Verifica si el artesano ya está registrado para el objeto en la categoría
            c.execute('''
                SELECT crafter FROM crafters
                WHERE category = ? AND item_name = ? AND crafter = ?
            ''', (category, item_name, crafter))

            if c.fetchone() is None:
                # Almacena el enlace y el nombre del objeto sin dividir
                c.execute('''
                    INSERT INTO crafters (category, item_name, item_link, crafter)
                    VALUES (?, ?, ?, ?)
                ''', (category, item_name, item_link, crafter))
                conn.commit()
                return True  # Artesano añadido
            else:
                return False  # Artesano ya registrado

    def get_crafters(self, category, item_name):
        """Obtiene los artesanos y el enlace del objeto en una categoría de la base de datos,
           permitiendo búsquedas parciales en el nombre del objeto"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Si el nombre del objeto incluye espacios, se busca exactamente ese nombre
            if ' ' in item_name:
                c.execute('''
                    SELECT crafter, item_link FROM crafters
                    WHERE category = ? AND item_name = ?
                ''', (category, item_name))
                results = [(item_name, c.fetchall())]
            else:
                # Si el nombre del objeto es una palabra, se busca parcialmente
                c.execute('''
                    SELECT DISTINCT item_name FROM crafters
                    WHERE category = ? AND item_name LIKE ?
                ''', (category, f'%{item_name}%'))
                item_names = c.fetchall()

                results = []
                for (item_name,) in item_names:
                    c.execute('''
                        SELECT crafter, item_link FROM crafters
                        WHERE category = ? AND item_name = ?
                    ''', (category, item_name))
                    results.append((item_name, c.fetchall()))

            return results

    def list_all_crafters(self):
        """Obtiene una lista de todos los artesanos y los objetos registrados en la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT category, item_name, item_link, GROUP_CONCAT(crafter, ', ') as crafters
                FROM crafters
                GROUP BY category, item_name, item_link
            ''')
            return c.fetchall()

    async def on_ready(self):
        print(f'Bot conectado como {self.user}')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.channel.id != self.allowed_channel_id:
            return

        content = message.content.strip()

        if content.startswith('!mprof registrar'):
            parts = content.split(' ', 3)
            if len(parts) < 4:
                await message.channel.send(
                    "**Formato incorrecto.**\nEl formato correcto es: `!mprof registrar <categoria> <objeto> <enlace>`")
                return

            category, remainder = parts[2], parts[3]
            item_name, item_link = remainder.rsplit(' ', 1)
            item_name = item_name.strip().lower()
            item_link = item_link.strip()
            category = category.strip().lower()

            # Validar que el enlace sea de Wowhead
            if not item_link.startswith("https://www.wowhead.com/"):
                await message.channel.send(
                    "**Enlace inválido.**\nPor favor, proporciona un enlace válido de Wowhead que comience con `https://www.wowhead.com/`.")
                return

            crafter = message.author.name

            added = self.add_crafter(category, item_name, item_link, crafter)
            if added:
                await message.channel.send(
                    f"**¡Éxito!**\n{message.author.mention} ha sido registrado como artesano de **[{item_name}]({item_link})** en la categoría **{category}**.")
            else:
                await message.channel.send(
                    f"**¡Ya registrado!**\n{message.author.mention} ya estaba registrado como artesano de **[{item_name}]({item_link})** en la categoría **{category}**.")

        elif content.startswith('!mprof buscar'):
            parts = content.split(' ', 3)
            if len(parts) < 4:
                await message.channel.send(
                    "**Formato incorrecto.**\nEl formato correcto es: `!mprof buscar <categoria> <objeto>`")
                return

            category, item_name = parts[2], parts[3]
            category = category.strip().lower()
            item_name = item_name.strip().lower()
            results = self.get_crafters(category, item_name)

            if results:
                response = "**Artesanos encontrados:**\n"
                for item_name, crafters in results:
                    crafters_list = '\n'.join(f" - {crafter}" for crafter, _ in crafters)
                    response += f"\nLos siguientes usuarios pueden craftear **[{item_name}]({crafters[0][1]})** en la categoría **{category}**:\n{crafters_list}"
                await message.channel.send(response)
            else:
                await message.channel.send(
                    f"**No se encontraron artesanos.**\nNo hay artesanos registrados para **{item_name}** en la categoría **{category}**.")

        elif content.startswith('!mprof list'):
            await self.list_crafters(message)

        elif content.startswith('!mprof backup'):
            await self.backup_database(message)

    async def list_crafters(self, message):
        """Lista todos los crafters y objetos registrados en la base de datos"""
        all_crafters = self.list_all_crafters()
        if all_crafters:
            response = "**Lista de todos los artesanos registrados:**\n\n"
            for category, item_name, item_link, crafters in all_crafters:
                response += f"**Categoría:** {category}\n**Objeto:** [{item_name}]({item_link})\n**Artesanos:**\n - {crafters.replace(',', '\n - ')}\n\n"
            await message.channel.send(response)
        else:
            await message.channel.send("**No hay artesanos registrados.**")

    async def backup_database(self, message):
        """Envía un backup de la base de datos al canal"""
        if os.path.exists(self.db_path):
            await message.channel.send("**Aquí está tu backup de la base de datos:**", file=discord.File(self.db_path))
        else:
            await message.channel.send("**Error:** No se encontró la base de datos para hacer un backup.")
