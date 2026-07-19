"""AI chat endpoint for querying claim details."""

import json
import logging
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import Config

router = APIRouter()
logger = logging.getLogger(__name__)


def _generate_offline_response(question: str, context: dict) -> str:
    """Generate a smart rule-based response when no LLM API key is available."""
    q = question.lower().strip()

    # Extract data from context
    pages = context.get("pages", [])
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


@router.post("")
async def chat_with_claim(request: Request):
    """Chat with AI about the extracted claim data. Uses Gemini or OpenAI."""
    try:
        body = await request.json()
    except Exception:
        from app.core.exceptions import ValidationException
        raise ValidationException("Request body must be valid JSON", "INVALID_JSON")
    question = body.get("question") or body.get("message", "")
    context = body.get("context", {})
    history = body.get("history", [])
    api_key = body.get("api_key") or Config.GOOGLE_API_KEY

    # Use offline generator if no API key is set/provided
    if not api_key and not Config.OPENAI_API_KEY:
        return JSONResponse(content={
            "answer": _generate_offline_response(question, context),
            "response": _generate_offline_response(question, context) # double compatibility for test scripts
        })

    if not question.strip():
        raise HTTPException(status_code=400, detail="No question/message provided")

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
        # Determine provider
        if Config.LLM_PROVIDER == "openai" or (Config.OPENAI_API_KEY and not api_key):
            from openai import OpenAI
            client = OpenAI(api_key=Config.OPENAI_API_KEY or api_key)

            messages = [{"role": "system", "content": system_prompt}]
            for h in history[-6:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            messages.append({"role": "user", "content": question})

            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            answer = response.choices[0].message.content.strip()
        else:
            # Fallback to Gemini
            import google.generativeai as genai
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                Config.GEMINI_MODEL,
                generation_config={"temperature": 0.3, "max_output_tokens": 1024},
            )

            parts = [system_prompt]
            for h in history[-6:]:
                role = h.get("role", "user")
                parts.append(f"{role}: {h.get('content', '')}")
            parts.append(f"user: {question}")

            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = model.generate_content(
                "\n\n".join(parts),
                safety_settings=safety_settings,
            )

            if not response.candidates or not response.candidates[0].content.parts:
                answer = "I couldn't generate a response for that query. Please try rephrasing your question about the claim."
            else:
                answer = response.text.strip()

        return JSONResponse(content={
            "answer": answer,
            "response": answer  # duplicate key for compatibility with test scripts
        })

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
