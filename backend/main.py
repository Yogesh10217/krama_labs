"""FastAPI backend for Document Intelligence."""

import os
import json
import uuid
import base64
import traceback
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import Config
from pipeline import DocumentProcessor
from engines.classifier import DOCUMENT_TAXONOMY, get_all_types, get_type_labels

# Create directories
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.RESULTS_DIR, exist_ok=True)

# Validate config
if not Config.validate():
    print("WARNING: Configuration incomplete - set GOOGLE_API_KEY in .env")

app = FastAPI(
    title="Krama Document Intelligence API",
    description="AI-powered document processing - Unstructured to Structured",
    version="1.0.0",
)

# CORS - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global processor (lazy init)
processor: DocumentProcessor = None


def get_processor() -> DocumentProcessor:
    global processor
    if processor is None:
        processor = DocumentProcessor()
    return processor


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "pipeline": "ocr-only",
        "ocr_engine": "PaddleOCR v4",
        "classifier": "keyword-based",
        "extractor": "regex-based",
        "chat_available": bool(Config.GOOGLE_API_KEY),
        "llm_provider": Config.LLM_PROVIDER,
        "deploy_mode": Config.DEPLOY_MODE,
        "version": "1.1.0",
    }


@app.get("/api/doc-types")
async def list_document_types():
    """List all supported document types with categories and labels."""
    types = []
    for key, info in DOCUMENT_TAXONOMY.items():
        types.append({
            "type": key,
            "label": info["label"],
            "category": info["category"],
            "description": info["description"],
        })
    return {"document_types": types, "count": len(types)}


