from flask import Flask, request, redirect, render_template, session, jsonify
import os, json, time, random, string

app = Flask(__name__)
app.secret_key = "imperio_dios"

DB = "db.json"
CODES = "codes.json"

def load():
    try:
        return json.load(open(DB))
    except:
        return {"users": {}}

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def load_codes():
    try:
        return json.load(open(CODES))
    except:
        return {}

def save_codes(data):
    json.dump(data, open(CODES, "w"), indent=2)

def now():
    return int(time.time())

def xp_needed(level):
    return 40 + level*20

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
                "coins":10,
                "xp":0,
                "level":1,
                "vip":0
            }

        if db["users"][u]["pass"] == p:
            session["user"] = u
            save(db)
            return redirect("/home")

    return render_template("login.html")

# HOME
@app.route("/home")
def home():
    db = load()
    u = db["users"][session["user"]]

    return render_template("index.html",
        user=session["user"],
        coins=u["coins"],
        xp=u["xp"],
        level=u["level"],
        need=xp_needed(u["level"])
    )

# DESCARGA (SIMULADA FUNCIONAL)
@app.route("/download", methods=["POST"])
def download():
    db = load()
    u = db["users"][session["user"]]

    urls = [request.form.get(f"url{i}") for i in range(1,7)]
    urls = [x for x in urls if x]

    if not urls:
        return "No URL"

    u["coins"] -= 1
    u["xp"] += 10 * len(urls)

    if u["xp"] >= xp_needed(u["level"]):
        u["xp"] = 0
        u["level"] += 1

    save(db)

    return "Descargando OK"

# CASINO
@app.route("/casino")
def casino():
    return render_template("casino.html")

@app.route("/spin")
def spin():
    db = load()
    u = db["users"][session["user"]]

    if u["coins"] < 5:
        return "No coins"

    u["coins"] -= 5
    r = random.choice([0,2,5,10,20])

    u["coins"] += r
    save(db)

    return f"Ganaste {r}"

# COFRE
@app.route("/chest")
def chest():
    db = load()
    u = db["users"][session["user"]]

    if u["coins"] < 10:
        return "No coins"

    u["coins"] -= 10
    premio = random.choice([5,10,20,50])

    u["coins"] += premio
    save(db)

    return redirect("/home")

# MISIONES
@app.route("/missions")
def missions():
    db = load()
    u = db["users"][session["user"]]

    u["coins"] += 2
    u["xp"] += 10

    save(db)
    return redirect("/home")

# VIP
@app.route("/buy_vip/<tipo>")
def buy_vip(tipo):
    db = load()
    u = db["users"][session["user"]]

    precios = {"dia":50,"mes":200,"inf":1000}
    tiempo = {"dia":86400,"mes":2592000,"inf":999999999}

    if u["coins"] < precios[tipo]:
        return "No coins"

    u["coins"] -= precios[tipo]
    u["vip"] = now() + tiempo[tipo]

    save(db)
    return redirect("/home")

# GENERAR CÓDIGOS
@app.route("/gen_code")
def gen_code():
    if session.get("user") != "demon":
        return "No admin"

    codes = load_codes()
    code = ''.join(random.choices(string.ascii_uppercase+string.digits, k=8))

    codes[code] = 100
    save_codes(codes)

    return code

# USAR CÓDIGOS
@app.route("/use_code", methods=["POST"])
def use_code():
    codes = load_codes()
    db = load()
    u = db["users"][session["user"]]

    code = request.form["code"]

    if code in codes:
        u["coins"] += codes[code]
        del codes[code]

    save(db)
    save_codes(codes)

    return redirect("/home")

# ADMIN
@app.route("/admin", methods=["GET","POST"])
def admin():
    if session.get("user") != "demon":
        return "No admin"

    db = load()

    if request.method == "POST":
        user = request.form["user"]
        coins = int(request.form["coins"])

        if user in db["users"]:
            db["users"][user]["coins"] += coins

    save(db)
    return render_template("admin.html", users=db["users"])

# CHAT SIMPLE
CHAT = []

@app.route("/chat")
def chat():
    return render_template("chat.html", msgs=CHAT)

@app.route("/send", methods=["POST"])
def send():
    CHAT.append(session["user"] + ": " + request.form["msg"])
    return redirect("/chat")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(host="0.0.0.0", port=5000)
