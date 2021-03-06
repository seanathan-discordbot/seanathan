import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown, CommandOnCooldown

import os
import time
import traceback
import logging

import asyncpg

from Utilities import Links, Checks
from Utilities.Checks import NoChar

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=Links.log_file, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

async def get_prefix(client, message):
    if isinstance(message.channel, discord.DMChannel):
        return '%'

    conn = await asyncpg.connect(database=Links.database_name, user=Links.database_user, password=Links.database_password)
    prefix = await conn.fetchval('SELECT prefix FROM prefixes WHERE server = $1', message.guild.id)
    if prefix is None: #bot joined server while offline
        await conn.execute("INSERT INTO prefixes (server, prefix) VALUES ($1, '%')", message.guild.id)
        prefix = '%'
    await conn.close()
    return prefix

client = commands.Bot(command_prefix=get_prefix, help_command=None, case_insensitive=True)

admins = [196465885148479489, 325080171591761921, 530760994289483790, 465388103792590878] #Seb, Sean, Demi, Bort
def is_admin(ctx):
        if ctx.author.id in admins:
            return True
        
#Create bot cooldown
_cd = commands.CooldownMapping.from_cooldown(1, 2.5, commands.BucketType.user) 

@client.check
async def cooldown_check(ctx):
    bucket = _cd.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(bucket, retry_after)
    return True

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('Say %tutorial to get started!'))
    print('Hi my name is Ayesha.')   

# ----- PREFIX CHANGING STUFF -----

@client.event #the default prefix is %
async def on_guild_join(guild):
    async with client.pg_con.acquire() as conn:
        await conn.execute("INSERT INTO prefixes (server, prefix) VALUES ($1, '%')", guild.id) 

@client.event #deletes the set prefix when a bot leaves the server
async def on_guild_remove(guild):
    async with client.pg_con.acquire() as conn:
        await conn.execute("DELETE FROM prefixes WHERE server = $1", guild.id) 

@client.command()
@cooldown(1, 30, BucketType.default)
@commands.has_guild_permissions(manage_permissions=True)
async def changeprefix(ctx, prefix):
    if isinstance(ctx.message.channel, discord.DMChannel):
        await ctx.reply('You can\'t do that here.')
        return

    if len(prefix) > 10:
        await ctx.reply('Your prefix can only be a maximum of 10 characters.')
        return
    async with client.pg_con.acquire() as conn:
        await conn.execute('UPDATE prefixes SET prefix = $1 WHERE server = $2', prefix, ctx.guild.id)
        await ctx.send(f'Prefix changed to `{prefix}`.')

# ----- OTHER COMMANDS -----
@client.command(brief=None, description='Ping to see if bot is working')
async def ping(ctx):
    embed = discord.Embed(title="Pong!", description=f"Latency is {client.latency * 1000:.2f} ms", color=0xBEDCF6)
    await ctx.send(embed=embed)

@client.command(brief=None, description='Returns the amount of servers this bot is in')
async def servers(ctx):
    await ctx.send("This bot is in "+str(len(ctx.bot.guilds))+" servers.")

# ----- LOAD COGS -----
@client.command()
@commands.check(is_admin)
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    await ctx.channel.send('Loaded.')

@client.command()
@commands.check(is_admin)
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    await ctx.channel.send('Unloaded.')

@client.command()
@commands.check(is_admin)
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    await ctx.channel.send('Reloaded.')

# Create connections to the database
async def create_db_pool():
    client.pg_con = await asyncpg.create_pool(database=Links.database_name, user=Links.database_user, password=Links.database_password)

client.loop.run_until_complete(create_db_pool())

# Runs at bot startup to load all cogs
# for filename in os.listdir(r'F:\OneDrive\Ayesha\cogs'):
for filename in os.listdir(r'C:\Users\sebas\OneDrive\Ayesha\cogs'):
    if filename.endswith('.py'): # see if the file is a python file
        client.load_extension(f'cogs.{filename[:-3]}')

#Also delete the music files downloaded
# for filename in os.listdir(r'F:\OneDrive\NguyenBot\Music Files'):
# for filename in os.listdir(r'C:\Users\sebas\OneDrive\Ayesha\Music Files'):
#     os.remove(f'F:/OneDrive/Ayesha/Music Files/{filename}')

client.run(Links.Token)