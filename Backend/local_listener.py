from flask import Flask, request, jsonify
import os , sys , time  ,json
import requests        
import numpy as np 
import serial_control as sc
import base64 

# 🎯 FIX: ต้องใส่ path ของ Model เพื่อให้ import ได้
sys.path.append(os.path.join(os.path.dirname(__file__),'..','Model'))
import merge , detect

app = Flask(__name__)
# URL สำหรับส่งผลลัพธ์กลับไปที่ Cloud Storage/Render (ถ้ามี)
# CLOUD_STORAGE_URL = "http://your-cloud-storage-endpoint.com/upload" 

# 🎯 -----------------------------------------------------------------
# GLOBAL STATE: ใช้เก็บคำสั่งล่าสุดที่มาจาก Web
# -----------------------------------------------------------------
GLOBAL_JSON = {
    "object_order": [],
    "object_centers":{},
    "last_run_time": 0
}

def read_json(filepath="Model/output.json"):
    """Read data from json file"""
    try:
        fullpath = os.path.join(os.path.dirname(__file__),'..',filepath)
        with open(fullpath,'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error reading JSON FILE : {e}")
        return None
    
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

    # connecting port
    sc.initialize_serial_connection()

    # 1. 🟢 Capture:
    capture_status, files_list = merge.capture_img() # (bool, list[str])
    
    if not capture_status or not files_list:
        sc.close_serial_connection()
        raise Exception("Capture failed. No images were successfully captured or device timed out.")
        
    # 2. 🟢 Stitch:
    # 🎯 FIX: Unpack correctly (stitch_img returns (status, path))
    stitch_status, stitched_path = merge.stitch_img(files_list) # (bool, str)
    
    # ถ้า Stitching ล้มเหลว ให้ใช้ภาพที่ได้จาก stitch_img (ซึ่งจะ Fallback ไปใช้ภาพแรก)
    if not stitch_status:
        print("❌ Stitching failed. Falling back to the first captured image path provided by merge.py.")
    
    if not stitched_path or not os.path.exists(stitched_path):
         sc.close_serial_connection()
         raise Exception("Stitching and fallback failed. No valid image path found.")

    # 3. 🟢 Detect AI (YOLO):
    # 🎯 FIX: detect.detect_ai ถูกปรับให้คืนค่าเป็น Dictionary 
    detection_results = detect.detect_ai(stitched_path)
    
    detect_status = detection_results.get('status', False)
    detection_img_path = detection_results.get('output_path', stitched_path)
    object_count = detection_results.get('object_count', 0)
    
    if not detect_status:
        print(f"WARNING: AI Detection reported failure/error. Using image path: {detection_img_path}")
    
    # 4. 🟢 Base64 Encode:
    image_base64_data = image_to_base64(detection_img_path) 
    
    # 5. อย่าลืมปิดการเชื่อมต่อเมื่อเสร็จ
    sc.close_serial_connection()

    # 6. คืนค่าผลลัพธ์ที่รวม object_order ไว้ด้วย
    return {
        "image_url": image_base64_data,
        "object_count": object_count,
        # "object_order": detection_results.get('object_order', [])
    }


# --- Endpoints สำหรับ Local Listener (รับคำสั่งจาก Render) ---

@app.route('/process/detect', methods=['POST'])
def local_process_detect():
    """
    รับคำสั่งจาก Render Backend ให้รัน Camera/AI Process
    """
    print("Local Device: Starting Camera and AI Detection...")
    
    try:
        # 🎯 FIX: รับค่าผลลัพธ์เป็น dictionary
        results = process_and_detect_ai() 
        
        # 🚨 ในการใช้งานจริง Local Device ควรส่งผลลัพธ์ AI (เช่น ลำดับการรดน้ำ) 
        #    ไปบันทึกในฐานข้อมูล Cloud (เช่น Supabase/Firebase) เพื่อให้ Water API ดึงมาใช้
        
        return jsonify({
            "status": "success",
            "image_url": results["image_url"],
            "object_count": results["object_count"],
            # "object_order": results["object_order"] # คืนค่าลำดับการรดน้ำ
        })
    except Exception as e:
        print(f"AI Processing Error: {e}")
        return jsonify({"status": "error", "message": f"Local AI processing failed: {e}"}), 500


@app.route('/loading/loadjson', methods=['POST'])
def load_json_file():
    """
    โหลดข้อมูลจาก json file และอัปเดตค่าของ GLOBAL_JSON
    """
    global GLOBAL_JSON
    jsonfile = read_json("Model/output.json")
    print("jsonfile ",jsonfile)
    if not jsonfile or jsonfile.get('object_count',0) == 0:
        return jsonify({"status": "error", "message": "AI Detection reported no objects in JSON."}), 404
    print("jsonfile work")
    print("jsonfile count : ",jsonfile['object_count'])
    object_centers_dict = {}
    object_order_list = []

    for obj in jsonfile['objects']:
        obj_id = obj['object_id']

        object_centers_dict[obj_id] = {
            'x':obj.get('center_x',0),
            'y':obj.get('center_y',0)
        }
        object_order_list.append(obj_id)
    
    GLOBAL_JSON.update({
        "object_order": object_order_list,
        "object_centers":object_centers_dict,
        "last_run_time": time.time()
    })
    image_base64_data = image_to_base64(jsonfile['output_path']) 
    
    return jsonify({
        "status":"success",
        "image_url":image_base64_data,
        "object_count":jsonfile['object_count']
    }),200

@app.route('/action/water_specific', methods=['POST'])
def local_water_specific():
    """
    รับคำสั่งจาก Render Backend ให้รดน้ำเฉพาะจุดผ่าน Serial Port
    """
    content = request.get_json()
    object_id = content.get('object_id')
    
    # 🚨 โค้ดควบคุม Serial Port จะอยู่ที่นี่
    response = sc.send_serial_command(f"WATER_SPECIFIC:{object_id}")
    
    print(f"Local Device: Serial Command SENT for object ID {object_id}. Response: {response}")
    
    if "WATERING_SPECIFIC_COMPLETE" in response.upper():
        return jsonify({"status": "success", "message": f"Serial command sent for {object_id}"})
    else:
        return jsonify({"status": "error", "message": f"Serial command failed for {object_id}: {response}"}), 500


@app.route('/action/water_all', methods=['POST'])
def local_water_all():
    """
    รับคำสั่งจาก Render Backend ให้รดน้ำทั้งหมดตามลำดับ
    """
    # 🚨 โค้ดนี้ควรดึงลำดับการรดน้ำล่าสุดจากฐานข้อมูล Cloud (ที่ AI บันทึกไว้)
    #    และทำการวนลูปส่งคำสั่งผ่าน Serial Port
    
    # เนื่องจากเรายังไม่มี DB, ให้ส่งคำสั่ง WATER_ALL ไปที่ ESP32 โดยตรง 
    # และคาดหวังว่า ESP32 จะมี Logic ในการรดน้ำตามลำดับอยู่แล้ว
    
    response = sc.send_serial_command("WATER_ALL")

    print(f"Local Device: Serial Command SENT for all objects in sequence. Response: {response}")
    
    if "ACK" in response.upper():
        return jsonify({"status": "success", "message": "All watering commands sent."})
    else:
        return jsonify({"status": "error", "message": f"Water All command failed: {response}"}), 500


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
            <li>/action/water_specific (POST)</li>
            <li>/action/water_all (POST)</li>
        </ul>
    </p>
</body>
</html>
    '''
    # 🎯 ใช้ return string โดยตรง และกำหนด Content-Type เป็น text/html
    return html_content, 200, {'Content-Type': 'text/html'}


if __name__ == '__main__':
    # รัน Local Listener บนพอร์ตที่ Render เข้าถึงได้ (เช่น 5001)
    app.run(host='0.0.0.0', port=5001)