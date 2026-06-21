import discord
from discord.ext import commands
import asyncio
import os
from config import TOKEN

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

def get_prefix(bot, message):
    """Préfixe dynamique par serveur, importé après le chargement des cogs."""
    from cogs.prefix import get_prefix as _get_prefix
    return _get_prefix(bot, message)

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

COGS = [
    "cogs.evenements",
    "cogs.utilitaires",
    "cogs.moderation",
    "cogs.tickets",
    "cogs.comptage",
    "cogs.vocal",
    "cogs.fun",
    "cogs.economie",
    "cogs.utilitaires2",
    "cogs.logs",
    "cogs.prefix",
    "cogs.membercount",
    "cogs.giveaway",
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