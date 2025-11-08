# -*- coding: utf-8 -*-
import serial , time, os , sys
from serial.tools import list_ports

# ----------------------------------------------------
# 1. การตั้งค่า PORT และ Global Variable
# ----------------------------------------------------

# ⚠️ ดึงชื่อ Serial Port จาก Environment Variable ที่ตั้งไว้ใน Terminal
SERIAL_PORT_NAME = os.environ.get("SERIAL_PORT")
BAUD_RATE = 115200  # Baud Rate ที่ตรงกับ Arduino/ESP32 (คุณเปลี่ยนเป็น 115200 แล้ว)
ser = None  # ตัวแปรสำหรับเก็บ Serial Connection


def find_available_ports():
    """ค้นหาและแสดงรายการ Serial Port ที่ใช้งานได้ทั้งหมด"""
    ports = list_ports.comports()
    # ... (โค้ดส่วนนี้คงเดิม)
    if not ports:
        print("💡 ไม่พบ Serial Port ใดๆ ในระบบ")
        return []

    print("\n--- Serial Ports ที่ตรวจพบ ---")
    available_ports = []
    for port in ports:
        print(f"  - PORT: {port.device} | DESCRIPTION: {port.description}")
        available_ports.append(port.device)
    print("------------------------------")
    return available_ports


def initialize_serial_connection():
    """เริ่มต้นการเชื่อมต่อ Serial Port"""
    global ser
    # ⚠️ แทนที่ COM4 ด้วย PORT ที่คุณต้องการใช้ทดสอบจริง (COM4 ในกรณีของคุณ)
    os.environ["SERIAL_PORT"] = "COM4"

    # ดึงค่า SERIAL_PORT_NAME ใหม่จาก Environment ที่เพิ่งตั้ง
    SERIAL_PORT_NAME = os.environ.get("SERIAL_PORT")

    # 1. ตรวจสอบว่ามีการกำหนดชื่อ PORT หรือไม่
    if not SERIAL_PORT_NAME:
        print(
            "❌ ERROR: กรุณากำหนด SERIAL_PORT Environment Variable (เช่น set SERIAL_PORT=COM3)"
        )
        find_available_ports()
        return False

    # 2. ตรวจสอบว่ามีการเชื่อมต่ออยู่แล้วหรือไม่
    if ser and ser.is_open:
        print(f"✅ Connection to {SERIAL_PORT_NAME} already open.")
        return True

    # 3. ลองเชื่อมต่อ
    try:
        print(f"🔄 Attempting to connect to {SERIAL_PORT_NAME} at {BAUD_RATE}...")
        ser = serial.Serial(SERIAL_PORT_NAME, BAUD_RATE, timeout=1)
        time.sleep(2)  # ให้เวลา Arduino/ESP32 รีเซ็ต

        # 🎯 FIX: Clear any junk data in the buffer from startup messages
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print(f"✅ Successfully connected to {SERIAL_PORT_NAME}")
        return True
    except serial.SerialException as e:
        print(f"❌ ERROR: Cannot open serial port {SERIAL_PORT_NAME}. Error: {e}")
        find_available_ports()
        return False


def send_serial_command(command: str) -> str:
    """
    ส่งคำสั่งไปยัง Arduino/ESP32 และรอรับการตอบกลับ
    :param command: ข้อความคำสั่งที่ต้องการส่ง (เช่น 'WATER_ALL', 'WATER_ZONE:A')
    :return: ข้อความตอบกลับจากอุปกรณ์
    """
    global ser
    # ... (โค้ดส่วนนี้คงเดิม)
    if not initialize_serial_connection():
        return "ERROR: Serial Connection Failed."
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # clear buffer
            ser.reset_input_buffer()

            command_bytes = (command + "\n").encode("utf-8")
            ser.write(command_bytes)
            print(f"-> Sent command (Attempt {attempt + 1}: {command})")

            # waiting response
            time.sleep(1)

            if ser.in_waiting > 0:
                # readline waiting response
                response_line = ser.readline().decode("utf-8", errors= 'ignore').strip()
                return response_line if response_line else "TIMEOUT : Empty response."
            
            if attempt < max_attempts - 1:
                time.sleep(0.5)
                continue
        except UnicodeDecodeError as e:
            print(f"❌ ERROR: Decoding failed: {e}. Clearing buffer and retrying.")
            time.sleep(0.5)
        except Exception as e:
            return f"Fatal_Error: {e}"
        
    return "ERROR: Max retry attempts reached (TIMEOUT)."

def close_serial_connection():
    """ปิดการเชื่อมต่อ Serial Port"""
    # ... (โค้ดส่วนนี้คงเดิม)
    global ser
    if ser and ser.is_open:
        print(f"🧹 Closing serial connection to {SERIAL_PORT_NAME}...")
        ser.close()
        ser = None
        print("✅ Connection closed.")


def read_all_available() -> str:
        """Reads all available data from the buffer without blocking."""
        # 🎯 FIX: ต้องประกาศใช้ global ser เพื่อให้เข้าถึง Object การเชื่อมต่อได้
        global ser

        if not ser or not ser.is_open:
            return "ERROR: Serial Connection Not Ready"
        
        # Check if any data is waiting in the input buffer
        if ser.in_waiting > 0:
            # Read all bytes available in the buffer
            return ser.read_all().decode('utf-8', errors= 'ignore') # ⬅️ นี่คือ Method ที่ถูกต้อง
        return ""
# ----------------------------------------------------
# ฟังก์ชันสำหรับการทดสอบ (สามารถรันแยกเพื่อทดสอบ Serial ได้)
# ----------------------------------------------------
# if __name__ == "__main__":
#     # 🎯 FIX: กำหนดค่า SERIAL_PORT เป็น Environment Variable ชั่วคราว
#     #        เพื่อให้โค้ดส่วนบน (initialize_serial_connection) สามารถอ่านได้

#     # ⚠️ แทนที่ COM4 ด้วย PORT ที่คุณต้องการใช้ทดสอบจริง (COM4 ในกรณีของคุณ)
#     os.environ["SERIAL_PORT"] = "COM4"

#     # ดึงค่า SERIAL_PORT_NAME ใหม่จาก Environment ที่เพิ่งตั้ง
#     SERIAL_PORT_NAME = os.environ.get("SERIAL_PORT")

#     find_available_ports()

#     if initialize_serial_connection():

#         user_input = ""
#         print("\n--- Starting Continuous Serial Test ---")

#         # 🎯 โครงสร้างการวนลูปที่ถูกต้องตามหลักการ Python
#         while user_input != "0":
#             user_input = input()
#             # ส่งคำสั่ง 'r' (หรือคำสั่งใดๆ ที่ ESP32 คาดหวัง)
#             send_serial_command(user_input)
#             # response = receive_multi_line_report()
#             # print(f"Test Result: {response}")

#             # อัปเดตตัวแปรสำหรับตรวจสอบเงื่อนไข
#             # Note: ต้องมั่นใจว่า ESP32 ส่ง '0' หรือ '1' กลับมา
#             # test_response = response.strip()

#             # หยุดลูปชั่วคราวเพื่อป้องกันการรันที่เร็วเกินไป
#             time.sleep(0.5)

#         print("✅ Continuous test stopped because device returned '0'.")
#         close_serial_connection()
