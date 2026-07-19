"""Demo form request endpoints for Krama AI."""

import os
import uuid
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import Config
from app.core.exceptions import ValidationException

router = APIRouter()
logger = logging.getLogger(__name__)

# File to store demo requests (located in backend/ root directory)
DEMO_REQUESTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "demo_requests.json"
)


@router.post("/demo-request")
async def submit_demo_request(request: Request):
    """Receive demo form submissions and store them."""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ["firstName", "email", "company"]
        for field in required_fields:
            if not data.get(field):
                raise ValidationException(f"Missing required field: {field}", "MISSING_FIELD")
        
        # Add server timestamp and ID
        data["id"] = str(uuid.uuid4())[:8]
        data["submitted_at"] = datetime.now().isoformat()
        data["status"] = "new"
        
        # Load existing requests
        existing_requests = []
        if os.path.exists(DEMO_REQUESTS_FILE):
            with open(DEMO_REQUESTS_FILE, "r", encoding="utf-8") as f:
                try:
                    existing_requests = json.load(f)
                except json.JSONDecodeError:
                    existing_requests = []
        
        # Append new request
        existing_requests.append(data)
        
        # Save updated requests
        with open(DEMO_REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_requests, f, indent=2, ensure_ascii=False)
        
        # Log for visibility
        logger.info(f"New demo request from {data.get('firstName')} ({data.get('company')}) saved to {DEMO_REQUESTS_FILE}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Demo request received successfully",
            "request_id": data["id"]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process demo request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process demo request: {str(e)}")


@router.get("/demo-requests")
async def get_demo_requests():
    """Retrieve all demo requests (for admin use)."""
    if not os.path.exists(DEMO_REQUESTS_FILE):
        return {"requests": [], "count": 0}
    
    with open(DEMO_REQUESTS_FILE, "r", encoding="utf-8") as f:
        try:
            requests_list = json.load(f)
        except json.JSONDecodeError:
            requests_list = []
    
    return {
        "requests": requests_list,
        "count": len(requests_list)
    }
