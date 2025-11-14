/**
 * ESP8266 主流程 - 改进版（防止数据丢失）
 * 功能: 接收Nano传感器数据并上传到云端服务器
 *
 * 硬串口(Serial): 用于调试输出 (USB连接电脑) - 9600波特率
 * 软串口(nanoSerial): 用于与Arduino Nano通讯 - 9600波特率
 *
 * 硬件连接:
 * - ESP8266 D2(GPIO4/RX) ← Nano TX
 * - ESP8266 D1(GPIO5/TX) → Nano RX
 * - GND ↔ GND
 *
 * 改进说明:
 * 1. 增加软串口缓冲区到256字节（默认64字节）
 * 2. 使用超时机制逐字符接收，避免数据丢失
 * 3. 改进的JSON验证和错误处理
 */

// ========== 增加软串口缓冲区大小 ==========
// 重要: 必须在 #include <SoftwareSerial.h> 之前定义
#define _SS_MAX_RX_BUFF 256  // 将缓冲区从64字节增加到256字节

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <SoftwareSerial.h>
#include <ArduinoJson.h>

// ========== WiFi配置 ==========
const char* ssid = "SCF-XIAOMI";        // 修改为你的WiFi名称
const char* password = "scf888888";     // 修改为你的WiFi密码

// ========== 云端服务器配置 ==========
const char* serverURL = "https://edisonchan.zeabur.app/sensor-data";
const char* commandURL = "https://edisonchan.zeabur.app/get-pending-command";

// ========== 串口配置 ==========
// 软串口: ESP8266 GPIO4=RX=D2, GPIO5=TX=D1
SoftwareSerial nanoSerial(4, 5);  // RX, TX

// ========== 全局变量 ==========
WiFiClientSecure client;  // HTTPS客户端
const unsigned long CHAR_TIMEOUT = 100;  // 字符超时时间(ms)

// 指令检查相关变量
unsigned long lastCommandCheckTime = 0;
const unsigned long COMMAND_CHECK_INTERVAL = 2000;  // 每2秒检查一次指令

void setup() {
  // 启动硬串口用于调试输出
  Serial.begin(9600);
  delay(1000);

  // 启动软串口用于与Arduino Nano通讯
  nanoSerial.begin(9600);

  // 初始化内置LED
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);  // 灯灭

  Serial.println("\nESP8266启动中...");

  // 连接WiFi
  connectToWiFi();

  // 配置HTTPS (忽略证书验证)
  client.setInsecure();

  // ESP8266初始化完成后，等待Nano就绪再发送信号
  delay(3000);  // 等待Nano完全初始化

  // 发送就绪信号给Nano
  nanoSerial.println("ESP8266_READY");
  Serial.println("ESP8266就绪\n");
}

void loop() {
  // 检查WiFi连接
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi断开，重新连接...");
    digitalWrite(LED_BUILTIN, LOW);
    connectToWiFi();
    delay(1000);
    return;
  }

  // 接收Nano数据并直接转发到云端
  receiveAndForwardNanoData();

  // 定期检查云端指令
  unsigned long currentTime = millis();
  if (currentTime - lastCommandCheckTime >= COMMAND_CHECK_INTERVAL) {
    lastCommandCheckTime = currentTime;
    checkPendingCommands();
  }

  delay(100);
}

// 转换短协议为长协议
// 短协议: {"light":60,"hum":42.5,"temp":21.5,"servo":30}
// 长协议: {"light_intensity":60,"humidity":42.5,"temperature":21.5,"servo_angle":30}
String convertToLongProtocol(String shortJson) {
  String longJson = shortJson;

  // 替换字段名（使用字符串替换）
  longJson.replace("\"light\":", "\"light_intensity\":");
  longJson.replace("\"hum\":", "\"humidity\":");
  longJson.replace("\"temp\":", "\"temperature\":");
  longJson.replace("\"servo\":", "\"servo_angle\":");

  return longJson;
}

// 连接WiFi网络
void connectToWiFi() {
  Serial.print("连接WiFi...");

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.println("WiFi已连接 IP: " + WiFi.localIP().toString());
  } else {
    digitalWrite(LED_BUILTIN, LOW);
    Serial.println("WiFi连接失败");
  }
}

