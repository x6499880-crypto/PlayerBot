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
 
 
# ── Panel de contrôle ──────────────────────────────────────────
 
class PanelVocal(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id
 
    async def check_owner(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Tu n'es pas le propriétaire de ce salon.", ephemeral=True)
            return False
        return True
 
    @discord.ui.button(label="✏️ Renommer", style=discord.ButtonStyle.primary, custom_id="vocal_rename", row=0)
    async def renommer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.response.send_modal(ModalRenommer())
 
    @discord.ui.button(label="👥 Limite", style=discord.ButtonStyle.primary, custom_id="vocal_limit", row=0)
    async def limite(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        await interaction.response.send_modal(ModalLimite())
 
    @discord.ui.button(label="🔒 Verrouiller", style=discord.ButtonStyle.danger, custom_id="vocal_lock", row=1)
    async def verrouiller(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            return await interaction.response.send_message("❌ Tu n'es pas dans un salon vocal.", ephemeral=True)
        await channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Salon verrouillé.", ephemeral=True)
 
    @discord.ui.button(label="🔓 Déverrouiller", style=discord.ButtonStyle.success, custom_id="vocal_unlock", row=1)
    async def deverrouiller(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            return await interaction.response.send_message("❌ Tu n'es pas dans un salon vocal.", ephemeral=True)
        await channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Salon déverrouillé.", ephemeral=True)
 
    @discord.ui.button(label="👢 Expulser", style=discord.ButtonStyle.danger, custom_id="vocal_kick", row=2)
    async def expulser(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            return await interaction.response.send_message("❌ Tu n'es pas dans un salon vocal.", ephemeral=True)
        membres = [m for m in channel.members if m.id != self.owner_id]
        if not membres:
            return await interaction.response.send_message("❌ Personne à expulser.", ephemeral=True)
        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in membres]
        await interaction.response.send_message(
            "Choisis qui expulser :",
            view=SelectExpulser(options, self.owner_id),
            ephemeral=True
        )
 
    @discord.ui.button(label="🙈 Masquer", style=discord.ButtonStyle.secondary, custom_id="vocal_hide", row=2)
    async def masquer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            return await interaction.response.send_message("❌ Tu n'es pas dans un salon vocal.", ephemeral=True)
        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message("🙈 Salon masqué.", ephemeral=True)
 
    @discord.ui.button(label="👁️ Afficher", style=discord.ButtonStyle.secondary, custom_id="vocal_show", row=2)
    async def afficher(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction):
            return
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            return await interaction.response.send_message("❌ Tu n'es pas dans un salon vocal.", ephemeral=True)
        await channel.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message("👁️ Salon visible.", ephemeral=True)
 
 
# ── Select : Expulser un membre ────────────────────────────────
 
class SelectExpulser(discord.ui.View):
    def __init__(self, options, owner_id):
        super().__init__(timeout=30)
        self.owner_id = owner_id
        select = discord.ui.Select(placeholder="Choisis un membre...", options=options)
        select.callback = self.callback
        self.add_item(select)
 
    async def callback(self, interaction: discord.Interaction):
        member_id = int(self.children[0].values[0])
        member = interaction.guild.get_member(member_id)
        if member and member.voice:
            await member.move_to(None)
            await interaction.response.send_message(f"👢 **{member.display_name}** a été expulsé du salon.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ce membre n'est plus dans le salon.", ephemeral=True)
 
 
# ── Modals ─────────────────────────────────────────────────────
 
class ModalRenommer(discord.ui.Modal, title="Renommer le salon"):
    nom = discord.ui.TextInput(label="Nouveau nom", placeholder="Ex: Salon de gaming", max_length=100)
 
    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            return await interaction.response.send_message("❌ Tu n'es pas dans un salon vocal.", ephemeral=True)
        await channel.edit(name=self.nom.value)
        await interaction.response.send_message(f"✅ Salon renommé en **{self.nom.value}**.", ephemeral=True)
 
 
class ModalLimite(discord.ui.Modal, title="Limite d'utilisateurs"):
    limite = discord.ui.TextInput(label="Limite (0 = illimitée)", placeholder="Ex: 5", max_length=2)
 
    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            return await interaction.response.send_message("❌ Tu n'es pas dans un salon vocal.", ephemeral=True)
        try:
            limit = int(self.limite.value)
            await channel.edit(user_limit=limit)
            msg = f"✅ Limite fixée à **{limit}**." if limit > 0 else "✅ Limite supprimée."
            await interaction.response.send_message(msg, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Entre un nombre valide.", ephemeral=True)
 
 
# ── Cog Vocal ──────────────────────────────────────────────────
 
class Vocal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels: dict[int, int] = {}  # channel_id → owner_id
 
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        settings = load_settings()
        guild_id = str(member.guild.id)
        hub_id = settings.get(guild_id, {}).get("vocal_hub")
        categorie_id = settings.get(guild_id, {}).get("vocal_categorie")
 
        # ── Rejoindre le hub → créer un salon temp ──
        if after.channel and after.channel.id == hub_id:
            categorie = member.guild.get_channel(categorie_id) if categorie_id else after.channel.category
 
            salon = await member.guild.create_voice_channel(
                name=f"Vocal [{member.display_name}]",
                category=categorie,
                user_limit=0
            )
            self.temp_channels[salon.id] = member.id
            await member.move_to(salon)
 
            # Envoyer le panel dans le chat intégré du salon vocal
            embed = discord.Embed(
                title="🎛️ Panneau de contrôle",
                description=f"{member.mention}, bienvenue dans ton salon !\nUtilise les boutons ci-dessous pour le gérer.",
                color=discord.Color.blurple()
            )
            embed.add_field(name="✏️ Renommer", value="Change le nom du salon", inline=True)
            embed.add_field(name="👥 Limite", value="Fixe le nombre de places", inline=True)
            embed.add_field(name="🔒/🔓", value="Verrouille ou ouvre l'accès", inline=True)
            embed.add_field(name="🙈/👁️", value="Masque ou affiche le salon", inline=True)
            embed.add_field(name="👢 Expulser", value="Kick quelqu'un du salon", inline=True)
            view = PanelVocal(owner_id=member.id)
            await salon.send(embed=embed, view=view)
 
        # ── Quitter un salon temp → supprimer si vide ──
        if before.channel and before.channel.id in self.temp_channels:
            if len(before.channel.members) == 0:
                del self.temp_channels[before.channel.id]
                try:
                    await before.channel.delete(reason="Salon vocal temporaire vide")
                except:
                    pass
 
    @app_commands.command(name="setup-vocal", description="Configure le système de salons vocaux temporaires")
    @app_commands.describe(
        hub="Le salon vocal hub où les membres rejoignent pour créer leur salon",
        categorie="La catégorie où créer les salons temporaires (optionnel)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_member_permissions(administrator=True)
    async def setup_vocal(
        self,
        interaction: discord.Interaction,
        hub: discord.VoiceChannel,
        categorie: discord.CategoryChannel = None
    ):
        settings = load_settings()
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = {}
 
        settings[guild_id]["vocal_hub"] = hub.id
        if categorie:
            settings[guild_id]["vocal_categorie"] = categorie.id
        save_settings(settings)
 
        embed = discord.Embed(
            title="✅ Système vocal configuré",
            color=discord.Color.green()
        )
        embed.add_field(name="🎙️ Salon hub", value=hub.mention, inline=True)
        if categorie:
            embed.add_field(name="📁 Catégorie", value=categorie.name, inline=True)
        embed.set_footer(text="Les membres rejoignent le hub pour créer leur salon !")
        await interaction.response.send_message(embed=embed)
 
    @setup_vocal.error
    async def vocal_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission.", ephemeral=True)
 
async def setup(bot):
    await bot.add_cog(Vocal(bot))
 