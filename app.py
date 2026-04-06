from flask import Flask, request, redirect, render_template, session
import os, json, time, random

app = Flask(__name__)
app.secret_key = "imperio_ultra"

DB = "db.json"

def load():
    if not os.path.exists(DB):
        return {"users": {}}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def now():
    return int(time.time())

def day():
    return int(time.time()/86400)

# XP necesaria por nivel (hasta 300)
def xp_needed(level):
    return int(40 + (level-1)*20)

# misiones
def missions():
    pool = [
        {"text":"Descarga 1 video","goal":1,"reward":1},
        {"text":"Descarga 3 videos","goal":3,"reward":2},
        {"text":"Gana 40 XP","goal":40,"reward":2},
        {"text":"Usa la web 5 veces","goal":5,"reward":2},
        {"text":"Sube 1 nivel","goal":1,"reward":3}
    ]
    return random.sample(pool,5)

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
                "missions":[],
                "done":[0]*5,
                "day":0
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

    # reset misiones diario
    if u["day"] != day():
        u["missions"] = missions()
        u["done"] = [0]*5
        u["day"] = day()

    save(db)

    return render_template("index.html",
        user=session["user"],
        coins=u["coins"],
        xp=u["xp"],
        level=u["level"],
        need=xp_needed(u["level"]),
        missions=u["missions"],
        done=u["done"]
    )

# DESCARGA REAL (con control)
@app.route("/download", methods=["POST"])
def download():
    db = load()
    u = db["users"][session["user"]]

    url = request.form.get("url")

    if not url:
        return "Pon URL"

    # anti spam (3 segundos)
    if now() - u["last"] < 3:
        return "⚠️ Espera 3s"

    u["last"] = now()
    u["use"] += 1
    u["xp"] += 10

    # nivel hasta 300
    if u["level"] < 300:
        if u["xp"] >= xp_needed(u["level"]):
            u["xp"] = 0
            u["level"] += 1
            u["coins"] += 2

    # misiones
    for i,m in enumerate(u["missions"]):
        if u["done"][i] == 1:
            continue

        if "Descarga" in m["text"] and u["use"] >= m["goal"]:
            u["coins"] += m["reward"]
            u["done"][i] = 1

        if "XP" in m["text"] and u["xp"] >= m["goal"]:
            u["coins"] += m["reward"]
            u["done"][i] = 1

    save(db)

    return redirect("/home")

# ADMIN coins
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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
