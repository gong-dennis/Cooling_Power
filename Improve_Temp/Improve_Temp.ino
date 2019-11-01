#include <SPI.h>
#include "Adafruit_MAX31855.h"
#include <Keyboard.h>

#define MAXDO   5
#define MAXCS   4
#define MAXCLK  3
#define seconds() (millis()/1000)

Adafruit_MAX31855 thermocouple(MAXCLK, MAXCS, MAXDO);
const int buttonPin = 2;
int buttonState = 0;

unsigned long timer = 0;
long loopTime = 0.0005;   // microseconds

void setup() {
  Serial.begin(9600);
  pinMode(buttonPin, INPUT);
  timer = seconds();
}

void loop() {
  timeSync(loopTime);
  //int val = analogRead(0) - 512;
  double val = thermocouple.readCelsius();
  
  buttonState = digitalRead(buttonPin);
  if (buttonState == HIGH) {
    val = -99;
  }
  sendToPC(&val);
}

void timeSync(unsigned long deltaT)
{
  unsigned long currTime = seconds();
  long timeToDelay = deltaT - (currTime - timer);
  if (timeToDelay > 5000)
  {
    delay(timeToDelay / 1000);
    delayMicroseconds(timeToDelay % 1000);
  }
  else if (timeToDelay > 0)
  {
    delayMicroseconds(timeToDelay);
  }
  else
  {
      // timeToDelay is negative so we start immediately
  }
  timer = currTime + timeToDelay;
}

void sendToPC(int* data)
{
  byte* byteData = (byte*)(data);
  Serial.write(byteData, 2);
}

void sendToPC(double* data)
{
  byte* byteData = (byte*)(data);
  Serial.write(byteData, 4);
}
