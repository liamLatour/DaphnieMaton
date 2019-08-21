#include <AccelStepper.h>

#define LED_PIN 13

AccelStepper Xaxis(AccelStepper::DRIVER, 60, 61);
AccelStepper Y1axis(AccelStepper::DRIVER, 54, 55);
AccelStepper Y2axis(AccelStepper::DRIVER, 46, 48);

const int A = 3;
const int B = 15;
const int C = 18;
const int D = 2;
const int MA = 19; //Milieu coté A
const int MD = 14; //Milieu coté A

int runningX = 0;
int runningY = 0;

void setup()
{
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

  Serial.begin(9600);
}

void loop()
{
  if (Serial.available() > 0)
  {
    int incomingByte = Serial.read();

    switch (incomingByte)
    {
    case 1:
      runningY = 1;
      Y1axis.setSpeed(500);
      Y2axis.setSpeed(500);
      break;
    case 2:
      runningY = 1;
      Y1axis.setSpeed(-500);
      Y2axis.setSpeed(-500);
      break;
    case 3:
      runningX = 1;
      Xaxis.setSpeed(500);
      break;
    case 4:
      runningX = 1;
      Xaxis.setSpeed(-500);
      break;
    case 5:
      runningY = 0;
      break;
    case 6:
      runningX = 0;
      break;
    case 7:
      String tosend = "{\"X\":" + String(Xaxis.currentPosition()) + ", \"Y\":" + String(Y1axis.currentPosition()) + ", \"A\":" + digitalRead(A) + ", \"B\":" + digitalRead(B) + ", \"C\":" + digitalRead(C) + ", \"D\":" + digitalRead(D) + ", \"MA\":" + digitalRead(MA) + ", \"MD\":" + digitalRead(MD) + "}";
      Serial.println(tosend);
      break;
    default:
      break;
    }

    if (incomingByte == 8)
    {
      goToOrigin();
    }
    else if (incomingByte == 9)
    {
      Serial.println("DaphnieMaton");
    }
    else if (incomingByte == 10)
    {
      calibrate();
    }
  }
  if (runningX == 1 &&  ((Xaxis.speed() > 0 && digitalRead(MD)) || (Xaxis.speed() < 0 && digitalRead(MA))))
  {
    Xaxis.runSpeed();
  }
  if (runningY == 1 && ((Y1axis.speed() > 0 && digitalRead(B) && digitalRead(C)) || (Y1axis.speed() < 0 && digitalRead(A) && digitalRead(D))))
  {
    Y1axis.runSpeed();
    Y2axis.runSpeed();
  }
}

void goToOrigin()
{
  Xaxis.setSpeed(-500);
  Y1axis.setSpeed(-500);
  Y2axis.setSpeed(-500);

  while (digitalRead(MA))
  {
    while (digitalRead(MA))
    {
      Xaxis.runSpeed();
    }
    delay(2);
  }

  while (digitalRead(A) && digitalRead(D))
  {
    while (digitalRead(A) && digitalRead(D))
    {
      Y1axis.runSpeed();
      Y2axis.runSpeed();
    }
    delay(2);
  }

  Xaxis.setCurrentPosition(0);
  Y1axis.setCurrentPosition(0);
  Y2axis.setCurrentPosition(0);
}

void calibrate()
{
  // Going to the end
  Xaxis.setSpeed(500);
  while (digitalRead(MD))
  {
    while (digitalRead(MD))
    {
      Xaxis.runSpeed();
    }
    delay(2);
  }

  // It arrived
  Xaxis.setCurrentPosition(0);

  unsigned long start = millis();

  // Go to the origin
  Xaxis.setSpeed(-500);
  while (digitalRead(MA))
  {
    while (digitalRead(MA))
    {
      Xaxis.runSpeed();
    }
    delay(2);
  }

  String tosend = "{\"Steps\":" + String(abs(Xaxis.currentPosition())) + ", \"Time\":" + String(millis() - start) + "}";
  Serial.println(tosend);

  //Reset origin
  Xaxis.setCurrentPosition(0);
}
