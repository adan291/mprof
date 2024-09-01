import discord
from database import add_crafter, get_crafters, list_all_crafters, delete_crafter

async def handle_register(message, db_path):
    content = message.content.split(' ', 4)
    if len(content) < 5:
        await message.channel.send(
            "**Formato incorrecto.**\nEl formato correcto es: `!mprof registrar <nombre-en-el-juego> <categoria> <enlace>`")
        return

    character_name, category, item_link = content[2].strip(), content[3].strip().lower(), content[4].strip()

    if not item_link.startswith("https://www.wowhead.com/"):
        await message.channel.send(
            "**Enlace inválido.**\nPor favor, proporciona un enlace válido de Wowhead que comience con `https://www.wowhead.com/`.")
        return

    try:
        item_name = item_link.split('/')[-1].replace('-', ' ')
    except IndexError:
        await message.channel.send("**Error al procesar el nombre del objeto desde la URL.**")
        return

    user_id = message.author.id
    added = add_crafter(db_path, character_name, category, item_name, item_link, user_id)
    if added:
        await message.channel.send(
            f"**¡Éxito!**\n{character_name} ha sido registrado como artesano de **[{item_name}]({item_link})** en la categoría **{category}**.")
    else:
        await message.channel.send(
            f"**¡Ya registrado!**\n{character_name} ya estaba registrado como artesano de **[{item_name}]({item_link})** en la categoría **{category}**.")

async def handle_search(message, db_path):
    content = message.content.split(' ', 3)
    if len(content) < 4:
        await message.channel.send(
            "**Formato incorrecto.**\nEl formato correcto es: `!mprof buscar <categoria> <objeto>`")
        return

    category, item_name = content[2].strip().lower(), content[3].strip().lower()
    results = get_crafters(db_path, category, item_name)

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

    character_name, category, item_link = content[2].strip(), content[3].strip().lower(), content[4].strip()

    if not item_link.startswith("https://www.wowhead.com/"):
        await message.channel.send(
            "**Enlace inválido.**\nPor favor, proporciona un enlace válido de Wowhead que comience con `https://www.wowhead.com/`.")
        return

    try:
        item_name = item_link.split('/')[-1].replace('-', ' ')
    except IndexError:
        await message.channel.send("**Error al procesar el nombre del objeto desde la URL.**")
        return

    user_id = message.author.id
    result = delete_crafter(db_path, character_name, category, item_name, item_link, user_id)
    if result == 'deleted':
        await message.channel.send(
            f"**¡Eliminado!**\n{character_name} ya no está registrado como artesano de **[{item_name}]({item_link})** en la categoría **{category}**.")
    elif result == 'not_found':
        await message.channel.send(
            f"**No encontrado!**\nNo se encontró un registro para {character_name} como artesano de **[{item_name}]({item_link})** en la categoría **{category}**.")
    elif result == 'no_permission':
        await message.channel.send(
            f"**Permiso denegado!**\nNo tienes permisos para eliminar el registro para **[{item_name}]({item_link})** en la categoría **{category}**.")
