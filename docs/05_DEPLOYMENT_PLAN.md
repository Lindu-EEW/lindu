
<!-- START OF 10_DEPLOYMENT.md -->
# 🚀 Deployment Guide — Lindu.id

## Key Features & Architecture

- **React Dashboard:** Now features a "Geoshake-style" UI (Animated epicenters, PGA-based color-coded nodes, Helicorder 24h mockup, RMS & PGA metrics, Node Detail Modals).
- **Consensus Engine:** The Consensus algorithm in Python strictly prevents false positives and groups multiple nodes using Haversine P-Wave velocity limits.
- **Database:** Fully utilizes PostgreSQL (Dockerized) for reliable and scalable data storage.
- **Hardware Node:** Built using the ESP32 microcontroller paired with the LSM6DS3 accelerometer.

## Server Setup (VPS Ubuntu 22.04)

### 1. Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo apt install docker-compose-plugin -y

# Install Certbot (TLS certificates)
sudo apt install certbot -y

# Install Nginx
sudo apt install nginx -y

# Install UFW Firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8883/tcp  # MQTT TLS
sudo ufw enable

# Clone repository
git clone https://github.com/yourusername/lindu.id.git
cd lindu.id/server
```

### 2. TLS Certificate Setup

```bash
# Generate Let's Encrypt certificate
sudo certbot certonly --standalone \
  -d lindu.id \
  -d www.lindu.id \
  -d mqtt.lindu.id \
  -d api.lindu.id \
  --email admin@lindu.id \
  --agree-tos

# Auto-renew (cronjob)
echo "0 0 * * * certbot renew --quiet && nginx -s reload" | sudo crontab -
```

### 3. Docker Compose Configuration

```yaml
# server/docker-compose.yml
version: '3.8'

services:
  # ─────────────────────────────────────
  # MQTT Broker
  # ─────────────────────────────────────
  mosquitto:
    image: eclipse-mosquitto:2.0
    container_name: lindu-mosquitto
    volumes:
      - ./mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
      - ./mosquitto/passwd:/mosquitto/config/passwd:ro
      - ./mosquitto/acl.conf:/mosquitto/config/acl.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - mosquitto_data:/mosquitto/data
      - mosquitto_logs:/mosquitto/log
    ports:
      - "8883:8883"   # MQTT TLS (external)
    networks:
      - external
      - internal
    restart: unless-stopped

  # ─────────────────────────────────────
  # Database (PostgreSQL)
  # ─────────────────────────────────────
  postgresql:
    image: postgres:16
    container_name: lindu-db
    environment:
      POSTGRES_DB: lindu
      POSTGRES_USER: lindu_app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - internal
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lindu_app"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─────────────────────────────────────
  # Consensus Engine
  # ─────────────────────────────────────
  consensus:
    build: ./consensus
    container_name: lindu-consensus
    env_file: .env
    environment:
      MQTT_HOST: mosquitto
      MQTT_PORT: 1883  # Internal port (no TLS)
      DB_HOST: postgresql
    depends_on:
      - mosquitto
      - postgresql
    networks:
      - internal
    restart: unless-stopped

  # ─────────────────────────────────────
  # Dashboard API
  # ─────────────────────────────────────
  api:
    build: ./api
    container_name: lindu-api
    env_file: .env
    environment:
      MQTT_HOST: mosquitto
      MQTT_PORT: 1883
      DB_HOST: postgresql
    depends_on:
      - postgresql
      - mosquitto
    networks:
      - internal
      - external
    restart: unless-stopped

  # ─────────────────────────────────────
  # Dashboard Frontend
  # ─────────────────────────────────────
  dashboard:
    build: ./dashboard
    container_name: lindu-dashboard
    environment:
      NEXT_PUBLIC_API_URL: https://api.lindu.id
      NEXT_PUBLIC_WS_URL: wss://api.lindu.id
    networks:
      - internal
    restart: unless-stopped

  # ─────────────────────────────────────
  # Nginx Reverse Proxy
  # ─────────────────────────────────────
  nginx:
    image: nginx:alpine
    container_name: lindu-nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
      - dashboard
    networks:
      - external
      - internal
    restart: unless-stopped

volumes:
  mosquitto_data:
  mosquitto_logs:
  db_data:

networks:
  internal:
    internal: true
  external:
    driver: bridge
```

### 4. Mosquitto Configuration

```conf
# mosquitto/mosquitto.conf

# ── General ──
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_type all

# ── External Listener (TLS) ──
listener 8883
protocol mqtt
cafile /etc/letsencrypt/live/mqtt.lindu.id/chain.pem
certfile /etc/letsencrypt/live/mqtt.lindu.id/fullchain.pem
keyfile /etc/letsencrypt/live/mqtt.lindu.id/privkey.pem
tls_version tlsv1.2
require_certificate false

# ── Internal Listener (no TLS, Docker only) ──
listener 1883
allow_anonymous false

# ── Auth ──
password_file /mosquitto/config/passwd
acl_file /mosquitto/config/acl.conf

# ── Rate Limiting ──
max_queued_messages 100
max_inflight_messages 20
```

```bash
# Generate hashed passwords
mosquitto_passwd -c mosquitto/passwd node1
mosquitto_passwd mosquitto/passwd node2
mosquitto_passwd mosquitto/passwd actuator1
mosquitto_passwd mosquitto/passwd consensus_engine
mosquitto_passwd mosquitto/passwd dashboard_api
```

### 5. Nginx Configuration

```nginx
# nginx/nginx.conf

events { worker_connections 1024; }

