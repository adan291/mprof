# bot.py

import discord
import os
from commands import handle_register, handle_search, handle_list, handle_delete
from database import create_db

class CraftingBot(discord.Client):
    def __init__(self, intents, allowed_channel_id, db_path):
        super().__init__(intents=intents)
        self.allowed_channel_id = allowed_channel_id
        self.db_path = db_path
        create_db(self.db_path)

    async def on_ready(self):
        print(f'Bot conectado como {self.user}')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.channel.id != self.allowed_channel_id:
            return

        content = message.content.strip()

        if content.startswith('!mprof registrar'):
            await handle_register(message, self.db_path)

        elif content.startswith('!mprof buscar'):
            await handle_search(message, self.db_path)

        elif content.startswith('!mprof list'):
            await handle_list(message, self.db_path)

        elif content.startswith('!mprof borrar'):
            await handle_delete(message, self.db_path)

        elif content.startswith('!mprof backup'):
            await self.backup_database(message)

    async def backup_database(self, message):
        """Envía un backup de la base de datos al canal"""
        if os.path.exists(self.db_path):
            await message.channel.send("**Aquí está tu backup de la base de datos:**", file=discord.File(self.db_path))
        else:
            await message.channel.send("**Error:** No se encontró la base de datos para hacer un backup.")
