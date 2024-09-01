import discord
import sqlite3
import os
from discord import File


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
                        crafter TEXT
                    )
                ''')
                conn.commit()

    def add_crafter(self, category, item_name, crafter):
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
                c.execute('''
                    INSERT INTO crafters (category, item_name, crafter)
                    VALUES (?, ?, ?)
                ''', (category, item_name, crafter))
                conn.commit()
                return True  # Artesano añadido
            else:
                return False  # Artesano ya registrado

    def get_crafters(self, category, item_name):
        """Obtiene los artesanos para un objeto en una categoría de la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT DISTINCT crafter FROM crafters
                WHERE category = ? AND item_name = ?
            ''', (category, item_name))
            return [row[0] for row in c.fetchall()]

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
                    "**Formato incorrecto.**\nEl formato correcto es: `!mprof registrar <categoria> <objeto>`")
                return

            command, category, item_name = parts[1], parts[2], parts[3]
            category = category.strip().lower()
            item_name = item_name.strip().lower()
            crafter = message.author.name

            added = self.add_crafter(category, item_name, crafter)
            if added:
                await message.channel.send(
                    f"**¡Éxito!**\n{message.author.mention} ha sido registrado como artesano de **{item_name}** en la categoría **{category}**.")
            else:
                await message.channel.send(
                    f"**¡Ya registrado!**\n{message.author.mention} ya estaba registrado como artesano de **{item_name}** en la categoría **{category}**.")

        elif content.startswith('!mprof buscar'):
            parts = content.split(' ', 3)
            if len(parts) < 4:
                await message.channel.send(
                    "**Formato incorrecto.**\nEl formato correcto es: `!mprof buscar <categoria> <objeto>`")
                return

            command, category, item_name = parts[1], parts[2], parts[3]
            category = category.strip().lower()
            item_name = item_name.strip().lower()
            crafters = self.get_crafters(category, item_name)

            if crafters:
                # Formatear la lista de artesanos
                crafters_list = '\n'.join(f" - {crafter}" for crafter in crafters)
                await message.channel.send(
                    f"**Artesanos encontrados:**\nLos siguientes usuarios pueden craftear **{item_name}** en la categoría **{category}**:\n{crafters_list}")
            else:
                await message.channel.send(
                    f"**No se encontraron artesanos.**\nNo hay artesanos registrados para **{item_name}** en la categoría **{category}**.")

        elif content.startswith('!mprof backup'):
            if os.path.exists(self.db_path):
                await message.channel.send("**Generando backup...**")

                # Enviar el archivo de la base de datos como un archivo adjunto
                await message.channel.send(file=File(self.db_path, filename="crafters_db_backup.sqlite"))
            else:
                await message.channel.send("**No se encontró la base de datos.**")

