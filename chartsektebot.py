import discord
from discord.ext import commands
import datetime
import os


bot = commands.Bot(command_prefix='>', description="This is a Helper Bot")

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def sum(ctx, numOne: int, numTwo: int):
    await ctx.send(numOne + numTwo)

# Events
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Chartsekte.de"))
    print('My Ready is Body')


@bot.listen()
async def on_raw_reaction_add(payload):#
    print("hallo1")
    print(payload)
    #await payload.member.send("DU hast einen Upvote von XXX bekommen :)")
    channel = bot.get_channel(780850691891134474)
    msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    print("\n")
    print(msg)
    await channel.send(f"User <@{msg.author.id}> hat einen Upvote von {payload.member.name} bekommen")
    #if not isinstance(reaciton.message.channel, discord.DMChannel):
async def on_reaction_add(ctx, reaciton):
    print(ctx)
    print(reaciton)
    print("hallo2")
    
async def on_message(message):
    if "tutorial" in message.content.lower():
        # in this case don't respond with the word "Tutorial" or you will call the on_message event recursively
        await message.channel.send('This is that you want http://youtube.com/fazttech')
        await bot.process_commands(message)
@bot.command()
async def poll(ctx, *, text):
    message = await ctx.send(text)
    for emoji in ('👍', '👎'):
        await message.add_reaction(emoji)

bot.run(os.getenv("BOTTOKEN"))