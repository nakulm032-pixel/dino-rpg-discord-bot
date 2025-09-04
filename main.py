import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
import os

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === DINOSAUR DATA ===
DINOSAURS = [
    {"name": "Tyrannosaurus Rex", "emoji": "🦖", "rarity": "Legendary", "hp": 120, "attack": 45, "defense": 25, "speed": 15, "level": 1},
    {"name": "Spinosaurus", "emoji": "🦕", "rarity": "Legendary", "hp": 110, "attack": 42, "defense": 22, "speed": 18, "level": 1},
    {"name": "Velociraptor", "emoji": "🏃‍♂️", "rarity": "Rare", "hp": 65, "attack": 35, "defense": 15, "speed": 45, "level": 1},
    {"name": "Triceratops", "emoji": "🥬", "rarity": "Common", "hp": 70, "attack": 20, "defense": 25, "speed": 15, "level": 1},
    {"name": "Stegosaurus", "emoji": "🎺", "rarity": "Common", "hp": 80, "attack": 18, "defense": 30, "speed": 10, "level": 1},
]

# === MEAT SYSTEM ===
MEATS = {
    "small_meat": {"name": "🥩 Small Meat", "chance": 50, "price": 50, "desc": "45-55% catch chance for small dinos"},
    "medium_meat": {"name": "🍖 Medium Meat", "chance": 70, "price": 120, "desc": "60-70% for medium dinos"},
    "big_meat": {"name": "🍗 Big Meat", "chance": 85, "price": 300, "desc": "75-80% for big dinos"},
    "legendary_meat": {"name": "⭐ Legendary Meat", "chance": 98, "price": 5000, "desc": "90% only for legendary (1/1000 spawn)"}
}

JOBS = ["Trainer", "Paleontologist", "Fossil Dealer", "Battle Coach"]
SPAWN_RATES = {"Common": 0.85, "Rare": 0.01, "Legendary": 0.001}

PLAYER_DATA = {}

# === FUNCTIONS ===
def get_player(user_id):
    if str(user_id) not in PLAYER_DATA:
        PLAYER_DATA[str(user_id)] = {
            "coins": 1000,
            "dinosaurs": [],
            "inventory": {"small_meat": 2, "medium_meat": 1},
            "job": None,
            "level": 1,
            "xp": 0,
            "achievements": [],
            "last_work": None,
            "last_daily": None
        }
    return PLAYER_DATA[str(user_id)]

def spawn_dinosaur():
    rand = random.random()
    if rand <= SPAWN_RATES["Legendary"]:
        rarity = "Legendary"
    elif rand <= SPAWN_RATES["Rare"]:
        rarity = "Rare"
    else:
        rarity = "Common"
    possible = [d for d in DINOSAURS if d["rarity"] == rarity]
    return random.choice(possible)

# === BOT COMMANDS ===
@bot.event
async def on_ready():
    print(f'🦖 {bot.user} has connected to Discord!')
    print('Dino RPG Bot is alive and running!')

@bot.command()
async def s(ctx):
    """Spawn a wild dinosaur"""
    dino = spawn_dinosaur()
    await ctx.send(f'🦖 Wild {dino["name"]} ({dino["rarity"]}) appeared! HP:{dino["hp"]}, ATK:{dino["attack"]}')

@bot.command()
async def c(ctx, meat_type: str = None):
    """Catch with or without meat"""
    player = get_player(ctx.author.id)
    chance = 30
    if meat_type and meat_type in MEATS:
        if player["inventory"].get(meat_type,0)>0:
            chance = MEATS[meat_type]["chance"]
            player["inventory"][meat_type]-=1
            await ctx.send(f'Used {MEATS[meat_type]["name"]}!')
        else:
            await ctx.send(f'You lack {meat_type}! Try !shop.')
            return
    if random.randint(1,100)<=chance:
        dino = spawn_dinosaur()
        player["dinosaurs"].append(dino)
        await ctx.send(f'SUCCESS! You caught {dino["name"]} {dino["emoji"]}!')
    else:
        await ctx.send('Missed! The dinosaur ran away.')

