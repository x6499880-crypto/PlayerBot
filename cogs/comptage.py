import discord
from discord import app_commands
from discord.ext import commands
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
 
 
class Comptage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
 
        settings = load_settings()
        guild_id = str(message.guild.id)
        guild_settings = settings.get(guild_id, {})
        salon_id = guild_settings.get("salon_comptage")
 
        if not salon_id or message.channel.id != salon_id:
            return
 
        compteur = guild_settings.get("compteur", 0)
        record = guild_settings.get("record_comptage", 0)
 
        # Vérifier que le message est bien un nombre
        try:
            nombre = int(message.content.strip())
        except ValueError:
            await message.delete()
            return
 
        # Bon nombre ?
        if nombre == compteur + 1:
            compteur += 1
            if compteur > record:
                record = compteur
                settings[guild_id]["record_comptage"] = record
            settings[guild_id]["compteur"] = compteur
            save_settings(settings)
            await message.add_reaction("✅")
 
            # Félicitations tous les 100
            if compteur % 100 == 0:
                await message.channel.send(f"🎉 Incroyable ! Vous avez atteint **{compteur}** !", delete_after=10)
 
        else:
            # Mauvais nombre → suppression silencieuse, compteur inchangé
            await message.delete()
 
    @app_commands.command(name="setup-comptage", description="Définit le salon de comptage")
    @app_commands.describe(salon="Le salon dédié au comptage")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_member_permissions(administrator=True)
    async def setup_comptage(self, interaction: discord.Interaction, salon: discord.TextChannel):
        settings = load_settings()
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = {}
 
        settings[guild_id]["salon_comptage"] = salon.id
        settings[guild_id].setdefault("compteur", 0)
        settings[guild_id].setdefault("record_comptage", 0)
        save_settings(settings)
 
        embed = discord.Embed(
            title="✅ Salon de comptage configuré",
            description=f"Le jeu de comptage se déroulera dans {salon.mention}.\nCommencez à compter à partir de **1** !",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="comptage-info", description="Affiche le compteur actuel et le record")
    async def comptage_info(self, interaction: discord.Interaction):
        settings = load_settings()
        guild_settings = settings.get(str(interaction.guild.id), {})
        compteur = guild_settings.get("compteur", 0)
        record = guild_settings.get("record_comptage", 0)
        salon_id = guild_settings.get("salon_comptage")
        salon = interaction.guild.get_channel(salon_id) if salon_id else None
 
        embed = discord.Embed(title="🔢 Jeu de comptage", color=discord.Color.blurple())
        embed.add_field(name="📍 Compteur actuel", value=str(compteur), inline=True)
        embed.add_field(name="🏆 Record", value=str(record), inline=True)
        embed.add_field(name="📌 Salon", value=salon.mention if salon else "Non configuré", inline=True)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="reset-comptage", description="Remet le compteur à 0")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_member_permissions(administrator=True)
    async def reset_comptage(self, interaction: discord.Interaction):
        settings = load_settings()
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = {}
        settings[guild_id]["compteur"] = 0
        save_settings(settings)
        await interaction.response.send_message("🔄 Compteur remis à **0**.")
 
    @setup_comptage.error
    @reset_comptage.error
    async def comptage_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
 
async def setup(bot):
    await bot.add_cog(Comptage(bot))
 