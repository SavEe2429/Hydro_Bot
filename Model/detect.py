import cv2, sys ,os
from ultralytics import YOLO
import numpy as np
from math import sqrt
import json

def detect_ai():
    save_path = "Model/img_detection"
    os.makedirs(save_path, exist_ok=True)
    img_path = "Model/stitched/stitched.jpg"

    # โหลดโมเดล
    model = YOLO("Model/best.pt")

    # โหลดภาพ
    results = model(img_path)

    # ดึง bounding boxes
    boxes = results[0].boxes.xyxy.cpu().numpy()  # [num_objects, 4]

    # คำนวณจุดศูนย์กลางของแต่ละกล่อง
    centers = np.array([[(x1 + x2) / 2, (y1 + y2) / 2] for x1, y1, x2, y2 in boxes])
    print(centers)
    # กำหนดความสูงของแถวแบบ dynamic จากค่าเฉลี่ยความสูงกล่อง
    heights = [box[3] - box[1] for box in boxes]
    row_height = int(np.mean(heights) * 1.2) if len(heights) > 0 else 100
    print("Auto row_height =", row_height)

    # จัดกลุ่มวัตถุตามแถว (y center)

    rows = {}
    for idx, (cx, cy) in enumerate(centers):
        row_idx = int(cy // row_height)  # แถวที่เป็น int
        print("idx : ", idx, "cx : ", cx, "cy : ", cy)
        if row_idx not in rows:
            rows[row_idx] = []
        rows[row_idx].append((cx, idx))  # เก็บ cx และ index ของกล่อง
        print("rows : ", rows)

    # เรียงแต่ละแถว
    sorted_indices = []
    for row_idx in sorted(rows.keys()):
        row_items = rows[row_idx]
        # สลับทิศทางแถว zig-zag
        if row_idx % 2 == 0:  # แถวคู่ -> ซ้ายไปขวา
            row_sorted = sorted(row_items, key=lambda x: x[0])
        else:  # แถวคี่ -> ขวาไปซ้าย 
            row_sorted = sorted(row_items, key=lambda x: x[0], reverse=True)
        sorted_indices.extend([idx for cx, idx in row_sorted])
    print("Sorted_indices : " , sorted_indices)
    # วาดกล่องพร้อมเรียงลำดับ
    img = cv2.imread(img_path)


    # หาจุดกึ่งกลางของรูป
    h, w = img.shape[:2]
    # print("W : " , w , "H : " ,h)
    cx_img, cy_img = w // 2, h // 2
    cv2.circle(img, (cx_img, cy_img), 5, (255, 0, 0), -1)

    distances = []  # เก็บผลลัพธ์ระยะทาง
    data = {"obj_count" : len(sorted_indices) ,"objects": []}

    # หาจุดตรงกลาง
    for i in range(len(sorted_indices)):
        idx1 = sorted_indices[i]

        # หาค่าจากกล่องรูป
        x1, y1, x2, y2 = map(int, boxes[idx1])
        cx1, cy1 = (x1 + x2) // 2, (y1 + y2) // 2

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(img, (cx1, cy1), 5, (0, 0, 255), -1)
        cv2.putText(img, f"{i+1}", (x1, y2-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

    cv2.imwrite('Model/img_detection/detected.jpg', img)

    # ลากเส้นระหว่างวัตถุ
    for i in range(len(sorted_indices) - 1):
        idx1 = sorted_indices[i]
        idx2 = sorted_indices[i+1]

        # เอากล่องของ id1 และ id2
        x1, y1, x2, y2 = map(int, boxes[idx1])
        cx1, cy1 = (x1 + x2) // 2, (y1 + y2) // 2

        x1_, y1_, x2_, y2_ = map(int, boxes[idx2])
        cx2, cy2 = (x1_ + x2_) // 2, (y1_ + y2_) // 2

        # คำนวณระยะทาง
        dist = sqrt((cx2 - cx1)**2 + (cy2 - cy1)**2)
        distances.append(dist)
        # print(f"Distance ID{i+1} -> ID{i+2} = {dist:.2f} px")

        # วาดเส้นเชื่อม ID
        cv2.line(img, (cx1, cy1), (cx2, cy2), (255, 0, 0), 2)
        # วาดระยะตรงกลางเส้น
        mid_x, mid_y = (cx1 + cx2)//2, (cy1 + cy2)//2
        cv2.putText(img, f"{dist:.1f}", (mid_x, mid_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
        cv2.putText(img, f"{i+1}", (x1, y2-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)


    # หาจุดตรงกลาง
    for i in range(len(sorted_indices)):
        idx1 = sorted_indices[i]

        # หาค่าจากกล่องรูป
        x1, y1, x2, y2 = map(int, boxes[idx1])
        cx1, cy1 = (x1 + x2) // 2, (y1 + y2) // 2

        # บันทึกค่ากึ่งกลางของวัตถุที่เจอ
        # บันทึกลง JSON
        data["objects"].append({
            "object_id": i,
            "object_center": [cx1, cy1]
        })

        cv2.putText(img, f"{cx1,cy1}", (cx1-50, cy1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

    # บันทึก JSON ทุก frame (ถ้าต้องการ)
    with open("Model/output.json", "w") as f:
        json.dump(data, f, indent=4)
