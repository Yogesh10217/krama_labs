"""Quick API test — upload gg.jpg and print key fields + chat test."""
import requests, json, sys

url = "http://localhost:8000/api/process"
img = r"C:\Users\manju\Downloads\gg.jpg"

with open(img, "rb") as f:
    resp = requests.post(url, files={"files": ("gg.jpg", f, "image/jpeg")}, timeout=120)

if resp.status_code != 200:
    print(f"ERROR {resp.status_code}: {resp.text[:500]}")
    sys.exit(1)

data = resp.json()
print("=== TOP-LEVEL KEYS ===")
print(list(data.keys()))

pages = data.get("pages", [])
print(f"\n=== PAGES ({len(pages)}) ===")
for p in pages:
    print(f"  Page {p.get('page_num')}: type={p.get('document_type')}")
    ed = p.get("extracted_data", {})
    print(f"    extracted_data ({len(ed)} fields): {dict(list(ed.items())[:5])}")
    v = p.get("validation", {})
    print(f"    validation: final_score={v.get('final_score')}, flags={v.get('flags')}")

docs = data.get("documents", [])
print(f"\n=== DOCUMENTS ({len(docs)}) ===")
for d in docs:
    print(f"  {d.get('filename')}: type={d.get('document_type')}, conf={d.get('confidence')}")

top_data = data.get("data", {})
print(f"\n=== DATA ({len(top_data)} fields) ===")
for k, v in list(top_data.items())[:8]:
    print(f"  {k}: {v}")

print("\n=== CHAT TEST ===")
chat_resp = requests.post("http://localhost:8000/api/chat", json={
    "message": "Summarize this document",
    "context": {"pages": pages, "documents": docs}
}, timeout=30)
if chat_resp.status_code == 200:
    cr = chat_resp.json()
    print(f"  Chat response: {cr.get('response', '')[:300]}")
else:
    print(f"  Chat ERROR {chat_resp.status_code}: {chat_resp.text[:200]}")

print("\nDone.")
