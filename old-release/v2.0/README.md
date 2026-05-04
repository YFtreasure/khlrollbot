# Roll-Bot —— 积分助手 v2.0.1

基于 [khl.py](https://github.com/TWT233/khl.py) 开发的 Kook 机器人

主要功能

- 随机抽奖：`/roll [最小值] [最大值] [数量]`  
  支持自定义范围和个数，结果以卡片形式返回。
- **负载**：`/cpu`  
  查看当前服务器的 CPU 使用率及物理/逻辑核心数。
- **交互式帮助**：`/help [页数]`  
  使用卡片分页展示所有命令，点击按钮即可切换页面（每次点击发送新卡片）。
- **机器人信息**：`/info`  
  展示版本、开发者及依赖库信息，包含 khl.py 链接按钮。
- **听音乐**：`/music [名称] [歌手]`  
  听音乐，默认为网易云，需要可以修改。


### 环境要求
- Python 3.8+
- 一个 Kook 机器人账号（在 [Kook 开发者平台](https://developer.kookapp.cn/) 创建）

### 安装依赖
```bash
pip install khl.py psutil aiohttp random
