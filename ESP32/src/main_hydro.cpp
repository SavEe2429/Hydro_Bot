#include <Arduino.h>
//https://docs.google.com/document/d/1Vxh6Z6RBmllpE-TCUfmOebgBQnEqvF-Deb4upEB9mnA/edit?tab=t.0

// Motor pins
#define Limit_X 18
#define Limit_Z 4
#define Relay_Pump 23
const int A_IN1 = 14, A_IN2 = 12, A_IN3 = 13, A_IN4 = 15; // X
const int B_IN1 = 27, B_IN2 = 26, B_IN3 = 25, B_IN4 = 33; // Z

// Step sequence
const int STEP_SEQ[8][4] = {
    {1, 0, 0, 0}, {1, 1, 0, 0}, {0, 1, 0, 0}, {0, 1, 1, 0},
     {0, 0, 1, 0}, {0, 0, 1, 1}, {0, 0, 0, 1}, {1, 0, 0, 1}};

const int STEPS_PER_REV = 4096; // สร้างตัวแปรความละเอียดการเคลื่อนที่ของมอเตอร์
const int STEP_DELAY = 800; // สร้างตัวแปรระยะเวลาหน่วงของการทำงานแต่ละรอบ
const float DIST_PER_REV = 15.71; // ความยาวรอบเพลา
const float HOME_OFFSET_MM = 3;  // กำหนดระยะที่ต้องการให้ถอยออกมาหลังจากชนกับ limit switch
// Motor state
float stepsToMoveX = 0, stepsToMoveZ = 0; // จำนวนหน่วยเคลื่อนที่ของมอเตอร์ที่จะต้องขยับไป
int dirX = 1, dirZ = 1; // ทิศทางเริ่มต้นของมอเตอร์ 1 = MotorZ = ซ้าย/MotorX = บน
int seqIndexX = 0, seqIndexZ = 0; // ลำดับการทำงานของ motor ที่ต้องทำงานในขณะนั้น
unsigned long lastStepTimeX = 0, lastStepTimeZ = 0;// เก็บเวลาล่าสุดที่ทำงานไป
float currentPosX = 0, currentPosZ = 0;// หน่วยการเคลื่อนที่ล่าสุดที่เคลื่อนที่ได้

// จำนวนหน่วยเคลื่อนที่ถอยหลัง
long backoffSteps = (HOME_OFFSET_MM / DIST_PER_REV) * STEPS_PER_REV;

// สูตรมาจาก จำนวนรอบที่ต้องหมุนในระยะถอยหลัง * ค่าความละเอียดของการทำงานมอเตอร์
// จำนวนรอบที่ต้องหมุนในระยะถอยหลัง = ระยะที่จะถอย / ความยาวรอบเพลา = 3 / 15.71
// ค่าความละเอียดของการทำงานมอเตอร์ = 4096

// เป็นตัวเช็คว่า limit switch ทำงานรึยัง
bool flagX, flagZ;

// targetX/Z คือ พิกัดที่จะเคลื่อนที่ไป diffX/Z ค่าพิกัดเป้าหมาย - พิกัดปัจจุบัน
// เพื่อรู้ได้ว่าต้องเคลื่อนที่ห่างจากจุดปัจจุบันเท่าไหร่
float targetX, diffX, targetZ, diffZ;

่// เป็นตัวเช็คว่าตอนนี้กำลังทำฟังก์ชัน doHoming อยู่รึป่าว
bool isdohoming = false;

// ระยะเริ่มต้นและระยะสุดท้ายของแกน X
float X_MIN_POS = 300.0, X_MAX_POS = 900.0; 
float Z_CEN_POS = 670.0; // ระยะกึ่งกลางของแกน Z

// ================= Interrupt =================
void IRAM_ATTR LimitInteruptX()
{
  flagX = true;

  dirX = (currentPosX > 18413) ? -1 : 1;
}
void IRAM_ATTR LimitInteruptZ()
{
  flagZ = true;

  dirZ = (currentPosZ > 9843) ? -1 : 1;
}

// ================= Step Motor =================
void setOutputs(int in1, int in2, int in3, int in4, const int pattern[4])
{
  digitalWrite(in1, pattern[0]);
  digitalWrite(in2, pattern[1]);
  digitalWrite(in3, pattern[2]);
  digitalWrite(in4, pattern[3]);
}
void stopMotor(int in1, int in2, int in3, int in4)
{
  digitalWrite(in1, 0);
  digitalWrite(in2, 0);
  digitalWrite(in3, 0);
  digitalWrite(in4, 0);
}

