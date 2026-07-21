"""运营看板 — 成员5原始逻辑 + JWT + _ok包装"""
import asyncio, json
from datetime import datetime
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.models.user import User
from app.core.database import get_db, SessionLocal
from app.modules.chat.services.stats_service import get_dashboard_stats,get_trend_data,build_advice_summary,refresh_daily_stats
from app.modules.chat.services.llm_service import generate_operation_advice
from app.modules.chat.services.export_service import export_excel,export_pdf

def _ok(d=None,m="success"):return{"code":200,"message":m,"data":d}
router=APIRouter(prefix="/api/dashboard",tags=["dashboard"])

@router.get("/stats")
def api_stats(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return _ok(get_dashboard_stats(db))

@router.get("/trend")
def api_trend(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    return _ok(get_trend_data(db))

@router.get("/advice")
async def api_advice(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    summary=build_advice_summary(db);advice=await generate_operation_advice(summary)
    return _ok({"advice":advice,"generated_at":str(datetime.utcnow())})

@router.get("/export/excel")
def api_export_xl(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    stats=get_dashboard_stats(db);trend=get_trend_data(db);data=export_excel(stats,trend)
    return Response(content=data,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":"attachment; filename=dashboard_report.xlsx"})

@router.get("/export/pdf")
def api_export_pdf(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    stats=get_dashboard_stats(db);trend=get_trend_data(db);data=export_pdf(stats,trend)
    return Response(content=data,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=dashboard_report.pdf"})

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
    except (WebSocketDisconnect, asyncio.CancelledError):
        # Ctrl+C / 服务关闭时会取消任务，直接退出即可
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
