#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <secrets.h>

#define MPU6050_ADDR 0x68
#define INT_PIN 2

const char* ssid = SECRET_SSID;
const char* password = SECRET_PASSWORD;


const char* MQTT_Adress = SECRET_MQTT_ADRESS;
const int MQTT_Port = SECRET_MQTT_PORT;

const char* mqttusername = SECRET_MQTT_USERNAME;
const char* mqttpassword = SECRET_MQTT_PASSWORD;

const char* MQTT_Surface = "home/livingroom/smartcube/surface";
const char* MQTT_Shaking = "home/livingroom/smartcube/shaking";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long startTime = 0;

void sendmqtt(int surface, String shaking);
void getdata();
int getsurface();
bool getshake();
void writeRegister(uint8_t reg, uint8_t value);
void startdeepsleeptimer(int surface) {
  // Calculate the time until the next full minute
  static unsigned long currentTime = millis();

  if(millis() - currentTime > 10000) {

    bool state = digitalRead(INT_PIN); // The following lines will make the ESP go out of a deep sleep on toggle

    if(state == HIGH) 
    {
      esp_deep_sleep_enable_gpio_wakeup(BIT(INT_PIN),ESP_GPIO_WAKEUP_GPIO_LOW);
    } 
    else 
    {
      esp_deep_sleep_enable_gpio_wakeup(BIT(INT_PIN),ESP_GPIO_WAKEUP_GPIO_HIGH);
    }
    currentTime = millis();
    if(surface != 0)
      {
        sendmqtt(surface, "Ruhig");
      }
    
    esp_deep_sleep_start();
  }
  


}

void setup() {
  Serial.begin(115200);
  startTime = millis();
  pinMode(INT_PIN, INPUT_PULLUP);
  Wire.begin();
  writeRegister(0x6B, 0x00); // Wake up MPU6050
  const unsigned long wifistarttime = millis();
  int counter = 0;
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
    {
      delay(500);
      if(millis() - wifistarttime > 10000) 
        {
          if(counter == 0) 
            {
              WiFi.begin(SECRET_SSID1, SECRET_PASSWORD1);
              counter++;
            }
          else if(counter == 1) 
            {
              WiFi.begin(SECRET_SSID2, SECRET_PASSWORD2);
              counter++;
            }
          else 
            {
              Serial.println("Could not connect to WiFi");
              startdeepsleeptimer(0);
              break;
            }
        }
    } 
  Serial.println("Connected to WiFi");
  client.setServer(MQTT_Adress, MQTT_Port);
  
}

void loop() {
  static unsigned long lastsurfaceTime = 0;
  static unsigned long lastshakeTime = 0;
  static int surface;
  bool lastshake = false;
  
  //getdata();

  if(millis() - lastsurfaceTime > 1000) {
    surface = getsurface();
    sendmqtt(surface, "Ruhig");
    lastsurfaceTime = millis();
  }
  bool isshaked = getshake();
  if(isshaked != lastshake) 
    {
      if(isshaked) 
        {
          sendmqtt(surface, "Geschüttelt");
        }
      else 
        {
          sendmqtt(surface, "Ruhig");
        }
    }
  lastshake = isshaked;
  startdeepsleeptimer(surface);

  }

void sendmqtt(int surface, String shaking) {
  if (!client.connected()) {
    while (!client.connect("ESP32Client", mqttusername, mqttpassword)) {
      delay(500);
    }
  }
  
  client.publish(MQTT_Surface, String(surface).c_str());
  client.publish(MQTT_Shaking, shaking.c_str());

}

void getdata() {
  // Read 14 bytes starting at 0x3B (Accel, Temp, Gyro)
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR, 14, true);

  

  int16_t AcX = Wire.read() << 8 | Wire.read();
  int16_t AcY = Wire.read() << 8 | Wire.read();
  int16_t AcZ = Wire.read() << 8 | Wire.read();
  int16_t Tmp = Wire.read() << 8 | Wire.read();
  int16_t GyX = Wire.read() << 8 | Wire.read();
  int16_t GyY = Wire.read() << 8 | Wire.read();
  int16_t GyZ = Wire.read() << 8 | Wire.read();

  Serial.println("Accel: " + String(AcX) + ", " + String(AcY) + ", " + String(AcZ));
  Serial.println("Gyro: " + String(GyX) + ", " + String(GyY) + ", " + String(GyZ));
  Serial.println();
  

}

int getsurface() {
   
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR, 14, true);

  int16_t AcX = Wire.read() << 8 | Wire.read();
  int16_t AcY = Wire.read() << 8 | Wire.read();
  int16_t AcZ = Wire.read() << 8 | Wire.read();

  if (AcZ > 15000) {
    return 1; // Surface up
  } else if (AcZ < -15000) {
    return 6; // Surface down
  } else if (AcX > 15000) {
    return 2; // Surface right
  } else if (AcX < -15000) {
    return 5; // Surface left
  } else if (AcY > 15000) {
    return 3; // Surface front
  } else if (AcY < -15000) {
    return 4; // Surface back
  } else {
    return 1; // No significant orientation
    
  }

}


void writeRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

bool getshake() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR, 14, true);

  int16_t AcX = Wire.read() << 8 | Wire.read();
  int16_t AcY = Wire.read() << 8 | Wire.read();
  int16_t AcZ = Wire.read() << 8 | Wire.read();

  static int16_t AcXold = 0;
  static int16_t AcYold = 0;

  static unsigned long lastShakeTime = 0;
  static int shakenumber = 0;

  int16_t deltax = AcX - AcXold;
  int16_t deltay = AcY - AcYold;

  bool xpos = false;
  bool ypos = false;
  bool xneg = false;
  bool yneg = false;

  if(deltax > 20000 && xpos == false || deltay > 20000 && ypos == false || deltay < -20000 && yneg == false || deltay < -20000 && yneg == false) 
    {
      lastShakeTime = millis();
      if(deltax > 20000) 
        {
          xpos = true;
        }
      else
        {
          xpos = false;
        }
      if(deltay > 20000) 
        {
          ypos = true;
        }
      else
        {
          ypos = false;
        }
      if(deltax < -20000) 
        {
          xneg = true;
        }
      else
        {
          xneg = false;
        }
      if(deltay < -20000) 
        {
          yneg = true;
        }
      else
        {
          yneg = false;
        }
    }
  
  if(millis() - lastShakeTime > 200) 
    {
      shakenumber = 0;
      xpos = false;
      ypos = false;
      xneg = false;
      yneg = false;
    }
  else
    {
      shakenumber++;
    }

    if(shakenumber > 5) 
    {
      return true;
    }
    else 
    {
      return false;
    }


}

