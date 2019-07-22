#include <AccelStepper.h>
     #define LED_PIN            13
     AccelStepper Xaxis(AccelStepper::DRIVER, 60, 61);
     AccelStepper Y1axis(AccelStepper::DRIVER, 54, 55);
     AccelStepper Y2axis(AccelStepper::DRIVER, 46, 48);
     
     const int A = 3;
     const int B = 15;
     const int C = 18;
     const int D = 2;
     const int MA = 19;
     const int MD = 14;
     
     const int waypointNb = 6;
     int currentWaypoint = 0;
     const int waypoints[] = {315, 315, 5985, 315, 315, 1575, 5985, 1575, 315, 2835, 5985, 2835};
     const bool photo[] = {true, false, true, false, true, false};
     
     bool hasStarted = false;

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
         pinMode(40, INPUT_PULLUP);
     }

void loop() {
         if(digitalRead(40) == 1){
             if(hasStarted){
                 Xaxis.setSpeed(500);
                 Y1axis.setSpeed(500);
                 Y2axis.setSpeed(500);
                 Xaxis.moveTo(waypoints[currentWaypoint*2]);
                 Y1axis.moveTo(waypoints[currentWaypoint*2+1]);
                 Y2axis.moveTo(waypoints[currentWaypoint*2+1]);
                 if( (Xaxis.speed()>0 && digitalRead(MD)) || (Xaxis.speed()<0 && digitalRead(MA)) ){
                     Xaxis.runSpeedToPosition();
                     if(photo[currentWaypoint]){
                         //Gotta take them
                     }
                 }
                 if( (Y1axis.speed()>0 && digitalRead(B) && digitalRead(C)) || (Y1axis.speed()<0 && digitalRead(A) && digitalRead(D)) ){
                     Y1axis.runSpeedToPosition();
                     Y2axis.runSpeedToPosition();
                     if(photo[currentWaypoint]){
                         //Gotta take them
                     }
                 }
                 if(Xaxis.distanceToGo()==0 && (Y1axis.distanceToGo()==0 || Y2axis.distanceToGo()==0)){
                     currentWaypoint = (currentWaypoint+1)%waypointNb;
                     delay(500);
                 }
             }
             else{
                 Xaxis.setSpeed(-500);
                 Y1axis.setSpeed(-500);
                 Y2axis.setSpeed(-500);
                 if(digitalRead(MA)){
                     Xaxis.runSpeed();
                 }
                 if(digitalRead(A) && digitalRead(D)){
                     Y1axis.runSpeed();
                     Y2axis.runSpeed();
                 }
                 if(!digitalRead(MA) && (!digitalRead(A) || !digitalRead(D))){
                     hasStarted = true;
                     Xaxis.setCurrentPosition(0);
                     Y1axis.setCurrentPosition(0);
                     Y2axis.setCurrentPosition(0);
                     Xaxis.setSpeed(500);
                     Y1axis.setSpeed(500);
                     Y2axis.setSpeed(500);
                 }
             }
         }
     }