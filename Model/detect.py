import cv2, sys
from ultralytics import YOLO
import numpy as np
from math import sqrt
import json

img_path = "train/images/20251030_225606_jpg.rf.5dee77d50916ea62df868e974f7dc5f3.jpg"
# img_path = sys.argv[1]

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
data = {"camera_center": [], "objects": []}

# ลากเส้นระหว่างวัตถุ
for i in range(len(sorted_indices) - 1):
    idx1 = sorted_indices[i]
    idx2 = sorted_indices[i+1]

    # เอากล่องของ id1 และ id2
    x1, y1, x2, y2 = map(int, boxes[idx1])
    cx1, cy1 = (x1 + x2) // 2, (y1 + y2) // 2

    print("id : " , i)

    x1_, y1_, x2_, y2_ = map(int, boxes[idx2])
    cx2, cy2 = (x1_ + x2_) // 2, (y1_ + y2_) // 2

    # คำนวณระยะทาง
    dist = sqrt((cx2 - cx1)**2 + (cy2 - cy1)**2)
    distances.append(dist)


    print(f"Distance ID{i+1} -> ID{i+2} = {dist:.2f} px")

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

    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.circle(img, (cx1, cy1), 5, (0, 0, 255), -1)
    
    print("id : " , i)

    # บันทึกค่ากึ่งกลางของวัตถุที่เจอ
    # บันทึกลง JSON
    data["objects"].append({
        "object_id": i,
        "object_center": [cx1, cy1]
    })

    cv2.putText(img, f"{i+1}", (x1, y2-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
    cv2.putText(img, f"{cx1,cy1}", (cx1-50, cy1-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
cv2.imshow("Zig-Zag Order", img)
cv2.waitKey(0)

# เปิดกล้อง (0 = default webcam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ ไม่สามารถเปิดกล้องได้")
    exit()

while True:
    ret, img = cap.read()
    if not ret:
        print("❌ ไม่สามารถอ่านภาพจากกล้องได้")
        break

    # Detect วัตถุ
    results = model(img ,verbose=False)
    boxes = results[0].boxes.xyxy.cpu().numpy()

    # หาจุดกึ่งกลางกล้อง
    h, w = img.shape[:2]
    cx_cam, cy_cam = w // 2, h // 2
    cv2.circle(img, (cx_cam, cy_cam), 5, (255, 0, 0), -1)  # กล้อง center
    

    for idx, (x1, y1, x2, y2) in enumerate(boxes):
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

        # center ของ object
        cx_obj, cy_obj = (x1 + x2) // 2, (y1 + y2) // 2
        cv2.circle(img, (cx_obj, cy_obj), 5, (0, 0, 255), -1)

        # คำนวณระยะห่าง (pixel distance)
        dx, dy = cx_obj - cx_cam, cy_obj - cy_cam
        distance = sqrt(dx**2 + dy**2)

        # วาดกล่อง
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # แสดงระยะห่าง
        text = f"ID:{idx+1} Dist:{distance:.1f}"
        cv2.putText(img, text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 3, cv2.LINE_AA)
        cv2.putText(img, text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1, cv2.LINE_AA)

        # ถ้าใกล้พอ (<=10 pixels) → ถึงแล้ว
        if distance <= 10:
            cv2.putText(img, "Arrived", (cx_obj, cy_obj - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    # แสดงผล
    cv2.imshow("Camera Detection", img)

    # บันทึก JSON ทุก frame (ถ้าต้องการ)
    with open("output.json", "w") as f:
        json.dump(data, f, indent=4)

    # กด q เพื่อออก
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