void stepMotorX()
{
  if (micros() - lastStepTimeX >= STEP_DELAY)
  {
    seqIndexX = (seqIndexX + dirX + 8) % 8;
    setOutputs(A_IN1, A_IN2, A_IN3, A_IN4, STEP_SEQ[seqIndexX]);
    lastStepTimeX = micros();
    currentPosX += dirX;
    // printf("CurrentPosX : %d\n", currentPosX);
    stepsToMoveX--;
  }
}
void stepMotorZ()
{
  if (micros() - lastStepTimeZ >= STEP_DELAY)
  {
    seqIndexZ = (seqIndexZ + dirZ + 8) % 8;
    setOutputs(B_IN1, B_IN2, B_IN3, B_IN4, STEP_SEQ[seqIndexZ]);
    lastStepTimeZ = micros();
    currentPosZ += dirZ;
    // printf("CurrentPosZ : %d\n", currentPosZ);
    stepsToMoveZ--;
  }
}

// ================= Move To =================
void moveX_to(float distance_pixel)
{
  targetX = distance_pixel * 40.92;
  diffX = targetX - currentPosX;
  dirX = (diffX >= 0) ? 1 : -1;
  stepsToMoveX = abs(diffX);
}
void moveZ_to(float distance_pixel)
{
  targetZ = distance_pixel * 29.38;
  diffZ = targetZ - currentPosZ;
  dirZ = (diffZ >= 0) ? 1 : -1;
  stepsToMoveZ = abs(diffZ);
  // printf("targetZ : %.2f , currentZ : %.2f , diffZ : diffZ : %.2f , stepstomoveZ : %.2f\n",targetZ,currentPosZ,diffZ,stepsToMoveZ);
}

void backoffX()
{
  detachInterrupt(digitalPinToInterrupt(Limit_X));
  flagX = false;
  for (long i = 0; i < backoffSteps; i++)
  {
    stepMotorX();
    delayMicroseconds(STEP_DELAY);
  }
  stopMotor(A_IN1, A_IN2, A_IN3, A_IN4);
  attachInterrupt(digitalPinToInterrupt(Limit_X), LimitInteruptX, FALLING);
  stepsToMoveX = 0;
  // currentPosX = 0;
}

void backoffZ()
{
  detachInterrupt(digitalPinToInterrupt(Limit_Z));
  flagZ = false;
  for (long i = 0; i < backoffSteps; i++)
  {
    stepMotorZ();
    delayMicroseconds(STEP_DELAY);
  }
  stopMotor(B_IN1, B_IN2, B_IN3, B_IN4);
  attachInterrupt(digitalPinToInterrupt(Limit_Z), LimitInteruptZ, FALLING);
  stepsToMoveZ = 0;
  // currentPosZ = 0;
}

// ================= Homing Function =================
void doHoming()
{
  isdohoming = true;
  // ---------- Homing X (Blocking, Silent) ----------
  dirX = -1;
  while (!flagX)
  {
    stepMotorX();
  } // ⬅️ Blocking (ต้องพึ่งพา stepMotorX Non-Blocking)
  backoffX();
  flagX = false;
  currentPosX = 0;

  // ---------- Homing Z (Blocking, Silent) ----------
  dirZ = -1;
  while (!flagZ)
  {
    stepMotorZ();
  }
  backoffZ();
  flagZ = false;
  currentPosZ = 0;

  isdohoming = false;
}

// 🎯 SCAN STATE MACHINE VARIABLES
enum State
{
  // ===================  Default  =====================
  IDLE,
  HOMING,

  // ===================  Scan  =====================
  MOVING_SCAN_Z,
  MOVING_SCAN_X,
  HOMING_SCAN,
  WAITING_ACK,
  SCANNING_X_MOVE,
  WAITING_ACK_X,
  SCAN_COMPLETE,

  // ===================  Watering  =====================
  MOVING_WATER_Z,
  MOVING_WATER_X,
  WATER_COMPLETE
};

