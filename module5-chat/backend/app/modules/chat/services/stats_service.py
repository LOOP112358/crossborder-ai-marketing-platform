from datetime import date, timedelta
from typing import Any, Dict, List, Tuple

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.chat import (
    ChatFeedback,
    SystemDailyStat,
)


def _today() -> date:
    return date.today()


def _count_table_on(db: Session, table: str, day: date) -> int:
    try:
        row = db.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE date(created_at) = :d"),
            {"d": day.isoformat()},
        ).scalar()
        return int(row or 0)
    except Exception:
        return 0


def _count_table_since(db: Session, table: str, start: date) -> int:
    try:
        row = db.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE date(created_at) >= :d"),
            {"d": start.isoformat()},
        ).scalar()
        return int(row or 0)
    except Exception:
        return 0


def refresh_daily_stats(db: Session) -> SystemDailyStat:
    """从各历史表汇总今日统计并写入 system_daily_stats。"""
    today = _today()
    total_users = db.query(func.count(User.id)).scalar() or 0

    writing = _count_table_on(db, "history_writing", today)
    matte = _count_table_on(db, "history_matte", today)
    bg = _count_table_on(db, "history_background", today)
    poster = _count_table_on(db, "history_poster", today)
    chat = _count_table_on(db, "chat_messages", today) // 2
    errors = _count_table_on(db, "module_errors", today)

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


def get_trend_data(db: Session, days: int = 7) -> List[Dict[str, Any]]:
    start = _today() - timedelta(days=days - 1)
    refresh_daily_stats(db)
    for i in range(days):
        d = _today() - timedelta(days=i)
        existing = db.query(SystemDailyStat).filter(SystemDailyStat.stat_date == d).first()
        if existing:
            continue
        writing = _count_table_on(db, "history_writing", d)
        matte = _count_table_on(db, "history_matte", d)
        bg = _count_table_on(db, "history_background", d)
        poster = _count_table_on(db, "history_poster", d)
        chat = _count_table_on(db, "chat_messages", d) // 2
        errors = _count_table_on(db, "module_errors", d)
        if writing + matte + bg + poster + chat + errors == 0:
            continue
        db.add(
            SystemDailyStat(
                stat_date=d,
                total_users=db.query(func.count(User.id)).scalar() or 0,
                writing_calls=writing,
                matte_calls=matte,
                bg_calls=bg,
                poster_calls=poster,
                chat_calls=chat,
                error_count=errors,
            )
        )
    db.commit()

    rows = (
        db.query(SystemDailyStat)
        .filter(SystemDailyStat.stat_date >= start)
        .order_by(SystemDailyStat.stat_date)
        .all()
    )
    return [
        {
            "stat_date": r.stat_date.isoformat(),
            "writing_calls": r.writing_calls or 0,
            "matte_calls": r.matte_calls or 0,
            "bg_calls": r.bg_calls or 0,
            "poster_calls": r.poster_calls or 0,
            "chat_calls": r.chat_calls or 0,
            "error_count": r.error_count or 0,
            "total_calls": (
                (r.writing_calls or 0)
                + (r.matte_calls or 0)
                + (r.bg_calls or 0)
                + (r.poster_calls or 0)
                + (r.chat_calls or 0)
            ),
        }
        for r in rows
    ]


