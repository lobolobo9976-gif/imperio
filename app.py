from flask import Flask, request, redirect, render_template, session
import yt_dlp, os, json, time, random, string

app = Flask(__name__)
app.secret_key = "imperio_total"

DB = "db.json"
CHAT_FILE = "chat.json"

# ===== DB =====
def load():
    if not os.path.exists(DB):
        return {"users": {}, "codes": {}, "downloads": 0, "ips": {}}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

# ===== CHAT =====
def load_chat():
    if not os.path.exists(CHAT_FILE):
        return []
    return json.load(open(CHAT_FILE))

def save_chat(data):
    json.dump(data, open(CHAT_FILE, "w"), indent=2)

# ===== LIMITES =====
def limit(plan):
    if plan == "free": return 5
    if plan == "vip": return 50
    if plan == "lifetime": return 999999

def get_ip():
    return request.remote_addr

# ===== LOGIN =====
@app.route("/", methods=["GET","POST"])
def login():
    db = load()
    ip = get_ip()

    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        if ip in db["ips"] and db["ips"][ip] != u:
            return "🚫 Solo 1 cuenta por dispositivo"

        if u in db["users"]:
            if db["users"][u]["pass"] == p:
                session["user"] = u
        else:
            db["users"][u] = {
                "pass": p,
                "plan": "free",
                "exp": 0,
                "ban": False,
                "use": 0,
                "history": [],
                "last": 0,
                "strikes": 0
            }
            db["ips"][ip] = u
            session["user"] = u

        save(db)
        return redirect("/home")

    return render_template("login.html")

# ===== HOME =====
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    db = load()
    u = db["users"][session["user"]]

    if u.get("ban"):
        return "🚫 Baneado"

    if u["plan"] == "vip" and time.time() > u["exp"]:
        u["plan"] = "free"

    save(db)

    return render_template("index.html",
        user=session["user"],
        plan=u["plan"],
        total=db["downloads"],
        limite=limit(u["plan"]),
        uso=u["use"],
        history=u["history"]
    )

# ===== DESCARGA =====
@app.route("/download", methods=["POST"])
def download():
    if "user" not in session:
        return redirect("/")

    url = request.form["url"]
    db = load()
    u = db["users"][session["user"]]

    now = time.time()

    if now - u["last"] < 3:
        u["strikes"] += 1
        save(db)
        return "⚠️ Espera unos segundos"

    if u["use"] >= limit(u["plan"]):
        return "❌ Límite alcanzado"

    if u["strikes"] >= 5:
        u["ban"] = True
        save(db)
        return "🚫 Baneado por abuso"

    ydl_opts = {
        "quiet": True,
        "format": "best",
        "noplaylist": True,
        "extractor_args": {
            "youtube": {"player_client": ["android"]}
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            u["use"] += 1
            u["last"] = now
            db["downloads"] += 1

            if u["strikes"] > 0:
                u["strikes"] -= 1

            u["history"].append({
                "url": url,
                "time": time.strftime("%H:%M:%S")
            })

            save(db)

            if "url" in info:
                return redirect(info["url"])

            for f in reversed(info.get("formats", [])):
                if f.get("url"):
                    return redirect(f["url"])

    except:
        return redirect(f"https://www.y2mate.is/youtube?url={url}")

# ===== VIP =====
@app.route("/activar", methods=["POST"])
def activar():
    db = load()
    code = request.form["code"]
    u = db["users"][session["user"]]

    if code in db["codes"]:
        tipo = db["codes"][code]

        if tipo == "1d": u["exp"] = time.time()+86400
        elif tipo == "30d": u["exp"] = time.time()+86400*30
        elif tipo == "365d": u["exp"] = time.time()+86400*365
        elif tipo == "life": u["plan"] = "lifetime"

        if tipo != "life":
            u["plan"] = "vip"

        del db["codes"][code]
        save(db)

    return redirect("/home")

# ===== ADMIN =====
@app.route("/admin")
def admin():
    if session.get("user") != "demon":
        return "No admin"

    db = load()

    html = f"<h1>ADMIN 💀</h1>Total: {db['downloads']}<br><br>"

    for u in db["users"]:
        user = db["users"][u]
        html += f"{u} | {user['plan']} | uso:{user['use']} <a href='/ban/{u}'>BAN</a><br>"

    html += """
    <form action="/gen" method="post">
    <select name="tipo">
    <option value="1d">1 día</option>
    <option value="30d">1 mes</option>
    <option value="365d">1 año</option>
    <option value="life">∞</option>
    </select>
    <button>Generar código</button>
    </form>
    """

    return html

@app.route("/ban/<user>")
def ban(user):
    db = load()
    db["users"][user]["ban"] = True
    save(db)
    return redirect("/admin")

@app.route("/gen", methods=["POST"])
def gen():
    db = load()
    tipo = request.form["tipo"]

    code = ''.join(random.choices(string.ascii_uppercase+string.digits, k=10))
    db["codes"][code] = tipo

    save(db)
    return f"CODIGO: {code}"

# ===== CHAT =====
@app.route("/chat", methods=["GET","POST"])
def chat():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        msg = request.form["msg"]
        data = load_chat()

        data.append({
            "user": session["user"],
            "msg": msg,
            "time": time.strftime("%H:%M")
        })

        save_chat(data)

    return render_template("chat.html", msgs=load_chat())

@app.route("/chat_data")
def chat_data():
    return load_chat()

# ===== LOGOUT =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
