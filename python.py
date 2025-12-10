from flask import Flask, render_template, jsonify
import subprocess
import platform
import math
import os

app = Flask(__name__)

# ---------------- DISTANCE ----------------
def signal_to_distance(signal):
    try:
        signal = int(signal)
        rssi = (signal / 2) - 100
        tx_power = -40
        n = 2.7
        return round(pow(10, (tx_power - rssi) / (10 * n)), 2)
    except:
        return None


# ---------------- WIFI SCAN ----------------
def scan_wifi():
    system = platform.system()
    networks = []

    # ===== WINDOWS =====
    if system == "Windows":
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            shell=True
        )

        ssid = security = bssid = None

        for line in result.stdout.splitlines():
            line = line.strip()

            if line.startswith("SSID ") and ":" in line:
                ssid = line.split(":", 1)[1].strip()

            elif line.startswith("Authentication"):
                security = line.split(":", 1)[1].strip()

            elif line.startswith("BSSID"):
                bssid = line.split(":", 1)[1].strip()

            elif line.startswith("Signal"):
                signal = line.split(":", 1)[1].replace("%", "").strip()
                networks.append({
                    "ssid": ssid,
                    "bssid": bssid,
                    "signal": signal,
                    "security": security or "Unknown",
                    "distance": signal_to_distance(signal)
                })

    # ===== LINUX =====
    elif system == "Linux":
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,SECURITY", "device", "wifi", "list"],
            capture_output=True,
            text=True
        )

        for line in result.stdout.splitlines():
            if line:
                ssid, bssid, signal, security = line.split(":")
                networks.append({
                    "ssid": ssid or "<hidden>",
                    "bssid": bssid,
                    "signal": signal,
                    "security": security or "Unknown",
                    "distance": signal_to_distance(signal)
                })

    # ===== MACOS =====
    elif system == "Darwin":
        airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        result = subprocess.run([airport, "-s"], capture_output=True, text=True)

        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4:
                rssi = int(parts[2])
                signal = min(100, max(0, 2 * (rssi + 100)))
                networks.append({
                    "ssid": parts[0],
                    "bssid": parts[1],
                    "signal": signal,
                    "security": parts[-1],
                    "distance": signal_to_distance(signal)
                })

    return networks


# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scan")
def scan():
    return jsonify(scan_wifi())


@app.route("/wifi")
def wifi_details():
    return render_template("wifi.html")


@app.route("/ping")
def ping():
    return "OK"


# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
