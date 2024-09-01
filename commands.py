# commands.py

import discord
from database import add_crafter, get_crafters, list_all_crafters, delete_crafter, normalize_text
from urllib.parse import unquote
from profesiones import VALID_CATEGORIES

async def handle_register(message, db_path):
    content = message.content.split(' ', 4)
    if len(content) < 5:
        await message.channel.send(
            "**Formato incorrecto.**\nEl formato correcto es: `!mprof registrar <nombre-en-el-juego> <categoria> <enlace>`")
        return

    character_name = content[2].strip()
    category = content[3].strip()
    item_link = content[4].strip()

    normalized_category = normalize_text(category)

    if normalized_category not in VALID_CATEGORIES:
        await message.channel.send(
            f"**Categoría inválida.**\nLas categorías válidas son: {', '.join(VALID_CATEGORIES)}.")
        return

    if not item_link.startswith("https://www.wowhead.com/"):
        await message.channel.send(
            "**Enlace inválido.**\nPor favor, proporciona un enlace válido de Wowhead que comience con `https://www.wowhead.com/`.")
        return

    try:
        item_name = item_link.split('/')[-1].replace('-', ' ')
        item_name = unquote(item_name)
    except IndexError:
        await message.channel.send("**Error al procesar el nombre del objeto desde la URL.**")
        return

    user_id = message.author.id
    added = add_crafter(db_path, character_name, normalized_category, item_name, item_link, user_id)
    if added:
        response = f"**¡Éxito!**\n{character_name} ha sido registrado como artesano de **[{item_name}]({item_link})** en la categoría **{category}**."
        await message.channel.send(response)
    else:
        response = f"**¡Ya registrado!**\n{character_name} ya estaba registrado como artesano de **[{item_name}]({item_link})** en la categoría **{category}**."
        await message.channel.send(response)

async def handle_search(message, db_path):
    content = message.content.split(' ', 3)
    if len(content) < 4:
        await message.channel.send(
            "**Formato incorrecto.**\nEl formato correcto es: `!mprof buscar <categoria> <objeto>`")
        return

    category = content[2].strip()
    item_name = content[3].strip()

    normalized_category = normalize_text(category)

    if normalized_category not in VALID_CATEGORIES:
        await message.channel.send(
            f"**Categoría inválida.**\nLas categorías válidas son: {', '.join(VALID_CATEGORIES)}.")
        return

    results = get_crafters(db_path, normalized_category, item_name)

    if results:
        response = "**Artesanos encontrados:**\n"
        for item_name, crafters in results:
            response += f"\nObjeto: **[{item_name}]({crafters[0][1]})**\n"
            response += '\n'.join(f"**{character_name}**" for character_name, _ in crafters)
        await message.channel.send(response)
    else:
        await message.channel.send(
            f"**No se encontraron artesanos.**\nNo hay artesanos registrados para **{item_name}** en la categoría **{category}**.")

async def handle_list(message, db_path):
    all_crafters = list_all_crafters(db_path)
    if all_crafters:
        response = "**Lista de todos los artesanos registrados:**\n\n"
        for category, item_name, item_link, crafters in all_crafters:
            response += f"**Categoría:** {category}\n**Objeto:** [{item_name}]({item_link})\n**Artesanos:**\n - {crafters.replace(',', '\n - ')}\n\n"
        await message.channel.send(response)
    else:
        await message.channel.send("**No hay artesanos registrados.**")

async def handle_delete(message, db_path):
    content = message.content.split(' ', 4)
    if len(content) < 5:
        await message.channel.send(
            "**Formato incorrecto.**\nEl formato correcto es: `!mprof borrar <nombre-en-el-juego> <categoria> <enlace>`")
        return

    character_name = content[2].strip()
    category = content[3].strip()
    item_link = content[4].strip()

    normalized_category = normalize_text(category)

    if normalized_category not in VALID_CATEGORIES:
        await message.channel.send(
            f"**Categoría inválida.**\nLas categorías válidas son: {', '.join(VALID_CATEGORIES)}.")
        return

    if not item_link.startswith("https://www.wowhead.com/"):
        await message.channel.send(
            "**Enlace inválido.**\nPor favor, proporciona un enlace válido de Wowhead que comience con `https://www.wowhead.com/`.")
        return

    try:
        item_name = item_link.split('/')[-1].replace('-', ' ')
        item_name = unquote(item_name)
    except IndexError:
        await message.channel.send("**Error al procesar el nombre del objeto desde la URL.**")
        return

    user_id = message.author.id
    result = delete_crafter(db_path, character_name, normalized_category, item_name, item_link, user_id)

    if result == 'deleted':
        await message.channel.send(f"**¡Éxito!**\n{character_name} ha sido eliminado como artesano de **[{item_name}]({item_link})** en la categoría **{category}**.")
    elif result == 'not_found':
        await message.channel.send(f"**No encontrado.**\nNo se encontró a {character_name} como artesano de **[{item_name}]({item_link})** en la categoría **{category}**.")
    elif result == 'no_permission':
        await message.channel.send("**No tienes permiso para eliminar este registro.**")
