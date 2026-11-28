import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import ast
import math
import operator


# --- Évaluateur mathématique sécurisé (remplace eval) -----------------------
# Seuls les nombres, les opérateurs arithmétiques et une liste blanche de
# fonctions/constantes de `math` sont autorisés. Aucun accès aux attributs,
# aux noms arbitraires, aux appels de méthodes ou aux compréhensions.

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

_FUNCS = {
    name: getattr(math, name)
    for name in (
        "sqrt", "sin", "cos", "tan", "asin", "acos", "atan",
        "log", "log10", "log2", "exp", "floor", "ceil", "fabs",
        "radians", "degrees",
    )
}
_FUNCS.update({"abs": abs, "round": round})
_CONSTS = {"pi": math.pi, "e": math.e, "tau": math.tau}

_MAX_EXPR_LEN = 200
_MAX_NUMBER = 10 ** 100
_MAX_EXPONENT = 1000


def _check(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Résultat non numérique")
    if abs(value) > _MAX_NUMBER:
        raise ValueError("Nombre trop grand")
    return value


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return _check(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_EXPONENT:
            raise ValueError("Exposant trop grand")
        return _check(_BIN_OPS[type(node.op)](left, right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _check(_UNARY_OPS[type(node.op)](_eval_node(node.operand)))
    if isinstance(node, ast.Name) and node.id in _CONSTS:
        return _CONSTS[node.id]
    # Accepte aussi la forme "math.sqrt(...)" / "math.pi" par compatibilité
    if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == "math" and node.attr in _CONSTS):
        return _CONSTS[node.attr]
    if isinstance(node, ast.Call) and not node.keywords:
        func = node.func
        if isinstance(func, ast.Name):
            name = func.id
        elif (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
              and func.value.id == "math"):
            name = func.attr
        else:
            raise ValueError("Fonction non autorisée")
        if name not in _FUNCS:
            raise ValueError("Fonction non autorisée")
        args = [_eval_node(a) for a in node.args]
        return _check(_FUNCS[name](*args))
    raise ValueError("Expression non autorisée")


def safe_calc(expression: str):
    if len(expression) > _MAX_EXPR_LEN:
        raise ValueError("Expression trop longue")
    tree = ast.parse(expression.replace("^", "**"), mode="eval")
    return _eval_node(tree)


class Utilitaires2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    @app_commands.command(name="botinfo", description="Affiche les informations du bot")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Informations du bot", color=discord.Color.blurple())
        embed.add_field(name="📛 Nom", value=self.bot.user.name, inline=True)
        embed.add_field(name="🆔 ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="🖥️ Serveurs", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="👥 Membres", value=sum(g.member_count for g in self.bot.guilds), inline=True)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="suggestion", description="Envoie une suggestion dans le salon dédié")
    @app_commands.describe(texte="Ta suggestion", salon="Le salon où envoyer la suggestion")
    async def suggestion(self, interaction: discord.Interaction, texte: str, salon: discord.TextChannel):
        embed = discord.Embed(
            title="💡 Nouvelle suggestion",
            description=texte,
            color=discord.Color.yellow(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Suggéré par {interaction.user.display_name}")
        msg = await salon.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await interaction.response.send_message(f"✅ Ta suggestion a été envoyée dans {salon.mention} !", ephemeral=True)
 
    @app_commands.command(name="rappel", description="Programme un rappel")
    @app_commands.describe(duree="Durée en minutes", message="Le message de rappel")
    async def rappel(self, interaction: discord.Interaction, duree: int, message: str):
        if duree <= 0:
            return await interaction.response.send_message("❌ La durée doit être positive.", ephemeral=True)
        await interaction.response.send_message(f"⏰ Je te rappellerai dans **{duree} minute(s)** : {message}")
        await asyncio.sleep(duree * 60)
        await interaction.followup.send(f"⏰ {interaction.user.mention} Rappel : **{message}**")
 
    @app_commands.command(name="calc", description="Résout un calcul mathématique")
    @app_commands.describe(calcul="Le calcul à effectuer (ex: 23*45)")
    async def calc(self, interaction: discord.Interaction, calcul: str):
        try:
            resultat = safe_calc(calcul)
        except (ValueError, SyntaxError, TypeError, ZeroDivisionError, OverflowError, RecursionError, MemoryError):
            return await interaction.response.send_message("❌ Calcul invalide.", ephemeral=True)
        calcul_affiche = discord.utils.escape_markdown(calcul).replace("`", "")
        await interaction.response.send_message(
            f"🧮 `{calcul_affiche}` = **{resultat}**",
            allowed_mentions=discord.AllowedMentions.none(),
        )
 
    @app_commands.command(name="slowmode", description="Active le mode lent sur le salon")
    @app_commands.describe(secondes="Délai en secondes (0 pour désactiver)")
    @app_commands.checks.has_permissions(administrator=True)
    async def slowmode(self, interaction: discord.Interaction, secondes: int):
        await interaction.channel.edit(slowmode_delay=secondes)
        if secondes == 0:
            await interaction.response.send_message("✅ Mode lent désactivé.")
        else:
            await interaction.response.send_message(f"✅ Mode lent activé : **{secondes} secondes** entre chaque message.")
 
    @app_commands.command(name="lock", description="Verrouille le salon actuel")
    @app_commands.checks.has_permissions(administrator=True)
    async def lock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 Salon verrouillé.")
 
    @app_commands.command(name="unlock", description="Déverrouille le salon actuel")
    @app_commands.checks.has_permissions(administrator=True)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 Salon déverrouillé.")
 
    @app_commands.command(name="nuke", description="Clone et supprime le salon pour effacer son historique")
    @app_commands.checks.has_permissions(administrator=True)
    async def nuke(self, interaction: discord.Interaction):
        channel = interaction.channel
        new_channel = await channel.clone(reason="Nuke")
        await new_channel.edit(position=channel.position)
        await channel.delete()
        await new_channel.send("💥 Salon nuke ! L'historique a été effacé.")
 
    @app_commands.command(name="warn", description="Avertit un membre")
    @app_commands.describe(membre="Le membre à avertir", raison="Raison de l'avertissement")
    @app_commands.checks.has_permissions(administrator=True)
    async def warn(self, interaction: discord.Interaction, membre: discord.Member, raison: str):
        import json, os
        warns_file = "warns.json"
        data = json.load(open(warns_file)) if os.path.exists(warns_file) else {}
        gid = str(interaction.guild.id)
        uid = str(membre.id)
        if gid not in data: data[gid] = {}
        if uid not in data[gid]: data[gid][uid] = []
        warn_id = len(data[gid][uid]) + 1
        data[gid][uid].append({"id": warn_id, "raison": raison, "par": str(interaction.user.id)})
        json.dump(data, open(warns_file, "w"), indent=4)
 
        embed = discord.Embed(title="⚠️ Avertissement", color=discord.Color.orange())
        embed.add_field(name="Membre", value=membre.mention, inline=True)
        embed.add_field(name="Raison", value=raison, inline=True)
        embed.add_field(name="Warn #", value=warn_id, inline=True)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="seewarns", description="Affiche les avertissements d'un membre")
    @app_commands.describe(membre="Le membre à inspecter")
    @app_commands.checks.has_permissions(administrator=True)
    async def seewarns(self, interaction: discord.Interaction, membre: discord.Member):
        import json, os
        warns_file = "warns.json"
        data = json.load(open(warns_file)) if os.path.exists(warns_file) else {}
        warns = data.get(str(interaction.guild.id), {}).get(str(membre.id), [])
 
        embed = discord.Embed(title=f"⚠️ Avertissements de {membre.display_name}", color=discord.Color.orange())
        if not warns:
            embed.description = "Aucun avertissement."
        else:
            for w in warns:
                embed.add_field(name=f"Warn #{w['id']}", value=w['raison'], inline=False)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="clearwarns", description="Efface tous les avertissements d'un membre")
    @app_commands.describe(membre="Le membre")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearwarns(self, interaction: discord.Interaction, membre: discord.Member):
        import json, os
        warns_file = "warns.json"
        data = json.load(open(warns_file)) if os.path.exists(warns_file) else {}
        gid = str(interaction.guild.id)
        uid = str(membre.id)
        if gid in data and uid in data[gid]:
            data[gid][uid] = []
            json.dump(data, open(warns_file, "w"), indent=4)
        await interaction.response.send_message(f"✅ Tous les avertissements de {membre.mention} ont été effacés.")
 
    @app_commands.command(name="tempban", description="Bannit temporairement un membre")
    @app_commands.describe(membre="Le membre", duree="Durée en minutes", raison="Raison")
    @app_commands.checks.has_permissions(administrator=True)
    async def tempban(self, interaction: discord.Interaction, membre: discord.Member, duree: int, raison: str = "Aucune raison"):
        await membre.ban(reason=raison)
        await interaction.response.send_message(f"🔨 {membre.mention} a été banni pour **{duree} minutes**. Raison : {raison}")
        await asyncio.sleep(duree * 60)
        await interaction.guild.unban(discord.Object(id=membre.id))
 
async def setup(bot):
    await bot.add_cog(Utilitaires2(bot))
 