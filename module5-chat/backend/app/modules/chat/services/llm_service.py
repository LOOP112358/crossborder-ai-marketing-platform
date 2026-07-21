import httpx
from datetime import datetime
from typing import List

from app.modules.chat.services.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


def _fallback_answer(question: str, contexts: List[str], language: str) -> str:
    if not contexts:
        if language == "en":
            return (
                "Sorry, I couldn't find relevant information in the knowledge base. "
                "Please upload a product document or try asking about Amazon product features."
            )
        return "抱歉，未在知识库中找到相关信息。请上传商品文档，或尝试询问具体品类，例如：耳机、运动鞋、手机壳。"

    # 尽量结构化展示，贴近成员5演示效果
    lines = []
    if language == "en":
        lines.append("Based on the knowledge base:")
    else:
        lines.append("根据知识库检索结果：")
    lines.append("")
    for i, c in enumerate(contexts[:5], 1):
        parsed = {}
        for row in c.splitlines():
            if ":" in row:
                k, v = row.split(":", 1)
                parsed[k.strip().lower()] = v.strip()
        name = parsed.get("product name") or c[:80]
        brand = parsed.get("brand") or "-"
        ptype = parsed.get("product type") or "-"
        bullets = parsed.get("bullet points") or ""
        tip = bullets.split("|")[0].strip() if bullets else ""
        lines.append(f"{i}. {name}")
        lines.append(f"   - {'Type' if language == 'en' else '类型'}：{ptype}")
        lines.append(f"   - {'Brand' if language == 'en' else '品牌'}：{brand}")
        if tip:
            lines.append(f"   - {'Highlight' if language == 'en' else '卖点'}：{tip[:120]}")
        lines.append("")
    if language == "en":
        lines.append(f'Related to your question "{question}". You can ask a brand name for more details.')
    else:
        lines.append(f"关于「{question}」，可继续追问某个品牌名获取更多细节。")
    return "\n".join(lines).strip()


async def generate_bilingual_reply(question: str, contexts: List[str], language: str,
                                   catalog_summary: str = "", history: str = "") -> str:
    """生成指定语言的回复；若配置了 LLM 则调用，否则使用检索增强模板回复。"""
    if not OPENAI_API_KEY:
        return _fallback_answer(question, contexts, language)

    context_block = "\n".join(contexts) if contexts else "无相关资料"
    catalog_info = f"\n【商品目录概况】\n{catalog_summary}\n" if catalog_summary else ""
    history_block = f"\n【对话历史】\n{history}\n" if history else ""
    prompt = (
        f"你是电商智能客服助手。请根据用户提问的语言，用同样的语言回答。\n\n"
        f"{catalog_info}"
        f"{history_block}"
        f"【重要规则】\n"
        f"1. 如果用户问「有什么商品」「在售什么」「推荐商品」等笼统问题，"
        f"请根据【商品目录概况】中的真实数据来回答，告诉用户商品总数和品类分布，引导用户选择品类。\n"
        f"2. 只有当用户指定了品类、品牌等具体条件时，才从参考知识中列出具体商品。\n"
        f"3. 用户的追问（如「还有别的吗」「继续」）要结合【对话历史】理解上下文，基于之前讨论的品类继续回答。\n"
        f"4. 用中文回答时，商品属性（材质、颜色、款式、卖点等）必须全部翻译成中文，"
        f"但品牌名保留英文原名不翻译。整段回复不能中英混杂，读起来要自然流畅。\n\n"
        f"参考知识（检索到的部分商品）：\n{context_block}\n\n"
        f"用户问题：{question}\n\n"
        "请基于参考知识给出准确、简洁的回答。"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            clean = raw.replace("**", "")
            return clean
    except Exception:
        return _fallback_answer(question, contexts, language)


async def generate_operation_advice(stats_summary: str) -> str:
    if not OPENAI_API_KEY:
        return (
            "【运营建议（本地模式）】\n"
            f"{stats_summary}\n\n"
            "建议：关注使用量最高的功能模块，优化低使用率功能的用户体验；"
            "对错误率偏高的模块进行日志排查；加大热门品类相关商品的推广力度。"
        )

    prompt = (
        "你是电商运营专家。以下是一个AI电商平台的数据，平台分为两类工具：\n"
        "1. 商家端（文案生成、商品抠图、背景生成、海报合成）—— 帮助卖家制作商品海报，目前还在开发联调阶段，使用量可能为0是正常的\n"
        "2. 顾客端（智能客服）—— 面向消费者的商品问答，这是目前唯一已上线的模块\n\n"
        "请聚焦智能客服模块，结合热门品类、用户反馈（点赞/点踩）、调用趋势等数据，"
        "给出3条具体可执行的运营建议（中文）。不要建议「提高XX功能使用量」因为那是商家端的开发问题不是运营问题。\n\n"
        f"{stats_summary}"
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip().replace("**", "")
    except Exception:
        return (
            "【运营建议（本地模式）】\n"
            f"{stats_summary}\n\n"
            "建议：持续监控各功能模块调用量，优化客服知识库覆盖热门品类。"
        )
