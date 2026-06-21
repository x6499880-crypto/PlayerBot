import discord
from discord import app_commands
from discord.ext import commands
import datetime
import json
import os
import asyncio

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)


CATEGORIES_TICKET = {
    "support": {"label": "🛟 Support", "emoji": "🛟", "couleur": discord.Color.blurple()},
    "recrutement": {"label": "📋 Recrutement", "emoji": "📋", "couleur": discord.Color.green()},
    "partenariat": {"label": "🤝 Partenariat", "emoji": "🤝", "couleur": discord.Color.gold()},
    "signalement": {"label": "🚨 Signalement", "emoji": "🚨", "couleur": discord.Color.red()},
    "autres": {"label": "📁 Autres", "emoji": "📁", "couleur": discord.Color.greyple()},
}


def prioriser_salons(guild, mot_cle):
    """Met en avant les salons dont le nom contient mot_cle."""
    correspond = [c for c in guild.text_channels if mot_cle in c.name.lower()]
    autres = [c for c in guild.text_channels if mot_cle not in c.name.lower()]
    return correspond + autres


async def log_ticket(guild, texte):
    settings = load_settings()
    salon_id = settings.get(str(guild.id), {}).get("logs_tickets")
    if not salon_id:
        return
    salon = guild.get_channel(salon_id)
    if salon:
        embed = discord.Embed(description=texte, color=discord.Color.blurple(), timestamp=datetime.datetime.utcnow())
        try:
            await salon.send(embed=embed)
        except:
            pass


# ── Panel principal : sélecteur de catégorie ───────────────────

class PanelOuvrirTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="📨 Choisis une catégorie pour ouvrir un ticket...",
        custom_id="select_categorie_ticket",
        options=[
            discord.SelectOption(label="Support", value="support", emoji="🛟", description="Besoin d'aide ou d'assistance"),
            discord.SelectOption(label="Recrutement", value="recrutement", emoji="📋", description="Postuler pour rejoindre l'équipe"),
            discord.SelectOption(label="Partenariat", value="partenariat", emoji="🤝", description="Proposer un partenariat"),
            discord.SelectOption(label="Signalement", value="signalement", emoji="🚨", description="Signaler un problème ou un membre"),
            discord.SelectOption(label="Autres", value="autres", emoji="📁", description="Toute autre demande"),
        ]
    )
    async def select_categorie(self, interaction: discord.Interaction, select: discord.ui.Select):
        categorie = select.values[0]
        await creer_ticket(interaction, categorie)


async def creer_ticket(interaction: discord.Interaction, categorie: str):
    guild = interaction.guild
    member = interaction.user
    settings = load_settings()
    guild_id = str(guild.id)
    guild_settings = settings.get(guild_id, {})

    role_staff_id = guild_settings.get("role_staff")
    categorie_discord_id = guild_settings.get("categorie_tickets")

    if not role_staff_id:
        return await interaction.response.send_message("❌ Aucun rôle staff configuré. Utilise `/setup-tickets`.", ephemeral=True)

    role_staff = guild.get_role(role_staff_id)
    categorie_discord = guild.get_channel(categorie_discord_id) if categorie_discord_id else None

    for channel in guild.text_channels:
        if channel.topic and f"ticket-owner-{member.id}" in channel.topic and "status-open" in channel.topic:
            return await interaction.response.send_message(
                f"❌ Tu as déjà un ticket ouvert : {channel.mention}", ephemeral=True
            )

    numero = guild_settings.get("ticket_count", 0) + 1
    settings.setdefault(guild_id, {})["ticket_count"] = numero
    save_settings(settings)

    cat_info = CATEGORIES_TICKET[categorie]

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        role_staff: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
    }

    salon = await guild.create_text_channel(
        name=f"{categorie}-{numero:04d}",
        overwrites=overwrites,
        category=categorie_discord,
        topic=f"ticket-owner-{member.id}-status-open-cat-{categorie}"
    )

    embed = discord.Embed(
        title=f"{cat_info['emoji']} Ticket — {cat_info['label']}",
        description=(
            f"Bonjour {member.mention}, bienvenue dans ton ticket !\n\n"
            f"**Catégorie :** {cat_info['label']}\n"
            f"**Numéro :** #{numero:04d}\n\n"
            f"Explique ta demande, le staff {role_staff.mention} va te répondre dès que possible."
        ),
        color=cat_info["couleur"],
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=f"Ticket #{numero:04d} • {guild.name}")
    embed.set_thumbnail(url=member.display_avatar.url)

    await salon.send(content=f"{member.mention} {role_staff.mention}", embed=embed, view=PanelGestionTicket())
    await interaction.response.send_message(f"✅ Ton ticket a été créé : {salon.mention}", ephemeral=True)
    await log_ticket(guild, f"🎫 **Ticket ouvert** : {salon.mention} par {member.mention} ({cat_info['label']})")


