#include <Arduino.h>
#include <ArduinoJson.h>

// Motor pins
// CurrentPosX : 36813
// CurrentPosZ : 19836
// CurrentPosX : 36799
// CurrentPosZ : 19912
// CurrentPosX : 36869
// CurrentPosZ : 19911

// avg posX = 36877
// avg posZ = 19786

#define Limit_X 18
#define Limit_Z 4
const int A_IN1 = 14, A_IN2 = 12, A_IN3 = 13, A_IN4 = 15; // X
const int B_IN1 = 27, B_IN2 = 26, B_IN3 = 25, B_IN4 = 33; // Z

// Step sequence
const int STEP_SEQ[8][4] = {
    {1, 0, 0, 0}, {1, 1, 0, 0}, {0, 1, 0, 0}, {0, 1, 1, 0}, {0, 0, 1, 0}, {0, 0, 1, 1}, {0, 0, 0, 1}, {1, 0, 0, 1}};

const int STEPS_PER_REV = 4096;
const int STEP_DELAY = 800;
const float DIST_PER_REV = 15.71;
const float HOME_OFFSET_MM = 3;

// Motor state
long stepsToMoveX = 0, stepsToMoveZ = 0;
int dirX = 1, dirZ = 1;
int seqIndexX = 0, seqIndexZ = 0;
unsigned long lastStepTimeX = 0, lastStepTimeZ = 0;
long currentPosX = 0, currentPosZ = 0;

// string receive
String receivedData = "";

// Backoff steps
long backoffSteps = (HOME_OFFSET_MM / DIST_PER_REV) * STEPS_PER_REV;

bool flagX, flagZ;

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
long targetX, diffX;
long targetZ, diffZ;
// ================= Move To =================
void moveX_to(float distance_pixel)
{
  targetX = distance_pixel * 30.73;
  diffX = targetX - currentPosX;
  dirX = (diffX >= 0) ? 1 : -1;
  stepsToMoveX = abs(diffX);
}
void moveZ_to(float distance_pixel)
{
  targetZ = distance_pixel * 30.92;
  diffZ = targetZ - currentPosZ;
  dirZ = (diffZ >= 0) ? 1 : -1;
  stepsToMoveZ = abs(diffZ);
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
  printf("CurrentPosX : %d\n", currentPosX);
  stepsToMoveX = 0;
  currentPosX = 0;
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
  printf("CurrentPosZ : %d\n", currentPosZ);
  stepsToMoveZ = 0;
  currentPosZ = 0;
}

bool homing = false;
// ================= Homing Function =================
void doHoming()
{
  homing = true;
  // ---------- Homing X ----------
  Serial.println("Homing X...");
  dirX = -1;                           // วิ่งเข้าหาลิมิต
  while (digitalRead(Limit_X) == HIGH) // รอจนกว่าจะกด (LOW)
  {
    stepMotorX();
    delayMicroseconds(STEP_DELAY);
  }

  // overshoot เข้าไปอีกนิด
  // for (int i = 0; i < 50; i++)
  // {
  //   stepMotorX();
  //   delayMicroseconds(STEP_DELAY);
  // }
  backoffX();
  flagX = false;
  currentPosX = 0;
  Serial.println("Homing X done.");

  // ---------- Homing Z ----------
  Serial.println("Homing Z...");
  dirZ = -1;
  while (digitalRead(Limit_Z) == HIGH)
  {
    stepMotorZ();
    delayMicroseconds(STEP_DELAY);
  }

  // overshoot เข้าไปอีกนิด
  // for (int i = 0; i < 50; i++)
  // {
  //   stepMotorZ();
  //   delayMicroseconds(STEP_DELAY);
  // }

  backoffZ();
  flagZ = false;
  currentPosZ = 0;
  Serial.println("Homing Z done.");

  Serial.println("Homing finished.");
}

