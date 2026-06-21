import discord
from discord.ext import commands
import json
import os

SETTINGS_FILE = "settings.json"
DEFAULT_PREFIX = "+"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_prefix(bot, message):
    """Fonction utilisée par le bot pour déterminer le préfixe du serveur."""
    if not message.guild:
        return DEFAULT_PREFIX
    settings = load_settings()
    return settings.get(str(message.guild.id), {}).get("prefix", DEFAULT_PREFIX)


class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="prefix")
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, nouveau_prefix: str = None):
        """Affiche ou change le préfixe du serveur."""
        settings = load_settings()
        guild_id = str(ctx.guild.id)

        if nouveau_prefix is None:
            actuel = settings.get(guild_id, {}).get("prefix", DEFAULT_PREFIX)
            embed = discord.Embed(
                title="⚙️ Préfixe actuel",
                description=f"Le préfixe de ce serveur est : `{actuel}`\n\nPour le changer : `{actuel}prefix <nouveau_prefixe>`",
                color=discord.Color.blurple()
            )
            return await ctx.send(embed=embed)

        if len(nouveau_prefix) > 5:
            return await ctx.send("❌ Le préfixe doit faire 5 caractères maximum.")

        if guild_id not in settings:
            settings[guild_id] = {}
        settings[guild_id]["prefix"] = nouveau_prefix
        save_settings(settings)

        embed = discord.Embed(
            title="✅ Préfixe modifié",
            description=f"Le nouveau préfixe est désormais : `{nouveau_prefix}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @prefix.error
    async def prefix_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tu n'as pas la permission de changer le préfixe.")

    @commands.command(name="help")
    async def help_prefix(self, ctx):
        """Affiche la liste des commandes préfixées."""
        settings = load_settings()
        prefix = settings.get(str(ctx.guild.id), {}).get("prefix", DEFAULT_PREFIX)
        is_admin = ctx.author.guild_permissions.administrator

        embed = discord.Embed(
            title="📖 Aide — Commandes préfixées",
            description=f"Préfixe actuel : `{prefix}`",
            color=discord.Color.blurple()
        )
        embed.add_field(name="⚙️ Général", value=(
            f"`{prefix}help` — Affiche ce message\n"
            f"`{prefix}ping` — Latence du bot"
        ), inline=False)

        if is_admin:
            embed.add_field(name="🔧 Admin", value=(
                f"`{prefix}prefix [nouveau]` — Voir/changer le préfixe"
            ), inline=False)

        embed.set_footer(text="La plupart des commandes du bot sont aussi disponibles en slash (/) !")
        await ctx.send(embed=embed)

    @commands.command(name="ping")
    async def ping_prefix(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong ! Latence : **{latency}ms**")


async def setup(bot):
    await bot.add_cog(Prefix(bot))