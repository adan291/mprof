import asyncio
import config
from bot import CraftingBot
import webserver


async def main():
    config.Config.load_env()
    token = config.Config.get_token()
    if not token:
        raise ValueError("El token de Discord es inválido o no se cargó correctamente.")

    intents = config.Config.get_intents()
    channel_id = config.Config.get_channel_id()
    guild_id = config.Config.get_guild_id()

    bot = CraftingBot(intents=intents, channel_id=channel_id, guild_id=guild_id)

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("El bot recibió una interrupción (Ctrl+C).")
    except asyncio.CancelledError:
        print("La tarea asincrónica fue cancelada.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        print("Cerrando el bot...")
        await bot.close()
        print("Bot cerrado correctamente.")


if __name__ == "__main__":
    webserver.keep_alive()
    asyncio.run(main())