State currentState = IDLE; // เป็นการกำหนด สถานะ เริ่มต้น
int currentShot = 0; // จำนวนที่ได้ถ่ายไปล่าสุด
int totalShots = 0; // จำนวนที่ต้องถ่าย
float currentGap = 0.0; // ค่าความห่างชดเชยหลังจากที่รวมรูป

int id; // เก็บ id ที่ส่งมา
String incomingCommand = ""; // เก็บ คำสั่งทั้งหมด ที่ส่งมา
String currentCommand = ""; // เก็บ คำสั่งที่ทำการแยกออกมาจาก incomingCommand 

// Relay
unsigned long startTime = 0; // เวลาเริ่มต้น
const long duration = 3000; // 3000 มิลลิวินาที = 3 วินาที
bool pump_active = false;   // สถานะเริ่มต้น

// ----------------------------------------------------
// 🎯 NON-BLOCKING SCAN/MOVE LOGIC
// ----------------------------------------------------

void handleScan()
{
  switch (currentState)
  {
  case IDLE:
    break;

  case HOMING:
    doHoming();
    currentState = IDLE;
    break;

  case HOMING_SCAN:
    // 1. ทำ Homing แบบ Blocking
    doHoming();
    moveZ_to(Z_CEN_POS / 2);
    currentState = MOVING_SCAN_Z; // ไปสถานะถัดไป
    break;

  case MOVING_SCAN_Z:
    // 2. ขยับ Z ไปตรงกลาง (Non-Blocking Move Init)
    // 💡 Logic: ถ้า stepsToMoveZ ยัง > 0 ให้ stepMotorZ ใน loop() จัดการต่อ
    if (stepsToMoveZ <= 0)
    {
      // ถ้าขยับเสร็จแล้ว (stepMotorZ ลด stepsToMoveZ จนหมด)
      stopMotor(B_IN1, B_IN2, B_IN3, B_IN4);
      Serial.println("WAITING_COMMAND"); // ⬅️ สั่งให้ Python ส่ง CAPTURE:shots
      Serial.flush();
      currentState = WAITING_ACK;
    }
    break;

  case WAITING_ACK:
    // 3. รอคำสั่ง CAPTURE:shots จาก Python ใน processCommand()
    break;

  case SCANNING_X_MOVE:
    // 4. ขยับ X ไปจุดถัดไป (Non-Blocking Move Init)
    Serial.println(currentShot);
    if (currentShot < totalShots)
    {
      float spotX = min(X_MIN_POS + (currentGap * currentShot), X_MAX_POS - 50);
      moveX_to(spotX);
      currentState = MOVING_SCAN_X;
    }
    else
    {
      // 5. สแกนครบแล้ว
      currentState = SCAN_COMPLETE;
    }
    break;

  case MOVING_SCAN_X:
    // 6. รอให้ stepsToMoveX เสร็จ
    if (stepsToMoveX <= 0)
    {
      // 7. ถึงจุดแล้ว: ส่งสัญญาณ ARRIVED ไป Python
      stopMotor(A_IN1, A_IN2, A_IN3, A_IN4);
      Serial.println("ARRIVED");
      Serial.flush();
      currentState = WAITING_ACK_X; // เข้าสู่สถานะรอ CAPTURED
    }
    break;

  case WAITING_ACK_X:
    // 8. รอการตอบรับ 'CAPTURED' จาก Python ใน processCommand()
    break;

  case SCAN_COMPLETE:
    // stopMotor(A_IN1, A_IN2, A_IN3, A_IN4);
    doHoming();                   // กลับไป Home เมื่อเสร็จสิ้น
    Serial.println("REPORT_END"); // ⬅️ ส่งสัญญาณจบงาน
    Serial.flush();
    currentState = IDLE;
    break;

  // ------------------------ WATERING -----------------------------------
  case MOVING_WATER_Z:
    if (stepsToMoveZ <= 0)
    {
      // ถ้าขยับเสร็จแล้ว (stepMotorZ ลด stepsToMoveZ จนหมด)
      stopMotor(B_IN1, B_IN2, B_IN3, B_IN4);
      // Serial.println("WAITING_COMMAND"); // ⬅️ สั่งให้ Python ส่ง CAPTURE:shots
      // Serial.flush();
      currentState = MOVING_WATER_X;
    }
    break;

  case MOVING_WATER_X:
    if (stepsToMoveX <= 0)
    {
      stopMotor(A_IN1, A_IN2, A_IN3, A_IN4);
      // Serial.println("WAITING_COMMAND"); // ⬅️ สั่งให้ Python ส่ง CAPTURE:shots
      // Serial.flush();
      currentState = WATER_COMPLETE;
    }
    break;

  case WATER_COMPLETE:
    if (!pump_active)
    {
      // ✅ FIX 1: ยกเลิก Interrupt ก่อนเปิดรีเลย์
      detachInterrupt(digitalPinToInterrupt(Limit_X));
      detachInterrupt(digitalPinToInterrupt(Limit_Z));
      startTime = millis();           // บันทึกเวลาที่เริ่มทำงาน
      digitalWrite(Relay_Pump, LOW); // เปิดรีเลย์
      pump_active = true;             // ตั้งค่าสถานะว่าปั๊มกำลังทำงาน
    }

    // ตรวจสอบว่าถึงเวลาปิดหรือยัง
    if (pump_active && (millis() - startTime >= duration))
    {
      digitalWrite(Relay_Pump, HIGH); // ปิดรีเลย์
      // ✅ FIX 2: เปิดใช้งาน Interrupt อีกครั้งหลังจากปิดรีเลย์
      pump_active = false; // ตั้งค่าสถานะว่าปั๊มหยุดแล้ว
      if (currentCommand == "WATER_SPECIFIC")
      {
        Serial.println("WATERING_SPECIFIC_COMPLETE");
        Serial.flush();
      }
      if (currentCommand == "WATER_ALL")
      {
        Serial.print("\nWATERING_"); // ส่งการตอบกลับ
        Serial.print(id);            // ส่งการตอบกลับ
        Serial.println("_COMPLETE"); // ส่งการตอบกลับ
        Serial.flush();
      }
      currentState = IDLE;
      attachInterrupt(digitalPinToInterrupt(Limit_X), LimitInteruptX, FALLING);
      attachInterrupt(digitalPinToInterrupt(Limit_Z), LimitInteruptZ, FALLING);
    }
    break;
  }
}