def _module_health(
    db: Session, today: date, feature_usage: Dict[str, int]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    modules = [
        ("writing", "文案生成", feature_usage.get("文案生成", 0)),
        ("matte", "商品抠图", feature_usage.get("商品抠图", 0)),
        ("background", "背景生成", feature_usage.get("背景生成", 0)),
        ("poster", "海报合成", feature_usage.get("海报合成", 0)),
        ("chat", "智能客服", feature_usage.get("智能客服", 0)),
    ]
    health: List[Dict[str, Any]] = []
    alerts: List[Dict[str, Any]] = []
    for module_key, module_name, calls in modules:
        err_count = db.execute(
            text(
                "SELECT COUNT(*) FROM module_errors WHERE module_name = :m AND date(created_at) = :d"
            ),
            {"m": module_key, "d": today.isoformat()},
        ).scalar() or 0
        total = calls + int(err_count)
        rate = (int(err_count) / total * 100) if total > 0 else 0.0
        status = "ok"
        if rate > 10:
            status = "critical"
            alerts.append(
                {
                    "module": module_name,
                    "error_rate": round(rate, 1),
                    "message": f"{module_name} 错误率 {rate:.1f}%，已超过 10% 预警阈值",
                }
            )
        elif rate > 5:
            status = "warn"
        health.append(
            {
                "key": module_key,
                "name": module_name,
                "calls": calls,
                "errors": int(err_count),
                "error_rate": round(rate, 1),
                "status": status,
            }
        )
    return health, alerts


def _recent_activity(db: Session, limit: int = 12) -> List[Dict[str, Any]]:
    sql = text(
        """
        SELECT * FROM (
            SELECT created_at AS ts, '文案生成' AS module, product_name AS detail, 'writing' AS kind
            FROM history_writing
            UNION ALL
            SELECT created_at, '商品抠图', COALESCE(category, '未分类'), 'matte'
            FROM history_matte
            UNION ALL
            SELECT created_at, '背景生成', COALESCE(style, product_category), 'background'
            FROM history_background
            UNION ALL
            SELECT created_at, '海报合成', COALESCE(title, '海报'), 'poster'
            FROM history_poster
            UNION ALL
            SELECT created_at, '智能客服', substr(content, 1, 40), 'chat'
            FROM chat_messages WHERE role = 'user'
        )
        ORDER BY ts DESC
        LIMIT :lim
        """
    )
    try:
        rows = db.execute(sql, {"lim": limit}).fetchall()
    except Exception:
        return []
    out = []
    for r in rows:
        ts = r[0]
        out.append(
            {
                "time": str(ts)[5:16] if ts else "",
                "module": r[1],
                "detail": (r[2] or "")[:48],
                "kind": r[3],
            }
        )
    return out


def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    today = _today()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=6)

    stat = refresh_daily_stats(db)
    feature_usage = {
        "文案生成": stat.writing_calls,
        "商品抠图": stat.matte_calls,
        "背景生成": stat.bg_calls,
        "海报合成": stat.poster_calls,
        "智能客服": stat.chat_calls,
    }
    total_calls = sum(feature_usage.values())
    denom = total_calls or 1
    feature_ratio = {k: round(v / denom * 100, 1) for k, v in feature_usage.items()}

    y_writing = _count_table_on(db, "history_writing", yesterday)
    y_matte = _count_table_on(db, "history_matte", yesterday)
    y_bg = _count_table_on(db, "history_background", yesterday)
    y_poster = _count_table_on(db, "history_poster", yesterday)
    y_chat = _count_table_on(db, "chat_messages", yesterday) // 2
    yesterday_calls = y_writing + y_matte + y_bg + y_poster + y_chat

    week_writing = _count_table_since(db, "history_writing", week_start)
    week_matte = _count_table_since(db, "history_matte", week_start)
    week_bg = _count_table_since(db, "history_background", week_start)
    week_poster = _count_table_since(db, "history_poster", week_start)
    week_chat = _count_table_since(db, "chat_messages", week_start) // 2
    week_calls = week_writing + week_matte + week_bg + week_poster + week_chat

    delta = total_calls - yesterday_calls
    delta_pct = round((delta / yesterday_calls) * 100, 1) if yesterday_calls else None

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
            hot_from_abo = db.execute(
                text(
                    "SELECT product_type AS name, COUNT(*) AS cnt FROM abo_products "
                    "WHERE product_type IS NOT NULL AND product_type != '' "
                    "GROUP BY product_type ORDER BY cnt DESC LIMIT 10"
                )
            ).fetchall()
            hot_categories = [{"name": r[0], "count": r[1]} for r in hot_from_abo]
        except Exception:
            hot_categories = []

    max_cat = max((c["count"] for c in hot_categories), default=1)
    for c in hot_categories:
        c["ratio"] = round(c["count"] / max_cat * 100, 1)

    platforms = []
    try:
        rows = db.execute(
            text(
                """
                SELECT COALESCE(platform, '未标注') AS name, COUNT(*) AS cnt
                FROM history_writing
                GROUP BY COALESCE(platform, '未标注')
                ORDER BY cnt DESC
                LIMIT 8
                """
            )
        ).fetchall()
        platforms = [{"name": r[0], "count": r[1]} for r in rows]
    except Exception:
        platforms = []

    funnel = [
        {"step": "商品抠图", "count": week_matte, "key": "matte"},
        {"step": "背景生成", "count": week_bg, "key": "background"},
        {"step": "海报合成", "count": week_poster, "key": "poster"},
    ]
    base = funnel[0]["count"] or 1
    for i, step in enumerate(funnel):
        step["ratio"] = round(step["count"] / base * 100, 1)
        if i > 0:
            prev = funnel[i - 1]["count"] or 1
            step["conversion"] = round(step["count"] / prev * 100, 1)
        else:
            step["conversion"] = 100.0

    module_health, error_alerts = _module_health(db, today, feature_usage)

    likes = db.query(func.count(ChatFeedback.id)).filter(ChatFeedback.feedback_type == "like").scalar() or 0
    dislikes = db.query(func.count(ChatFeedback.id)).filter(ChatFeedback.feedback_type == "dislike").scalar() or 0
    fb_total = likes + dislikes
    satisfaction = round(likes / fb_total * 100, 1) if fb_total else 100.0

    sessions = 0
    try:
        sessions = int(db.execute(text("SELECT COUNT(*) FROM chat_sessions")).scalar() or 0)
    except Exception:
        sessions = 0

    posters = 0
    try:
        posters = int(db.execute(text("SELECT COUNT(*) FROM history_poster")).scalar() or 0)
    except Exception:
        posters = 0

    return {
        "total_users": stat.total_users,
        "today_calls": total_calls,
        "yesterday_calls": yesterday_calls,
        "week_calls": week_calls,
        "delta_calls": delta,
        "delta_pct": delta_pct,
        "feature_usage": feature_usage,
        "feature_ratio": feature_ratio,
        "week_feature_usage": {
            "文案生成": week_writing,
            "商品抠图": week_matte,
            "背景生成": week_bg,
            "海报合成": week_poster,
            "智能客服": week_chat,
        },
        "hot_categories": hot_categories,
        "platforms": platforms,
        "funnel": funnel,
        "module_health": module_health,
        "error_alerts": error_alerts,
        "chat_feedback_stats": {"like": likes, "dislike": dislikes},
        "satisfaction": satisfaction,
        "chat_sessions": sessions,
        "poster_total": posters,
        "recent_activity": _recent_activity(db),
        "updated_at": str(stat.stat_date),
    }


