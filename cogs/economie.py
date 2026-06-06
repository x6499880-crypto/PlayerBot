import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import datetime
 
ECONOMIE_FILE = "economie.json"
 
def load_eco():
    if os.path.exists(ECONOMIE_FILE):
        with open(ECONOMIE_FILE, "r") as f:
            return json.load(f)
    return {}
 
def save_eco(data):
    with open(ECONOMIE_FILE, "w") as f:
        json.dump(data, f, indent=4)
 
def get_user(data, guild_id, user_id):
    gid = str(guild_id)
    uid = str(user_id)
    if gid not in data:
        data[gid] = {}
    if uid not in data[gid]:
        data[gid][uid] = {"wallet": 0, "bank": 0, "last_daily": None, "last_work": None}
    return data[gid][uid]
 
class Economie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    @app_commands.command(name="daily", description="Récupère ta récompense quotidienne")
    async def daily(self, interaction: discord.Interaction):
        data = load_eco()
        user = get_user(data, interaction.guild.id, interaction.user.id)
        now = datetime.datetime.utcnow().date().isoformat()
 
        if user["last_daily"] == now:
            return await interaction.response.send_message("❌ Tu as déjà récupéré ta récompense aujourd'hui !", ephemeral=True)
 
        montant = random.randint(100, 300)
        user["wallet"] += montant
        user["last_daily"] = now
        save_eco(data)
        await interaction.response.send_message(f"💰 Tu as récupéré **{montant} coins** ! Reviens demain pour plus.")
 
    @app_commands.command(name="money", description="Affiche ton solde")
    @app_commands.describe(membre="Le membre dont tu veux voir le solde")
    async def money(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        data = load_eco()
        user = get_user(data, interaction.guild.id, membre.id)
        save_eco(data)
 
        embed = discord.Embed(title=f"💰 Solde de {membre.display_name}", color=discord.Color.gold())
        embed.add_field(name="👛 Portefeuille", value=f"{user['wallet']} coins", inline=True)
        embed.add_field(name="🏦 Banque", value=f"{user['bank']} coins", inline=True)
        embed.add_field(name="💎 Total", value=f"{user['wallet'] + user['bank']} coins", inline=True)
        await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="work", description="Travaille pour gagner des coins")
    async def work(self, interaction: discord.Interaction):
        data = load_eco()
        user = get_user(data, interaction.guild.id, interaction.user.id)
        now = datetime.datetime.utcnow()
 
        if user["last_work"]:
            last = datetime.datetime.fromisoformat(user["last_work"])
            diff = (now - last).total_seconds()
            if diff < 3600:
                restant = int(3600 - diff)
                mins = restant // 60
                return await interaction.response.send_message(f"❌ Tu dois attendre encore **{mins} minutes** avant de retravailler.", ephemeral=True)
 
        metiers = ["développeur", "cuisinier", "livreur", "streamer", "professeur"]
        montant = random.randint(50, 200)
        user["wallet"] += montant
        user["last_work"] = now.isoformat()
        save_eco(data)
        await interaction.response.send_message(f"💼 Tu as travaillé comme **{random.choice(metiers)}** et gagné **{montant} coins** !")
 
    @app_commands.command(name="pay", description="Transfère des coins à un membre")
    @app_commands.describe(membre="Le membre à payer", montant="Le montant à transférer")
    async def pay(self, interaction: discord.Interaction, membre: discord.Member, montant: int):
        if membre == interaction.user:
            return await interaction.response.send_message("❌ Tu ne peux pas te payer toi-même !", ephemeral=True)
        if montant <= 0:
            return await interaction.response.send_message("❌ Le montant doit être positif.", ephemeral=True)
 
        data = load_eco()
        sender = get_user(data, interaction.guild.id, interaction.user.id)
        receiver = get_user(data, interaction.guild.id, membre.id)
 
        if sender["wallet"] < montant:
            return await interaction.response.send_message("❌ Tu n'as pas assez de coins dans ton portefeuille.", ephemeral=True)
 
        sender["wallet"] -= montant
        receiver["wallet"] += montant
        save_eco(data)
        await interaction.response.send_message(f"✅ Tu as transféré **{montant} coins** à {membre.mention} !")
 
    @app_commands.command(name="coinflip-bet", description="Parie des coins sur un lancer de pièce")
    @app_commands.describe(montant="Le montant à parier", choix="Ton choix")
    @app_commands.choices(choix=[
        app_commands.Choice(name="Pile", value="pile"),
        app_commands.Choice(name="Face", value="face"),
    ])
    async def coinflip_bet(self, interaction: discord.Interaction, montant: int, choix: str):
        if montant <= 0:
            return await interaction.response.send_message("❌ Le montant doit être positif.", ephemeral=True)
 
        data = load_eco()
        user = get_user(data, interaction.guild.id, interaction.user.id)
 
        if user["wallet"] < montant:
            return await interaction.response.send_message("❌ Tu n'as pas assez de coins.", ephemeral=True)
 
        resultat = random.choice(["pile", "face"])
        if choix == resultat:
            user["wallet"] += montant
            msg = f"🎉 **{resultat.capitalize()}** ! Tu gagnes **{montant} coins** !"
        else:
            user["wallet"] -= montant
            msg = f"😢 **{resultat.capitalize()}** ! Tu perds **{montant} coins** !"
 
        save_eco(data)
        await interaction.response.send_message(msg)
 
    @app_commands.command(name="slots", description="Joue à la machine à sous")
    @app_commands.describe(montant="Le montant à miser")
    async def slots(self, interaction: discord.Interaction, montant: int):
        if montant <= 0:
            return await interaction.response.send_message("❌ Le montant doit être positif.", ephemeral=True)
 
        data = load_eco()
        user = get_user(data, interaction.guild.id, interaction.user.id)
 
        if user["wallet"] < montant:
            return await interaction.response.send_message("❌ Tu n'as pas assez de coins.", ephemeral=True)
 
        symboles = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎"]
        rouleaux = [random.choice(symboles) for _ in range(3)]
        affichage = " | ".join(rouleaux)
 
        if rouleaux[0] == rouleaux[1] == rouleaux[2]:
            gain = montant * 5
            user["wallet"] += gain
            msg = f"🎰 {affichage}\n🎉 **JACKPOT !** Tu gagnes **{gain} coins** !"
        elif rouleaux[0] == rouleaux[1] or rouleaux[1] == rouleaux[2]:
            gain = montant
            user["wallet"] += gain
            msg = f"🎰 {affichage}\n✅ Deux symboles identiques ! Tu gagnes **{gain} coins** !"
        else:
            user["wallet"] -= montant
            msg = f"🎰 {affichage}\n😢 Pas de chance ! Tu perds **{montant} coins** !"
 
        save_eco(data)
        await interaction.response.send_message(msg)
 
    @app_commands.command(name="rob", description="Tente de voler des coins à un membre")
    @app_commands.describe(membre="Le membre à voler")
    async def rob(self, interaction: discord.Interaction, membre: discord.Member):
        if membre == interaction.user:
            return await interaction.response.send_message("❌ Tu ne peux pas te voler toi-même !", ephemeral=True)
 
        data = load_eco()
        voleur = get_user(data, interaction.guild.id, interaction.user.id)
        victime = get_user(data, interaction.guild.id, membre.id)
 
        if victime["wallet"] < 50:
            return await interaction.response.send_message("❌ Cette personne n'a pas assez de coins à voler.", ephemeral=True)
 
        if random.random() < 0.5:
            montant = random.randint(10, min(100, victime["wallet"]))
            voleur["wallet"] += montant
            victime["wallet"] -= montant
            msg = f"🦹 Tu as volé **{montant} coins** à {membre.mention} !"
        else:
            amende = random.randint(50, 150)
            voleur["wallet"] = max(0, voleur["wallet"] - amende)
            msg = f"🚔 Tu t'es fait attraper ! Tu paies une amende de **{amende} coins** !"
 
        save_eco(data)
        await interaction.response.send_message(msg)
 
    @app_commands.command(name="leaderboard", description="Affiche les membres les plus riches")
    async def leaderboard(self, interaction: discord.Interaction):
        data = load_eco()
        guild_data = data.get(str(interaction.guild.id), {})
 
        classement = []
        for uid, udata in guild_data.items():
            total = udata.get("wallet", 0) + udata.get("bank", 0)
            member = interaction.guild.get_member(int(uid))
            if member:
                classement.append((member.display_name, total))
 
        classement.sort(key=lambda x: x[1], reverse=True)
 
        embed = discord.Embed(title="🏆 Classement des plus riches", color=discord.Color.gold())
        medailles = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (nom, total) in enumerate(classement[:10]):
            medal = medailles[i] if i < 3 else f"`#{i+1}`"
            desc += f"{medal} **{nom}** — {total} coins\n"
 
        embed.description = desc or "Aucun membre dans le classement."
        await interaction.response.send_message(embed=embed)
 
async def setup(bot):
    await bot.add_cog(Economie(bot))
 