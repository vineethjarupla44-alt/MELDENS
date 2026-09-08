import os
import sys
import socket
import threading
import time
import requests

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

def test_image_pipeline():
    ensure_server()
    # 1. Seed demo data to ensure patient exists
    seed_resp = requests.post(f"{BASE_URL}/seed")
    assert seed_resp.status_code == 200
    patient_id = seed_resp.json()["id"]

    # 2. Upload synthetic PNG
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

    files = {
        "file": ("lab_report_scan.png", png_bytes, "image/png")
    }
    up_resp = requests.post(f"{BASE_URL}/patients/{patient_id}/documents/upload", files=files)
    assert up_resp.status_code == 200, f"Upload failed: {up_resp.text}"
    doc_id = up_resp.json()["id"]
    print("[PASS] Image uploaded:", doc_id)

    # 3. Process Image Document
    proc_resp = requests.post(f"{BASE_URL}/documents/{doc_id}/process")
    assert proc_resp.status_code == 200, f"Process failed: {proc_resp.text}"
    proc_data = proc_resp.json()
    assert len(proc_data["pages"]) == 1
    assert len(proc_data["pages"][0]["extracted_text"]) > 20
    print("[PASS] Image processed via OCR, extracted text length:", len(proc_data["pages"][0]["extracted_text"]))

    # 4. Extract AI Medical Data from Image
    ext_resp = requests.post(f"{BASE_URL}/documents/{doc_id}/extract-medical-data")
    assert ext_resp.status_code == 200, f"Extraction failed: {ext_resp.text}"
    ext_data = ext_resp.json()
    assert len(ext_data["laboratories"]) > 0
    print(f"[PASS] Successfully extracted {len(ext_data['laboratories'])} clinical labs from image document!")

    # 5. Clean up
    del_resp = requests.delete(f"{BASE_URL}/documents/{doc_id}")
    assert del_resp.status_code == 200
    print("[PASS] Cleaned up test image")

if __name__ == "__main__":
    test_image_pipeline()
    print("\nIMAGE PIPELINE FULLY FUNCTIONAL AND VERIFIED!")
