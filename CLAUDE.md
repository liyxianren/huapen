# ESP8266 Sensor Monitoring System - Technical Documentation

## Project Overview

This ESP8266 sensor monitoring system is a Flask-based web application that collects environmental data (temperature, humidity, light intensity, servo angle) from ESP8266/Arduino Nano hardware and provides a web interface for data visualization and hardware control. The system features real-time data collection, historical data analysis, and remote hardware control capabilities.

## System Architecture

### Hardware Layer
- **ESP8266**: WiFi microcontroller acting as communication bridge
- **Arduino Nano**: Sensor data collection and actuator control
- **Sensors**: Light (A0), Humidity (A1), Temperature (A2)
- **Actuators**: Servo motor for position control, water valve for irrigation

### Communication Flow
```
Arduino Nano → (Serial 9600) → ESP8266 → (HTTPS) → Flask Server → Web Interface
Web Interface → (HTTPS) → Flask Server → ESP8266 → (Serial) → Arduino Nano
```

### Software Components
- **app_sqlite.py**: Main Flask application with REST API endpoints
- **database.py**: SQLite database operations and data management
- **templates/**: Jinja2 HTML templates for web interface
- **static/**: CSS/JavaScript frontend assets
- **esp8266_simple_upload.ino**: ESP8266 firmware
- **nano.ino**: Arduino Nano firmware

## Development Setup

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask application
python app_sqlite.py
# OR
flask run --host=0.0.0.0 --port=5000
```

### Environment Variables
- `PORT`: Server port (default: 5000)
- `FLASK_ENV`: Set to 'production' for production deployment

### Database Initialization
The SQLite database (`sensor_data.db`) is automatically created on first run with the following schema:

```sql
CREATE TABLE sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    humidity REAL NOT NULL,
    temperature REAL NOT NULL,
    light_intensity INTEGER NOT NULL,
    servo_angle INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL,         -- ISO format with timezone
    created_at TEXT NOT NULL,        -- YYYY-MM-DD HH:MM:SS
    year INTEGER NOT NULL,           -- For time-based queries
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    date_key TEXT NOT NULL,          -- YYYY-MM-DD
    datetime_key TEXT NOT NULL       -- YYYY-MM-DD-HH
);
```

## API Endpoints

### Data Reception
- `POST /sensor-data` - Receive JSON sensor data from ESP8266
  - Required fields: `humidity`, `temperature`, `light_intensity`
  - Optional field: `servo_angle` (default: 0)

### Data Retrieval
- `GET /sensor-data` - Get all sensor data (supports `limit` and `offset` params)
- `GET /sensor-data/latest` - Get most recent sensor reading
- `GET /sensor-data/statistics` - Get data statistics (min, max, avg)
- `GET /sensor-data/dates` - Get available dates with data counts
- `GET /sensor-data/year/<year>` - Get data by year
- `GET /sensor-data/month/<year>/<month>` - Get data by month
- `GET /sensor-data/day/<year>/<month>/<day>` - Get data by specific day
- `GET /sensor-data/hour/<year>/<month>/<day>/<hour>` - Get data by hour
- `GET /sensor-data/date/<date_key>` - Get data by date key (YYYY-MM-DD)
- `GET /sensor-data/datetime/<datetime_key>` - Get data by datetime key (YYYY-MM-DD-HH)
- `GET /sensor-data/hours?date_key=YYYY-MM-DD` - Get available hours

### Data Management
- `GET /sensor-data/export` - Export all data to JSON file
- `POST /sensor-data/backup` - Create database backup
- `DELETE /sensor-data/clear` - Clear all sensor data

### Hardware Control
- `POST /sensor-command` - Process commands from web interface
- `GET /get-pending-command` - ESP8266 retrieves pending commands

### System Information
- `GET /api` - System information and endpoint documentation
- `GET /` - Main web interface
- `GET /admin` - Admin panel with statistics

## Hardware Communication Protocols

### ESP8266 → Arduino Nano
Commands are sent as plain text strings:
- `Dataup_0` - Trigger sensor reading and data upload
- `Watering_<milliseconds>` - Activate water valve for specified duration
- `ServoTurnTo_<angle>` - Move servo to specified angle (0-180°)
- `Reset` - Reset system to default state
- `Status` - Request current sensor status

### Arduino Nano → ESP8266
Sensor data is sent as JSON using short protocol to minimize bandwidth:
```json
{"light":850,"hum":65.2,"temp":25.6,"servo":90}
```

ESP8266 automatically converts short protocol to long protocol:
- `light` → `light_intensity`
- `hum` → `humidity`
- `temp` → `temperature`
- `servo` → `servo_angle`

### ESP8266 ↔ Server
HTTPS communication with JSON payloads:
- **POST** sensor data to `/sensor-data`
- **GET** pending commands from `/get-pending-command`

## Frontend Features

### Real-time Dashboard
- Live sensor data display with trend indicators
- Interactive charts using Chart.js
- Manual data refresh capability
- Status indicator showing system connectivity

### Data Query Interface
- Date-based data filtering
- Hour-based data filtering
- Query reset functionality
- Pagination support for large datasets

### Control Panel
- **Update Data Button**: Triggers `Dataup_0` command to ESP8266
- **Watering Controls**: Send irrigation commands with duration
- **Sunshade Controls**: Servo position control for shade management
- **Command Status**: Real-time feedback on command execution

### Admin Panel (`/admin`)
- Database statistics
- Data management tools
- Export and backup functionality

## Deployment Process

### Zeabur Cloud Deployment

#### Files Required
```
├── app_sqlite.py              # Main Flask application
├── database.py                # Database operations
├── requirements.txt           # Python dependencies
├── runtime.txt               # Python 3.13 specification
├── Procfile                  # Gunicorn startup command
├── main.py                   # Entry point for Zeabur
├── templates/                # HTML templates
├── static/                   # CSS/JS assets
└── zbpack.json              # Zeabur build configuration
```

#### Deployment Configuration

**requirements.txt:**
```
Flask==3.0.0
gunicorn==21.2.0
pytz==2023.3
```

**runtime.txt:**
```
python-3.13
```

**Procfile:**
```
web: gunicorn app_sqlite:app -b 0.0.0.0:$PORT
```

**zbpack.json:**
```json
{
  "app_name": "ESP8266 Sensor System",
  "build_command": "pip install -r requirements.txt",
  "start_command": "gunicorn app_sqlite:app -b 0.0.0.0:$PORT"
}
```

#### Deployment Steps
1. Push code to GitHub repository
2. Create new Zeabur service from Git
3. Zeabur automatically detects Python Flask framework
4. Configure environment variables if needed
5. Deploy and access via provided URL

### Hardware Configuration

#### Arduino Nano Pinout
- A0: Light sensor (analog input)
- A1: Humidity sensor (analog input)
- A2: Temperature sensor (analog input)
- D2: RX to ESP8266 TX (SoftwareSerial)
- D3: TX to ESP8266 RX (SoftwareSerial)

#### ESP8266 Pinout
- D1 (GPIO5): TX to Arduino Nano RX
- D2 (GPIO4): RX from Arduino Nano TX
- Built-in LED: Status indicator

#### WiFi Configuration
Update these in `esp8266_simple_upload.ino`:
```cpp
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverURL = "https://your-domain.zeabur.app/sensor-data";
const char* commandURL = "https://your-domain.zeabur.app/get-pending-command";
```

## Key Technical Decisions

### Database Design
- **SQLite**: Chosen for simplicity and Zeabur compatibility
- **Time-based indexing**: Optimized for temporal queries with separate year/month/day/hour fields
- **Beijing Timezone**: All timestamps stored in Asia/Shanghai timezone for consistency

### Communication Protocol
- **Short Protocol**: Minimizes serial transmission bandwidth between Arduino and ESP8266
- **HTTPS Encryption**: Secure communication between ESP8266 and cloud server
- **Polling-based Command System**: ESP8266 checks for commands every 2 seconds

### Error Handling
- **Command Manager**: In-memory command queuing system prevents command loss
- **Retry Logic**: ESP8266 includes timeout and retry mechanisms for failed uploads
- **Data Validation**: Server-side validation of all incoming sensor data

### Frontend Architecture
- **Manual Refresh**: Intentional design choice to avoid overwhelming the system with automatic polling
- **Progressive Enhancement**: Core functionality works without JavaScript, enhanced with Chart.js for visualization

## Troubleshooting

### Common Issues

1. **Database Not Creating**
   - Ensure write permissions in deployment directory
   - Check that SQLite is properly installed

2. **ESP8266 Connection Issues**
   - Verify WiFi credentials and signal strength
   - Check server URL configuration
   - Monitor serial output for error messages

3. **Data Not Appearing**
   - Check ESP8266 serial monitor for upload success/failure
   - Verify HTTPS certificate handling (setInsecure() used)
   - Check server logs for incoming requests

4. **Commands Not Executing**
   - Ensure ESP8266 is actively polling for commands
   - Check command format (must be one of: Dataup_, Watering_, ServoTurnTo_)
   - Verify Arduino Nano is properly connected and responsive

### Debug Commands
```bash
# Test API endpoint
curl https://your-domain.zeabur.app/api

# Test command submission
curl -X POST https://your-domain.zeabur.app/sensor-command \
  -H "Content-Type: application/json" \
  -d '{"command":"Dataup_0"}'

# Check pending commands
curl https://your-domain.zeabur.app/get-pending-command
```

## Security Considerations

- **HTTPS Only**: All server communication uses HTTPS
- **Input Validation**: All sensor data and commands are validated on the server
- **No Admin Authentication**: Current system lacks admin authentication (consider adding for production)
- **Certificate Verification**: ESP8266 uses insecure HTTPS (consider adding certificate validation for production)

## Performance Notes

- **Database Indexes**: Comprehensive indexing on time-based fields for fast queries
- **Pagination**: Large datasets support efficient pagination
- **Data Retention**: Consider implementing automatic data cleanup for long-running deployments
- **Rate Limiting**: No rate limiting implemented (consider adding for production)

This system provides a complete end-to-end solution for environmental monitoring and hardware control with real-time web interface and cloud deployment capabilities.