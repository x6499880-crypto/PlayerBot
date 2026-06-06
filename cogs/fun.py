import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
 
REPONSES_8BALL = [
    "Absolument !", "C'est certain.", "Sans aucun doute.", "Oui, définitivement.",
    "Tu peux compter dessus.", "Très probable.", "Les signes pointent vers oui.",
    "Réponse floue, réessaie.", "Mieux vaut ne pas te le dire maintenant.",
    "Ne compte pas dessus.", "Ma réponse est non.", "Mes sources disent non.",
    "Les perspectives ne sont pas bonnes.", "Très douteux."
]
 
BLAGUES = [
    "Pourquoi les plongeurs plongent-ils toujours en arrière ? Parce que sinon ils tomberaient dans le bateau !",
    "Qu'est-ce qu'un canif ? Un petit fien !",
    "Pourquoi les squelettes ne se battent pas entre eux ? Ils n'ont pas le cran !",
    "Comment appelle-t-on un chat tombé dans un pot de peinture le jour de Noël ? Un chat-peint de Noël !",
    "Qu'est-ce qu'un crocodile qui surveille la cour ? Un sac à dents !",
    "Pourquoi les scientifiques n'ont pas trouvé de vie sur la Lune ? Parce qu'ils l'ont cherchée de jour !",
    "Qu'est-ce qu'un chien sans pattes ? Peu importe, tu peux pas l'amener en balade !",
]
 
ACTIONS_OU_VERITES = [
    "Action : Fais 10 pompes !", "Vérité : Quelle est ta plus grande peur ?",
    "Action : Imite quelqu'un dans le salon vocal !", "Vérité : Quel est ton secret le plus gênant ?",
    "Action : Chante le début d'une chanson !", "Vérité : Qui est ton crush sur le serveur ?",
    "Action : Fais 3 tours sur toi-même !", "Vérité : Quelle est la chose la plus stupide que tu aies faite ?",
]
 
