# Krama AI

**AI Claims Engine for Insurance** — Turn discharge summaries, repair estimates, and claim forms into validated, fraud-checked decisions in minutes.

🌐 **Live:** [kramaai.com](https://kramaai.com)

---

## What It Does

Krama AI automates insurance claims processing for Indian insurers and TPAs. Upload any claim document — discharge summaries, hospital bills, FIRs, repair estimates, pharmacy receipts — in any format (PDF, scan, photo, handwritten Hindi) and get a structured, validated claim decision.

### Pipeline

```
Document Upload → Conversion → OCR → Classification → Field Extraction → Validation → Fraud Detection → Decision
```

- **Ingest** — PDF, scans, photos, XLSX, PPTX. Handles handwritten Hindi/English.
- **Extract** — PaddleOCR + Gemini Vision for field-level extraction with confidence scores.
- **Validate** — Triple validation cross-checks OCR, VLM, and structural patterns. Flags anomalies.
- **Decide** — IRDAI rule checks, fraud detection, auto-adjudication recommendations with full audit trail.

---

## Supported Document Types

| Category | Documents |
|----------|-----------|
| **Medical** | Discharge Summary, Lab Report, Prescription, Medical Certificate |
| **Financial** | Hospital Bill, Pharmacy Receipt, Repair Estimate, Invoice |
| **Insurance** | Claim Form, Policy Document, Cashless Authorization, Surveyor Report |
| **Identity** | Aadhaar Card, PAN Card, Driving License, Voter ID |
| **Vehicle** | RC Book, FIR Copy, Accident Report |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **OCR** | PaddleOCR v4 |
| **Vision LLM** | Google Gemini 2.0 Flash |
| **Backend** | Python, FastAPI |
| **Frontend** | HTML/CSS/JS (landing page), React (app) |
| **Validation** | Custom triple-validation engine with 5 grounding strategies |
| **Deployment** | Vercel (frontend), self-hosted (backend) |

---

## Project Structure

```
├── index.html              # Landing page
├── backend/
│   ├── main.py             # FastAPI server
│   ├── pipeline.py         # Document processing pipeline
│   ├── config.py           # Configuration
│   ├── models.py           # Data models
│   ├── engines/
│   │   ├── ocr_engine.py       # PaddleOCR wrapper
│   │   ├── vlm_engine.py       # Gemini Vision extraction
│   │   ├── classifier.py       # Document type classification
│   │   ├── ocr_extractor.py    # Regex-based field extraction
│   │   ├── chunker.py          # Document chunking
│   │   ├── converter.py        # PDF/image conversion
│   │   ├── grounding.py        # Confidence grounding
│   │   ├── validator.py        # Triple validation
│   │   └── llm_provider.py     # LLM provider abstraction
│   ├── uploads/            # Uploaded documents
│   └── results/            # Processing results (JSON)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Google Gemini API key (optional — OCR pipeline works without it)

### Setup

```bash
# Clone the repo
git clone https://github.com/your-org/kramaai.git
cd kramaai

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key    # Optional — enables VLM extraction + chat
LLM_PROVIDER=gemini                    # gemini | openai | local
DEPLOY_MODE=saas                       # saas | onpremise | hybrid
HOST=0.0.0.0
PORT=8000
```

### Run

```bash
# Start the backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check & pipeline status |
| `GET` | `/api/doc-types` | List supported document types |
| `POST` | `/api/process` | Upload and process a document |
| `POST` | `/api/chat` | Chat with AI about processed results |
| `GET` | `/api/results/{job_id}` | Retrieve processing results |

### Process a Document

```bash
curl -X POST http://localhost:8000/api/process \
  -F "file=@discharge_summary.pdf"
```

Returns structured JSON with extracted fields, confidence scores, validation results, and decision recommendation.

---

## How It Works

1. **Document Conversion** — PDFs are converted to images at 200 DPI. Supports multi-page documents.
2. **OCR (PaddleOCR)** — Extracts text regions with bounding boxes and confidence scores.
3. **Classification** — Keyword-based classifier identifies document type (30+ types across 6 categories).
4. **Field Extraction** — Regex patterns extract structured fields specific to each document type.
5. **VLM Extraction** *(optional)* — Gemini Vision provides a second extraction pass for higher accuracy.
6. **Triple Validation** — OCR results, VLM results, and structural patterns are cross-checked. Conflicts are flagged.
7. **Fraud Detection** — Anomaly detection checks for inflated bills, date inconsistencies, and forged patterns.
8. **Decision** — IRDAI policy rules are applied. Claims are auto-approved, flagged for review, or rejected with reasons.

---

## License

Proprietary. All rights reserved.

---

**Krama AI** — AI Claims Engine for Insurance  
[kramaai.com](https://kramaai.com) · Built for Indian Insurance
