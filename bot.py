import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. Set up a dummy web server to satisfy Render's web portal check
app = Flask('')

@app.route('/')
def home():
    return "Bot is online!"

def run_web_server():
    # Render expects port 10000 by default for web services
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

# 2. Standard Discord Bot Setup
intents = discord.Intents.default()
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

TARGET_ROLE_ID = int(os.getenv("TARGET_ROLE_ID")) 
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# Hardcoded Log Channels
LOGS_CHANNEL_ID = 1566516311494893630
ACTIVITY_FEED_CHANNEL_ID = 1566514591570075848

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} and monitoring roles 24/7.")

@bot.event
async def on_member_update(before, after):
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        
        if new_role.id == TARGET_ROLE_ID:
            try:
                # Execute the ban immediately
                await after.ban(reason=f"Honeypot Trigger: Acquired restricted role ({new_role.name}).")
                print(f"Successfully banned {after.name} for receiving the target role.")
                
                # Build the alert embed for the log channels
                embed = discord.Embed(
                    title="🚨 Honeypot Role Ban executed",
                    description=f"**User:** {after.mention} (`{after.id}`)\n**Tag:** {after.name}\n**Trigger Role:** {new_role.mention}",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                
                # Dispatch messages to your log channels
                for channel_id in [LOGS_CHANNEL_ID, ACTIVITY_FEED_CHANNEL_ID]:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)
                    
            except discord.Forbidden:
                print(f"Failed to ban {after.name}. Check bot hierarchy and permissions.")
                logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
                if logs_channel:
                    await logs_channel.send(f"⚠️ **Failed Ban Attempt:** {after.mention} received the restricted role, but I lack permissions to ban them.")

# 3. Start the web server thread and launch the bot
def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

keep_alive()
bot.run(BOT_TOKEN)