class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quiz_actif = {}
 
    @app_commands.command(name="8ball", description="Pose une question à la boule magique")
    @app_commands.describe(question="Ta question")
    async def ball8(self, interaction: discord.Interaction, question: str):
        reponse = random.choice(REPONSES_8BALL)
        embed = discord.Embed(
            title="🎱 Boule Magique",
            color=discord.Color.purple()
        )
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="🔮 Réponse", value=reponse, inline=False)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="pileouface", description="Lance une pièce de monnaie")
    async def pileouface(self, interaction: discord.Interaction):
        resultat = random.choice(["🪙 Pile !", "🪙 Face !"])
        await interaction.response.send_message(f"La pièce tombe sur... **{resultat}**")
 
    @app_commands.command(name="roll", description="Lance un dé")
    @app_commands.describe(faces="Nombre de faces du dé (défaut: 6)")
    async def roll(self, interaction: discord.Interaction, faces: int = 6):
        if faces < 2:
            return await interaction.response.send_message("❌ Le dé doit avoir au moins 2 faces.", ephemeral=True)
        resultat = random.randint(1, faces)
        await interaction.response.send_message(f"🎲 Tu lances un dé à **{faces}** faces... **{resultat}** !")
 
    @app_commands.command(name="chifoumi", description="Joue au pierre-feuille-ciseaux contre le bot")
    @app_commands.describe(choix="Ton choix")
    @app_commands.choices(choix=[
        app_commands.Choice(name="Pierre", value="pierre"),
        app_commands.Choice(name="Feuille", value="feuille"),
        app_commands.Choice(name="Ciseaux", value="ciseaux"),
    ])
    async def chifoumi(self, interaction: discord.Interaction, choix: str):
        bot_choix = random.choice(["pierre", "feuille", "ciseaux"])
        emojis = {"pierre": "🪨", "feuille": "📄", "ciseaux": "✂️"}
 
        if choix == bot_choix:
            resultat = "Égalité ! 🤝"
        elif (choix == "pierre" and bot_choix == "ciseaux") or \
             (choix == "feuille" and bot_choix == "pierre") or \
             (choix == "ciseaux" and bot_choix == "feuille"):
            resultat = "Tu gagnes ! 🎉"
        else:
            resultat = "Tu perds ! 😈"
 
        embed = discord.Embed(title="✂️ Pierre-Feuille-Ciseaux", color=discord.Color.blurple())
        embed.add_field(name="Ton choix", value=f"{emojis[choix]} {choix.capitalize()}", inline=True)
        embed.add_field(name="Mon choix", value=f"{emojis[bot_choix]} {bot_choix.capitalize()}", inline=True)
        embed.add_field(name="Résultat", value=resultat, inline=False)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="blague", description="Raconte une blague aléatoire")
    async def blague(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"😂 {random.choice(BLAGUES)}")
 
    @app_commands.command(name="avatar", description="Affiche la photo de profil d'un membre")
    @app_commands.describe(membre="Le membre dont tu veux voir l'avatar")
    async def avatar(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        embed = discord.Embed(title=f"🖼️ Avatar de {membre.display_name}", color=discord.Color.blurple())
        embed.set_image(url=membre.display_avatar.url)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="actionouverite", description="Action ou Vérité aléatoire")
    async def actionouverite(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🎭 {random.choice(ACTIONS_OU_VERITES)}")
 
    @app_commands.command(name="lovecalc", description="Calcule le pourcentage d'amour entre deux membres")
    @app_commands.describe(membre1="Premier membre", membre2="Deuxième membre")
    async def lovecalc(self, interaction: discord.Interaction, membre1: discord.Member, membre2: discord.Member):
        pourcentage = random.randint(0, 100)
        if pourcentage >= 80:
            emoji = "💞"
        elif pourcentage >= 50:
            emoji = "💕"
        elif pourcentage >= 20:
            emoji = "💔"
        else:
            emoji = "😬"
        embed = discord.Embed(
            title=f"{emoji} Love Calculator",
            description=f"**{membre1.display_name}** + **{membre2.display_name}** = **{pourcentage}%** d'amour !",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="say", description="Fait répéter un message au bot")
    @app_commands.describe(message="Le message à répéter")
    @app_commands.checks.has_permissions(administrator=True)
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message("✅ Message envoyé !", ephemeral=True)
        await interaction.channel.send(message)
 
    @app_commands.command(name="sondage", description="Crée un sondage")
    @app_commands.describe(question="La question du sondage")
    async def sondage(self, interaction: discord.Interaction, question: str):
        embed = discord.Embed(
            title="📊 Sondage",
            description=question,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Sondage créé par {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("🟢")
        await msg.add_reaction("🔴")
 
    @app_commands.command(name="quiz", description="Lance une question de culture générale")
    async def quiz(self, interaction: discord.Interaction):
        questions = [
            {"question": "Quelle est la capitale de la France ?", "reponse": "paris"},
            {"question": "Combien font 7 x 8 ?", "reponse": "56"},
            {"question": "Quel est le plus grand océan du monde ?", "reponse": "pacifique"},
            {"question": "En quelle année a eu lieu la Révolution française ?", "reponse": "1789"},
            {"question": "Quel est l'animal le plus rapide du monde ?", "reponse": "guépard"},
        ]
        q = random.choice(questions)
        self.quiz_actif[interaction.channel.id] = q["reponse"]
 
        embed = discord.Embed(
            title="🧠 Quiz !",
            description=q["question"],
            color=discord.Color.gold()
        )
        embed.set_footer(text="Le premier qui répond correctement gagne !")
        await interaction.response.send_message(embed=embed)
 
        def check(m):
            return m.channel.id == interaction.channel.id and not m.author.bot
 
        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            if msg.content.lower() == q["reponse"]:
                await msg.channel.send(f"🎉 Bravo {msg.author.mention} ! La bonne réponse était **{q['reponse']}** !")
            else:
                await msg.channel.send(f"❌ Mauvaise réponse ! La bonne réponse était **{q['reponse']}**.")
        except asyncio.TimeoutError:
            await interaction.channel.send(f"⏰ Temps écoulé ! La réponse était **{q['reponse']}**.")
        finally:
            self.quiz_actif.pop(interaction.channel.id, None)
 
async def setup(bot):
    await bot.add_cog(Fun(bot))
 