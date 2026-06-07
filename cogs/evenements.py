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
 
class Evenements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.bot.user} (ID: {self.bot.user.id})")
        try:
            synced = await self.bot.tree.sync()
            print(f"✅ {len(synced)} commande(s) slash synchronisée(s)")
        except Exception as e:
            print(f"❌ Erreur de synchronisation : {e}")
 
    @commands.Cog.listener()
    async def on_member_join(self, member):
        settings = load_settings()
        guild_id = str(member.guild.id)
 
        salon_id = settings.get(guild_id, {}).get("salon_bienvenue")
        if not salon_id:
            return  # Aucun salon configuré, on ne fait rien
 
        channel = self.bot.get_channel(salon_id)
        if not channel:
            return
 
        numero = member.guild.member_count
        embed = discord.Embed(
            title=f"👋 Bienvenue sur {member.guild.name} !",
            description=(
                f"Heureux de t'accueillir, {member.mention} !\n\n"
                f"Tu es notre **{numero}ème membre** 🎉"
            ),
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📅 Compte créé le", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.set_footer(text=f"ID : {member.id}")
 
        await channel.send(embed=embed)
 
    @app_commands.command(name="set-bienvenue", description="Définit le salon pour les messages de bienvenue")
    @app_commands.describe(salon="Le salon où envoyer les messages de bienvenue")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_bienvenue(self, interaction: discord.Interaction, salon: discord.TextChannel):
        settings = load_settings()
        guild_id = str(interaction.guild.id)
 
        if guild_id not in settings:
            settings[guild_id] = {}
        settings[guild_id]["salon_bienvenue"] = salon.id
        save_settings(settings)
 
        embed = discord.Embed(
            title="✅ Salon de bienvenue configuré",
            description=f"Les messages de bienvenue seront envoyés dans {salon.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="test-bienvenue", description="Teste le message de bienvenue")
    @app_commands.checks.has_permissions(administrator=True)
    async def test_bienvenue(self, interaction: discord.Interaction):
        settings = load_settings()
        salon_id = settings.get(str(interaction.guild.id), {}).get("salon_bienvenue")
 
        if not salon_id:
            return await interaction.response.send_message(
                "❌ Aucun salon configuré. Utilise `/set-bienvenue` d'abord.", ephemeral=True
            )
 
        channel = self.bot.get_channel(salon_id)
        if not channel:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)
 
        member = interaction.user
        numero = interaction.guild.member_count
        embed = discord.Embed(
            title=f"👋 Bienvenue sur {interaction.guild.name} !",
            description=(
                f"Heureux de t'accueillir, {member.mention} !\n\n"
                f"Tu es notre **{numero}ème membre** 🎉"
            ),
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📅 Compte créé le", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.set_footer(text=f"ID : {member.id}")
 
        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Message de test envoyé dans {channel.mention} !", ephemeral=True)
 
    @set_bienvenue.error
    @test_bienvenue.error
    async def bienvenue_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
 
async def setup(bot):
    await bot.add_cog(Evenements(bot))
 