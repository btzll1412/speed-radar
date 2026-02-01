"""
Speed Radar Hub - Main FastAPI Application
Central hub for managing multiple speed radar units
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import database as db
from .mqtt import MQTTClient

# Configuration from environment
INGRESS_PATH = os.environ.get("INGRESS_PATH", "")
EXTERNAL_URL = os.environ.get("EXTERNAL_URL", "")  # e.g., https://smart.rosenberg21.com
INTERNAL_URL = os.environ.get("INTERNAL_URL", "")  # e.g., http://192.168.3.100:8123
MQTT_HOST = os.environ.get("MQTT_HOST", "core-mosquitto")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")
DATA_RETENTION_DAYS = int(os.environ.get("DATA_RETENTION_DAYS", 30))

# MQTT client instance
mqtt_client: Optional[MQTTClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    global mqtt_client

    # Initialize database
    db.init_database()

    # Connect to MQTT
    mqtt_client = MQTTClient(
        host=MQTT_HOST,
        port=MQTT_PORT,
        username=MQTT_USERNAME if MQTT_USERNAME else None,
        password=MQTT_PASSWORD if MQTT_PASSWORD else None
    )
    await mqtt_client.connect()

    # Publish discovery for existing radars
    for radar in db.get_all_radars():
        await mqtt_client.publish_discovery(radar)

    # Start cleanup task
    asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown
    if mqtt_client:
        await mqtt_client.disconnect()


async def periodic_cleanup():
    """Periodically clean up old data."""
    while True:
        await asyncio.sleep(3600)  # Every hour
        db.cleanup_old_data(DATA_RETENTION_DAYS)


# Create FastAPI app
app = FastAPI(
    title="Speed Radar Hub",
    description="Central hub for managing speed radar units",
    version="1.0.0",
    lifespan=lifespan
)

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_url(path: str) -> str:
    """Get full URL with ingress path prefix."""
    return f"{INGRESS_PATH}{path}"


# ============================================================
# Web UI Routes
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard showing all radars."""
    radars = db.get_all_radars()

    # Add latest stats to each radar
    for radar in radars:
        radar["stats"] = db.get_latest_stats(radar["id"]) or {}
        radar["config"] = json.loads(radar.get("config", "{}"))
        # Check if online (seen in last 5 minutes)
        if radar.get("last_seen"):
            last_seen = datetime.fromisoformat(radar["last_seen"])
            radar["online"] = (datetime.now() - last_seen).seconds < 300
        else:
            radar["online"] = False

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "radars": radars,
        "ingress_path": INGRESS_PATH
    })


@app.get("/radar/{radar_id}", response_class=HTMLResponse)
async def radar_detail(request: Request, radar_id: int):
    """Detailed view for a single radar."""
    radar = db.get_radar_by_id(radar_id)
    if not radar:
        raise HTTPException(status_code=404, detail="Radar not found")

    radar["config"] = json.loads(radar.get("config", "{}"))
    radar["stats"] = db.get_latest_stats(radar_id) or {}
    radar["readings"] = db.get_recent_readings(radar_id, hours=24)
    radar["daily_summary"] = db.get_daily_summary(radar_id)

    return templates.TemplateResponse("radar_detail.html", {
        "request": request,
        "radar": radar,
        "ingress_path": INGRESS_PATH,
        "external_url": EXTERNAL_URL,
        "internal_url": INTERNAL_URL
    })


@app.get("/add", response_class=HTMLResponse)
async def add_radar_form(request: Request):
    """Form to add a new radar."""
    return templates.TemplateResponse("add_radar.html", {
        "request": request,
        "ingress_path": INGRESS_PATH
    })


@app.post("/add")
async def add_radar(
    request: Request,
    name: str = Form(...),
    location: str = Form(""),
    notes: str = Form("")
):
    """Create a new radar."""
    radar = db.create_radar(name=name, location=location, notes=notes)

    # Publish MQTT discovery
    if mqtt_client:
        full_radar = db.get_radar_by_id(radar["id"])
        await mqtt_client.publish_discovery(full_radar)

    return RedirectResponse(
        url=get_url(f"/radar/{radar['id']}?new=1"),
        status_code=303
    )


