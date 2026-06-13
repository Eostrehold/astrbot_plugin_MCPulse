# MCPulse

AstrBot 插件 - Minecraft 服务器状态监控

## 功能特性

- 支持查询 Minecraft Java 版和 Bedrock 版服务器状态
- 支持自动识别服务器类型（Java/Bedrock）
- 支持定时监控多个服务器
- 支持服务器离线/恢复/高延迟告警通知
- 支持历史数据统计和图表生成
- 支持通过 AstrBot WebUI 配置

## 指令列表

| 指令 | 说明 |
|------|------|
| /mcstatus <地址或名称> | 查询服务器状态 |
| /mcping <地址:端口> | 一次性查询（不添加监控） |
| /mcadd <地址:端口> [备注] [分组] | 添加服务器监控 |
| /mcdel <地址或名称> | 删除服务器监控 |
| /mclist | 查看监控服务器列表 |
| /mcstats <地址或名称> [天数] | 查看统计信息 |
| /mcchart <地址或名称> [天数] | 生成趋势图表 |

## 安装

1. 将插件目录复制到 AstrBot 的 plugins 目录
2. 安装依赖：pip install -r requirements.txt
3. 在 AstrBot WebUI 中启用插件

## 配置

插件支持通过 AstrBot WebUI 进行配置：

- 监控设置: 监控间隔、超时时间
- 通知设置: 离线告警、恢复通知、高延迟告警
- 数据保留: 历史数据保留天数
- 权限设置: 是否仅管理员可管理

## 开发

`
pip install -r requirements.txt
pip install pytest pytest-asyncio
pytest tests/ -v
`

## License

MIT
