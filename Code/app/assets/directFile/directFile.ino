#include <AccelStepper.h>

#define LED_PIN            13

AccelStepper Xaxis(AccelStepper::DRIVER, 54, 55);
AccelStepper Y1axis(AccelStepper::DRIVER, 60, 61);
AccelStepper Y2axis(AccelStepper::DRIVER, 46, 48);
 
const int X_Stops[] = {3, 2};
const int Y1_Stops[] = {14, 15};
const int Y2_Stops[] = {18, 19};

int runningX = 0;
int runningY = 0;

void setup(){
  Xaxis.setEnablePin(38);
  Y1axis.setEnablePin(56);
  Y2axis.setEnablePin(62);
  Xaxis.setPinsInverted(false, false, true);
  Y1axis.setPinsInverted(false, false, true);
  Y2axis.setPinsInverted(true, false, true);
  Xaxis.enableOutputs();
  Y1axis.enableOutputs();
  Y2axis.enableOutputs();
  Xaxis.setMaxSpeed(850);
  Y1axis.setMaxSpeed(850);
  Y2axis.setMaxSpeed(850);
  Xaxis.setAcceleration(800);
  Y1axis.setAcceleration(800);
  Y2axis.setAcceleration(800);
  Xaxis.setSpeed(-500);
  Y1axis.setSpeed(-500);
  Y2axis.setSpeed(-500);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    int incomingByte = Serial.read();

    if(incomingByte == 1){
      runningY = 1;
    }
    else if(incomingByte == 2){
      runningY = -1;
    }
    else if(incomingByte == 3){
      runningX = 1;
    }
    else if(incomingByte == 4){
      runningX = -1;
    }
    else if(incomingByte == 5){
      runningY = 0;
    }
    else if(incomingByte == 6){
      runningY = 0;
    }
    else if(incomingByte == 7){
      runningX = 0;
    }
    else if(incomingByte == 8){
      runningX = 0;
    }
    else if(incomingByte == 9){
      Serial.println(Xaxis.currentPosition());
      Serial.println(Y1axis.currentPosition());
    }
  }
  if(runningX == 1){
    Xaxis.setSpeed(500);
    Xaxis.runSpeed();
  }
  if(runningX == -1){
    Xaxis.setSpeed(-500);
    Xaxis.runSpeed();
  }
  if(runningY == 1){
    Y1axis.setSpeed(500);
    Y2axis.setSpeed(500);
    Y1axis.runSpeed();
    Y2axis.runSpeed();
  }
  if(runningY == -1){
    Y1axis.setSpeed(-500);
    Y2axis.setSpeed(-500);
    Y1axis.runSpeed();
    Y2axis.runSpeed();
  }
}