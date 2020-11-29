import discord
from discord.ext import commands
from discord.ext.tasks import loop
from discord.utils import get
import datetime
import mysql.connector as mysql
from config import config as cfg
from config import IGNORE_LIST as IGNORE_LIST

try:
    DB = mysql.connect(
        host= cfg["DB_Server"],
        user= cfg["DB_User"],
        passwd = cfg["DB_Pass"],
        port = cfg["DB_Port"],
        db = cfg["DB_Database"]
    )
    DBCursor = DB.cursor()
    WPDB = mysql.connect(
        host= cfg["WP_DB_Server"],
        user= cfg["WP_DB_User"],
        passwd = cfg["WP_DB_Pass"],
        port = cfg["WP_DB_Port"],
        db = cfg["WP_DB_Database"]
    )
    WPDBCursor = WPDB.cursor()
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

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='>', description="Chartsekte Bot",intents=intents)
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
async def call(ctx):
    #ONLY IN VERIFICATION
    if checkDM(ctx.message.channel):
        if ctx.message.channel.id == cfg["VERIFICATION_CHANNEL"]:
            await ctx.message.author.send("\nHallo,\num dich automatisch für unserem Discord Server freizuschalten, wird deine EMail-Adresse benötigt.\nBitte schreibe einfach deine EMail-Adresse, welche du beim kauf auf chartsekte.de angegeben hast mit: \n>mail DEINEMAIL")
        else:
            return
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

@bot.command()
async def mail(ctx ,mail="none"):
    #ONLY DM
    if not checkDM(ctx.message.channel):
        #CHECK MAIL
        if mail == "none":
            await ctx.send("Du hast vergessen eine EMail-Adresse anzugeben.\nBeispiel:\n>mail meinemail@mail.de")
        else:
            #CHECK MAIL IN DB
            await ctx.send("Danke, deine Email wird überprüft. Wenn du eine aktives Abonnement hast, erhältst du deinen Rang in den nächsten Sekunden.\n\nWenn du nach 10 Minuten noch keinen Rang hast, du aber das Produkt gekauft hast, schreibe bitte unserem Support unter: https://t.me/chartsektensupport an.\n\nDu hast ausversehen eine falsche Email-Adresse angegeben? Wiederhole den Command einfach.")
            DBCursor.execute(f"SELECT STATUS FROM users where USER_MAIL = '{mail}'")
            res =DBCursor.fetchall()
            try:
                #SET ROLE
                if res[0][0] == 'ACTIVE':
                    guild = bot.get_guild(cfg["GUILD_ID"])
                    role = get(guild.roles, name=cfg["ROLE"])
                    user = guild.get_member(ctx.message.author.id)
                    await user.add_roles(role)
                    #SAFE ID IN DB
                    DBCursor.execute(f"UPDATE users SET DISCORD_ID ='{ctx.message.author.id}' where USER_MAIL = '{mail}'")
                    DB.commit()
            except:
                pass
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
        if msg.author.id in IGNORE_LIST:
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

@loop(minutes=5)
async def member_sync():
    #INSERT USERS FROM WP WITH STATUS ACTIVE
    WPDBCursor.execute(f"""SELECT DISTINCT um.user_id, u.user_email, u.display_name, p2.post_title, p2.post_type
        FROM  {cfg["WORDPRESS_PREFIX"]}_posts AS p
        LEFT JOIN  {cfg["WORDPRESS_PREFIX"]}_posts AS p2 ON p2.ID = p.post_parent
        LEFT JOIN  {cfg["WORDPRESS_PREFIX"]}_users AS u ON u.id = p.post_author
        LEFT JOIN  {cfg["WORDPRESS_PREFIX"]}_usermeta AS um ON u.id = um.user_id
        WHERE p.post_type = 'wc_user_membership'
        AND p.post_status IN ('wcm-active')
        AND p2.post_type = 'wc_membership_plan';""")
    res = WPDBCursor.fetchall()
    for x in res:
        DBCursor.execute(f"""
        INSERT INTO users
        (DISCORD_ID, USER_MAIL, DISPLAY_NAME, MEMBERSHIP, STATUS)
        VALUES(NULL, '{x[1]}', '{x[2]}', '{x[3]}', 'ACTIVE')
        ON DUPLICATE KEY UPDATE 
        MEMBERSHIP = '{x[3]}', STATUS='ACTIVE'
        """)
        DB.commit()

    #SET STATUS INACTIVE IF EMAIL NOT IN WP DB
    WPDBCursor.execute(f"""
        update chartsekte.users 
        SET STATUS = 'INACTIVE'
        WHERE BINARY USER_MAIL NOT IN
        (
         SELECT DISTINCT  BINARY u.user_email
        FROM  {cfg["WORDPRESS_PREFIX"]}_posts AS p
        LEFT JOIN  {cfg["WORDPRESS_PREFIX"]}_posts AS p2 ON p2.ID = p.post_parent
        LEFT JOIN  {cfg["WORDPRESS_PREFIX"]}_users AS u ON u.id = p.post_author
        LEFT JOIN  {cfg["WORDPRESS_PREFIX"]}_usermeta AS um ON u.id = um.user_id
        WHERE p.post_type = 'wc_user_membership'
        AND p.post_status IN ('wcm-active')
        AND p2.post_type = 'wc_membership_plan'
        )
        """)
    WPDB.commit()

    #REMOVE ROLES FROM DB ENTRYS
    DBCursor.execute(f"""
        SELECT * from users WHERE STATUS = 'INACTIVE'
        """)
    res = DBCursor.fetchall()

    await bot.wait_until_ready()
    guild = bot.get_guild(cfg["GUILD_ID"])
    role = get(guild.roles, name=cfg["ROLE"])

    for x in res:
        user = guild.get_member(int(x[0]))
        await user.remove_roles(role)

    channel = bot.get_channel(cfg["OutputChannel"])
    await channel.send(f"Wordpress DataBase Sync")

@member_sync.before_loop
async def member_sync_before():
    global role_to_change
    await bot.wait_until_ready()

#colour_change.start()
member_sync.start()
bot.run(cfg["DiscordToken"])