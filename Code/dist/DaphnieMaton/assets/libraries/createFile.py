'''
File will look like this:



#include <AccelStepper.h>

AccelStepper Xaxis(AccelStepper::DRIVER, 54, 55); // pin 54 = step, pin 55 = direction, pin 38 = enable
AccelStepper Y1axis(AccelStepper::DRIVER, 60, 61); // pin 60 = step, pin 61 = direction, pin 56 = enable
AccelStepper Y2axis(AccelStepper::DRIVER, 46, 48); // pin 46 = step, pin 48 = direction, pin 62 = enable

waypoints = [x1, y1, x2, y2, x3, y3, ...]   // size = n
takePhotos = [true, false, false, ...]      // size = n/2; it defines at the same time speed and photo taking
/* Other constants */


void setup(){
    Xaxis.setEnablePin(38);
    Y1axis.setEnablePin(56);
    Y2axis.setEnablePin(62);

    Xaxis.setPinsInverted(false, false, true);
    Y1axis.setPinsInverted(false, false, true);
    Y2axis.setPinsInverted(false, false, true);

    Xaxis.enableOutputs();
    Y1axis.enableOutputs();
    Y2axis.enableOutputs();
    
    Xaxis.setMaxSpeed(850);
    Y1axis.setMaxSpeed(850);
    Y2axis.setMaxSpeed(850);

    Xaxis.setAcceleration(800);
    Y1axis.setAcceleration(800);
    Y2axis.setAcceleration(800);
    
    Xaxis.setSpeed(500);
    Y1axis.setSpeed(500);
    Y2axis.setSpeed(500);
}

void loop() {
   Xaxis.moveTo(5000); // For acceleration
   Xaxis.run();
   Y1axis.runSpeed();   // For constant speed
   Y2axis.runSpeed();
}
'''

def generateFile(waypoints, photos):
    top = "#include <AccelStepper.h>\n \
    AccelStepper Xaxis(AccelStepper::DRIVER, 54, 55);\n \
    AccelStepper Y1axis(AccelStepper::DRIVER, 60, 61);\n \
    AccelStepper Y2axis(AccelStepper::DRIVER, 46, 48);\n \
    \n \
    const int X_Stops[] = {3, 2};\n \
    const int Y1_Stops[] = {14, 15};\n \
    const int Y2_Stops[] = {18, 19};\n \
    \n \
    const int waypointNb = 2;\n \
    int currentWaypoint = 0;\n \
    const int waypoints[] = "+str(waypoints).replace("[", "{").replace("]", "}")+";\n \
    const bool photo[] = "+str(photos).replace("[", "{").replace("]", "}").replace("F", "f").replace("T", "t")+";\n \
    \n \
    bool hasStarted = false;\n\n" # Min, Max


    setup = "void setup(){\n \
        Xaxis.setEnablePin(38);\n \
        Y1axis.setEnablePin(56);\n \
        Y2axis.setEnablePin(62);\n \
        Xaxis.setPinsInverted(false, false, true);\n \
        Y1axis.setPinsInverted(false, false, true);\n \
        Y2axis.setPinsInverted(true, false, true);\n \
        Xaxis.enableOutputs();\n \
        Y1axis.enableOutputs();\n \
        Y2axis.enableOutputs();\n \
        Xaxis.setMaxSpeed(850);\n \
        Y1axis.setMaxSpeed(850);\n \
        Y2axis.setMaxSpeed(850);\n \
        Xaxis.setAcceleration(800);\n \
        Y1axis.setAcceleration(800);\n \
        Y2axis.setAcceleration(800);\n \
        Xaxis.setSpeed(-500);\n \
        Y1axis.setSpeed(-500);\n \
        Y2axis.setSpeed(-500);\n \
    }\n\n"

    loop = "void loop() {\n \
        if(hasStarted){\n \
            if(!digitalRead(X_Stops[0]) && !digitalRead(X_Stops[1])){\n \
                Xaxis.moveTo(waypoints[currentWaypoint*2]);\n \
                Xaxis.run();\n \
                if(photo[currentWaypoint]){\n \
                    Xaxis.setSpeed(850);\n \
                }\n \
            }\n \
            if(!digitalRead(Y1_Stops[0]) && !digitalRead(Y2_Stops[0]) && !digitalRead(Y1_Stops[1]) && !digitalRead(Y2_Stops[1])){\n \
                Y1axis.moveTo(waypoints[currentWaypoint*2+1]);\n \
                Y1axis.run();\n \
                Y2axis.moveTo(waypoints[currentWaypoint*2+1]);\n \
                Y2axis.run();\n \
                if(photo[currentWaypoint]){\n \
                    Y1axis.setSpeed(850);\n \
                    Y2axis.setSpeed(850);\n \
                }\n \
            }\n \
            if(Xaxis.distanceToGo()==0 && (Y1axis.distanceToGo()==0 || Y2axis.distanceToGo()==0)){\n \
                currentWaypoint = (currentWaypoint+1)%waypointNb;\n \
            }\n \
        }\n \
        else{\n \
            if(!digitalRead(X_Stops[0])){\n \
                Xaxis.runSpeed();\n \
            }\n \
            if(!digitalRead(Y1_Stops[0]) && !digitalRead(Y2_Stops[0])){\n \
                Y1axis.runSpeed();\n \
                Y2axis.runSpeed();\n \
            }\n \
            if(digitalRead(X_Stops[0]) && (digitalRead(Y1_Stops[0]) || digitalRead(Y2_Stops[0]))){\n \
                hasStarted = true;\n \
                Xaxis.setCurrentPosition(0);\n \
                Y1axis.setCurrentPosition(0);\n \
                Y2axis.setCurrentPosition(0);\n \
                Xaxis.setSpeed(500);\n \
                Y1axis.setSpeed(500);\n \
                Y2axis.setSpeed(500);\n \
            }\n \
        }\n \
    }"

    return top + setup + loop