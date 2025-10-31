from flask import Flask, request, jsonify
from flask_cors import CORS  # ⬅️ นำเข้า CORS
import requests
import os

app = Flask(__name__)

# 🎯 กำหนดค่า CORS: อนุญาตเฉพาะ Origin ที่แน่นอน
CORS(app, resources={r"/api/*": {"origins": "https://savee2429.github.io"}}) 
# Note: r"/api/*" คือการบอกว่าให้ใช้กฎนี้กับทุก Endpoint ที่ขึ้นต้นด้วย /api/

# 🚨 ดึง URL ของ Local Device (Cloudflare Tunnel URL) จาก Environment Variable
LOCAL_DEVICE_URL = os.environ.get("LOCAL_DEVICE_URL")

# --- Endpoints สำหรับการควบคุม ---

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """
    Endpoint สำหรับรับคำสั่ง 'ถ่ายรูปและตรวจจับ' จาก Frontend (Vue.js)
    และส่งต่อคำสั่งไปยัง Local Device
    """
    print("Received detection request from Frontend.")
    try:
        # 1. ส่งคำสั่งไปยัง Local Listener เพื่อให้ Local Device รันโค้ด AI/Camera/Stitching
        local_response = requests.post(f"{LOCAL_DEVICE_URL}/process/detect", timeout=300) # Timeout 5 นาที สำหรับงานหนัก
        local_response.raise_for_status()
        
        # 2. รับผลลัพธ์จาก Local Listener
        data = local_response.json()
        
        # คืนผลลัพธ์กลับไปให้ Frontend (Vue.js)
        return jsonify({
            "status": "success",
            "message": "AI detection and stitching completed on local device.",
            "image_url": data.get("image_url", ""),  # URL ของภาพผลลัพธ์ (สมมติว่า Local Upload ไปที่ Cloud Storage)
            "object_count": data.get("object_count", 0), # จำนวนวัตถุที่พบ
            "object_data": data.get("object_data", [])
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "message": "Local device took too long to process (Timeout).",
            "object_count": 0
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Could not connect to local device listener: {e}",
            "object_count": 0
        }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred on Render: {e}",
            "object_count": 0
        }), 500

@app.route('/api/water', methods=['POST'])
def api_water_specific():
    """
    Endpoint สำหรับสั่งรดน้ำเฉพาะจุดจาก Frontend
    """
    content = request.get_json()
    object_id = content.get('object_id')
    
    if object_id is None:
        return jsonify({"status": "error", "message": "Missing object_id"}), 400

    print(f"Received command to water specific object ID: {object_id}")
    try:
        # ส่งคำสั่งไปยัง Local Listener เพื่อควบคุม Serial Port
        local_response = requests.post(f"{LOCAL_DEVICE_URL}/action/water_specific", json={"object_id": object_id}, timeout=30)
        local_response.raise_for_status()

        return jsonify({
            "status": "success",
            "message": f"Command sent to local device for watering object {object_id}."
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to communicate with local device: {e}"}), 503

@app.route('/api/water_all', methods=['POST'])
def api_water_all():
    """
    Endpoint สำหรับสั่งรดน้ำทั้งหมดจาก Frontend
    """
    print("Received command to water all objects.")
    try:
        # ส่งคำสั่งไปยัง Local Listener เพื่อรดน้ำตามลำดับที่ AI จัดเรียงไว้
        local_response = requests.post(f"{LOCAL_DEVICE_URL}/action/water_all", timeout=60)
        local_response.raise_for_status()
        
        return jsonify({
            "status": "success",
            "message": "Command sent to local device for watering all objects."
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to communicate with local device: {e}"}), 503

# -----------------
# Health Check (สำหรับ Render)
@app.route('/', methods=['GET'])
def health_check():
    """
    Endpoint พื้นฐานสำหรับ Render ใช้ตรวจสอบสถานะ
    """
    return "Hydro-Bot Render Backend is running.", 200

if __name__ == '__main__':
    # เมื่อรันบน Render ควรใช้ Gunicorn หรือ Waitress แต่สำหรับการทดสอบ Local ให้รัน Flask โดยตรง
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)