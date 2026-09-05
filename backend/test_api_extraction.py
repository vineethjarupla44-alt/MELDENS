"""
Tests the FastAPI HTTP endpoints for document text extraction:
1. Upload a PDF
2. Call POST /api/v1/documents/{document_id}/process
3. Verify returned JSON shape:
   {
       "document_id": "...",
       "pages": [
           {
               "page_number": 1,
               "extracted_text": "...",
               "extraction_status": "SUCCESS"
           }
       ]
   }
4. Call GET /api/v1/documents/{document_id}/pages
5. Verify response
"""
import os
import socket
import threading
import time
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

BASE_URL = "http://127.0.0.1:8000/api/v1"

def ensure_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', 8000)) == 0:
            return
    import uvicorn
    from app.main import app
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(40):
        time.sleep(0.2)
        try:
            r = requests.get("http://127.0.0.1:8000/api/health", timeout=0.5)
            if r.status_code == 200:
                return
        except Exception:
            pass

def create_temp_pdf(filename: str):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, 740, "HTTP ENDPOINT TEST - CLINICAL SUMMARY")
    c.setFont("Helvetica", 10)
    c.drawString(60, 710, "Patient ID: Synthetic Test Case")
    c.drawString(60, 690, "Laboratory: White Blood Cells 6.5 x10^3/uL (Normal)")
    c.showPage()
    c.save()

def main():
    ensure_server()
    # 1. Get a patient
    patients_resp = requests.get(f"{BASE_URL}/patients")
    assert patients_resp.status_code == 200
    patients = patients_resp.json()
    assert len(patients) > 0
    patient_id = patients[0]["id"]
    print(f"Testing with patient ID: {patient_id}")

    # 2. Create and upload a PDF
    pdf_filename = "api_test_doc.pdf"
    create_temp_pdf(pdf_filename)
    try:
        with open(pdf_filename, "rb") as f:
            upload_resp = requests.post(
                f"{BASE_URL}/patients/{patient_id}/documents/upload",
                files={"file": (pdf_filename, f, "application/pdf")},
            )
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        doc_data = upload_resp.json()
        doc_id = doc_data["id"]
        print(f"Uploaded document ID: {doc_id}")

        # 3. Call Process Endpoint
        process_resp = requests.post(f"{BASE_URL}/documents/{doc_id}/process")
        assert process_resp.status_code == 200, f"Process failed: {process_resp.text}"
        process_data = process_resp.json()

        print("\nProcess Response:")
        print("document_id:", process_data["document_id"])
        print("pages count:", len(process_data["pages"]))
        page1 = process_data["pages"][0]
        print("page_number:", page1["page_number"])
        print("extraction_status:", page1["extraction_status"])
        print("extracted_text snippet:", page1["extracted_text"][:60])

        assert process_data["document_id"] == doc_id
        assert len(process_data["pages"]) == 1
        assert page1["page_number"] == 1
        assert page1["extraction_status"] == "SUCCESS"
        assert "HTTP ENDPOINT TEST - CLINICAL SUMMARY" in page1["extracted_text"]

        # 4. Call GET /pages endpoint
        pages_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/pages")
        assert pages_resp.status_code == 200
        pages = pages_resp.json()
        assert len(pages) == 1
        assert pages[0]["extraction_status"] == "SUCCESS"
        assert "HTTP ENDPOINT TEST" in pages[0]["extracted_text"]

        print("\nAll HTTP extraction endpoint assertions passed successfully!")

        # 5. Cleanup document via API
        del_resp = requests.delete(f"{BASE_URL}/documents/{doc_id}")
        assert del_resp.status_code == 200
        print("Cleaned up test document.")

    finally:
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)

if __name__ == "__main__":
    main()
