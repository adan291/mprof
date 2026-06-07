import discord
from discord.ext import commands

import config
from registry.store import RegistryStore
from registry.commands import RegistryCog


class CraftingBot(commands.Bot):
    def __init__(self, intents, channel_id=None, guild_id=None):
        super().__init__(command_prefix='!', intents=intents)
        self.channel_id = channel_id
        self.guild_id = guild_id

        self.db_path = config.Config.get_db_path()
        self.registry_config = config.Config.load_registry_config()
        self.store = RegistryStore(self.db_path)

    async def setup_hook(self):
        await self.add_cog(
            RegistryCog(self, self.store, self.registry_config, self.db_path, self.channel_id)
        )

        if self.guild_id:
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Comandos sincronizados en el servidor {self.guild_id}.")
        else:
            await self.tree.sync()
            print("Comandos sincronizados globalmente.")

    async def on_ready(self):
        print(f'Bot conectado como {self.user}')
