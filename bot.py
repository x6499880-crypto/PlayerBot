import discord
from discord.ext import commands
import asyncio
import os
from config import TOKEN, PREFIX
 
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
 
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
 
COGS = [
    "cogs.evenements",
    "cogs.utilitaires",
    "cogs.moderation",
    "cogs.tickets",
    "cogs.comptage",
    "cogs.vocal",
]
 
async def main():
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"✅ Cog chargé : {cog}")
            except Exception as e:
                print(f"❌ Erreur chargement {cog} : {e}")
        await bot.start(TOKEN)
 
asyncio.run(main())
 