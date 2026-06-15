#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


WIDTH = 1080
HEIGHT = 1920
NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?%?")
DEFAULT_HTML_VIDEO_ROOT = Path("/Volumes/PSSD/html-video")
MOTION_RUNTIME_MODE = "auto"
MOTION_LIB_CACHE: dict[str, str | None] = {}


def clean_text(text: Any) -> str:
    value = html.unescape(str(text or ""))
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def html_video_root() -> Path:
    return Path(os.environ.get("HTML_VIDEO_ROOT", str(DEFAULT_HTML_VIDEO_ROOT))).expanduser().resolve()


def find_first(root: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(root.glob(pattern))
        if matches:
            return matches[0]
    return None


def read_motion_lib(name: str) -> str | None:
    if name in MOTION_LIB_CACHE:
        return MOTION_LIB_CACHE[name]
    root = html_video_root()
    if name == "gsap":
        path = find_first(root, ["node_modules/**/gsap/dist/gsap.min.js"])
    elif name == "lottie":
        path = find_first(root, ["node_modules/**/lottie-web/build/player/lottie_light.min.js", "node_modules/**/lottie-web/build/player/lottie.min.js"])
    else:
        path = None
    if path and path.exists():
        MOTION_LIB_CACHE[name] = path.read_text(encoding="utf-8", errors="ignore")
    else:
        MOTION_LIB_CACHE[name] = None
    return MOTION_LIB_CACHE[name]


def esc(text: Any) -> str:
    return html.escape(clean_text(text), quote=True)


def short(text: Any, limit: int) -> str:
    value = clean_text(text)
    return value if len(value) <= limit else value[: limit - 1] + "…"


def split_units(text: str, limit: int = 6) -> list[str]:
    parts = [item.strip() for item in re.split(r"[。；;，,、\n]+", clean_text(text)) if item.strip()]
    if not parts:
        parts = [clean_text(text)]
    return [short(item, 28) for item in parts[:limit]]


def table_from_variables(scene: dict[str, Any]) -> list[list[str]]:
    variables = scene.get("variables") or {}
    table = variables.get("table") or variables.get("rows") or []
    if not isinstance(table, list):
        return []
    out: list[list[str]] = []
    for row in table[:8]:
        if isinstance(row, list):
            out.append([clean_text(cell) for cell in row[:4]])
    return out


def numbers_from_scene(scene: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    text = " ".join([clean_text(scene.get("title")), clean_text(scene.get("narration"))])
    rows = []
    for idx, match in enumerate(NUMBER_RE.findall(text)[:limit], 1):
        raw = match.replace("%", "")
        try:
            value = float(raw)
        except ValueError:
            value = float(idx * 10)
        rows.append({"label": f"指标 {idx}", "display": match, "value": value})
    if rows:
        return rows
    fallback = [18, 32, 45, 61, 53]
    return [{"label": f"T+{idx}", "display": str(value), "value": value} for idx, value in enumerate(fallback, 1)]


def chart_rows(scene: dict[str, Any]) -> list[dict[str, Any]]:
    variables = scene.get("variables") or {}
    metrics = variables.get("metrics") or []
    if isinstance(metrics, list):
        rows = []
        for idx, item in enumerate(metrics[:6], 1):
            if not isinstance(item, dict):
                continue
            label = item.get("label") or f"指标 {idx}"
            display = item.get("display") or item.get("value") or ""
            found = NUMBER_RE.search(str(display).replace(",", ""))
            if found:
                try:
                    value = float(found.group(0).replace("%", ""))
                except ValueError:
                    value = float(idx * 10)
            else:
                value = float(idx * 8)
            rows.append({"label": short(label, 9), "display": short(display, 12), "value": value})
        if rows:
            return rows
    table = table_from_variables(scene)
    rows = []
    for idx, row in enumerate(table[1:7] if len(table) > 1 else table[:6], 1):
        label = row[0] if row else f"指标 {idx}"
        value_text = row[1] if len(row) > 1 else ""
        found = NUMBER_RE.search(value_text.replace(",", ""))
        if found:
            try:
                value = float(found.group(0).replace("%", ""))
            except ValueError:
                value = float(idx * 10)
        else:
            value = float(idx * 8)
        rows.append({"label": short(label, 9), "display": short(value_text or str(value), 12), "value": value})
    return rows or numbers_from_scene(scene)


def motion_policy(scene: dict[str, Any]) -> dict[str, Any]:
    policy = scene.get("motion_policy") or {}
    if not isinstance(policy, dict):
        policy = {}
    return {
        "framework": policy.get("framework", "hyperframes"),
        "animation": policy.get("animation", "gsap_fade_rise"),
        "lottie_allowed": bool(policy.get("lottie_allowed", True)),
        "lottie_required": bool(policy.get("lottie_required", False)),
        "lottie_role": policy.get("lottie_role", "optional_ambient"),
        "lottie_keywords": policy.get("lottie_keywords", ["abstract", "motion graphics"]),
        "fact_rule": policy.get("fact_rule", "Lottie is decorative only; facts come from article variables."),
    }


def motion_meta(scene: dict[str, Any]) -> str:
    return html.escape(json.dumps(motion_policy(scene), ensure_ascii=False), quote=True)


def director_meta(scene: dict[str, Any]) -> dict[str, Any]:
    return {
        "beat_class": scene.get("beat_class") or "claim",
        "director_state": scene.get("director_state") or "question_setup",
        "transition_to_next": scene.get("transition_to_next") or "hard_cut",
        "driver_score": scene.get("driver_score"),
        "audio": scene.get("audio") or {},
    }


def director_meta_attr(scene: dict[str, Any]) -> str:
    return html.escape(json.dumps(director_meta(scene), ensure_ascii=False), quote=True)


def director_body_class(scene: dict[str, Any]) -> str:
    state = re.sub(r"[^0-9A-Za-z_-]+", "-", str(scene.get("director_state") or "question_setup"))
    transition = re.sub(r"[^0-9A-Za-z_-]+", "-", str(scene.get("transition_to_next") or "hard_cut"))
    beat = re.sub(r"[^0-9A-Za-z_-]+", "-", str(scene.get("beat_class") or "claim"))
    return f"state-{state} transition-{transition} beat-{beat}"


def motion_layer(scene: dict[str, Any]) -> str:
    policy = motion_policy(scene)
    return f"""
<div id="lottie-accent" class="motion-accent" data-lottie-role="{esc(policy['lottie_role'])}" aria-hidden="true">
</div>
"""


def lottie_color_for_scene(scene: dict[str, Any]) -> list[float]:
    part = str(scene.get("content_part") or "")
    if part in {"warning_or_risk", "opening_hook"}:
        return [0.92, 0.18, 0.12, 1]
    if part in {"data_chart", "financial_chart", "data_table", "kpi_card"}:
        return [0.1, 0.37, 0.55, 1]
    if part in {"article_title", "chapter_divider", "closing_outro", "brand_mark"}:
        return [0.85, 0.67, 0.33, 1]
    return [0.38, 0.68, 0.56, 1]


def lottie_data_for_scene(scene: dict[str, Any]) -> dict[str, Any]:
    color = lottie_color_for_scene(scene)
    part = str(scene.get("content_part") or "")
    role = motion_policy(scene)["lottie_role"]
    # Minimal valid Lottie shape animation generated from the scene role. This
    # gives lottie-web a real asset now; later an asset search step can replace it.
    if part in {"data_chart", "financial_chart", "data_table"}:
        shapes = [
            {
                "ty": "rc",
                "s": {"a": 0, "k": [18 + i * 8, 70 + i * 18]},
                "p": {"a": 0, "k": [-64 + i * 44, 0]},
                "r": {"a": 0, "k": 6},
            }
            for i in range(4)
        ]
    else:
        shapes = [
            {
                "ty": "el",
                "s": {"a": 1, "k": [{"t": 0, "s": [80, 80]}, {"t": 45, "s": [124, 124]}, {"t": 90, "s": [80, 80]}]},
                "p": {"a": 0, "k": [0, 0]},
            }
        ]
    return {
        "v": "5.13.0",
        "fr": 30,
        "ip": 0,
        "op": 90,
        "w": 240,
        "h": 240,
        "nm": role,
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": role,
                "sr": 1,
                "ks": {
                    "o": {"a": 0, "k": 72},
                    "r": {"a": 1, "k": [{"t": 0, "s": [0]}, {"t": 90, "s": [360]}]},
                    "p": {"a": 0, "k": [120, 120, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]},
                },
                "ao": 0,
                "shapes": [
                    {"ty": "gr", "it": shapes + [{"ty": "fl", "c": {"a": 0, "k": color}, "o": {"a": 0, "k": 100}}, {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}]},
                ],
                "ip": 0,
                "op": 90,
                "st": 0,
                "bm": 0,
            }
        ],
    }