// ================= Setup =================
void setup()
{
  Serial.begin(115200);

  pinMode(Limit_X, INPUT_PULLUP);
  pinMode(Limit_Z, INPUT_PULLUP);
  pinMode(Relay_Pump, OUTPUT);

  attachInterrupt(digitalPinToInterrupt(Limit_X), LimitInteruptX, FALLING);
  attachInterrupt(digitalPinToInterrupt(Limit_Z), LimitInteruptZ, FALLING);
  pinMode(A_IN1, OUTPUT);
  pinMode(A_IN2, OUTPUT);
  pinMode(A_IN3, OUTPUT);
  pinMode(A_IN4, OUTPUT);
  pinMode(B_IN1, OUTPUT);
  pinMode(B_IN2, OUTPUT);
  pinMode(B_IN3, OUTPUT);
  pinMode(B_IN4, OUTPUT);
  digitalWrite(Relay_Pump, HIGH);
  // homing = false;
  Serial.println("Ready.");
}

void processCommand(String command);

void loop()
{
  // 1. Interrupt Logic (คงเดิม)
  if (flagX)
  {
    backoffX();
  }
  if (flagZ)
  {
    backoffZ();
  }

  // 2. Motor Logic (Non-Blocking Stepper)
  if (stepsToMoveX > 0)
  {
    stepMotorX();
  }
  if (stepsToMoveZ > 0)
  {
    stepMotorZ();
  }

  // 3. Handle Scan State Machine
  handleScan();

  // 4. Serial Command Receiver
  while (Serial.available())
  {
    char incomingChar = Serial.read();
    if (incomingChar == '\n')
    {
      processCommand(incomingCommand);
      incomingCommand = "";
    }
    else
    {
      incomingCommand += incomingChar;
    }
  }
}

