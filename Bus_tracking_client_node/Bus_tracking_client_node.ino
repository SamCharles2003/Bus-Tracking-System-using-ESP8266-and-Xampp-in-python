#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include<SoftwareSerial.h>
#include <TinyGPS++.h>

TinyGPSPlus gps;
SoftwareSerial gps_dev(D3,D4); //D3 ,D4
const char *ssid = "Galaxy A14 5G";
const char *password = "masleschar3002";
String serverAddress = "http://192.168.108.215:5000"; // Change this to the IP address of your server


int bus_no=3;

void setup() {
    
  Serial.begin(115200);
  gps_dev.begin(9600);
  WiFi.begin(ssid, password);
  pinMode(D9,OUTPUT);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi"+String(WiFi.localIP().toString()));
}

void loop() {

  while (gps_dev.available() > 0){
    if (gps.encode(gps_dev.read())){

 if(gps.location.isUpdated())
  {
   
    sendToServer(String(gps.location.lat(), 6),String(gps.location.lng(), 6));
    Serial.print("Latitude:"+String(gps.location.lat(), 6)+"\t"+"Longitude:"+String(gps.location.lng(), 6)+"\n");
    Serial.println("Data sent to server");
  } 
  else 
  {
    Serial.println("Location Not Yet Detected");
  }
  }
  }
  
}

void sendToServer(String latitude, String longitude) {
  WiFiClient wifiClient;
  HTTPClient http;

  String url = serverAddress + "/location_update";

  Serial.println("Sending data to server...");

  http.begin(wifiClient, url);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");

  // Build the POST body
  String postBody = "latitude=" + latitude + "&longitude=" + longitude+ "&bun_no=" + String(bus_no);

  int httpCode = http.POST(postBody);

  if (httpCode == HTTP_CODE_OK) {
    Serial.println("Server response: " + http.getString());
    
  } else {
    Serial.println("HTTP request failed with code " + String(httpCode));
    
  }

  http.end();

}







