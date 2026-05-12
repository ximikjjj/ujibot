from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from datetime import date
from database import get_db
from models import User, Suggestion, Goal, CommunicationStat, DailyDigest
from ai_service import analyze_message, generate_daily_digest, chat_with_ai
from telethon_worker import (
    start_auth_request_code,
    complete_auth_with_code,
    active_clients,
)
import asyncio

router = APIRouter(prefix="/bot-api")

live_ws_connections: dict[int, list[WebSocket]] = {}


class AnalyzeRequest(BaseModel):
    telegram_id: int
    message: str
    context: list[dict] | None = None


class AuthPhoneRequest(BaseModel):
    telegram_id: int
    phone: str


class AuthCodeRequest(BaseModel):
    telegram_id: int
    code: str
    password: str | None = None


class GoalRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    telegram_id: int
    message: str
    history: list[dict] | None = None


@router.get("/healthz")
async def health():
    return {"status": "ok"}


@router.post("/analyze")
async def analyze(req: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == req.telegram_id))
    user = result.scalar_one_or_none()

    goals = []
    if user:
        g_result = await db.execute(
            select(Goal).where(Goal.user_id == req.telegram_id, Goal.is_active == True)
        )
        goals = [g.text for g in g_result.scalars().all()]

    analysis = await analyze_message(req.message, req.context, goals)

    if user:
        suggestion = Suggestion(
            user_id=req.telegram_id,
            incoming_message=req.message,
            analysis=analysis.get("analysis"),
            variants=analysis.get("variants", []),
            tone=analysis.get("tone")
        )
        db.add(suggestion)

        scales = analysis.get("scales")
        if scales:
            stat = CommunicationStat(
                user_id=req.telegram_id,
                confidence=int(scales.get("confidence", 50)),
                ease=int(scales.get("ease", 50)),
                tension=int(scales.get("tension", 50)),
                initiative=int(scales.get("initiative", 50)),
                warmth=int(scales.get("warmth", 50)),
                clarity=int(scales.get("clarity", 50)),
            )
            db.add(stat)

        await db.commit()

    if req.telegram_id in live_ws_connections:
        for ws in live_ws_connections[req.telegram_id]:
            try:
                await ws.send_json({"type": "suggestion", "data": analysis, "message": req.message})
            except Exception:
                pass

    return analysis


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        reply = await chat_with_ai(req.message, req.history)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{telegram_id}")
async def get_user(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "phone": user.phone,
        "is_session_active": user.is_session_active and telegram_id in active_clients,
        "created_at": user.created_at.isoformat()
    }


@router.get("/user/{telegram_id}/stats")
async def get_stats(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CommunicationStat)
        .where(CommunicationStat.user_id == telegram_id)
        .order_by(desc(CommunicationStat.recorded_at))
        .limit(1)
    )
    stat = result.scalar_one_or_none()

    if not stat:
        return {"confidence": None, "ease": None, "tension": None,
                "initiative": None, "warmth": None, "clarity": None, "no_data": True}

    return {
        "confidence": stat.confidence,
        "ease": stat.ease,
        "tension": stat.tension,
        "initiative": stat.initiative,
        "warmth": stat.warmth,
        "clarity": stat.clarity,
        "recorded_at": stat.recorded_at.isoformat(),
        "no_data": False,
    }


@router.get("/user/{telegram_id}/suggestions")
async def get_suggestions(telegram_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Suggestion)
        .where(Suggestion.user_id == telegram_id)
        .order_by(desc(Suggestion.created_at))
        .limit(limit)
    )
    suggestions = result.scalars().all()

    return [
        {
            "id": s.id,
            "incoming_message": s.incoming_message,
            "analysis": s.analysis,
            "variants": s.variants,
            "tone": s.tone,
            "created_at": s.created_at.isoformat()
        }
        for s in suggestions
    ]


@router.get("/user/{telegram_id}/goals")
async def get_goals(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Goal).where(Goal.user_id == telegram_id, Goal.is_active == True)
    )
    goals = result.scalars().all()
    return [{"id": g.id, "text": g.text, "progress_count": g.progress_count} for g in goals]


@router.post("/user/{telegram_id}/goals")
async def add_goal(telegram_id: int, req: GoalRequest, db: AsyncSession = Depends(get_db)):
    goal = Goal(user_id=telegram_id, text=req.text)
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return {"id": goal.id, "text": goal.text, "progress_count": 0}


@router.delete("/user/{telegram_id}/goals/{goal_id}")
async def delete_goal(telegram_id: int, goal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == telegram_id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    goal.is_active = False
    await db.commit()
    return {"success": True}


@router.get("/user/{telegram_id}/digest")
async def get_digest(telegram_id: int, db: AsyncSession = Depends(get_db)):
    today = date.today().isoformat()
    result = await db.execute(
        select(DailyDigest).where(
            DailyDigest.user_id == telegram_id,
            DailyDigest.date == today
        )
    )
    digest = result.scalar_one_or_none()

    if not digest:
        s_result = await db.execute(
            select(Suggestion)
            .where(Suggestion.user_id == telegram_id)
            .order_by(desc(Suggestion.created_at))
            .limit(30)
        )
        suggestions_today = s_result.scalars().all()

        g_result = await db.execute(
            select(Goal).where(Goal.user_id == telegram_id, Goal.is_active == True)
        )
        goals = [g.text for g in g_result.scalars().all()]

        suggestions_data = [
            {"incoming": s.incoming_message, "tone": s.tone}
            for s in suggestions_today
        ]

        digest_data = await generate_daily_digest(telegram_id, suggestions_data, goals)

        digest = DailyDigest(
            user_id=telegram_id,
            date=today,
            **digest_data
        )
        db.add(digest)
        await db.commit()
        await db.refresh(digest)

    return {
        "date": digest.date,
        "what_worked": digest.what_worked,
        "near_misses": digest.near_misses,
        "best_reply": digest.best_reply,
        "funniest_moment": digest.funniest_moment,
        "dead_dialogs": digest.dead_dialogs or [],
        "goals_progress": digest.goals_progress or {}
    }


@router.post("/session/start")
async def session_start(req: AuthPhoneRequest):
    try:
        result = await start_auth_request_code(req.telegram_id, req.phone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/session/verify")
async def session_verify(req: AuthCodeRequest):
    result = await complete_auth_with_code(req.telegram_id, req.code, req.password)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/session/status/{telegram_id}")
async def session_status(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    is_live = telegram_id in active_clients
    return {
        "telegram_id": telegram_id,
        "is_connected": is_live,
        "has_session": bool(user and user.telethon_session) if user else False,
        "phone": user.phone if user else None
    }


@router.websocket("/ws/{telegram_id}")
async def websocket_endpoint(websocket: WebSocket, telegram_id: int):
    await websocket.accept()

    if telegram_id not in live_ws_connections:
        live_ws_connections[telegram_id] = []
    live_ws_connections[telegram_id].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if telegram_id in live_ws_connections:
            try:
                live_ws_connections[telegram_id].remove(websocket)
            except ValueError:
                pass
            if not live_ws_connections[telegram_id]:
                del live_ws_connections[telegram_id]