http {
    # ── Dashboard ──
    server {
        listen 80;
        server_name lindu.id www.lindu.id;
        return 301 https://$host$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name lindu.id www.lindu.id;
        
        ssl_certificate /etc/letsencrypt/live/lindu.id/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/lindu.id/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        
        add_header Strict-Transport-Security "max-age=31536000" always;
        
        location / {
            proxy_pass http://dashboard:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    
    # ── API ──
    server {
        listen 443 ssl http2;
        server_name api.lindu.id;
        
        ssl_certificate /etc/letsencrypt/live/lindu.id/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/lindu.id/privkey.pem;
        
        location / {
            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";  # WebSocket support
        }
    }
}
```

### 6. Start & Deploy

```bash
# Copy environment file
cp .env.example .env
nano .env  # Edit with actual values

# Build and start all services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f consensus

# Restart a single service
docker compose restart mosquitto
```

---

## ESP32 Firmware Deployment (Flashing Guide)

Because you are using the **ESP32 (with LSM6DS3)** and **PlatformIO**, the process of transferring code from your computer to the hardware (called *Flashing*) is very straightforward.

### 1. First Time Flashing (Via USB Cable)

When your physical device arrives fresh from the factory, it is still empty. You must upload the *firmware* for the first time via a USB Type-C cable.

1. **Connect the Cable:** Connect the ESP32 to your Mac using a USB Type-C cable (ensure the cable supports data transfer, not just a charging cable).
2. **Open PlatformIO:** Open the `src/esp32_node_mvp` project in your VS Code (with the PlatformIO extension installed).
3. **Select Upload:** In the bottom bar of VS Code (blue color), click the **Right Arrow (→)** icon or the word **Upload**.
   - *Terminal Alternative:* Type `pio run -t upload` in your VS Code terminal.
4. **Done!** PlatformIO will automatically detect the USB port on your Mac, upload the 16MB OTA Partition, and flash `firmware.bin`.

### 2. Troubleshooting: Failed to Enter Upload Mode (Bootloader)

Sometimes, the *auto-reset* circuit on the ESP32 board fails to execute, resulting in the message `Connecting... Fatal Error: Failed to connect to ESP32`. If this happens, you must manually force it into *Bootloader* (Download Mode):

1. Press and HOLD the **BOOT** (or **B**) button on the ESP32 board.
2. While holding the BOOT button, press and RELEASE the **RST** (or **EN**) button.
3. Release the **BOOT** button.
4. Repeat the Upload process in PlatformIO. Once successfully uploaded 100%, press the **RST** button once so the device starts working (running).

### 3. Subsequent Flashing (Via OTA / Wireless)

Since we have installed the **ArduinoOTA** feature and the A/B Rollback partition table, you no longer need to climb the roof to plug in a USB cable in the future. You can flash via your home WiFi connection.

1. When the ESP32 turns on, it will register itself to the WiFi network.
2. In PlatformIO (on your Mac), ensure you are connected to the same WiFi network as the ESP32.
3. Edit your `platformio.ini` file, adding these two lines at the bottom:
   ```ini
   upload_protocol = espota
   upload_port = 192.168.1.xxx ; (Replace with your ESP32's IP Address)
   ```
4. Click **Upload** in PlatformIO. The new code will be transmitted over the air (WiFi) into the `app1` Partition, and the ESP32 will automatically *restart* with the new C++ code!

---

## Monitoring & Maintenance

### Health Check Script

```bash
#!/bin/bash
# scripts/health_check.sh

echo "=== Lindu.id Health Check ==="

# Check containers
echo "--- Docker Services ---"
docker compose ps

# Check MQTT broker
echo "--- MQTT Broker Test ---"
mosquitto_sub -h mqtt.lindu.id -p 8883 --cafile ca.crt \
  -u dashboard_api -P $DASHBOARD_PASS \
  -t "lindu/sensor/+/status" -C 2 -W 5 && echo "MQTT OK" || echo "MQTT FAIL"

# Check API
echo "--- API Health ---"
curl -s https://api.lindu.id/api/status | jq .

# Check database
echo "--- Database ---"
docker exec lindu-db pg_isready -U lindu_app && echo "DB OK"
```

### Backup Script

```bash
#!/bin/bash
# scripts/backup.sh — Run via cron every day at 2 AM

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/lindu"

# Database backup
docker exec lindu-db pg_dump -U lindu_app lindu | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Mosquitto data backup
tar czf "$BACKUP_DIR/mosquitto_$DATE.tar.gz" mosquitto/data/

# Keep only last 7 days
find "$BACKUP_DIR" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Add to crontab
0 2 * * * /opt/lindu.id/scripts/backup.sh >> /var/log/lindu_backup.log 2>&1
```


---

<!-- START OF 08_SECURITY.md -->
# 🔒 Security Plan — Lindu.id

## Threat Model

| Threat | Risk | Mitigation |
|---------|------|----------|
| Man-in-the-middle (MQTT) | CRITICAL | TLS 1.2/1.3 on all MQTT connections |
| False alert injection | CRITICAL | Mutual TLS authentication + ACL |
| Node spoofing | HIGH | Unique device certificate per node |
| Dashboard unauthorized access | MEDIUM | JWT + session management |
| Server compromise | HIGH | Firewall, least privilege, Docker isolation |
| Firmware tampering | MEDIUM | Secure Boot + Flash Encryption (ESP32) |
| Replay attack | MEDIUM | Message timestamp + sequence number validation |
| Denial of Service (MQTT flood) | MEDIUM | Rate limiting per client ID |

---

## MQTT Security

### TLS Certificate Architecture

```
Certificate Authority (Lindu.id CA)
        │
        ├── Server Certificate (mqtt.lindu.id)
        │       → Signed by Let's Encrypt (public CA)
        │       → Renewable every 90 days (auto-certbot)
        │
        ├── Node1 Client Certificate (optional — Phase 2)
        ├── Node2 Client Certificate (optional — Phase 2)
        └── Actuator Client Certificate (optional — Phase 2)
```

### Phase 1: Username/Password + Server TLS

```cpp
// ESP32 with LSM6DS3 — embed CA cert for server verification
const char* CA_CERT = R"(
-----BEGIN CERTIFICATE-----
MIIEkjCCA3qgAwIBAgIQCgFBQgAAAVOFc2oLheynCDANBgkqhkiG9w0BAQsFADA/
...
-----END CERTIFICATE-----
)";

// Setup MQTT client with TLS
WiFiClientSecure secureClient;
secureClient.setCACert(CA_CERT);  // Verify server certificate
// secureClient.setCertificate(CLIENT_CERT);   // Phase 2: mutual TLS
// secureClient.setPrivateKey(CLIENT_KEY);     // Phase 2: mutual TLS

PubSubClient mqttClient(secureClient);
mqttClient.setServer("mqtt.lindu.id", 8883);
```

### Mosquitto ACL Configuration

```conf
# /etc/mosquitto/acl.conf

# Sensor Node 1 (ESP32 with LSM6DS3)
user node1
topic write lindu/sensor/node1/#
topic read lindu/alert/#
topic read lindu/cmd/node1/#
topic read lindu/system/#

# Sensor Node 2 (ESP32 with LSM6DS3)
user node2
topic write lindu/sensor/node2/#
topic read lindu/alert/#
topic read lindu/cmd/node2/#
topic read lindu/system/#

# Actuator Node 1
user actuator1
topic read lindu/alert/#
topic read lindu/cmd/actuator1/#
topic write lindu/actuator/actuator1/#

# Consensus Engine (Internal Python service: strictly prevents false positives and groups multiple nodes using Haversine P-Wave velocity limits)
user consensus_engine
topic readwrite lindu/#

# Dashboard API (Read-only for monitoring. React Dashboard: Geoshake-style UI, Animated epicenters, PGA-based color-coded nodes, Helicorder 24h mockup, RMS & PGA metrics, Node Detail Modals)
user dashboard_api
topic read lindu/#

# Rate limiting (Mosquitto 2.x)
# max_queued_messages 100 per client
```

---

## ESP32 Firmware Security

### Credentials Storage (NVS Encrypted)

```cpp
// DO NOT store credentials as plain text in the code!
// Use NVS (Non-Volatile Storage) with encryption

#include <Preferences.h>

class SecureCredentials {
    Preferences prefs;
    
public:
    void init() {
        // Open NVS namespace (read-only in production)
        prefs.begin("lindu-creds", true);  // true = read-only
    }
    
    String getMqttPassword() {
        return prefs.getString("mqtt_pass", "");
    }
    
    // Credentials provisioned during manufacturing/setup
    // Cannot be read back after provisioning
};
```

### Anti-Hijacking Cloud OTA (Defense Without Secure Boot)

**Threat Model:** A hacker intercepts an MQTT command and instructs the device to download *malware* via OTA to turn the device into a *Botnet*.

**Defense Solution (Firmware Level):**
Considering the *Hardware Secure Boot* feature has a high risk (permanently blowing silicon eFuses which can potentially ruin the device during the prototype phase), the Lindu.id MVP system uses a **Hardcoding Trust** & **SSL Validation** strategy as an absolute defense that is safe for *developers*.

#### Layer 1: Hardcoded Base URL (URL Spoofing Prevention)
The ESP32 **never** receives a full URL from MQTT. The server only sends a version parameter (example: `v1.2.0`). The ESP32 will construct the URL internally in C++ memory:
```cpp
// Hacker sends: {"cmd": "UPDATE_FIRMWARE", "version": "malware"}
String version = doc["version"]; 

// ESP32 locks the domain using hardcoding
String url = "https://api.lindu.id/firmware/lindu_esp32_" + version + ".bin";
// Resulting URL: https://api.lindu.id/firmware/lindu_esp32_malware.bin (Will be Rejected by Server/404)
```
With this strategy, it is impossible for a *hacker* to force the ESP32 to download a virus from an external server (*hacker's domain*).

#### Layer 2: HTTPS & Root CA Validation (Network Layer)
To prevent *DNS Spoofing* (a hacker directing `api.lindu.id` traffic to a fake server via a hacked WiFi *router*), the ESP32 in the production stage will validate the Let's Encrypt *Root CA* Certificate.
```cpp
WiFiClientSecure otaClient;
otaClient.setCACert(isrg_root_x1); // ESP32 rejects fake servers
t_httpUpdate_return ret = httpUpdate.update(otaClient, url);
```

#### [WARNING] About Hardware Secure Boot V2
> [!CAUTION]
> **eFuse DANGER (Irreversible):** ESP32-S3 has a *Secure Boot V2* feature. However, enabling this feature will shoot high voltage internally to **melt (blow)** the eFuse memory silicon circuits.
> Once *Secure Boot* is active, the Public Key is locked permanently. If you lose the *Private Key* file on your computer, the ESP32 will become a **Brick** forever.
> **Conclusion:** The *Secure Boot* feature MUST ONLY be enabled at the final assembly factory for commercial products. It is **STRICTLY PROHIBITED** to turn it on during the prototyping or Thesis writing phase.

```text
# [For Final Mass Production Only] Enabled via ESP-IDF menuconfig:
Security features
  ├── Enable hardware Secure Boot in bootloader (V2)
  └── Enable flash encryption on boot (AES-XTS)
```

### Anti-Replay Protection

```cpp
struct MqttMessage {
    String node_id;
    uint64_t timestamp_ms;   // Unix timestamp in ms
    uint32_t seq_number;     // Monotonic sequence counter
    String payload;
    String hmac;             // HMAC-SHA256 (Phase 2)
};

// Server-side validation
bool isValidMessage(MqttMessage& msg, uint64_t last_ts, uint32_t last_seq) {
    // Reject if timestamp is too old (> 30 seconds)
    uint64_t now_ms = getCurrentTimeMs();
    if (abs((int64_t)(now_ms - msg.timestamp_ms)) > 30000) {
        return false;  // Replay attack or clock drift
    }
    
    // Reject if sequence number is not monotonically increasing
    if (msg.seq_number <= last_seq) {
        return false;  // Duplicate or replay
    }
    
    return true;
}
```

---

## Server Security

### Firewall Rules (UFW)

```bash
# Default: deny all incoming
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (restricted to admin IP)
ufw allow from YOUR_ADMIN_IP to any port 22

# Allow HTTPS (dashboard + API)
ufw allow 443/tcp

# Allow MQTT TLS (IoT devices)
ufw allow 8883/tcp

# Allow HTTP (redirect to HTTPS only)
ufw allow 80/tcp

# Block internal MQTT port from internet
# Port 1883 is NOT opened to the public (internal Docker only)

ufw enable
```

### Docker Network Isolation

```yaml
# docker-compose.yml
networks:
  internal:          # Isolated internal network
    internal: true   # No internet access for internal services
  external:          # Internet-facing
    driver: bridge

services:
  mosquitto:
    networks:
      - external    # Port 8883 accessible
      - internal    # Port 1883 for internal services
    ports:
      - "8883:8883"
    # Port 1883 NOT exposed to host

  consensus:
    # Python Consensus algorithm strictly prevents false positives and groups multiple nodes using Haversine P-Wave velocity limits
    networks:
      - internal    # Only internal, no direct internet
    
  postgresql:
    # PostgreSQL (Dockerized)
    image: postgres:15-alpine
    networks:
      - internal    # Database: completely isolated
    # No ports exposed to host
```

### Nginx Security Headers

```nginx
server {
    # HTTPS only
    listen 443 ssl http2;
    server_name lindu.id;
    
    # TLS
    ssl_certificate /etc/letsencrypt/live/lindu.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lindu.id/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; ..." always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location /api/ {
        limit_req zone=api burst=20;
        proxy_pass http://dashboard-api:8000;
    }
}
```

### JWT Authentication (Dashboard API)

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.environ["JWT_SECRET"]  # 256-bit random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## Environment Variables & Secrets Management

```bash
# .env (NOT committed to git!)
# Add .env to .gitignore

MQTT_USERNAME_NODE1=node1
MQTT_PASSWORD_NODE1=<strong-random-password>
MQTT_USERNAME_NODE2=node2
MQTT_PASSWORD_NODE2=<strong-random-password>
MQTT_USERNAME_ACTUATOR1=actuator1
MQTT_PASSWORD_ACTUATOR1=<strong-random-password>
MQTT_USERNAME_CONSENSUS=consensus_engine
MQTT_PASSWORD_CONSENSUS=<strong-random-password>

DB_HOST=postgresql
DB_PORT=5432
DB_NAME=lindu
DB_USER=lindu_app
DB_PASSWORD=<strong-random-password>

JWT_SECRET=<256-bit-random-hex>

BMKG_POLL_INTERVAL=60
JMA_POLL_INTERVAL=60
```

---

## Security Checklist

### Before Deployment
- [ ] All credentials in environment variables (no hardcoding)
- [ ] TLS certificate is valid and auto-renew is configured
- [ ] UFW firewall is active and rules are correct
- [ ] Docker networking isolation is correct
- [ ] MQTT node passwords are hashed in the passwd file
- [ ] MQTT ACL is configured
- [ ] .env is in .gitignore
- [ ] JWT secret is a 256-bit random hex

### ESP32 Firmware
- [ ] CA certificate is embedded for server verification
- [ ] Credentials are saved in NVS, not plaintext flash
- [ ] Secure Boot is enabled (production)
- [ ] Flash Encryption is enabled (production)
- [ ] Anti-replay: timestamp + sequence validation

### Runtime Monitoring
- [ ] Log all authentication failures
- [ ] Alert if a node suddenly goes offline (>5 minutes)
- [ ] Alert if too many MQTT messages per second (flood detection)
- [ ] Regular database backups (daily)


---

<!-- START OF 13_PROJECT_PLAN.md -->
# 🚀 Lindu.id — Final Project Plan (Production)

> **Project Goal:** Build an Enterprise-grade earthquake detection system with multi-node consensus and advanced signal analytics to trigger emergency actuators instantaneously.

---

## 1. Hardware Specifications

| Component | Final Specification | Selection Rationale |
| :--- | :--- | :--- |
| **MCU** | ESP32-S3 | Dual-core enables 100Hz signal processing without blocking the TCP/TLS stack. |
| **Vibration Sensor** | LSM6DS3 | A low-cost MEMS sensor transformed into a high-precision seismometer via Zero-Crossing Rate and DC offset calibration. |
| **Actuator (Local)** | **Buzzer (Beep) + LED** | Early visual and audio indicators before relays are engaged. |
| **Power** | Direct USB-C cable | *Always-On* architecture. Relies on P-Wave detection which is significantly faster than power pole destruction by S-Waves. |
| **Actuator (Physical)** | **Relay / Solenoid Door Lock** | Directly cuts off gas flow and opens building emergency doors. |
| **Display** | ❌ None | Focuses on high-speed *Edge Computing* processing, eliminating UI computation (YAGNI). |

---

## 2. Core Software Feature Scope

### A. Edge (ESP32 Sensor Node)
1. **Sensor Polling (Core 1):** Reads accelerometer at 100Hz (Hardware ODR).
2. **Smart DSP (Edge Math):**
   - **Dynamic DC Offset:** Removes earth's gravity bias allowing wall-mounted or flat installations (detects pose and tilt angle).
   - **Zero-Crossing Rate (ZCR):** Calculates vibration frequency to filter out truck/door profiles (human activities >20Hz).
   - **STA/LTA Energy Ratio:** Calculates short-term vs long-term energy ratio for trigger accuracy matching BMKG seismometers.
3. **Connectivity (Core 0):** MQTTS (Port 8883 with Let's Encrypt CA). Streams both PGA and RMS data.
4. **Cloud OTA:** Supports *pull-based* Over-The-Air updates via HTTPS for security patches.

### B. Central Server (Python / MQTT / PostgreSQL)
1. **Enterprise Consensus Engine:** Awaits `trigger` signals from multiple nodes.
2. **Physics Rules (Speed Envelope Validation):** Calculates trigger time differences between nodes relative to Haversine distance. If energy travels > 15 km/second, the system rejects it as a power grid surge.
3. **Global Broadcast:** Fires early warning alerts globally (Actuators).
4. **Database:** Uses a Dockerized PostgreSQL database for scalable data storage.

### C. Web Dashboard (React)
1. **Geoshake-style UI:** Features animated epicenters, PGA-based color-coded nodes, a 24h Helicorder mockup, RMS & PGA metrics, and Node Detail Modals for intuitive analytics.

### D. Edge (ESP32 Actuator Node)
1. Actuator receives earthquake epicenter coordinates from the Server.
2. Actuator calculates its own Haversine distance to the epicenter locally.
3. If distance < danger radius, the actuator engages the Relay (Siren / Emergency Doors).

---

## 3. The "No-Refactor" Data Contract

**MQTT Topics (Data Contract):**
- `lindu/sensor/<node_id>/status` (Heartbeat Online & UPSERT Location/Pose into PostgreSQL)
- `lindu/sensor/<node_id>/event` (Sent upon local vibration detection, streaming both PGA and RMS)
- `lindu/actuator/cmd/all` (ALARM/EEW broadcast from Server to ALL nodes. Edge Computing Haversine Filter)

*(Nodes use their factory MAC Address as `node_id` and send coordinates and 'pose' status on the `/status` topic.)*

**Global ALARM / EEW Broadcast Payload (Server ➔ Node):**
```json
// Broadcasted globally. Danger radius calculation (Edge Computing) is executed at the Node.
{
  "cmd": "ALARM_ON",
  "level": "CRITICAL",
  "epi_lat": -6.90,
  "epi_lon": 106.50,
  "radius_km": 100
}
```

**Event Payload (Node ➔ Server):**
```json
{
  "node_id": "node_01",
  "timestamp_ms": 1718273645000,
  "pga_g": 0.024,
  "rms_g": 0.012,
  "sta_lta": 4.1, 
  "phase": "trigger",
  "bssid": "AA:BB:CC:DD:EE:FF"
}
```

**Status Payload (Node ➔ Server):**
```json
{
  "node_id": "node_01",
  "lat": -6.90,
  "lon": 106.50,
  "pose": "Flat",
  "tilt_angle": 2.5
}
```

---

## 4. Final Execution Plan

1. **Sprint 1 (Sensor C++):** ✅ COMPLETED (DC Offset Calibration, STA/LTA, ZCR, FreeRTOS).
2. **Sprint 2 (Server Python):** ✅ COMPLETED (Speed of Sound Consensus, Haversine Math).
3. **Sprint 3 (Dashboard React):** ✅ COMPLETED (Geoshake-style UI, animated epicenters).
4. **Sprint 4 (Actuator C++):** ⏳ *To Be Done* (Building alarm listener).
5. **Sprint 5 (Captive Portal):** ⏳ *To Be Done* (Initial WiFi & GPS UI setup).
6. **Sprint 6 (Hardware Test):** ⏳ Demo shaking 2 separate tables.


---

<!-- START OF 03_CODE_PLAN.md -->
# 💻 Code Plan & Project Structure — Lindu.id

## Repository Structure

```
lindu.id/
├── README.md
├── docs/                          # Documentation (this folder)
├── firmware/                      # ESP32 Code
│   ├── sensor_node/               # Firmware for Node 1 & 2 (identical)
│   │   ├── platformio.ini
│   │   ├── src/
│   │   │   ├── main.cpp           # Entry point
│   │   │   ├── config.h           # WiFi, MQTT config
│   │   │   ├── sensors/
│   │   │   │   ├── lsm6ds3.cpp    # Accelerometer driver (Gravity vector/pose)
│   │   │   │   └── lsm6ds3.h
│   │   │   ├── mqtt/
│   │   │   │   ├── mqtt_client.cpp # MQTT TLS handler
│   │   │   │   └── mqtt_client.h
│   │   │   ├── detection/
│   │   │   │   ├── seismic.cpp    # Local vibration detection
│   │   │   │   └── seismic.h
│   │   │   ├── alert/
│   │   │   │   ├── alarm.cpp      # LED + Buzzer handler
│   │   │   │   └── alarm.h
│   │   │   └── time/
│   │   │       └── ntp_sync.cpp   # NTP sync
│   │   └── lib/                   # Third-party libraries
│   │
│   └── actuator_node/             # Actuator Firmware
│       ├── platformio.ini
│       └── src/
│           ├── main.cpp
│           ├── config.h
│           ├── mqtt/
│           │   └── mqtt_client.cpp
│           └── actuators/
│               ├── door_lock.cpp  # Solenoid door
│               ├── gas_valve.cpp  # Servo valve
│               └── alarm.cpp      # Buzzer + LED
│
├── server/                        # Server-side code
│   ├── docker-compose.yml         # Orchestration for all services
│   ├── .env.example               # Environment vars template
│   │
│   ├── consensus/                 # App 1: Consensus Engine
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py                # Entry point
│   │   ├── config.py              # Settings (env vars)
│   │   ├── mqtt/
│   │   │   ├── broker.py          # Paho MQTT client
│   │   │   └── topics.py          # Topic constants
│   │   ├── consensus/
│   │   │   ├── engine.py          # Core consensus logic
│   │   │   ├── spatial.py         # Spatial triangulation
│   │   │   └── scoring.py         # Confidence scoring
│   │   ├── detection/
│   │   │   ├── pga.py             # PGA calculator
│   │   │   ├── magnitude.py       # Magnitude estimator
│   │   │   └── fft_analysis.py    # FFT P/S wave analysis
│   │   ├── external/
│   │   │   ├── bmkg.py            # BMKG API client
│   │   │   └── jma.py             # JMA API client
│   │   └── database/
│   │       ├── models.py          # SQLAlchemy models
│   │       └── crud.py            # DB operations (PostgreSQL)
│   │
│   ├── api/                       # App 2: Dashboard API (Python/Flask)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app.py                 # Flask app
│   │   ├── routes/
│   │   │   ├── events.py          # /api/events endpoints
│   │   │   ├── nodes.py           # /api/nodes endpoints
│   │   │   ├── alerts.py          # /api/alerts endpoints
│   │   │   └── websocket.py       # WebSocket handler (Flask-SocketIO)
│   │   ├── auth/
│   │   │   └── jwt.py             # JWT auth
│   │   └── schemas/
│   │       └── models.py          # Validation schemas
│   │
│   ├── dashboard/                 # App 3: React Frontend (Geoshake-style UI)
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── src/
│   │   │   ├── App.jsx            # Entry point
│   │   │   ├── components/
│   │   │   │   ├── Map.jsx            # Animated epicenters map
│   │   │   │   ├── NodeCard.jsx       # PGA-based color-coded nodes
│   │   │   │   ├── Helicorder.jsx     # Helicorder 24h mockup
│   │   │   │   ├── MetricsPanel.jsx   # RMS & PGA metrics
│   │   │   │   └── NodeDetailModal.jsx# Node detail modals
│   │   │   └── utils/
│   │   │       ├── websocket.js       # WS client
│   │   │       └── api.js             # API client
│   │
│   └── mosquitto/                 # MQTT Broker config
│       ├── mosquitto.conf
│       ├── passwd                 # Credentials (hashed)
│       └── certs/                 # TLS certificates
│
└── scripts/                       # Utility scripts
    ├── gen_certs.sh               # Generate TLS certs
    ├── test_mqtt.py               # Test MQTT connection
    └── simulate_sensor.py         # Sensor data simulation
```

---

## Firmware: Sensor Node (C++ / Arduino)

### `main.cpp` — Main Flow

```cpp
// Pseudocode flow
void setup() {
    // 1. Init hardware
    Serial.begin(115200);
    Wire.begin();               // I2C for LSM6DS3
    
    // 2. Init sensor (calculate gravity vector for flat/wall mount)
    lsm6ds3.begin();
    lsm6ds3.setODR(1600_HZ);    // High sample rate
    lsm6ds3.setFullScale(8G);   // ±8g for seismic
    lsm6ds3.calibratePose();    // Determine gravity vector
    
    // 3. Connect WiFi
    WiFi.begin(SSID, PASSWORD);
    
    // 4. Sync NTP
    ntp.sync();
    
    // 5. Connect MQTT (TLS)
    mqttClient.begin(MQTT_HOST, 8883, MQTT_CA_CERT);
    mqttClient.subscribe("lindu/alert/#", QOS_2);
    mqttClient.subscribe("lindu/cmd/node_id", QOS_1);
    
    // 6. Setup interrupt from LSM6DS3
    attachInterrupt(LSM_INT1, onVibrationDetected, RISING);
}

void loop() {
    mqttClient.loop();  // Handle incoming messages
    
    // Publish metrics every 100ms (10 Hz)
    if (millis() - lastPublish > 100) {
        SensorData data = lsm6ds3.read();
        publishMetrics(data);
        lastPublish = millis();
    }
    
    // Seismic pre-detection
    if (vibrationDetected) {
        runLocalDetection();  // Additional processing during vibration
        vibrationDetected = false;
    }
}
```

### MQTT Payload — Sensor Metrics

```json
{
  "node_id": "node1",
  "ts": 1725379200.123,        // Unix timestamp (ms precision)
  "seq": 12345,                // Sequence number
  "accel": {
    "x": 0.012, "y": -0.003, "z": 9.812   // m/s² (includes gravity vector)
  },
  "gyro": {
    "x": 0.001, "y": 0.002, "z": -0.001   // rad/s
  },
  "pga": 0.015,                // Current Peak Ground Acceleration
  "vibration": false,          // Local detection flag
  "rssi": -65,                 // WiFi signal strength
  "battery": 98                // Battery % (if applicable)
}
```

---

## Firmware: Actuator Node (C++ / Arduino)

### Received Alert Payload

```json
{
  "alert_id": "evt_20260904_001",
  "level": "DANGER",           // SAFE / WARNING / DANGER
  "magnitude": 5.2,
  "confidence": 87,            // %
  "source": "consensus",       // "consensus" | "bmkg" | "jma"
  "epicenter": {
    "lat": -6.200, "lon": 106.816
  },
  "distance_km": 12.5,
  "eta_seconds": 8,            // Estimated S-wave arrival time
  "commands": {
    "door_unlock": true,
    "gas_valve_close": true,
    "alarm": true
  }
}
```

---

## Server: Consensus Engine (Python)

### `consensus/engine.py` — Core Logic

```python
class ConsensusEngine:
    def __init__(self):
        self.node_buffer = {}     # {node_id: [SensorReading]}
        self.time_window = 5.0    # seconds for correlation
        self.alert_cooldown = 60  # seconds between alerts
        
    def on_metrics_received(self, node_id: str, data: dict):
        """Called when MQTT message arrives from a sensor"""
        reading = SensorReading(**data)
        self.node_buffer[node_id].append(reading)
        
        # Check if data from all nodes is present within the time window
        if self.has_consensus_window():
            result = self.run_consensus()
            if result.is_earthquake:
                self.publish_alert(result)
    
    def run_consensus(self) -> ConsensusResult:
        """Multi-node consensus algorithm"""
        # 1. Fetch readings within time window
        readings = self.get_synchronized_readings()
        
        # 2. Calculate PGA for each node
        pga_values = [self.calculate_pga(r) for r in readings]
        
        # 3. Voting: how many nodes crossed the threshold?
        above_threshold = sum(1 for p in pga_values if p > PGA_THRESHOLD)
        
        # 4. If majority agrees → earthquake candidate
        if above_threshold >= MIN_NODES_AGREE:
            # 5. Estimate magnitude
            magnitude = self.estimate_magnitude(max(pga_values))
            
            # 6. Validate with external APIs (if available)
            external_validation = self.validate_with_external()
            
            # 7. Calculate confidence score
            confidence = self.calculate_confidence(
                pga_values, above_threshold, external_validation
            )
            
            return ConsensusResult(
                is_earthquake=True,
                magnitude=magnitude,
                confidence=confidence,
                ...
            )
        
        return ConsensusResult(is_earthquake=False)
```

---

## Server: Dashboard API (Flask/Python)

### API Endpoints

```
GET  /api/nodes                    → List all nodes + statuses
GET  /api/nodes/{id}/metrics       → Historical metrics for a node
GET  /api/events                   → List earthquake events
GET  /api/events/{id}              → Detail for a single event
GET  /api/alerts                   → Alert history
GET  /api/status                   → System health

WebSocket /ws/metrics              → Stream real-time metrics
WebSocket /ws/alerts               → Stream real-time alerts

POST /api/auth/login               → Login (returns JWT)
POST /api/auth/logout              → Logout

POST /api/nodes/{id}/command       → Send command to a node (admin only)
```

---

## Server: Dashboard Frontend (React)

### Geoshake-style UI Components

```
/                  → Geoshake Dashboard: Animated epicenters, live map
/components        → PGA-based color-coded node indicators
/helicorder        → Helicorder 24h continuous plot mockup
/metrics           → Real-time RMS & PGA metrics displays
/modal             → Node Detail Modals for drill-down stats
```

---

## Database Schema

### PostgreSQL (Dockerized)

```sql
-- Sensor readings (time-series)
CREATE TABLE sensor_readings (
    time        TIMESTAMPTZ NOT NULL,
    node_id     VARCHAR(50) NOT NULL,
    accel_x     FLOAT8,
    accel_y     FLOAT8,
    accel_z     FLOAT8,
    gyro_x      FLOAT8,
    gyro_y      FLOAT8,
    gyro_z      FLOAT8,
    pga         FLOAT8,
    vibration   BOOLEAN,
    rssi        INT,
    battery     INT
);
-- Setup indexing for time-series queries
CREATE INDEX ON sensor_readings (time DESC);
CREATE INDEX ON sensor_readings (node_id, time DESC);

-- Earthquake events
CREATE TABLE events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detected_at     TIMESTAMPTZ NOT NULL,
    magnitude       FLOAT4,
    confidence      INT,
    source          VARCHAR(20),  -- 'consensus'|'bmkg'|'jma'
    epicenter_lat   FLOAT8,
    epicenter_lon   FLOAT8,
    depth_km        FLOAT4,
    nodes_triggered TEXT[],       -- Array of node IDs
    raw_data        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts log
CREATE TABLE alerts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id    UUID REFERENCES events(id),
    level       VARCHAR(20),     -- 'WARNING'|'DANGER'
    sent_at     TIMESTAMPTZ NOT NULL,
    recipients  TEXT[],          -- node IDs that received
    payload     JSONB,
    ack_by      TEXT[]           -- node IDs that confirmed
);