void scanArea(long X_min, long X_max, long Z_max)
{
  // 1. ขยับ Z ไปตรงกลาง
  long Z_mid = Z_max / 2;
  moveZ_to(Z_mid);

  // ขยับจนถึง Z_mid
  while (stepsToMoveZ > 0)
  {
    stepMotorZ();
  }
  stopMotor(B_IN1, B_IN2, B_IN3, B_IN4);
  Serial.println("Z moved to center.");

  // 2. ขยับ X 4 รอบไป-กลับ
  for (int i = 0; i < 16; i++)
  {
    // ไป X_max
    float spotX = X_min + (85 * i);
    moveX_to(spotX);
    while (stepsToMoveX > 0)
    {
      stepMotorX();
    }
    // ✅ ส่งสัญญาณ arrived ไป Python
    Serial.println("arrived");
    delay(3000);
  }

  Serial.println("Scan finished, holding position.");
}

// ================= Setup =================
void setup()
{
  Serial.begin(115200);

  pinMode(Limit_X, INPUT_PULLUP);
  pinMode(Limit_Z, INPUT_PULLUP);

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
  doHoming();
  homing = false;
  Serial.println("Ready.");
}

bool startScan = false;

void loop()
{
  if (flagX == true) // ทำงานเมื่อ Interrupt X ถูกเรียกเท่านั้น
  {
    backoffX(); // ส่ง flagX (Global) แบบอ้างอิงเข้าไป
    printf("CurrentPosX : %d\n", currentPosX);
    receivedData = "";
  }

  if (flagZ == true) // ทำงานเมื่อ Interrupt Z ถูกเรียกเท่านั้น
  {
    backoffZ(); // ส่ง flagZ (Global) แบบอ้างอิงเข้าไป
    printf("CurrentPosZ : %d\n", currentPosZ);
    receivedData = "";
  }
  // 1. รับและประมวลผลข้อมูล Serial (ถ้ามี)
  // ใช้วิธีรับข้อมูลทั้งหมดจนกว่าจะเจออักขระขึ้นบรรทัดใหม่ '\n'
  if (Serial.available())
  {
    // อ่าน String ทั้งหมดจนกว่าจะเจออักขระขึ้นบรรทัดใหม่ '\n'
    String input = Serial.readStringUntil('\n');

    // ลบช่องว่างหรืออักขระที่ไม่จำเป็นที่ต้นและท้าย String (รวมถึง '\r')
    input.trim();

    // เก็บคำสั่งที่พร้อมใช้งาน
    receivedData = input;

    // แสดงคำสั่งที่ได้รับ (เพื่อตรวจสอบ)
    Serial.print("Command received: ");
    Serial.println(receivedData);
  }

  // 2. ตรวจสอบคำสั่งและควบคุมมอเตอร์ (นอกเหนือจากการรับ Serial)

  // ถ้าได้รับคำสั่ง "X"
  if (receivedData.equalsIgnoreCase("X"))
  {
    // ใช้วิธี if เพื่อตรวจสอบเงื่อนไขทุกครั้งที่ loop() ทำงาน
    if (digitalRead(Limit_X) == HIGH)
    {
      // Serial.println("Executing Motor X step...");
      stepMotorX();
      delayMicroseconds(STEP_DELAY);
    }
  }
  // ถ้าได้รับคำสั่ง "Z"
  else if (receivedData.equalsIgnoreCase("Z"))
  {
    if (digitalRead(Limit_Z) == HIGH)
    {
      // Serial.println("Executing Motor Z step...");
      stepMotorZ();
      delayMicroseconds(STEP_DELAY);
    }
  }

  if (receivedData.equalsIgnoreCase("R"))
  {
    printf("CurrentPosX : %d\n", currentPosX);
    printf("CurrentPosZ : %d\n", currentPosZ);
    printf("dirX : %d , dirZ : %d\n", dirX, dirZ);
    printf("flagX : %s , flagZ : %s\n", flagX ? "T" : "F", flagZ ? "T" : "F");
    printf("diffX = %ld , diffZ = %ld\n", diffX,diffZ);
    printf("stepsToMoveX = %ld , stepsToMoveZ = %ld\n", stepsToMoveX,stepsToMoveZ);
    receivedData = "";
  }
  if (receivedData.equalsIgnoreCase("H"))
  {
    doHoming();
    receivedData = "";
  }
  if (receivedData.equalsIgnoreCase("1"))
  {
    moveX_to(1200);
    receivedData = "";
  }
  if (receivedData.equalsIgnoreCase("2"))
  {
    moveZ_to(640);
    receivedData = "";
  }

  // โค้ดอื่นๆ ที่ต้องทำงานตลอดเวลา (ถ้ามี)
}