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

def checkDM(Channdel_Object):
    if type(Channdel_Object) is discord.channel.TextChannel:
        return True
    else:
        return False

bot = commands.Bot(command_prefix='>', description="Chartsekte Bot")
bot.remove_command('help')

@bot.command()
async def help(ctx):
    if checkDM(ctx.message.channel):
        await ctx.send('**ChartSekte Bot**\n\n**Website**\nhttps://chartsekte.de \n**Commands:**`\n>ping [Selftest]\n>top [Zeigt die Top 5 User an]`')
    else:
        return
@bot.command()
async def ping(ctx):
    if checkDM(ctx.message.channel):
        await ctx.send('pong')
    else:
        return
@bot.command()
async def top(ctx, num=5):
    if checkDM(ctx.message.channel):
        DBCursor.execute("select USER_ID, sum(Upvote)  from chartsekte.upvote group by USER_ID Order by sum(Upvote) DESC")
        res = DBCursor.fetchall()
        res_string = ""
        i = 0
        for y,x in res:
            i = i+1
            res_string = res_string+ f"**Platz {i}:** Votes: {x} User:<@{y}>\n"
            if i == 5:
                break
        await ctx.send('**Top 5 gevoteten Personen:**\n\n'+res_string)
    else:
        return

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
    ch = bot.get_channel(payload.channel_id)
    msg = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

    #CHECK EMOJI
    if payload.emoji.name != cfg["Emoji"]:
        return

    #CHECK SELFVOTE
    if payload.member.id == msg.author.id:
        
        await ch.send(f"User <@{payload.member.id}> du kannst dich nicht selbst voten.",delete_after=cfg["DELETE_AFTER"])
        return

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

    #INSERT UPVOTE        
    if res == "yes":
        #IGNORE USER
        if msg.author.id == cfg["IGNORE_MENTION_ID"]:
            await ch.send(f"Der User {msg.author.name} kann nicht gevotet werden.", delete_after=cfg["DELETE_AFTER"])
        else:
             #INSERT LAST UPVOTE
            DBCursor.execute(f"INSERT INTO last_upvote (USER_ID, UPVOTE_DATE) VALUES ({payload.member.id}, current_timestamp()) ON DUPLICATE KEY UPDATE UPVOTE_DATE = current_timestamp()")
            DB.commit()
            DBCursor.execute(f"INSERT INTO upvote (USER_ID, UPVOTE_DATE, UPVOTE, VONUSER_ID) VALUES ({msg.author.id}, current_timestamp(), 1, {payload.member.id}) ON DUPLICATE KEY UPDATE UPVOTE_DATE = current_timestamp()")
            DB.commit()
            await channel.send(f"<@{msg.author.id}> hat einen Upvote von {payload.member.name} bekommen")
    else:
        await ch.send(f"<@{payload.member.id}> du hast erst kürzlich gevotet. Zwischen jedem Vote müssen {minutes} Minuten liegen.",delete_after=cfg["DELETE_AFTER"])
        #await payload.member.send(f"User <@{payload.member.id}> du hast erst kürzlich gevotet. Zwischen jedem Vote müssen {minutes} Minuten liegen.")

bot.run(cfg["DiscordToken"])