// 接收Nano数据并直接转发到云端
void receiveAndForwardNanoData() {
  static bool isReading = false;  // 防止重复读取

  if (nanoSerial.available() > 0 && !isReading) {
    isReading = true;

    String receivedString = "";
    unsigned long lastCharTime = millis();

    // 使用超时机制逐字符接收，避免数据丢失
    while (true) {
      if (nanoSerial.available() > 0) {
        char c = nanoSerial.read();
        receivedString += c;
        lastCharTime = millis();
      }

      // 如果超过100ms没有新字符到达，认为接收完成
      if (millis() - lastCharTime > CHAR_TIMEOUT) {
        break;
      }

      delay(1);
    }

    receivedString.trim();  // 去除首尾空白

    Serial.println("接收: " + receivedString);

    // 验证JSON格式
    if (receivedString.length() > 0 && receivedString.startsWith("{")
  && receivedString.endsWith("}")) {
      // 检查是否是有效的JSON
      int braceCount = 0;
      bool validJson = true;

      for (int i = 0; i < receivedString.length(); i++) {
        char c = receivedString.charAt(i);
        if (c == '{') braceCount++;
        if (c == '}') braceCount--;
        if (braceCount < 0) {
          validJson = false;
          break;
        }
      }

      if (validJson && braceCount == 0) {
        // 检查是否包含必需字段（短协议）
        bool hasRequiredFields = (receivedString.indexOf("\"temp\"") > 0 ||
                                   receivedString.indexOf("\"hum\"") > 0 ||
                                   receivedString.indexOf("\"light\"") > 0);

        if (hasRequiredFields) {
          // 转换短协议为长协议
          String longProtocolJson = convertToLongProtocol(receivedString);
          
          Serial.println("发送: " + longProtocolJson);

          // 使用转换后的长协议JSON
          receivedString = longProtocolJson;
          // LED快闪表示正在发送
          digitalWrite(LED_BUILTIN, LOW);

          HTTPClient http;
          http.begin(client, serverURL);
          http.addHeader("Content-Type", "application/json");
          http.setTimeout(15000);

          int httpCode = http.POST(receivedString);

          if (httpCode == 200 || httpCode == 201) {
            Serial.println("上传成功 HTTP: " + String(httpCode));

            // 向NANO发送成功状态
            nanoSerial.println("OK");
            nanoSerial.flush();

            // 成功闪烁3次
            for (int i = 0; i < 3; i++) {
              digitalWrite(LED_BUILTIN, LOW);
              delay(100);
              digitalWrite(LED_BUILTIN, HIGH);
              delay(100);
            }
          } else {
            Serial.println("上传失败 HTTP: " + String(httpCode));

            // 向NANO发送失败状态
            nanoSerial.println("FAIL:" + String(httpCode));
            nanoSerial.flush();
          }

          http.end();
          digitalWrite(LED_BUILTIN, HIGH);
        } else {
          Serial.println("数据缺少必需字段");
        }
      } else {
        Serial.println("JSON格式无效");
      }
    } else {
      if (receivedString.length() > 0) {
        Serial.println("非JSON数据: " + receivedString);
      }
    }

    // 重置读取状态
    isReading = false;
  }
}

// 检查云端服务器是否有待处理的指令
void checkPendingCommands() {
  HTTPClient http;
  http.begin(client, commandURL);
  http.setTimeout(5000);  // 5秒超时

  int httpCode = http.GET();

  if (httpCode == 200) {
    String response = http.getString();

    // 简单解析JSON响应
    if (response.indexOf("\"has_command\":true") > 0) {
      // 提取指令内容
      int commandStart = response.indexOf("\"command\":\"");
      if (commandStart > 0) {
        commandStart += 11;  // 跳过"command":"
        int commandEnd = response.indexOf("\"", commandStart);
        if (commandEnd > commandStart) {
          String command = response.substring(commandStart, commandEnd);
          Serial.println("云端指令: " + command);

          // 转发指令到Arduino Nano
          forwardCommandToNano(command);
        }
      }
    }
  }

  http.end();
}

// 转发指令到Arduino Nano
void forwardCommandToNano(String command) {
  Serial.println("转发: " + command);

  // 通过软串口发送指令到Arduino Nano
  nanoSerial.println(command);
  nanoSerial.flush();

  // LED闪烁表示指令转发
  for (int i = 0; i < 2; i++) {
    digitalWrite(LED_BUILTIN, LOW);
    delay(50);
    digitalWrite(LED_BUILTIN, HIGH);
    delay(50);
  }
}
