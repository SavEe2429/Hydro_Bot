import cv2, sys ,os
from ultralytics import YOLO
import numpy as np
from math import sqrt
import json

def detect_ai(stitched_img_path):
    save_path = "Model/img_detection"
    os.makedirs(save_path, exist_ok=True)
    
    # 🎯 FIX: สร้าง Dictionary สำหรับคืนค่าผลลัพธ์ที่สอดคล้อง
    output_data = {
        "status": False, # สถานะเริ่มต้นคือล้มเหลว
        "output_path": stitched_img_path, # Default: ใช้ Path ภาพเดิม
        "object_count": 0,
        "object_order": [],
        "objects": []
    }

    try:
        # โหลดโมเดล
        model = YOLO("Model/best.pt")

        # โหลดภาพ
        results = model(stitched_img_path)
        
        # 1. จัดการกรณีไม่พบวัตถุ
        if not results or not results[0].boxes or results[0].boxes.xyxy.shape[0] == 0:
            output_data["status"] = True # ถือว่า AI ทำงานสำเร็จ แม้จะไม่เจอวัตถุ
            print("INFO: AI Detection completed, but no objects found.")
            return output_data

        # ดึง bounding boxes
        boxes = results[0].boxes.xyxy.cpu().numpy()  # [num_objects, 4]
        centers = np.array([[(x1 + x2) / 2, (y1 + y2) / 2] for x1, y1, x2, y2 in boxes])

        # 2. คำนวณความสูงแถวและจัดกลุ่ม (Zig-Zag Sorting Logic)
        heights = [box[3] - box[1] for box in boxes]
        row_height = int(np.mean(heights) * 1.2) if len(heights) > 0 else 100
        rows = {}
        for idx, (cx, cy) in enumerate(centers):
            row_idx = int(cy // row_height)
            if row_idx not in rows:
                rows[row_idx] = []
            rows[row_idx].append((cx, idx))
        
        # 3. เรียงลำดับ Zig-Zag
        sorted_indices = []
        for row_idx in sorted(rows.keys()):
            row_items = rows[row_idx]
            if row_idx % 2 == 0:  # แถวคู่ -> ซ้ายไปขวา
                row_sorted = sorted(row_items, key=lambda x: x[0])
            else:  # แถวคี่ -> ขวาไปซ้าย 
                row_sorted = sorted(row_items, key=lambda x: x[0], reverse=True)
            sorted_indices.extend([idx for cx, idx in row_sorted])

        # 4. วาดผลลัพธ์และบันทึกข้อมูล
        img = cv2.imread(stitched_img_path)
        if img is None:
            raise FileNotFoundError(f"Failed to load stitched image: {stitched_img_path}")

        output_img_path = os.path.join(save_path, "detected.jpg")
        
        
        # วาดกล่องพร้อมเรียงลำดับและเก็บข้อมูลศูนย์กลาง
        for i, original_box_idx in enumerate(sorted_indices):
            x1, y1, x2, y2 = map(int, boxes[original_box_idx])
            cx1, cy1 = (x1 + x2) // 2, (y1 + y2) // 2

            # วาด: กล่อง, จุดศูนย์กลาง, หมายเลขลำดับ
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(img, (cx1, cy1), 5, (0, 0, 255), -1)
            cv2.putText(img, f"{i+1}", (x1, y2 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
            
            # บันทึกค่ากึ่งกลางของวัตถุที่เจอ
            output_data["objects"].append({
                "object_id": i + 1, # Start ID from 1
                "center_x": cx1, 
                "center_y": cy1,
            })
            
            cv2.putText(img, f"({cx1},{cy1})", (cx1 - 50, cy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # บันทึกไฟล์
        cv2.imwrite(output_img_path , img)

        # ลากเส้นเชื่อม
        for i in range(len(sorted_indices) - 1):
            idx1 = sorted_indices[i]
            idx2 = sorted_indices[i+1]
            cx1, cy1 = map(int, centers[idx1])
            cx2, cy2 = map(int, centers[idx2])

            dist = sqrt((cx2 - cx1)**2 + (cy2 - cy1)**2)
            mid_x, mid_y = (cx1 + cx2)//2, (cy1 + cy2)//2
            
            cv2.line(img, (cx1, cy1), (cx2, cy2), (255, 0, 0), 2)
            cv2.putText(img, f"{dist:.1f}", (mid_x, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)


        cv2.imwrite(output_img_path, img)
        
        # 5. บันทึก JSON
        with open("Model/output.json", "w") as f:
            json.dump(output_data, f, indent=4)
            
        # 6. คืนค่าสำเร็จ
        output_data["status"] = True
        output_data["output_path"] = output_img_path
        output_data["object_count"] = len(sorted_indices)
        output_data["object_order"] = [i+1 for i in range(len(sorted_indices))] # 1-based index 

        return output_data

    except Exception as e:
        print(f"FATAL ERROR in AI Detection: {e}")
        # 🎯 FIX: คืนค่า Dictionary ล้มเหลว (status=False)
        output_data["message"] = str(e)
        return output_data