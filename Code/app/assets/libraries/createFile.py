import numpy as np

def generateFile(waypoints, photos, ratio, photoPipe, action, actionOnSpot=False):
    waypoints = list(np.rint(np.multiply(waypoints, ratio)).tolist())

    top = "#include <AccelStepper.h>\n \
    #include <"+str(action)+">\n \
    #define LED_PIN 13\n \
    #define firstHalf 0\n \
    #define middle 1\n \
    #define lastHalf 2\n \
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
    const int waypointNb = "+str(round(len(waypoints)/2))+";\n \
    float waypointLength = 0;\n \
    float waypointXLength = 0;\n \
    float waypointYLength = 0;\n \
    int currentWaypoint = 0;\n \
    const int waypoints[] = "+str(waypoints).replace("[", "{").replace("]", "}").replace(".0", "")+";\n \
    const bool photo[] = "+str(photos).replace("[", "{").replace("]", "}").replace("F", "f").replace("T", "t")+";\n \
    \n \
    float photoPipe = "+photoPipe+";\n \
    int state = firstHalf;\n \
    int middleNb = 0;\n \
    int middleTotal = 0;\n \
    bool actionOnSpot = "+str(actionOnSpot).lower()+";\n \
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
        pinMode(40, INPUT_PULLUP);\n \
    }\n\n"

#FIXME: at start go to waypoint normally

    loop = "void loop() {\n \
        if(digitalRead(40) == 1){\n \
            if(hasStarted){\n \
                Xaxis.setSpeed(500);\n \
                Y1axis.setSpeed(500);\n \
                Y2axis.setSpeed(500);\n \
                \n \
                if(state == firstHalf){\n \
                    float top = (waypointLength-middleTotal*photoPipe)/(2*waypointLength);\n \
                    Xaxis.moveTo(waypoints[((currentWaypoint-1)%waypointNb)*2] + top*waypointXLength);\n \
                    Y1axis.moveTo(waypoints[((currentWaypoint-1)%waypointNb)*2+1] + top*waypointYLength);\n \
                    Y2axis.moveTo(waypoints[((currentWaypoint-1)%waypointNb)*2+1] + top*waypointYLength);\n \
                }\n \
                else if(state == middle){\n \
                    Xaxis.moveTo(waypoints[currentWaypoint*2]);\n \
                    Y1axis.moveTo(waypoints[currentWaypoint*2+1]);\n \
                    Y2axis.moveTo(waypoints[currentWaypoint*2+1]);\n \
                }\n \
                else{\n \
                    Xaxis.moveTo(waypoints[currentWaypoint*2]);\n \
                    Y1axis.moveTo(waypoints[currentWaypoint*2+1]);\n \
                    Y2axis.moveTo(waypoints[currentWaypoint*2+1]);\n \
                }\n \
                \n \
                if( (Xaxis.speed()>0 && digitalRead(MD)) || (Xaxis.speed()<0 && digitalRead(MA)) ){\n \
                    Xaxis.runSpeedToPosition();\n \
                    if(photo[currentWaypoint] & !actionOnSpot){\n \
                        //Gotta take them\n \
                        action();\n \
                    }\n \
                }\n \
                if( (Y1axis.speed()>0 && digitalRead(B) && digitalRead(C)) || (Y1axis.speed()<0 && digitalRead(A) && digitalRead(D)) ){\n \
                    Y1axis.runSpeedToPosition();\n \
                    Y2axis.runSpeedToPosition();\n \
                    if(photo[currentWaypoint] & !actionOnSpot){\n \
                        //Gotta take them\n \
                        action();\n \
                    }\n \
                }\n \
                if(Xaxis.distanceToGo()==0 && (Y1axis.distanceToGo()==0 || Y2axis.distanceToGo()==0)){\n \
                    if(state == lastHalf){\n \
                        state = firstHalf;\n \
                        int nextWaypoint = (currentWaypoint+1)%waypointNb;\n \
                        waypointXLength = waypoints[nextWaypoint*2] - waypoints[currentWaypoint*2];\n \
                        waypointYLength = waypoints[nextWaypoint*2+1] - waypoints[currentWaypoint*2+1];\n \
                        waypointLength = sqrt(sq(waypointXLength)+sq(waypointYLength));\n \
                        currentWaypoint = nextWaypoint;\n \
                        middleTotal = waypointLength/photoPipe;\n \
                        if(actionOnSpot){\n \
                            action();\n \
                        }\n \
                        delay(500);\n \
                    }\n \
                    else if(state == firstHalf){\n \
                        state = middle;\n \
                    }\n \
                    else{\n \
                        if(middleNb == middleTotal){\n \
                            state = lastHalf;\n \
                            middleNb = 0;\n \
                        }\n \
                        else{\n \
                            middleNb += 1;\n \
                        }\n \
                    }\n \
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