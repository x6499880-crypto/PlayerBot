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
 
# ── Étape 1 ────────────────────────────────────────────────────
 
class SetupLogsView1(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=180)
        self.guild = guild
        self.selections = {}
 
        options = [discord.SelectOption(label="❌ Désactiver", value="0")]
        log_channels = [c for c in guild.text_channels if "log" in c.name.lower()]
        other_channels = [c for c in guild.text_channels if "log" not in c.name.lower()]
        all_channels = (log_channels + other_channels)[:24]
        options += [discord.SelectOption(label=f"#{c.name}", value=str(c.id)) for c in all_channels]
 
        for label, key in [("🔨 Modération", "moderation"), ("💬 Messages", "messages"), ("👥 Membres", "membres")]:
            select = discord.ui.Select(placeholder=f"{label} — Choisir un salon", options=options.copy(), custom_id=f"logs_{key}")
            select.callback = self.make_callback(key)
            self.add_item(select)
 
        btn = discord.ui.Button(label="Suivant ▶", style=discord.ButtonStyle.primary, row=4)
        btn.callback = self.suivant
        self.add_item(btn)
 
    def make_callback(self, key):
        async def callback(interaction: discord.Interaction):
            self.selections[key] = int(interaction.data["values"][0]) if interaction.data["values"][0] != "0" else None
            await interaction.response.defer()
        return callback
 
    async def suivant(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📋 Logs — Étape 2/2", description="Configure les logs **Vocal** et **Salons**.", color=discord.Color.blurple())
        await interaction.response.edit_message(embed=embed, view=SetupLogsView2(self.guild, self.selections))
 
 
# ── Étape 2 ────────────────────────────────────────────────────
 
class SetupLogsView2(discord.ui.View):
    def __init__(self, guild, selections):
        super().__init__(timeout=180)
        self.guild = guild
        self.selections = selections
 
        options = [discord.SelectOption(label="❌ Désactiver", value="0")]
        log_channels = [c for c in guild.text_channels if "log" in c.name.lower()]
        other_channels = [c for c in guild.text_channels if "log" not in c.name.lower()]
        all_channels = (log_channels + other_channels)[:24]
        options += [discord.SelectOption(label=f"#{c.name}", value=str(c.id)) for c in all_channels]
 
        for label, key in [("🔊 Vocal", "vocal"), ("📁 Salons", "salons")]:
            select = discord.ui.Select(placeholder=f"{label} — Choisir un salon", options=options.copy(), custom_id=f"logs_{key}")
            select.callback = self.make_callback(key)
            self.add_item(select)
 
        btn_retour = discord.ui.Button(label="◀ Retour", style=discord.ButtonStyle.secondary, row=4)
        btn_retour.callback = self.retour
        self.add_item(btn_retour)
 
        btn_confirm = discord.ui.Button(label="✅ Confirmer", style=discord.ButtonStyle.success, row=4)
        btn_confirm.callback = self.confirmer
        self.add_item(btn_confirm)
 
    def make_callback(self, key):
        async def callback(interaction: discord.Interaction):
            self.selections[key] = int(interaction.data["values"][0]) if interaction.data["values"][0] != "0" else None
            await interaction.response.defer()
        return callback
 
    async def retour(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📋 Logs — Étape 1/2", description="Configure les logs **Modération**, **Messages** et **Membres**.", color=discord.Color.blurple())
        view1 = SetupLogsView1(self.guild)
        view1.selections = self.selections
        await interaction.response.edit_message(embed=embed, view=view1)
 
    async def confirmer(self, interaction: discord.Interaction):
        settings = load_settings()
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = {}
 
        labels = {"moderation": "🔨 Modération", "messages": "💬 Messages", "membres": "👥 Membres", "vocal": "🔊 Vocal", "salons": "📁 Salons"}
        desc = ""
        for key, channel_id in self.selections.items():
            settings[guild_id][f"logs_{key}"] = channel_id
            ch = interaction.guild.get_channel(channel_id) if channel_id else None
            desc += f"{labels.get(key, key)} → {ch.mention if ch else '❌ Désactivé'}\n"
 
        save_settings(settings)
        embed = discord.Embed(title="✅ Logs configurés !", description=desc, color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=None)
 
 
# ── Cog Logs ───────────────────────────────────────────────────
 
class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    @app_commands.command(name="setup-logs", description="Configure les salons de logs")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_member_permissions(discord.Permissions(administrator=True))
    async def setup_logs(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📋 Logs — Étape 1/2",
            description="Configure les logs **Modération**, **Messages** et **Membres**.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=SetupLogsView1(interaction.guild), ephemeral=True)
 
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
 
    @setup_logs.error
    async def logs_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission.", ephemeral=True)
 
async def setup(bot):
    await bot.add_cog(Logs(bot))
 


