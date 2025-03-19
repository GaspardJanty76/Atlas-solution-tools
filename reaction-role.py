import discord
from discord.ext import commands
import sys
import os
from dotenv import load_dotenv
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

TOKEN_DISCORD = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

REACTION_ROLE_MESSAGE_ID = 1310606412627447890
ROLE_EMOJI_MAPPING = {
    "🐀": 1292600689729732659,
    "🎵": 1310571661803651145,
}

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté et prêt !")

@bot.event
async def on_raw_reaction_add(payload):
    print(f"Réaction ajoutée : {payload.emoji.name} par {payload.user_id}")
    if payload.message_id != REACTION_ROLE_MESSAGE_ID:
        print("Réaction ignorée : message non concerné.")
        return

    guild = bot.get_guild(payload.guild_id)
    role_id = ROLE_EMOJI_MAPPING.get(payload.emoji.name)
    if role_id:
        role = guild.get_role(role_id)
        if role:
            member = guild.get_member(payload.user_id)
            if member:
                await member.add_roles(role)
                print(f"✅ Rôle '{role.name}' ajouté à {member.display_name}")
            else:
                print("⚠️ Utilisateur introuvable dans la guilde.")
        else:
            print("⚠️ Rôle introuvable.")
    else:
        print("⚠️ Emoji non mappé à un rôle.")

@bot.event
async def on_raw_reaction_remove(payload):
    print(f"Réaction retirée : {payload.emoji.name} par {payload.user_id}")
    if payload.message_id != REACTION_ROLE_MESSAGE_ID:
        print("Réaction ignorée : message non concerné.")
        return

    guild = bot.get_guild(payload.guild_id)
    role_id = ROLE_EMOJI_MAPPING.get(payload.emoji.name)
    if role_id:
        role = guild.get_role(role_id)
        if role:
            member = guild.get_member(payload.user_id)
            if member:
                await member.remove_roles(role)
                print(f"❌ Rôle '{role.name}' retiré de {member.display_name}")
            else:
                print("⚠️ Utilisateur introuvable dans la guilde.")
        else:
            print("⚠️ Rôle introuvable.")
    else:
        print("⚠️ Emoji non mappé à un rôle.")

@bot.command()
async def setup_reaction_roles(ctx):
    message = await ctx.send(
        "Réagissez avec 🐀 pour obtenir le rôle Pokémon, ou 🎵 pour obtenir le rôle Concerts !"
    )
    await message.add_reaction("🐀")
    await message.add_reaction("🎵")
    print(f"Message de rôles configuré : {message.id}")

bot.run(TOKEN_DISCORD)
