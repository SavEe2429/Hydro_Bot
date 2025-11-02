from flask import Flask, request, jsonify
import os , sys
import requests # เพื่อส่งผลลัพธ์กลับไปที่ Cloud
# import serial # 🚨 สำหรับ Serial Port Control
# from your_ai_script import run_ai_detection # 🚨 นำเข้าฟังก์ชัน AI/Stitching
import numpy as np # (ใช้สำหรับตัวอย่าง AI Logic)
# ⚠️ โค้ดนี้ต้องการการติดตั้ง Library Python ทั้งหมด: opencv-python, ultralytics, pyserial
import serial_control as sc
import base64
sys.path.append(os.path.join(os.path.dirname(__file__),'..','Model'))
import merge

app = Flask(__name__)
# URL สำหรับส่งผลลัพธ์กลับไปที่ Cloud Storage/Render (ถ้ามี)
# CLOUD_STORAGE_URL = "http://your-cloud-storage-endpoint.com/upload" 

sc.initialize_serial_connection()

def image_to_base64(filepath):
    """แปลงไฟล์ภาพให้เป็น Base64 String พร้อม MIME type"""
    try:
        with open(filepath, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # คืนค่าเป็น Data URI
        return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image: {e}")
        return ""

# 🚨 Placeholder: นี่คือฟังก์ชันที่รวมโค้ด AI/Stitching/Sorting ของคุณไว้
def process_and_detect_ai():
    # # 🚨 สร้าง Data สำหรับส่งกลับ (รวมถึงข้อมูลที่จำเป็นสำหรับการควบคุม Serial Port)
    object_count = 5 # สมมติว่าเจอ 5 จุด
    merge.capture()
    
    # # 🚨 ในการใช้งานจริง โค้ดต้อง Upload 'stitched.jpg' ไปที่ Cloud Storage 
    # #    และคืน URL สาธารณะกลับมาให้ Frontend (Vue.js) แสดงผล
    # # image_display_url = "https://images4.alphacoders.com/133/thumb-1920-1332281.jpeg"
    stitched_img_path = "Model/img_detection/detected.jpg"
    # # image_display_url = "./Model/captured_shots/shot_1.jpg"
    image_base64_data = image_to_base64(stitched_img_path)
    # # 🚨 Data ที่จำเป็นสำหรับการควบคุม Serial Port (เช่น ลำดับการรดน้ำ) ควรถูกเก็บไว้ที่นี่
    # # object_order = [3, 1, 4, 2, 5] # สมมติว่าได้ลำดับนี้จากการจัดเรียง Zig-Zag
    
    return {
        "image_url": image_base64_data,
        "object_count": object_count,
        # "object_order": object_order # ข้อมูลนี้จะถูกใช้โดย Endpoints water_specific/water_all
    }



# --- Endpoints สำหรับ Local Listener (รับคำสั่งจาก Render) ---

@app.route('/process/detect', methods=['POST'])
def local_process_detect():
    """
    รับคำสั่งจาก Render Backend ให้รัน Camera/AI Process
    """
    print("Local Device: Starting Camera and AI Detection...")
    
    try:
        results = process_and_detect_ai() # รันโค้ด AI/Camera ของคุณ
        
        # 🚨 ในการใช้งานจริง Local Device ควรส่งผลลัพธ์ AI (เช่น ลำดับการรดน้ำ) 
        #    ไปบันทึกในฐานข้อมูล Cloud (เช่น Supabase/Firebase) เพื่อให้ Water API ดึงมาใช้
        
        return jsonify({
            "status": "success",
            "image_url": results["image_url"],
            "object_count": results["object_count"]
        })
    except Exception as e:
        print(f"AI Processing Error: {e}")
        return jsonify({"status": "error", "message": f"Local AI processing failed: {e}"}), 500


@app.route('/action/water_specific', methods=['POST'])
def local_water_specific():
    """
    รับคำสั่งจาก Render Backend ให้รดน้ำเฉพาะจุดผ่าน Serial Port
    """
    content = request.get_json()
    object_id = content.get('object_id')
    
    # 🚨 โค้ดควบคุม Serial Port จะอยู่ที่นี่
    # ser = serial.Serial('/dev/ttyACM0', 9600) # ตัวอย่างการเปิด Serial Port
    # command = f"W:{object_id}\n"
    # ser.write(command.encode())
    # ser.close()

    print(f"Local Device: Serial Command SENT for object ID {object_id}")
    
    return jsonify({"status": "success", "message": f"Serial command sent for {object_id}"})


@app.route('/action/water_all', methods=['POST'])
def local_water_all():
    """
    รับคำสั่งจาก Render Backend ให้รดน้ำทั้งหมดตามลำดับ
    """
    # 🚨 โค้ดนี้ควรดึงลำดับการรดน้ำล่าสุดจากฐานข้อมูล Cloud (ที่ AI บันทึกไว้)
    #    และทำการวนลูปส่งคำสั่งผ่าน Serial Port
    
    # ... (Logic: Fetch object_order from DB) ...

    print("Local Device: Serial Command SENT for all objects in sequence.")
    return jsonify({"status": "success", "message": "All watering commands sent."})

# เพิ่มโค้ดนี้ใน local_listener.py (ก่อน if __name__ == '__main__':)

# ในไฟล์ local_listener.py:

# 1. ⚠️ ต้องเปลี่ยน Import: ลบ render_template ออกถ้าคุณไม่ใช้
#    จาก: from flask import Flask, request, jsonify, render_template
#    เป็น: 
from flask import Flask, request, jsonify 
#    หรือใช้แค่ import Flask และ import jsonify ถ้าคุณใช้แค่ 2 ตัวนี้

# ... (โค้ดส่วนอื่น) ...

@app.route('/', methods=['GET'])
def health_check():
    """ Endpoint สำหรับตรวจสอบสถานะ Server (แสดงผลเป็น HTML String) """
    
    html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>Local Listener Status</title>
</head>
<body>
    <h1>Local Listener is Running!</h1>
    <p>This server is ready to receive commands from Render Backend via Cloudflare Tunnel on Port 5001.</p>
    <p>API Endpoints: 
        <ul>
            <li>/process/detect (POST)</li>
            <li>/action/water (POST)</li>
        </ul>
    </p>
</body>
</html>
    '''
    # 🎯 ใช้ return string โดยตรง และกำหนด Content-Type เป็น text/html
    return html_content, 200, {'Content-Type': 'text/html'}


if __name__ == '__main__':
    # รัน Local Listener บนพอร์ตที่ Render เข้าถึงได้ (เช่น 5001)
    # ⚠️ ให้รันโค้ดนี้ใน Virtual Environment ที่ติดตั้ง AI/cv2/pyserial ไว้
    # print(f"Local Listener running on port 5001. Ready to receive commands from Render ({LOCAL_DEVICE_URL})")
    app.run(host='0.0.0.0', port=5001)