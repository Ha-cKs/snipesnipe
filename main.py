import discord
import requests
import asyncio
import time
import os

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = 1234567890123456781496573000642854975

DEALS_URL = "https://api.rolimons.com/market/v1/dealactivity"
ITEMS_URL = "https://api.rolimons.com/items/v1/itemdetails"

session = requests.Session()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

items = {}
seen = set()

MIN_DEAL = 30
MAX_PRICE = 1000

def fetch_items():
    try:
        return session.get(ITEMS_URL, timeout=8).json()["items"]
    except:
        return {}

def calc_deal(rap, price):
    return ((rap - price) / rap) * 100 if rap > 0 else 0

def is_projected(item, rap, price):
    p = item[7]
    if p != -1 and p >= 1:
        return True
    if rap > 0 and abs(rap - price) / rap >= 0.5:
        return True
    return False

async def loop():
    global items

    items = fetch_items()
    last_refresh = time.time()

    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print("Channel not found")
        return

    while not client.is_closed():
        try:
            if time.time() - last_refresh > 600:
                items = fetch_items()
                last_refresh = time.time()

            data = session.get(DEALS_URL, timeout=8).json()
            activities = data.get("activities", [])

            for entry in activities:
                ts, _, item_id, price = entry
                key = f"{item_id}-{ts}-{price}"

                if key in seen:
                    continue

                seen.add(key)

                if price > MAX_PRICE:
                    continue

                item = items.get(str(item_id))
                if not item:
                    continue

                name = item[0]
                rap = item[2]

                deal = calc_deal(rap, price)

                if deal >= MIN_DEAL and not is_projected(item, rap, price):

                    embed = discord.Embed(
                        title="🚨 SNIPER ALERT",
                        description=f"🔥 **{name}**",
                        color=0x00ff00
                    )

                    embed.add_field(name="💰 RAP", value=str(rap), inline=True)
                    embed.add_field(name="💸 Price", value=str(price), inline=True)
                    embed.add_field(name="📈 Deal", value=f"{deal:+.2f}%", inline=True)

                    embed.add_field(
                        name="⚡ ACTION",
                        value=f"https://www.roblox.com/catalog/{item_id}",
                        inline=False
                    )

                    embed.set_footer(text="Tap link to open instantly on mobile")

                    await channel.send(embed=embed)

            await asyncio.sleep(1.5)

        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(3)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(loop())

client.run(TOKEN)
