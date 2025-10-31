import cv2
import os
import subprocess

save_path = "captured_shots"
os.makedirs(save_path, exist_ok=True)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ ไม่สามารถเปิดกล้องได้")
    exit()
# 🔥 Warm-up กล้อง อ่านเฟรมทิ้งไป 10 ครั้ง
for i in range(10):
    cap.read()

shots = 3  # จำนวนภาพที่ต้องการถ่าย
interval = 3  # วินาทีเว้นระหว่างการถ่าย
captured_files = []

for img_length in range(shots):
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Live", frame)

    filename = os.path.join(save_path, f"shot_{img_length+1}.jpg")
    cv2.imwrite(filename, frame)
    captured_files.append(filename)
    print(f"📸 บันทึก {filename}")

    # รอ interval วินาที หรือถ้ากด q จะออกก่อน
    if cv2.waitKey(interval * 1000) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("✅ ถ่ายครบแล้ว ปิดกล้อง")

# โหลดภาพที่เพิ่งถ่ายมา stitch
images = [cv2.imread(img_length) for img_length in captured_files]

stitcher = cv2.Stitcher_create(cv2.Stitcher_SCANS)  # ใช้โหมด SCANS
(status, stitched) = stitcher.stitch(images)

save_path = "img_detection"
os.makedirs(save_path, exist_ok=True)
img_path = "img_detection/stitched.jpg"

if status == cv2.Stitcher_OK:
    cv2.imwrite(img_path, stitched)
    # cv2.imshow("Stitched Image", stitched)
else:
    print("❌ Stitching ไม่สำเร็จ, status =", status)

# Resize และบันทึกทับไฟล์ stitched
# img = cv2.imread(img_path)
# img = cv2.resize(img, (640, 640))
# cv2.imwrite(img_path, img)   # ✅ บันทึกกลับ

print("file : ",img_path)
# subprocess.run(['python' , 'detect.py' , img_path])