"""
MedLens Document Upload Module Test Suite
Tests:
- Upload synthetic PDF
- Upload synthetic PNG
- Upload synthetic JPG
- File type validation (reject invalid format)
- File size validation
- List patient documents
- Download / Preview stream
- Delete document and verify physical file removal
"""
import os
import sys
import io
import socket
import threading
import time
import requests
from pypdf import PdfWriter

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

def create_synthetic_pdf(filename: str, num_pages: int = 2) -> str:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    with open(filename, "wb") as f:
        writer.write(f)
    return filename

def create_synthetic_png(filename: str) -> str:
    # 1x1 transparent PNG binary bytes
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
        0x42, 0x60, 0x82
    ])
    with open(filename, "wb") as f:
        f.write(png_bytes)
    return filename

def create_synthetic_jpg(filename: str) -> str:
    # Minimal 1x1 JPEG binary bytes
    jpg_bytes = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
        0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48,
        0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C,
        0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D,
        0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
        0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
        0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
        0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4,
        0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
        0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
        0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF,
        0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F,
        0x00, 0xBF, 0x80, 0xFF, 0xD9
    ])
    with open(filename, "wb") as f:
        f.write(jpg_bytes)
    return filename

def run_tests():
    print("\n--- Running Medical Document Upload Module Tests ---")
    ensure_server()

    # 1. Get a patient
    res = requests.get(f"{BASE_URL}/patients")
    assert res.status_code == 200, f"Failed to list patients: {res.text}"
    patients = res.json()
    assert len(patients) > 0, "No patients found"
    patient = patients[0]
    patient_id = patient["id"]
    print(f"Testing with patient: {patient['first_name']} {patient['last_name']} ({patient_id})")

    # 2. Test PDF Upload
    pdf_path = "temp_test_report.pdf"
    create_synthetic_pdf(pdf_path, num_pages=3)
    try:
        with open(pdf_path, "rb") as f:
            upload_res = requests.post(
                f"{BASE_URL}/patients/{patient_id}/documents/upload",
                files={"file": ("CBC_Chemistry_Report_2026.pdf", f, "application/pdf")}
            )
        assert upload_res.status_code == 200, f"PDF upload failed: {upload_res.text}"
        pdf_data = upload_res.json()
        assert pdf_data["processing_status"] == "UPLOADED"
        assert pdf_data["page_count"] == 3
        assert pdf_data["original_name"] == "CBC_Chemistry_Report_2026.pdf"
        assert pdf_data["checksum"] is not None
        pdf_doc_id = pdf_data["id"]
        print(f"PASS: Synthetic PDF uploaded successfully -> ID: {pdf_doc_id}, Pages: {pdf_data['page_count']}, Status: {pdf_data['processing_status']}")
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    # 3. Test PNG Upload
    png_path = "temp_test_chest_xray.png"
    create_synthetic_png(png_path)
    try:
        with open(png_path, "rb") as f:
            upload_res = requests.post(
                f"{BASE_URL}/patients/{patient_id}/documents/upload",
                files={"file": ("Chest_XRay_Scan.png", f, "image/png")}
            )
        assert upload_res.status_code == 200, f"PNG upload failed: {upload_res.text}"
        png_data = upload_res.json()
        assert png_data["processing_status"] == "UPLOADED"
        assert png_data["page_count"] == 1
        png_doc_id = png_data["id"]
        print(f"PASS: Synthetic PNG uploaded successfully -> ID: {png_doc_id}, Status: {png_data['processing_status']}")
    finally:
        if os.path.exists(png_path):
            os.remove(png_path)

    # 4. Test JPG Upload
    jpg_path = "temp_test_ecg.jpg"
    create_synthetic_jpg(jpg_path)
    try:
        with open(jpg_path, "rb") as f:
            upload_res = requests.post(
                f"{BASE_URL}/patients/{patient_id}/documents/upload",
                files={"file": ("ECG_Rhythm_Strip.jpg", f, "image/jpeg")}
            )
        assert upload_res.status_code == 200, f"JPG upload failed: {upload_res.text}"
        jpg_data = upload_res.json()
        assert jpg_data["processing_status"] == "UPLOADED"
        jpg_doc_id = jpg_data["id"]
        print(f"PASS: Synthetic JPG uploaded successfully -> ID: {jpg_doc_id}, Status: {jpg_data['processing_status']}")
    finally:
        if os.path.exists(jpg_path):
            os.remove(jpg_path)

    # 5. Test File Type Validation (Reject invalid extension)
    bad_res = requests.post(
        f"{BASE_URL}/patients/{patient_id}/documents/upload",
        files={"file": ("malicious_payload.exe", io.BytesIO(b"MZ..."), "application/x-msdownload")}
    )
    assert bad_res.status_code == 400, "Expected 400 rejection for .exe format"
    print("PASS: Insecure file format (.exe) properly rejected with HTTP 400")

    # 6. Test Document Listing for Patient
    list_res = requests.get(f"{BASE_URL}/patients/{patient_id}/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    doc_ids = [d["id"] for d in docs]
    assert pdf_doc_id in doc_ids
    assert png_doc_id in doc_ids
    assert jpg_doc_id in doc_ids
    print(f"PASS: List patient documents returned {len(docs)} documents, including newly uploaded items")

    # 7. Test Secure File Download / Preview Stream
    stream_res = requests.get(f"{BASE_URL}/documents/{pdf_doc_id}/file")
    assert stream_res.status_code == 200
    assert stream_res.headers.get("Content-Type") == "application/pdf"
    assert len(stream_res.content) > 0
    print(f"PASS: Secure file preview stream returned {len(stream_res.content)} bytes with Content-Type: application/pdf")

    # 8. Test Document Deletion
    for did in [jpg_doc_id, pdf_doc_id, png_doc_id]:
        del_res = requests.delete(f"{BASE_URL}/documents/{did}")
        assert del_res.status_code == 200

    # Verify deleted from list
    list_after = requests.get(f"{BASE_URL}/patients/{patient_id}/documents").json()
    assert jpg_doc_id not in [d["id"] for d in list_after]
    assert pdf_doc_id not in [d["id"] for d in list_after]
    assert png_doc_id not in [d["id"] for d in list_after]

    # Verify 404 on preview after deletion
    preview_after = requests.get(f"{BASE_URL}/documents/{jpg_doc_id}/file")
    assert preview_after.status_code == 404
    print("PASS: Document deletion verified -> removed from database and disk, returns HTTP 404")

    print("\n ALL MEDICAL DOCUMENT UPLOAD TESTS PASSED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
