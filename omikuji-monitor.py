import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import sys

# Correction de l'encodage pour éviter les erreurs d'affichage
sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1215697019574812752  
URL = "https://omikujistore.com/collections/francais?limit=48"

# Initialisation du bot
intents = discord.Intents.default()
bot = discord.Client(intents=intents)

last_scraped_data = None  # Stocke les dernières données pour comparer les changements

def scrape_website():
    """ Fonction de scraping qui retourne les données d'un article. """
    global last_scraped_data
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)

    if response.status_code != 200:
        print(f"[ERREUR] Impossible de récupérer la page. Code HTTP: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # 🔍 Sélection des éléments avec vérification
    title_element = soup.select_one(".spf-product-card__title a")
    price_element = soup.select_one(".spf-product-card__price-wrapper .money")
    link_element = soup.select_one(".spf-product-card__title a")

    if not title_element or not price_element or not link_element:
        print("[ERREUR] Impossible de récupérer certains éléments du site.")
        return None

    # Extraction des données
    title = title_element.text.strip()
    price = price_element.text.strip()
    link = "https://omikujistore.com" + link_element["href"]  # Ajoute le domaine

    data = {"title": title, "price": price, "link": link}

    # Vérifie si les données ont changé
    if last_scraped_data is None or data != last_scraped_data:
        last_scraped_data = data
        return data
    return None

@tasks.loop(minutes=5)  # Vérifie toutes les 5 minutes
async def check_website():
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print("[ERREUR] Canal introuvable. Vérifiez l'ID du canal.")
        return

    new_data = scrape_website()
    if new_data:
        embed = discord.Embed(
            title=new_data["title"],
            description=f"**Prix:** {new_data['price']}",
            url=new_data["link"],
            color=discord.Color.green(),
        )
        embed.set_footer(text="Nouveau produit détecté ! 🚀")
        await channel.send(embed=embed)
        print("[INFO] Nouveau produit envoyé sur Discord.")

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté ! ✅")
    check_website.start()

bot.run(TOKEN)
