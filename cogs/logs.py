import discord
from discord import app_commands
from discord.ext import commands
import datetime
import json
import os

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_log_channel(guild, category):
    settings = load_settings()
    channel_id = settings.get(str(guild.id), {}).get(f"logs_{category}")
    if channel_id:
        return guild.get_channel(channel_id)
    return None

async def send_log(guild, category, embed):
    channel = get_log_channel(guild, category)
    if channel:
        try:
            await channel.send(embed=embed)
        except:
            pass

def prioriser_salons(guild, mot_cle):
    correspond = [c for c in guild.text_channels if mot_cle in c.name.lower()]
    autres = [c for c in guild.text_channels if mot_cle not in c.name.lower()]
    return correspond + autres


CATEGORIES_LOGS = [
    ("moderation", "🔨 Modération", "moderation"),
    ("messages", "💬 Messages", "messages"),
    ("membres", "👥 Membres", "membres"),
    ("vocal", "🔊 Vocal", "vocal"),
    ("salons", "📁 Salons", "salons"),
    ("tickets", "🎫 Tickets", "ticket"),
]


# ── Panel central façon UltimeBots ──────────────────────────────

class SetupLogsView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=300)
        self.guild = guild
        self.selections = {}
        self.message = None

        # Pré-charge les valeurs déjà configurées
        settings = load_settings()
        guild_settings = settings.get(str(guild.id), {})
        for key, _, _ in CATEGORIES_LOGS:
            self.selections[key] = guild_settings.get(f"logs_{key}")

        # Génère un bouton par catégorie (max 5 en row 0-1, le reste s'organise auto)
        for i, (key, label, _) in enumerate(CATEGORIES_LOGS):
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, row=i // 3)
            btn.callback = self.make_callback(key)
            self.add_item(btn)

        reset_btn = discord.ui.Button(label="🔄 Réinitialiser", style=discord.ButtonStyle.danger, row=2)
        reset_btn.callback = self.reset
        self.add_item(reset_btn)

        confirm_btn = discord.ui.Button(label="✅ Enregistrer", style=discord.ButtonStyle.success, row=2)
        confirm_btn.callback = self.confirmer
        self.add_item(confirm_btn)

    def embed_recap(self):
        embed = discord.Embed(title="📋 Système de logs", color=discord.Color.blurple())
        for key, label, _ in CATEGORIES_LOGS:
            channel_id = self.selections.get(key)
            channel = self.guild.get_channel(channel_id) if channel_id else None
            embed.add_field(name=label, value=channel.mention if channel else "❌ Non configuré", inline=True)
        embed.set_footer(text="Clique sur une catégorie pour choisir son salon, puis Enregistrer.")
        return embed

    def make_callback(self, key):
        async def callback(interaction: discord.Interaction):
            mot_cle = {"ticket": "ticket"}.get(key, key[:4])
            options = [discord.SelectOption(label="❌ Désactiver", value="0")]
            options += [discord.SelectOption(label=f"#{c.name}", value=str(c.id)) for c in prioriser_salons(self.guild, mot_cle)[:24]]
            await interaction.response.send_message(
                f"Choisis le salon pour cette catégorie :",
                view=SousMenuLog(self, key, options),
                ephemeral=True
            )
        return callback

    async def reset(self, interaction: discord.Interaction):
        for key, _, _ in CATEGORIES_LOGS:
            self.selections[key] = None
        await interaction.response.edit_message(embed=self.embed_recap(), view=self)

    async def confirmer(self, interaction: discord.Interaction):
        settings = load_settings()
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = {}
        for key, channel_id in self.selections.items():
            settings[guild_id][f"logs_{key}"] = channel_id
        save_settings(settings)

        await interaction.response.edit_message(
            embed=discord.Embed(title="✅ Logs enregistrés !", description="La configuration a été sauvegardée.", color=discord.Color.green()),
            view=None
        )

    async def refresh(self):
        if self.message:
            try:
                await self.message.edit(embed=self.embed_recap(), view=self)
            except:
                pass


class SousMenuLog(discord.ui.View):
    def __init__(self, parent_view: SetupLogsView, key: str, options: list):
        super().__init__(timeout=60)
        self.parent_view = parent_view
        self.key = key
        select = discord.ui.Select(placeholder="Choisis un salon...", options=options)
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        valeur = self.children[0].values[0]
        self.parent_view.selections[self.key] = int(valeur) if valeur != "0" else None
        await self.parent_view.refresh()
        await interaction.response.edit_message(content="✅ Choix enregistré ! Tu peux fermer ce message.", view=None)


