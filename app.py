from flask import Flask, request, redirect, render_template, session, send_file
import os, json, time, random, string
import yt_dlp

app = Flask(__name__)
app.secret_key = "imperio_ultra"

DB = "db.json"
CODES = "codes.json"
DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def load():
    if not os.path.exists(DB):
        return {"users": {}}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def load_codes():
    if not os.path.exists(CODES):
        return {}
    return json.load(open(CODES))

def save_codes(data):
    json.dump(data, open(CODES, "w"), indent=2)

def now():
    return int(time.time())

def xp_needed(level):
    return int(40 + (level-1)*15)

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase+string.digits, k=10))

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    db = load()

    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        if u not in db["users"]:
            db["users"][u] = {
                "pass":p,
                "coins":5,
                "xp":0,
                "level":1,
                "use":0,
                "last":0,
                "vip":0,
                "banned":False
            }

        if db["users"][u]["pass"] == p:
            session["user"] = u
            save(db)
            return redirect("/home")

    return render_template("login.html")

# HOME
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    db = load()
    u = db["users"][session["user"]]

    vip_rest = max(0, u["vip"] - now())

    return render_template("index.html",
        user=session["user"],
        coins=u["coins"],
        xp=u["xp"],
        level=u["level"],
        need=xp_needed(u["level"]),
        vip=vip_rest
    )

# DESCARGA REAL
@app.route("/download", methods=["POST"])
def download():
    db = load()
    u = db["users"][session["user"]]

    if u["banned"]:
        return "🚫 Baneado"

    url = request.form.get("url")

    if not url:
        return "Pon URL"

    if u["vip"] < now():
        if now() - u["last"] < 10:
            return "⏳ Espera 10s"

    u["last"] = now()
    u["use"] += 1
    u["xp"] += 15

    if u["level"] < 300 and u["xp"] >= xp_needed(u["level"]):
        u["xp"] = 0
        u["level"] += 1
        u["coins"] += 2

    save(db)

    filename = f"{int(time.time())}.mp4"
    path = os.path.join(DOWNLOAD_FOLDER, filename)

    ydl_opts = {
        'outtmpl': path,
        'format': 'mp4',
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except:
        return "❌ Error descarga"

    return send_file(path, as_attachment=True)

# 🎰 CASINO
@app.route("/spin")
def spin():
    db = load()
    u = db["users"][session["user"]]

    if u["coins"] < 5:
        return "❌ No coins"

    u["coins"] -= 5

    r = random.choice([0,2,5,10,20])

    if r == 0:
        msg = "💀 Perdiste"
    else:
        u["coins"] += r
        msg = f"🔥 Ganaste {r}"

    save(db)

    return f"{msg}<br><a href='/home'>Volver</a>"

# 💎 COMPRAR VIP
PRICES = {
    "vip_dia": 50,
    "vip_mes": 500,
    "vip_inf": 2000
}

@app.route("/buy/<tipo>")
def buy(tipo):
    db = load()
    u = db["users"][session["user"]]

    if tipo not in PRICES:
        return "Error"

    if u["coins"] < PRICES[tipo]:
        return "❌ No coins"

    u["coins"] -= PRICES[tipo]

    if tipo == "vip_dia":
        u["vip"] = now() + 86400
    elif tipo == "vip_mes":
        u["vip"] = now() + 2592000
    elif tipo == "vip_inf":
        u["vip"] = 9999999999

    save(db)

    return "💎 VIP ACTIVADO<br><a href='/home'>Volver</a>"

# 🎟️ GENERAR CÓDIGOS
@app.route("/admin_codes", methods=["GET","POST"])
def admin_codes():
    if session.get("user") != "demon":
        return "🚫 No admin"

    codes = load_codes()

    if request.method == "POST":
        t = int(request.form["time"])
        unit = request.form["unit"]

        if unit == "seg":
            sec = t
        elif unit == "min":
            sec = t*60
        elif unit == "dia":
            sec = t*86400
        elif unit == "mes":
            sec = t*2592000
        elif unit == "inf":
            sec = 9999999999

        code = gen_code()

        codes[code] = {"time":sec,"used":False}
        save_codes(codes)

        return f"🔥 Código: {code}<br><a href='/admin_codes'>Volver</a>"

    return """
    <h2>GENERAR CÓDIGO</h2>
    <form method="post">
    Tiempo: <input name="time"><br>
    <select name="unit">
    <option value="seg">Segundos</option>
    <option value="min">Minutos</option>
    <option value="dia">Días</option>
    <option value="mes">Mes</option>
    <option value="inf">Infinito</option>
    </select><br>
    <button>Generar</button>
    </form>
    """

# CANJEAR
@app.route("/redeem", methods=["POST"])
def redeem():
    codes = load_codes()
    db = load()

    code = request.form["code"]

    if code not in codes or codes[code]["used"]:
        return "❌ Código inválido"

    db["users"][session["user"]]["vip"] = now() + codes[code]["time"]
    codes[code]["used"] = True

    save(db)
    save_codes(codes)

    return "🔥 VIP ACTIVADO<br><a href='/home'>Volver</a>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
