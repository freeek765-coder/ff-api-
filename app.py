from flask import Flask, request, jsonify, render_template_string
import requests
import time
import base64
import json
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import random
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import data_pb2
import my_pb2
import output_pb2

app = Flask(__name__)
app.json.sort_keys = False

SECRET_KEY = b'Yg&tc%DEuh6%Zc^8'
SECRET_IV = b'6oyZDr22E3ychjM%'

TARGET_URLS = [
    "https://loginbp.ggpolarbear.com/MajorModifyNickname",
    "https://loginbp.ggblueshark.com/MajorModifyNickname",
    "https://loginbp.ggpanda.com/MajorModifyNickname",
    "https://loginbp.ggtiger.com/MajorModifyNickname"
]

MAJOR_LOGIN_URLS = [
    "https://loginbp.ggpolarbear.com/MajorLogin",
    "https://loginbp.ggblueshark.com/MajorLogin",
    "https://loginbp.ggpanda.com/MajorLogin"
]

GAME_VERSION = "OB54"
UNITY_VERSION = "2018.4.11f1"
DEVELOPERS = "@Prime_x_Samiul"

USER_AGENTS = [
    "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
    "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B Build/SP1A.210812.016)",
    "Dalvik/2.1.0 (Linux; U; Android 10; Redmi Note 8 Build/QKQ1.190825.002)"
]

def encrypt_message(plaintext):
    try:
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, SECRET_IV)
        return cipher.encrypt(pad(plaintext, AES.block_size))
    except:
        return b""

def decode_ff_name(b64_str):
    try:
        key = b"1e5898ccb8dfdd921f9bdea848768b64a201"
        b64_str = b64_str.strip()
        b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
        encrypted_bytes = base64.b64decode(b64_str)
        decrypted_bytes = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            key_byte = key[i % len(key)]
            decrypted_bytes.append(byte ^ key_byte)
        return decrypted_bytes.decode('utf-8', errors='ignore')
    except:
        return "Unknown"

