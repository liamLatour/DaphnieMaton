import numpy as np


def generateFile(waypoints, photos, ratio, loop, action):
    waypoints = list(np.rint(np.multiply(waypoints, ratio)).tolist())

    top = "#include <AccelStepper.h>\n \
    #include <"+str(action)+">\n \
    #define LED_PIN 13\n \
    #define LOOP "+str(loop).replace("F", "f")+"\n \
    AccelStepper Xaxis(AccelStepper::DRIVER, 60, 61);\n \
    AccelStepper Y1axis(AccelStepper::DRIVER, 54, 55);\n \
    AccelStepper Y2axis(AccelStepper::DRIVER, 46, 48);\n \
    \n \
    const int A = 3;\n \
    const int B = 15;\n \
    const int C = 18;\n \
    const int D = 2;\n \
    const int MA = 19;\n \
    const int MD = 14;\n \
    \n \
    const int waypointNb = "+str(len(waypoints))+";\n \
    int currentWaypoint = 0;\n \
    const int waypoints["+str(len(waypoints))+"][2] = "+str(waypoints).replace("[", "{").replace("]", "}").replace(".0", "")+";\n \
    const bool photo[] = "+str(photos).replace("[", "{").replace("]", "}").replace("F", "f").replace("T", "t")+";\n \
    \n \
    bool hasStarted = false;\n \
    int increment = 1;\n\n"


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
        pinMode(40, INPUT_PULLUP);\n \
    }\n\n"

    loop = "void loop() {\n \
        if(digitalRead(40) == 1){\n \
            if(hasStarted){\n \
                Xaxis.setSpeed(500);\n \
                Y1axis.setSpeed(500);\n \
                Y2axis.setSpeed(500);\n \
                \n \
                Xaxis.moveTo(waypoints[currentWaypoint][0]);\n \
                Y1axis.moveTo(waypoints[currentWaypoint][1]);\n \
                Y2axis.moveTo(waypoints[currentWaypoint][1]);\n \
                \n \
                bool xmax = false;\n \
                bool ymax = false;\n \
                \n \
                if( (Xaxis.targetPosition() - Xaxis.currentPosition()>0 && digitalRead(MD)) || (Xaxis.targetPosition() - Xaxis.currentPosition()<0 && digitalRead(MA)) ){\n \
                    Xaxis.runSpeedToPosition();\n \
                }\n \
                else{\n \
                    xmax = true;\n \
                }\n \
                if( (Y1axis.targetPosition() - Y1axis.currentPosition()>0 && digitalRead(B) && digitalRead(C)) || (Y1axis.targetPosition() - Y1axis.currentPosition()<0 && digitalRead(A) && digitalRead(D)) ){\n \
                    Y1axis.runSpeedToPosition();\n \
                    Y2axis.runSpeedToPosition();\n \
                }\n \
                else{\n \
                    ymax = true;\n \
                }\n \
                if((Xaxis.distanceToGo()==0 || xmax) && (Y1axis.distanceToGo()==0 || Y2axis.distanceToGo()==0 || ymax)){\n \
                    if(photo[currentWaypoint]){\n \
                        //Gotta take them\n \
                        action();\n \
                    }\n \
                    if(LOOP && (currentWaypoint+increment+1)%(waypointNb+1) == 0){\n \
                        increment = -increment;\n \
                    }\n \
                    currentWaypoint = (currentWaypoint+increment)%waypointNb;\n \
                }\n \
            }\n \
            else{\n \
                Xaxis.setSpeed(-500);\n \
                Y1axis.setSpeed(-500);\n \
                Y2axis.setSpeed(-500);\n \
                if(digitalRead(MA)){\n \
                    Xaxis.runSpeed();\n \
                }\n \
                if(digitalRead(A) && digitalRead(D)){\n \
                    Y1axis.runSpeed();\n \
                    Y2axis.runSpeed();\n \
                }\n \
                if(!digitalRead(MA) && (!digitalRead(A) || !digitalRead(D))){\n \
                    hasStarted = true;\n \
                    Xaxis.setCurrentPosition(0);\n \
                    Y1axis.setCurrentPosition(0);\n \
                    Y2axis.setCurrentPosition(0);\n \
                    Xaxis.setSpeed(500);\n \
                    Y1axis.setSpeed(500);\n \
                    Y2axis.setSpeed(500);\n \
                }\n \
            }\n \
        }\n \
    }"

    return top + setup + loop
