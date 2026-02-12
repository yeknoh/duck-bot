import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import requests
import re
import datetime

# Import configuration from cfg.py
from cfg import duckpath

# Initialize the bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Define the slash command to send a random image
@bot.tree.command(name="duck", description="Sends a random image of a duck")
async def duck(interaction: discord.Interaction):
    # Get a list of all files in the directory
    images = [f for f in os.listdir(duckpath) if os.path.isfile(os.path.join(duckpath, f))]
    
    # Check if there are any images in the directory
    if not images:
        await interaction.response.send_message("No images found in the directory.")
        return
    
    # Select a random image
    random_image = random.choice(images)
    image_path = os.path.join(duckpath, random_image)
    
    # Send the random image
    with open(image_path, "rb") as image_file:
        await interaction.response.send_message(file=discord.File(image_file, random_image))

# Event listener for when the bot is tagged in a message
@bot.event
async def on_message(message):
    # Avoid the bot responding to itself
    if message.author == bot.user:
        return
    
    # Check if the bot is mentioned in the message
    if bot.user in message.mentions:
        # Get a list of all files in the directory
        images = [f for f in os.listdir(duckpath) if os.path.isfile(os.path.join(duckpath, f))]
        
        # Check if there are any images in the directory
        if not images:
            await message.channel.send("No images found in the directory.")
            return
        
        # Select a random image
        random_image = random.choice(images)
        image_path = os.path.join(duckpath, random_image)
        
        # Send the random image
        with open(image_path, "rb") as image_file:
            await message.channel.send(file=discord.File(image_file, random_image))
    
    # Process other commands if any
    await bot.process_commands(message)

@bot.command(name="farfetch")
async def farfetch(ctx, message_id: int):
    # Check if the user is allowed
    if str(ctx.author.id) != os.getenv("ALLOWED_USER_ID"):
        await ctx.send("You don't have permission to use this command.")
        return

    # Fetch the message by ID
    try:
        message = await ctx.channel.fetch_message(message_id)
    except discord.NotFound:
        await ctx.send("Message not found.")
        return
    except discord.Forbidden:
        await ctx.send("I don't have permission to access that message.")
        return

    # Step 1: Try downloading the first attachment if present
    if message.attachments:
        attachment = message.attachments[0]
        image_url = attachment.url
        file_path = os.path.join(duckpath, attachment.filename)
    else:
        # Step 2: Check if there's a link in the message content
        url_pattern = r'(https?://\S+\.(?:jpg|jpeg|png|gif))'
        match = re.search(url_pattern, message.content)
        if match:
            image_url = match.group(0)
            file_name = os.path.basename(image_url)
            file_path = os.path.join(duckpath, file_name)
        else:
            await ctx.send("No attachment or image link found in the message.")
            return

    # Check if the file already exists and add a timestamp if necessary
    if os.path.exists(file_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"{timestamp}_{attachment.filename if message.attachments else os.path.basename(image_url)}"
        file_path = os.path.join(duckpath, file_name)

    # Download the image from the URL
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            file.write(response.content)
        
        # React with the 🦆 emoji if download is successful
        await ctx.message.add_reaction("🦆")
        
    except requests.exceptions.RequestException as e:
        await ctx.send(f"Failed to download image: {e}")

# Sync commands and start the bot
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    
    # Set the bot's rich presence (status)
    status_message = "with ducks | /duck"
    activity = discord.Game(name=status_message)  # "Playing" status
    await bot.change_presence(status=discord.Status.online, activity=activity)
    
    # Sync commands to Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s) globally.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Run the bot using the token from cfg.py
bot.run(os.getenv("DTOKEN"))
