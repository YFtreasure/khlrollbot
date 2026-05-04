import random
import psutil
import asyncio
import os
import aiosqlite
from datetime import datetime, date

from khl import Bot, Message, EventTypes
from khl.card import CardMessage, Card, Module, Element, Types, Struct

bot = Bot(token='YOUR_BOT_TOKEN_HERE')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'checkin.db')
_db = None

ADMIN_IDS = set()  # 在此填入你的KOOK用户ID


async def get_db():
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
    return _db


async def init_db():
    db = await get_db()
    await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            points INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            total_checkins INTEGER DEFAULT 0,
            last_checkin TEXT DEFAULT ''
        )
    ''')
    await db.commit()


@bot.on_startup
async def startup(_):
    await init_db()
    print('机器人启动成功！Bot is ready!')


@bot.command()
async def music(msg: Message, music_name: str, singer: str):
    await bot.client.update_listening_music(music_name, singer, 'cloudmusic')
    print(music_name, singer)
    await msg.reply('开听吧！', is_temp=True)


@bot.command(name='roll')
async def rollcard(msg: Message, min: int = 1, max: int = 100, c: int = 1):
    print("The Command 'roll' is run now.")
    result = [random.randint(min, max) for i in range(c)]
    c = Card(Module.Header('抽奖结果'), Module.Section(f'您抽到了**{result}**'))
    await msg.reply(CardMessage(c))


@bot.command(name='cpu')
async def world(msg: Message):
    cpu_percent = psutil.cpu_percent()
    cpu_physical = psutil.cpu_count(logical=False)
    cpu_logical = psutil.cpu_count(logical=True)

    card = Card(
        Module.Header('CPU 状态'),
        Module.Section(f'**当前负载**：{cpu_percent}%'),
        Module.Section(f'**物理核心**：{cpu_physical} 个\n**逻辑核心**：{cpu_logical} 个'),
        Module.Divider(),
        Module.Context('数据来源：*psutil* 库 | 实时数据')
    )
    await msg.reply(CardMessage(card))


help_dict = {
    1: '/roll <最小值> <最大值> <数量> (抽取随机数) ',
    2: '/cpu (查看服务端CPU占用及数据)',
    3: '/info (Bot基本数据，版本及开发者)',
    4: '/help <页数> 本命令帮助，共8个',
    5: '/签到 (每日签到，获取积分奖励)',
    6: '/积分 (查看积分) | /排行榜 [人数] | /转账 @用户 数量',
    7: '【管理员】/补签 @用户 (为指定用户补签)',
    8: '【管理员】/签到查询 | /重置签到 | /签到设置 | /设置积分',
}


def build_help_card(page: int) -> Card:
    command_desc = help_dict.get(page, '未找到该help页数')
    card = Card(
        Module.Header(f'命令帮助 - 第 {page} / 8 页'),
        Module.Section(command_desc)
    )
    buttons = []
    if page > 1:
        buttons.append(Element.Button('上一页', str(page - 1), Types.Click.RETURN_VAL))
    if page < 8:
        buttons.append(Element.Button('下一页', str(page + 1), Types.Click.RETURN_VAL))
    if buttons:
        card.append(Module.ActionGroup(*buttons))
    card.append(Module.Context('点击按钮切换页面'))
    return card


@bot.command(name='help')
async def help_cmd(msg: Message, page: int = 1):
    if page < 1:
        page = 1
    elif page > 8:
        page = 8
    card = build_help_card(page)
    await msg.reply(CardMessage(card))


@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def handle_button_click(bot, event):
    target_page = int(event.body['value'])
    channel_id = event.body['target_id']
    new_card = build_help_card(target_page)
    channel = await bot.client.fetch_public_channel(channel_id)
    await channel.send(CardMessage(new_card))


@bot.command(name='info')
async def world(msg: Message):
    card = Card(
        Module.Header('积分助手 v2.2.0 - 2026'),
        Module.Section('更新：**积分系统 (积分/排行榜/转账/设置积分)**'),
        Module.Divider(),
        Module.Section('制作：**Nixer** (核心开发者)，**Wind阿风** (辅助开发者)'),
        Module.Section('本机器人基于'),
        Module.ActionGroup(
            Element.Button('khl.py', click=Types.Click.LINK, value='https://github.com/TWT233/khl.py')
        ),
        Module.Context('(c) Nixer 2023-2026')
    )
    await msg.reply(CardMessage(card))


import logging
logging.basicConfig(level=logging.INFO)


# ============================================================
# 权限 & 工具
# ============================================================

async def is_admin(msg: Message):
    if msg.author.id in ADMIN_IDS:
        return True
    try:
        guild = msg.ctx.guild
        if msg.author.id == guild.master_id:
            return True
        guild_user = await guild.fetch_user(msg.author.id)
        for role_id in guild_user.roles:
            role = await guild.fetch_role(role_id)
            if role.name == '管理员' or role.has_permission(0):
                return True
    except Exception:
        pass
    return False


async def get_user_display(user_id, guild=None):
    try:
        if guild:
            u = await guild.fetch_user(user_id)
        else:
            u = await bot.client.fetch_user(user_id)
        name = u.nickname or u.username
        return f'(met){user_id}(met)', name
    except Exception:
        return user_id, user_id


def strip_mention(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith('(met)') and raw.endswith('(met)'):
        return raw[5:-5]
    return raw


# ============================================================
# 数据库操作
# ============================================================

async def db_ensure_user(user_id: str):
    db = await get_db()
    await db.execute(
        'INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,)
    )
    await db.commit()


async def db_get_user(user_id: str):
    db = await get_db()
    cur = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = await cur.fetchone()
    return row


async def db_do_checkin(user_id: str, streak: int, total: int, date_str: str, bonus: int):
    db = await get_db()
    await db.execute(
        'UPDATE users SET streak = ?, total_checkins = ?, last_checkin = ?, '
        'points = points + ? WHERE user_id = ?',
        (streak, total, date_str, bonus, user_id)
    )
    await db.commit()


async def db_set_fields(user_id: str, streak: int, total: int, date_str: str):
    params = [streak, total, user_id]
    extra = ''
    if date_str:
        extra = ', last_checkin = ?'
        params.insert(2, date_str)
    db = await get_db()
    await db.execute(
        f'UPDATE users SET streak = ?, total_checkins = ?{extra} WHERE user_id = ?',
        tuple(params)
    )
    await db.commit()


async def db_delete_user(user_id: str):
    db = await get_db()
    await db.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    await db.commit()


async def db_set_points(user_id: str, points: int):
    db = await get_db()
    await db.execute(
        'INSERT INTO users (user_id, points) VALUES (?, ?) '
        'ON CONFLICT(user_id) DO UPDATE SET points = ?',
        (user_id, points, points)
    )
    await db.commit()


async def db_get_leaderboard(limit: int = 10):
    db = await get_db()
    cur = await db.execute(
        'SELECT user_id, points, streak, total_checkins FROM users ORDER BY points DESC LIMIT ?',
        (limit,)
    )
    return await cur.fetchall()


async def db_transfer(from_id: str, to_id: str, amount: int):
    db = await get_db()
    await db.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (amount, from_id))
    await db.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (amount, to_id))
    await db.commit()


# ============================================================
# 签到
# ============================================================

@bot.command(name='签到')
async def checkin(msg: Message):
    user = msg.author
    user_id = user.id
    today = str(date.today())
    now = datetime.now()

    await db_ensure_user(user_id)
    row = await db_get_user(user_id)

    if row['last_checkin'] == today:
        await msg.reply(f'(met){user_id}(met) 你今天已经签到过了！明天再来吧~', is_temp=True)
        return

    yesterday = str(date.today().fromordinal(date.today().toordinal() - 1))
    new_streak = row['streak'] + 1 if row['last_checkin'] == yesterday else 1
    new_total = row['total_checkins'] + 1

    bonus = random.randint(1, 10)
    if new_streak >= 7:
        bonus += random.randint(5, 20)

    await db_do_checkin(user_id, new_streak, new_total, today, bonus)

    new_row = await db_get_user(user_id)

    cm = CardMessage(
        Card(
            Module.Header('签到成功！'),
            Module.Section(f'(met){user_id}(met) 签到成功！'),
            Module.Divider(),
            Module.Section(
                f'连续签到：**{new_streak}** 天\n'
                f'累计签到：**{new_total}** 天\n'
                f'本次获得积分：**{bonus}** 分\n'
                f'当前积分：**{new_row["points"]}** 分'
            ),
            Module.Context(f'签到时间：{now.strftime("%Y-%m-%d %H:%M:%S")}')
        )
    )
    await msg.reply(cm)


# ============================================================
# 管理员签到管理
# ============================================================

@bot.command(name='补签')
async def makeup_checkin(msg: Message, target: str = ''):
    if not await is_admin(msg):
        await msg.reply('你没有权限使用此命令！', is_temp=True)
        return

    if not target:
        await msg.reply('请 @要补签的用户，例如：`/补签 @用户`', is_temp=True)
        return

    target_id = strip_mention(target)
    today = str(date.today())
    now = datetime.now()

    await db_ensure_user(target_id)
    row = await db_get_user(target_id)

    if row['last_checkin'] == today:
        await msg.reply(f'(met){target_id}(met) 今天已经签到过了，无需补签！', is_temp=True)
        return

    yesterday = str(date.today().fromordinal(date.today().toordinal() - 1))
    new_streak = row['streak'] + 1 if row['last_checkin'] == yesterday else 1
    new_total = row['total_checkins'] + 1

    await db_do_checkin(target_id, new_streak, new_total, today, 0)

    mention, name = await get_user_display(target_id, msg.ctx.guild)
    cm = CardMessage(
        Card(
            Module.Header('补签完成'),
            Module.Section(f'{mention} 已被管理员 (met){msg.author.id}(met) 补签！'),
            Module.Divider(),
            Module.Section(
                f'连续签到：**{new_streak}** 天\n'
                f'累计签到：**{new_total}** 天'
            ),
            Module.Context(f'补签时间：{now.strftime("%Y-%m-%d %H:%M:%S")}')
        )
    )
    await msg.reply(cm)


@bot.command(name='签到查询')
async def query_checkin(msg: Message, target: str = ''):
    if not await is_admin(msg):
        await msg.reply('你没有权限使用此命令！', is_temp=True)
        return

    if not target:
        await msg.reply('请 @要查询的用户，例如：`/签到查询 @用户`', is_temp=True)
        return

    target_id = strip_mention(target)
    row = await db_get_user(target_id)

    if not row:
        await msg.reply(f'(met){target_id}(met) 还没有签到记录！', is_temp=True)
        return

    mention, name = await get_user_display(target_id, msg.ctx.guild)
    last = row['last_checkin'] or '无'
    cm = CardMessage(
        Card(
            Module.Header(f'{name} 的签到数据'),
            Module.Section(
                f'{mention}\n\n'
                f'积分：**{row["points"]}** 分\n'
                f'连续签到：**{row["streak"]}** 天\n'
                f'累计签到：**{row["total_checkins"]}** 天\n'
                f'最后签到：**{last}**'
            )
        )
    )
    await msg.reply(cm)


@bot.command(name='重置签到')
async def reset_checkin(msg: Message, target: str = ''):
    if not await is_admin(msg):
        await msg.reply('你没有权限使用此命令！', is_temp=True)
        return

    if not target:
        await msg.reply('请 @要重置的用户，例如：`/重置签到 @用户`', is_temp=True)
        return

    target_id = strip_mention(target)
    await db_delete_user(target_id)
    await msg.reply(f'(met){target_id}(met) 的签到数据已被管理员 (met){msg.author.id}(met) 重置！')


@bot.command(name='签到设置')
async def set_checkin(msg: Message, target: str = '', streak: int = 0, total: int = 0, last_date: str = ''):
    if not await is_admin(msg):
        await msg.reply('你没有权限使用此命令！', is_temp=True)
        return

    if not target:
        await msg.reply(
            '用法：`/签到设置 @用户 连续天数 累计天数 [最后签到日期]`\n'
            '例如：`/签到设置 @用户 7 30 2026-05-04`',
            is_temp=True
        )
        return

    target_id = strip_mention(target)
    await db_ensure_user(target_id)
    await db_set_fields(target_id, streak, total, last_date)

    mention, name = await get_user_display(target_id, msg.ctx.guild)
    cm = CardMessage(
        Card(
            Module.Header('签到数据已修改'),
            Module.Section(
                f'{mention} 的数据已被管理员 (met){msg.author.id}(met) 修改：\n\n'
                f'连续签到：**{streak}** 天\n'
                f'累计签到：**{total}** 天'
                + (f'\n最后签到：**{last_date}**' if last_date else '')
            )
        )
    )
    await msg.reply(cm)


# ============================================================
# 积分系统
# ============================================================

@bot.command(name='积分')
async def cmd_points(msg: Message):
    user_id = msg.author.id
    await db_ensure_user(user_id)
    row = await db_get_user(user_id)

    cm = CardMessage(
        Card(
            Module.Header('积分信息'),
            Module.Section(f'(met){user_id}(met)'),
            Module.Divider(),
            Module.Section(
                f'当前积分：**{row["points"]}** 分\n'
                f'连续签到：**{row["streak"]}** 天\n'
                f'累计签到：**{row["total_checkins"]}** 天'
            )
        )
    )
    await msg.reply(cm)


@bot.command(name='排行榜')
async def cmd_leaderboard(msg: Message, count: int = 10):
    count = max(1, min(count, 20))
    rows = await db_get_leaderboard(count)

    if not rows:
        await msg.reply('暂无数据！', is_temp=True)
        return

    lines = []
    medals = ['🥇', '🥈', '🥉']
    for i, r in enumerate(rows):
        medal = medals[i] if i < 3 else f'{i + 1}.'
        mention, name = await get_user_display(r['user_id'], msg.ctx.guild)
        lines.append(f'{medal} {mention} — **{r["points"]}** 分')

    cm = CardMessage(
        Card(
            Module.Header('积分排行榜'),
            Module.Section('\n'.join(lines)),
            Module.Context(f'共 {len(rows)} 人上榜')
        )
    )
    await msg.reply(cm)


@bot.command(name='转账')
async def cmd_transfer(msg: Message, target: str = '', amount: int = 0):
    user_id = msg.author.id

    if not target or amount <= 0:
        await msg.reply('用法：`/转账 @用户 数量`\n例如：`/转账 @用户 100`', is_temp=True)
        return

    target_id = strip_mention(target)
    if target_id == user_id:
        await msg.reply('不能给自己转账！', is_temp=True)
        return

    await db_ensure_user(user_id)
    await db_ensure_user(target_id)

    sender = await db_get_user(user_id)
    if sender['points'] < amount:
        await msg.reply(f'积分不足！你当前只有 **{sender["points"]}** 分。', is_temp=True)
        return

    await db_transfer(user_id, target_id, amount)

    new_sender = await db_get_user(user_id)
    mention, name = await get_user_display(target_id, msg.ctx.guild)

    cm = CardMessage(
        Card(
            Module.Header('转账成功'),
            Module.Section(
                f'(met){user_id}(met) → {mention}\n'
                f'转账金额：**{amount}** 分\n'
                f'你的余额：**{new_sender["points"]}** 分'
            )
        )
    )
    await msg.reply(cm)


@bot.command(name='设置积分')
async def cmd_set_points(msg: Message, target: str = '', points: int = 0):
    if not await is_admin(msg):
        await msg.reply('你没有权限使用此命令！', is_temp=True)
        return

    if not target:
        await msg.reply('用法：`/设置积分 @用户 数量`\n例如：`/设置积分 @用户 10086`', is_temp=True)
        return

    target_id = strip_mention(target)
    await db_set_points(target_id, points)

    mention, name = await get_user_display(target_id, msg.ctx.guild)
    cm = CardMessage(
        Card(
            Module.Header('积分已设置'),
            Module.Section(
                f'{mention} 的积分已被管理员 (met){msg.author.id}(met) 设置为：**{points}** 分'
            )
        )
    )
    await msg.reply(cm)


# ============================================================

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
bot.run()
