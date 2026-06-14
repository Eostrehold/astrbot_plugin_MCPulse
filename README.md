# MCPulse

AstrBot 插件 - Minecraft 服务器状态监控

## 功能特性

- 支持查询 Minecraft Java 版和 Bedrock 版服务器状态
- 支持自动识别服务器类型（Java/Bedrock）
- 支持定时监控多个服务器
- 支持服务器离线/恢复/高延迟告警通知
- 支持历史数据统计和图表生成
- 支持通过 AstrBot WebUI 配置
- 支持以图片形式输出服务器状态信息
- 支持每个群独立设置默认服务器
- 添加服务器后立即执行首次状态查询

## 指令列表

| 指令 | 说明 |
|------|------|
| /mcstatus [地址或名称] | 查询服务器状态（省略参数则使用默认服务器） |
| /mcping <地址:端口> | 一次性查询（不添加监控） |
| /mcadd <地址:端口> [备注] [分组] | 添加服务器监控并立即查询 |
| /mcdel <地址或名称> | 删除服务器监控 |
| /mclist | 查看监控服务器列表 |
| /mcstats [地址或名称] [天数] | 查看统计信息（省略参数则使用默认服务器） |
| /mcsetdefault <地址或名称> | 设置当前群/用户的默认服务器 |

## 使用示例

**查询服务器状态（图片输出）：**

/mcstatus mc.hypixel.net

返回精美图片卡片，包含服务器图标、在线状态、人数、延迟、版本、MOTD 和在线玩家列表。

**设置默认服务器：**

/mcsetdefault Hypixel

设置后，直接输入 /mcstatus 即可查询默认服务器，无需每次输入地址。

**添加服务器监控：**

/mcadd mc.hypixel.net:25565 Hypixel 小游戏

添加成功后立即执行一次状态查询并返回结果。

## 安装

进入 AstrBot 插件目录：

```powershell
cd C:\path\to\AstrBot\data\plugins
git clone https://github.com/Eostrehold/astrbot_plugin_MCPulse.git
```

重启 AstrBot 或在插件管理页重新加载插件。

## 配置

插件支持通过 AstrBot WebUI 进行配置（_conf_schema.json）：

- 监控设置：监控间隔（秒）、超时时间（秒）、启用监控
- 通知设置：离线告警、恢复通知、高延迟告警、延迟阈值（ms）
- 数据保留：历史数据保留天数，到期自动清理
- 权限设置：是否仅管理员可管理服务器

## 开发

```
pip install -r requirements.txt
pip install pytest pytest-asyncio
pytest tests/ -v
```

## 依赖

- mcstatus - Minecraft 服务器状态查询
- aiosqlite - 异步 SQLite 数据库
- matplotlib - 图表生成
- Pillow - 图片渲染（状态卡片）

## License

MIT
