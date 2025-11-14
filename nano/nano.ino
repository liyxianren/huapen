
//----------------------------------预处理-------
#include <SoftwareSerial.h>
// 定义软串口引脚 (RX, TX) - 与ESP8266通讯
SoftwareSerial esp8266(2, 3);

// 传感器引脚定义
#define Light_Pin        A0    // 光照传感器
#define Humidity_Pin     A1    // 湿度传感器
#define Temperature_Pin  A2    // 温度传感器

//---------------------------------全局变量-------
int Light = 0;                    // 光照强度 [0~1023]
float Humidity = 0.0;             // 湿度 [0~1023][湿➡干] - 改为float类型
float Temperature = 0.0;          // 温度 (摄氏度)
int Servo_angle = 90;             // 舵机角度

// 指令处理相关变量
String INchar = "";
String Sign = "";
int Number = -1;

// 调试和状态相关变量
unsigned long lastDebugTime = 0;
const unsigned long DEBUG_INTERVAL = 5000;  // 每5秒输出一次状态

// Nano仅响应指令，不自动发送数据

//-----------------------------------初始化--------
void setup() {
  Serial.begin(9600);           // 硬串口 - 调试输出
  esp8266.begin(9600);         // 软串口 - 与ESP8266通讯 (匹配ESP8266的波特率)

  // 初始化引脚
  pinMode(Light_Pin, INPUT);
  pinMode(Humidity_Pin, INPUT);
  pinMode(Temperature_Pin, INPUT);

  // 初始读取传感器数值
  Light = 100;
  Humidity = 50.0;
  Temperature = 25.0;

  // 舵机初始复位
  Servo_angle = 90;

  Serial.println("Arduino Nano 初始化完成");
  Serial.println("等待ESP8266指令...");
}

//-----------------------------------主循环---------
void loop() {
  // 检查来自ESP8266的指令
  if(esp8266.available() > 0) {
    Serial.println("检测到ESP8266串口数据...");
    INchar = esp8266.readStringUntil('\n');
    INchar.trim();  // 去除首尾空白

    Serial.println("接收到ESP8266数据: [" + INchar + "] (长度:" + String(INchar.length()) + ")");

    if(INchar.length() > 0) {
      // 过滤掉ESP8266启动信息和乱码
      if(INchar.startsWith("ESP8266_READY")) {
        Serial.println("✅ ESP8266已就绪，开始通讯");
        return;
      }

      // 只处理包含下划线的有效指令或已知的命令词
      if(INchar.indexOf('_') > 0 ||
         INchar.startsWith("Dataup") ||
         INchar.startsWith("Watering") ||
         INchar.startsWith("ServoTurnTo") ||
         INchar.startsWith("Reset") ||
         INchar.startsWith("Status")) {

        Serial.println("✅ 收到有效ESP8266指令: " + INchar);

        // 处理指令
        Get(INchar);        // 提取命令词和参数
        Command();          // 识别并执行命令

        // 清理变量
        INchar = "";
        Sign = "";
        Number = -1;
      } else {
        // 忽略无效的ESP8266调试信息
        // Serial.println("忽略ESP8266调试信息: " + INchar);
      }
    }
  }

  // 定期输出调试信息
  unsigned long currentTime = millis();
  if(currentTime - lastDebugTime >= DEBUG_INTERVAL) {
    lastDebugTime = currentTime;
    Serial.println("🔍 Nano运行正常 - 等待ESP8266指令...");
    Serial.println("  串口状态: 软串口(RX:" + String(digitalRead(2)) + ",TX:" + String(digitalRead(3)) + ")");
  }

  delay(50);  // 短暂延时，避免过度占用CPU
}

//------------------------------------函数定义-------

//------------------------------------读取传感器数据-------
void readSensorData() {
  // 测试模式：使用预定义的传感器数据进行验证
  static int testCounter = 0;
  testCounter++;

  // 模拟变化的传感器数据用于测试，符合前端要求的数据范围
  Light = 50 + (testCounter % 10) * 10;           // 光照强度: 50-140
  Humidity = 40.0 + (testCounter % 8) * 2.5;      // 湿度: 40-57.5%
  Temperature = 20.0 + (testCounter % 6) * 1.5;   // 温度: 20-27.5°C
  Servo_angle = (testCounter * 30) % 180;         // 舵机: 0-150度循环

  Serial.println("=== 测试传感器数据生成 ===");
  Serial.print("测试次数: "); Serial.println(testCounter);
  Serial.print("  Light: "); Serial.print(Light); Serial.println(" (light_intensity)");
  Serial.print("  Humidity: "); Serial.print(Humidity, 1); Serial.println("%");
  Serial.print("  Temperature: "); Serial.print(Temperature, 1); Serial.println("°C");
  Serial.print("  Servo_angle: "); Serial.print(Servo_angle); Serial.println("°");
  Serial.println("===========================");
}

//------------------------------------数据上传-------
void DataUp() {
  Serial.println("执行数据更新指令...");

  // 立即读取最新传感器数据
  readSensorData();

  // 发送数据到ESP8266
  sendDataToESP8266();

  Serial.println("数据更新完成");
}