@bot.command()
async def shop(ctx):
    txt = '\n'.join([f"{m['name']}: {m['desc']} ({m['price']} coins)" for m in MEATS.values()])
    await ctx.send(f'🏪 Shop Items:\n{txt}')

@bot.command()
async def buy(ctx,item:str):
    player = get_player(ctx.author.id)
    for k,v in MEATS.items():
        if item==k:
            if player["coins"]>=v["price"]:
                player["coins"]-=v["price"]
                player["inventory"][k]=player["inventory"].get(k,0)+1
                await ctx.send(f'Bought {v["name"]}!')
            else:
                await ctx.send('Not enough coins!')
            return
    await ctx.send('Item not found!')

@bot.command()
async def job(ctx, role:str=None):
    player = get_player(ctx.author.id)
    if not role:
        await ctx.send(f'Your job: {player["job"]}. Jobs: {JOBS}')
    elif role in JOBS:
        player["job"]=role
        await ctx.send(f'Now you are a {role}! Use !work to earn coins.')
    else:
        await ctx.send(f'Not a valid job.')

@bot.command()
async def work(ctx):
    player = get_player(ctx.author.id)
    if not player["job"]:
        await ctx.send('Select job first with !job.')
        return
    now=datetime.now()
    if player["last_work"] and now-datetime.fromisoformat(player["last_work"])<timedelta(hours=1):
        left=timedelta(hours=1)-(now-datetime.fromisoformat(player["last_work"]))
        await ctx.send(f'Cooldown: wait {left.seconds//60} min.')
        return
    earnings={"Trainer":random.randint(50,100),"Paleontologist":random.randint(80,150),"Fossil Dealer":random.randint(60,120),"Battle Coach":random.randint(70,130)}
    val=earnings[player["job"]]
    player["coins"]+=val
    player["last_work"]=now.isoformat()
    await ctx.send(f'Earned {val} coins as {player["job"]}!')

@bot.command()
async def profile(ctx):
    player = get_player(ctx.author.id)
    txt = f'📊 **Profile**\nCoins: {player["coins"]}\nDinos: {len(player["dinosaurs"])}\nLevel: {player["level"]}\nXP: {player["xp"]}\nJob: {player["job"]}'
    await ctx.send(txt)

@bot.command()
async def inventory(ctx):
    player = get_player(ctx.author.id)
    txt = '\n'.join([f'{MEATS[k]["name"]}: {v}' for k,v in player["inventory"].items()])
    await ctx.send(f'🎒 **Inventory**\n{txt}')

@bot.command()
async def daily(ctx):
    player = get_player(ctx.author.id)
    now=datetime.now()
    if player["last_daily"] and now-datetime.fromisoformat(player["last_daily"])<timedelta(days=1):
        left=timedelta(days=1)-(now-datetime.fromisoformat(player["last_daily"]))
        await ctx.send(f'Cooldown: wait {left.seconds//3600} hrs.')
        return
    coins = random.randint(100,300)
    player["coins"]+=coins
    player["last_daily"]=now.isoformat()
    await ctx.send(f'💎 Daily: Got {coins} coins!')

@bot.command(name='helpme')
async def helpme(ctx):
    help_text = """
🦖 **Dino RPG Commands**
`!s` - Spawn a wild dinosaur
`!c [meat]` - Catch dinosaur (optional: use meat for better chances)
`!shop` - View meat shop
`!buy <item>` - Buy meat from shop
`!profile` - View your profile
`!inventory` - Check your items
`!job [role]` - Set/view your job
`!work` - Work to earn coins (1 hour cooldown)
`!daily` - Claim daily coins reward
    """
    await ctx.send(help_text)

# Run the bot
if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
