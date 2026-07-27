from datetime import date, timedelta
from typing import Any, Dict, List

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.chat import (
    ChatFeedback,
    SystemDailyStat,
    ModuleError,
)


def _today() -> date:
    return date.today()


def _count_on_date(db: Session, table: str, day: date, *, half: bool = False) -> int:
    """按自然日从业务历史表计数（不依赖可能过期的 system_daily_stats 快照）。"""
    try:
        row = db.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE date(created_at) = :d"),
            {"d": day.isoformat()},
        ).scalar()
        n = int(row or 0)
        return n // 2 if half else n
    except Exception:
        return 0


def refresh_daily_stats(db: Session) -> SystemDailyStat:
    """从各历史表汇总今日统计并写入 system_daily_stats。"""
    today = _today()
    total_users = db.query(func.count(User.id)).scalar() or 0

    writing = _count_on_date(db, "history_writing", today)
    matte = _count_on_date(db, "history_matte", today)
    bg = _count_on_date(db, "history_background", today)
    poster = _count_on_date(db, "history_poster", today)
    chat = _count_on_date(db, "chat_messages", today, half=True)  # user+assistant 算一次
    errors = _count_on_date(db, "module_errors", today)

    stat = db.query(SystemDailyStat).filter(SystemDailyStat.stat_date == today).first()
    if not stat:
        stat = SystemDailyStat(stat_date=today)
        db.add(stat)

    stat.total_users = total_users
    stat.writing_calls = writing
    stat.matte_calls = matte
    stat.bg_calls = bg
    stat.poster_calls = poster
    stat.chat_calls = chat
    stat.error_count = int(errors)
    db.commit()
    db.refresh(stat)
    return stat


def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    stat = refresh_daily_stats(db)
    feature_usage = {
        "文案生成": stat.writing_calls,
        "商品抠图": stat.matte_calls,
        "背景生成": stat.bg_calls,
        "海报合成": stat.poster_calls,
        "智能客服": stat.chat_calls,
    }
    total_calls = sum(feature_usage.values()) or 1
    feature_ratio = {k: round(v / total_calls * 100, 1) for k, v in feature_usage.items()}

    # 热门品类：优先从抠图/背景历史，fallback ABO product_type
    hot_from_matte = db.execute(
        text(
            """
            SELECT category AS name, COUNT(*) AS cnt
            FROM history_matte
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY cnt DESC
            LIMIT 10
            """
        )
    ).fetchall()

    if hot_from_matte:
        hot_categories = [{"name": r[0], "count": r[1]} for r in hot_from_matte]
    else:
        try:
            hot_from_abo = db.execute(text(
                "SELECT product_type AS name, COUNT(*) AS cnt FROM abo_products WHERE product_type IS NOT NULL AND product_type != '' GROUP BY product_type ORDER BY cnt DESC LIMIT 10"
            )).fetchall()
            hot_categories = [{"name": r[0], "count": r[1]} for r in hot_from_abo]
        except Exception:
            hot_categories = []

    # 异常预警：各模块错误率 > 10%
    error_alerts = []
    modules = [
        ("writing", "文案生成", stat.writing_calls),
        ("matte", "商品抠图", stat.matte_calls),
        ("background", "背景生成", stat.bg_calls),
        ("poster", "海报合成", stat.poster_calls),
        ("chat", "智能客服", stat.chat_calls),
    ]
    for module_key, module_name, calls in modules:
        err_count = db.execute(
            text(
                "SELECT COUNT(*) FROM module_errors WHERE module_name = :m AND date(created_at) = :d"
            ),
            {"m": module_key, "d": _today().isoformat()},
        ).scalar() or 0
        total = calls + err_count
        rate = (err_count / total * 100) if total > 0 else 0
        if rate > 10:
            error_alerts.append(
                {
                    "module": module_name,
                    "error_rate": round(rate, 1),
                    "message": f"{module_name} 错误率 {rate:.1f}%，已超过 10% 预警阈值",
                }
            )

    likes = db.query(func.count(ChatFeedback.id)).filter(ChatFeedback.feedback_type == "like").scalar() or 0
    dislikes = db.query(func.count(ChatFeedback.id)).filter(ChatFeedback.feedback_type == "dislike").scalar() or 0

    return {
        "total_users": stat.total_users,
        "today_calls": total_calls,
        "feature_usage": feature_usage,
        "feature_ratio": feature_ratio,
        "hot_categories": hot_categories,
        "error_alerts": error_alerts,
        "chat_feedback_stats": {"like": likes, "dislike": dislikes},
    }


def get_trend_data(db: Session, days: int = 7) -> List[Dict[str, Any]]:
    """近 N 天趋势：直接汇总各历史表，保证抠图/背景/海报等已写入记录都能显示。"""
    today = _today()
    result: List[Dict[str, Any]] = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        writing = _count_on_date(db, "history_writing", day)
        matte = _count_on_date(db, "history_matte", day)
        bg = _count_on_date(db, "history_background", day)
        poster = _count_on_date(db, "history_poster", day)
        chat = _count_on_date(db, "chat_messages", day, half=True)
        errors = _count_on_date(db, "module_errors", day)
        # 顺带回写当日快照，导出/旧逻辑仍可读
        stat = db.query(SystemDailyStat).filter(SystemDailyStat.stat_date == day).first()
        if not stat:
            stat = SystemDailyStat(stat_date=day)
            db.add(stat)
        if day == today:
            stat.total_users = db.query(func.count(User.id)).scalar() or 0
        stat.writing_calls = writing
        stat.matte_calls = matte
        stat.bg_calls = bg
        stat.poster_calls = poster
        stat.chat_calls = chat
        stat.error_count = errors
        result.append(
            {
                "stat_date": day.isoformat(),
                "writing_calls": writing,
                "matte_calls": matte,
                "bg_calls": bg,
                "poster_calls": poster,
                "chat_calls": chat,
                "error_count": errors,
            }
        )
    db.commit()
    return result


def build_advice_summary(db: Session) -> str:
    stats = get_dashboard_stats(db)
    trend = get_trend_data(db)
    lines = [
        "=== 平台角色说明 ===",
        "商家端工具（店家使用）：文案生成、商品抠图、背景生成、海报合成 —— 这些是帮助商家制作商品海报的工作流",
        "顾客端工具（消费者使用）：智能客服 —— 这是面向终端消费者的商品问答助手",
        "",
        f"总用户数：{stats['total_users']}",
        f"今日总调用：{stats['today_calls']}",
        "各功能使用量：" + ", ".join(f"{k}={v}" for k, v in stats["feature_usage"].items()),
        "热门品类：" + ", ".join(c["name"] for c in stats["hot_categories"][:5]) or "暂无",
        f"客服点赞/点踩：{stats['chat_feedback_stats']['like']}/{stats['chat_feedback_stats']['dislike']}",
    ]
    if trend:
        lines.append(f"近7天客服调用趋势：{[t['chat_calls'] for t in trend]}")
    if stats["error_alerts"]:
        lines.append("异常预警：" + "; ".join(a["message"] for a in stats["error_alerts"]))
    return "\n".join(lines)
