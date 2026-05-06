#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>


#define MPU6050_ADDR 0x68


const char* ssid = "LIONS_HOME_OG";
const char* password = "68133733";


const char* MQTT_Adress = "10.0.0.68";
const int MQTT_Port = 1883;

const char* mqttusername = "mqtt";
const char* mqttpassword = "mqtt";

const char* MQTT_Surface = "home/livingroom/smartcube/surface";
const char* MQTT_Shaking = "home/livingroom/smartcube/shaking";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long startTime = 0;

void sendmqtt(int surface);
void getdata();
int getsurface();
void writeRegister(uint8_t reg, uint8_t value);

void setup() {
  Serial.begin(115200);
  startTime = millis();
  Wire.begin();
  writeRegister(0x6B, 0x00); // Wake up MPU6050
  writeRegister(0x38, 0b0100000); // Enable I2C bypass
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  Serial.println("Connected to WiFi");
  client.setServer(MQTT_Adress, MQTT_Port);
}

void loop() {
  static unsigned long lastsurfaceTime = 0;
  getdata();
  static int surface;
  if(millis() - lastsurfaceTime > 1000) {
    surface = getsurface();
    lastsurfaceTime = millis();
  }
  sendmqtt(surface);

}

void sendmqtt(int surface) {
  if (!client.connected()) {
    while (!client.connect("ESP32Client", mqttusername, mqttpassword)) {
      delay(500);
    }
  }
  unsigned long currentTime = millis();
  client.publish(MQTT_Surface, String(surface).c_str());
  
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