-- Node status
CREATE TABLE nodes (
    id              VARCHAR(50) PRIMARY KEY,
    name            VARCHAR(100),
    location_name   VARCHAR(200),
    lat             FLOAT8,
    lon             FLOAT8,
    last_seen       TIMESTAMPTZ,
    firmware_ver    VARCHAR(20),
    status          VARCHAR(20)  -- 'online'|'offline'|'error'
);
```


---

<!-- START OF 11_ROADMAP.md -->
# 🗺️ Roadmap & Milestone — Lindu.id

## Phase 1: Core System (Proof of Concept & Edge Math)
> **Objective:** System runs *end-to-end* — sensors read precisely, server validates physics, actuators execute commands.

### 1. Hardware & Firmware Sensor (C++)
- [x] Setup PlatformIO & Library Dependencies
- [x] Install ESP32 + LSM6DS3 (I2C Wiring)
- [x] Test reading accelerometer data (X, Y, Z) at 100Hz (FreeRTOS)
- [x] **[Advanced]** Implement Dynamic DC Offset (Gravity Tilt Calibration)
- [x] **[Advanced]** Implement Zero-Crossing Rate (ZCR) to reject Truck signals (>20Hz)
- [x] Implement STA/LTA (Short/Long Term Average) for vibration energy
- [x] Wi-Fi + MQTT connection to broker (`NetworkManager.cpp`)
- [x] Publish trigger data (PGA, STA/LTA) to MQTT topic

### 2. Consensus Central Server (Python)
- [x] Setup Python MQTT Client architecture
- [x] Subscribe to sensor topics (`/status` and `/event`)
- [x] Implement Memory Node Registry system (Save coordinates upon *heartbeat*)
- [x] Implement *Buffer Time-Window* (10 seconds *trigger* container)
- [x] **[Advanced]** Strictly prevents false positives and groups multiple nodes using Haversine P-Wave velocity limits
- [x] Publish `ALARM_ON` command to global topic if consensus is reached
- [x] Dockerize Server (Dockerfile & docker-compose.yml)

### 3. Actuator Hardware & Firmware (C++)
- [x] Setup independent PlatformIO project for Actuator Node
- [x] Wi-Fi Connection & Subscribe to global alarm MQTT topic
- [x] **[Advanced]** Implement Edge Computing: Actuator calculates its own distance to the epicenter
- [x] Logic to trigger Relay/Siren if entering the danger zone
- [ ] *[Hardware]* Install ESP32 + Siren Relay + Solenoid Valve
- [ ] *[Hardware]* Physical test: Send manual command → actuator responds (open/close valve)

**Milestone 1:** 🎯 **(WE ARE HERE)** The *end-to-end logic* system is fully coded. Ready for physical testing by shaking 2 sensors simultaneously.

---

## Phase 2: Infrastructure & Dashboard (Web & Cloud)
> **Objective:** System visibility, TLS security, and *real-time* monitoring via Web.

### 1. Cloud & Security (VPS Deployment)
- [ ] Setup VPS (Ubuntu 22.04) on DigitalOcean/AWS
- [ ] Purchase/Setup Domain `lindu.id` + DNS configuration
- [ ] Install Let's Encrypt CA certificate
- [ ] Setup public Mosquitto Broker with TLS configuration (Port 8883)
- [ ] Enable Cloud OTA Update (ESP32 *pulls* `.bin` file from HTTPS)

### 2. Database & API (Backend)
- [ ] Setup PostgreSQL (Dockerized)
- [ ] Create table schemas (`nodes`, `events`, `alarms`)
- [x] Modify `consensus.py` to save location/event logs to Database (PostgreSQL)
- [ ] Create simple *FastAPI endpoints* (`/api/nodes`, `/api/events`)

### 3. Web Dashboard (Frontend)
- [ ] React Dashboard: "Geoshake-style" UI (Animated epicenters, PGA-based color-coded nodes, Helicorder 24h mockup, RMS & PGA metrics, Node Detail Modals)
- [ ] Interactive map (Leaflet.js) displaying *Node* locations and Earthquake Epicenter
- [ ] WebSocket: *Real-time* red *banner* notification on *browser* screen if an earthquake occurs

**Milestone 2:** System deployed on the public internet securely and can be monitored by lecturers/examiners from a web browser.

---

## Phase 3: Reliability & UX (Final Polish)
> **Objective:** Make the device easier for the general public to use and more durable.

- [x] **Captive Portal UI:** Local Web page on ESP32 at first boot for *inputting* WiFi SSID & Latitude/Longitude (saved in NVS).
- [ ] BMKG Data polling integration (`autogempa.json`) for post-event correlation.
- [ ] OLED Display on sensor node (WiFi Status, IP Address, local PGA).
- [ ] Manual *override button* on actuator (Emergency button to turn off the siren).

---

## 🕒 Estimated Remaining Work (Main Phases)

| Task | Status | Notes |
|------|--------|-------|
| Sensor Firmware (Math/DSP) | ✅ Completed | Outperforms basic *scripts* thanks to ZCR & DC Offset. |
| Python Server (Consensus) | ✅ Completed | Strictly prevents false positives and groups multiple nodes using Haversine P-Wave velocity limits. |
| Actuator Firmware (Edge Filter) | ✅ Completed | C++ Captive Portal with NVS ready to flash. |
| Cloud VPS & TLS Setup | ⏳ Waiting | Needs VPS / Domain access from the team. |
| Web Dashboard UI | ⏳ Waiting | React Dashboard with "Geoshake-style" UI pending. |


---
