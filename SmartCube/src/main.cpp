#include <Arduino.h>
#include <Wire.h>
#include <Wifi.h>
#include <PubSubClient.h>


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

void setup() {
  Serial.begin(115200);
  startTime = millis();
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  Serial.println("Connected to WiFi");
  client.setServer(MQTT_Adress, MQTT_Port);
}

void loop() {
  sendmqtt();

}

void sendmqtt() {
  if (!client.connected()) {
    while (!client.connect("ESP32Client", mqttusername, mqttpassword)) {
      delay(500);
    }
  }
  unsigned long currentTime = millis();
  client.publish("home/livingroom/smartcube/test", String(currentTime - startTime).c_str());
  Serial.println("Published: " + String(currentTime - startTime));
  while(true) {
    delay(1000);
  }
  
}