"""FastAPI application for Campus AI — TNEA Counselling Recommendation System."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .chatbot import clear_session, get_session, process_message
from .data import DATASET, calculate_cutoff
from .nlp import detect_branch as normalize_branch

APP_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = APP_DIR.parents[1] / "frontend" / "dist"

app = FastAPI(
    title="Campus AI — TNEA Counselling API",
    description="Dataset-grounded TNEA college recommendation chatbot, cutoff calculator and college finder.",
    version="6.7.0",
)

origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CutoffRequest(BaseModel):
    mathematics: float = Field(ge=0, le=100)
    physics: float = Field(ge=0, le=100)
    chemistry: float = Field(ge=0, le=100)


class RecommendRequest(BaseModel):
    cutoff: float = Field(ge=0, le=200)
    community: str = "OC"
    district: str = "ALL"
    branch: str = "ALL"
    search: str = ""
    include_na: bool = True
    limit: int = Field(default=10000, ge=1, le=10000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    session_id: Optional[str] = None
    cutoff: Optional[float] = Field(default=None, ge=0, le=200)
    community: Optional[str] = None
    district: Optional[str] = None
    branch: Optional[str] = None
    profile: Optional[dict] = None
    history: Optional[list] = None


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "campus-ai",
        "version": "6.7.0",
        **DATASET.stats(),
    }


@app.get("/api/config")
def config():
    from .chatbot import GROQ_KEY, GROQ_MODEL
    return {
        "llm_enabled": bool(GROQ_KEY),
        "llm_provider": "Groq" if GROQ_KEY else "deterministic NLP + dataset retrieval",
        "model": GROQ_MODEL if GROQ_KEY else None,
        "official_tnea": "https://www.tneaonline.org/",
        "dataset_year": 2025,
        "official_process_year": 2026,
    }


@app.get("/api/meta")
def meta():
    return {
        "records": DATASET.meta["record_count"],
        "colleges": DATASET.meta["college_count"],
        "districts": DATASET.district_set,
        "branches": DATASET.branch_set,
        "communities": DATASET.stats()["communities"],
        "formula": "Mathematics + Physics/2 + Chemistry/2",
        "data_fields": [
            "COLLEGE_CODE", "COLLEGE_NAME", "DISTRICT", "BRANCH_NAME",
            "BRANCH_CODE", "OC", "BC", "BCM", "MBC", "SC", "SCA", "ST", "RECORD_ID",
        ],
    }


@app.get("/api/stats")
def stats():
    return DATASET.stats()


@app.post("/api/calculate-cutoff")
def calculate(req: CutoffRequest):
    value = calculate_cutoff(req.mathematics, req.physics, req.chemistry)
    return {
        "cutoff": value,
        "formula": "Mathematics + Physics/2 + Chemistry/2",
        "breakdown": {
            "mathematics": req.mathematics,
            "physics_half": round(req.physics / 2, 2),
            "chemistry_half": round(req.chemistry / 2, 2),
        },
    }


@app.post("/api/recommend")
def recommend(req: RecommendRequest):
    community = req.community.upper().strip()
    if community not in DATASET.stats()["communities"]:
        raise HTTPException(400, "Unsupported community. Use OC, BC, BCM, MBC, SC, SCA or ST.")
    branch = req.branch.strip() or "ALL"
    if branch != "ALL":
        resolved = normalize_branch(branch, DATASET.branch_set)
        if resolved:
            branch = resolved
        else:
            # Fall back to uppercase contains-match semantics used by the engine.
            branch = branch.upper()
    result = DATASET.recommend(
        cutoff=req.cutoff,
        community=community,
        district=req.district,
        branch=branch,
        search=req.search,
        include_na=req.include_na,
        limit=req.limit,
    )
    return {
        "message": "All eligible records returned. Records without a published cutoff for this community are shown separately and never hidden.",
        "resolved_branch": branch if branch != "ALL" else None,
        **result,
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    sess = get_session(req.session_id)

    # Pre-seed profile from the request (frontend keeps it in sync).
    if req.cutoff is not None:
        sess.profile["cutoff"] = req.cutoff
    if req.community:
        sess.profile["community"] = req.community.upper()
    if req.district:
        sess.profile["district"] = req.district.upper()
    if req.branch:
        sess.profile["branch"] = req.branch.upper()

    client_profile = dict(req.profile or {})
    if req.cutoff is not None: client_profile["cutoff"] = req.cutoff
    if req.community: client_profile["community"] = req.community
    if req.district: client_profile["district"] = req.district
    if req.branch: client_profile["branch"] = req.branch
    return process_message(sess.id, req.message, client_profile=client_profile, client_history=req.history)


@app.post("/api/chat/reset")
def chat_reset(req: dict):
    session_id = req.get("session_id", "")
    clear_session(session_id)
    return {"status": "ok", "session_id": None}


# Serve the built frontend when available (same-origin deployment).
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
