import random  #随机数
import psutil  #CPU查询
import aiohttp #尝试HTTP失败力
import json    #尝试JSON也失败力

from khl import Bot, Message, EventTypes  #发消息/捕捉事件
from khl.card import CardMessage, Card, Module, Element, Types, Struct #全明星阵容 再也不缺了 有些用不到摆在这里当吉祥物 以后要用就不用再重新搞了
import khl.api #妄想 没用

# init Bot
bot = Bot(token='token')


@bot.on_startup #start!!!!
async def _(_):
    print("机器人启动成功！Bot is ready!")





# 听音乐状态~ 来自khl.py官方文档
@bot.command()
async def music(msg: Message, music: str, singer: str):
    # music name : str
    # singer name : str
    # music_software : Enum ['cloudmusic'、'qqmusic'、'kugou'], 'cloudmusic' in default
    await bot.client.update_listening_music(music, singer, "cloudmusic")
    print(music, singer)
    await msg.reply(f'开听吧！Music is {music},Singer is {singer}')







@bot.command(name='roll')
async def rollcard(msg: Message, min: int = 1, max: int = 100, c: int = 1):
    print("The Command 'roll' is run now.")
    result = [random.randint(min, max) for i in range(c)]
    c = Card(Module.Header('抽奖结果'), Module.Section(f'您抽到了**{result}**'))
    cm = CardMessage(c)
    await msg.reply(cm)
          





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








# 字典
help_dict = {
    1: "/roll <最小值> <最大值> <数量> (抽取随机数) ",
    2: "/cpu (查看服务端CPU占用及数据)",
    3: "/info (Bot基本数据，版本及开发者",
    4: "/help <页数> 本命令帮助，共4个",
}

def build_help_card(page: int) -> Card:
    """根据页码构建帮助卡片"""
    # 获取当前页命令内容
    command_desc = help_dict.get(page, "未找到该help页数")
    
    # 卡片
    card = Card(
        Module.Header(f'命令帮助 - 第 {page} / 4 页'),
        Module.Section(command_desc)
    )
    
    # 构建按钮行
    buttons = []
    if page > 1:
        buttons.append(Element.Button('上一页', str(page - 1), Types.Click.RETURN_VAL))
    if page < 4:
        buttons.append(Element.Button('下一页', str(page + 1), Types.Click.RETURN_VAL))
    
    if buttons:
        card.append(Module.ActionGroup(*buttons))
    
    card.append(Module.Context('点击按钮切换页面'))
    return card

@bot.command(name='help')
async def help_cmd(msg: Message, page: int = 1):
    """/help 命令，默认显示第一页"""
    # 边界检查
    if page < 1:
        page = 1
    elif page > 4:
        page = 4
    
    # 构建卡片并发送
    card = build_help_card(page)
    await msg.reply(CardMessage(card))

@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def handle_button_click(bot, event):
    target_page = int(event.body['value'])  #这一段最阴间，要指定频道id和位置
    channel_id = event.body['target_id']
    new_card = build_help_card(target_page)

    # 获取频道对象
    channel = await bot.client.fetch_public_channel(channel_id)
    # 发送新卡片
    await channel.send(CardMessage(new_card))














@bot.command(name='info')   # Card Info By Nixer At 2026.3.28
async def world(msg: Message):
    card = Card(
        Module.Header('积分助手 v2.0 - 2026'),
        Module.Section('更新：**卡片消息**'),
        Module.Divider(),
        Module.Section(
            '制作：**Nixer** (核心开发者)，**Wind阿风** (辅助开发者)',
        ),
        Module.Section(
            '本机器人基于'
        ),
        Module.ActionGroup(      # 套一个AcionGroup就可以让他在下一行，不加按钮会在结尾
        Element.Button(
                'khl.py',
                click=Types.Click.LINK,            # 大写LINK！！
                value='https://github.com/TWT233/khl.py'
        )),
        
        Module.Context('© Nixer 2023-2026')
    )
    await msg.reply(CardMessage(card))
    
import logging
logging.basicConfig(level='INFO')
bot.run()
