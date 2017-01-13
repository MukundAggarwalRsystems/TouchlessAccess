// Demo for Grove - Starter Kit V2.0

// Prints the value of the potentiometer to the serial console.
// Connect the Grove - Rotary Angle Sensor to the socket marked A0
// Open the Serial Monitor in the Arduino IDE after uploading

// Define the pin to which the angle sensor is connected.
#include<string.h>
#include <Wire.h>
#include "rgb_lcd.h"

rgb_lcd lcd;

int colorR = 0;
int colorG = 0;
int colorB = 0;

const int potentiometer = A0;

FILE* tempFile;
char buff[100];
void setup()
{
  // set up the LCD's number of columns and rows:
    lcd.begin(16, 2);
    
    lcd.setRGB(colorR, colorG, colorB);
    
    // Print a message to the LCD.
    // Configure the serial communication line at 9600 baud (bits per second.)
    Serial.begin(9600);
    Serial.println("Code started.");
    // Configure the angle sensor's pin for input.

    tempFile = fopen("/home/root/temp.txt","r");
  
    // Read the value of the sensor and print it to the serial console.
   
   fread(buff, 4, 1, tempFile);
    Serial.print(buff);
    Serial.println();
  

    // Wait 0.1 seconds between readings.
    delay(10);
    fclose(tempFile);
}
int gateflag = 0;
int lcdflag = 0;
void loop()
{
  
    tempFile = fopen("/home/root/temp.txt","r");
    memset(buff, '\0',sizeof(buff));
    // Read the value of the sensor and print it to the serial console.
    fread(buff, 4, 1, tempFile);
    //Serial.print(buff);
    //Serial.println();
      
    fclose(tempFile);

    if(strcmp(buff,"open") == 0)
    {
      Serial.println("Open the gate");
      colorR = 0;
      colorG = 255;
      colorB = 0;
      lcd.setRGB(colorR, colorG, colorB);
      lcd.setCursor(0, 1);
      if (lcdflag != 1)
      {
        lcd.clear();
        lcd.print("Open the Gate");
      }
      gateflag = 0;
      lcdflag = 1;
    }
    if(strcmp(buff ,"clos")==0 && gateflag == 0)
    {
      Serial.println("Close the gate");
      colorR = 255;
      colorG = 0;
      colorB = 0;
      lcd.setRGB(colorR, colorG, colorB);
      lcd.setCursor(0, 1);
      lcd.clear();
      lcd.print("Close the Gate");
      gateflag = 1;
      lcdflag = 0;
    }
    // Wait 0.1 seconds between readings.
    delay(10);
}

