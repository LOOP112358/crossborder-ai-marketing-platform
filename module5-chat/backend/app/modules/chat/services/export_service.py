from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def export_excel(stats: Dict[str, Any], trend: List[Dict[str, Any]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "运营看板"

    ws.append(["AI电商运营报告", datetime.now().strftime("%Y-%m-%d %H:%M")])
    ws.append([])
    ws.append(["指标", "数值"])
    ws.append(["总用户数", stats["total_users"]])
    ws.append(["今日总调用", stats["today_calls"]])
    ws.append([])
    ws.append(["功能模块", "调用次数", "占比(%)"])
    for name, count in stats["feature_usage"].items():
        ws.append([name, count, stats["feature_ratio"].get(name, 0)])

    ws.append([])
    ws.append(["热门品类", "数量"])
    for cat in stats["hot_categories"]:
        ws.append([cat["name"], cat["count"]])

    ws2 = wb.create_sheet("近7天趋势")
    ws2.append(["日期", "文案", "抠图", "背景", "海报", "客服", "错误"])
    for t in trend:
        ws2.append([
            t["stat_date"], t["writing_calls"], t["matte_calls"],
            t["bg_calls"], t["poster_calls"], t["chat_calls"], t["error_count"],
        ])

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_pdf(stats: Dict[str, Any], trend: List[Dict[str, Any]]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("AI电商运营数据报告", styles["Title"]))
    story.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), styles["Normal"]))
    story.append(Spacer(1, 12))

    overview = [
        ["总用户数", str(stats["total_users"])],
        ["今日总调用", str(stats["today_calls"])],
    ]
    t = Table(overview, colWidths=[200, 200])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    usage_data = [["功能", "调用量", "占比%"]]
    for name, count in stats["feature_usage"].items():
        usage_data.append([name, str(count), str(stats["feature_ratio"].get(name, 0))])
    t2 = Table(usage_data, colWidths=[150, 100, 100])
    t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(Paragraph("功能使用统计", styles["Heading2"]))
    story.append(t2)
    story.append(Spacer(1, 12))

    if stats["error_alerts"]:
        story.append(Paragraph("异常预警", styles["Heading2"]))
        for alert in stats["error_alerts"]:
            story.append(Paragraph(alert["message"], styles["Normal"]))

    doc.build(story)
    return buf.getvalue()
