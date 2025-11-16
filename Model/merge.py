import cv2, os, sys, time

# 🎯 FIX: อ้างอิง Backend ถูกต้อง
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Backend"))
import serial_control as sc


def capture_img():
    save_path = "Model/captured_shots"
    os.makedirs(save_path, exist_ok=True)

    # ... (โค้ดเตรียมการ, Warm-up กล้อง) ...

    # --- 1. INITIAL HANDSHAKE (ส่งคำสั่ง SCAN) ---
    print("\n--- Starting Scan and Capture Process ---")

    initial_response = sc.send_serial_command("SCAN")

    if "SCAN_ACK" not in initial_response.upper():
        print(f"❌ ERROR: ESP32 failed to start scan. Response: {initial_response}")
        return False, []

    print("✅ Scan sequence initiated. Waiting for ARRIVED signals...")

    # --- 2. INTERACTIVE LOOP: รอสัญญาณ ARRIVED ---
    shots_count = 12
    max_wait_sec = 120  # 3 นาที สำหรับการสแกนทั้งหมด
    start_time = time.time()
    captured_files = []
    
    img_count = 0 # 🎯 FIX: Initialize counter for image naming (แก้ปัญหา img_length)
    
    cap = cv2.VideoCapture(0)  
    if not cap.isOpened():
        print("❌ ERROR: Cannot open video capture device (Webcam).")
        return False, []

    while (time.time() - start_time) < max_wait_sec:

        # 🟢 อ่านข้อมูล Serial ที่มีทั้งหมดใน Buffer (ไม่บล็อก)
        serial_data = sc.read_all_available().upper().strip()  
        
        if "WAITING_COMMAND" in serial_data:
            print("<- Received 'WAITING_COMMAND'. Send command and shots_count...")
            # 🎯 FIX: ส่งคำสั่งที่มีค่าตัวแปร: CAPTURE:10
            sc.send_serial_command(f"CAPTURE:{shots_count}")
            
        # 3. ตรวจสอบสัญญาณ ARRIVED
        if "ARRIVED" in serial_data:
            print("<- Received 'ARRIVED'. Capturing image...")

            # 📸 CAPTURE LOGIC
            ret, frame = cap.read()
            if ret:
                img_count += 1 
                filename = os.path.join(save_path, f"shot_{img_count}.jpg") 
                cv2.imwrite(filename, frame)
                captured_files.append(filename)
                print(f"📸 บันทึก {filename}")
                sc.send_serial_command("CAPTURED")


        # 4. ตรวจสอบสัญญาณสิ้นสุด
        if "REPORT_END" in serial_data :
            print("🛑 Received SCAN_FINISHED signal. Halting.")
            break

        time.sleep(0.05)  # พักเล็กน้อย

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Capture loop finished.")
    
    # 🎯 Return True ถ้ามีไฟล์ภาพอย่างน้อย 1 ไฟล์
    return len(captured_files) > 0, captured_files


def stitch_img(captured_files):
    # โหลดภาพที่เพิ่งถ่ายมา stitch
    images = [cv2.imread(f) for f in captured_files] 
    images = [img for img in images if img is not None] # กรองภาพที่โหลดไม่สำเร็จ

    save_path = "Model/stitched/"
    os.makedirs(save_path, exist_ok=True)
    img_path = os.path.join(save_path, "stitched.jpg")

    if len(images) < 2:
        print("❌ Stitching ไม่สำเร็จ: มีภาพไม่เพียงพอสำหรับการต่อภาพ (Need >= 2).")
        # 🎯 FIX: Fallback ไปใช้ภาพแรกสุด (ถ้ามี)
        fallback_path = captured_files[0] if captured_files else img_path
        return False, fallback_path 

    try:
        stitcher = cv2.Stitcher_create(cv2.Stitcher_SCANS)  # ใช้โหมด SCANS
        (status, stitched) = stitcher.stitch(images)

        if status == cv2.Stitcher_OK:
            cv2.imwrite(img_path, stitched)
            print("✅ Stitching สำเร็จ. File:", img_path)
            return True, img_path
        else:
            print(f"❌ Stitching ไม่สำเร็จ, status = {status}")
            # 🎯 FIX: Fallback ไปใช้ภาพแรกสุด
            fallback_path = captured_files[0] if captured_files else img_path
            return False, fallback_path
            
    except Exception as e:
        print(f"❌ Stitching Failed with Exception: {e}")
        fallback_path = captured_files[0] if captured_files else img_path
        return False, fallback_path