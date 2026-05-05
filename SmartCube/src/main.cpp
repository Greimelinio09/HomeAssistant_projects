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

void sendmqtt();
void getdata();

void setup() {
  Serial.begin(115200);
  for(int i = 0; i < 5; i++) {
    Serial.println("Hello World!");
    delay(1000);
  }
  startTime = millis();
  Wire.begin();
  // Wake up MPU6050: write 0 to PWR_MGMT_1 (0x6B)
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);
  Wire.endTransmission();
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  Serial.println("Connected to WiFi");
  client.setServer(MQTT_Adress, MQTT_Port);
}

void loop() {
  
  getdata();
  sendmqtt();

}

void sendmqtt() {
  if (!client.connected()) {
    while (!client.connect("ESP32Client", mqttusername, mqttpassword)) {
      delay(500);
    }
  }
  unsigned long currentTime = millis();
  
  
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
  delay(1000);

}