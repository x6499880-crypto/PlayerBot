import discord
from discord import app_commands
from discord.ext import commands
import datetime
 
class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    def mod_embed(self, titre, couleur, membre, raison, moderateur):
        """Helper pour créer un embed de modération."""
        embed = discord.Embed(title=titre, color=couleur, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Membre", value=f"{membre} ({membre.id})", inline=False)
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.add_field(name="Modérateur", value=moderateur.mention, inline=False)
        return embed
 
    def peut_moderer(self, moderateur: discord.Member, cible: discord.Member):
        """Vérifie si le modérateur peut agir sur la cible."""
        if cible == moderateur:
            return False, "Tu ne peux pas te modérer toi-même."
        if cible.top_role >= moderateur.top_role:
            return False, "Tu ne peux pas modérer quelqu'un avec un rôle supérieur ou égal au tien."
        return True, None
 
    @app_commands.command(name="kick", description="Expulse un membre du serveur")
    @app_commands.describe(membre="Le membre à expulser", raison="Raison de l'expulsion")
    @app_commands.checks.has_permissions(administrator=True)
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
        ok, msg = self.peut_moderer(interaction.user, membre)
        if not ok:
            return await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
 
        try:
            await membre.send(f"Tu as été **expulsé** de **{interaction.guild.name}**.\nRaison : {raison}")
        except:
            pass
        await membre.kick(reason=raison)
        embed = self.mod_embed("👢 Membre expulsé", discord.Color.orange(), membre, raison, interaction.user)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="ban", description="Bannit un membre du serveur")
    @app_commands.describe(membre="Le membre à bannir", raison="Raison du bannissement")
    @app_commands.checks.has_permissions(administrator=True)
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
        ok, msg = self.peut_moderer(interaction.user, membre)
        if not ok:
            return await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
 
        try:
            await membre.send(f"Tu as été **banni** de **{interaction.guild.name}**.\nRaison : {raison}")
        except:
            pass
        await membre.ban(reason=raison)
        embed = self.mod_embed("🔨 Membre banni", discord.Color.red(), membre, raison, interaction.user)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="unban", description="Débannit un utilisateur par son ID")
    @app_commands.describe(user_id="L'ID de l'utilisateur à débannir")
    @app_commands.checks.has_permissions(administrator=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ **{user}** a été débanni.")
        except discord.NotFound:
            await interaction.response.send_message("❌ Utilisateur introuvable ou non banni.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ ID invalide.", ephemeral=True)
 
    @app_commands.command(name="mute", description="Rend muet un membre (timeout)")
    @app_commands.describe(membre="Le membre à mute", duree="Durée en minutes", raison="Raison")
    @app_commands.checks.has_permissions(administrator=True)
    async def mute(self, interaction: discord.Interaction, membre: discord.Member, duree: int = 10, raison: str = "Aucune raison fournie"):
        ok, msg = self.peut_moderer(interaction.user, membre)
        if not ok:
            return await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
 
        until = datetime.datetime.utcnow() + datetime.timedelta(minutes=duree)
        await membre.timeout(until, reason=raison)
        embed = self.mod_embed("🔇 Membre mute", discord.Color.yellow(), membre, raison, interaction.user)
        embed.add_field(name="Durée", value=f"{duree} minute(s)", inline=True)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="unmute", description="Retire le mute d'un membre")
    @app_commands.describe(membre="Le membre à unmute")
    @app_commands.checks.has_permissions(administrator=True)
    async def unmute(self, interaction: discord.Interaction, membre: discord.Member):
        await membre.timeout(None)
        await interaction.response.send_message(f"✅ {membre.mention} n'est plus mute.")
 
    @app_commands.command(name="clear", description="Supprime des messages en masse")
    @app_commands.describe(nombre="Nombre de messages à supprimer (max 100)")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction, nombre: int):
        if nombre < 1 or nombre > 100:
            return await interaction.response.send_message("❌ Le nombre doit être entre 1 et 100.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=nombre)
        await interaction.followup.send(f"🗑️ **{len(deleted)}** message(s) supprimé(s).", ephemeral=True)
 
    @kick.error
    @ban.error
    @unban.error
    @mute.error
    @unmute.error
    @clear.error
    async def moderation_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Erreur : `{error}`", ephemeral=True)
 
async def setup(bot):
    await bot.add_cog(Moderation(bot))
 