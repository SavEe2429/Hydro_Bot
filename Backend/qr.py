import qrcode
from PIL import Image

# 1. กำหนดข้อมูลที่คุณต้องการเข้ารหัสใน QR Code
data_to_encode = "https://savee2429.github.io/Hydro_Bot/#/"  # หรือข้อความที่คุณต้องการ

# 2. สร้างอ็อบเจกต์ QRCode
# version=1: ตั้งค่าเป็นค่าเริ่มต้น
# error_correction=qrcode.constants.ERROR_CORRECT_L: กำหนดระดับการแก้ไขข้อผิดพลาด (L, M, Q, H)
# box_size=10: กำหนดจำนวนพิกเซลสำหรับแต่ละ 'กล่อง' ของ QR Code
# border=4: กำหนดความหนาของขอบสีขาวรอบ QR Code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # ใช้ระดับ H เพื่อการแก้ไขข้อผิดพลาดสูงสุด
    box_size=10,
    border=4,
)

# 3. เพิ่มข้อมูลเข้าไปในอ็อบเจกต์
qr.add_data(data_to_encode)
qr.make(fit=True)

# 4. สร้างรูปภาพ QR Code
# fill_color: สีของสี่เหลี่ยมด้านใน (ตามปกติคือสีดำ)
# back_color: สีพื้นหลัง (ตามปกติคือสีขาว)
img = qr.make_image(fill_color="black", back_color="white")

# 5. บันทึกรูปภาพ
file_name = "my_qr_code.png"
img.save(file_name)

print(f"สร้าง QR Code เรียบร้อยแล้ว: {file_name}")