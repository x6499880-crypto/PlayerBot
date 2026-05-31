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
 
 
# ── Bouton : Ouvrir un ticket ──────────────────────────────────
 
class BoutonOuvrirTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="📩 Ouvrir un ticket", style=discord.ButtonStyle.primary, custom_id="ouvrir_ticket")
    async def ouvrir_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        settings = load_settings()
        guild_settings = settings.get(str(guild.id), {})
 
        role_staff_id = guild_settings.get("role_staff")
        categorie_id = guild_settings.get("categorie_tickets")
 
        if not role_staff_id:
            return await interaction.response.send_message("❌ Aucun rôle staff configuré. Contacte un administrateur.", ephemeral=True)
 
        role_staff = guild.get_role(role_staff_id)
        categorie = guild.get_channel(categorie_id) if categorie_id else None
 
        # Vérifier si le membre a déjà un ticket ouvert
        for channel in guild.text_channels:
            if channel.topic and f"ticket-{member.id}" in channel.topic:
                return await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket ouvert : {channel.mention}", ephemeral=True
                )
 
        # Créer le salon du ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            role_staff: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
 
        numero = guild_settings.get("ticket_count", 0) + 1
        settings[str(guild.id)]["ticket_count"] = numero
        save_settings(settings)
 
        salon = await guild.create_text_channel(
            name="tickets",
            overwrites=overwrites,
            category=categorie,
            topic=f"ticket-{member.id}"
        )
 
        embed = discord.Embed(
            title="🎫 Ticket ouvert",
            description=(
                f"Bonjour {member.mention}, bienvenue dans ton ticket !\n\n"
                f"Explique ton problème ou ta demande, le staff {role_staff.mention} va t'aider dès que possible."
            ),
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Ticket #{numero:04d}")
 
        await salon.send(embed=embed, view=BoutonFermerTicket())
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {salon.mention}", ephemeral=True)
 
 
# ── Bouton : Fermer un ticket ──────────────────────────────────
 
class BoutonFermerTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger, custom_id="fermer_ticket")
    async def fermer_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⏳ Fermeture du ticket en cours...", ephemeral=True)
        await fermer_et_sauvegarder(interaction.channel, interaction.guild, interaction.user)
 
 
# ── Fonction de fermeture + transcript ────────────────────────
 
async def fermer_et_sauvegarder(channel: discord.TextChannel, guild: discord.Guild, ferme_par: discord.User):
    settings = load_settings()
    salon_transcript_id = settings.get(str(guild.id), {}).get("salon_transcript")
 
    # Générer le transcript en HTML
    messages = []
    async for msg in channel.history(limit=500, oldest_first=True):
        if msg.author.bot and not msg.embeds:
            continue
        messages.append(
            f'<div class="msg">'
            f'<span class="auteur">{discord.utils.escape_mentions(str(msg.author))}</span> '
            f'<span class="date">{msg.created_at.strftime("%d/%m/%Y %H:%M")}</span><br>'
            f'<span class="contenu">{discord.utils.escape_mentions(msg.content) if msg.content else "<em>[embed]</em>"}</span>'
            f'</div>'
        )
 
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Transcript {channel.name}</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #1e1e2e; color: #cdd6f4; padding: 20px; }}
  h1 {{ color: #89b4fa; }}
  .msg {{ background: #313244; margin: 8px 0; padding: 10px; border-radius: 8px; }}
  .auteur {{ font-weight: bold; color: #cba6f7; }}
  .date {{ font-size: 0.8em; color: #6c7086; margin-left: 10px; }}
  .contenu {{ margin-top: 4px; display: block; }}
</style>
</head>
<body>
<h1>📋 Transcript — {channel.name}</h1>
<p>Serveur : <b>{guild.name}</b> | Fermé par : <b>{ferme_par}</b> | Date : <b>{datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M")}</b></p>
<hr>
{''.join(messages)}
</body>
</html>"""
 
    # Sauvegarder localement
    os.makedirs("transcripts", exist_ok=True)
    filepath = f"transcripts/{channel.name}.html"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
 
    # Envoyer dans le salon transcript si configuré
    if salon_transcript_id:
        salon_transcript = guild.get_channel(salon_transcript_id)
        if salon_transcript:
            embed = discord.Embed(
                title=f"📋 Transcript — {channel.name}",
                description=f"Fermé par {ferme_par.mention}",
                color=discord.Color.greyple(),
                timestamp=datetime.datetime.utcnow()
            )
            await salon_transcript.send(embed=embed, file=discord.File(filepath))
 
    await channel.delete(reason=f"Ticket fermé par {ferme_par}")
 
 
# ── Cog Tickets ────────────────────────────────────────────────
 
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(BoutonOuvrirTicket())
        bot.add_view(BoutonFermerTicket())
 
    @app_commands.command(name="setup-tickets", description="Envoie le panel de tickets dans un salon")
    @app_commands.describe(
        salon="Salon où envoyer le panel",
        role_staff="Rôle qui peut gérer les tickets",
        salon_transcript="Salon où sauvegarder les transcripts",
        categorie="Catégorie où créer les tickets (optionnel)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        role_staff: discord.Role,
        salon_transcript: discord.TextChannel,
        categorie: discord.CategoryChannel = None
    ):
        settings = load_settings()
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = {}
 
        settings[guild_id]["role_staff"] = role_staff.id
        settings[guild_id]["salon_transcript"] = salon_transcript.id
        if categorie:
            settings[guild_id]["categorie_tickets"] = categorie.id
        save_settings(settings)
 
        embed = discord.Embed(
            title="🎫 Support — Ouvre un ticket",
            description=(
                "Tu as besoin d'aide ou tu as une question ?\n\n"
                "Clique sur le bouton ci-dessous pour ouvrir un ticket.\n"
                "Notre équipe te répondra dès que possible."
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=interaction.guild.name)
 
        await salon.send(embed=embed, view=BoutonOuvrirTicket())
        await interaction.response.send_message(
            f"✅ Panel de tickets envoyé dans {salon.mention} !\n"
            f"Staff : {role_staff.mention} | Transcripts : {salon_transcript.mention}",
            ephemeral=True
        )
 
    @setup_tickets.error
    async def setup_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
 
 
async def setup(bot):
    await bot.add_cog(Tickets(bot))
 