import os
from discord import Intents
from dotenv import load_dotenv

class Config:
    @staticmethod
    def load_env():
        load_dotenv(".env")
        load_dotenv(".env.local")

    @staticmethod
    def get_token():
        return os.getenv('DISCORD_TOKEN')

    @staticmethod
    def get_intents():
        intents = Intents.default()
        intents.message_content = True
        intents.reactions = True
        return intents
