"""Short-video script generation for the trial-operation feature."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import settings


def _feature_text(features: str) -> str:
    return (features or "高颜值、实用、适合日常分享").strip()


def _mock_script(
    product_name: str,
    features: str,
    platform: str,
    language: str,
    duration_sec: int,
    style: str = "casual",
) -> dict[str, Any]:
    feat = _feature_text(features)
    shots = max(3, min(6, duration_sec // 4))
    step = max(1, duration_sec // shots)

    if language.startswith("en"):
        hook = f"Stop scrolling: {product_name} is worth a closer look."
        voiceover = (
            f"Today I am sharing {product_name}. The key reasons are: {feat}. "
            f"In the next {duration_sec} seconds, show the product context, highlight the details, "
            f"and end with a clear reason to search it on {platform}."
        )
        cta = f"Search {product_name} on {platform}."
        hashtags = f"#{product_name.replace(' ', '')},#TikTokMadeMeBuyIt,#ShoppingFinds"
        templates = [
            ("Close-up opening shot with strong on-screen hook", f"Here is why {product_name} caught my eye."),
            ("Show the main use case in a real-life setting", f"The first thing to notice is {feat[:60]}."),
            ("Detail shot for material, texture, or packaging", "The details make it feel more premium."),
            ("Before-and-after or pain-point comparison", "This solves a small problem in a very simple way."),
            ("Final hero shot with CTA", f"Search {product_name} on {platform} if you want the same one."),
        ]
    else:
        hook = f"别划走，{product_name} 这个卖点很适合做短视频开场。"
        voiceover = (
            f"今天试运营一条 {product_name} 的短视频脚本。核心卖点是：{feat}。"
            f"前 3 秒先用痛点或高颜值画面抓住注意力，中段展示使用场景和细节，"
            f"结尾用明确行动号召引导用户去 {platform} 搜索或下单。"
        )
        cta = f"想要同款，可以去 {platform} 搜索：{product_name}"
        hashtags = f"#{product_name},#跨境好物,#短视频脚本,#种草推荐"
        templates = [
            ("开场抓眼：商品特写或场景化镜头，加一句强钩子字幕", f"别划走，{product_name} 这个点真的能打。"),
            ("卖点展示：用手持、桌面或生活场景展示核心使用方式", f"它最适合主打的是：{feat[:60]}。"),
            ("细节特写：材质、做工、包装、颜色或尺寸对比", "细节给到位，用户会更容易相信质感。"),
            ("痛点反转：展示使用前后的差异或决策理由", "以前纠结很久，现在可以直接看这个方案。"),
            ("收尾 CTA：定格商品和购买入口", f"想要同款，就去 {platform} 搜索 {product_name}。"),
        ]

    storyboard = []
    for i in range(shots):
        visual, vo = templates[i % len(templates)]
        start = i * step
        end = duration_sec if i == shots - 1 else min(duration_sec, (i + 1) * step)
        storyboard.append(
            {
                "idx": i + 1,
                "start_sec": start,
                "end_sec": end,
                "visual": visual,
                "voiceover": vo,
                "on_screen_text": product_name if i == 0 else feat.split("，")[0][:16],
            }
        )

    return {
        "hook": hook,
        "voiceover": voiceover,
        "cta": cta,
        "hashtags": hashtags,
        "storyboard": storyboard,
        "style": style,
        "source": "mock",
    }


def _extract_json(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("\n```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        raise


def _normalize_plan(data: dict[str, Any]) -> dict[str, Any]:
    board = []
    for i, shot in enumerate(data.get("storyboard") or []):
        board.append(
            {
                "idx": int(shot.get("idx") or i + 1),
                "start_sec": int(shot.get("start_sec") or 0),
                "end_sec": int(shot.get("end_sec") or 0),
                "visual": str(shot.get("visual") or ""),
                "voiceover": str(shot.get("voiceover") or ""),
                "on_screen_text": str(shot.get("on_screen_text") or ""),
            }
        )
    if not board:
        raise ValueError("empty storyboard")
    return {
        "hook": str(data.get("hook") or ""),
        "voiceover": str(data.get("voiceover") or ""),
        "cta": str(data.get("cta") or ""),
        "hashtags": str(data.get("hashtags") or ""),
        "storyboard": board,
        "source": "llm",
    }


async def generate_video_plan(
    product_name: str,
    features: str = "",
    platform: str = "TikTok",
    language: str = "zh",
    duration_sec: int = 15,
    style: str = "casual",
) -> dict[str, Any]:
    if not settings.LLM_API_KEY:
        return _mock_script(product_name, features, platform, language, duration_sec, style)

    lang_name = {
        "zh": "中文",
        "en": "English",
        "ja": "日本語",
        "ko": "한국어",
        "es": "Español",
    }.get(language, language)

    prompt = f"""你是跨境电商短视频策划。请为商品生成 {duration_sec} 秒短视频口播脚本与分镜表。

商品：{product_name}
卖点：{features or "高颜值、实用、值得入手"}
平台：{platform}
语言：{lang_name}
风格：{style}

严格输出 JSON，不要 Markdown：
{{
  "hook": "开头 3 秒钩子",
  "voiceover": "完整口播稿",
  "cta": "结尾行动号召",
  "hashtags": "标签，逗号分隔",
  "storyboard": [
    {{
      "idx": 1,
      "start_sec": 0,
      "end_sec": 3,
      "visual": "画面描述",
      "voiceover": "该段旁白",
      "on_screen_text": "字幕"
    }}
  ]
}}

要求：
1. storyboard 3 到 6 镜，时间连续覆盖 0 到 {duration_sec} 秒。
2. 画面要可执行，包含特写、使用场景、卖点展示和 CTA。
3. 不要输出解释，只输出 JSON。
"""

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                settings.LLM_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL or "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a short-video creative director. Output valid JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.8,
                    "max_tokens": 1200,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return _normalize_plan(_extract_json(content))
    except Exception as exc:
        print(f"[video] LLM failed, fallback mock: {exc}")
        return _mock_script(product_name, features, platform, language, duration_sec, style)
