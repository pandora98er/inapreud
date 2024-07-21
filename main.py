import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from gtts import gTTS
from datetime import datetime
import os
import asyncio
from keep_alive import keep_alive
from collections import deque
import pytz
import re
from datetime import datetime, timedelta, timezone
import random
import sqlite3
from discord.ext import commands, tasks

queue = deque()
keep_alive()

import sqlite3
giveaway_running = False
countdown_task = None
start_message_id = None
end_time = None
winners = None
channel = None

conn = sqlite3.connect('giveaways.db')
c = conn.cursor()


ffmpegOptions = {'options': "-vn"}

os.system('clear')

class color():
    green = '\033[92m'
    pink = '\033[95m'
    red = '\33[91m'
    yellow = '\33[93m'
    blue = '\33[94m'
    gray = '\33[90m'
    reset = '\33[0m'
    bold = '\33[1m'
    italic = '\33[3m'
    unline = '\33[4m'

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='i', intents=intents)
bot.remove_command('help')
voice = None
playing = False

@bot.event
async def on_ready():
    print(
        f'{color.gray + color.bold}{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {color.blue}CONSOLE{color.reset}  {color.pink}discord.on_ready{color.reset} Đã đăng nhập bot {color.bold}{bot.user}{color.reset}'
    )
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(
                                  type=discord.ActivityType.listening,
                                  name='Ina hát'))

greetings_join = [
    "<a:INA_gaurun:1240722330217484298> Dân chơi @userđã join vào phòng~",
    "Vịt con <a:INA_beoi:1240722765611536486> @user <a:INA_beoi:1240722765611536486> đã đi lạc vào phòng~",
    "<a:INA_yay:1234620570914656346> Bạn @user đã đến thăm~"
]

# Danh sách các câu chào khi rời phòng
greetings_leave = [
    "<a:INA_EBE:1240722884305883236>  Em bé {member} đã rời khỏi phòng~",
    "<a:INA_gaukhunglong4:1245022497733349447>  Mình sẽ nhớ {member} lắm, nhớ quay lại vào lần sau nhé~"
    "<:textcut:1245023392827183224> "
]

# Hàm gửi tin nhắn chào mừng
async def send_welcome_message(channel, message, color=0xFF69B4):
    try:
        embed = discord.Embed(description=message, color=color)
        await channel.send(embed=embed)
    except Exception as e:
        print(e)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        if after.channel is not None and not member.bot:  # Kiểm tra nếu thành viên mới tham gia và không phải là bot
            random_greeting = random.choice(greetings_join)  # Chọn ngẫu nhiên một câu chào từ danh sách `greetings_join`
            await send_welcome_message(
                after.channel,
                random_greeting.replace("@user", f"<@{member.id}>").replace("<phòng>", f"<#{after.channel.id}>"),
                color=0xFF69B4  # Màu hồng đậm
            )
        if before.channel is not None and not member.bot:  # Kiểm tra nếu thành viên rời khỏi phòng voice chat và không phải là bot
            random_greeting_leave = random.choice(greetings_leave)  # Chọn ngẫu nhiên một câu chào từ danh sách `greetings_leave`
            await send_welcome_message(
                before.channel,
                random_greeting_leave.replace("{member}", f"{member.display_name}"),
                color=0xFF0000  # Màu đỏ
            )

@bot.command(name='join')
async def join(ctx):
    global voice

    if ctx.author.voice is None:
        await ctx.send('Tạo room voice chat đi bae ~')
        return

    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(ctx.author.voice.channel)
    else:
        voice = await ctx.author.voice.channel.connect()

@bot.command(name='s')
async def s(ctx, *, arg: str):
    global voice, playing

    if not arg:
        return

    if ctx.message.author.voice is None:
        await ctx.send('Tạo room voicechat đê!')
        return

    if ctx.guild.voice_client is None:
        try:
            voice = await ctx.message.author.voice.channel.connect()
        except Exception as e:
            print('error', e)
            return
    elif ctx.guild.voice_client.channel != ctx.message.author.voice.channel:
        await ctx.send('Đang ở voice chat khác')
        return

    tts = gTTS(text=arg, lang='vi')
    tts.save('tts-audio.mp3')
    queue.append(('tts-audio.mp3', ctx))
    if not playing:
        await play_next()

async def play_next():
    global playing
    if queue:
        playing = True
        file, ctx = queue.popleft()
        voice.play(FFmpegPCMAudio(file),
                   after=lambda e: asyncio.run_coroutine_threadsafe(
                       play_next(), bot.loop))
        while voice.is_playing():
            await asyncio.sleep(1)
        os.remove(file)
        playing = False
    else:
        playing = False

