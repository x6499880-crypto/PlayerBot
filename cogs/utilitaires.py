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

async def setup(bot):
    await bot.add_cog(Utilitaires(bot))
