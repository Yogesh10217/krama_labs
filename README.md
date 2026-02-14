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
- **Extract** — OCR + VLM for field-level extraction with confidence scores.
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
| **OCR** | OCR Engine (bounding box + confidence) |
| **Vision LLM** | VLM-based extraction |
| **Backend** | Python, FastAPI |
| **Frontend** | HTML/CSS/JS |
| **Validation** | Custom triple-validation engine with 5 grounding strategies |

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
│   │   ├── ocr_engine.py       # OCR wrapper
│   │   ├── vlm_engine.py       # Vision LLM extraction
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
- API key for VLM provider (optional — OCR pipeline works without it)

### Setup

```bash
# Clone the repo
git clone https://github.com/OnHighEngineer/krama_labs.git
cd krama_labs

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt
```

### Configuration

Create a `.env` file in `backend/` with your API keys (see `.env.example`).

### Run

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

API available at `http://localhost:8000`.

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

1. **Document Conversion** — PDFs converted to images. Supports multi-page documents.
2. **OCR** — Extracts text regions with bounding boxes and confidence scores.
3. **Classification** — Identifies document type (30+ types across 6 categories).
4. **Field Extraction** — Type-specific regex patterns extract structured fields.
5. **VLM Extraction** *(optional)* — Vision model provides a second extraction pass for higher accuracy.
6. **Triple Validation** — OCR results, VLM results, and structural patterns are cross-checked. Conflicts flagged.
7. **Fraud Detection** — Checks for inflated bills, date inconsistencies, and forged patterns.
8. **Decision** — IRDAI policy rules applied. Claims auto-approved, flagged, or rejected with reasons.

---

## License

Proprietary. All rights reserved.

---

**Krama AI** — AI Claims Engine for Insurance  
[kramaai.com](https://kramaai.com) · Built for Indian Insurance