@bot.event
async def on_message(message):
    # ID của phòng cần xóa tin nhắn
    target_channel_id = 1181611632779087892
  # Thay thế bằng ID của phòng cần xóa tin nhắn

    # Kiểm tra nếu tin nhắn được gửi trong phòng voice chat cần xóa tin nhắn
    if message.channel.id == target_channel_id:
        # Xóa tin nhắn
        await message.delete()

    # Tiếp tục xử lý các sự kiện khác
    await bot.process_commands(message)

@bot.command(name='leave')
async def leave(ctx):
    global voice, playing

    if ctx.guild.voice_client is None:
        await ctx.send('Bot không ở trong room này')
        return

    if voice is not None and voice.is_playing():
        voice.stop()

    await ctx.guild.voice_client.disconnect()
    voice = None
    playing = False

# Hàm để bot nhạc tham gia vào kênh voice và gửi thông báo
@bot.event
async def on_guild_channel_create(channel):
    # Kiểm tra nếu kênh mới tạo là một phòng voice chat
    if isinstance(channel, discord.VoiceChannel):
        # Gửi trạng thái bot nhạc vào phòng voice chat mới tạo sau 3 giây
        await asyncio.sleep(3)
        await botnhac(channel)


async def musicbot(voice_channel):
    music_role_id = 1218176567566536754
    guild = voice_channel.guild

    music_members = [
        member for member in guild.members
        if any(role.id == music_role_id for role in member.roles)
    ]
    active_members = [
        member for member in voice_channel.members if member in music_members
    ]

    if not active_members:
        return

    total_active_bots = len(active_members)

    active_embed = discord.Embed(
        title="<a:GoogleVoice:1240721830948638901> Thông tin bot nhạc<a:GoogleVoice:1240721830948638901>",
        color=discord.Color.green())
    active_embed.add_field(name="Tổng số bot nhạc đang phát",
                           value=f"{total_active_bots}",
                           inline=False)
    active_embed.add_field(
        name=f"Phòng: {voice_channel.mention}",
        value=" ".join([member.display_name for member in active_members]),
        inline=False)

    # Gửi embed vào phòng voice chat mới tạo
    await voice_channel.send(embed=active_embed)


@bot.command(name='botnhac')
async def botnhac(ctx):
    music_role_id = 1218176567566536754
    voice_channels = ctx.guild.voice_channels

    if not voice_channels:
        await ctx.send("Không có bot nhạc nào đang hoạt động trong server")
        return

    active_music_bots = {}
    inactive_music_bots = set()
    error_music_bots = set()  # Danh sách bot không online

    music_members = [
        member for member in ctx.guild.members
        if any(role.id == music_role_id for role in member.roles)
    ]

    total_music_bots = len(music_members)
    total_active_bots = 0

    # Tạo danh sách bot lỗi và bot chưa được sử dụng
    for member in music_members:
        if member.status == discord.Status.offline:
            error_music_bots.add(
                member)  # Thêm bot không online vào danh sách bot lỗi
        elif member.voice:  # Kiểm tra bot đang ở trong phòng voice chat
            total_active_bots += 1
        else:
            inactive_music_bots.add(
                member
            )  # Thêm bot không đang hoạt động vào danh sách bot chưa được sử dụng

    active_embed = discord.Embed(
        title="<a:GoogleVoice:1240721830948638901>  Thông tin bot nhạc  <a:GoogleVoice:1240721830948638901>",
        color=discord.Color.red())
    active_embed.add_field(name="Tổng số bot",
                           value=f"{total_active_bots}/{total_music_bots}",
                           inline=False)
    for voice_channel in voice_channels:
        active_members = [
            member for member in voice_channel.members
            if member in music_members
        ]
        if active_members:
            bot_list = ""
            for bot in active_members:
                bot_list += f"{bot.display_name}\n"
            active_embed.add_field(
                name=f"Phòng: {voice_channel.mention}",
                value=bot_list,
                inline=False)  # Sử dụng voice_channel.mention để tag tên phòng

    # Tạo embed cho bot chưa được sử dụng
    inactive_embed = discord.Embed(
        title="<a:quayde:1240725149247078410> Bot nhạc còn trống <a:quayde:1240725149247078410> ",
        color=discord.Color.green())
    for bot in inactive_music_bots:
        inactive_embed.add_field(
            name=bot.display_name, value="",
            inline=False)  # Đề cập đến bot chưa được sử dụng

    error_embed = discord.Embed(
        title="<:10263818:1240757641576316938> Bot đang bảo trì <:10263818:1240757641576316938>",
        color=discord.Color.yellow())
    for bot in error_music_bots:
        error_embed.add_field(name=bot.display_name, value="",
                              inline=False)  # Đề cập đến bot lỗi

    await ctx.send(embed=active_embed)
    await ctx.send(embed=inactive_embed)
    await ctx.send(embed=error_embed)


