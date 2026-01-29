from nonebot.plugin import PluginMetadata
from pydantic import BaseModel
from nonebot import get_bots, logger, get_plugin_config, require
from nonebot.adapters.onebot.v11 import Message

import httpx
import json
from datetime import datetime
from pathlib import Path

# -----------------------------
# 插件配置
# -----------------------------
class InternetOutageConfig(BaseModel):
    outage_debug: bool = False
    outage_proxies: str = None
    outage_group_id: list[int | str] = []
    outage_cf_token: str

__plugin_meta__ = PluginMetadata(
    name="互联网异常事件监测",
    description="基于 Cloudflare Radar 的全球互联网异常事件自动推送",
    usage="自动运行",
    type="application",
    homepage="https://github.com/CN171-1/nonebot-plugin-internet-outage",
    supported_adapters={"~onebot.v11"},
    config=InternetOutageConfig,
)

config = get_plugin_config(InternetOutageConfig)

proxy = config.outage_proxies
group_ids = config.outage_group_id
CF_TOKEN = config.outage_cf_token

TRAFFIC_API = "https://api.cloudflare.com/client/v4/radar/traffic_anomalies"
OUTAGE_API = "https://api.cloudflare.com/client/v4/radar/annotations/outages"

OUTAGE_CAUSE_MAP = {
    "GOVERNMENT_DIRECTED": "政府命令",
    "MILITARY_ACTION": "军事行动影响",
    "CABLE_CUT": "光缆断裂",
    "POWER_OUTAGE": "大规模停电",
    "TECHNICAL_PROBLEM": "重大技术故障",
    "NETWORK_CONGESTION": "网络严重拥塞",
    "UNKNOWN": "原因暂不明确",
    "WEATHER": "自然灾害",
    "MISCONFIGURATION": "配置错误",
    "DNS": "DNS 故障",
}

OUTAGE_TYPE_MAP = {
    "NATIONWIDE": "全国级中断",
    "REGIONAL": "区域级中断",
    "NETWORK": "运营商 / 网络级中断",
    "PLATFORM": "平台级中断",
}

require("nonebot_plugin_localstore")
require("nonebot_plugin_apscheduler")

import nonebot_plugin_localstore as store
from nonebot_plugin_apscheduler import scheduler

