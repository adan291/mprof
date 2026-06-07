import os
import json
from discord import Intents
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_CONFIG_PATH = os.path.join(BASE_DIR, "config", "registry.json")


class Config:
    @staticmethod
    def load_env():
        load_dotenv(".env")
        load_dotenv(".env.local")

    @staticmethod
    def get_token():
        return os.getenv('DISCORD_TOKEN_PROF')

    @staticmethod
    def get_intents():
        # Con slash commands no necesitamos message_content.
        return Intents.default()

    @staticmethod
    def get_channel_id():
        """Canal opcional donde se permiten los comandos. None = cualquier canal."""
        value = os.getenv('CHANNEL_ID')
        return int(value) if value else None

    @staticmethod
    def get_guild_id():
        """Servidor para sincronizar slash commands al instante (desarrollo)."""
        value = os.getenv('GUILD_ID')
        return int(value) if value else None

    @staticmethod
    def get_data_dir():
        """Directorio persistente. En Fly.io está montado en /data."""
        return os.getenv('DATA_DIR', os.path.join(BASE_DIR, "data"))

    @staticmethod
    def get_db_path():
        return os.path.join(Config.get_data_dir(), "registry.sqlite")

    @staticmethod
    def load_registry_config():
        """Carga la configuración del registro (categorías, etiquetas, validación)."""
        with open(REGISTRY_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