class AvatarView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    @discord.ui.button(label="Check avatar cá nhân", style=discord.ButtonStyle.secondary)
    async def user_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=0xffb782)
        embed.set_author(name=f"{self.member.name}", icon_url=self.member.avatar.url)
        embed.set_image(url=self.member.avatar.url)
        embed.set_footer(text=f"Yêu cầu bởi {interaction.user}", icon_url=interaction.user.avatar.url)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Check avatar guild", style=discord.ButtonStyle.primary)
    async def server_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.member.guild_avatar:
            embed = discord.Embed(color=0xffb782)
            embed.set_author(name=f"{self.member.name}#{self.member.discriminator}", icon_url=self.member.guild_avatar.url)
            embed.set_image(url=self.member.guild_avatar.url)
            embed.set_footer(text=f"Yêu cầu bởi {interaction.user}", icon_url=interaction.user.avatar.url)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("Người dùng này không có avatar server.", ephemeral=True)

    @discord.ui.button(label="Check ảnh bìa", style=discord.ButtonStyle.success)
    async def personal_banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await bot.fetch_user(self.member.id)
        if user.banner:
            embed = discord.Embed(color=0xffb782)
            embed.set_author(name=f"{self.member.name}", icon_url=user.avatar.url)
            embed.set_image(url=user.banner.url)
            embed.set_footer(text=f"Yêu cầu bởi {interaction.user}", icon_url=interaction.user.avatar.url)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("Người dùng này không có banner cá nhân.", ephemeral=True)

c.execute('''CREATE TABLE IF NOT EXISTS giveaways
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              prize TEXT,
              duration TEXT,
              num_winners INTEGER,
              author_id INTEGER,
              start_message_id INTEGER,
              channel_id INTEGER,
              end_time TEXT)''')
conn.commit()

giveaway_count = 0  # Khởi tạo biến giveaway_count

def parse_time(duration: str) -> int:
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    match = re.match(r"(\d+)([smhd])$", duration)
    if match:
        value, unit = match.groups()
        return int(value) * time_units[unit]
    else:
        return 0

def create_start_embed(ctx, prize: str, duration: str, author: discord.User, num_winners: int, giveaway_id: int, time_left: str) -> discord.Embed:
    global giveaway_count
    giveaway_count += 1

    hanoi_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    current_datetime = datetime.now(hanoi_timezone).strftime("%d/%m/%Y %H:%M:%S")

    title = f"<a:2canh_left:1252579452643180584>__Giveaway Bắt Đầu__<a:2canh_right:1252579413866971176> "
    start_embed = discord.Embed(title=title, color=discord.Color.yellow())

    author_avatar_url = author.avatar.url if author.avatar else "https://discord.com/assets/dd4dbc0016779df1378e7812eabaa04d.png"
    start_embed.set_thumbnail(url=author_avatar_url)
    start_embed.set_footer(text=f"Mã số {giveaway_id} Giveaways  {(current_datetime)}", icon_url=author_avatar_url)

    start_embed.description = f"<:Gift:1263234506400206999>  𝙶𝚒𝚊̉𝚒 𝚝𝚑𝚞̛𝚘̛̉𝚗𝚐:  {prize}\n<a:1alarm_clock:1263242729526395000>𝚃𝚑𝚘̛̀𝚒 𝚐𝚒𝚊𝚗 𝚍̄𝚎̂́𝚖 𝚗𝚐𝚞̛𝚘̛̣𝚌: {time_left}\n<a:tim_hoa:1245033196975034389>𝚂𝚘̂́ 𝚕𝚞̛𝚘̛̣𝚗𝚐: {num_winners}\n  <:money_pinkcoin:1240722584455086201>𝙽𝚐𝚞̛𝚘̛̀𝚒 𝚝𝚘̂̉ 𝚌𝚑𝚞̛́𝚌: <@{author.id}>\n\n _Thả react <a:ga_pinggiveaway:1199748822654537728> để tham gia_"
    return start_embed