class StorageManager:
    def __init__(self):
        self.data_dir = Path(store.get_plugin_data_dir())
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def get_seen_dict(self, key: str) -> dict:
        file = self.data_dir / f"{key}.json"
        if file.exists():
            try:
                with open(file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    async def save_seen_dict(self, key: str, data: dict):
        file = self.data_dir / f"{key}.json"
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def is_first_run(self, key: str) -> bool:
        return not (self.data_dir / f"{key}.json").exists()

storage = StorageManager()

async def get_json(url: str, params: dict = None, timeout: int = 30) -> dict:
    """获取JSON数据"""
    headers = {"Authorization": f"Bearer {CF_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers, proxy=proxy) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"请求失败 {url}: {e}")
        return {}

async def fetch_traffic_anomalies():
    params = {"type": "LOCATION", "status": "VERIFIED", "dateRange": "7d"}
    data = await get_json(TRAFFIC_API, params)
    return data.get("result", {}).get("trafficAnomalies", [])

async def fetch_outages():
    params = {"dateRange": "7d"}
    data = await get_json(OUTAGE_API, params)
    return data.get("result", {}).get("annotations", [])

def normalize_time(ts: str, bucket_minutes: int = 30) -> str:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    bucket = (dt.minute // bucket_minutes) * bucket_minutes
    normalized = dt.replace(minute=bucket, second=0, microsecond=0)
    return normalized.isoformat()

def build_event_id(country: str, start_date: str) -> str:
    normalized_time = normalize_time(start_date, 30)
    event_id = f"{country}_{normalized_time}"
    return event_id

def match_outage(anomaly, outages):
    country = anomaly["locationDetails"]["code"]
    a_start = datetime.fromisoformat(anomaly["startDate"].replace("Z", "+00:00"))
    for o in outages:
        if country not in o["locations"]:
            continue
        o_start = datetime.fromisoformat(o["startDate"].replace("Z", "+00:00"))
        if abs((a_start - o_start).total_seconds()) <= 900:
            return o
    return None

def build_message(outage):
    loc = outage["locationsDetails"][0]["name"]
    cause = outage["outage"]["outageCause"]
    cause_cn = OUTAGE_CAUSE_MAP.get(cause, cause)
    otype = outage["outage"]["outageType"]
    otype_cn = OUTAGE_TYPE_MAP.get(otype, otype)
    return Message(
        f"🌐 互联网中断事件\n\n"
        f"📍 国家：{loc}\n"
        f"🕒 开始时间：{outage['startDate']} UTC\n"
        f"📡 影响范围：{otype_cn}\n"
        f"⚠️ 原因：{cause_cn}\n\n"
        f"📝 说明：\n{outage['description']}\n\n"
        f"🔗 来源：\n{outage['linkedUrl']}"
    )

def build_message_from_anomaly(anomaly):
    loc = anomaly["locationDetails"]["name"]
    start = anomaly["startDate"]
    return Message(
        f"⚠️ 互联网流量异常\n\n"
        f"📍 国家：{loc}\n"
        f"🕒 开始时间：{start} UTC\n"
        f"💡 备注：该事件为流量异常，尚未确认中断。"
    )

async def broadcast(message: Message):
    bots = get_bots()
    if not bots:
        return
    bot = list(bots.values())[0]
    if not group_ids:
        logger.warning("未配置推送群，跳过")
        return
    for gid in group_ids:
        try:
            await bot.send_group_msg(group_id=int(gid), message=message)
        except Exception as e:
            logger.error(f"推送至群 {gid} 失败: {e}")

@scheduler.scheduled_job("interval", minutes=10, id="internet_outage_monitor", misfire_grace_time=20)
async def outage_schedule():
    key = "outage_events"

    anomalies = await fetch_traffic_anomalies()
    outages = await fetch_outages()

    if anomalies is None or outages is None:
        logger.warning(
            "Cloudflare Radar 数据不完整（anomalies 或 outages 获取失败），跳过本轮检查"
        )
        return

    seen = await storage.get_seen_dict(key)
    first_run = await storage.is_first_run(key)

    used_outages: set[tuple] = set()

    for a in anomalies:
        country = a["locationDetails"]["code"]
        event_id = build_event_id(country, a["startDate"])

        outage = match_outage(a, outages)

        # 如果匹配到了 outage，先标记该 outage 已被使用
        if outage:
            outage_id = (
                outage["outage"]["outageType"],
                outage["outage"]["outageCause"],
                outage["startDate"],
                tuple(outage["locations"]),
            )
            used_outages.add(outage_id)

        if event_id not in seen:
            # 新事件
            if outage:
                msg = build_message(outage)
                sent_type = "outage"
                log_type = "anomaly + outage"
            else:
                msg = build_message_from_anomaly(a)
                sent_type = "anomaly"
                log_type = "anomaly"

            if not first_run:
                await broadcast(msg)

            if outage:
                cause = OUTAGE_CAUSE_MAP.get(
                    outage["outage"]["outageCause"],
                    outage["outage"]["outageCause"]
                )
                logger.info(
                    f"发现断网事件（{log_type}）：[{country}] {cause}"
                )
            else:
                logger.info(
                    f"发现断网事件（{log_type}）：[{country}]"
                )

            seen[event_id] = {"sent_type": sent_type}

        else:
            # anomaly -> outage 升级
            if seen[event_id]["sent_type"] == "anomaly" and outage:
                msg = build_message(outage)

                if not first_run:
                    await broadcast(msg)

                cause = OUTAGE_CAUSE_MAP.get(
                    outage["outage"]["outageCause"],
                    outage["outage"]["outageCause"]
                )
                logger.info(
                    f"更新断网事件（anomaly -> outage）：[{country}] {cause}"
                )

                seen[event_id]["sent_type"] = "outage"

    for o in outages:
        outage_id = (
            o["outage"]["outageType"],
            o["outage"]["outageCause"],
            o["startDate"],
            tuple(o["locations"]),
        )

        # 已被 anomaly 消费过的 outage，直接跳过
        if outage_id in used_outages:
            continue

        country = o["locations"][0]
        event_id = build_event_id(country, o["startDate"])

        if event_id in seen:
            continue

        msg = build_message(o)

        if not first_run:
            await broadcast(msg)

        cause = OUTAGE_CAUSE_MAP.get(
            o["outage"]["outageCause"],
            o["outage"]["outageCause"]
        )
        logger.info(
            f"发现断网事件（仅 outage）：[{country}] {cause}"
        )

        seen[event_id] = {"sent_type": "outage"}

    await storage.save_seen_dict(key, seen)
