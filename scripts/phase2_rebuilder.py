#!/usr/bin/env python3

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from desktop_delivery import sync_brief_to_desktop
from provider_registry import extract_chat_content, resolve_chat_provider

WORKFLOW_ENGINE_DIR = Path("" + str(Path(__file__).resolve().parents[1]) + "/引擎/03_全链路SOP工作流")
PHASE2_SKILL_DIR = Path("" + str(Path(__file__).resolve().parents[1]) + "/skills/dasheng-daily-phase2")
BRIEF_AI_PROMPT_PATH = WORKFLOW_ENGINE_DIR / "02_Brief_AI生成规则.md"
BRIEF_AI_SCHEMA_PATH = PHASE2_SKILL_DIR / "brief_card_schema.json"

SOURCE_TIER_WEIGHT = {
    "official": 1.35,
    "mainstream_media": 1.18,
    "platform_hotspot": 1.0,
    "self_media": 0.82,
    "personal_opinion": 0.58,
}

CHANNEL_EDITORIAL_WEIGHT = {
    "reports": 1.15,
    "content_research": 1.0,
    "wechat": 1.05,
    "wb": 0.95,
    "x": 0.8,
    "douyin": 0.72,
    "bili": 0.72,
    "xhs": 0.65,
}

SERIOUS_LABELS = {
    "宏观",
    "国际局势",
    "科技产业",
    "产业链",
    "金融市场",
    "AI工具",
    "政策",
    "时政",
    "半导体",
    "能源",
}

NOISE_KEYWORDS = {
    "vlog",
    "好物",
    "探店",
    "穿搭",
    "长高",
    "补钙",
    "搞笑",
    "剧情",
    "新歌",
    "美食",
    "拉伸",
    "自我按摩",
    "肩颈酸痛",
    "体态",
    "儿童",
    "恋爱",
    "八卦",
    "测评",
    "开箱",
    "颜值",
}

GENERIC_TOKENS = {
    "今天",
    "最新",
    "继续",
    "目前",
    "现在",
    "消息",
    "内容",
    "视频",
    "文章",
    "报道",
    "观察",
    "分享",
    "直播",
    "市场",
    "global",
    "latest",
    "video",
    "news",
    "report",
}

CHAIN_STOPWORDS = {
    "最新", "今天", "继续", "市场", "视频", "报道", "消息", "官方", "全球", "再次", "突发", "局势",
    "事件", "回应", "分析", "观察", "直播", "财经", "干货", "更新", "曝光", "战争", "冲突",
    "score", "reports", "report", "bili", "douyin", "xhs", "wb", "wechat", "trendradar",
    "topnote", "topnotes", "research", "content", "latest", "来自", "热度代理", "家人们", "兄弟们",
}

STRUCTURE_KEYS = ("opening", "part_1", "part_2", "part_3", "ending")
MIN_TOPIC_COUNT = 8
MAX_TOPIC_COUNT = 10
DEFAULT_CANDIDATE_COUNT = 10


@dataclass
class IntakeRecord:
    title: str
    summary: str
    source: str
    source_item_id: str
    raw_payload: dict[str, Any]
    meta: dict[str, Any]
    source_quality_tier: str
    entities: dict[str, list[str]]
    noise_tags: list[str]
    dynamic_cluster_key: str
    dynamic_tokens: list[str]
    editor_labels: list[str]
    trendradar_signal: bool
    freshness_score: float
    heat_score: float
    heat_level: str
    source_freshness_weight: float
    source_timeliness_weight: float
    source_authority_weight: float


def read_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def normalize_text(*parts: str) -> str:
    text = " ".join(str(part or "") for part in parts if part)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def slugify(text: str) -> str:
    value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5]+", "-", text or "").strip("-").lower()
    return value or "topic"


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    return re.sub(r"[?#].*$", "", str(url).strip())


def source_type(source: str) -> str:
    value = str(source or "").lower()
    if "wechat" in value or "wx" in value:
        return "公众号文章"
    if "wb" in value:
        return "微博"
    if "xhs" in value:
        return "小红书"
    if "douyin" in value:
        return "抖音"
    if "bili" in value:
        return "B站"
    if "x" == value or value.endswith("/x") or "/x" in value:
        return "X"
    if "report" in value or "research" in value:
        return "聚合新闻"
    return "采集来源"


def extract_url(record: IntakeRecord) -> str:
    for key in ("url", "link", "jump_url", "share_url", "note_url"):
        value = record.raw_payload.get(key)
        if value:
            return str(value)
    return f"https://example.invalid/{record.source}/{record.source_item_id or 'unknown'}"


def entity_values(record: IntakeRecord) -> list[str]:
    values: list[str] = []
    for key in ("people", "orgs", "countries", "commodities", "sectors", "policies"):
        values.extend(str(item) for item in record.entities.get(key, []) if str(item).strip())
    return values


def meaningful_tokens(*parts: str) -> list[str]:
    tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", " ".join(part for part in parts if part))
    result: list[str] = []
    for token in tokens:
        lowered = token.lower()
        if lowered in (item.lower() for item in GENERIC_TOKENS):
            continue
        result.append(token)
    return result


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = str(item or "").strip()
        key = value.lower()
        if not value or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def title_noise_score(title: str, summary: str = "", noise_tags: list[str] | None = None) -> float:
    text = normalize_text(title, summary, " ".join(noise_tags or []))
    score = 0.0
    for keyword in NOISE_KEYWORDS:
        if keyword.lower() in text:
            score += 1.0
    if not re.search(r"[\u4e00-\u9fffA-Za-z]{3,}", title or ""):
        score += 2.0
    if re.fullmatch(r"https?://\S+", (title or "").strip()):
        score += 3.0
    if len(title or "") < 6:
        score += 0.8
    return round(score, 3)


def record_signal_score(record: IntakeRecord) -> float:
    tier_weight = SOURCE_TIER_WEIGHT.get(record.source_quality_tier, 0.7)
    heat_component = min(record.heat_score / 30.0, 4.0)
    timeliness_component = record.source_timeliness_weight * 2.0
    authority_component = record.source_authority_weight * 2.2
    trend_component = 1.0 if record.trendradar_signal else 0.0
    label_component = 0.8 if any(label in SERIOUS_LABELS for label in record.editor_labels) else 0.0
    penalty = title_noise_score(record.title, record.summary, record.noise_tags) * 1.25
    return round(tier_weight * 2.6 + heat_component + timeliness_component + authority_component + trend_component + label_component - penalty, 3)


def record_editorial_relevance(record: IntakeRecord) -> float:
    serious_entities = sum(len(record.entities.get(bucket, [])) for bucket in ("people", "orgs", "countries", "commodities", "sectors", "policies"))
    serious_labels = sum(1 for label in record.editor_labels if label in SERIOUS_LABELS)
    text = normalize_text(record.title, record.summary, " ".join(record.dynamic_tokens), " ".join(entity_values(record)))
    macro_hits = sum(
        1
        for keyword in (
            "通胀", "降息", "加息", "利率", "关税", "霍尔木兹", "伊朗", "以色列", "俄罗斯", "日本",
            "半导体", "英伟达", "美元", "黄金", "原油", "航运", "停火", "制裁", "美联储", "特朗普",
            "openclaw", "agent", "workflow", "芯片", "核电", "能源", "政策"
        )
        if keyword.lower() in text
    )
    channel_bonus = CHANNEL_EDITORIAL_WEIGHT.get(record.source.split("/")[-1], CHANNEL_EDITORIAL_WEIGHT.get(record.source, 0.7))
    trend_bonus = 1.0 if record.trendradar_signal else 0.0
    penalty = title_noise_score(record.title, record.summary, record.noise_tags) * 1.6
    return round(
        record_signal_score(record) * 0.55
        + serious_entities * 0.75
        + serious_labels * 0.65
        + macro_hits * 0.28
        + channel_bonus
        + trend_bonus
        - penalty,
        3,
    )


def record_to_evidence(record: IntakeRecord) -> dict[str, Any]:
    return {
        "title": record.title,
        "url": extract_url(record),
        "source_type": source_type(record.source),
        "source_tier": record.source_quality_tier,
        "channel": record.source,
        "note": record.summary,
        "entities": entity_values(record),
        "heat_level": record.heat_level,
        "heat_score": record.heat_score,
        "trendradar_signal": record.trendradar_signal,
        "signal_score": record_signal_score(record),
    }