def inline_real_motion_libs() -> str:
    if MOTION_RUNTIME_MODE == "lite":
        return ""
    chunks = []
    gsap_code = read_motion_lib("gsap")
    lottie_code = read_motion_lib("lottie")
    if gsap_code:
        chunks.append(f"<script data-motion-lib=\"gsap\">{gsap_code}</script>")
    if lottie_code:
        chunks.append(f"<script data-motion-lib=\"lottie-web\">{lottie_code}</script>")
    return "\n".join(chunks)


def motion_runtime() -> str:
    # Tiny GSAP-compatible facade for offline previews. Production can swap this
    # with real GSAP and lottie-web when assets are installed.
    return """
<script data-motion-runtime="dasheng">
(function(){
  var q=function(sel){return Array.prototype.slice.call(document.querySelectorAll(sel));};
  window.gsap=window.gsap||{
    to:function(sel,vars){q(sel).forEach(function(el){Object.keys(vars||{}).forEach(function(k){if(k!=='duration'&&k!=='delay'&&k!=='stagger'&&k!=='ease'){el.style[k]=vars[k];}});});},
    from:function(sel,vars){q(sel).forEach(function(el,i){el.style.opacity='0';el.style.transform='translateY(26px)';setTimeout(function(){el.style.transition='opacity .7s ease, transform .7s ease';el.style.opacity='1';el.style.transform='none';},((vars&&vars.delay)||0)*1000+i*((vars&&vars.stagger)||.08)*1000);});},
    timeline:function(){return {from:function(sel,vars){window.gsap.from(sel,vars);return this;},to:function(sel,vars){window.gsap.to(sel,vars);return this;}};}
  };
  window.initScene=function(){
    var root=document.querySelector('[data-motion-policy]');
    var policy={};
    try{policy=JSON.parse(root.getAttribute('data-motion-policy')||'{}');}catch(e){}
    document.documentElement.setAttribute('data-animation',policy.animation||'gsap_fade_rise');
    window.gsap.from('.kicker,.title,h1,.subtitle,.lead,.card,.paper,.logo',{stagger:.08,delay:.06});
    window.gsap.from('.note,.bar,li,tr,.motion-accent',{stagger:.06,delay:.16});
    if(window.lottie){
      var holder=document.getElementById('lottie-accent');
      var dataNode=document.getElementById('lottie-data');
      if(holder&&dataNode){
        try{
          var data=JSON.parse(dataNode.textContent||'{}');
          holder.innerHTML='';
          window.lottie.loadAnimation({container:holder,renderer:'svg',loop:true,autoplay:true,animationData:data});
        }catch(e){}
      }
    }
  };
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',window.initScene);}else{window.initScene();}
})();
</script>
"""


