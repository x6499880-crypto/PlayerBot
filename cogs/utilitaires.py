
import discord
from discord import app_commands
from discord.ext import commands
import datetime
 
# ── Pages du /help ─────────────────────────────────────────────
 
def page_utilitaires():
    embed = discord.Embed(title="📖 Aide — 🛠️ Utilitaires", color=discord.Color.blurple(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="🛠️ Utilitaires", value=(
        "`/ping` — Latence du bot\n"
        "`/info-serveur` — Infos du serveur\n"
        "`/info-membre` — Infos d'un membre\n"
        "`/botinfo` — Infos du bot\n"
        "`/tiktok` — Lien vers notre TikTok\n"
        "`/calc` — Calculatrice\n"
        "`/rappel` — Programme un rappel\n"
        "`/suggestion` — Envoie une suggestion"
    ), inline=False)
    embed.set_footer(text="Page 1/6")
    return embed
 
def page_fun():
    embed = discord.Embed(title="📖 Aide — 🎮 Fun", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="🎮 Fun", value=(
        "`/8ball` — Boule magique\n"
        "`/pileouface` — Lance une pièce\n"
        "`/roll` — Lance un dé\n"
        "`/chifoumi` — Pierre-feuille-ciseaux\n"
        "`/blague` — Blague aléatoire\n"
        "`/avatar` — Affiche un avatar\n"
        "`/actionouverite` — Action ou Vérité\n"
        "`/lovecalc` — Calcul d'amour\n"
        "`/sondage` — Crée un sondage\n"
        "`/quiz` — Question de culture générale"
    ), inline=False)
    embed.set_footer(text="Page 2/6")
    return embed
 
def page_economie():
    embed = discord.Embed(title="📖 Aide — 💰 Économie", color=discord.Color.gold(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="💰 Économie", value=(
        "`/daily` — Récompense quotidienne\n"
        "`/money` — Voir son solde\n"
        "`/work` — Travailler pour gagner des coins\n"
        "`/pay` — Transférer des coins\n"
        "`/coinflip-bet` — Parier sur pile ou face\n"
        "`/slots` — Machine à sous\n"
        "`/rob` — Voler un membre\n"
        "`/leaderboard` — Classement des plus riches"
    ), inline=False)
    embed.set_footer(text="Page 3/6")
    return embed
 
def page_divers():
    embed = discord.Embed(title="📖 Aide — 🎯 Divers", color=discord.Color.purple(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="🔢 Comptage", value="`/comptage-info` — Compteur actuel et record", inline=False)
    embed.add_field(name="🎙️ Vocal", value="Rejoins le salon **Ton Vocal** pour créer ton salon vocal temporaire.", inline=False)
    embed.add_field(name="🎫 Tickets", value="Clique sur le bouton dans le salon de support pour ouvrir un salon **tickets**.", inline=False)
    embed.set_footer(text="Page 4/6")
    return embed
 
def page_moderation():
    embed = discord.Embed(title="📖 Aide — 🔨 Modération (Admin)", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="🔨 Modération", value=(
        "`/ban` — Bannir un membre\n"
        "`/unban` — Débannir un membre\n"
        "`/tempban` — Bannir temporairement\n"
        "`/kick` — Expulser un membre\n"
        "`/mute` — Mettre en timeout\n"
        "`/unmute` — Retirer le timeout\n"
        "`/clear` — Supprimer des messages\n"
        "`/nuke` — Effacer l'historique du salon\n"
        "`/warn` — Avertir un membre\n"
        "`/seewarns` — Voir les avertissements\n"
        "`/clearwarns` — Effacer les avertissements\n"
        "`/slowmode` — Mode lent\n"
        "`/lock` — Verrouiller le salon\n"
        "`/unlock` — Déverrouiller le salon"
    ), inline=False)
    embed.set_footer(text="Page 5/6")
    return embed
 
def page_config():
    embed = discord.Embed(title="📖 Aide — ⚙️ Configuration (Admin)", color=discord.Color.orange(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="⚙️ Configuration", value=(
        "`/set-bienvenue` — Salon des messages de bienvenue\n"
        "`/test-bienvenue` — Tester le message de bienvenue\n"
        "`/setup-tickets` — Configurer le système de tickets\n"
        "`/setup-comptage` — Configurer le salon de comptage\n"
        "`/reset-comptage` — Remettre le compteur à 0\n"
        "`/setup-vocal` — Configurer les salons vocaux\n"
        "`/setup-logs` — Configurer les salons de logs\n"
        "`/commandes` — Afficher les commandes membres\n"
        "`/say` — Faire parler le bot"
    ), inline=False)
    embed.set_footer(text="Page 6/6")
    return embed
 
PAGES_MEMBRES = [page_utilitaires, page_fun, page_economie, page_divers]
PAGES_ADMIN = [page_utilitaires, page_fun, page_economie, page_divers, page_moderation, page_config]
 
 
# ── Vue avec boutons de navigation ─────────────────────────────
 
class HelpView(discord.ui.View):
    def __init__(self, is_admin: bool):
        super().__init__(timeout=120)
        self.pages = PAGES_ADMIN if is_admin else PAGES_MEMBRES
        self.current = 0
        self.update_buttons()
 
    def update_buttons(self):
        self.children[0].disabled = self.current == 0
        self.children[1].disabled = self.current == len(self.pages) - 1
 
    @discord.ui.button(label="◀ Précédent", style=discord.ButtonStyle.secondary)
    async def precedent(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current](), view=self)
 
    @discord.ui.button(label="Suivant ▶", style=discord.ButtonStyle.secondary)
    async def suivant(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current](), view=self)
 
    @discord.ui.button(label="🛠️", style=discord.ButtonStyle.primary)
    async def utilitaires(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current](), view=self)
 
    @discord.ui.button(label="🎮", style=discord.ButtonStyle.primary)
    async def fun(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current](), view=self)
 
    @discord.ui.button(label="💰", style=discord.ButtonStyle.primary)
    async def economie(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = 2
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current](), view=self)
 
 
# ── Cog Utilitaires ────────────────────────────────────────────
 
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
        embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.blurple(), timestamp=datetime.datetime.utcnow())
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
        embed = discord.Embed(title=f"👤 {membre.display_name}", color=membre.color, timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="🆔 ID", value=membre.id, inline=True)
        embed.add_field(name="📅 Compte créé", value=membre.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="📥 Rejoint le", value=membre.joined_at.strftime("%d/%m/%Y"), inline=True)
        roles = [r.mention for r in membre.roles[1:]]
        embed.add_field(name="🎭 Rôles", value=", ".join(roles) if roles else "Aucun", inline=False)
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
 
    @app_commands.command(name="commandes", description="Affiche les commandes disponibles pour les membres")
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
            "`/botinfo` — Infos du bot\n"
            "`/tiktok` — Lien vers notre TikTok\n"
            "`/calc` — Calculatrice\n"
            "`/rappel` — Programme un rappel\n"
            "`/suggestion` — Envoie une suggestion"
        ), inline=False)
        embed.add_field(name="🎮 Fun", value=(
            "`/8ball` — Boule magique\n"
            "`/pileouface` — Lance une pièce\n"
            "`/roll` — Lance un dé\n"
            "`/chifoumi` — Pierre-feuille-ciseaux\n"
            "`/blague` — Blague aléatoire\n"
            "`/avatar` — Affiche un avatar\n"
            "`/actionouverite` — Action ou Vérité\n"
            "`/lovecalc` — Calcul d'amour\n"
            "`/sondage` — Crée un sondage\n"
            "`/quiz` — Question de culture générale"
        ), inline=False)
        embed.add_field(name="💰 Économie", value=(
            "`/daily` — Récompense quotidienne\n"
            "`/money` — Voir son solde\n"
            "`/work` — Travailler pour gagner des coins\n"
            "`/pay` — Transférer des coins\n"
            "`/coinflip-bet` — Parier sur pile ou face\n"
            "`/slots` — Machine à sous\n"
            "`/rob` — Voler un membre\n"
            "`/leaderboard` — Classement des plus riches"
        ), inline=False)
        embed.add_field(name="🔢 Comptage", value="`/comptage-info` — Compteur actuel et record", inline=False)
        embed.add_field(name="🎙️ Vocal", value="Rejoins le salon **Ton Vocal** pour créer ton salon vocal temporaire.", inline=False)
        embed.add_field(name="🎫 Tickets", value="Clique sur le bouton dans le salon de support pour ouvrir un salon **tickets**.", inline=False)
        embed.set_footer(text=interaction.guild.name)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="help", description="Affiche la liste des commandes")
    async def help(self, interaction: discord.Interaction):
        is_admin = interaction.user.guild_permissions.administrator
        view = HelpView(is_admin=is_admin)
        await interaction.response.send_message(embed=page_utilitaires(), view=view, ephemeral=True)
 
async def setup(bot):
    await bot.add_cog(Utilitaires(bot))
 