@app.post("/api/process")
async def process_document(file: UploadFile = File(...)):
    """Upload and process a document using OCR-only pipeline. No API key required."""

    # Validate file
    if not file.filename:
        raise HTTPException(400, "No file provided")

    allowed_ext = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".gif", ".xlsx", ".xls", ".pptx", ".ppt"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_ext:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_ext)}")

    # Check file size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > Config.MAX_FILE_SIZE_MB:
        raise HTTPException(400, f"File too large: {size_mb:.1f}MB (max {Config.MAX_FILE_SIZE_MB}MB)")

    # Save to temp file
    job_id = str(uuid.uuid4())[:8]
    save_path = os.path.join(Config.UPLOAD_DIR, f"{job_id}_{file.filename}")

    with open(save_path, "wb") as f:
        f.write(contents)

    try:
        # Process (OCR-only pipeline - no API key needed)
        proc = get_processor()
        result = proc.process(save_path)

        # Build response
        response = result.to_json()
        response["job_id"] = job_id
        response["filename"] = file.filename
        response["file_size_mb"] = round(size_mb, 2)

        # Generate annotated image preview (first page with bboxes)
        if result.pages and result.pages[0].ocr_regions:
            from engines.converter import DocumentConverter
            from PIL import Image, ImageDraw

            images, _ = DocumentConverter.convert(save_path)
            if images:
                img = images[0].copy()
                draw = ImageDraw.Draw(img)
                for region in result.pages[0].ocr_regions:
                    bbox = region.bbox
                    draw.rectangle([bbox.x1, bbox.y1, bbox.x2, bbox.y2], outline="lime", width=2)

                # Encode as base64
                buf = BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                response["annotated_image"] = base64.b64encode(buf.read()).decode("utf-8")

                # Also encode original
                buf2 = BytesIO()
                images[0].save(buf2, format="PNG")
                buf2.seek(0)
                response["original_image"] = base64.b64encode(buf2.read()).decode("utf-8")

        # Save result
        result_path = os.path.join(Config.RESULTS_DIR, f"{job_id}.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2, ensure_ascii=False)

        return JSONResponse(content=response)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Processing failed: {str(e)}")

    finally:
        # Cleanup temp file
        try:
            os.remove(save_path)
        except Exception:
            pass


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Retrieve processing results by job ID."""
    result_path = os.path.join(Config.RESULTS_DIR, f"{job_id}.json")
    if not os.path.exists(result_path):
        raise HTTPException(404, f"Results not found for job: {job_id}")

    with open(result_path, "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))


def _generate_offline_response(question: str, context: dict) -> str:
    """Generate a smart rule-based response when no LLM API key is available."""
    q = question.lower().strip()

    # Extract data from context
    pages = context.get("pages", [])
    docs = context.get("documents", [])
    all_fields = {}
    doc_types = []
    for p in pages:
        all_fields.update(p.get("extracted_data", {}))
        dt = p.get("document_type", "")
        if dt:
            doc_types.append(dt)
    # Also check top-level data
    top_data = context.get("data", {})
    if top_data:
        all_fields.update({k: v for k, v in top_data.items() if not str(k).startswith("_")})

    doc_label = context.get("document_label", "") or (doc_types[0] if doc_types else "Document")
    filename = context.get("filename", "uploaded document")
    confidence = context.get("validation", {}).get("overall_confidence", 0)

    # Build field summary
    clean_fields = {k: v for k, v in all_fields.items() if v and not str(k).startswith("_")}
    field_summary = "\n".join(f"  - {k}: {v}" for k, v in list(clean_fields.items())[:20])

    # Summarize
    if any(w in q for w in ["summarize", "summary", "overview", "what is this", "describe"]):
        resp = f"**Document Summary: {doc_label}**\n\n"
        resp += f"File: {filename}\n"
        resp += f"Classification: {doc_label} (confidence: {confidence:.0%})\n"
        resp += f"Fields extracted: {len(clean_fields)}\n\n"
        if field_summary:
            resp += f"**Extracted Data:**\n{field_summary}\n"
        return resp

    # Fraud check
    if any(w in q for w in ["fraud", "suspicious", "red flag", "anomaly"]):
        resp = f"**Fraud Analysis: {doc_label}**\n\n"
        issues = []
        # Check for missing critical fields
        if "aadhaar" in doc_label.lower() and not clean_fields.get("aadhaar_number"):
            issues.append("Aadhaar number not detected - verify document authenticity")
        if "hospital" in doc_label.lower() or "discharge" in doc_label.lower():
            if not clean_fields.get("hospital_name"):
                issues.append("Hospital name missing - verify source")
            if not clean_fields.get("total_amount"):
                issues.append("Total amount not found - check for billing discrepancies")
        if confidence < 0.6:
            issues.append(f"Low extraction confidence ({confidence:.0%}) - document may be unclear or tampered")
        if not issues:
            issues.append("No obvious fraud indicators detected based on extracted data")
            issues.append("Recommend manual verification of document authenticity")
        resp += "\n".join(f"- {i}" for i in issues)
        return resp

    # IRDAI compliance
    if any(w in q for w in ["irdai", "compliance", "regulation", "compliant"]):
        resp = f"**IRDAI Compliance Check: {doc_label}**\n\n"
        checks = []
        checks.append(f"Document type: {doc_label} - recognized under IRDAI guidelines")
        if clean_fields.get("date_of_admission") and clean_fields.get("date_of_discharge"):
            checks.append("Admission and discharge dates present - timeline verifiable")
        if clean_fields.get("total_amount"):
            checks.append(f"Claim amount: Rs. {clean_fields['total_amount']} - verify against GIPSA rate schedule")
        if clean_fields.get("diagnosis"):
            checks.append(f"Diagnosis recorded: {clean_fields['diagnosis'][:80]} - check ICD coding")
        checks.append("Recommendation: Cross-reference with policy terms and sub-limits")
        resp += "\n".join(f"- {c}" for c in checks)
        return resp

    # What data extracted
    if any(w in q for w in ["extracted", "what data", "fields", "what was found"]):
        if field_summary:
            return f"**Extracted Fields from {doc_label}:**\n\n{field_summary}"
        return f"No structured fields were extracted from this {doc_label}."

    # Default: show summary of what we know
    resp = f"**Analysis of {doc_label}** ({filename}):\n\n"
    resp += f"Extraction confidence: {confidence:.0%}\n"
    resp += f"Fields found: {len(clean_fields)}\n\n"
    if field_summary:
        resp += f"**Data:**\n{field_summary}\n\n"
    resp += "You can ask me to: summarize documents, check for fraud indicators, verify IRDAI compliance, or ask about specific extracted fields."
    return resp


@app.post("/api/chat")
async def chat_with_claim(request: Request):
    """Chat with AI about the extracted claim data. Uses Gemini or OpenAI."""
    body = await request.json()
    question = body.get("question", "")
    context = body.get("context", {})
    history = body.get("history", [])
    api_key = body.get("api_key") or Config.GOOGLE_API_KEY

    if not api_key:
        # No API key - provide smart rule-based response from extracted data
        return JSONResponse(content={
            "answer": _generate_offline_response(question, context)
        })

    if not question.strip():
        raise HTTPException(400, "No question provided")

    # Build context from extracted data
    extracted_fields = {}
    doc_type = "Unknown"
    for page in context.get("pages", []):
        extracted_fields.update(page.get("extracted_data", {}))
        if page.get("document_type"):
            doc_type = page["document_type"]

    system_prompt = f"""You are an insurance claims AI assistant for Krama AI — a Document Intelligence platform for Indian insurance.

EXTRACTED CLAIM DATA:
- Document Type: {doc_type}
- Fields: {json.dumps(extracted_fields, indent=2, ensure_ascii=False)}
- Filename: {context.get('filename', 'N/A')}

YOUR EXPERTISE:
- IRDAI (Insurance Regulatory and Development Authority of India) regulations
- Health insurance claims (discharge summaries, hospital bills, pre-auth)
- Motor insurance claims (FIR, repair estimates, surveyor reports)
- Life insurance claims (death certificates, nominee verification)
- Fraud detection patterns (bill inflation, phantom claims, upcoding)
- GIPSA (General Insurance Public Sector Association) rate schedules

RULES:
- Answer based on the extracted data above
- Reference specific IRDAI regulations when relevant
- Flag any potential fraud indicators you notice
- Be concise but thorough — this is for insurance professionals
- If data is insufficient, say what additional documents are needed
- Use Indian insurance terminology (TPA, cashless, reimbursement, pre-auth, etc.)"""

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            generation_config={"temperature": 0.3, "max_output_tokens": 1024},
        )

        # Build conversation
        parts = [system_prompt]
        for h in history[-6:]:
            role = h.get("role", "user")
            parts.append(f"{role}: {h.get('content', '')}")
        parts.append(f"user: {question}")

        response = model.generate_content("\n\n".join(parts))
        answer = response.text.strip()

        return JSONResponse(content={"answer": answer})

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Chat error: {str(e)}")


# ============================================================
# DEMO REQUEST ENDPOINT
# ============================================================
DEMO_REQUESTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_requests.json")

@app.post("/api/demo-request")
async def submit_demo_request(request: Request):
    """Receive demo form submissions and store them."""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ["firstName", "email", "company"]
        for field in required_fields:
            if not data.get(field):
                raise HTTPException(400, f"Missing required field: {field}")
        
        # Add server timestamp and ID
        from datetime import datetime
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
        
        # Log to console for visibility
        print(f"\n{'='*60}")
        print(f"📬 NEW DEMO REQUEST RECEIVED!")
        print(f"{'='*60}")
        print(f"  ID:      {data['id']}")
        print(f"  Name:    {data.get('firstName', '')} {data.get('lastName', '')}")
        print(f"  Email:   {data.get('email', '')}")
        print(f"  Company: {data.get('company', '')}")
        print(f"  Role:    {data.get('role', 'N/A')}")
        print(f"  Volume:  {data.get('volume', 'N/A')}")
        print(f"  Message: {data.get('message', 'N/A')}")
        print(f"  Time:    {data['submitted_at']}")
        print(f"{'='*60}")
        print(f"  → Saved to: {DEMO_REQUESTS_FILE}")
        print(f"{'='*60}\n")
        
        return JSONResponse(content={
            "success": True,
            "message": "Demo request received successfully",
            "request_id": data["id"]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Failed to process demo request: {str(e)}")


@app.get("/api/demo-requests")
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


# Mount the parent directory for serving the frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print(f"\nStarting Kimi Document Intelligence API")
    print(f"  Backend API: http://localhost:{Config.PORT}/api/health")
    print(f"  Demo Page:   http://localhost:{Config.PORT}/demo.html")
    print(f"  Frontend:    http://localhost:{Config.PORT}/")
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