def create_end_embed(ctx, prize: str, winners_mentions: str, giveaway_id: int) -> discord.Embed:
    global giveaway_count

    hanoi_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    current_datetime = datetime.now(hanoi_timezone).strftime("%d/%m/%Y %H:%M:%S")

    end_embed = discord.Embed(
        title="<a:2canh_left:1252579452643180584>__Giveaway Kết Thúc__ <a:2canh_right:1252579413866971176>",
        color=discord.Color.pink()
    )

    author_avatar_url = ctx.author.avatar.url if ctx.author.avatar else "https://discord.com/assets/dd4dbc0016779df1378e7812eabaa04d.png"
    end_embed.set_thumbnail(url=author_avatar_url)
    end_embed.set_footer(text=f"Mã số {giveaway_id} giveaways  {(current_datetime)}", icon_url=author_avatar_url)

    end_embed.description = f"<:Gift:1263234506400206999>𝙶𝚒𝚊̉𝚒 𝚝𝚑𝚞̛𝚘̛̉𝚗𝚐: {prize}\n <:vm_neoncrown8:1200544726496059412> 𝚆𝚒𝚗𝚗𝚎𝚛:{winners_mentions}\n  <:money_pinkcoin:1240722584455086201>𝙽𝚐𝚞̛𝚘̛̀𝚒 𝚝𝚘̂̉ 𝚌𝚑𝚞̛́𝚌: <@{ctx.author.id}>"
    return end_embed



async def countdown(ctx, message, end_time, prize, duration, num_winners, giveaway_id):
    while True:
        time_left = end_time - datetime.now(timezone.utc)
        if time_left.total_seconds() <= 0:
            break
        time_left_str = str(timedelta(seconds=int(time_left.total_seconds())))
        start_embed = create_start_embed(ctx, prize, duration, ctx.author, num_winners, giveaway_id, time_left_str)
        await message.edit(embed=start_embed)
        await asyncio.sleep(1)

    # Sau khi đếm ngược kết thúc
    emoji = discord.utils.get(ctx.guild.emojis, name='ga_pinggiveaway')
    if emoji:
        try:
            message = await ctx.channel.fetch_message(message.id)  # Fetch message to get the latest reactions
            reaction = discord.utils.get(message.reactions, emoji=emoji)
            await handle_giveaway_end(ctx, reaction, prize, num_winners, ctx.channel, giveaway_id)
        except discord.errors.NotFound:
            await ctx.send("Tin nhắn bắt đầu giveaway không tồn tại.")
    else:
        await ctx.send("Emoji không tồn tại hoặc bot không có quyền sử dụng emoji này.")

async def handle_giveaway_end(ctx, reaction, prize, num_winners, channel, giveaway_id):
    if reaction is None:
        await channel.send("Không có ai tham gia giveaway.")
        return

    users = await reaction.users().flatten()
    users = [user for user in users if not user.bot]  # Loại bỏ bot

    if len(users) == 0:
        await channel.send("Không có ai tham gia giveaway.")
        return

    winners = random.sample(users, min(num_winners, len(users)))
    winner_mentions = ', '.join([winner.mention for winner in winners])

    end_embed = discord.Embed(
        title="Giveaway đã kết thúc!",
        description=f"Phần thưởng: **{prize}**\nNgười chiến thắng: {winner_mentions}",
        color=discord.Color.green()
    )
    await channel.send(embed=end_embed)

