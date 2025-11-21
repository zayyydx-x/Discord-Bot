import discord
from discord.ext import commands, tasks
import random
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import logging
import sys

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configure simple logging
logging.basicConfig(
	level=logging.INFO,
	format='[%(asctime)s] %(levelname)s: %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)

# Fail fast if token is missing to provide a clear error message
if not TOKEN:
	logging.error('DISCORD_TOKEN not set. Please set DISCORD_TOKEN in your environment or in a .env file.')
	sys.exit(1)

# Set up bot with command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Database setup
def init_db():
	conn = sqlite3.connect('discord_bot.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS users (
					user_id INTEGER PRIMARY KEY,
					username TEXT,
					points INTEGER DEFAULT 0,
					joined_date TEXT
				)''')
	c.execute('''CREATE TABLE IF NOT EXISTS warnings (
					warning_id INTEGER PRIMARY KEY AUTOINCREMENT,
					user_id INTEGER,
					reason TEXT,
					warned_by INTEGER,
					date TEXT
				)''')
	conn.commit()
	conn.close()

init_db()

# ==================== EVENTS ====================

@bot.event
async def on_ready():
	logging.info('%s has connected to Discord!', bot.user)
	logging.info('Bot ID: %s', bot.user.id)
	try:
		synced = await bot.tree.sync()
		logging.info('Synced %d command(s)', len(synced))
	except Exception as e:
		logging.warning('Error syncing commands: %s', e)
	# Only start the background task if it's not already running (prevents double-starts)
	if not status_update.is_running():
		status_update.start()

@bot.event
async def on_member_join(member):
	"""Welcome new members"""
	try:
		# Send DM directly; this works whether or not a DM channel already exists
		embed = discord.Embed(
			title=f'Welcome to {member.guild.name}!',
			description=f'Hi {member.mention}! Use `/help` or `!help` to see available commands.',
			color=discord.Color.green()
		)
		# Use display_avatar for a safer avatar URL (works when a member has no custom avatar)
		embed.set_thumbnail(url=member.display_avatar.url)
		await member.send(embed=embed)
	except Exception:
		# ignore DM fails (user may have DMs disabled)
		pass
    
	# Add user to database
	conn = sqlite3.connect('discord_bot.db')
	c = conn.cursor()
	c.execute('INSERT OR IGNORE INTO users (user_id, username, joined_date) VALUES (?, ?, ?)',
			  (member.id, member.name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
	conn.commit()
	conn.close()

@bot.event
async def on_member_remove(member):
	"""Log when members leave"""
	logging.info('%s left the server', member.name)

@bot.event
async def on_message(message):
	"""Handle messages"""
	if message.author == bot.user:
		return
    
	# Add points to user
	if not message.author.bot:
		conn = sqlite3.connect('discord_bot.db')
		c = conn.cursor()
		c.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
				  (message.author.id, message.author.name))
		c.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (message.author.id,))
		conn.commit()
		conn.close()
    
	await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
	"""Handle command errors"""
	if isinstance(error, commands.CommandNotFound):
		await ctx.send('❌ Command not found. Use `!help` for available commands.')
	elif isinstance(error, commands.MissingPermissions):
		await ctx.send('❌ You don\'t have permission to use this command.')
	elif isinstance(error, commands.MissingRequiredArgument):
		await ctx.send(f'❌ Missing required argument. Use `!help {ctx.command.name}`')
	elif isinstance(error, commands.BadArgument):
		await ctx.send('❌ Invalid argument provided.')
	else:
		await ctx.send(f'❌ An error occurred: {str(error)}')

# ==================== BACKGROUND TASKS ====================

@tasks.loop(minutes=30)
async def status_update():
	"""Update bot status every 30 minutes"""
	statuses = [
		discord.Activity(type=discord.ActivityType.watching, name="!help"),
		discord.Activity(type=discord.ActivityType.playing, name="with commands"),
		discord.Activity(type=discord.ActivityType.listening, name="your messages"),
	]
	await bot.change_presence(activity=random.choice(statuses))

# ==================== UTILITY COMMANDS ====================

@bot.command(name='ping')
async def ping(ctx):
	"""Check bot latency"""
	embed = discord.Embed(title='🏓 Pong!', color=discord.Color.blue())
	embed.add_field(name='Latency', value=f'{round(bot.latency * 1000)}ms')
	await ctx.send(embed=embed)

@bot.command(name='hello')
async def hello(ctx):
	"""Bot greets the user"""
	await ctx.send(f'👋 Hello {ctx.author.mention}! How can I help you?')

@bot.command(name='serverinfo')
async def server_info(ctx):
	"""Get information about the server"""
	guild = ctx.guild
	embed = discord.Embed(title=f'{guild.name} Info', color=discord.Color.purple())
	embed.add_field(name='Members', value=guild.member_count)
	embed.add_field(name='Channels', value=len(guild.channels))
	embed.add_field(name='Roles', value=len(guild.roles))
	embed.add_field(name='Owner', value=guild.owner.mention)
	embed.add_field(name='Created', value=guild.created_at.strftime('%Y-%m-%d'))
	if guild.icon:
		embed.set_thumbnail(url=guild.icon.url)
	await ctx.send(embed=embed)

@bot.command(name='userinfo')
async def user_info(ctx, member: discord.Member = None):
	"""Get info about a user"""
	if member is None:
		member = ctx.author
    
	conn = sqlite3.connect('discord_bot.db')
	c = conn.cursor()
	c.execute('SELECT points FROM users WHERE user_id = ?', (member.id,))
	result = c.fetchone()
	points = result[0] if result else 0
	conn.close()
    
	embed = discord.Embed(title=f'{member.name}\'s Profile', color=member.color)
	embed.add_field(name='ID', value=member.id, inline=False)
	embed.add_field(name='Joined Server', value=member.joined_at.strftime('%Y-%m-%d'))
	embed.add_field(name='Account Created', value=member.created_at.strftime('%Y-%m-%d'))
	embed.add_field(name='Points', value=points)
	embed.add_field(name='Roles', value=', '.join([role.mention for role in member.roles[1:]]) or 'No roles')
	embed.set_thumbnail(url=member.display_avatar.url)
    
	await ctx.send(embed=embed)

@bot.command(name='avatar')
async def avatar(ctx, member: discord.Member = None):
	"""Get a user's avatar"""
	if member is None:
		member = ctx.author
    
	embed = discord.Embed(title=f'{member.name}\'s Avatar', color=member.color)
	embed.set_image(url=member.display_avatar.url)
	await ctx.send(embed=embed)

# ==================== FUN COMMANDS ====================

@bot.command(name='roll')
async def roll(ctx, num: int = 100):
	"""Roll a random number between 1 and num (default 100)"""
	if num < 1:
		await ctx.send('❌ Number must be greater than 0!')
		return
	result = random.randint(1, num)
	embed = discord.Embed(title='🎲 Dice Roll', color=discord.Color.gold())
	embed.add_field(name='Result', value=f'**{result}** (1-{num})')
	embed.set_footer(text=f'Rolled by {ctx.author.name}')
	await ctx.send(embed=embed)

@bot.command(name='8ball')
async def magic_8ball(ctx, *, question):
	"""Ask the magic 8ball a question"""
	responses = [
		'Yes, definitely!',
		'No, not at all.',
		'Ask again later.',
		'It is certain.',
		'Don\'t count on it.',
		'Maybe... 🤔',
		'Absolutely!',
		'Signs point to yes.',
		'Very doubtful.',
		'Outlook good.',
		'Better not tell you now.',
		'Concentrate and ask again.',
	]
	embed = discord.Embed(title='🎱 Magic 8Ball', description=f'Question: {question}', color=discord.Color.blurple())
	embed.add_field(name='Answer', value=random.choice(responses))
	await ctx.send(embed=embed)

@bot.command(name='coin')
async def coin_flip(ctx):
	"""Flip a coin"""
	result = random.choice(['Heads', 'Tails'])
	emoji = '🪙'
	embed = discord.Embed(title='Coin Flip', color=discord.Color.gold())
	embed.add_field(name='Result', value=f'{emoji} **{result}**')
	await ctx.send(embed=embed)

@bot.command(name='joke')
async def joke(ctx):
	"""Tell a random joke"""
	jokes = [
		'Why don\'t scientists trust atoms? Because they make up everything!',
		'What do you call a fake noodle? An impasta!',
		'Why did the scarecrow win an award? He was outstanding in his field!',
		'What did the ocean say to the beach? Nothing, it just waved.',
		'Why don\'t eggs tell jokes? They\'d crack each other up!',
		'What\'s the best thing about Switzerland? I don\'t know, but their flag is a big plus.',
	]
	embed = discord.Embed(title='😂 Random Joke', description=random.choice(jokes), color=discord.Color.purple())
	await ctx.send(embed=embed)

@bot.command(name='meme')
async def meme(ctx):
	"""Get a random meme response"""
	memes = [
		'Did you ever hear the tragedy of Darth Plagueis The Wise?',
		'It\'s over 9000! 🌊',
		'To be continued... ➡️',
		'This is the way.',
		'I\'m not crying, you\'re crying 😭',
		'UNLIMITED POWER! ⚡',
		'Hello there... General Kenobi!',
		'It\'s treason, then.',
	]
	await ctx.send(f'✨ {random.choice(memes)}')

@bot.command(name='choose')
async def choose(ctx, *, choices):
	"""Choose between options (separate with commas)"""
	options = [choice.strip() for choice in choices.split(',')]
	if len(options) < 2:
		await ctx.send('❌ Please provide at least 2 options separated by commas!')
		return
	chosen = random.choice(options)
	embed = discord.Embed(title='🎯 Random Choice', color=discord.Color.green())
	embed.add_field(name='Picked', value=f'**{chosen}**')
	await ctx.send(embed=embed)

# ==================== MODERATION COMMANDS ====================

@bot.command(name='warn')
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason='No reason provided'):
	"""Warn a user (moderator only)"""
	if member == ctx.author:
		await ctx.send('❌ You can\'t warn yourself!')
		return
    
	conn = sqlite3.connect('discord_bot.db')
	c = conn.cursor()
	c.execute('INSERT INTO warnings (user_id, reason, warned_by, date) VALUES (?, ?, ?, ?)',
			  (member.id, reason, ctx.author.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
	c.execute('SELECT COUNT(*) FROM warnings WHERE user_id = ?', (member.id,))
	warn_count = c.fetchone()[0]
	conn.commit()
	conn.close()
    
	embed = discord.Embed(title='⚠️ User Warned', color=discord.Color.orange())
	embed.add_field(name='User', value=member.mention)
	embed.add_field(name='Reason', value=reason)
	embed.add_field(name='Total Warnings', value=warn_count)
	await ctx.send(embed=embed)
    
	try:
		await member.send(f'You have been warned in {ctx.guild.name} for: {reason}')
	except:
		pass

@bot.command(name='warnings')
@commands.has_permissions(moderate_members=True)
async def warnings(ctx, member: discord.Member):
	"""Check warnings for a user"""
	conn = sqlite3.connect('discord_bot.db')
	c = conn.cursor()
	c.execute('SELECT reason, warned_by, date FROM warnings WHERE user_id = ? ORDER BY date DESC', (member.id,))
	warns = c.fetchall()
	conn.close()
    
	if not warns:
		await ctx.send(f'{member.mention} has no warnings.')
		return
    
	embed = discord.Embed(title=f'⚠️ Warnings for {member.name}', color=discord.Color.orange())
	for i, (reason, warned_by, date) in enumerate(warns, 1):
		embed.add_field(name=f'Warning #{i}', value=f'**Reason:** {reason}\n**Date:** {date}', inline=False)
	await ctx.send(embed=embed)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason='No reason provided'):
	"""Kick a user from the server"""
	if member == ctx.author:
		await ctx.send('❌ You can\'t kick yourself!')
		return
    
	try:
		await member.kick(reason=reason)
		embed = discord.Embed(title='👢 User Kicked', color=discord.Color.red())
		embed.add_field(name='User', value=member.mention)
		embed.add_field(name='Reason', value=reason)
		await ctx.send(embed=embed)
	except discord.Forbidden:
		await ctx.send('❌ I don\'t have permission to kick this user.')

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason='No reason provided'):
	"""Ban a user from the server"""
	if member == ctx.author:
		await ctx.send('❌ You can\'t ban yourself!')
		return
    
	try:
		await member.ban(reason=reason)
		embed = discord.Embed(title='🔨 User Banned', color=discord.Color.dark_red())
		embed.add_field(name='User', value=member.mention)
		embed.add_field(name='Reason', value=reason)
		await ctx.send(embed=embed)
	except discord.Forbidden:
		await ctx.send('❌ I don\'t have permission to ban this user.')

@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
	"""Delete messages (moderator only)"""
	if amount < 1 or amount > 100:
		await ctx.send('❌ Please provide a number between 1 and 100.')
		return
    
	deleted = await ctx.channel.purge(limit=amount)
	embed = discord.Embed(title='🗑️ Messages Deleted', color=discord.Color.red())
	embed.add_field(name='Count', value=len(deleted))
	msg = await ctx.send(embed=embed)
	await msg.delete(delay=5)

# ==================== POINTS/LEVEL SYSTEM ====================

@bot.command(name='points')
async def points(ctx, member: discord.Member = None):
	"""Check user points"""
	if member is None:
		member = ctx.author
    
	conn = sqlite3.connect('discord_bot.db')
	c = conn.cursor()
	c.execute('SELECT points FROM users WHERE user_id = ?', (member.id,))
	result = c.fetchone()
	user_points = result[0] if result else 0
	conn.close()
    
	embed = discord.Embed(title='⭐ User Points', color=discord.Color.gold())
	embed.add_field(name='User', value=member.mention)
	embed.add_field(name='Points', value=user_points)
	await ctx.send(embed=embed)

@bot.command(name='leaderboard')
async def leaderboard(ctx):
	"""Show top 10 users by points"""
	conn = sqlite3.connect('discord_bot.db')
	c = conn.cursor()
	c.execute('SELECT user_id, username, points FROM users ORDER BY points DESC LIMIT 10')
	results = c.fetchall()
	conn.close()
    
	embed = discord.Embed(title='🏆 Leaderboard', color=discord.Color.gold())
	for i, (user_id, username, points) in enumerate(results, 1):
		embed.add_field(name=f'{i}. {username}', value=f'{points} points', inline=False)
    
	await ctx.send(embed=embed)

# ==================== ADMIN COMMANDS ====================

@bot.command(name='say')
@commands.has_permissions(administrator=True)
async def say(ctx, *, message):
	"""Make the bot say something (admin only)"""
	await ctx.message.delete()
	await ctx.send(message)

@bot.command(name='embed')
@commands.has_permissions(administrator=True)
async def send_embed(ctx, title, *, description):
	"""Create an embed message (admin only)"""
	embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
	await ctx.send(embed=embed)

@bot.command(name='announce')
@commands.has_permissions(administrator=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
	"""Send announcement to a channel (admin only)"""
	embed = discord.Embed(title='📢 Announcement', description=message, color=discord.Color.red())
	embed.set_footer(text=f'Announced by {ctx.author.name}')
	await channel.send(embed=embed)

# ==================== HELP COMMAND ====================

@bot.command(name='help')
async def help_command(ctx):
	"""Show all available commands"""
	embed = discord.Embed(title='📖 Bot Commands', color=discord.Color.blurple())
    
	embed.add_field(name='⚙️ Utility', value='`!ping` `!hello` `!serverinfo` `!userinfo [user]` `!avatar [user]`', inline=False)
	embed.add_field(name='🎮 Fun', value='`!roll [num]` `!8ball [question]` `!coin` `!joke` `!meme` `!choose [option1,option2,...]`', inline=False)
	embed.add_field(name='⭐ Points', value='`!points [user]` `!leaderboard`', inline=False)
	embed.add_field(name='🛡️ Moderation', value='`!warn [user] [reason]` `!warnings [user]` `!kick [user] [reason]` `!ban [user] [reason]` `!purge [amount]`', inline=False)
	embed.add_field(name='👑 Admin', value='`!say [message]` `!embed [title] [description]` `!announce [channel] [message]`', inline=False)
    
	await ctx.send(embed=embed)

if __name__ == '__main__':
	# Run the bot
	bot.run(TOKEN)