def extract_jwt_info(jwt_token):
    try:
        payload_b64 = jwt_token.split('.')[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        decoded_token = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        account_id = decoded_token.get("account_id")
        enc_nickname = decoded_token.get("nickname")
        old_name = decode_ff_name(enc_nickname) if enc_nickname else "Unknown"
        region = decoded_token.get("lock_region", "Unknown")
        release_version = decoded_token.get("release_version", "Unknown")
        return account_id, old_name, region, release_version
    except:
        return None, "Unknown", "Unknown", "Unknown"

def guest_login(uid, password):
    login_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    password_formats = []
    for candidate in (
        str(password),
        str(password).lower(),
        str(password).upper(),
        hashlib.sha256(str(password).encode("utf-8")).hexdigest(),
    ):
        if candidate not in password_formats:
            password_formats.append(candidate)
    last_error = "upstream authentication failed"
    for pwd in password_formats:
        payload = {
            "uid": str(uid),
            "password": pwd,
            "response_type": "token",
            "client_type": "2",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_id": "100067",
        }
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        try:
            response = requests.post(login_url, data=payload, headers=headers, timeout=15)
            auth_data = response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = str(exc)
            continue
        if auth_data.get("access_token"):
            return auth_data["access_token"], auth_data.get("open_id")
        last_error = auth_data.get("error") or auth_data.get("message") or f"HTTP {response.status_code}"
    logger.warning("Guest login rejected: %s", last_error)
    return None, None

def perform_majorlogin(access_token, open_id):
    platforms = list(range(0, 21))
    for platform_type in platforms:
        for major_url in MAJOR_LOGIN_URLS:
            try:
                game_data = my_pb2.GameData()
                game_data.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                game_data.game_name = "free fire"
                game_data.game_version = 1
                game_data.version_code = "1.108.3"
                game_data.os_info = "Android OS 10 / API-29"
                game_data.device_type = "Handheld"
                game_data.network_provider = "WiFi"
                game_data.connection_type = "WIFI"
                game_data.screen_width = 720
                game_data.screen_height = 1600
                game_data.dpi = "269"
                game_data.cpu_info = "ARMv8 VFPv3 NEON"
                game_data.total_ram = 2048
                game_data.gpu_name = "PowerVR GE8320"
                game_data.gpu_version = "OpenGL ES 3.2"
                game_data.device_form_factor = "Mobile"
                game_data.device_model = "Redmi 9A"
                game_data.build_number = "QKQ1.190711.020"
                game_data.unknown_field_30 = platform_type
                game_data.field_97 = 0
                game_data.field_98 = 0
                game_data.total_storage = 32000
                game_data.encryption_key = hashlib.md5(f"{access_token}{open_id}".encode()).hexdigest()
                game_data.user_id = f"Google|{random.randint(100000,999999)}"
                game_data.ip_address = f"192.168.{random.randint(1,255)}.{random.randint(1,255)}"
                game_data.language = "en"
                game_data.open_id = open_id
                game_data.access_token = access_token
                game_data.platform_type = platform_type
                game_data.field_99 = str(platform_type)
                game_data.field_100 = str(platform_type)

                encrypted_data = encrypt_message(game_data.SerializeToString())
                if not encrypted_data:
                    continue

                headers = {
                    "User-Agent": random.choice(USER_AGENTS),
                    "Connection": "Keep-Alive",
                    "Accept-Encoding": "gzip",
                    "Content-Type": "application/octet-stream",
                    "X-Unity-Version": UNITY_VERSION,
                    "X-GA": "v1 1",
                    "ReleaseVersion": GAME_VERSION,
                    "Accept": "*/*",
                    "Cache-Control": "no-cache"
                }

                response = requests.post(major_url, data=encrypted_data, headers=headers, verify=False, timeout=10)
                if response.status_code == 200:
                    try:
                        example_msg = output_pb2.Garena_420()
                        example_msg.ParseFromString(response.content)
                        token_value = getattr(example_msg, "token", None)
                        if token_value:
                            logger.info(f"✅ MajorLogin success on {major_url} platform {platform_type}")
                            return token_value
                    except Exception as e:
                        logger.warning(f"Parse error: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Request error: {e}")
                continue
    return None

def change_nickname(jwt_token, new_name):
    account_id, old_name, region, release_version = extract_jwt_info(jwt_token)
    if not new_name or len(new_name) < 3 or len(new_name) > 12:
        return None, "Name must be 3-12 characters"

    try:
        msg = data_pb2.Message()
        msg.data = new_name.encode("utf-8")
        msg.timestamp = int(time.time() * 1000)
        encrypted_data = encrypt_message(msg.SerializeToString())
    except Exception as e:
        encrypted_data = new_name.encode('utf-8')
        logger.warning(f"Fallback to plaintext due to {e}")

    results = []
    for url in TARGET_URLS:
        for attempt in range(3):
            try:
                headers = {
                    "Authorization": f"Bearer {jwt_token}",
                    "X-Unity-Version": UNITY_VERSION,
                    "ReleaseVersion": GAME_VERSION,
                    "Content-Type": "application/octet-stream",
                    "User-Agent": random.choice(USER_AGENTS),
                    "Connection": "Keep-Alive",
                    "Accept-Encoding": "gzip",
                    "Accept": "*/*",
                    "X-GA": "v1 1",
                    "Cache-Control": "no-cache"
                }
                response = requests.post(url, data=encrypted_data, headers=headers, verify=False, timeout=15)
                results.append({
                    "url": url,
                    "status": response.status_code,
                    "body": response.text[:100]
                })
                if response.status_code == 200:
                    return {
                        "success": True,
                        "account_id": account_id,
                        "old_name": old_name,
                        "new_name": new_name,
                        "region": region,
                        "release_version": release_version,
                        "response": response.text[:200]
                    }, None
                elif response.status_code == 503:
                    time.sleep(2 ** attempt)
                    continue
            except Exception as e:
                results.append({"url": url, "error": str(e)})
                continue
        time.sleep(1)

    return None, f"All servers failed. Details: {json.dumps(results, indent=2)}"

# ===================== CHECK ACCOUNT (NEW) =====================
@app.route("/check", methods=["GET"])
def check_account():
    uid = request.args.get("uid")
    password = request.args.get("password")
    if not uid or not password:
        return jsonify({"error": "Missing uid/password"}), 400

    access_token, open_id = guest_login(uid, password)
    if not access_token:
        return jsonify({"valid": False, "message": "❌ Invalid or fake account. Please check UID and password."}), 200

    jwt = perform_majorlogin(access_token, open_id)
    if not jwt:
        return jsonify({"valid": True, "message": "✅ Account exists but unable to fetch full details (JWT failed).", "open_id": open_id, "access_token": access_token[:20] + "..."}), 200

    account_id, old_name, region, release_version = extract_jwt_info(jwt)
    return jsonify({
        "valid": True,
        "account": {
            "uid": uid,
            "open_id": open_id,
            "old_name": old_name,
            "region": region,
            "account_id": account_id,
            "release_version": release_version
        }
    }), 200

# ===================== MAIN UI =====================
@app.route("/", methods=["GET"])
def home():
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>🔥 FF Nickname Changer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1a1a2e, #16213e); color: #fff; font-family: 'Segoe UI', sans-serif; }
        .container { margin-top: 50px; max-width: 600px; }
        .card { background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border: none; border-radius: 20px; padding: 30px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
        .form-control { background: rgba(255,255,255,0.1); border: 1px solid #444; color: #fff; border-radius: 10px; }
        .form-control:focus { background: rgba(255,255,255,0.15); border-color: #ff6b6b; box-shadow: none; }
        .btn-primary { background: #ff6b6b; border: none; border-radius: 50px; padding: 12px 30px; font-weight: bold; transition: 0.3s; }
        .btn-primary:hover { background: #ee5a24; transform: scale(1.02); }
        .btn-outline-light { border-radius: 50px; }
        .result-box { background: rgba(0,0,0,0.3); border-radius: 12px; padding: 15px; margin-top: 20px; white-space: pre-wrap; word-break: break-all; }
        .emoji-big { font-size: 2.5rem; }
        .footer { margin-top: 30px; text-align: center; color: #aaa; }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="text-center">
            <span class="emoji-big">🔥</span>
            <h1 class="display-6">Free Fire Nickname Changer</h1>
            <p class="text-muted">✨ Real Account Check • Auto JWT • Multi‑Server</p>
        </div>
        <hr style="border-color: #444;">
        <form action="/guest" method="get" id="changeForm">
            <div class="mb-3">
                <label class="form-label">🆔 UID</label>
                <input type="text" name="uid" class="form-control" placeholder="Enter your UID" required>
            </div>
            <div class="mb-3">
                <label class="form-label">🔑 Password</label>
                <input type="password" name="password" class="form-control" placeholder="Guest password (or SHA256 hash)" required>
            </div>
            <div class="mb-3">
                <label class="form-label">✏️ New Name</label>
                <input type="text" name="name" class="form-control" placeholder="3-12 characters" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">🚀 Change Name Now</button>
        </form>

        <hr style="border-color: #444;">

        <div class="d-grid gap-2">
            <button class="btn btn-outline-light" onclick="checkAccount()">🔍 Check if Account is Real</button>
        </div>
        <div id="checkResult" class="result-box" style="display:none;"></div>

        <div id="resultBox" class="result-box" style="display:none;"></div>
        <div class="footer">
            <small>Developed with ❤️ by @Prime_x_Samiul • Version 3.0</small>
        </div>
    </div>
</div>

<script>
document.getElementById('changeForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const params = new URLSearchParams(formData).toString();
    const url = '/guest?' + params;
    fetch(url)
        .then(res => res.json())
        .then(data => {
            const box = document.getElementById('resultBox');
            box.style.display = 'block';
            box.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        })
        .catch(err => {
            alert('Error: ' + err);
        });
});

function checkAccount() {
    const uid = document.querySelector('input[name="uid"]').value;
    const password = document.querySelector('input[name="password"]').value;
    if (!uid || !password) {
        alert('Please fill UID and password first!');
        return;
    }
    const url = '/check?uid=' + encodeURIComponent(uid) + '&password=' + encodeURIComponent(password);
    fetch(url)
        .then(res => res.json())
        .then(data => {
            const box = document.getElementById('checkResult');
            box.style.display = 'block';
            if (data.valid) {
                box.innerHTML = '✅ <b>Real Account</b><br>UID: ' + data.account.uid + '<br>Old Name: ' + data.account.old_name + '<br>Region: ' + data.account.region + '<br>OpenID: ' + data.account.open_id;
            } else {
                box.innerHTML = '❌ ' + data.message;
            }
        })
        .catch(err => {
            alert('Error: ' + err);
        });
}
</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    """
    return render_template_string(html)

# ===================== OTHER ROUTES =====================
@app.route("/guest", methods=["GET"])
def process_guest():
    try:
        uid = request.args.get("uid")
        password = request.args.get("password")
        name = request.args.get("name")
        if not all([uid, password, name]):
            return jsonify({"error": "Missing uid, password, name", "example": "/guest?uid=123&password=123&name=Pro"}), 400
        if len(name) < 3 or len(name) > 12:
            return jsonify({"error": "Name must be 3-12 characters"}), 400
        access_token, open_id = guest_login(uid, password)
        if not access_token:
            return jsonify({"error": "Login failed", "message": "Check UID/password"}), 401
        jwt_token = perform_majorlogin(access_token, open_id)
        if not jwt_token:
            return jsonify({"error": "Failed to get JWT", "message": "MajorLogin failed"}), 401
        result, error = change_nickname(jwt_token, name)
        if result:
            return jsonify({
                "success": True,
                "message": "🎉 Name changed!",
                "account": {
                    "uid": uid,
                    "old_name": result["old_name"],
                    "new_name": result["new_name"],
                    "region": result["region"],
                    "account_id": result["account_id"]
                },
                "tokens": {
                    "jwt": jwt_token[:50] + "...",
                    "access_token": access_token[:50] + "..."
                }
            }), 200
        else:
            return jsonify({"error": "Failed to change name", "message": error}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/token", methods=["GET"])
def process_token():
    try:
        jwt = request.args.get("jwt")
        name = request.args.get("name")
        if not jwt or not name:
            return jsonify({"error": "Missing jwt and name", "example": "/token?jwt=JWT&name=Pro"}), 400
        if len(name) < 3 or len(name) > 12:
            return jsonify({"error": "Name must be 3-12 characters"}), 400
        result, error = change_nickname(jwt, name)
        if result:
            return jsonify({"success": True, "account": {"old_name": result["old_name"], "new_name": result["new_name"], "region": result["region"], "account_id": result["account_id"]}}), 200
        else:
            return jsonify({"error": "Failed", "message": error}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/change", methods=["GET"])
def process_change():
    try:
        access_token = request.args.get("access_token")
        name = request.args.get("name")
        if not access_token or not name:
            return jsonify({"error": "Missing access_token and name", "example": "/change?access_token=TOKEN&name=Pro"}), 400
        if len(name) < 3 or len(name) > 12:
            return jsonify({"error": "Name must be 3-12 characters"}), 400
        headers = {"access-token": access_token}
        uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", headers=headers, verify=False, timeout=10)
        uid_data = uid_res.json()
        uid = uid_data.get("uid")
        if not uid:
            return jsonify({"error": "Invalid access token"}), 401
        payload = {"app_id": 100067, "login_id": str(uid)}
        openid_res = requests.post("https://topup.pk/api/auth/player_id_login", json=payload, verify=False, timeout=10)
        open_id = openid_res.json().get("open_id")
        if not open_id:
            return jsonify({"error": "Failed to get OpenID"}), 401
        jwt_token = perform_majorlogin(access_token, open_id)
        if not jwt_token:
            return jsonify({"error": "Failed to generate JWT"}), 401
        result, error = change_nickname(jwt_token, name)
        if result:
            return jsonify({"success": True, "account": {"old_name": result["old_name"], "new_name": result["new_name"], "region": result["region"], "account_id": result["account_id"]}}), 200
        else:
            return jsonify({"error": error}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["GET"])
def process_login():
    try:
        uid = request.args.get("uid")
        password = request.args.get("password")
        if not uid or not password:
            return jsonify({"error": "Missing uid and password", "example": "/login?uid=123&password=123"}), 400
        access_token, open_id = guest_login(uid, password)
        if access_token:
            return jsonify({"success": True, "access_token": access_token, "open_id": open_id, "uid": uid, "next": f"/change?access_token={access_token}&name=ProPlayer"}), 200
        else:
            return jsonify({"error": "Login failed", "message": "Invalid UID/password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/getjwt", methods=["GET"])
def get_jwt():
    uid = request.args.get("uid")
    password = request.args.get("password")
    if not uid or not password:
        return jsonify({"error": "Missing uid/password"}), 400
    access_token, open_id = guest_login(uid, password)
    if not access_token:
        return jsonify({"error": "Guest login failed"}), 401
    jwt = perform_majorlogin(access_token, open_id)
    if jwt:
        return jsonify({"jwt": jwt})
    else:
        return jsonify({"error": "MajorLogin failed"}), 401

@app.route("/debug", methods=["GET"])
def debug_major():
    uid = request.args.get("uid")
    password = request.args.get("password")
    if not uid or not password:
        return jsonify({"error": "Missing uid/password"}), 400
    access_token, open_id = guest_login(uid, password)
    if not access_token:
        return jsonify({"error": "Guest login failed"}), 401
    jwt = perform_majorlogin(access_token, open_id)
    if jwt:
        return jsonify({"status": "success", "jwt_full": jwt, "message": "MajorLogin succeeded"})
    else:
        return jsonify({"error": "MajorLogin failed"}), 401

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"status": "ONLINE", "message": "API working", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "developer": DEVELOPERS})

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not found", "available": ["/", "/guest", "/token", "/change", "/login", "/test", "/debug", "/getjwt", "/check"]}), 404

@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "Internal server error", "try": "/guest with valid credentials"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)