import os
import re
from urllib.parse import unquote

import discord
from discord import app_commands
from discord.ext import commands

from registry.store import normalize_text


def derive_name_from_link(link):
    """Deriva un nombre legible a partir del último segmento de la URL."""
    try:
        segment = link.rstrip('/').split('/')[-1]
        return unquote(segment.replace('-', ' ')).strip() or link
    except Exception:
        return link


class RegistryCog(commands.Cog):
    registro = app_commands.Group(name="registro", description="Registro de proveedores por categoría.")

    def __init__(self, bot, store, cfg, db_path, channel_id=None):
        self.bot = bot
        self.store = store
        self.cfg = cfg
        self.db_path = db_path
        self.channel_id = channel_id
        self.categorias = [normalize_text(c) for c in cfg["categorias"]]
        self.label_entrada = cfg.get("nombre_entrada", "entrada")
        self.label_proveedor = cfg.get("nombre_proveedor", "proveedor")
        self.patron_enlace = cfg.get("patron_enlace") or None

    # ---- helpers ---------------------------------------------------------

    def _channel_ok(self, interaction):
        return not self.channel_id or interaction.channel_id == self.channel_id

    def _valid_category(self, category):
        return normalize_text(category) in self.categorias

    def _valid_link(self, link):
        if not self.patron_enlace:
            return True
        return re.search(self.patron_enlace, link) is not None

    async def _categoria_autocomplete(self, interaction: discord.Interaction, current: str):
        cur = normalize_text(current)
        return [
            app_commands.Choice(name=c, value=c)
            for c in self.cfg["categorias"]
            if cur in normalize_text(c)
        ][:25]

    async def _reject_common(self, interaction, category, link, check_link=True):
        """Valida canal, categoría y enlace. Devuelve True si hay que abortar."""
        if not self._channel_ok(interaction):
            await interaction.response.send_message(
                f"Este comando solo se puede usar en <#{self.channel_id}>.", ephemeral=True)
            return True
        if not self._valid_category(category):
            await interaction.response.send_message(
                f"Categoría inválida. Válidas: {', '.join(self.cfg['categorias'])}.", ephemeral=True)
            return True
        if check_link and not self._valid_link(link):
            await interaction.response.send_message(
                "Enlace inválido para este registro.", ephemeral=True)
            return True
        return False

    # ---- comandos --------------------------------------------------------

    @registro.command(name="registrar", description="Registra un proveedor para un objeto.")
    @app_commands.describe(
        proveedor="Nombre del proveedor (p. ej. tu personaje).",
        categoria="Categoría del objeto.",
        enlace="Enlace al objeto.",
        nombre="Nombre del objeto (opcional; si se omite, se deduce del enlace).",
    )
    @app_commands.autocomplete(categoria=_categoria_autocomplete)
    async def registrar(self, interaction, proveedor: str, categoria: str, enlace: str, nombre: str = None):
        if await self._reject_common(interaction, categoria, enlace):
            return
        name = nombre or derive_name_from_link(enlace)
        added = self.store.add(proveedor, categoria, name, enlace, interaction.user.id)
        if added:
            await interaction.response.send_message(
                f"✅ **{proveedor}** registrado como {self.label_proveedor} de "
                f"**[{name}]({enlace})** en **{categoria}**.")
        else:
            await interaction.response.send_message(
                f"⚠️ **{proveedor}** ya estaba registrado para **[{name}]({enlace})** en **{categoria}**.",
                ephemeral=True)

    @registro.command(name="buscar", description="Busca proveedores de un objeto en una categoría.")
    @app_commands.describe(categoria="Categoría donde buscar.", objeto="Nombre (o parte) del objeto.")
    @app_commands.autocomplete(categoria=_categoria_autocomplete)
    async def buscar(self, interaction, categoria: str, objeto: str):
        if not self._channel_ok(interaction):
            await interaction.response.send_message(
                f"Este comando solo se puede usar en <#{self.channel_id}>.", ephemeral=True)
            return
        if not self._valid_category(categoria):
            await interaction.response.send_message(
                f"Categoría inválida. Válidas: {', '.join(self.cfg['categorias'])}.", ephemeral=True)
            return

        results = self.store.search(categoria, objeto)
        if not results:
            await interaction.response.send_message(
                f"No se encontraron {self.label_proveedor}s para **{objeto}** en **{categoria}**.",
                ephemeral=True)
            return

        lines = [f"**{self.label_proveedor.capitalize()}s encontrados:**\n"]
        for name, link, providers in results:
            lines.append(f"\n**[{name}]({link})**")
            lines.extend(f"- {p}" for p in providers)
        await self._send_long(interaction, "\n".join(lines))

    @registro.command(name="listar", description="Lista todas las entradas registradas.")
    async def listar(self, interaction):
        if not self._channel_ok(interaction):
            await interaction.response.send_message(
                f"Este comando solo se puede usar en <#{self.channel_id}>.", ephemeral=True)
            return
        entries = self.store.list_all()
        if not entries:
            await interaction.response.send_message("No hay entradas registradas.", ephemeral=True)
            return
        lines = [f"**Todas las entradas registradas:**\n"]
        for category, name, link, providers in entries:
            lines.append(f"\n**{category}** · [{name}]({link})")
            lines.extend(f"- {p}" for p in providers)
        await self._send_long(interaction, "\n".join(lines))

    @registro.command(name="borrar", description="Elimina una entrada tuya.")
    @app_commands.describe(
        proveedor="Nombre del proveedor.",
        categoria="Categoría del objeto.",
        enlace="Enlace al objeto.",
        nombre="Nombre del objeto (opcional; si se omite, se deduce del enlace).",
    )
    @app_commands.autocomplete(categoria=_categoria_autocomplete)
    async def borrar(self, interaction, proveedor: str, categoria: str, enlace: str, nombre: str = None):
        if await self._reject_common(interaction, categoria, enlace):
            return
        name = nombre or derive_name_from_link(enlace)
        result = self.store.delete(proveedor, categoria, name, enlace, interaction.user.id)
        if result == 'deleted':
            await interaction.response.send_message(
                f"🗑️ **{proveedor}** eliminado de **[{name}]({enlace})** en **{categoria}**.")
        elif result == 'not_found':
            await interaction.response.send_message(
                f"No se encontró ese registro de **{proveedor}**.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "No tienes permiso para eliminar este registro.", ephemeral=True)

    @registro.command(name="backup", description="(Admin) Recibe por privado una copia de la base de datos.")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup(self, interaction):
        if not os.path.exists(self.db_path):
            await interaction.response.send_message("No se encontró la base de datos.", ephemeral=True)
            return
        try:
            await interaction.user.send(
                "Copia de seguridad de la base de datos:", file=discord.File(self.db_path))
            await interaction.response.send_message("📩 Te envié el backup por privado.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                "No pude enviarte el backup por privado. ¿Tienes los DMs abiertos?", ephemeral=True)

    @backup.error
    async def backup_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "Solo un administrador puede usar este comando.", ephemeral=True)

    # ---- utilidades ------------------------------------------------------

    @staticmethod
    async def _send_long(interaction, text):
        """Envía texto respetando el límite de 2000 caracteres de Discord."""
        chunks, current = [], ""
        for line in text.split("\n"):
            if len(current) + len(line) + 1 > 1900:
                chunks.append(current)
                current = ""
            current += line + "\n"
        if current:
            chunks.append(current)

        await interaction.response.send_message(chunks[0])
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)
