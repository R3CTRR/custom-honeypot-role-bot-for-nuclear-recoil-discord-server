import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# Pull variables safely from environment variables
TARGET_ROLE_ID = int(os.getenv("TARGET_ROLE_ID")) 
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# Hardcoded Channel IDs provided for logging
LOGS_CHANNEL_ID = 1566516311494893630
ACTIVITY_FEED_CHANNEL_ID = 1566514591570075848

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} and monitoring roles 24/7.")

@bot.event
async def on_member_update(before, after):
    # Detect if a role was added to the user
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        
        if new_role.id == TARGET_ROLE_ID:
            try:
                # 1. Execute the ban immediately
                await after.ban(reason=f"Honeypot Trigger: Acquired restricted role ({new_role.name}).")
                print(f"Successfully banned {after.name} for receiving the target role.")
                
                # 2. Build the alert embed for the log channels
                embed = discord.Embed(
                    title="🚨 Honeypot Role Ban executed",
                    description=f"**User:** {after.mention} (`{after.id}`)\n**Tag:** {after.name}\n**Trigger Role:** {new_role.mention}",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                
                # 3. Dispatch messages to your log channels
                logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
                if logs_channel:
                    await logs_channel.send(embed=embed)
                    
                activity_channel = bot.get_channel(ACTIVITY_FEED_CHANNEL_ID)
                if activity_channel:
                    await activity_channel.send(embed=embed)
                    
            except discord.Forbidden:
                print(f"Failed to ban {after.name}. Check bot hierarchy and permissions.")
                # Optional fallback log if the bot lacked permissions to execute the ban
                logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
                if logs_channel:
                    await logs_channel.send(f"⚠️ **Failed Ban Attempt:** {after.mention} received the restricted role, but I lack permissions to ban them.")

bot.run(BOT_TOKEN)
