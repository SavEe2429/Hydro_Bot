#include <Arduino.h>
//https://docs.google.com/document/d/1Vxh6Z6RBmllpE-TCUfmOebgBQnEqvF-Deb4upEB9mnA/edit?tab=t.0
#define LimitX  
#define LimitZ 
#define RelayPump
const int X_IN1 = 14, X_IN2 = 12, X_IN3 = 13, X_IN4 = 15; // X
const int Z_IN1 = 27, Z_IN2 = 26, Z_IN3 = 25, Z_IN4 = 33; // Z

const int STEP_SEQ[8][4] = {
    {1, 0, 0, 0},
    {1, 1, 0, 0},
    {0, 1, 0, 0},
    {0, 1, 1, 0},
    {0, 0, 1, 0},
    {0, 0, 1, 1},
    {0, 0, 0, 1},
    {1, 0, 0, 1}
};

const int MOTOR_REV = 4096; // ค่าความละเอียดของมอเตอร์  motor reslution 
const int MOTOR_DELAY = 800; // ช่วงเวลาหน่วงของแต่ละรอบ motor cycle delay
int seqIndexX , seqIndexZ = 0;
unsigned long lastStepIndexX , lastStepIndexZ = 0;
int MOTORX_DIR = -1; // ทิศทางเริ่มต้นของ motorX
int MOTORZ_DIR = -1; // ทิศทางเริ่มต้นของ motorZ

// กำหนดขาที่ต้องการใช้
void setOutputs(int in0 ,int in1 ,int in2 ,int in3 ,const int pattern[4]){
    digitalWrite(in0,pattern[0]);
    digitalWrite(in1,pattern[1]);
    digitalWrite(in2,pattern[2]);
    digitalWrite(in3,pattern[3]);
}

void stepMotorX(){
    if(micros() - lastStepIndexX >= MOTOR_DELAY){
        seqIndexX = (seqIndexX + MOTORX_DIR + 8) % 8; // คำนวนหาค่าลำดับการทำงานของมอเตอร์
        
    }
}

// ทำให้มอเตอร์หยุดหมุน
void stopMotor(int in0 ,int in1 ,int in2 ,int in3){
    digitalWrite(in0,0);
    digitalWrite(in1,0);
    digitalWrite(in2,0);
    digitalWrite(in3,0);
}


void setup() {
    // set esp32 pin output
    pinMode(X_IN1,OUTPUT);
    pinMode(X_IN2,OUTPUT);
    pinMode(X_IN3,OUTPUT);
    pinMode(X_IN4,OUTPUT);
    pinMode(Z_IN1,OUTPUT);
    pinMode(Z_IN2,OUTPUT);
    pinMode(Z_IN3,OUTPUT);
    pinMode(Z_IN4,OUTPUT);
}

