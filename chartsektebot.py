import discord
from discord.ext import commands
import datetime
import mysql.connector as mysql
from config import config as cfg

try:
    DB = mysql.connect(
        host= cfg["DB_Server"],
        user= cfg["DB_User"],
        passwd = cfg["DB_Pass"],
        port = cfg["DB_Port"],
        db = cfg["DB_Database"]
    )
    DBCursor = DB.cursor()
except:
    quit("Database Error - Is MariaDB Server running? - Config correct?")

def checkGuild(ID):
    if ID == cfg["GUILD_ID"]:
        return True
    else:
        return False


bot = commands.Bot(command_prefix='>', description="This is a Helper Bot")

@bot.command()
async def ping(ctx):
    print(ctx.message)
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
    if checkGuild(payload.guild_id):
        pass
    else:
        return
    minutes = cfg["minutes"]
    channel = bot.get_channel(cfg["OutputChannel"])
    msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

    if payload.member.id == msg.author.id:
        await channel.send(f"User <@{payload.member.id}> du kannst dich nicht selbst voten.")
        return
    if payload.emoji.name == cfg["Emoji"]:
        #CHECK LAST UPVOTE
        DBCursor.execute("select 'yes' as Result from last_upvote where USER_ID = '%s' AND current_timestamp() > DATE_ADD(UPVOTE_DATE, INTERVAL %s MINUTE);",(payload.member.id,minutes))
        res = DBCursor.fetchall()
        try:
            res = res[0][0]
        except IndexError:
            #IF NOT IN DB, THEN RES=YES ELSE NOTHING
            DBCursor.execute(f"select 'yes' as Result from last_upvote where USER_ID = {payload.member.id};")
            res = DBCursor.fetchall()
            try:
                res = res[0][0]
                res = "false"
            except IndexError:
                res = "yes"
            
        if res == "yes":
            #INSERT LAST UPVOTE
            DBCursor.execute(f"INSERT INTO last_upvote (USER_ID, UPVOTE_DATE) VALUES ({payload.member.id}, current_timestamp()) ON DUPLICATE KEY UPDATE UPVOTE_DATE = current_timestamp()")
            DB.commit()
            DBCursor.execute(f"INSERT INTO upvote (USER_ID, UPVOTE_DATE, UPVOTE, VONUSER_ID) VALUES ({msg.author.id}, current_timestamp(), 1, {payload.member.id}) ON DUPLICATE KEY UPDATE UPVOTE_DATE = current_timestamp()")
            DB.commit()
            #INSERT UPVOTE
            await channel.send(f"<@{msg.author.id}> hat einen Upvote von {payload.member.name} bekommen")
        else:
            await channel.send(f"<@{payload.member.id}> du hast erst kürzlich gevotet. Zwischen jedem Vote müssen {minutes} Minuten liegen.")
            #await payload.member.send(f"User <@{payload.member.id}> du hast erst kürzlich gevotet. Zwischen jedem Vote müssen {minutes} Minuten liegen.")

            #mycursor.execute()
            
            
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

bot.run(cfg["DiscordToken"])