# ── Cog Logs ───────────────────────────────────────────────────

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup-logs", description="Configure les salons de logs")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_logs(self, interaction: discord.Interaction):
        view = SetupLogsView(interaction.guild)
        await interaction.response.send_message(embed=view.embed_recap(), view=view, ephemeral=True)
        view.message = await interaction.original_response()

    @setup_logs.error
    async def logs_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission.", ephemeral=True)

    # ── Logs Modération ──

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(title="🔨 Membre banni", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Utilisateur", value=f"{user} ({user.id})")
        embed.set_thumbnail(url=user.display_avatar.url)
        await send_log(guild, "moderation", embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(title="✅ Membre débanni", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Utilisateur", value=f"{user} ({user.id})")
        await send_log(guild, "moderation", embed)

    # ── Logs Messages ──

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        embed = discord.Embed(title="🗑️ Message supprimé", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Auteur", value=f"{message.author.mention}", inline=True)
        embed.add_field(name="Salon", value=message.channel.mention, inline=True)
        embed.add_field(name="Contenu", value=message.content or "*[Aucun contenu]*", inline=False)
        await send_log(message.guild, "messages", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        embed = discord.Embed(title="✏️ Message modifié", color=discord.Color.yellow(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Auteur", value=before.author.mention, inline=True)
        embed.add_field(name="Salon", value=before.channel.mention, inline=True)
        embed.add_field(name="Avant", value=before.content or "*vide*", inline=False)
        embed.add_field(name="Après", value=after.content or "*vide*", inline=False)
        embed.add_field(name="🔗 Lien", value=f"[Voir le message]({after.jump_url})", inline=False)
        await send_log(before.guild, "messages", embed)

    # ── Logs Membres ──

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="📥 Nouveau membre", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Membre", value=f"{member.mention} ({member.id})")
        embed.add_field(name="Compte créé le", value=member.created_at.strftime("%d/%m/%Y"))
        embed.set_thumbnail(url=member.display_avatar.url)
        await send_log(member.guild, "membres", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="📤 Membre parti", color=discord.Color.orange(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Membre", value=f"{member} ({member.id})")
        embed.set_thumbnail(url=member.display_avatar.url)
        await send_log(member.guild, "membres", embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        roles_ajoutes = set(after.roles) - set(before.roles)
        roles_retires = set(before.roles) - set(after.roles)
        if roles_ajoutes or roles_retires:
            embed = discord.Embed(title="🎭 Rôles modifiés", color=discord.Color.blurple(), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Membre", value=after.mention, inline=False)
            if roles_ajoutes:
                embed.add_field(name="✅ Ajoutés", value=", ".join(r.mention for r in roles_ajoutes), inline=True)
            if roles_retires:
                embed.add_field(name="❌ Retirés", value=", ".join(r.mention for r in roles_retires), inline=True)
            await send_log(after.guild, "membres", embed)
        if before.nick != after.nick:
            embed = discord.Embed(title="✏️ Pseudo modifié", color=discord.Color.blurple(), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Membre", value=after.mention)
            embed.add_field(name="Avant", value=before.nick or "*Aucun*", inline=True)
            embed.add_field(name="Après", value=after.nick or "*Aucun*", inline=True)
            await send_log(after.guild, "membres", embed)

    # ── Logs Vocal ──

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not before.channel and after.channel:
            embed = discord.Embed(title="🔊 Rejoint un vocal", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Membre", value=member.mention, inline=True)
            embed.add_field(name="Salon", value=after.channel.name, inline=True)
            await send_log(member.guild, "vocal", embed)
        elif before.channel and not after.channel:
            embed = discord.Embed(title="🔇 Quitté un vocal", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Membre", value=member.mention, inline=True)
            embed.add_field(name="Salon", value=before.channel.name, inline=True)
            await send_log(member.guild, "vocal", embed)
        elif before.channel and after.channel and before.channel != after.channel:
            embed = discord.Embed(title="🔀 Changé de vocal", color=discord.Color.yellow(), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Membre", value=member.mention)
            embed.add_field(name="Avant", value=before.channel.name, inline=True)
            embed.add_field(name="Après", value=after.channel.name, inline=True)
            await send_log(member.guild, "vocal", embed)

    # ── Logs Salons ──

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title="📁 Salon créé", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Nom", value=channel.name, inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        await send_log(channel.guild, "salons", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title="🗑️ Salon supprimé", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Nom", value=channel.name, inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        await send_log(channel.guild, "salons", embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name != after.name:
            embed = discord.Embed(title="✏️ Salon renommé", color=discord.Color.yellow(), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Avant", value=before.name, inline=True)
            embed.add_field(name="Après", value=after.name, inline=True)
            await send_log(after.guild, "salons", embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))