# ── Panel de gestion à l'intérieur du ticket ───────────────────

class PanelGestionTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket_fermer", row=0)
    async def fermer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await is_staff_or_owner(interaction):
            return
        await fermer_ticket(interaction)

    @discord.ui.button(label="Verrouiller", emoji="🔐", style=discord.ButtonStyle.secondary, custom_id="ticket_lock", row=0)
    async def verrouiller(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await is_staff(interaction):
            return
        topic = interaction.channel.topic or ""
        owner_id = extraire_owner_id(topic)
        if owner_id:
            owner = interaction.guild.get_member(owner_id)
            if owner:
                await interaction.channel.set_permissions(owner, send_messages=False)
        await interaction.response.send_message("🔐 Ticket verrouillé. Le membre ne peut plus écrire.", ephemeral=False)
        await log_ticket(interaction.guild, f"🔐 **Ticket verrouillé** : {interaction.channel.mention} par {interaction.user.mention}")

    @discord.ui.button(label="Transcrire", emoji="📋", style=discord.ButtonStyle.secondary, custom_id="ticket_transcript", row=0)
    async def transcrire(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await is_staff(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        filepath = await generer_transcript(interaction.channel, interaction.guild, interaction.user)
        await interaction.followup.send("📋 Transcript généré !", file=discord.File(filepath), ephemeral=True)

    @discord.ui.button(label="Ajouter membre", emoji="➕", style=discord.ButtonStyle.success, custom_id="ticket_add", row=1)
    async def ajouter_membre(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await is_staff(interaction):
            return
        await interaction.response.send_modal(ModalAjouterMembre())

    @discord.ui.button(label="Retirer membre", emoji="➖", style=discord.ButtonStyle.success, custom_id="ticket_remove", row=1)
    async def retirer_membre(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await is_staff(interaction):
            return
        await interaction.response.send_modal(ModalRetirerMembre())

    @discord.ui.button(label="Supprimer", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="ticket_delete_direct", row=1)
    async def supprimer_direct(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await is_staff(interaction):
            return
        await interaction.response.send_message("🗑️ Suppression du salon dans 3 secondes...")
        await log_ticket(interaction.guild, f"🗑️ **Ticket supprimé** : `{interaction.channel.name}` par {interaction.user.mention}")
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete(reason=f"Ticket supprimé par {interaction.user}")
        except:
            pass


class PanelTicketFerme(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Réouvrir", emoji="🔓", style=discord.ButtonStyle.success, custom_id="ticket_reopen")
    async def reouvrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await is_staff(interaction):
            return
        topic = interaction.channel.topic or ""
        owner_id = extraire_owner_id(topic)
        owner = interaction.guild.get_member(owner_id) if owner_id else None

        if owner:
            await interaction.channel.set_permissions(owner, view_channel=True, send_messages=True, read_message_history=True)

        nouveau_topic = topic.replace("status-closed", "status-open")
        await interaction.channel.edit(topic=nouveau_topic)

        embed = discord.Embed(title="🔓 Ticket réouvert", description=f"Réouvert par {interaction.user.mention}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, view=PanelGestionTicket())
        await log_ticket(interaction.guild, f"🔓 **Ticket réouvert** : {interaction.channel.mention} par {interaction.user.mention}")

    @discord.ui.button(label="Supprimer", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="ticket_delete")
    async def supprimer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await is_staff(interaction):
            return
        await interaction.response.send_message("🗑️ Suppression du salon dans 3 secondes...")
        await log_ticket(interaction.guild, f"🗑️ **Ticket supprimé** : `{interaction.channel.name}` par {interaction.user.mention}")
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete(reason=f"Ticket supprimé par {interaction.user}")
        except:
            pass


# ── Modals ─────────────────────────────────────────────────────

class ModalAjouterMembre(discord.ui.Modal, title="Ajouter un membre au ticket"):
    user_id = discord.ui.TextInput(label="ID ou mention du membre", placeholder="123456789012345678")

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.user_id.value.strip().replace("<@", "").replace(">", "").replace("!", "")
        try:
            member = interaction.guild.get_member(int(raw))
        except ValueError:
            member = None
        if not member:
            return await interaction.response.send_message("❌ Membre introuvable.", ephemeral=True)

        await interaction.channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
        await interaction.response.send_message(f"✅ {member.mention} a été ajouté au ticket.")
        await log_ticket(interaction.guild, f"➕ **Membre ajouté** : {member.mention} dans {interaction.channel.mention} par {interaction.user.mention}")


class ModalRetirerMembre(discord.ui.Modal, title="Retirer un membre du ticket"):
    user_id = discord.ui.TextInput(label="ID ou mention du membre", placeholder="123456789012345678")

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.user_id.value.strip().replace("<@", "").replace(">", "").replace("!", "")
        try:
            member = interaction.guild.get_member(int(raw))
        except ValueError:
            member = None
        if not member:
            return await interaction.response.send_message("❌ Membre introuvable.", ephemeral=True)

        await interaction.channel.set_permissions(member, overwrite=None)
        await interaction.response.send_message(f"✅ {member.mention} a été retiré du ticket.")
        await log_ticket(interaction.guild, f"➖ **Membre retiré** : {member.mention} de {interaction.channel.mention} par {interaction.user.mention}")


# ── Fonctions utilitaires ──────────────────────────────────────

def extraire_owner_id(topic: str):
    if not topic or "ticket-owner-" not in topic:
        return None
    try:
        return int(topic.split("ticket-owner-")[1].split("-")[0])
    except:
        return None


async def is_staff(interaction: discord.Interaction) -> bool:
    settings = load_settings()
    role_staff_id = settings.get(str(interaction.guild.id), {}).get("role_staff")
    role_staff = interaction.guild.get_role(role_staff_id) if role_staff_id else None
    if interaction.user.guild_permissions.administrator or (role_staff and role_staff in interaction.user.roles):
        return True
    await interaction.response.send_message("❌ Seul le staff peut faire ça.", ephemeral=True)
    return False


async def is_staff_or_owner(interaction: discord.Interaction) -> bool:
    topic = interaction.channel.topic or ""
    owner_id = extraire_owner_id(topic)
    if interaction.user.id == owner_id:
        return True
    return await is_staff(interaction)


async def generer_transcript(channel: discord.TextChannel, guild: discord.Guild, ferme_par: discord.User):
    messages = []
    async for msg in channel.history(limit=500, oldest_first=True):
        if msg.author.bot and not msg.embeds and not msg.content:
            continue
        contenu = discord.utils.escape_mentions(msg.content) if msg.content else "<em>[embed/composant]</em>"
        messages.append(
            f'<div class="msg"><span class="auteur">{discord.utils.escape_mentions(str(msg.author))}</span> '
            f'<span class="date">{msg.created_at.strftime("%d/%m/%Y %H:%M")}</span><br>'
            f'<span class="contenu">{contenu}</span></div>'
        )

    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Transcript {channel.name}</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #1e1e2e; color: #cdd6f4; padding: 20px; }}
  h1 {{ color: #89b4fa; }}
  .msg {{ background: #313244; margin: 8px 0; padding: 10px; border-radius: 8px; }}
  .auteur {{ font-weight: bold; color: #cba6f7; }}
  .date {{ font-size: 0.8em; color: #6c7086; margin-left: 10px; }}
  .contenu {{ margin-top: 4px; display: block; }}
</style></head><body>
<h1>📋 Transcript — {channel.name}</h1>
<p>Serveur : <b>{guild.name}</b> | Action par : <b>{ferme_par}</b> | Date : <b>{datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M")}</b></p>
<hr>{''.join(messages)}</body></html>"""

    os.makedirs("transcripts", exist_ok=True)
    filepath = f"transcripts/{channel.name}.html"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath


async def fermer_ticket(interaction: discord.Interaction):
    channel = interaction.channel
    guild = interaction.guild
    settings = load_settings()
    salon_transcript_id = settings.get(str(guild.id), {}).get("salon_transcript")

    await interaction.response.send_message("⏳ Fermeture du ticket en cours...")
    filepath = await generer_transcript(channel, guild, interaction.user)

    topic = channel.topic or ""
    nouveau_topic = topic.replace("status-open", "status-closed")
    await channel.edit(topic=nouveau_topic)

    owner_id = extraire_owner_id(topic)
    if owner_id:
        owner = guild.get_member(owner_id)
        if owner:
            await channel.set_permissions(owner, view_channel=True, send_messages=False, read_message_history=True)

    if salon_transcript_id:
        salon_transcript = guild.get_channel(salon_transcript_id)
        if salon_transcript:
            embed = discord.Embed(
                title=f"📋 Transcript — {channel.name}",
                description=f"Fermé par {interaction.user.mention}",
                color=discord.Color.greyple(),
                timestamp=datetime.datetime.utcnow()
            )
            await salon_transcript.send(embed=embed, file=discord.File(filepath))

    embed_ferme = discord.Embed(
        title="🔒 Ticket fermé",
        description=f"Ce ticket a été fermé par {interaction.user.mention}.\nUtilise le bouton ci-dessous pour le réouvrir si besoin.",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    await channel.send(embed=embed_ferme, view=PanelTicketFerme())
    await log_ticket(guild, f"🔒 **Ticket fermé** : {channel.mention} par {interaction.user.mention}")


# ── Cog principal ──────────────────────────────────────────────

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(PanelOuvrirTicket())
        bot.add_view(PanelGestionTicket())
        bot.add_view(PanelTicketFerme())

    @app_commands.command(name="setup-tickets", description="Configure le système de tickets via un menu interactif")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        view = SetupTicketsView(interaction.guild)
        await interaction.response.send_message(embed=view.embed_recap(), view=view, ephemeral=True)
        view.message = await interaction.original_response()

    @setup_tickets.error
    async def setup_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)

    @app_commands.command(name="ticket-stats", description="Affiche les statistiques des tickets")
    async def ticket_stats(self, interaction: discord.Interaction):
        settings = load_settings()
        guild_settings = settings.get(str(interaction.guild.id), {})
        total = guild_settings.get("ticket_count", 0)
        ouverts = sum(1 for c in interaction.guild.text_channels if c.topic and "status-open" in (c.topic or ""))

        embed = discord.Embed(title="📊 Statistiques des tickets", color=discord.Color.blurple())
        embed.add_field(name="🎫 Total créés", value=total, inline=True)
        embed.add_field(name="📬 Actuellement ouverts", value=ouverts, inline=True)
        await interaction.response.send_message(embed=embed)



# ── Setup Tickets Menu (style UltimeBots) ──────────────────────

class SetupTicketsView(discord.ui.View):
    """Panel central façon UltimeBots avec boutons ouvrant des sous-menus."""
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=300)
        self.guild = guild
        self.salon_id = None
        self.role_staff_id = None
        self.salon_transcript_id = None
        self.categorie_id = None
        self.message = None

    def embed_recap(self):
        salon = self.guild.get_channel(self.salon_id) if self.salon_id else None
        role = self.guild.get_role(self.role_staff_id) if self.role_staff_id else None
        transcript = self.guild.get_channel(self.salon_transcript_id) if self.salon_transcript_id else None
        categorie = self.guild.get_channel(self.categorie_id) if self.categorie_id else None

        embed = discord.Embed(title="🔧 Système de tickets", color=discord.Color.blurple())
        embed.add_field(name="📌 Salon du panel", value=salon.mention if salon else "❌ Non configuré", inline=False)
        embed.add_field(name="👮 Rôle staff", value=role.mention if role else "❌ Non configuré", inline=False)
        embed.add_field(name="📋 Salon transcripts", value=transcript.mention if transcript else "❌ Non configuré", inline=False)
        embed.add_field(name="📁 Catégorie", value=categorie.name if categorie else "Aucune (optionnel)", inline=False)
        embed.set_footer(text="Configure chaque option puis clique sur Déployer le panel.")
        return embed

    async def refresh(self, interaction: discord.Interaction):
        try:
            await self.message.edit(embed=self.embed_recap(), view=self)
        except:
            pass

    @discord.ui.button(label="Salon du panel", emoji="📌", style=discord.ButtonStyle.secondary, row=0)
    async def btn_salon(self, interaction: discord.Interaction, button: discord.ui.Button):
        options = [discord.SelectOption(label=f"#{c.name}", value=str(c.id)) for c in prioriser_salons(self.guild, "ticket")[:25]]
        await interaction.response.send_message("📌 Choisis le salon où envoyer le panel :", view=SousMenuSelect(self, "salon_id", options), ephemeral=True)

    @discord.ui.button(label="Rôle staff", emoji="👮", style=discord.ButtonStyle.secondary, row=0)
    async def btn_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        options = [discord.SelectOption(label=r.name, value=str(r.id)) for r in self.guild.roles[1:][:25]]
        await interaction.response.send_message("👮 Choisis le rôle staff :", view=SousMenuSelect(self, "role_staff_id", options), ephemeral=True)

    @discord.ui.button(label="Transcripts", emoji="📋", style=discord.ButtonStyle.secondary, row=0)
    async def btn_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        options = [discord.SelectOption(label=f"#{c.name}", value=str(c.id)) for c in prioriser_salons(self.guild, "transcript")[:25]]
        await interaction.response.send_message("📋 Choisis le salon des transcripts :", view=SousMenuSelect(self, "salon_transcript_id", options), ephemeral=True)

    @discord.ui.button(label="Catégorie", emoji="📁", style=discord.ButtonStyle.secondary, row=1)
    async def btn_categorie(self, interaction: discord.Interaction, button: discord.ui.Button):
        options = [discord.SelectOption(label="Aucune catégorie", value="0")]
        options += [discord.SelectOption(label=c.name, value=str(c.id)) for c in self.guild.categories[:24]]
        await interaction.response.send_message("📁 Choisis la catégorie où créer les tickets :", view=SousMenuSelect(self, "categorie_id", options), ephemeral=True)

    @discord.ui.button(label="Réinitialiser", emoji="🔄", style=discord.ButtonStyle.danger, row=1)
    async def btn_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.salon_id = None
        self.role_staff_id = None
        self.salon_transcript_id = None
        self.categorie_id = None
        await interaction.response.edit_message(embed=self.embed_recap(), view=self)

    @discord.ui.button(label="Déployer le panel", emoji="🚀", style=discord.ButtonStyle.success, row=2)
    async def btn_deployer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.salon_id or not self.role_staff_id or not self.salon_transcript_id:
            return await interaction.response.send_message("❌ Tu dois configurer le salon, le rôle staff et les transcripts avant de déployer.", ephemeral=True)

        settings = load_settings()
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = {}
        settings[guild_id]["role_staff"] = self.role_staff_id
        settings[guild_id]["salon_transcript"] = self.salon_transcript_id
        if self.categorie_id:
            settings[guild_id]["categorie_tickets"] = self.categorie_id
        save_settings(settings)

        salon = interaction.guild.get_channel(self.salon_id)
        embed_panel = discord.Embed(
            title="🎫 Centre de support",
            description=(
                "Besoin d'aide, envie de postuler, ou autre demande ?\n\n"
                "Choisis une catégorie dans le menu ci-dessous pour ouvrir un ticket.\n"
                "Notre équipe te répondra dès que possible."
            ),
            color=discord.Color.blurple()
        )
        embed_panel.set_footer(text=interaction.guild.name)
        await salon.send(embed=embed_panel, view=PanelOuvrirTicket())

        await interaction.response.edit_message(
            embed=discord.Embed(title="✅ Panel déployé !", description=f"Le panel a été envoyé dans {salon.mention}.", color=discord.Color.green()),
            view=None
        )


class SousMenuSelect(discord.ui.View):
    """Sous-menu temporaire pour choisir une valeur, met à jour le panel principal au retour."""
    def __init__(self, parent_view: SetupTicketsView, attribut: str, options: list):
        super().__init__(timeout=60)
        self.parent_view = parent_view
        self.attribut = attribut

        select = discord.ui.Select(placeholder="Choisis une option...", options=options)
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        valeur = self.children[0].values[0]
        setattr(self.parent_view, self.attribut, int(valeur) if valeur != "0" else None)
        await self.parent_view.refresh(interaction)
        await interaction.response.edit_message(content="✅ Choix enregistré ! Tu peux fermer ce message.", view=None)


async def setup(bot):
    await bot.add_cog(Tickets(bot))