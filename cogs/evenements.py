import discord
from discord.ext import commands
import datetime
from config import SALON_BIENVENUE
 
class Evenements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.bot.user} (ID: {self.bot.user.id})")
        try:
            synced = await self.bot.tree.sync()
            print(f"✅ {len(synced)} commande(s) slash synchronisée(s)")
        except Exception as e:
            print(f"❌ Erreur de synchronisation : {e}")
 
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(SALON_BIENVENUE)
        if not channel:
            return
 
        # Calcul du numéro de membre
        numero = member.guild.member_count
 
        embed = discord.Embed(
            title=f"👋 Bienvenue sur {member.guild.name} !",
            description=(
                f"Heureux de t'accueillir, {member.mention} !\n\n"
                f"Tu es notre **{numero}ème membre** 🎉"
            ),
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📅 Compte créé le", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.set_footer(text=f"ID : {member.id}")
 
        await channel.send(embed=embed)
 
async def setup(bot):
    await bot.add_cog(Evenements(bot))
 