void processCommand(String command)
{
  command.toUpperCase(); // ⬅️ FIX: ใช้ ToUpperCase() เพื่อความเข้ากันได้กับ Python

  if (command == "HOMING")
  {
    Serial.println("");
    Serial.flush();
    currentState = HOMING;
    return;
  }
  if (command == "SCAN")
  {
    // 🎯 FIX: เริ่มต้น State Machine (จะเรียก Homing ใน handleScan)
    if (currentState == IDLE || currentState == SCAN_COMPLETE)
    {
      currentState = HOMING_SCAN;
      Serial.println("SCAN_ACK");
      Serial.flush();
    }
    else
    {
      Serial.println("ERROR: ALREADY_BUSY");
      Serial.flush();
    }
    return;
  }

  // 🎯 จัดการ CAPTURE:shots (รับค่าตัวแปร)
  if (command.startsWith("CAPTURE:"))
  {
    if (currentState == WAITING_ACK)
    {
      int separatorIndex = command.indexOf(':');
      String valueStr = command.substring(separatorIndex + 1);
      totalShots = valueStr.toInt();

      currentGap = (X_MAX_POS - X_MIN_POS) / totalShots;
      currentShot = 0;

      // 2. เริ่มต้นลูปสแกน X
      currentState = SCANNING_X_MOVE;
      Serial.println("STATUS: X_SEQUENCE_START");
      return;
    }
  }

  // 🎯 จัดการสัญญาณ ACK (CAPTURED) จาก Python
  if (command == "CAPTURED" && currentState == WAITING_ACK_X)
  {
    currentShot++;                  // ไปจุดต่อไป
    currentState = SCANNING_X_MOVE; // กลับไปลูปสแกน X
    return;
  }

  // 2. ตรวจสอบคำสั่ง WATER_SPECIFIC
  // รูปแบบคำสั่งที่มาจาก Python: "WATER_SPECIFIC:3"
  if (command.startsWith("WATER_SPECIFIC:"))
  {
    currentCommand = "WATER_SPECIFIC";
    // find symbol index from command
    int colonIndex = command.indexOf(":");
    String valueStr = command.substring(colonIndex + 1); // 3,123,456

    int firstComma = valueStr.indexOf(",");
    int SecComma = valueStr.indexOf(",", firstComma + 1);
    if (colonIndex == -1 || firstComma == -1 || SecComma == -1)
    {
      Serial.println("Invalid index value.");
      return;
    }
    // substring to assign value
    String valueStrID = valueStr.substring(0, firstComma);           // 3
    String valueStrX = valueStr.substring(firstComma + 1, SecComma); // 123
    String valueStrZ = valueStr.substring(SecComma + 1);             // 456
    // tran string type to int
    id = valueStrID.toInt();
    float pos_X = valueStrX.toFloat();
    float pos_Z = valueStrZ.toFloat();
    moveX_to(pos_X);
    moveZ_to(pos_Z);
    Serial.println(""); // ส่งการตอบกลับ
    currentState = MOVING_WATER_Z;
    return;
  }

  if (command.startsWith("CHECK_WATER_ALL")) // WATER_ALL:3,123,456
  {
    // ถ้าใช้ read_all_available() ต้องมี \n ข้างหน้าเพื่อส่งค่าว่างตอบกลับคำสั่ง send_serial_command()
    Serial.println("\nWAITING_COMMAND"); // ส่งการตอบกลับ
    return;
  }

  // 3. ตรวจสอบคำสั่ง WATER_ALL
  if (command.startsWith("WATER_ALL:")) // WATER_ALL:3,123,456
  {
    currentCommand = "WATER_ALL";
    // find symbol index from command
    int colonIndex = command.indexOf(":");
    String valueStr = command.substring(colonIndex + 1); // 3,123,456

    int firstComma = valueStr.indexOf(",");
    int SecComma = valueStr.indexOf(",", firstComma + 1);
    if (colonIndex == -1 || firstComma == -1 || SecComma == -1)
    {
      Serial.println("Invalid index value.");
      return;
    }
    // substring to assign value
    String valueStrID = valueStr.substring(0, firstComma);           // 3
    String valueStrX = valueStr.substring(firstComma + 1, SecComma); // 123
    String valueStrZ = valueStr.substring(SecComma + 1);             // 456
    // tran string type to int
    id = valueStrID.toInt();
    float pos_X = valueStrX.toFloat();
    float pos_Z = valueStrZ.toFloat();
    moveX_to(pos_X);
    moveZ_to(pos_Z);
    Serial.println(""); // ส่งการตอบกลับ
    currentState = MOVING_WATER_Z;
    return;
  }

  // หากไม่มีคำสั่งใดตรงกัน
  Serial.print("ERROR: UNKNOWN COMMAND: ");
  Serial.println(command);
}