def base_css() -> str:
    return f"""
*{{box-sizing:border-box}}
html,body{{width:{WIDTH}px;height:{HEIGHT}px;margin:0;overflow:hidden;background:#07090d;color:#f5f2e9}}
body{{font-family:"PingFang SC","Noto Sans SC","Hiragino Sans GB","Microsoft YaHei",sans-serif}}
.frame{{position:relative;width:{WIDTH}px;height:{HEIGHT}px;overflow:hidden;padding:72px}}
.mono{{font-family:"SFMono-Regular","Menlo","Consolas",monospace}}
.serif{{font-family:"Songti SC","Noto Serif SC","Iowan Old Style",serif}}
.kicker{{font-size:22px;letter-spacing:.16em;text-transform:uppercase;color:#d8aa55}}
.title{{font-size:86px;line-height:1.04;font-weight:900;letter-spacing:-.04em}}
.subtitle{{font-size:34px;line-height:1.55;color:#d3d7df}}
.caption{{font-size:24px;line-height:1.5;color:#aab2c2}}
.hairline{{height:1px;background:linear-gradient(90deg,transparent,#d8aa55,transparent)}}
.safe-bottom{{position:absolute;left:72px;right:72px;bottom:74px}}
.motion-accent{{position:absolute;right:54px;top:180px;width:180px;height:180px;border:1px solid rgba(216,170,85,.28);border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;color:#d8aa55;background:radial-gradient(circle,rgba(216,170,85,.12),rgba(216,170,85,.02) 58%,transparent);opacity:.58;animation:pulse 5s ease-in-out infinite;pointer-events:none;text-align:center}}
body.state-evidence_scene .motion-accent{{top:126px;right:44px;opacity:.38}}
body.state-chapter_card .motion-accent{{top:230px;right:72px;transform:scale(1.25)}}
body.state-logic_animation .motion-accent{{border-radius:24px;opacity:.42}}
body.transition-impact_cut .frame:after{{content:"";position:absolute;inset:0;border:8px solid rgba(216,170,85,.34);animation:impactFlash .42s ease both;pointer-events:none}}
body.transition-chapter_hit .frame:after{{content:"";position:absolute;left:0;right:0;top:0;height:9px;background:#d8aa55;animation:slideIn .7s ease both}}
body.transition-data_reveal .bar rect{{transform-origin:left center;animation:barGrow .8s cubic-bezier(.2,.8,.2,1) both}}
body.transition-path_highlight .lines path{{stroke-dasharray:16 9;stroke:#b8862f}}
.fade-in{{animation:fadeIn .8s ease both}}
.rise{{animation:rise .9s cubic-bezier(.2,.8,.2,1) both}}
.delay1{{animation-delay:.18s}}.delay2{{animation-delay:.34s}}.delay3{{animation-delay:.5s}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(34px)}}to{{opacity:1;transform:none}}}}
@keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.035)}}}}
@keyframes slideIn{{from{{opacity:0;transform:translateX(60px)}}to{{opacity:1;transform:none}}}}
@keyframes impactFlash{{0%{{opacity:0;transform:scale(.98)}}20%{{opacity:1;transform:scale(1)}}100%{{opacity:0;transform:scale(1.03)}}}}
@keyframes barGrow{{from{{transform:scaleX(.08)}}to{{transform:scaleX(1)}}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important;transition:none!important}}}}
"""


