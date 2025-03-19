import discord
import requests
import logging
import json
from discord.ext import commands
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
load_dotenv()

TOKEN_DISCORD = os.getenv('DISCORD_TOKEN')
TOKEN_ROCKET = os.getenv('ROCKET_API_KEY')
API_URL = "https://app.rocketsource.io/api/v3/convert"

ID_DU_CANAL = 1310572165040574474

intents = discord.Intents.default()
intents.messages = True  
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f'✅ Connecté en tant que {bot.user}')
    
    channel = bot.get_channel(ID_DU_CANAL)
    if channel:
        await channel.send("✅ Le bot est en ligne ! Envoyez `!ean 1234567890123` pour tester.")
        logging.info(f"📢 Message envoyé dans #{channel.name} (ID: {ID_DU_CANAL})")
    else:
        logging.warning("⚠️ Impossible de trouver le canal pour envoyer un message de test.")

@bot.event
async def on_message(message):
    logging.info(f"📩 Message reçu : {message.content} de {message.author}")
    await bot.process_commands(message)

@bot.command()
async def ean(ctx, ean_number: str):
    logging.info(f"📢 Commande reçue: !ean {ean_number} par {ctx.author}")

    if not ean_number.isdigit() or len(ean_number) not in [12, 13]:
        await ctx.send("⚠️ Format EAN invalide. Un EAN doit contenir 12 ou 13 chiffres.")
        logging.warning("❌ Format EAN invalide")
        return

    payload = {
        "marketplace": "FR",
        "ids": [ean_number]
    }

    headers = {
        "Authorization": f"Bearer {TOKEN_ROCKET}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        logging.info(f"🔍 Requête API envoyée : {API_URL}")
        logging.info(f"🔄 Statut de la réponse : {response.status_code}")

        logging.info(f"📡 Contenu brut de la réponse : {response.text}")

        if response.status_code == 200:
            try:
                data = response.json()
                await ctx.send(f"📡 **Réponse brute de l'API :**\n```json\n{json.dumps(data, indent=4)}\n```")
            except requests.exceptions.JSONDecodeError:
                logging.error("🚨 Impossible de décoder la réponse JSON de l'API.")
                await ctx.send("⚠️ L'API a renvoyé une réponse invalide.")
        else:
            await ctx.send(f"⚠️ Erreur API - Statut {response.status_code} : {response.text}")
            logging.error(f"❌ Erreur API - Statut : {response.status_code} - Réponse : {response.text}")

    except requests.exceptions.RequestException as e:
        await ctx.send("🚨 Erreur lors de la communication avec l'API.")
        logging.exception("🚨 Exception lors de la requête API : ")

bot.run(TOKEN_DISCORD)
