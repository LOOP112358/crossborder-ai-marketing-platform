import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from ..schemas import DashboardStats, TrendPoint, AdviceResponse
from ..services.stats_service import (
    get_dashboard_stats, get_trend_data, build_advice_summary, refresh_daily_stats,
)
from ..services.llm_service import generate_operation_advice
from ..services.export_service import export_excel, export_pdf

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)


@router.get("/trend", response_model=list[TrendPoint])
def dashboard_trend(db: Session = Depends(get_db)):
    return get_trend_data(db)


@router.get("/advice", response_model=AdviceResponse)
async def dashboard_advice(db: Session = Depends(get_db)):
    summary = build_advice_summary(db)
    advice = await generate_operation_advice(summary)
    return AdviceResponse(advice=advice, generated_at=datetime.utcnow())


@router.get("/export/excel")
def export_dashboard_excel(db: Session = Depends(get_db)):
    stats = get_dashboard_stats(db)
    trend = get_trend_data(db)
    data = export_excel(stats, trend)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dashboard_report.xlsx"},
    )


@router.get("/export/pdf")
def export_dashboard_pdf(db: Session = Depends(get_db)):
    stats = get_dashboard_stats(db)
    trend = get_trend_data(db)
    data = export_pdf(stats, trend)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=dashboard_report.pdf"},
    )


@router.websocket("/ws")
async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            try:
                refresh_daily_stats(db)
                stats = get_dashboard_stats(db)
                await websocket.send_text(json.dumps(stats, ensure_ascii=False, default=str))
            finally:
                db.close()
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
