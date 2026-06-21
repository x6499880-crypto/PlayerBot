import discord
from discord import app_commands
from discord.ext import commands, tasks
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


class MemberCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_loop.start()

    def cog_unload(self):
        self.update_loop.cancel()

    @app_commands.command(name="setup-membercount", description="Crée un salon affichant le nombre de membres")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_membercount(self, interaction: discord.Interaction):
        guild = interaction.guild
        settings = load_settings()
        guild_id = str(guild.id)

        # Supprime l'ancien salon s'il existe déjà
        ancien_id = settings.get(guild_id, {}).get("membercount_channel")
        if ancien_id:
            ancien = guild.get_channel(ancien_id)
            if ancien:
                try:
                    await ancien.delete(reason="Recréation du salon Member Count")
                except:
                    pass

        salon = await guild.create_voice_channel(
            name=f"🔒│Member Count: {guild.member_count}",
            position=0
        )
        await salon.set_permissions(guild.default_role, connect=False, view_channel=True)

        if guild_id not in settings:
            settings[guild_id] = {}
        settings[guild_id]["membercount_channel"] = salon.id
        save_settings(settings)

        embed = discord.Embed(
            title="✅ Salon Member Count créé",
            description=f"Le salon {salon.mention} affichera le nombre de membres et se mettra à jour automatiquement.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup_membercount.error
    async def membercount_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.update_salon(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.update_salon(member.guild)

    async def update_salon(self, guild):
        settings = load_settings()
        salon_id = settings.get(str(guild.id), {}).get("membercount_channel")
        if not salon_id:
            return
        salon = guild.get_channel(salon_id)
        if salon:
            try:
                await salon.edit(name=f"🔒│Member Count: {guild.member_count}")
            except:
                pass

    @tasks.loop(minutes=10)
    async def update_loop(self):
        """Met à jour périodiquement tous les salons (sécurité contre les ratés d'événements)."""
        settings = load_settings()
        for guild in self.bot.guilds:
            salon_id = settings.get(str(guild.id), {}).get("membercount_channel")
            if salon_id:
                salon = guild.get_channel(salon_id)
                if salon:
                    nom_attendu = f"🔒│Member Count: {guild.member_count}"
                    if salon.name != nom_attendu:
                        try:
                            await salon.edit(name=nom_attendu)
                        except:
                            pass

async def setup(bot):
    await bot.add_cog(MemberCount(bot))