from flask import Flask, render_template, request, jsonify
import json, os, datetime
from cryptography.fernet import Fernet
import qrcode

app = Flask(__name__)

# Encryption Key
if not os.path.exists("key.key"):
    key = Fernet.generate_key()
    open("key.key", "wb").write(key)
else:
    key = open("key.key", "rb").read()

cipher = Fernet(key)

DB_FILE = "database.json"

# Initialize DB
if not os.path.exists(DB_FILE):
    open(DB_FILE, "w").write("[]")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        batch = request.form.get('batch')
        expiry = request.form.get('expiry')
        salt = request.form.get('salt')

        if not all([name, batch, expiry, salt]):
            return "All fields required"

        payload = f"{name}|{batch}|{expiry}|{salt}"
        encrypted = cipher.encrypt(payload.encode()).decode()

        db = json.load(open(DB_FILE))

        # 🔥 Prevent duplicate registration
        if any(item['data'] == encrypted for item in db):
            return "Medicine already registered!"

        db.append({
            "data": encrypted,
            "scanned": False   # 👈 NEW FIELD
        })

        json.dump(db, open(DB_FILE, "w"), indent=4)

        os.makedirs("static/qrs", exist_ok=True)
        path = f"static/qrs/{batch}.png"
        qrcode.make(encrypted).save(path)

        return render_template('qr.html', qr=path)

    return render_template('register.html')


@app.route('/verify', methods=['POST'])
def verify():
    encrypted = request.json.get('data')

    db = json.load(open(DB_FILE))

    found_item = None
    for item in db:
        if item['data'] == encrypted:
            found_item = item
            break

    try:
        decrypted = cipher.decrypt(encrypted.encode()).decode()
        name, batch, expiry, salt = decrypted.split('|')

        current_year = datetime.datetime.now().year

        # 🔥 LOGIC
        if not found_item:
            status = "COUNTERFEIT"

        elif int(expiry) < current_year:
            status = "EXPIRED"

        elif found_item["scanned"]:
            status = "DUPLICATE"

        else:
            status = "GENUINE"
            found_item["scanned"] = True

        # Save DB update
        json.dump(db, open(DB_FILE, "w"), indent=4)

        return jsonify({
            "status": status,
            "name": name,
            "expiry": expiry,
            "salt": salt
        })

    except:
        return jsonify({"status": "INVALID"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)