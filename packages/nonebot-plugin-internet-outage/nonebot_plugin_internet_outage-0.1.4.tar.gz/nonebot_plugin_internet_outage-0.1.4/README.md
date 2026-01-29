# nonebot-plugin-internet-outage

## 描述

一个基于 NoneBot2 的插件，用于定时获取 Cloudflare Radar 的全球互联网中断事件数据，并在指定的群组内发送消息通知。

## 功能特点

* 定时从 **Cloudflare Radar API** 获取全球网络事件数据
* 同时监测：

  * **流量异常（Traffic Anomaly）**
  * **已确认中断（Outage Annotation）**
* 自动区分并推送以下四种情况：

  1. **仅流量异常**
  2. **仅已确认中断**
  3. **流量异常 + 已确认中断（同时存在）**
  4. **流量异常 → 后期升级为已确认中断**
* 升级事件会 **重新推送一次**，避免信息遗漏

## 安装

<details>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行，输入以下指令即可安装

```bash
nb plugin install nonebot-plugin-internet-outage
```

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下，打开命令行，根据你使用的包管理器，输入相应的安装命令

<details>
<summary>pip</summary>

```bash
pip install nonebot-plugin-internet-outage
```
</details>
<details>
<summary>pdm</summary>

```bash
pdm add nonebot-plugin-internet-outage
```
</details>
<details>
<summary>poetry</summary>

```bash
poetry add nonebot-plugin-internet-outage
```
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件，在 `[tool.nonebot]` 部分追加写入

```toml
plugins = ["nonebot-plugin-internet-outage"]
```

</details>

## 依赖插件

本插件需要以下依赖插件：
- `nonebot_plugin_apscheduler`：用于定时任务调度
- `nonebot_plugin_localstore`：用于本地数据存储

## 配置项

在 NoneBot2 配置文件（如 `.env`、`.env.prod`）中添加以下配置：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `outage_cf_token` | `str` | 无 |  Cloudflare API Token（必填） |
| `outage_group_id` | `list[int \| str]` | `[]` | 接收通知的群号列表 |
| `outage_proxies` | `str` | `None` | HTTP 代理地址（可选） |
| `outage_debug` | `bool` | `False` | 调试模式 |

## Cloudflare API Token 权限说明

你需要在 Cloudflare 控制台创建一个 **API Token**，并至少启用以下权限：

* **Account → Radar → Read**

该插件仅使用 Radar 数据，不涉及任何账号写入操作。

### 配置示例

```ini
# 在 .env 文件中添加以下配置
outage_cf_token="your_cloudflare_api_token_here"
outage_group_id=[123456789, 987654321]
outage_proxies="http://127.0.0.1:7890"  # 可选
outage_debug=false
```

## 消息示例

### 确认中断事件
```
🌐 互联网中断事件

📍 国家：日本
🕒 开始时间：2025-12-01T08:30:00Z UTC
📡 影响范围：全国级中断
⚠️ 原因：光缆断裂

📝 说明：
日本部分区域发生海底光缆断裂，导致全国范围内互联网服务中断...

🔗 来源：
https://radar.cloudflare.com/...
```

### 流量异常事件
```
⚠️ 互联网流量异常

📍 国家：美国
🕒 开始时间：2025-12-01T10:15:00Z UTC
💡 备注：该事件为流量异常，尚未确认中断。
```

## 工作机制

1. **数据获取**：每10分钟从 Cloudflare Radar API 获取最近7天的流量异常和中断事件数据
2. **事件匹配**：尝试将流量异常与中断事件进行时间关联（±15分钟）
3. **状态处理**：
   - 新流量异常 → 发送异常通知
   - 新确认中断 → 发送中断通知
   - 已存在的异常匹配到中断 → 更新为中断通知
4. **避免重复**：使用本地存储记录已处理的事件UUID，避免重复推送

## 故障排除

### 常见问题

1. **无法获取数据**
   - 检查 `outage_cf_token` 是否正确
   - 检查网络连接，如有需要配置代理
   - 查看 NoneBot 日志获取详细错误信息

2. **未收到推送**
   - 检查 `outage_group_id` 是否正确配置
   - 确认机器人已加入目标群组
   - 检查是否有权限在群组中发送消息

3. **重复推送**
   - 检查本地存储文件是否损坏（位于插件数据目录）
   - 可尝试删除存储文件重新开始

## 鸣谢

- [Cloudflare Radar](https://radar.cloudflare.com/) - 提供全球互联网中断数据
- [nonebot-plugin-apscheduler](https://github.com/nonebot/plugin-apscheduler) - NoneBot 的定时任务插件
- [nonebot-plugin-localstore](https://github.com/nonebot/plugin-localstore) - NoneBot 的本地数据存储插件

## 许可证

MIT License
