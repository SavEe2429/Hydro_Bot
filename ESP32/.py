import qrcode

def generate_qr(link, filename):
    # สร้างวัตถุ QR Code พร้อมกำหนดค่าเบื้องต้น
    qr = qrcode.QRCode(
        version=1, # ขนาดของ QR Code (1 คือเล็กสุด)
        error_correction=qrcode.constants.ERROR_CORRECT_L, # ระดับการกู้คืนข้อมูล
        box_size=10, # ขนาดของแต่ละช่องสี่เหลี่ยม
        border=4, # ความหนาของขอบขาว
    )
    
    # ใส่ลิงก์ที่ต้องการ
    qr.add_data(link)
    qr.make(fit=True)

    # สร้างรูปภาพ (สีดำบนพื้นขาว)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # บันทึกไฟล์
    img.save(filename)
    print(f"สร้าง QR Code สำเร็จ! บันทึกไฟล์เป็น: {filename}")

# เรียกใช้งาน
generate_qr("https://drive.google.com/file/d/1xqWgWtNKv_KIgQ-3Lv9N3oAC96OiIvcG/view?usp=sharing", "my_qrcode.png")