def scene_shell(scene: dict[str, Any], body: str, extra_css: str = "") -> str:
    title = esc(scene.get("title"))
    duration = scene.get("duration_sec", "")
    template_id = esc(scene.get("template_id"))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={WIDTH}, initial-scale=1">
<title>{title}</title>
<style>{base_css()}{extra_css}</style>
</head>
<body class="{director_body_class(scene)}" data-motion-policy="{motion_meta(scene)}" data-director-policy="{director_meta_attr(scene)}">
<!-- template: {template_id}; duration: {duration}s -->
{body}
<script id="lottie-data" type="application/json">{html.escape(json.dumps(lottie_data_for_scene(scene), ensure_ascii=False), quote=False)}</script>
{inline_real_motion_libs()}
{motion_runtime()}
</body>
</html>
"""


def render_liquid_hero(scene: dict[str, Any]) -> str:
    return scene_shell(
        scene,
        f"""
<main class="frame liquid">
  <div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div>
  {motion_layer(scene)}
  <div class="kicker fade-in">DASHENG · MARKET BRIEF</div>
  <h1 class="title serif rise">{esc(scene.get('title'))}</h1>
  <p class="subtitle rise delay1">{esc(short(scene.get('narration'), 90))}</p>
  <div class="safe-bottom">
    <div class="hairline"></div>
    <p class="caption mono">MARKET BRIEF · SIGNAL BEFORE PRICE</p>
  </div>
</main>
""",
        """
