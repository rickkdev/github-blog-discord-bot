import os
import asyncio
import discord
import feedparser
from discord.ext.tasks import loop
from discord.ext import commands
from aiohttp import ClientSession
import openai
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
RSS_FEED_URL = os.getenv("RSS_FEED_URL")
API_KEY = os.getenv("API_KEY")
MODEL_ID = os.getenv("MODEL_ID")

openai.api_key = API_KEY

# Set up the bot
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def fetch_rss_articles(session):
    async with session.get(RSS_FEED_URL) as response:
        rss_text = await response.text()
    feed = feedparser.parse(rss_text)
    return feed.entries

async def generate_summary(prompt):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.7,
        max_tokens=250,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    ))
    return response.choices[0].text.strip()

@loop(minutes=5)
async def post_new_articles():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    print(f"Channel: {channel}")  # Added print statement
    posted_links = set()

    async with ClientSession() as session:
        articles = await fetch_rss_articles(session)

    for article in articles:
        if article.link not in posted_links:
            posted_links.add(article.link)

            # Generate a summary for the article
            summary_prompt = f"Please provide a brief summary of the following article:\nTitle: {article.title}\nLink: {article.link}\n\nSummary:"
            summary = await generate_summary(summary_prompt)

            # Print the article title, link, and summary to the console
            print(f"Title: {article.title}\nLink: {article.link}\nSummary: {summary}\n")

            await channel.send(f"{article.title}\n{article.link}\nSummary: {summary}\n\n")

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    post_new_articles.start()

bot.run(TOKEN)