#include <AccelStepper.h>
     AccelStepper Xaxis(AccelStepper::DRIVER, 54, 55);
     AccelStepper Y1axis(AccelStepper::DRIVER, 60, 61);
     AccelStepper Y2axis(AccelStepper::DRIVER, 46, 48);
     
     const int X_Stops[] = {3, 2};
     const int Y1_Stops[] = {14, 15};
     const int Y2_Stops[] = {18, 19};
     
     const int waypointNb = 2;
     int currentWaypoint = 0;
     const int waypoints[] = {-90.0, -7.291666666666668, -90.0, 7.291666666666668};
     const bool photo[] = {true, false};
     
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
         Xaxis.setSpeed(-500);
         Y1axis.setSpeed(-500);
         Y2axis.setSpeed(-500);
     }

void loop() {
         if(hasStarted){
             if(!digitalRead(X_Stops[0]) && !digitalRead(X_Stops[1])){
                 Xaxis.moveTo(waypoints[currentWaypoint*2]);
                 Xaxis.run();
                 if(photo[currentWaypoint]){
                     Xaxis.setSpeed(850);
                 }
             }
             if(!digitalRead(Y1_Stops[0]) && !digitalRead(Y2_Stops[0]) && !digitalRead(Y1_Stops[1]) && !digitalRead(Y2_Stops[1])){
                 Y1axis.moveTo(waypoints[currentWaypoint*2+1]);
                 Y1axis.run();
                 Y2axis.moveTo(waypoints[currentWaypoint*2+1]);
                 Y2axis.run();
                 if(photo[currentWaypoint]){
                     Y1axis.setSpeed(850);
                     Y2axis.setSpeed(850);
                 }
             }
             if(Xaxis.distanceToGo()==0 && (Y1axis.distanceToGo()==0 || Y2axis.distanceToGo()==0)){
                 currentWaypoint = (currentWaypoint+1)%waypointNb;
             }
         }
         else{
             if(!digitalRead(X_Stops[0])){
                 Xaxis.runSpeed();
             }
             if(!digitalRead(Y1_Stops[0]) && !digitalRead(Y2_Stops[0])){
                 Y1axis.runSpeed();
                 Y2axis.runSpeed();
             }
             if(digitalRead(X_Stops[0]) && (digitalRead(Y1_Stops[0]) || digitalRead(Y2_Stops[0]))){
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