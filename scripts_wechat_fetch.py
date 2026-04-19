#!/usr/bin/env python3
"""Fetch WeChat mp.weixin.qq.com articles and extract main content.

No third-party deps: uses urllib + html.parser.
Outputs both raw HTML and a cleaned markdown-ish text to data/wechat_scrapes/.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple


URLS = [
    "https://mp.weixin.qq.com/s/mYh_xCV1C8vA8NDhlLxr4w?clicktime=1769846447&enterid=1769846447&scene=126&sessionid=1769846443&subscene=227",
    "https://mp.weixin.qq.com/s/c2zPPrM_tEwU0CRhLp8osg?clicktime=1769846485&enterid=1769846485&scene=126&sessionid=1769846443&subscene=227",
    "https://mp.weixin.qq.com/s/B17jMF7Kb2IDF2aVxlPTGw?clicktime=1769846504&enterid=1769846504&scene=126&sessionid=1769846443&subscene=227",
    "https://mp.weixin.qq.com/s/t9w1ffdBospC5VIncX8aHA?clicktime=1769846528&enterid=1769846528&scene=126&sessionid=1769846517&subscene=227",
    "https://mp.weixin.qq.com/s/U6b45qP1A4hu28auQGrPZQ?scene=0&subscene=90",
    "https://mp.weixin.qq.com/s/tL0GR32DqYDY6LpsmPTBAA?scene=0&subscene=90",
]


def _find_first(pattern: str, s: str) -> str:
    m = re.search(pattern, s, flags=re.S)
    return unescape(m.group(1).strip()) if m else ""


@dataclass
class Extracted:
    url: str
    title: str
    author: str
    date: str
    text: str
    images: int


class WechatContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.in_author = False
        self.in_date = False
        self.in_content = False

        self._buf: List[str] = []
        self._line: List[str] = []
        self._stack: List[str] = []

        self.title_parts: List[str] = []
        self.author_parts: List[str] = []
        self.date_parts: List[str] = []
        self.images = 0

        self._bold_depth = 0
        self._quote_depth = 0
        self._li_depth = 0
        self._need_space = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attrs_d = {k: (v or "") for k, v in attrs}

        if tag == "h1" and attrs_d.get("id") == "activity-name":
            self.in_title = True
        if tag in ("a", "span") and attrs_d.get("id") == "js_name":
            self.in_author = True
        if tag == "em" and attrs_d.get("id") == "publish_time":
            self.in_date = True

        if tag == "div" and attrs_d.get("id") == "js_content":
            self.in_content = True

        if self.in_content:
            self._stack.append(tag)
            if tag in ("p", "section"):
                self._flush_line()
            elif tag in ("br",):
                self._line.append("\n")
            elif tag in ("h2",):
                self._flush_line()
                self._buf.append("\n## ")
            elif tag in ("h3",):
                self._flush_line()
                self._buf.append("\n### ")
            elif tag in ("h4",):
                self._flush_line()
                self._buf.append("\n#### ")
            elif tag == "strong" or tag == "b":
                self._bold_depth += 1
                self._buf.append("**")
            elif tag == "blockquote":
                self._quote_depth += 1
                self._flush_line()
                self._buf.append("\n> ")
            elif tag == "li":
                self._li_depth += 1
                self._flush_line()
                self._buf.append("\n- ")
            elif tag == "img":
                self.images += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self.in_title:
            self.in_title = False
        if tag in ("a", "span") and self.in_author:
            self.in_author = False
        if tag == "em" and self.in_date:
            self.in_date = False

        if self.in_content:
            if tag == "strong" or tag == "b":
                if self._bold_depth > 0:
                    self._buf.append("**")
                    self._bold_depth -= 1
            elif tag == "blockquote":
                if self._quote_depth > 0:
                    self._quote_depth -= 1
                    self._buf.append("\n")
            elif tag == "li":
                if self._li_depth > 0:
                    self._li_depth -= 1
                    self._buf.append("\n")
            elif tag in ("p", "section", "h2", "h3", "h4"):
                self._buf.append("\n")

            # pop stack best-effort
            if self._stack and self._stack[-1] == tag:
                self._stack.pop()

        if tag == "div" and self.in_content:
            # end of js_content
            self._flush_line()
            self.in_content = False

    def handle_data(self, data: str) -> None:
        s = data
        if not s or not s.strip():
            return

        if self.in_title:
            self.title_parts.append(s.strip())
            return
        if self.in_author:
            self.author_parts.append(s.strip())
            return
        if self.in_date:
            self.date_parts.append(s.strip())
            return

        if not self.in_content:
            return

        # Normalize whitespace inside content.
        s = re.sub(r"\s+", " ", s)

        if self._need_space and not s.startswith(("\n", ",", ".", "?", "!", "，", "。", "？", "！", "：", ":")):
            self._line.append(" ")
        self._line.append(s)
        self._need_space = True

    def _flush_line(self) -> None:
        if not self._line:
            self._need_space = False
            return
        text = "".join(self._line).strip()
        if text:
            self._buf.append(text)
            self._buf.append("\n")
        self._line = []
        self._need_space = False

    def markdown(self) -> str:
        self._flush_line()
        md = "".join(self._buf)
        # Clean excessive blank lines.
        md = re.sub(r"\n{3,}", "\n\n", md)
        md = md.strip() + "\n"
        return md


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    return raw.decode("utf-8", errors="replace")


def extract(url: str, html: str) -> Extracted:
    p = WechatContentParser()
    p.feed(html)
    title = "".join(p.title_parts).strip() or _find_first(r"<title>(.*?)</title>", html)
    author = "".join(p.author_parts).strip()
    date = "".join(p.date_parts).strip()
    text = p.markdown()

    # Fallbacks if parser missed header fields.
    if not author:
        author = _find_first(r"id=\"js_name\"[^>]*>(.*?)</", html)
    if not date:
        date = _find_first(r"id=\"publish_time\"[^>]*>(.*?)</", html)

    return Extracted(url=url, title=title, author=author, date=date, text=text, images=p.images)


def slug_for(url: str, title: str) -> str:
    # Stable id from the /s/<id>
    m = re.search(r"/s/([^?]+)", url)
    short = m.group(1) if m else hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    safe_title = re.sub(r"[\\/:*?\"<>|]+", "_", title).strip()
    safe_title = re.sub(r"\s+", " ", safe_title)[:60]
    if safe_title:
        return f"{short}__{safe_title}"
    return short


def main() -> int:
    out_dir = os.path.join("data", "wechat_scrapes")
    os.makedirs(out_dir, exist_ok=True)

    index = []
    for i, url in enumerate(URLS, 1):
        print(f"[{i}/{len(URLS)}] fetching {url}")
        html = fetch_html(url)
        ex = extract(url, html)
        slug = slug_for(url, ex.title)

        raw_path = os.path.join(out_dir, f"{slug}.html")
        txt_path = os.path.join(out_dir, f"{slug}.md")
        meta_path = os.path.join(out_dir, f"{slug}.meta.json")

        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(html)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(ex.text)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "url": ex.url,
                    "title": ex.title,
                    "author": ex.author,
                    "date": ex.date,
                    "images": ex.images,
                    "text_chars": len(ex.text),
                    "slug": slug,
                    "raw_path": raw_path,
                    "text_path": txt_path,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        index.append(
            {
                "url": ex.url,
                "title": ex.title,
                "author": ex.author,
                "date": ex.date,
                "images": ex.images,
                "text_chars": len(ex.text),
                "slug": slug,
                "raw_path": raw_path,
                "text_path": txt_path,
            }
        )

        # be polite
        time.sleep(0.6)

    with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(index)} articles to {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
