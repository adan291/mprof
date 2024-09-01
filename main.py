import asyncio
from bot import CraftingBot
import config

async def main():
    config.Config.load_env()
    token = config.Config.get_token()
    if not token:
        raise ValueError("El token de Discord es inválido o no se cargó correctamente.")
    intents = config.Config.get_intents()
    channel_id = 1279550419990872144  # Canal "anuncios"

    bot = CraftingBot(intents=intents, allowed_channel_id=channel_id)

    try:
        # Ejecutar el bot
        await bot.start(token)
    except KeyboardInterrupt:
        print("El bot recibió una interrupción (Ctrl+C).")
    except asyncio.CancelledError:
        print("La tarea asincrónica fue cancelada.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        print("Enviando mensaje de desconexión...")
        await bot.close()
        print("Bot cerrado correctamente.")

if __name__ == "__main__":
    asyncio.run(main())
