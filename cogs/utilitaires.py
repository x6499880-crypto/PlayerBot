
import discord
from discord import app_commands
from discord.ext import commands
import datetime
 
class Utilitaires(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    @app_commands.command(name="ping", description="Affiche la latence du bot")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong ! Latence : **{latency}ms**")
 
    @app_commands.command(name="info-serveur", description="Affiche les infos du serveur")
    async def info_serveur(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="👥 Membres", value=guild.member_count, inline=True)
        embed.add_field(name="📅 Créé le", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="👑 Propriétaire", value=guild.owner.mention, inline=True)
        embed.add_field(name="💬 Salons", value=len(guild.channels), inline=True)
        embed.add_field(name="🎭 Rôles", value=len(guild.roles), inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="info-membre", description="Affiche les infos d'un membre")
    @app_commands.describe(membre="Le membre à inspecter")
    async def info_membre(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        embed = discord.Embed(
            title=f"👤 {membre.display_name}",
            color=membre.color,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="🆔 ID", value=membre.id, inline=True)
        embed.add_field(name="📅 Compte créé", value=membre.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="📥 Rejoint le", value=membre.joined_at.strftime("%d/%m/%Y"), inline=True)
        roles = [r.mention for r in membre.roles[1:]]
        embed.add_field(name="🎭 Rôles", value=", ".join(roles) if roles else "Aucun", inline=False)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="commandes", description="Affiche les commandes disponibles pour les membres dans ce salon")
    @app_commands.checks.has_permissions(administrator=True)
    async def commandes(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Commandes disponibles",
            description="Voici toutes les commandes que tu peux utiliser !",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="🛠️ Utilitaires", value=(
            "`/ping` — Latence du bot\n"
            "`/info-serveur` — Infos du serveur\n"
            "`/info-membre` — Infos d'un membre\n"
            "`/tiktok` — Lien vers notre TikTok"
        ), inline=False)
        embed.add_field(name="🔢 Comptage", value=(
            "`/comptage-info` — Compteur actuel et record"
        ), inline=False)
        embed.add_field(name="🎙️ Vocal", value=(
            "Rejoins le salon **Ton Vocal** pour créer ton salon vocal temporaire."
        ), inline=False)
        embed.add_field(name="🎫 Tickets", value=(
            "Clique sur le bouton dans le salon de support pour ouvrir un salon **tickets**."
        ), inline=False)
        embed.set_footer(text=interaction.guild.name)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="tiktok", description="Affiche le lien vers le TikTok du serveur")
    async def tiktok(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎵 TikTok",
            description="Retrouve-nous sur TikTok !\n\n🔗 [**@xplayer0724**](https://www.tiktok.com/@xplayer0724)",
            color=0x010101
        )
        embed.set_footer(text="N'oublie pas de t'abonner ! 🙏")
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="help", description="Affiche la liste des commandes")
    async def help(self, interaction: discord.Interaction):
        is_admin = interaction.user.guild_permissions.administrator
 
        # ── Commandes membres ──
        embed = discord.Embed(
            title="📖 Aide — Commandes disponibles",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Demandé par {interaction.user.display_name}")
 
        embed.add_field(name="🛠️ Utilitaires", value=(
            "`/ping` — Latence du bot\n"
            "`/info-serveur` — Infos du serveur\n"
            "`/info-membre` — Infos d'un membre\n"
            "`/tiktok` — Lien vers le TikTok du serveur"
        ), inline=False)
 
        embed.add_field(name="🔢 Comptage", value=(
            "`/comptage-info` — Compteur actuel et record"
        ), inline=False)
 
        embed.add_field(name="🎙️ Vocal", value=(
            "Rejoins le salon **hub** pour créer ton salon vocal temporaire."
        ), inline=False)
 
        embed.add_field(name="🎫 Tickets", value=(
            "Clique sur le bouton dans le salon de support pour ouvrir un ticket."
        ), inline=False)
 
        # ── Commandes admin ──
        if is_admin:
            embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━", inline=False)
            embed.add_field(name="🔨 Modération (admin)", value=(
                "`/ban` — Bannir un membre\n"
                "`/unban` — Débannir un membre\n"
                "`/kick` — Expulser un membre\n"
                "`/mute` — Mettre en timeout\n"
                "`/unmute` — Retirer le timeout\n"
                "`/clear` — Supprimer des messages"
            ), inline=False)
 
            embed.add_field(name="⚙️ Configuration (admin)", value=(
                "`/set-bienvenue` — Salon des messages de bienvenue\n"
                "`/test-bienvenue` — Tester le message de bienvenue\n"
                "`/setup-tickets` — Configurer le système de tickets\n"
                "`/setup-comptage` — Configurer le salon de comptage\n"
                "`/reset-comptage` — Remettre le compteur à 0\n"
                "`/setup-vocal` — Configurer les salons vocaux temporaires\n"
                "`/commandes` — Afficher les commandes membres dans un salon"
            ), inline=False)
 
        await interaction.response.send_message(embed=embed, ephemeral=True)
 
async def setup(bot):
    await bot.add_cog(Utilitaires(bot))
 