@bot.command(name='ga')
async def ga(ctx, duration: str, num_winners: int, *, prize: str):
    required_role_id = 1246846231955636380
    if required_role_id not in [role.id for role in ctx.author.roles]:
        error_embed = discord.Embed(
            description=f"Hello {ctx.author.mention}, để tổ chức Giveaway vui lòng liên hệ <@1036641731610947604> để được hướng dẫn",
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
        return

    seconds = parse_time(duration)
    if seconds == 0:
        return await ctx.send("Vui lòng sử dụng đúng định dạng giờ m (phút), h (giờ), d (ngày)")

    end_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)

    c.execute('''INSERT INTO giveaways (prize, duration, num_winners, author_id, start_message_id, channel_id, end_time)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', (prize, duration, num_winners, ctx.author.id, None, ctx.channel.id, end_time.strftime("%Y-%m-%d %H:%M:%S")))
    giveaway_id = c.lastrowid
    conn.commit()
    time_left_str = str(timedelta(seconds=seconds))

    start_message = await ctx.send(embed=create_start_embed(ctx, prize, duration, ctx.author, num_winners, giveaway_id, time_left_str))
    start_message_id = start_message.id

    c.execute('UPDATE giveaways SET start_message_id = ? WHERE id = ?', (start_message.id, giveaway_id))
    conn.commit()

    await ctx.message.delete()

    emoji = discord.utils.get(ctx.guild.emojis, name='ga_pinggiveaway')
    if emoji:
        await start_message.add_reaction(emoji)
    else:
        await ctx.send("Emoji không tồn tại hoặc bot không có quyền sử dụng emoji này.")
        return

    # Bắt đầu đếm ngược trong một tác vụ riêng biệt
    asyncio.create_task(countdown(ctx, start_message, end_time, prize, duration, num_winners, giveaway_id))


@tasks.loop(seconds=1)
async def start_countdown(ctx, message, end_time, prize, duration, num_winners, giveaway_id):
    time_left = end_time - datetime.now(timezone.utc)
    if time_left.total_seconds() <= 0:
        start_countdown.stop()
        time_left_str = "00:00:00"
    else:
        time_left_str = str(timedelta(seconds=int(time_left.total_seconds())))

    start_embed = create_start_embed(ctx, prize, duration, ctx.author, num_winners, giveaway_id, time_left_str)
    await message.edit(embed=start_embed)

async def handle_giveaway_end(ctx, reaction, prize, num_winners, channel, giveaway_id):
    c.execute('SELECT * FROM giveaways WHERE id = ?', (giveaway_id,))
    giveaway_info = c.fetchone()

    if not giveaway_info:
        return await ctx.send("Thông tin giveaway không tồn tại trong hệ thống.")

    if reaction:
        eligible_users = []
        async for user in reaction.users():
            if not user.bot:
                eligible_users.append(user)

        if len(eligible_users) < num_winners:
            await ctx.send("Không đủ người tham gia huhu")
            return

        winners = random.sample(eligible_users, num_winners)

        if winners:
            winners_mentions = ' '.join([winner.mention for winner in winners])
            end_embed = create_end_embed(ctx, prize, winners_mentions, giveaway_id)
            await channel.send(embed=end_embed)

            role_id = 1246846231955636380
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            if role:
                topic = f"Trao giải giveaways"
                thread = await channel.create_thread(
                    name=topic, 
                    type=discord.ChannelType.public_thread
                )

                thread_embed = discord.Embed(
                    description=f"Xin chúc mừng <a:sao_9pinkstar:1198024071032619150>{winners_mentions}<a:sao_9pinkstar:1198024071032619150> đã trở thành người chiến thắng giải *{prize}*! <:ga_200:1252579269121413191>  Tận hưởng phần thưởng của mình nhaa!!\n<@&{role_id}> trao giải cho bạn nè <:cggl_timneon:1249430852316827698>.\nMã số giveaway: {giveaway_id}",
                    color=discord.Color.pink()
                )
                await thread.send(embed=thread_embed)

            else:
                await ctx.send("Role không tồn tại.")
        else:
            await ctx.send("Không có ai tham gia giveaway!\n")
    else:
        await ctx.send("Không có ai tham gia giveaway!\n")
@bot.event
async def on_disconnect():
    conn.close()

@bot.command()
async def start_giveaway(ctx, duration: str, num_winners: int, *, prize: str):
    global giveaway_running, current_giveaway_info

    required_role_id = 1246846231955636380
    if required_role_id not in [role.id for role in ctx.author.roles]:
        await ctx.send("Bạn không có quyền bắt đầu giveaway.")
        return

    seconds = parse_time(duration)
    if seconds == 0:
        return await ctx.send("Vui lòng sử dụng đúng định dạng giây s, phút m, giờ h, ngày d tương ứng với giây, phút, giờ, ngày")


    end_time = datetime.utcnow() + timedelta(seconds=seconds)


    start_embed = create_start_embed(ctx, prize, duration, ctx.author, num_winners)
    start_message = await ctx.send(embed=start_embed)

    current_giveaway_info = {
        'end_time': end_time,
        'num_winners': num_winners,
        'prize': prize,
        'message_id': start_message.id,
        'channel_id': ctx.channel.id
    }
    giveaway_running = True

    emoji = discord.utils.get(ctx.guild.emojis, name='ga_pinggiveaway')
    if emoji:
        await start_message.add_reaction(emoji)
    else:
        await ctx.send("Emoji không tồn tại hoặc bot không có quyền sử dụng emoji này.")
        return

@bot.event
async def on_ready():
    print(f'Đăng nhập thành công {bot.user}')

@bot.event
async def on_disconnect():
    conn.close()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def check(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    embed = discord.Embed(title=f"Xin chào, bạn cần check gì ở {member}", color=0xffb782)
    embed.set_footer(text=f"Yêu cầu bởi {ctx.author}", icon_url=ctx.author.avatar.url)
    view = AvatarView(member)
    await ctx.send(embed=embed, view=view)
bot.run(os.environ.get('TOKEN'))