//------------------------------------发送数据到ESP8266-------
void sendDataToESP8266() {
  // 发送短协议JSON格式数据到ESP8266 (节省串口带宽)
  // 短协议映射: light->light_intensity, hum->humidity, temp->temperature, servo->servo_angle
  String jsonString = "{";
  jsonString += "\"light\":" + String(Light) + ",";
  jsonString += "\"hum\":" + String(Humidity, 1) + ",";
  jsonString += "\"temp\":" + String(Temperature, 1) + ",";
  jsonString += "\"servo\":" + String(Servo_angle);
  jsonString += "}";

  Serial.println("=== 发送传感器数据到ESP8266 ===");
  Serial.print("传感器数据: Light=");
  Serial.print(Light);
  Serial.print(", Humidity=");
  Serial.print(Humidity, 1);
  Serial.print(", Temperature=");
  Serial.print(Temperature, 1);
  Serial.print(", Servo_angle=");
  Serial.println(Servo_angle);

  Serial.print("短协议JSON: ");
  Serial.println(jsonString);
  Serial.print("数据长度: ");
  Serial.print(jsonString.length());
  Serial.println(" 字节");

  // 发送数据到ESP8266
  delay(50);  // 确保ESP8266准备好接收
  esp8266.println(jsonString);
  esp8266.flush();

  Serial.println("数据已发送，等待ESP8266响应...");

  // 等待ESP8266响应 (最多等待10秒)
  unsigned long startTime = millis();
  const unsigned long RESPONSE_TIMEOUT = 10000;  // 10秒超时
  String response = "";

  while (millis() - startTime < RESPONSE_TIMEOUT) {
    if (esp8266.available() > 0) {
      response = esp8266.readStringUntil('\n');
      response.trim();

      if (response.length() > 0) {
        Serial.println("收到ESP8266响应: " + response);

        // 检查响应内容
        if (response == "OK") {
          Serial.println("✅ 数据上传成功！");
          break;
        } else if (response.startsWith("FAIL")) {
          Serial.println("❌ 数据上传失败: " + response);
          Serial.println("⚠️ 本次数据更新已抛弃");
          break;
        }
      }
    }
    delay(10);  // 短暂延时，避免过度占用CPU
  }

  // 检查是否超时
  if (response.length() == 0 || (!response.equals("OK") && !response.startsWith("FAIL"))) {
    Serial.println("⏱️ 等待ESP8266响应超时或收到无效响应");
  }

  Serial.println("=== 数据发送流程结束 ===");
  Serial.println();
}

//--------------------------------浇水(毫秒)---------
void Watering(int Time){ 
  Serial.println("开始浇水,时长"+Time);
}

//--------------------------------舵机转到(角度)------
void ServoTurnTo(int angle){ 
  Serial.println("舵机转至角度"+angle);
}

//----------------------------抓取命令词和参数----------
void Get(String input) {
  // 从字符串中获取下划线_位置
  int underscoreIndex = input.indexOf('_');
  if (underscoreIndex != -1) {
    // 截取下划线_左半段为命令词
    Sign = input.substring(0, underscoreIndex);
    Sign.trim();  // 去除空白字符

    // 截取下划线_右半段为参数
    String rightPart = input.substring(underscoreIndex + 1);
    rightPart.trim();
    Number = rightPart.toInt();

    Serial.println("解析指令 - 命令: " + Sign + ", 参数: " + Number);
  } else {
    // 没有下划线，可能是一个无参数的命令
    Sign = input;
    Sign.trim();
    Number = -1;
    Serial.println("解析指令 - 命令: " + Sign + " (无参数)");
  }
}

//-------------------------------识别命令词,执行任务-----
// 支持的指令:
// "Dataup_0" - 执行数据更新，参数被忽略
// "Watering_10" - 浇水10毫秒
// "ServoTurnTo_90" - 舵机转到90度
// "Reset" - 系统重置
// 默认: 回复"Command_error"

void Command() {
  if (Sign == "Dataup") {
    Serial.println("🚀 执行Dataup命令...");
    DataUp();
    esp8266.println("Dataup_done");

  } else if (Sign == "Watering") {
    Serial.println("💧 执行Watering命令，参数: " + String(Number));
    Watering(Number);
    esp8266.println("Watering_done");

  } else if (Sign == "ServoTurnTo") {
    Serial.println("🔧 执行ServoTurnTo命令，角度: " + String(Number));
    ServoTurnTo(Number);
    esp8266.println("ServoTurnTo_done");

  } else if (Sign == "Reset") {
    // 系统重置
    Serial.println("🔄 执行系统重置...");
    Servo_angle = 90;
    readSensorData();
    sendDataToESP8266();
    esp8266.println("Reset_done");

  } else if (Sign == "Status") {
    // 状态查询
    Serial.println("📊 执行Status命令...");
    String statusMsg = "Status:" + String(Light) + "," + String(Humidity) + "," + String(Temperature, 1) + "," + String(Servo_angle);
    esp8266.println(statusMsg);

  } else {
    Serial.println("❌ 未知指令: " + Sign);
    esp8266.println("Command_error");
  }
}
