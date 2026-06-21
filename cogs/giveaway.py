import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import json
import os
import random
import re

GIVEAWAYS_FILE = "giveaways.json"
EMOJI_PARTICIPATION = "🎉"

def load_giveaways():
    if os.path.exists(GIVEAWAYS_FILE):
        with open(GIVEAWAYS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_giveaways(data):
    with open(GIVEAWAYS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def parse_duree(texte: str):
    """Convertit '10m', '2h', '1d' en secondes."""
    match = re.match(r"^(\d+)([smhd])$", texte.strip().lower())
    if not match:
        return None
    valeur, unite = int(match.group(1)), match.group(2)
    multiplicateurs = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return valeur * multiplicateurs[unite]


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @app_commands.command(name="giveaway", description="Lance un giveaway")
    @app_commands.describe(
        prix="Ce que le gagnant remporte",
        duree="Durée du giveaway (ex: 10m, 2h, 1d)",
        salon="Le salon où lancer le giveaway (par défaut: salon actuel)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, prix: str, duree: str, salon: discord.TextChannel = None):
        secondes = parse_duree(duree)
        if secondes is None:
            return await interaction.response.send_message(
                "❌ Format de durée invalide. Utilise par exemple : `10m`, `2h`, `1d`.", ephemeral=True
            )
        if secondes < 10:
            return await interaction.response.send_message("❌ La durée minimale est de 10 secondes.", ephemeral=True)

        salon = salon or interaction.channel
        fin = datetime.datetime.utcnow() + datetime.timedelta(seconds=secondes)
        fin_ts = int(fin.timestamp())

        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=(
                f"**Prix :** {prix}\n\n"
                f"Réagis avec {EMOJI_PARTICIPATION} pour participer !\n\n"
                f"⏰ Se termine <t:{fin_ts}:R> (<t:{fin_ts}:f>)\n"
                f"🎁 Organisé par {interaction.user.mention}"
            ),
            color=discord.Color.gold(),
            timestamp=fin
        )
        embed.set_footer(text="1 gagnant • Fin du giveaway")

        await interaction.response.send_message(f"✅ Giveaway lancé dans {salon.mention} !", ephemeral=True)
        msg = await salon.send(embed=embed)
        await msg.add_reaction(EMOJI_PARTICIPATION)

        giveaways = load_giveaways()
        guild_id = str(interaction.guild.id)
        if guild_id not in giveaways:
            giveaways[guild_id] = {}
        giveaways[guild_id][str(msg.id)] = {
            "salon_id": salon.id,
            "prix": prix,
            "fin": fin.isoformat(),
            "organisateur_id": interaction.user.id,
            "termine": False
        }
        save_giveaways(giveaways)

    @giveaway.error
    async def giveaway_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission de lancer un giveaway.", ephemeral=True)

    @app_commands.command(name="giveaway-reroll", description="Retire un nouveau gagnant pour un giveaway terminé")
    @app_commands.describe(message_id="L'ID du message du giveaway")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        giveaways = load_giveaways()
        guild_id = str(interaction.guild.id)
        data = giveaways.get(guild_id, {}).get(message_id)

        if not data:
            return await interaction.response.send_message("❌ Giveaway introuvable.", ephemeral=True)

        salon = interaction.guild.get_channel(data["salon_id"])
        if not salon:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)

        try:
            msg = await salon.fetch_message(int(message_id))
        except:
            return await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)

        gagnant = await tirer_gagnant(msg)
        if not gagnant:
            return await interaction.response.send_message("❌ Aucun participant valide trouvé.", ephemeral=True)

        await salon.send(f"🎉 Nouveau gagnant pour **{data['prix']}** : {gagnant.mention} !")
        await interaction.response.send_message("✅ Nouveau gagnant tiré !", ephemeral=True)

    @giveaway_reroll.error
    async def reroll_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas la permission.", ephemeral=True)

    @tasks.loop(seconds=15)
    async def check_giveaways(self):
        giveaways = load_giveaways()
        maintenant = datetime.datetime.utcnow()
        modifie = False

        for guild_id, guild_giveaways in giveaways.items():
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            for message_id, data in guild_giveaways.items():
                if data.get("termine"):
                    continue

                fin = datetime.datetime.fromisoformat(data["fin"])
                if maintenant < fin:
                    continue

                salon = guild.get_channel(data["salon_id"])
                if not salon:
                    data["termine"] = True
                    modifie = True
                    continue

                try:
                    msg = await salon.fetch_message(int(message_id))
                except:
                    data["termine"] = True
                    modifie = True
                    continue

                gagnant = await tirer_gagnant(msg)

                embed_fini = discord.Embed(
                    title="🎉 GIVEAWAY TERMINÉ 🎉",
                    description=(
                        f"**Prix :** {data['prix']}\n\n"
                        f"🏆 Gagnant : {gagnant.mention if gagnant else 'Aucun participant valide'}"
                    ),
                    color=discord.Color.greyple()
                )
                await msg.edit(embed=embed_fini)

                if gagnant:
                    await salon.send(f"🎉 Félicitations {gagnant.mention} ! Tu remportes **{data['prix']}** !")
                else:
                    await salon.send(f"😢 Personne n'a participé au giveaway pour **{data['prix']}**.")

                data["termine"] = True
                modifie = True

        if modifie:
            save_giveaways(giveaways)


async def tirer_gagnant(msg: discord.Message):
    for reaction in msg.reactions:
        if str(reaction.emoji) == EMOJI_PARTICIPATION:
            utilisateurs = [u async for u in reaction.users() if not u.bot]
            if utilisateurs:
                return random.choice(utilisateurs)
    return None


async def setup(bot):
    await bot.add_cog(Giveaway(bot))