.liquid{background:#090b12}
.blob{position:absolute;border-radius:999px;filter:blur(58px);opacity:.72;mix-blend-mode:screen;animation:pulse 7s ease-in-out infinite}
.b1{width:760px;height:760px;left:-210px;top:120px;background:#173b7a}
.b2{width:680px;height:680px;right:-240px;top:360px;background:#a4512d;animation-delay:-2s}
.b3{width:620px;height:620px;left:120px;bottom:-160px;background:#184b3d;animation-delay:-4s}
.liquid .title{position:relative;margin:290px 0 34px;font-size:98px;text-shadow:0 14px 60px rgba(0,0,0,.42)}
.liquid .subtitle{position:relative;max-width:850px}
""",
    )


def render_glitch(scene: dict[str, Any]) -> str:
    title = esc(scene.get("title"))
    return scene_shell(
        scene,
        f"""
<main class="frame glitch">
  <div class="scan"></div>
  {motion_layer(scene)}
  <div class="top mono">&gt;&gt; SIGNAL · MARKET · WATCH</div>
  <section class="glitch-title">
    <h1 data-text="{title}">{title}</h1>
    <p class="mono">{esc(short(scene.get('narration'), 96))}</p>
  </section>
  <div class="safe-bottom mono">NOISE ≠ SIGNAL · FOLLOW THE MONEY</div>
</main>
""",
        """
.glitch{background:#08090d;background-image:linear-gradient(rgba(0,255,220,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,220,.045) 1px,transparent 1px);background-size:54px 54px}
.scan{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.035),rgba(255,255,255,.035) 1px,transparent 1px,transparent 4px)}
.top{position:absolute;top:62px;left:72px;right:72px;color:#80fff0;font-size:20px;letter-spacing:.14em}
.glitch-title{position:absolute;left:72px;right:72px;top:520px}
.glitch h1{position:relative;margin:0;font-size:96px;line-height:1.05;font-weight:950;letter-spacing:-.05em;animation:glitch 3.8s infinite}
.glitch h1:before,.glitch h1:after{content:attr(data-text);position:absolute;inset:0;pointer-events:none}
.glitch h1:before{color:#00f0ff;transform:translate(-4px,2px);mix-blend-mode:screen}
.glitch h1:after{color:#ff2bd6;transform:translate(4px,-2px);mix-blend-mode:screen}
.glitch p{margin-top:34px;color:#c7cbd6;font-size:28px;line-height:1.55}
@keyframes glitch{0%,92%,100%{transform:none}94%{transform:translateX(-10px)}95%{transform:translateX(8px)}96%{transform:translateX(-3px)}}
""",
    )


def render_cinema(scene: dict[str, Any]) -> str:
    return scene_shell(
        scene,
        f"""
<main class="frame cinema">
  <div class="leak"></div>
  <div class="letterbox top"></div><div class="letterbox bottom"></div>
  {motion_layer(scene)}
  <div class="kicker rise">CHAPTER</div>
  <h1 class="serif rise delay1">{esc(scene.get('title'))}</h1>
  <p class="subtitle rise delay2">{esc(short(scene.get('narration'), 80))}</p>
</main>
""",
        """
.cinema{background:#17110d}
.cinema:before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 15% 20%,rgba(255,177,89,.35),transparent 28%),radial-gradient(circle at 85% 45%,rgba(141,38,20,.32),transparent 35%),linear-gradient(180deg,#17110d,#090806)}
.leak{position:absolute;inset:-20%;background:linear-gradient(115deg,transparent 35%,rgba(255,205,120,.36),transparent 58%);animation:slideIn 1.6s ease both}
.letterbox{position:absolute;left:0;right:0;height:180px;background:#030303;z-index:3}.letterbox.top{top:0}.letterbox.bottom{bottom:0}
.cinema .kicker{position:relative;z-index:4;margin-top:380px}
.cinema h1{position:relative;z-index:4;margin:28px 0 22px;font-size:92px;line-height:1.05}
.cinema .subtitle{position:relative;z-index:4;max-width:790px}
""",
    )


def render_flowchart(scene: dict[str, Any]) -> str:
    variables = scene.get("variables") or {}
    nodes = variables.get("headings") if isinstance(variables.get("headings"), list) else split_units(scene.get("narration", ""), 5)
    nodes = [short(item, 18) for item in nodes[:5] if clean_text(item)] or split_units(scene.get("title", ""), 5)
    positions = [(84, 445), (558, 410), (178, 760), (620, 828), (320, 1135)]
    cards = []
    path_parts = []
    for idx, node in enumerate(nodes):
        x, y = positions[idx % len(positions)]
        cards.append(f'<div class="note n{idx}" style="left:{x}px;top:{y}px"><b>{idx+1:02d}</b><span>{esc(node)}</span></div>')
        if idx < len(nodes) - 1:
            x2, y2 = positions[(idx + 1) % len(positions)]
            path_parts.append(f'M{x+230},{y+95} C{x+330},{y+40} {x2-70},{y2+130} {x2},{y2+90}')
    paths = "".join(f'<path d="{d}" />' for d in path_parts)
    return scene_shell(
        scene,
        f"""
<main class="frame flow">
  {motion_layer(scene)}
  <div class="kicker">LOGIC MAP</div>
  <h1>{esc(scene.get('title'))}</h1>
  <svg class="lines" viewBox="0 0 {WIDTH} {HEIGHT}">{paths}</svg>
  {''.join(cards)}
  <p class="safe-bottom caption">{esc(short(scene.get('narration'), 120))}</p>
</main>
""",
        """
.flow{background:#f4ede1;color:#1f1d18;background-image:linear-gradient(rgba(0,0,0,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.035) 1px,transparent 1px);background-size:42px 42px}
.flow h1{font-size:54px;line-height:1.16;margin:22px 0 0;max-width:860px}
.lines{position:absolute;inset:0}.lines path{fill:none;stroke:#1f1d18;stroke-width:4;stroke-dasharray:10 9;stroke-linecap:round;opacity:.55;animation:draw 1.1s ease both}
.note{position:absolute;width:330px;min-height:190px;background:#fcd34d;color:#1b1b18;box-shadow:0 18px 38px rgba(0,0,0,.16);padding:24px;transform:rotate(-2deg);animation:rise .8s ease both}
.note:nth-of-type(odd){background:#a7f3d0;transform:rotate(1.6deg)}.note b{display:block;font-size:22px;margin-bottom:18px}.note span{font-size:31px;line-height:1.22;font-weight:800}
@keyframes draw{from{stroke-dashoffset:500;opacity:0}to{stroke-dashoffset:0;opacity:.55}}
.flow .safe-bottom{color:#5f584d}
""",
    )


def render_data(scene: dict[str, Any], table_mode: bool = False) -> str:
    rows = chart_rows(scene)
    values = [abs(float(row["value"])) for row in rows]
    max_value = max(values) if values else 1
    bars = []
    for idx, row in enumerate(rows[:6]):
        w = 120 + int((abs(float(row["value"])) / max_value) * 600)
        y = 700 + idx * 118
        color = "#b91c1c" if float(row["value"]) < 0 or "-" in str(row["display"]) else "#1f5f8b"
        bars.append(
            f'<g class="bar" style="animation-delay:{idx*.12}s"><text x="80" y="{y+38}">{esc(row["label"])}</text><rect x="250" y="{y}" width="{w}" height="54" rx="8" fill="{color}"/><text x="{270+w}" y="{y+38}" class="value">{esc(row["display"])}</text></g>'
        )
    table = table_from_variables(scene)
    table_html = ""
    if table_mode and table:
        trs = []
        for ridx, row in enumerate(table[:7]):
            tag = "th" if ridx == 0 else "td"
            trs.append("<tr>" + "".join(f"<{tag}>{esc(cell)}</{tag}>" for cell in row[:4]) + "</tr>")
        table_html = f"<table>{''.join(trs)}</table>"
    return scene_shell(
        scene,
        f"""
<main class="frame data">
  {motion_layer(scene)}
  <div class="kicker mono">DATA · FROM ARTICLE</div>
  <h1 class="serif">{esc(scene.get('title'))}</h1>
  <p class="lead">{esc(short(scene.get('narration'), 92))}</p>
  <svg class="chart" viewBox="0 0 {WIDTH} {HEIGHT}">
    <line x1="250" y1="650" x2="250" y2="1420" />
    {''.join(bars)}
  </svg>
  {table_html}
  <footer class="mono">Source: 原文资料 · 数据经核验</footer>
</main>
""",
        """
.data{background:#f7f5ee;color:#161616}
.data h1{font-size:66px;line-height:1.1;margin:24px 0 18px;max-width:900px}.lead{font-size:30px;line-height:1.45;max-width:880px;color:#4a463d}
.chart{position:absolute;left:0;top:0}.chart line{stroke:#1a1a1a;stroke-width:2;opacity:.25}.bar{opacity:0;animation:slideIn .65s ease both}.bar text{font:26px Menlo,monospace;fill:#333}.bar .value{font-weight:800;fill:#111}
table{position:absolute;left:72px;right:72px;bottom:145px;width:936px;border-collapse:collapse;background:#fffaf0;border:1px solid #d7d0bf;font-size:22px}
th,td{padding:16px 14px;border-bottom:1px solid #ded6c8;text-align:left}th{background:#1b365d;color:#fff}td{color:#1f1d18}
footer{position:absolute;left:72px;bottom:78px;color:#777;font-size:18px}
""",
    )


def render_alert(scene: dict[str, Any]) -> str:
    bullets = split_units(scene.get("narration", ""), 4)
    lis = "".join(f"<li>{esc(item)}</li>" for item in bullets)
    return scene_shell(
        scene,
        f"""
<main class="frame alert">
  <div class="stripe"></div>
  {motion_layer(scene)}
  <p class="mono kicker">RISK ALERT</p>
  <h1>{esc(scene.get('title'))}</h1>
  <ul>{lis}</ul>
  <div class="safe-bottom mono">WATCH: POLICY · LIQUIDITY · POSITIONING</div>
</main>
""",
        """
.alert{background:#130807;color:#fff4ea}.stripe{position:absolute;left:-80px;right:-80px;top:0;height:190px;background:repeating-linear-gradient(135deg,#2b0505 0 34px,#c2410c 34px 68px)}
.alert .kicker{margin-top:260px;color:#ffbd6b}.alert h1{font-size:74px;line-height:1.08;margin:30px 0 60px;max-width:870px;text-decoration:line-through;text-decoration-color:#ff6b47}
.alert li{list-style:none;margin:0 0 28px;padding:24px 28px;border-left:8px solid #ff6b47;background:#26100e;font-size:34px;line-height:1.35;animation:rise .7s ease both}
""",
    )


def render_quote(scene: dict[str, Any]) -> str:
    quote = (scene.get("variables") or {}).get("quote") or scene.get("narration") or scene.get("title")
    return scene_shell(
        scene,
        f"""
<main class="frame quote">
  {motion_layer(scene)}
  <div class="card rise">
    <p class="mark">“</p>
    <h1 class="serif">{esc(quote)}</h1>
    <p class="mono">— 关键判断 · FROM ARTICLE</p>
  </div>
</main>
""",
        """
.quote{background:#111827;background-image:radial-gradient(circle at 18% 20%,rgba(216,170,85,.2),transparent 32%),radial-gradient(circle at 78% 70%,rgba(31,95,139,.25),transparent 30%)}
.card{position:absolute;left:72px;right:72px;top:420px;padding:68px;background:#f7f2e7;color:#14120f;border-radius:42px;box-shadow:0 30px 90px rgba(0,0,0,.38)}
.mark{font-size:120px;margin:0;color:#b67b2f}.quote h1{font-size:62px;line-height:1.2;margin:-30px 0 42px}.quote .mono{font-size:22px;color:#686055}
""",
    )


def render_document(scene: dict[str, Any]) -> str:
    variables = scene.get("variables") or {}
    image_src = esc(variables.get("src") or "")
    image_block = f'<img src="{image_src}" alt="{esc(variables.get("alt"))}">' if image_src else '<div class="placeholder">SOURCE MATERIAL</div>'
    return scene_shell(
        scene,
        f"""
<main class="frame doc">
  {motion_layer(scene)}
  <section class="paper">
    <p class="mono">DOCUMENT EVIDENCE</p>
    <h1 class="serif">{esc(scene.get('title'))}</h1>
    {image_block}
    <p>{esc(short(scene.get('narration'), 150))}</p>
  </section>
</main>
""",
        """
.doc{background:#ebe5d6;color:#1f1d18}.paper{position:absolute;left:80px;right:80px;top:150px;bottom:150px;background:#f5f4ed;border:1px solid #d4d1c5;padding:58px}
.paper .mono{color:#1b365d;letter-spacing:.14em}.paper h1{font-size:58px;line-height:1.16;margin:28px 0 34px}.paper p{font-size:28px;line-height:1.52;color:#4f4a40}
img,.placeholder{display:block;width:100%;height:760px;object-fit:contain;background:#efeee5;border:1px solid #d4d1c5;margin:26px 0}.placeholder{font:34px Menlo,monospace;color:#1b365d;display:flex;align-items:center;justify-content:center}
""",
    )


def render_outro(scene: dict[str, Any]) -> str:
    return scene_shell(
        scene,
        f"""
<main class="frame outro">
  {motion_layer(scene)}
  <div class="logo">大</div>
  <h1>大圣财经</h1>
  <p>{esc(short(scene.get('narration'), 80))}</p>
  <div class="safe-bottom mono">SIGNAL · NOT NOISE</div>
</main>
""",
        """
.outro{background:#08090c;text-align:center}.logo{width:220px;height:220px;border-radius:48px;margin:430px auto 54px;background:linear-gradient(135deg,#d8aa55,#7a4b19);display:flex;align-items:center;justify-content:center;font-size:130px;font-weight:950;box-shadow:0 0 70px rgba(216,170,85,.25);animation:rise .9s ease both}
.outro h1{font-size:76px;margin:0 0 26px}.outro p{font-size:32px;line-height:1.5;color:#cfd3dc;max-width:760px;margin:0 auto}
""",
    )


def render_generic(scene: dict[str, Any]) -> str:
    return scene_shell(
        scene,
        f"""
<main class="frame generic">
  {motion_layer(scene)}
  <p class="kicker mono">MARKET NOTE</p>
  <h1>{esc(scene.get('title'))}</h1>
  <p>{esc(short(scene.get('narration'), 180))}</p>
</main>
""",
        """
.generic{background:#111827}.generic h1{font-size:72px;line-height:1.12;margin:360px 0 38px}.generic p{font-size:32px;line-height:1.55;color:#cfd3dc}
""",
    )


def render_scene(scene: dict[str, Any]) -> str:
    part = scene.get("content_part")
    template_id = scene.get("template_id")
    if part == "article_title" or template_id == "frame-liquid-bg-hero":
        return render_liquid_hero(scene)
    if part in {"opening_hook", "transition"} or template_id == "frame-glitch-title":
        return render_glitch(scene)
    if part == "chapter_divider" or template_id == "frame-light-leak-cinema":
        return render_cinema(scene)
    if part in {"overall_outline", "logic_chain", "timeline"} or template_id == "frame-flowchart-sticky":
        return render_flowchart(scene)
    if part in {"data_chart", "financial_chart", "kpi_card"}:
        return render_data(scene)
    if part == "data_table":
        return render_data(scene, table_mode=True)
    if part == "warning_or_risk":
        return render_alert(scene)
    if part in {"quote", "pull_quote"}:
        return render_quote(scene)
    if part in {"article_image", "news_or_document", "source_citation"}:
        return render_document(scene)
    if part in {"closing_outro", "brand_mark"} or template_id == "frame-logo-outro":
        return render_outro(scene)
    return render_generic(scene)


def build_preview(manifest: dict[str, Any]) -> str:
    cards = []
    for scene in manifest["scenes"]:
        cards.append(
            f"""
<article>
  <iframe src="{esc(scene['relative_html'])}"></iframe>
  <div><b>{esc(scene['id'])}</b><span>{esc(scene['content_part'])}</span><code>{esc(scene['template_id'])}</code><em>{scene['start_sec']}s → {scene['end_sec']}s</em></div>
</article>
"""
        )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{esc(manifest['title'])}</title>
<style>
body{{margin:0;padding:28px;background:#10131a;color:#f5f2e9;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
h1{{margin:0 0 8px;font-size:34px}}p{{color:#aab2c2}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}}
article{{background:#171c27;border:1px solid #30394a;border-radius:18px;overflow:hidden}}iframe{{width:100%;aspect-ratio:9/16;border:0;background:#000}}
article div{{padding:12px 14px;display:grid;gap:5px}}span,em,code{{color:#aab2c2;font-style:normal}}code{{color:#d8aa55}}
</style></head><body>
<h1>{esc(manifest['title'])}</h1>
<p>{manifest['scene_count']} scenes · {manifest['duration_estimate_sec']}s · HTML Anything routed preview</p>
<section class="grid">{''.join(cards)}</section>
</body></html>
"""


def build_pack(timeline_path: Path, output_dir: Path) -> dict[str, Any]:
    timeline = load_json(timeline_path)
    scenes = timeline.get("timeline") or []
    output_dir.mkdir(parents=True, exist_ok=True)
    scene_dir = output_dir / "scenes"
    rendered = []
    for index, scene in enumerate(scenes, 1):
        file_name = f"{index:03d}_{scene.get('content_part','scene')}_{scene.get('template_id','template')}.html"
        safe_name = re.sub(r"[^0-9A-Za-z_.-]+", "_", file_name)
        html_path = scene_dir / safe_name
        write_text(html_path, render_scene(scene))
        rendered.append(
            {
                "id": scene.get("id"),
                "index": index,
                "content_part": scene.get("content_part"),
                "beat_class": scene.get("beat_class"),
                "director_state": scene.get("director_state"),
                "driver_scores": scene.get("driver_scores"),
                "driver_score": scene.get("driver_score"),
                "template_id": scene.get("template_id"),
                "start_sec": scene.get("start_sec"),
                "end_sec": scene.get("end_sec"),
                "duration_sec": scene.get("duration_sec"),
                "title": scene.get("title"),
                "narration": scene.get("narration"),
                "motion_policy": motion_policy(scene),
                "transition_to_next": scene.get("transition_to_next"),
                "audio": scene.get("audio"),
                "html": str(html_path.resolve()),
                "relative_html": str(html_path.relative_to(output_dir)),
            }
        )
    manifest = {
        "schema_version": "dasheng.html_anything_scene_pack.v1",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_timeline": str(timeline_path.resolve()),
        "title": timeline.get("title"),
        "aspect": timeline.get("aspect", "9:16"),
        "width": WIDTH,
        "height": HEIGHT,
        "scene_count": len(rendered),
        "duration_estimate_sec": timeline.get("duration_estimate_sec"),
        "template_usage": dict(Counter(scene["template_id"] for scene in rendered)),
        "director_usage": dict(Counter(clean_text(scene.get("director_state")) for scene in rendered)),
        "beat_usage": dict(Counter(clean_text(scene.get("beat_class")) for scene in rendered)),
        "transition_usage": dict(Counter(clean_text(scene.get("transition_to_next")) for scene in rendered)),
        "motion_runtime": {
            "mode": MOTION_RUNTIME_MODE,
            "gsap_inline": bool(read_motion_lib("gsap")) and MOTION_RUNTIME_MODE != "lite",
            "lottie_inline": bool(read_motion_lib("lottie")) and MOTION_RUNTIME_MODE != "lite",
            "lottie_asset_policy": "Generated lightweight Lottie JSON per scene; replace with searched/designed assets when available.",
        },
        "scenes": rendered,
        "render_next": {
            "preview_html": str((output_dir / "preview.html").resolve()),
            "policy": "Render each scene HTML to video/image segment, align to audio master, then stitch.",
        },
    }
    write_text(output_dir / "scene_pack_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_text(output_dir / "preview.html", build_preview(manifest))
    narration = "\n".join(f"{idx:02d}. {scene['narration']}" for idx, scene in enumerate(rendered, 1))
    write_text(output_dir / "narration_script.txt", narration + "\n")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render HTML Anything routed timeline into standalone scene HTML pack.")
    parser.add_argument("--timeline", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--motion-runtime", choices=["auto", "lite"], default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    global MOTION_RUNTIME_MODE
    MOTION_RUNTIME_MODE = args.motion_runtime
    manifest = build_pack(Path(args.timeline).expanduser().resolve(), Path(args.output_dir).expanduser().resolve())
    print(
        json.dumps(
            {
                "status": "ok",
                "output_dir": str(Path(args.output_dir).expanduser().resolve()),
                "scene_count": manifest["scene_count"],
                "preview_html": manifest["render_next"]["preview_html"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