def load_records(path: Path) -> list[IntakeRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("items") or payload.get("data") or []
    records: list[IntakeRecord] = []
    for item in payload:
        records.append(
            IntakeRecord(
                title=str(item.get("title") or "").strip(),
                summary=str(item.get("summary") or "").strip(),
                source=str(item.get("source") or "").strip(),
                source_item_id=str(item.get("source_item_id") or "").strip(),
                raw_payload=item.get("raw_payload") or {},
                meta=item.get("meta") or {},
                source_quality_tier=str(item.get("source_quality_tier") or "personal_opinion"),
                entities=item.get("entities") or {},
                noise_tags=[str(tag) for tag in item.get("noise_tags") or []],
                dynamic_cluster_key=str(item.get("dynamic_cluster_key") or item.get("event_key") or ""),
                dynamic_tokens=[str(token) for token in item.get("dynamic_tokens") or []],
                editor_labels=[str(label) for label in item.get("editor_labels") or []],
                trendradar_signal=bool(item.get("trendradar_signal")),
                freshness_score=float(item.get("freshness_score") or 0.0),
                heat_score=float(item.get("heat_score") or 0.0),
                heat_level=str(item.get("heat_level") or "D"),
                source_freshness_weight=float(item.get("source_freshness_weight") or item.get("freshness_score") or 1.0),
                source_timeliness_weight=float(item.get("source_timeliness_weight") or item.get("freshness_score") or 1.0),
                source_authority_weight=float(item.get("source_authority_weight") or 1.0),
            )
        )
    return records


def infer_run_id(records: list[IntakeRecord], arg_run_id: str | None, intake_file: Path) -> str:
    if arg_run_id:
        return arg_run_id
    if records and records[0].meta.get("run_id"):
        return str(records[0].meta["run_id"])
    return intake_file.parent.parent.name or datetime.now().strftime("%Y-%m-%d_%H%M%S")


def collect_auxiliary(intake_file: Path) -> dict[str, Any]:
    intake_root = intake_file.parent.parent
    brief_input = read_json_if_exists(intake_root / "brief_input.json") or {}
    return {
        "intake_root": intake_root,
        "brief_input": brief_input,
        "channel_top10": read_json_if_exists(intake_root / "channel_top10.json") or {},
        "event_clusters": read_json_if_exists(intake_root / "event_clusters.json") or [],
        "entity_rankings": read_json_if_exists(intake_root / "entity_rankings.json") or {},
    }


def dedupe_evidence_records(records: list[IntakeRecord]) -> list[IntakeRecord]:
    seen: set[str] = set()
    kept: list[IntakeRecord] = []
    ordered = sorted(records, key=record_signal_score, reverse=True)
    for record in ordered:
        key = canonicalize_url(extract_url(record)) or normalize_text(record.title)
        if not key or key in seen:
            continue
        seen.add(key)
        kept.append(record)
    return kept


def summarize_entities(records: list[IntakeRecord]) -> dict[str, list[dict[str, Any]]]:
    counters: dict[str, Counter[str]] = {
        "people": Counter(),
        "orgs": Counter(),
        "countries": Counter(),
        "commodities": Counter(),
        "sectors": Counter(),
        "policies": Counter(),
    }
    for record in records:
        for bucket in counters:
            counters[bucket].update(str(item) for item in record.entities.get(bucket, []) if str(item).strip())
    result: dict[str, list[dict[str, Any]]] = {}
    for bucket, counter in counters.items():
        result[bucket] = [{"name": name, "count": count} for name, count in counter.most_common(12)]
    return result


def compact_channel_top10(channel_top10: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    compacted: dict[str, list[dict[str, Any]]] = {}
    for channel, items in (channel_top10 or {}).items():
        compacted[channel] = []
        for item in items[:10]:
            compacted[channel].append(
                {
                    "channel": channel,
                    "title": item.get("title") or "",
                    "url": item.get("url") or "",
                    "heat_level": item.get("heat_level") or "D",
                    "heat_score": float(item.get("heat_score") or 0.0),
                    "author_or_account": item.get("author_or_account") or "",
                    "publish_time": item.get("publish_time") or "",
                    "excerpt": item.get("excerpt") or item.get("note") or "",
                    "trendradar_signal": bool(item.get("trendradar_signal")),
                    "noise_tags": item.get("noise_tags") or [],
                }
            )
    return compacted


def filter_event_clusters(event_clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for cluster in event_clusters:
        title = str(cluster.get("cluster_title_candidate") or cluster.get("cluster_name") or "")
        summary = str(cluster.get("cluster_summary") or "")
        noise_ratio = float(cluster.get("noise_ratio") or 0.0)
        authority = float(cluster.get("authority_score") or 0.0)
        count = int(cluster.get("count") or 0)
        entities = cluster.get("dominant_entities") or []
        actions = cluster.get("dominant_actions") or []
        serious_entity_count = len([item for item in entities if str(item).strip()])
        if title_noise_score(title, summary) >= 2.5 and authority < 1.0:
            continue
        if noise_ratio >= 0.7:
            continue
        if count <= 0:
            continue
        if count == 1 and authority < 1.0 and serious_entity_count == 0 and not actions:
            continue
        kept.append(
            {
                "cluster_id": cluster.get("cluster_id") or "",
                "cluster_title_candidate": title,
                "cluster_summary": summary,
                "count": count,
                "source_mix": cluster.get("source_mix") or {},
                "dominant_entities": cluster.get("dominant_entities") or [],
                "dominant_actions": cluster.get("dominant_actions") or [],
                "representative_titles": cluster.get("representative_titles") or [],
                "representative_links": cluster.get("representative_links") or [],
                "trendradar_coverage": float(cluster.get("trendradar_coverage") or 0.0),
                "freshness_score": float(cluster.get("freshness_score") or 0.0),
                "timeliness_score": float(cluster.get("timeliness_score") or 0.0),
                "authority_score": authority,
                "noise_ratio": noise_ratio,
                "avg_heat_score": float(cluster.get("avg_heat_score") or 0.0),
            }
        )
    kept.sort(
        key=lambda item: (
            item["authority_score"],
            item["timeliness_score"],
            item["trendradar_coverage"],
            item["avg_heat_score"],
            item["count"],
        ),
        reverse=True,
    )
    return kept[:50]


def build_cross_channel_events(channel_top10: dict[str, list[dict[str, Any]]], event_clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for cluster in event_clusters:
        sources = cluster.get("source_mix") or {}
        if len(sources) < 2:
            continue
        events.append(
            {
                "cluster_id": cluster.get("cluster_id") or "",
                "title": cluster.get("cluster_title_candidate") or "",
                "summary": cluster.get("cluster_summary") or "",
                "channels": sorted(sources.keys()),
                "count": cluster.get("count") or 0,
                "authority_score": cluster.get("authority_score") or 0.0,
                "trendradar_coverage": cluster.get("trendradar_coverage") or 0.0,
                "representative_links": (cluster.get("representative_links") or [])[:3],
            }
        )
    if events:
        return events[:15]

    token_counter: dict[str, set[str]] = defaultdict(set)
    for channel, items in channel_top10.items():
        for item in items:
            for token in meaningful_tokens(item.get("title", ""))[:5]:
                token_counter[token.lower()].add(channel)
    fallback: list[dict[str, Any]] = []
    for token, channels in token_counter.items():
        if len(channels) >= 2:
            fallback.append({"token": token, "channels": sorted(channels)})
    fallback.sort(key=lambda item: len(item["channels"]), reverse=True)
    return fallback[:10]


def derive_record_anchor_tokens(record: IntakeRecord) -> list[str]:
    anchors: list[str] = []
    anchors.extend(entity_values(record))
    anchors.extend(record.dynamic_tokens[:6])
    anchors.extend(meaningful_tokens(record.title, record.summary)[:10])
    cleaned: list[str] = []
    for token in anchors:
        value = str(token).strip()
        lowered = value.lower()
        if not value or lowered in (item.lower() for item in CHAIN_STOPWORDS):
            continue
        if title_noise_score(value) >= 2.0:
            continue
        cleaned.append(value)
    return unique_preserve_order(cleaned)[:8]


def derive_record_signature_tokens(record: IntakeRecord) -> list[str]:
    tokens: list[str] = []
    tokens.extend(entity_values(record))
    tokens.extend(record.dynamic_tokens[:8])
    tokens.extend(meaningful_tokens(record.title, record.summary)[:12])
    cleaned: list[str] = []
    for token in tokens:
        value = str(token).strip()
        lowered = value.lower()
        if not value or lowered in (item.lower() for item in CHAIN_STOPWORDS):
            continue
        if title_noise_score(value) >= 2.0:
            continue
        cleaned.append(value)
    return unique_preserve_order(cleaned)[:10]


def build_logic_chains(records: list[IntakeRecord]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    ordered = sorted(records, key=record_editorial_relevance, reverse=True)
    chains: list[dict[str, Any]] = []
    record_to_chain: dict[str, str] = {}
    for record in ordered:
        record_key = canonicalize_url(extract_url(record)) or normalize_text(record.title)
        anchors = derive_record_anchor_tokens(record)
        if not anchors:
            anchors = meaningful_tokens(record.title, record.summary)[:4]
        anchor_set = {item.lower() for item in anchors}
        best_chain = None
        best_overlap = 0
        for chain in chains:
            overlap = len(anchor_set & chain["anchor_set"])
            if overlap > best_overlap:
                best_overlap = overlap
                best_chain = chain
        if best_chain and best_overlap >= 2:
            chain = best_chain
        else:
            chain = {
                "chain_id": "",
                "records": [],
                "anchor_counter": Counter(),
                "entity_counter": Counter(),
                "channels": Counter(),
                "score_sum": 0.0,
                "anchor_set": set(),
            }
            chains.append(chain)
        chain["records"].append(record)
        chain["anchor_counter"].update(item.lower() for item in anchors)
        chain["entity_counter"].update(item.lower() for item in entity_values(record))
        chain["channels"][record.source.split("/")[-1]] += 1
        chain["score_sum"] += record_editorial_relevance(record)
        chain["anchor_set"].update(anchor_set)
        record_to_chain[record_key] = "__pending__"

    for index, chain in enumerate(chains, start=1):
        dominant = [token for token, _ in chain["anchor_counter"].most_common(3)] or [f"chain-{index}"]
        chain_id = slugify("-".join(dominant[:3]))[:48] or f"chain-{index}"
        chain["chain_id"] = chain_id
        chain["dominant_tokens"] = dominant
        chain["record_count"] = len(chain["records"])
        chain["avg_score"] = round(chain["score_sum"] / max(len(chain["records"]), 1), 3)
        chain["summary_title"] = " / ".join(dominant[:2])
        chain["top_titles"] = [record.title for record in chain["records"][:3]]
        chain["top_urls"] = [extract_url(record) for record in chain["records"][:3]]
        chain["top_entities"] = [token for token, _ in chain["entity_counter"].most_common(4)]
        chain["channels"] = dict(chain["channels"])
        for record in chain["records"]:
            record_key = canonicalize_url(extract_url(record)) or normalize_text(record.title)
            record_to_chain[record_key] = chain_id
    chains.sort(key=lambda item: (item["avg_score"], item["record_count"]), reverse=True)
    return chains, record_to_chain


def build_logic_chain_summaries(chains: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for chain in chains[:limit]:
        summaries.append(
            {
                "chain_id": chain["chain_id"],
                "summary_title": chain["summary_title"],
                "dominant_tokens": chain["dominant_tokens"][:4],
                "top_entities": chain.get("top_entities", [])[:4],
                "record_count": chain["record_count"],
                "avg_score": chain["avg_score"],
                "channels": chain["channels"],
                "top_titles": chain["top_titles"],
                "top_urls": chain["top_urls"],
            }
        )
    return summaries


def build_secondary_distinct_signals(chains: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    selected_tokens: set[str] = set()
    remaining = list(chains[1:])
    while remaining and len(results) < limit:
        best_index = -1
        best_score = float("-inf")
        for index, chain in enumerate(remaining):
            if not chain["records"]:
                continue
            chain_tokens = {str(token).lower() for token in chain.get("dominant_tokens", []) + chain.get("top_entities", []) if str(token).strip()}
            overlap = len(chain_tokens & selected_tokens)
            score = float(chain.get("avg_score") or 0.0) + min(int(chain.get("record_count") or 0), 3) * 0.15 - overlap * 0.9
            if score > best_score:
                best_score = score
                best_index = index
        if best_index < 0:
            break
        chain = remaining.pop(best_index)
        record = chain["records"][0]
        item = record_to_evidence(record)
        item["logic_chain_id"] = chain["chain_id"]
        item["chain_summary"] = chain["summary_title"]
        results.append(item)
        selected_tokens.update(str(token).lower() for token in chain.get("dominant_tokens", []) + chain.get("top_entities", []) if str(token).strip())
    return results


def build_editorial_priority_pool(records: list[IntakeRecord], logic_chain_map: dict[str, str], limit: int = 40) -> list[dict[str, Any]]:
    signature_map: dict[str, list[str]] = {}
    signature_counter: Counter[str] = Counter()
    for record in records:
        record_key = canonicalize_url(extract_url(record)) or normalize_text(record.title)
        signature_tokens = [token.lower() for token in derive_record_signature_tokens(record)]
        signature_map[record_key] = signature_tokens
        signature_counter.update(set(signature_tokens))

    scored: list[tuple[float, IntakeRecord, str]] = []
    for record in records:
        relevance = record_editorial_relevance(record)
        serious_entities = sum(len(record.entities.get(bucket, [])) for bucket in ("people", "orgs", "countries", "commodities", "sectors", "policies"))
        serious_labels = sum(1 for label in record.editor_labels if label in SERIOUS_LABELS)
        if relevance < 4.0:
            continue
        if title_noise_score(record.title, record.summary, record.noise_tags) >= 1.8:
            continue
        if serious_entities == 0 and serious_labels == 0 and record.source_quality_tier not in {"official", "mainstream_media"} and not record.trendradar_signal:
            continue
        record_key = canonicalize_url(extract_url(record)) or normalize_text(record.title)
        scored.append((relevance, record, logic_chain_map.get(record_key, "misc")))
    scored.sort(key=lambda item: item[0], reverse=True)
    chain_buckets: dict[str, list[tuple[float, IntakeRecord]]] = defaultdict(list)
    for relevance, record, chain_id in scored:
        chain_buckets[chain_id].append((relevance, record))
    for chain_items in chain_buckets.values():
        chain_items.sort(key=lambda item: item[0], reverse=True)
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    selected_per_chain: Counter[str] = Counter()
    selected_signature_counter: Counter[str] = Counter()
    while len(result) < limit:
        best_candidate: tuple[float, IntakeRecord, str, float, float] | None = None
        for chain_id, chain_items in chain_buckets.items():
            for relevance, record in chain_items:
                key = canonicalize_url(extract_url(record)) or normalize_text(record.title)
                if key in seen:
                    continue
                signature_tokens = signature_map.get(key, [])
                novelty_bonus = 0.0
                if signature_tokens:
                    novelty_bonus = sum(1.0 / max(signature_counter[token], 1) for token in signature_tokens) / len(signature_tokens)
                    novelty_bonus *= 3.5
                overlap_penalty = sum(selected_signature_counter[token] for token in set(signature_tokens)) * 0.22
                if signature_tokens and sum(1 for token in set(signature_tokens) if selected_signature_counter[token] > 0) >= 2:
                    overlap_penalty += 0.45
                adjusted = relevance + novelty_bonus - selected_per_chain[chain_id] * 1.35 - overlap_penalty
                if best_candidate is None or adjusted > best_candidate[0]:
                    best_candidate = (adjusted, record, chain_id, novelty_bonus, overlap_penalty)
                break
        if best_candidate is None:
            break
        adjusted, record, chain_id, novelty_bonus, overlap_penalty = best_candidate
        key = canonicalize_url(extract_url(record)) or normalize_text(record.title)
        seen.add(key)
        selected_per_chain[chain_id] += 1
        selected_signature_counter.update(set(signature_map.get(key, [])))
        item = record_to_evidence(record)
        item["editorial_relevance"] = round(adjusted, 3)
        item["logic_chain_id"] = chain_id
        item["logic_chain_rank"] = selected_per_chain[chain_id]
        item["theme_novelty"] = round(novelty_bonus, 3)
        item["logic_overlap_penalty"] = round(overlap_penalty, 3)
        result.append(item)
    return result


def summarize_noise(records: list[IntakeRecord], limit: int = 20) -> list[dict[str, Any]]:
    noise_records = sorted(
        (
            record
            for record in records
            if record.noise_tags or title_noise_score(record.title, record.summary, record.noise_tags) >= 1.5
        ),
        key=lambda record: (title_noise_score(record.title, record.summary, record.noise_tags), -record_signal_score(record)),
        reverse=True,
    )
    return [
        {
            "title": record.title,
            "url": extract_url(record),
            "reason": record.noise_tags or ["低信息密度"],
        }
        for record in noise_records[:limit]
    ]


def build_brief_signal_bundle(
    run_id: str,
    records: list[IntakeRecord],
    aux: dict[str, Any],
    manual_topics: list[str],
    candidate_count: int,
) -> dict[str, Any]:
    cleaned_records = dedupe_evidence_records(records)
    logic_chains, logic_chain_map = build_logic_chains(cleaned_records)
    evidence_pool: list[dict[str, Any]] = []
    for record in cleaned_records:
        if title_noise_score(record.title, record.summary, record.noise_tags) >= 2.0:
            continue
        item = record_to_evidence(record)
        record_key = canonicalize_url(extract_url(record)) or normalize_text(record.title)
        item["logic_chain_id"] = logic_chain_map.get(record_key, "misc")
        evidence_pool.append(item)
    evidence_pool.sort(key=lambda item: item["signal_score"], reverse=True)
    trusted_evidence_pool = [
        item
        for item in evidence_pool
        if item["source_tier"] in {"official", "mainstream_media", "platform_hotspot"} or item["trendradar_signal"]
    ][:80]
    if len(trusted_evidence_pool) < 40:
        trusted_evidence_pool = evidence_pool[:80]
    editorial_priority_pool = build_editorial_priority_pool(cleaned_records, logic_chain_map, limit=40)
    if len(editorial_priority_pool) < 20:
        editorial_priority_pool = trusted_evidence_pool[:40]

    channel_top10 = compact_channel_top10(aux.get("channel_top10") or {})
    event_clusters = filter_event_clusters(aux.get("event_clusters") or [])
    cross_channel_events = aux.get("brief_input", {}).get("cross_channel_events") or build_cross_channel_events(channel_top10, event_clusters)
    trendradar_candidates = aux.get("brief_input", {}).get("trendradar_candidates") or [
        item for item in evidence_pool if item["trendradar_signal"]
    ][:20]
    top_entities = aux.get("brief_input", {}).get("top_entities") or summarize_entities(cleaned_records)

    stats = {
        "raw_record_count": len(records),
        "deduped_record_count": len(cleaned_records),
        "trusted_evidence_count": len(trusted_evidence_pool),
        "channel_count": len(channel_top10),
        "event_cluster_count": len(event_clusters),
        "logic_chain_count": len(logic_chains),
        "trendradar_candidate_count": len(trendradar_candidates),
        "manual_topic_count": len(manual_topics),
    }

    return {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),
        "requested_topic_count": max(MIN_TOPIC_COUNT, min(candidate_count, MAX_TOPIC_COUNT)),
        "channel_top10": channel_top10,
        "event_clusters": event_clusters,
        "logic_chain_summaries": build_logic_chain_summaries(logic_chains),
        "secondary_distinct_signals": build_secondary_distinct_signals(logic_chains),
        "cross_channel_events": cross_channel_events,
        "trendradar_candidates": trendradar_candidates[:20],
        "top_entities": top_entities,
        "editorial_priority_pool": editorial_priority_pool,
        "trusted_evidence_pool": trusted_evidence_pool,
        "noise_pool": summarize_noise(records),
        "manual_topics": [{"title": item, "must_cover": True} for item in manual_topics],
        "editorial_rubric": {
            "sharpness": "题目是否真的提出了一个判断、误判或冲突，而不是复述新闻。",
            "evidence": "现有 intake 证据是否足以支撑写成稿件。",
            "structural_value": "能否从事件升级成更大的结构命题。",
            "reader_value": "读者看完后能得到什么判断框架。",
            "seriousness": "是否值得占用本轮 8-10 个编辑题位。",
        },
        "anti_patterns": [
            "不要把单条生活方式、消费维权、情绪口水仗直接抬成主榜题。",
            "不要输出政策问答式、百科问答式、空泛影响式标题。",
            "不要把一个事件拆成两个近义词命题占两个题位。",
        ],
        "notes": {
            "rule": "代码只负责证据编排、显性噪音剔除、结构校验与落盘；命题与题卡内容由 AI 生成。",
            "evidence_boundary": "所有题卡必须能回指 intake 证据池中的真实标题和真实链接。",
        },
        "stats": stats,
    }


def resolve_brief_ai_config() -> dict[str, str] | None:
    return resolve_chat_provider(
        custom_env_var="DASHENG_PHASE2_PROVIDER_ENV",
        base_url_keys=["PHASE2_AI_BASE_URL", "QHAIGC_BASE_URL"],
        api_key_keys=["PHASE2_AI_API_KEY", "QHAIGC_API_KEY"],
        model_keys=["PHASE2_AI_MODEL", "PHASE3_AI_MODEL", "DRAFT_AI_MODEL"],
        timeout_keys=["PHASE2_AI_TIMEOUT_SECONDS"],
        default_model="gpt-4.1-mini",
        default_timeout_seconds="90",
    )


def load_brief_prompt_bundle() -> dict[str, Any]:
    return {
        "brief_ai_prompt": read_text_if_exists(BRIEF_AI_PROMPT_PATH),
        "brief_card_schema": read_json_if_exists(BRIEF_AI_SCHEMA_PATH) or {},
    }


def strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def parse_json_object_from_text(text: str) -> dict[str, Any] | None:
    cleaned = strip_code_fence(text)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def request_ai_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    config = resolve_brief_ai_config()
    if not config:
        return None
    body = {
        "model": config["model"],
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    req = urllib_request.Request(
        config["base_url"],
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib_request.urlopen(req, timeout=float(config["timeout_seconds"])) as resp:
                response_payload = json.loads(resp.read().decode("utf-8"))
            content = extract_chat_content(response_payload)
            if not content:
                return None
            return parse_json_object_from_text(content)
        except (
            urllib_error.URLError,
            urllib_error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
            ValueError,
            http.client.RemoteDisconnected,
        ) as exc:
            last_error = exc
            if attempt >= 2:
                break
            time.sleep(2 * (attempt + 1))
    if last_error:
        return None
    return None


def build_brief_brainstorm_payload(signal_bundle: dict[str, Any], prompt_bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": "Pass A｜发散生成",
        "target_topic_count": signal_bundle["requested_topic_count"],
        "editorial_rules": {
            "must_use_intake_evidence": True,
            "may_synthesize_across_signals": True,
            "must_not_copy_raw_titles": True,
            "must_not_output_duplicate_topics": True,
        },
        "prompt_reference": prompt_bundle.get("brief_ai_prompt", ""),
        "signal_bundle": {
            "channel_top10": signal_bundle["channel_top10"],
            "editorial_priority_pool": signal_bundle["editorial_priority_pool"][:30],
            "logic_chain_summaries": signal_bundle["logic_chain_summaries"][:12],
            "secondary_distinct_signals": signal_bundle["secondary_distinct_signals"][:12],
            "cross_channel_events": signal_bundle["cross_channel_events"],
            "trendradar_candidates": signal_bundle["trendradar_candidates"],
            "top_entities": signal_bundle["top_entities"],
            "event_clusters": signal_bundle["event_clusters"][:24],
            "manual_topics": signal_bundle["manual_topics"],
            "trusted_evidence_pool": signal_bundle["trusted_evidence_pool"][:32],
            "noise_pool": signal_bundle["noise_pool"][:12],
        },
        "editorial_rubric": signal_bundle["editorial_rubric"],
        "anti_patterns": signal_bundle["anti_patterns"],
        "output_contract": {
            "root_key": "candidate_seeds",
            "fields": [
                "seed_id",
                "working_title",
                "core_judgment",
                "why_now",
                "source_basis",
                "distinct_signal",
                "priority",
            ],
        },
    }


def build_brief_cards_payload(signal_bundle: dict[str, Any], brainstorm: dict[str, Any], prompt_bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": "Pass B｜收敛成题卡",
        "target_topic_count": signal_bundle["requested_topic_count"],
        "editorial_rules": {
            "flat_cards_only": True,
            "topic_kind": "independent",
            "must_not_fabricate_evidence": True,
            "must_not_keep_near_duplicates": True,
            "must_not_lift_raw_titles": True,
            "max_same_logic_chain_share": 0.5,
        },
        "prompt_reference": prompt_bundle.get("brief_ai_prompt", ""),
        "schema": prompt_bundle.get("brief_card_schema", {}),
        "editorial_rubric": signal_bundle["editorial_rubric"],
        "anti_patterns": signal_bundle["anti_patterns"],
        "brainstorm": brainstorm,
        "signal_bundle": signal_bundle,
    }


def request_ai_brief_brainstorm(signal_bundle: dict[str, Any], prompt_bundle: dict[str, Any]) -> dict[str, Any] | None:
    payload = build_brief_brainstorm_payload(signal_bundle, prompt_bundle)
    system_prompt = (
        "你是资深编辑会里的主编。你要基于 intake 证据池，先发散提出一组值得继续讨论的命题候选。"
        "你可以跨渠道、跨事件、跨来源综合提炼，但不能脱离输入证据池臆造题目。"
        "优先抓真正有编辑价值的结构命题，而不是把资讯条目改写成问答题。"
        "输出必须是 JSON 对象，根键为 candidate_seeds。"
    )
    user_prompt = (
        "请像编辑选题会一样，先提出一批值得继续讨论的命题候选。"
        "不要写成采集标题复述，也不要写成模板腔。"
        "请优先使用 editorial_priority_pool 里的证据，它是本轮最值得深挖的主证据池；channel_top10 只是全局热度背景，不是主榜题的直接来源。"
        "优先选择那些能上升到宏观、地缘、产业链、技术落地、市场定价这类更大命题的方向。"
        "如果一个信号只是单条社会新闻、消费维权、地方政策小事、社交平台口水仗，除非它能清晰升级成更大的制度或市场命题，否则不要挤进主榜。"
        "同一命题不要换词重复。标题优先陈述式判断，不要大面积使用“是否/如何/影响”这类考试题口吻。"
        "好标题通常能看出“表面事件 / 真正主线”“短期催化 / 长期变量”“局部热闹 / 全局重估”这类关系。"
        "每个候选至少给出 working_title、core_judgment、why_now、source_basis、distinct_signal、priority。\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    return request_ai_json(system_prompt, user_prompt)


def request_ai_brief_cards(
    signal_bundle: dict[str, Any],
    brainstorm: dict[str, Any],
    prompt_bundle: dict[str, Any],
    feedback: str = "",
) -> dict[str, Any] | None:
    payload = build_brief_cards_payload(signal_bundle, brainstorm, prompt_bundle)
    system_prompt = (
        "你是第二阶段 Brief 的唯一内容生成层。"
        "代码只负责证据编排与结构校验，你负责生成最终候选题卡。"
        "请基于真实信号，输出 8-10 个独立候选题卡。"
        "题卡要像成熟编辑给编辑部的建议，不像研报标题，也不像百科问答。"
        "输出必须是 JSON 对象，根键为 topic_cards。"
    )
    user_prompt = (
        "请基于 intake 证据池和发散候选，收敛成最终的独立题卡。"
        "要求："
        "1）每题必须体现判断关系、错判关系、因果链条或重估关系，而不是空泛的“分析/影响/变化”；"
        "2）可以综合多个信号，但关键来源必须来自证据池；"
        "3）不同题之间不能是近义词换壳；"
        "4）不要把采集标题原样抬升成编辑题；"
        "5）手动指定题如果存在，必须在最终题卡中被覆盖；"
        "6）不要返回母题/变体结构，全部是平铺独立题卡；"
        "7）标题优先使用有判断力的陈述句，少用“是否/如何”问句；"
        "8）不要把单条弱信号包装成大题，宁可让更强的宏观、时政、产业或市场命题进入最终榜单；"
        "9）优先使用 editorial_priority_pool 作为主要证据来源；"
        "10）标题尽量短，尽量一眼看出逻辑关系，少用“加剧、彰显、推动、反映”这种空泛官样词；"
        "11）同一逻辑链的题不能超过总题数的一半，若出现主链过多，必须主动回补其它高价值链条。"
        "如果你输出了消费琐事、社交口水仗、弱相关生活方式话题，就说明你没有正确理解这一阶段。\n\n"
        f"{feedback + chr(10) if feedback else ''}{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    return request_ai_json(system_prompt, user_prompt)


def best_overlap_score(a: str, b: str) -> float:
    tokens_a = {token.lower() for token in meaningful_tokens(a)}
    tokens_b = {token.lower() for token in meaningful_tokens(b)}
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / max(len(tokens_a), 1)


def select_supporting_evidence(card: dict[str, Any], evidence_pool: list[dict[str, Any]], limit: int = 4) -> list[dict[str, Any]]:
    probe_text = " ".join(
        [
            card.get("title", ""),
            card.get("core_proposition", ""),
            " ".join(card.get("priority_people", [])),
            " ".join(card.get("priority_orgs", [])),
            " ".join(card.get("priority_news_queries", [])),
        ]
    )
    scored: list[tuple[float, dict[str, Any]]] = []
    for item in evidence_pool:
        evidence_text = " ".join(
            [
                item.get("title", ""),
                item.get("note", ""),
                " ".join(item.get("entities", [])),
            ]
        )
        overlap = best_overlap_score(probe_text, evidence_text)
        bonus = 0.12 if item.get("trendradar_signal") else 0.0
        bonus += 0.1 if item.get("source_tier") in {"official", "mainstream_media"} else 0.0
        score = overlap + bonus + min(float(item.get("signal_score") or 0.0) / 20.0, 0.6)
        if score > 0.12:
            scored.append((score, item))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for _, item in scored:
        key = canonicalize_url(item.get("url", "")) or normalize_text(item.get("title", ""))
        if key in seen:
            continue
        seen.add(key)
        selected.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source_type": item.get("source_type", ""),
                "source_tier": item.get("source_tier", ""),
                "note": item.get("note", ""),
                "logic_chain_id": item.get("logic_chain_id", "misc"),
            }
        )
        if len(selected) >= limit:
            break
    return selected


def build_evidence_lookup(evidence_pool: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_url: dict[str, dict[str, Any]] = {}
    by_title: dict[str, dict[str, Any]] = {}
    for item in evidence_pool:
        url_key = canonicalize_url(item.get("url", ""))
        title_key = normalize_text(item.get("title", ""))
        if url_key and url_key not in by_url:
            by_url[url_key] = item
        if title_key and title_key not in by_title:
            by_title[title_key] = item
    return by_url, by_title


def match_evidence_item(
    raw_item: dict[str, Any],
    evidence_lookup: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]],
    evidence_pool: list[dict[str, Any]],
) -> dict[str, Any] | None:
    by_url, by_title = evidence_lookup
    url_key = canonicalize_url(str(raw_item.get("url") or "").strip())
    title = str(raw_item.get("title") or "").strip()
    title_key = normalize_text(title)
    if url_key and url_key in by_url:
        return by_url[url_key]
    if title_key and title_key in by_title:
        return by_title[title_key]
    if not title:
        return None

    best_match: dict[str, Any] | None = None
    best_score = 0.0
    for item in evidence_pool:
        score = max(
            best_overlap_score(title, item.get("title", "")),
            best_overlap_score(title, item.get("note", "")),
        )
        if score > best_score:
            best_score = score
            best_match = item
    return best_match if best_score >= 0.55 else None


def enrich_existing_evidence(
    raw_items: list[dict[str, Any]],
    card: dict[str, Any],
    evidence_pool: list[dict[str, Any]],
    limit: int = 4,
) -> list[dict[str, Any]]:
    evidence_lookup = build_evidence_lookup(evidence_pool)
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw_item in raw_items[:limit]:
        if not isinstance(raw_item, dict):
            continue
        matched = match_evidence_item(raw_item, evidence_lookup, evidence_pool)
        title = str(raw_item.get("title") or matched.get("title") if matched else "").strip()
        url = str(raw_item.get("url") or matched.get("url") if matched else "").strip()
        if not title and not url:
            continue
        key = canonicalize_url(url) or normalize_text(title)
        if not key or key in seen:
            continue
        seen.add(key)
        merged = {
            "title": title or (matched.get("title", "") if matched else ""),
            "url": url or (matched.get("url", "") if matched else ""),
            "source_type": str(raw_item.get("source_type") or (matched.get("source_type", "") if matched else "")),
            "source_tier": str(raw_item.get("source_tier") or (matched.get("source_tier", "") if matched else "")),
            "note": str(raw_item.get("note") or (matched.get("note", "") if matched else "")),
            "logic_chain_id": str(raw_item.get("logic_chain_id") or (matched.get("logic_chain_id", "misc") if matched else "misc")),
        }
        if matched and matched.get("signal_score") is not None:
            merged["signal_score"] = matched.get("signal_score")
        selected.append(merged)

    if len(selected) < limit:
        preferred_chain = ""
        for item in selected:
            chain_id = str(item.get("logic_chain_id") or "").strip()
            if chain_id and chain_id != "misc":
                preferred_chain = chain_id
                break
        fallback = select_supporting_evidence(card, evidence_pool, limit=limit)
        for item in fallback:
            if preferred_chain and str(item.get("logic_chain_id") or "").strip() not in {"", "misc", preferred_chain}:
                continue
            key = canonicalize_url(item.get("url", "")) or normalize_text(item.get("title", ""))
            if not key or key in seen:
                continue
            seen.add(key)
            selected.append(item)
            if len(selected) >= limit:
                break

    return selected[:limit]


def normalize_list(value: Any, limit: int, fallback: list[str] | None = None) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        if items:
            return items[:limit]
    return (fallback or [])[:limit]


def normalize_structure_hint(value: Any, title: str) -> dict[str, str]:
    hint = value if isinstance(value, dict) else {}
    normalized = {}
    for key in STRUCTURE_KEYS:
        content = hint.get(key)
        if isinstance(content, str) and content.strip():
            normalized[key] = content.strip()
    if normalized:
        return normalized
    return {
        "opening": f"开头先把《{title}》真正要判断的误判点抛出来。",
        "part_1": "先交代触发这题的真实事件与信号，不复述噪音。",
        "part_2": "再拆开核心变量，说明真正变化的链条。",
        "part_3": "给出证据缺口与下一步该补的数据或图。",
        "ending": "收束到读者最该记住的判断框架。",
    }


def normalize_card_title(title: str) -> str:
    value = re.sub(r"\s+", " ", str(title or "")).strip()
    value = re.sub(r"^(分析|剖析|关注|观察)[:：]?", "", value).strip()
    return value


def ensure_manual_topics_covered(cards: list[dict[str, Any]], manual_topics: list[str]) -> tuple[bool, str]:
    for manual_topic in manual_topics:
        covered = False
        for card in cards:
            overlap = max(
                best_overlap_score(manual_topic, card.get("title", "")),
                best_overlap_score(manual_topic, card.get("core_proposition", "")),
            )
            if overlap >= 0.25:
                covered = True
                break
        if not covered:
            return False, f"手动指定题未被覆盖：{manual_topic}"
    return True, ""


def infer_card_logic_chain_id(card: dict[str, Any], signal_bundle: dict[str, Any]) -> str:
    evidence_chain_counts: Counter[str] = Counter()
    for item in card.get("existing_evidence", []):
        chain_id = str(item.get("logic_chain_id") or "").strip()
        if chain_id and chain_id != "misc":
            evidence_chain_counts[chain_id] += 1
    if evidence_chain_counts:
        return evidence_chain_counts.most_common(1)[0][0]
    probe = " ".join(
        [
            card.get("title", ""),
            card.get("core_proposition", ""),
            card.get("one_line_judgment", ""),
            " ".join(card.get("priority_people", [])),
            " ".join(card.get("priority_orgs", [])),
        ]
    )
    best_chain = "misc"
    best_score = 0.0
    for chain in signal_bundle.get("logic_chain_summaries", []):
        chain_probe = " ".join(chain.get("dominant_tokens", []) + chain.get("top_entities", []) + chain.get("top_titles", []))
        score = best_overlap_score(probe, chain_probe)
        if score > best_score:
            best_score = score
            best_chain = chain.get("chain_id", "misc")
    return best_chain if best_score >= 0.18 else "misc"


def validate_logic_chain_balance(cards: list[dict[str, Any]], signal_bundle: dict[str, Any]) -> tuple[bool, str]:
    chain_counts: Counter[str] = Counter()
    for card in cards:
        chain_id = infer_card_logic_chain_id(card, signal_bundle)
        card["logic_chain_id"] = chain_id
        chain_counts[chain_id] += 1
    if not chain_counts:
        return True, ""
    dominant_chain, dominant_count = chain_counts.most_common(1)[0]
    if dominant_chain != "misc" and dominant_count > max(1, len(cards) // 2):
        return False, f"同一逻辑链 {dominant_chain} 题目过多：{dominant_count}/{len(cards)}"
    return True, ""


def normalize_ai_brief_cards(
    ai_result: dict[str, Any] | None,
    signal_bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    if not ai_result or not isinstance(ai_result.get("topic_cards"), list):
        raise RuntimeError("AI 未返回合法的 topic_cards 数组")

    evidence_pool = []
    seen_evidence_keys: set[str] = set()
    for pool_name in ("editorial_priority_pool", "trusted_evidence_pool"):
        for item in signal_bundle.get(pool_name, []):
            key = canonicalize_url(item.get("url", "")) or normalize_text(item.get("title", ""))
            if key in seen_evidence_keys:
                continue
            seen_evidence_keys.add(key)
            evidence_pool.append(item)
    normalized_cards: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    seen_props: set[str] = set()

    for index, raw in enumerate(ai_result["topic_cards"], start=1):
        if not isinstance(raw, dict):
            continue
        title = normalize_card_title(str(raw.get("title") or ""))
        core_proposition = str(raw.get("core_proposition") or "").strip()
        one_line_judgment = str(raw.get("one_line_judgment") or "").strip()
        why_now = str(raw.get("why_now") or "").strip()
        reader_payoff = str(raw.get("reader_payoff") or "").strip()
        distinctiveness_reason = str(raw.get("distinctiveness_reason") or "").strip()
        evidence_gap_summary = str(raw.get("evidence_gap_summary") or "").strip()
        article_use = str(raw.get("article_use") or "").strip() or "判断稿"
        if not all([title, core_proposition, one_line_judgment, why_now, reader_payoff, distinctiveness_reason, evidence_gap_summary]):
            continue

        title_key = normalize_text(title)
        prop_key = normalize_text(core_proposition)
        if title_key in seen_titles or prop_key in seen_props:
            continue
        seen_titles.add(title_key)
        seen_props.add(prop_key)

        card = {
            "topic_id": str(raw.get("topic_id") or f"topic-{slugify(title)[:48]}"),
            "mother_topic_id": None,
            "topic_kind": "independent",
            "angle_variant_of": None,
            "title": title,
            "one_line_judgment": one_line_judgment,
            "core_proposition": core_proposition,
            "why_now": why_now,
            "reader_payoff": reader_payoff,
            "article_use": article_use,
            "distinctiveness_reason": distinctiveness_reason,
            "evidence_gap_summary": evidence_gap_summary,
            "proof_requirements": normalize_list(raw.get("proof_requirements"), 5),
            "recommended_data_angles": normalize_list(raw.get("recommended_data_angles"), 5),
            "recommended_visual_angles": normalize_list(raw.get("recommended_visual_angles"), 6),
            "priority_people": normalize_list(raw.get("priority_people"), 6),
            "priority_orgs": normalize_list(raw.get("priority_orgs"), 6),
            "priority_news_queries": normalize_list(raw.get("priority_news_queries"), 6),
            "existing_evidence": [],
            "structure_hint": normalize_structure_hint(raw.get("structure_hint"), title),
        }
        card["mother_topic_id"] = card["topic_id"]
        evidence_items: list[dict[str, Any]] = []
        if isinstance(raw.get("existing_evidence"), list):
            evidence_items = enrich_existing_evidence(raw["existing_evidence"], card, evidence_pool, limit=4)
        if not evidence_items:
            evidence_items = select_supporting_evidence(card, evidence_pool, limit=4)
        card["existing_evidence"] = evidence_items
        normalized_cards.append(card)

    normalized_cards = normalized_cards[: signal_bundle["requested_topic_count"]]
    if len(normalized_cards) < MIN_TOPIC_COUNT:
        raise RuntimeError(f"AI 返回有效题卡不足：{len(normalized_cards)}")

    ok, reason = ensure_manual_topics_covered(normalized_cards, [item["title"] for item in signal_bundle["manual_topics"]])
    if not ok:
        raise RuntimeError(reason)

    return normalized_cards


def write_editor_brief(output_dir: Path, run_id: str, intake_file: Path, cards: list[dict[str, Any]], generation_mode: str) -> Path:
    lines = [
        "# 第二环节 编辑 Brief 库",
        "",
        f"- 运行批次：`{run_id}`",
        f"- 输入文件：`{intake_file.resolve()}`",
        f"- 生成模式：`{generation_mode}`",
        f"- 候选题数：`{len(cards)}`",
        "",
        "## 使用说明",
        "",
        "- 本轮候选题全部由 AI 基于 intake 证据池综合提炼生成。",
        "- 代码只做输入装配、显性噪音隔离、结构校验和落盘，不再使用规则模板硬造题。",
        "- 下游只需基于这些独立题卡做人工选题，不需要再先删一轮近义词换壳题。",
        "",
    ]
    for index, card in enumerate(cards, start=1):
        lines.extend(
            [
                f"## 题目 {index}",
                "",
                f"- 选题名：`{card['title']}`",
                f"- 类型：`{card['topic_kind']}`",
                f"- 一句话判断：{card['one_line_judgment']}",
                f"- 核心命题：{card['core_proposition']}",
                f"- 为什么现在值得写：{card['why_now']}",
                f"- 读者收益：{card['reader_payoff']}",
                f"- 文章用途：{card['article_use']}",
                f"- 不重复理由：{card['distinctiveness_reason']}",
                f"- 证据缺口：{card['evidence_gap_summary']}",
                "- 证明它成立需要：",
            ]
        )
        for item in card["proof_requirements"]:
            lines.append(f"  - {item}")
        lines.append("- 推荐数据角度：")
        for item in card["recommended_data_angles"]:
            lines.append(f"  - {item}")
        lines.append("- 推荐图片 / 视频方向：")
        for item in card["recommended_visual_angles"]:
            lines.append(f"  - {item}")
        lines.append("- 优先人物 / 机构 / 搜索：")
        lines.append(f"  - 人物：{', '.join(card['priority_people']) or '无'}")
        lines.append(f"  - 机构：{', '.join(card['priority_orgs']) or '无'}")
        for item in card["priority_news_queries"]:
            lines.append(f"  - 搜索：{item}")
        lines.append("- 关键来源：")
        for item in card["existing_evidence"]:
            lines.append(f"  - {item['title']}｜{item['url']}")
        lines.append("- 结构提示：")
        lines.append(f"  - 开头：{card['structure_hint']['opening']}")
        lines.append(f"  - 第一段：{card['structure_hint']['part_1']}")
        lines.append(f"  - 第二段：{card['structure_hint']['part_2']}")
        lines.append(f"  - 第三段：{card['structure_hint']['part_3']}")
        lines.append(f"  - 结尾：{card['structure_hint']['ending']}")
        lines.append("")
    target = output_dir / "02_编辑Brief库.md"
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return target


def write_research_brief(output_dir: Path, run_id: str, cards: list[dict[str, Any]]) -> Path:
    lines = [
        "# 第二环节 研究 Brief 库",
        "",
        f"- 运行批次：`{run_id}`",
        "",
    ]
    for index, card in enumerate(cards, start=1):
        lines.extend(
            [
                f"## 研究任务 {index}｜{card['title']}",
                "",
                f"- topic_id：`{card['topic_id']}`",
                f"- 核心命题：{card['core_proposition']}",
                f"- 一句话判断：{card['one_line_judgment']}",
                f"- 为什么现在值得写：{card['why_now']}",
                f"- 读者收益：{card['reader_payoff']}",
                f"- 证据缺口总述：{card['evidence_gap_summary']}",
                "- 研究优先顺序：",
            ]
        )
        for item in card["proof_requirements"]:
            lines.append(f"  - {item}")
        lines.append("- 数据图优先方向：")
        for item in card["recommended_data_angles"]:
            lines.append(f"  - {item}")
        lines.append("- 图片 / 视频优先方向：")
        for item in card["recommended_visual_angles"]:
            lines.append(f"  - {item}")
        lines.append("- 建议先搜的人物 / 机构 / 新闻页：")
        lines.append(f"  - 人物：{', '.join(card['priority_people']) or '无'}")
        lines.append(f"  - 机构：{', '.join(card['priority_orgs']) or '无'}")
        for item in card["priority_news_queries"]:
            lines.append(f"  - 搜索：{item}")
        lines.append("- 当前关键来源：")
        for item in card["existing_evidence"]:
            lines.append(f"  - {item['title']}｜{item['source_tier']}｜{item['url']}")
        lines.append("")
    target = output_dir / "02_研究Brief库.md"
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return target


def write_report(
    output_dir: Path,
    run_id: str,
    intake_file: Path,
    cards: list[dict[str, Any]],
    signal_bundle: dict[str, Any],
    generation_mode: str,
) -> Path:
    lines = [
        "# 第二环节 编辑 Brief 报告",
        "",
        f"- 运行批次：`{run_id}`",
        f"- 输入文件：`{intake_file.resolve()}`",
        f"- 生成模式：`{generation_mode}`",
        f"- 原始样本数：`{signal_bundle['stats']['raw_record_count']}`",
        f"- 去重后样本数：`{signal_bundle['stats']['deduped_record_count']}`",
        f"- 可信证据池：`{signal_bundle['stats']['trusted_evidence_count']}`",
        f"- 逻辑链数：`{signal_bundle['stats']['logic_chain_count']}`",
        f"- 候选题数：`{len(cards)}`",
        "",
        "## 本轮口径",
        "",
        "- 第二阶段改为 AI 原生生成：题卡内容由 AI 直接生成，代码只做接口与交付。",
        "- intake 的事件簇只作为证据归纳参考，不再强制决定题名。",
        "- 候选题是平铺独立题卡，不再强制母题 / 变体结构。",
        "- 同一逻辑链只做弱去重，不做题材配额，但会避免单链路占满榜单。",
        "",
        "## 渠道横截面",
        "",
    ]
    for channel, items in signal_bundle["channel_top10"].items():
        lines.append(f"- `{channel}`：Top10 `{len(items)}` 条")
    lines.extend(
        [
            "",
            "## AI 交付检查",
            "",
            f"- 手动指定题数：`{signal_bundle['stats']['manual_topic_count']}`",
            f"- TrendRadar 候选数：`{signal_bundle['stats']['trendradar_candidate_count']}`",
            f"- 动态事件簇参考数：`{signal_bundle['stats']['event_cluster_count']}`",
            "",
            "## 候选题一览",
            "",
        ]
    )
    for index, card in enumerate(cards, start=1):
        lines.append(f"- {index}. `{card['title']}`｜{card['article_use']}｜{card['one_line_judgment']}")
    target = output_dir / "02_编辑Brief_报告.md"
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return target


def write_selected_topics_files(output_dir: Path, run_id: str, cards: list[dict[str, Any]]) -> tuple[Path, Path]:
    # 为每个topic调用wechat-topic-outline-planner生成AI大纲
    enriched_candidates = []
    for card in cards:
        candidate = {
            "topic_id": card["topic_id"],
            "title": card["title"],
            "topic_kind": card["topic_kind"],
            "mother_topic_id": card["topic_id"],
            "angle_variant_of": None,
            "article_use": card["article_use"],
            "core_proposition": card["core_proposition"],
            "one_line_judgment": card["one_line_judgment"],
        }

        # 尝试生成AI大纲（非阻塞，失败不影响主流程）
        try:
            from skill_invoker import invoke_skill
            outline_result = invoke_skill(
                "wechat-topic-outline-planner",
                {
                    "topic_card": {
                        "title": card["title"],
                        "core_proposition": card["core_proposition"],
                        "article_use": card["article_use"],
                    },
                    "style": "wechat_article",
                    "sections": 3,  # 严格限制3-4个H2
                }
            )

            if outline_result.get("success"):
                candidate["ai_outline"] = outline_result.get("outline", "")
                candidate["structure_hint"] = outline_result.get("structure_template", "PCIS")
        except Exception:
            # outline生成失败不影响主流程
            pass

        enriched_candidates.append(candidate)

    template = {
        "run_id": run_id,
        "gate": "Brief Gate",
        "status": "pending_editor_review",
        "instructions": [
            "从 candidate_topics 中选择进入 draft 的题目。",
            "没有 selected_topics 或未批准状态，不允许进入下游阶段。",
        ],
        "selected_topics": [],
        "rejected_topic_ids": [],
        "candidate_topics": enriched_candidates,
        "editor_note": "",
    }
    template_path = output_dir / "selected_topics.template.json"
    selected_path = output_dir / "selected_topics.json"
    template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    if not selected_path.exists():
        selected_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    return template_path, selected_path


def write_legacy_files(
    output_dir: Path,
    run_id: str,
    cards: list[dict[str, Any]],
    signal_bundle: dict[str, Any],
    brief_file: Path,
    top_n: int,
) -> None:
    clusters = signal_bundle["event_clusters"]
    summary_payload = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),
        "stats": {
            "input_records": signal_bundle["stats"]["raw_record_count"],
            "cluster_count": len(clusters),
            "topic_card_count": len(cards),
        },
        "clusters": clusters[:40],
    }
    topic_index = [
        {
            "rank": index,
            "topic_id": card["topic_id"],
            "topic_name": card["title"],
            "topic_kind": card["topic_kind"],
            "mother_topic_id": card["topic_id"],
            "source_status": "ai_generated",
        }
        for index, card in enumerate(cards, start=1)
    ]
    topn = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),
        "count": min(top_n, len(cards)),
        "items": topic_index[:top_n],
    }
    (output_dir / "phase2-clusters-summary.json").write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "phase2-topic-index.json").write_text(json.dumps(topic_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "phase2-editorial-briefs.json").write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "phase2-topn-for-confirmation.json").write_text(json.dumps(topn, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "phase2-brief-library.md").write_text(brief_file.read_text(encoding="utf-8"), encoding="utf-8")


def write_manifest(
    output_dir: Path,
    run_id: str,
    intake_file: Path,
    cards: list[dict[str, Any]],
    generation_mode: str,
    status: str,
    failure_reason: str | None,
    artifacts: list[Path],
) -> Path:
    manifest = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),
        "stage": "brief",
        "status": status,
        "generation_mode": generation_mode,
        "failure_reason": failure_reason,
        "input_file": str(intake_file.resolve()),
        "output_dir": str(output_dir.resolve()),
        "candidate_count": len(cards),
        "candidate_topics": [card.get("title", "") for card in cards],
        "recommended_top_ids": [card.get("topic_id") for card in cards[:3]],
        "artifacts": [str(path.resolve()) for path in artifacts],
        "next_stage": "draft" if status == "ready" else None,
    }
    target = output_dir / "brief_manifest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def write_failure_manifest(output_dir: Path, run_id: str, intake_file: Path, failure_reason: str) -> Path:
    return write_manifest(
        output_dir=output_dir,
        run_id=run_id,
        intake_file=intake_file,
        cards=[],
        generation_mode="ai_only",
        status="failed",
        failure_reason=failure_reason,
        artifacts=[],
    )


def run_ai_brief_pipeline(
    run_id: str,
    records: list[IntakeRecord],
    aux: dict[str, Any],
    manual_topics: list[str],
    candidate_count: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    signal_bundle = build_brief_signal_bundle(run_id, records, aux, manual_topics, candidate_count)
    prompt_bundle = load_brief_prompt_bundle()
    brainstorm = request_ai_brief_brainstorm(signal_bundle, prompt_bundle)
    if not brainstorm or not isinstance(brainstorm.get("candidate_seeds"), list):
        raise RuntimeError("Pass A 发散生成失败")
    ai_result = request_ai_brief_cards(signal_bundle, brainstorm, prompt_bundle)
    cards = normalize_ai_brief_cards(ai_result, signal_bundle)
    balanced, reason = validate_logic_chain_balance(cards, signal_bundle)
    if not balanced:
        feedback = (
            f"上一轮结果未通过逻辑链平衡校验：{reason}。"
            "请保留最强主线，但必须主动回补其它高价值逻辑链，避免同一家族题目占满榜单。"
        )
        ai_result = request_ai_brief_cards(signal_bundle, brainstorm, prompt_bundle, feedback=feedback)
        cards = normalize_ai_brief_cards(ai_result, signal_bundle)
        balanced, reason = validate_logic_chain_balance(cards, signal_bundle)
        if not balanced:
            raise RuntimeError(reason)
    return cards, signal_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild Stage 2 brief artifacts from intake records")
    parser.add_argument("input_file", help="Path to intake_records.json")
    parser.add_argument("output_dir", help="Output directory for stage2 artifacts")
    parser.add_argument("--run-id")
    parser.add_argument("--manual-topic", action="append", default=[], help="Force a manual topic into the brief pool")
    parser.add_argument("--candidate-count", type=int, default=DEFAULT_CANDIDATE_COUNT, help="Number of topic cards to request")
    parser.add_argument("--topic-spec-file")
    parser.add_argument("--min-count")
    parser.add_argument("--max-clusters")
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--upstream-ref")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    intake_file = Path(args.input_file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    records = load_records(intake_file)
    if not records:
        raise RuntimeError(f"未从 {intake_file} 读取到有效 intake records")

    run_id = infer_run_id(records, args.run_id, intake_file)
    aux = collect_auxiliary(intake_file)

    try:
        cards, signal_bundle = run_ai_brief_pipeline(
            run_id=run_id,
            records=records,
            aux=aux,
            manual_topics=args.manual_topic,
            candidate_count=max(MIN_TOPIC_COUNT, min(args.candidate_count, MAX_TOPIC_COUNT)),
        )
        topic_cards_file = output_dir / "topic_cards.json"
        topic_cards_file.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
        brief_file = write_editor_brief(output_dir, run_id, intake_file, cards, "ai_only")
        research_file = write_research_brief(output_dir, run_id, cards)
        report_file = write_report(output_dir, run_id, intake_file, cards, signal_bundle, "ai_only")
        template_file, selected_file = write_selected_topics_files(output_dir, run_id, cards)
        write_legacy_files(output_dir, run_id, cards, signal_bundle, brief_file, max(args.top_n, 1))
        manifest_file = write_manifest(
            output_dir=output_dir,
            run_id=run_id,
            intake_file=intake_file,
            cards=cards,
            generation_mode="ai_only",
            status="ready",
            failure_reason=None,
            artifacts=[
                brief_file,
                research_file,
                report_file,
                topic_cards_file,
                template_file,
                selected_file,
                output_dir / "phase2-clusters-summary.json",
                output_dir / "phase2-topic-index.json",
                output_dir / "phase2-editorial-briefs.json",
                output_dir / "phase2-topn-for-confirmation.json",
            ],
        )
        sync_brief_to_desktop(run_id, output_dir)
    except Exception as exc:
        manifest_file = write_failure_manifest(output_dir, run_id, intake_file, str(exc))
        raise RuntimeError(str(exc)) from exc

    print(
        json.dumps(
            {
                "run_id": run_id,
                "input_file": str(intake_file),
                "output_dir": str(output_dir),
                "brief_file": str(brief_file),
                "research_file": str(research_file),
                "report_file": str(report_file),
                "manifest_file": str(manifest_file),
                "candidate_count": len(cards),
                "generation_mode": "ai_only",
                "manual_topics": args.manual_topic,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
