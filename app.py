from flask import Flask, request, redirect, render_template, session
import os, json, time, random, string

app = Flask(__name__)
app.secret_key = "imperio_dios"

DB = "db.json"

def load():
    if not os.path.exists(DB):
        return {"users": {}, "codes": {}, "downloads": 0}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def now_day():
    return int(time.time() / 86400)

# 🎯 misiones random
def generate_missions():
    pool = [
        {"text": "Descarga 1 video", "goal": 1, "reward": 1},
        {"text": "Descarga 3 videos", "goal": 3, "reward": 2},
        {"text": "Gana 20 XP", "goal": 20, "reward": 2},
        {"text": "Usa la web 5 veces", "goal": 5, "reward": 2},
        {"text": "Sube 1 nivel", "goal": 1, "reward": 3}
    ]
    return random.sample(pool, 5)

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    db = load()

    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        if u not in db["users"]:
            db["users"][u] = {
                "pass": p,
                "coins": 5,
                "xp": 0,
                "level": 1,
                "use": 0,
                "missions": [],
                "done": [],
                "day": 0,
                "vip": 0
            }
            save(db)

        if db["users"][u]["pass"] == p:
            session["user"] = u
            return redirect("/home")

    return render_template("login.html")

# HOME
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    db = load()
    u = db["users"][session["user"]]

    # 🔁 reset diario
    if u["day"] != now_day():
        u["missions"] = generate_missions()
        u["done"] = [0]*5
        u["day"] = now_day()

    save(db)

    return render_template("index.html",
        user=session["user"],
        coins=u["coins"],
        xp=u["xp"],
        level=u["level"],
        missions=u["missions"],
        done=u["done"]
    )

# DESCARGA
@app.route("/download", methods=["POST"])
def download():
    db = load()
    u = db["users"][session["user"]]

    u["use"] += 1
    u["xp"] += 10

    # subir nivel
    if u["xp"] >= u["level"] * 100:
        u["level"] += 1
        u["xp"] = 0
        u["coins"] += 2

    # 🎯 completar misiones
    for i, m in enumerate(u["missions"]):
        if u["done"][i] == 1:
            continue

        if "Descarga" in m["text"]:
            if u["use"] >= m["goal"]:
                u["coins"] += m["reward"]
                u["done"][i] = 1

    save(db)
    return redirect("/home")

# 🛒 tienda
@app.route("/buy", methods=["POST"])
def buy():
    db = load()
    u = db["users"][session["user"]]

    if u["coins"] >= 50:
        u["coins"] -= 50
        u["vip"] = time.time() + 86400

    save(db)
    return redirect("/home")

# ⚙️ admin coins
@app.route("/give", methods=["POST"])
def give():
    db = load()

    if session.get("user") != "demon":
        return "No admin"

    user = request.form["user"]
    coins = int(request.form["coins"])

    if user in db["users"]:
        db["users"][user]["coins"] += coins

    save(db)
    return redirect("/home")

# logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