def build_advice_summary(db: Session) -> str:
    stats = get_dashboard_stats(db)
    trend = get_trend_data(db)
    lines = [
        "=== 平台角色说明 ===",
        "商家端工具（店家使用）：文案生成、商品抠图、背景生成、海报合成 —— 这些是帮助商家制作商品海报的工作流",
        "顾客端工具（消费者使用）：智能客服 —— 这是面向终端消费者的商品问答助手",
        "",
        f"总用户数：{stats['total_users']}",
        f"今日总调用：{stats['today_calls']}（较昨日 {stats.get('delta_calls', 0):+d}）",
        f"近7日总调用：{stats.get('week_calls', 0)}",
        "各功能使用量：" + ", ".join(f"{k}={v}" for k, v in stats["feature_usage"].items()),
        "热门品类：" + (", ".join(c["name"] for c in stats["hot_categories"][:5]) or "暂无"),
        f"客服点赞/点踩：{stats['chat_feedback_stats']['like']}/{stats['chat_feedback_stats']['dislike']}",
        f"满意度：{stats.get('satisfaction', 100)}%",
    ]
    if stats.get("funnel"):
        lines.append(
            "海报漏斗：" + " → ".join(f"{s['step']}={s['count']}" for s in stats["funnel"])
        )
    if trend:
        lines.append(f"近7天总调用趋势：{[t.get('total_calls', 0) for t in trend]}")
    if stats["error_alerts"]:
        lines.append("异常预警：" + "; ".join(a["message"] for a in stats["error_alerts"]))
    return "\n".join(lines)
