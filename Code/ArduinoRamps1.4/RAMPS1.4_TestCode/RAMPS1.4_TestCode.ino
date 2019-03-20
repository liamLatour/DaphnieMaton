typedef struct{
  unsigned long totalSteps;
  unsigned long steps;
  uint8_t cur;
  float nextStep;
  const int motor[5];
} TurningMotor;

TurningMotor motors[5] = {
    {0, 0, LOW, 0, {54, 55, 38,  3,  2}},
    {0, 0, LOW, 0, {60, 61, 56, 14, 15}},
    {0, 0, LOW, 0, {46, 48, 62, 18, 19}},
    {0, 0, LOW, 0, {26, 28, 24, -1, -1}},
    {0, 0, LOW, 0, {36, 34, 30, -1, -1}}
  };

// Step, Dir, Enable, Min, Max
const int X_MOTOR[] = {54, 55, 38, 3, 2};
const int Y_MOTOR[] = {60, 61, 56, 14, 15};
const int Z_MOTOR[] = {46, 48, 62, 18, 19};

// Step, Dir, Enable
const int E_MOTOR[] = {26, 28, 24, -1, -1};
const int Q_MOTOR[] = {36, 34, 30, -1, -1};

#define SDPOWER            -1
#define SDSS               53
#define LED_PIN            13

#define FAN_PIN            9

#define PS_ON_PIN          12
#define KILL_PIN           -1

#define HEATER_0_PIN       10
#define HEATER_1_PIN       8
#define TEMP_0_PIN         13   // ANALOG NUMBERING
#define TEMP_1_PIN         14   // ANALOG NUMBERING

float timelapse = 1;

void setup() {
  pinMode(FAN_PIN , OUTPUT);
  pinMode(HEATER_0_PIN , OUTPUT);
  pinMode(HEATER_1_PIN , OUTPUT);
  pinMode(LED_PIN  , OUTPUT);

  //Serial.begin(9600);
  moveTo(1, 500, LOW);
  //moveTo(2, 500, LOW);

  attachInterrupt(digitalPinToInterrupt(Z_MOTOR[4]), blink, FALLING);
}

void blink() {
  //check which one was moving and go back or else...
  while(true){
    digitalWrite(motors[1].motor[0], HIGH);
    delayMicroseconds(500);
    digitalWrite(motors[1].motor[0], LOW);
  }
}

void loop () {
  if (millis() %1000 <500){
    digitalWrite(LED_PIN, HIGH);
  }
  else{
    digitalWrite(LED_PIN, LOW);
  }
  /*
  if (Serial.available()) {
    float tempTime = Serial.parseFloat();
    if(tempTime != 0){
      timelapse = tempTime;
    }
  }*/
/*
  digitalWrite(motors[1].motor[0], HIGH);
  delayMicroseconds(500);
  digitalWrite(motors[1].motor[0], LOW);
  */

  //Serial.println(timelapse);
/*
  for(int i=0; i<5; i++){
    if(motors[i].steps > 0){
      if(millis() > motors[i].nextStep){
        if(motors[i].cur == HIGH){
          digitalWrite(motors[i].motor[0], LOW);
          motors[i].cur = LOW;
        }
        else{
          digitalWrite(motors[i].motor[0], HIGH);
          motors[i].cur = HIGH;
        }
        motors[i].nextStep = millis() + timelapse;//toTime(max(min(sqrt(motors[i].totalSteps-motors[i].steps)+40, 120), 20));
        //Serial.println(toTime(max(min(sqrt(motors[i].totalSteps-motors[i].steps)+40, 120), 20)));
        motors[i].steps--;
      }
    }
  }*/
}


void moveTo(int mtr, int mm, uint8_t dir){
  // Step, Dir, Enable, Min, Max
  pinMode(motors[mtr].motor[0], OUTPUT);
  pinMode(motors[mtr].motor[1], OUTPUT);
  pinMode(motors[mtr].motor[2], OUTPUT);

  if(motors[mtr].motor[3] != -1){
    pinMode(motors[mtr].motor[3], INPUT);
    pinMode(motors[mtr].motor[4], INPUT);
  }  
  
  digitalWrite(motors[mtr].motor[1], dir);
  digitalWrite(motors[mtr].motor[2], LOW);

  motors[mtr].steps = mm;
  motors[mtr].totalSteps = mm;

  /*
  pinMode(motor[0], INPUT);
  pinMode(motor[1], INPUT);
  pinMode(motor[2], INPUT);
  */
}

float toTime(float tourParMin){
  return 6000.0/(tourParMin*200.0);
}
