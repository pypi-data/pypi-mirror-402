import json
import asyncio
import os
from typing import Any
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from .sessions import DurableSessionService
from google.genai.types import Content, Part
from .ipc_auth import TOKEN_STORE
from .agent import get_root_agent
from .distillation import capture_engine
from .tracing import setup_tracing

# Initialize tracing early
setup_tracing()

app = FastAPI(title="OneCoder Agent API")

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
from .alignment import auto_detect_sprint_id

# Mount static files for web UI
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Setup ADK session service
session_service = DurableSessionService()

@app.get("/")
async def root(token: str | None = None):
    """Root endpoint - redirects to web UI if token provided."""
    if token:
        return RedirectResponse(url=f"/static/index.html?token={token}")
    return {
        "message": "OneCoder API",
        "version": "0.1.0",
        "endpoints": {
            "web_ui": "/static/index.html?token=<token>",
            "chat": "POST /chat",
            "stream": "GET /stream",
        },
    }


async def verify_token(request: Request):
    """
    Middleware-like dependency to verify session-based tokens.
    The token can be passed in 'Authorization: Bearer <token>' or '?token=<token>'.
    """
    token = request.query_params.get("token")
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token or not TOKEN_STORE.validate_token(token):
        raise HTTPException(
            status_code=401, detail="Unauthorized: Invalid or expired token"
        )


@app.post("/chat")
async def chat(user_id: str, session_id: str, message: str, sprint_id: str | None = None, _=Depends(verify_token)):
    """
    Standard synchronous chat endpoint (returns full response).
    """
    session = await session_service.get_session(
        app_name="onecoder-unified-api", user_id=user_id, session_id=session_id
    )
    if not session:
        session = await session_service.create_session(
            app_name="onecoder-unified-api", user_id=user_id, session_id=session_id
        )

    # Contextual Agent & Runner
    effective_sprint_id = sprint_id or auto_detect_sprint_id()
    if effective_sprint_id:
        os.environ["ACTIVE_SPRINT_ID"] = effective_sprint_id
        
    os.environ["ACTIVE_SESSION_ID"] = session_id

    agent = get_root_agent(effective_sprint_id)
    local_runner = Runner(
        session_service=session_service, 
        agent=agent, 
        app_name="onecoder-unified-api"
    )

    final_text = ""
    async for event in local_runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=Content(parts=[Part(text=message)], role="user"),
    ):
        if hasattr(event, "content") and event.content and event.content.parts:
            text_part = next((part for part in event.content.parts if part.text), None)
            if text_part and text_part.text:
                final_text += text_part.text

    return {"response": final_text}


@app.get("/stream")
async def stream(user_id: str, session_id: str, message: str, token: str, sprint_id: str | None = None):
    """
    SSE endpoint for streaming agent responses and events.
    FastAPI handles StreamingResponse well for this.
    Note: Token validation is done inside since SSE doesn't always support headers easily.
    """
    if not TOKEN_STORE.validate_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    session = await session_service.get_session(
        app_name="onecoder-unified-api", user_id=user_id, session_id=session_id
    )
    if not session:
        session = await session_service.create_session(
            app_name="onecoder-unified-api", user_id=user_id, session_id=session_id
        )

    # Contextual Agent & Runner
    effective_sprint_id = sprint_id or auto_detect_sprint_id()
    if effective_sprint_id:
        os.environ["ACTIVE_SPRINT_ID"] = effective_sprint_id

    os.environ["ACTIVE_SESSION_ID"] = session_id

    agent = get_root_agent(effective_sprint_id)
    local_runner = Runner(
        session_service=session_service, 
        agent=agent, 
        app_name="onecoder-unified-api"
    )

    async def event_generator():
        capture_engine.start_session(session_id)
        try:
            async for event in local_runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=Content(parts=[Part(text=message)], role="user"),
            ):
                # Format event for SSE
                event_data: dict[str, str | dict[str, Any] | None] = {
                    "type": type(event).__name__,
                }

                if hasattr(event, "content") and event.content and event.content.parts:
                    text_part = next(
                        (part for part in event.content.parts if part.text), None
                    )
                    if text_part and text_part.text:
                        event_data["text"] = text_part.text

                    # Capture tool calls or delegation events if present
                    tool_call = next(
                        (part for part in event.content.parts if part.function_call),
                        None,
                    )
                    if tool_call and tool_call.function_call:
                        event_data["tool_call"] = {
                            "name": tool_call.function_call.name,
                            "args": tool_call.function_call.args,
                        }

                capture_engine.log_event(event_data)
                yield f"data: {json.dumps(event_data)}\n\n"
            
            capture_engine.save_session()
        except Exception as e:
            yield f"data: {json.dumps({'type': 'Error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Evals & Analytics Endpoints
from .evaluation.evals_engine import EvalsEngine
evals_engine = EvalsEngine()

@app.get("/evals/summary")
async def get_evals_summary(sprint_id: str | None = None, _=Depends(verify_token)):
    """Returns aggregate metrics for the specified sprint."""
    return evals_engine.get_summary_metrics(sprint_id)

@app.get("/evals/traces/{session_id}")
async def get_session_traces(session_id: str, _=Depends(verify_token)):
    """Returns all traces/events for a specific session."""
    return {
        "session_id": session_id,
        "traces": evals_engine.get_consolidated_trace(session_id)
    }

@app.get("/evals/performance")
async def get_performance_trends(sprint_id: str | None = None, _=Depends(verify_token)):
    """Returns performance trends (TTU/TTR, Costs)."""
    # Simply reuse summary for now, or add more trend-specific logic in EvalsEngine
    summary = evals_engine.get_summary_metrics(sprint_id)
    return {
        "sprint_id": sprint_id,
        "metrics": summary,
        "recommendations": [
            "Consider optimizing prompts if TTU > 120s",
            "Check tool usage patterns for cost spikes"
        ]
    }

# ------------------------------------------------------------------------
# Arena API (Proof of Concept)
# ------------------------------------------------------------------------
# This section mocks the Arena endpoints as defined in docs/roadmap/Coder-LM-Arena-Assessment.md
# Real implementation will move this to a dedicated router (onecoder.arena.api).

@app.post("/arena/challenge/submit")
async def submit_challenge(challenge_id: str, agent_id: str, code: str, _=Depends(verify_token)):
    """
    Submits a solution to a challenge.
    In the future, this will trigger the SandboxRunner in OneSDK.
    """
    return {
        "status": "queued",
        "job_id": f"job-{challenge_id}-{agent_id}",
        "message": "Solution queued for sandbox execution."
    }

@app.get("/arena/leaderboard")
async def get_leaderboard(track: str | None = None):
    """
    Returns the current leaderboard.
    """
    # Mock data
    return {
        "track": track or "global",
        "rankings": [
            {"rank": 1, "agent": "claude-3-opus", "elo": 1250},
            {"rank": 2, "agent": "gpt-4o", "elo": 1245},
            {"rank": 3, "agent": "llama-3-70b", "elo": 1180}
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
