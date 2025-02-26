import aiohttp
from bs4 import BeautifulSoup
import base64
import urllib.parse
import discord
import asyncio
import re
import os
from dotenv import load_dotenv


load_dotenv()

base_url = "https://boutique-occas.fr/catalogue.php?gamme=pokemon&parent=746&doJSON="
cardmarket_base_url = "https://www.cardmarket.com/fr/Pokemon/Products/Search?searchString="

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 1336690701433442405  
LOG_CHANNEL_ID = 1336689832742752276

historique_articles = set()

def encode_pagination(page_number):
    raw_string = f"Catalogue::addEndlessArticles('Liste','746',{page_number})"
    encoded_bytes = base64.b64encode(raw_string.encode("utf-8"))
    return urllib.parse.quote(encoded_bytes.decode("utf-8"))

def format_cardmarket_search(title):
    match = re.search(r":\s*(.*?)\s*\(([^)]+)\)", title)
    if match:
        return f"{match.group(1)} ({match.group(2)})"
    return title

async def send_log_message(client, message):
    log_channel = client.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"📢 {message}")

async def get_articles(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"Erreur de chargement de la page : {response.status}")
                return []
            
            soup = BeautifulSoup(await response.text(), 'html.parser')
            articles = soup.find_all("div", class_="ficheArticle")
            results = []
            
            for article in articles:
                title_tag = article.select_one("span.nom")
                price_tag = article.select_one("span.prix")
                image_tag = article.select_one("img")
                link_tag = article.select_one("a.ajaxPage")

                title = title_tag.text.strip() if title_tag else "Titre inconnu"
                price = price_tag.text.strip() if price_tag else "Prix inconnu"
                image_url = image_tag["data-src"] if image_tag and image_tag.has_attr("data-src") else (image_tag["src"] if image_tag else "")
                link = link_tag["href"] if link_tag else ""
                cardmarket_link = cardmarket_base_url + urllib.parse.quote(format_cardmarket_search(title))
                
                results.append({
                    "title": title,
                    "price": price,
                    "image_url": image_url,
                    "link": link,
                    "cardmarket_link": cardmarket_link
                })
            
            return results

async def fetch_and_send_articles(client, channel, page_number):
    encoded_param = encode_pagination(page_number)
    page_url = base_url + encoded_param
    
    articles = await get_articles(page_url)
    new_articles = [a for a in articles if a["title"] not in historique_articles]
    
    if new_articles:
        print(f"{len(new_articles)} nouveaux articles trouvés sur la page {page_number} !")
        tasks = []
        
        for article in new_articles:
            embed = discord.Embed(
                title=article["title"],
                url=article["link"],
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=article["image_url"])
            embed.add_field(name="Prix", value=article["price"], inline=True)
            embed.add_field(name="🔍 Lien vers CardMarket", value=f"[Voir sur CardMarket]({article['cardmarket_link']})", inline=False)
            tasks.append(channel.send(embed=embed))
            historique_articles.add(article["title"])
        
        await asyncio.gather(*tasks)
    
    return len(articles) > 0

async def monitor_and_notify():
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'Connecté en tant que {client.user}')
        await send_log_message(client, "Le Moniteur LaBoutiqueDeLoccas a démarré ✅")
        channel = client.get_channel(CHANNEL_ID)
        page_number = 1
        
        try:
            while True:
                tasks = [fetch_and_send_articles(client, channel, i) for i in range(page_number, page_number + 3)]
                results = await asyncio.gather(*tasks)
                
                if not any(results):
                    break
                
                page_number += 3
                
            await asyncio.sleep(30)
        except Exception as e:
            await send_log_message(client, f"❌ Une erreur sur le Moniteur LaBoutiqueDeLoccas est survenue : {e}")
    
    @client.event
    async def on_disconnect():
        await send_log_message(client, "Le Moniteur LaBoutiqueDeLoccas s'est arrêté ❌")
    
    await client.start(DISCORD_TOKEN)

asyncio.run(monitor_and_notify())