@app.post("/radar/{radar_id}/config")
async def update_radar_config(
    radar_id: int,
    speed_limit: int = Form(50),
    min_threshold: int = Form(15),
    direction_filter: str = Form("both")
):
    """Update radar configuration - INSTANTLY pushed via MQTT!"""
    config = {
        "speed_limit": speed_limit,
        "min_threshold": min_threshold,
        "direction_filter": direction_filter
    }

    # Save to database
    db.set_radar_config(radar_id, config)

    # INSTANT push to radar via MQTT!
    radar = db.get_radar_by_id(radar_id)
    if mqtt_client and radar:
        await mqtt_client.publish_config(radar, config)

    return RedirectResponse(
        url=get_url(f"/radar/{radar_id}?saved=1"),
        status_code=303
    )


@app.post("/radar/{radar_id}/regenerate-key")
async def regenerate_key(radar_id: int):
    """Regenerate API key for a radar."""
    new_key = db.regenerate_api_key(radar_id)
    if new_key:
        return RedirectResponse(
            url=get_url(f"/radar/{radar_id}?regenerated=1"),
            status_code=303
        )
    raise HTTPException(status_code=404, detail="Radar not found")


@app.post("/radar/{radar_id}/delete")
async def delete_radar(radar_id: int):
    """Delete a radar."""
    # Remove from MQTT
    radar = db.get_radar_by_id(radar_id)
    if mqtt_client and radar:
        await mqtt_client.remove_discovery(radar)

    db.delete_radar(radar_id)
    return RedirectResponse(url=get_url("/"), status_code=303)


# ============================================================
# API Routes (for ESP32 radars)
# ============================================================

@app.post("/api/radar/{api_key}")
async def receive_radar_data(api_key: str, request: Request):
    """
    Receive data from a radar.
    This is the main endpoint that ESP32s will POST to.
    """
    radar = db.get_radar_by_api_key(api_key)
    if not radar:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Parse JSON body
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Update last seen
    db.update_radar_last_seen(radar["id"])

    # Get radar config
    config = db.get_radar_config(radar["id"])

    # Check if this is a vehicle detection event
    if data.get("event") == "vehicle_detected":
        # Record individual reading
        is_speeder = data.get("speed", 0) > config.get("speed_limit", 50)
        db.record_reading(
            radar_id=radar["id"],
            speed=data.get("speed", 0),
            direction=data.get("direction", "Unknown"),
            is_speeder=is_speeder
        )

    # Record stats if present
    if "vehicle_count" in data:
        db.record_stats(radar["id"], data)

    # Publish to MQTT for Home Assistant
    if mqtt_client:
        await mqtt_client.publish_state(radar, data)

    # Return configuration to the radar
    return JSONResponse({
        "status": "ok",
        "config": config
    })


@app.get("/api/radar/{api_key}/config")
async def get_radar_config_api(api_key: str):
    """Get configuration for a radar."""
    radar = db.get_radar_by_api_key(api_key)
    if not radar:
        raise HTTPException(status_code=401, detail="Invalid API key")

    config = db.get_radar_config(radar["id"])
    return JSONResponse(config)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============================================================
# API Routes (for external integrations)
# ============================================================

@app.get("/api/radars")
async def list_radars():
    """List all radars with their current status."""
    radars = db.get_all_radars()
    result = []
    for radar in radars:
        stats = db.get_latest_stats(radar["id"]) or {}
        result.append({
            "id": radar["id"],
            "name": radar["name"],
            "location": radar["location"],
            "last_seen": radar["last_seen"],
            "stats": stats
        })
    return result


@app.get("/api/radars/{radar_id}/readings")
async def get_readings(radar_id: int, hours: int = 24):
    """Get recent readings for a radar."""
    radar = db.get_radar_by_id(radar_id)
    if not radar:
        raise HTTPException(status_code=404, detail="Radar not found")

    return db.get_recent_readings(radar_id, hours)


@app.get("/api/radars/{radar_id}/summary")
async def get_summary(radar_id: int, date: str = None):
    """Get daily summary for a radar."""
    radar = db.get_radar_by_id(radar_id)
    if not radar:
        raise HTTPException(status_code=404, detail="Radar not found")

    return db.get_daily_summary(radar_id, date)
