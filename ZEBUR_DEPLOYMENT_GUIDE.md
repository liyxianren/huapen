# ESP8266传感器系统 - Zeabur部署指南

## 📋 项目概述

ESP8266传感器数据监控系统，支持前端按钮触发数据更新，通过云端指令控制硬件设备。

## 🚀 Zeabur部署步骤

### 1. 准备项目文件

确保项目包含以下文件结构：

```
esp8266-sensor-system/
├── app_sqlite.py              # 主应用文件 (20,825 bytes)
├── database.py                # 数据库操作模块
├── requirements.txt           # Python依赖
├── runtime.txt               # Python版本指定
├── Procfile                  # 应用启动配置
├── .gitignore               # Git忽略文件
├── templates/
│   ├── index.html           # 前端主页面
│   └── admin.html           # 管理页面
├── static/
│   ├── style.css            # 样式文件
│   └── script.js            # JavaScript脚本
├── esp8266_simple_upload/
│   └── esp8266_simple_upload.ino  # ESP8266固件
└── nano/
    └── nano.ino              # Arduino Nano固件
```

### 2. 文件配置详情

#### requirements.txt
```
Flask==3.0.0
gunicorn==21.2.0
```

#### runtime.txt
```
python-3.13
```

#### Procfile
```
web: gunicorn app_sqlite:app --host 0.0.0.0 --port $PORT
```

#### .gitignore
```
__pycache__/
*.pyc
*.db
.DS_Store
```

### 3. 部署到Zeabur

#### 方法A: GitHub部署（推荐）

1. **推送到GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: ESP8266 sensor monitoring system"
   git branch -M main
   git remote add origin https://github.com/yourusername/esp8266-sensor-system.git
   git push -u origin main
   ```

2. **在Zeabur中创建项目**
   - 登录 [Zeabur控制台](https://zeabur.com)
   - 点击"New Service"
   - 选择"Deploy from Git"
   - 连接GitHub仓库
   - 选择 `esp8266-sensor-system` 仓库

3. **自动配置检测**
   Zeabur会自动检测：
   - Provider: Python
   - Framework: Flask
   - Package Manager: pip
   - Python Version: 3.13

4. **确认部署设置**
   - 点击"Deploy Service"
   - 等待部署完成

#### 方法B: 直接文件上传

1. **创建ZIP压缩包**
   ```bash
   # 在项目根目录执行
   zip -r esp8266-sensor-system.zip . -x "*.git*" "__pycache__/*"
   ```

2. **在Zeabur中上传**
   - 选择"Upload Files"
   - 上传 `esp8266-sensor-system.zip`
   - 确认配置设置

### 4. 部署验证

#### 检查部署状态

1. **查看部署日志**
   - 在Zeabur控制台查看部署日志
   - 确认没有错误信息

2. **测试基础功能**
   ```bash
   # 测试API端点
   curl https://your-domain.zeabur.app/api

   # 期望响应：
   # {
   #   "endpoints": {
   #     "POST /sensor-command": "Process sensor commands from frontend",
   #     "GET /get-pending-command": "ESP8266 get pending commands"
   #   }
   # }
   ```

3. **测试前端页面**
   - 访问 `https://your-domain.zeabur.app`
   - 确认页面正常显示
   - 检查是否有"更新数据"按钮

#### 功能测试

1. **测试指令端点**
   ```bash
   curl -X POST https://your-domain.zeabur.app/sensor-command \
     -H "Content-Type: application/json" \
     -d '{"command":"Dataup_0"}'
   ```

2. **测试指令获取端点**
   ```bash
   curl https://your-domain.zeabur.app/get-pending-command
   ```

## 🔧 常见问题解决

### 问题1: 部署失败

**可能原因**:
- 缺少依赖包
- Python版本不兼容
- 启动命令错误

**解决方案**:
```bash
# 检查requirements.txt是否包含所需依赖
Flask==3.0.0
gunicorn==21.2.0

# 确保Procfile格式正确
web: gunicorn app_sqlite:app --host 0.0.0.0 --port $PORT
```

### 问题2: 数据库错误

**可能原因**:
- 数据库文件权限问题
- SQLite路径错误

**解决方案**:
- Zeabur会自动创建数据库文件
- 确保代码中使用相对路径

### 问题3: 前端页面无法访问

**可能原因**:
- templates文件夹缺失
- 静态文件路径错误

**解决方案**:
```bash
# 确保目录结构正确
templates/
├── index.html
static/
├── style.css
└── script.js
```

### 问题4: API端点404错误

**可能原因**:
- 代码未正确更新
- 缓存问题

**解决方案**:
- 在Zeabur中重新部署
- 检查app_sqlite.py是否包含路由定义

## 📊 监控和维护

### 日志查看
- Zeabur控制台 → Service → Logs
- 查看应用运行日志和错误信息

### 性能监控
- Zeabur控制台 → Service → Metrics
- 监控CPU、内存使用情况

### 数据备份
- 定期备份SQLite数据库
- 使用Zeabur的备份功能

## 🎯 部署后功能

部署成功后，系统支持以下功能：

1. **前端数据展示**
   - 实时传感器数据显示
   - 历史数据查询
   - 图表可视化

2. **指令处理系统**
   - 前端按钮触发数据更新
   - 云端指令管理
   - ESP8266指令获取

3. **硬件通信**
   - ESP8266与服务器通信
   - Arduino Nano指令执行
   - 传感器数据采集

## 📞 技术支持

如遇到部署问题：

1. **查看Zeabur文档**: https://zeabur.com/docs
2. **联系Zeabur支持**: 控制台 → Support
3. **检查社区论坛**: https://github.com/zeabur/zeabur

---

**部署完成后，您的ESP8266传感器系统将完全正常运行！** 🚀