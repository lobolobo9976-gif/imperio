from flask import Flask, request, redirect, render_template, session
import json, os, time, random, requests

app = Flask(__name__)
app.secret_key = "imperio"

DB = "db.json"
DOWNLOADS = {}
CHAT = []

# ---------------- BASE ----------------

def load():
    try:
        return json.load(open(DB))
    except:
        return {"users": {}}

def save(db):
    json.dump(db, open(DB, "w"), indent=2)

def now():
    return int(time.time())

def xp_need(lvl):
    return 40 + lvl * 20

def generar_misiones():
    base = [
        {"name":"Descargar","coins":5,"xp":10},
        {"name":"Ganar coins","coins":10,"xp":20},
        {"name":"Abrir cofre","coins":8,"xp":15},
        {"name":"Chat","coins":3,"xp":5},
        {"name":"Subir nivel","coins":15,"xp":30}
    ]
    return base

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET","POST"])
def login():
    db = load()

    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        if u not in db["users"]:
            db["users"][u] = {
                "pass": p,
                "coins": 20,
                "xp": 0,
                "level": 1,
                "missions": []
            }

        if db["users"][u]["pass"] == p:
            session["user"] = u
            save(db)
            return redirect("/home")

    return render_template("login.html")

# ---------------- HOME ----------------

@app.route("/home")
def home():
    db = load()
    u = db["users"][session["user"]]

    return render_template("index.html",
        user=session["user"],
        coins=u["coins"],
        xp=u["xp"],
        level=u["level"],
        need=xp_need(u["level"])
    )

# ---------------- DESCARGA ----------------

@app.route("/download", methods=["POST"])
def download():
    db = load()
    u = db["users"][session["user"]]

    url = request.form["url"]

    try:
        r = requests.get(url, stream=True)
        name = url.split("/")[-1]

        os.makedirs("downloads", exist_ok=True)
        with open("downloads/"+name, "wb") as f:
            for chunk in r.iter_content(1024):
                if chunk:
                    f.write(chunk)

        u["coins"] += 2
        u["xp"] += 10

        save(db)
        return "OK"

    except:
        return "ERROR"

# ---------------- MISIONES ----------------

@app.route("/missions")
def missions():
    db = load()
    u = db["users"][session["user"]]

    if "missions" not in u or len(u["missions"]) == 0:
        u["missions"] = generar_misiones()

    html = "<h2>🎯 MISIONES</h2>"

    for i, m in enumerate(u["missions"]):
        html += f"""
        <p>{m['name']} 💰{m['coins']} ⭐{m['xp']}
        <a href='/claim/{i}'>[OK]</a></p>
        """

    html += "<br><a href='/home'>Volver</a>"

    save(db)
    return html

@app.route("/claim/<int:i>")
def claim(i):
    db = load()
    u = db["users"][session["user"]]

    if i < len(u["missions"]):
        m = u["missions"][i]
        u["coins"] += m["coins"]
        u["xp"] += m["xp"]
        u["missions"].pop(i)

    save(db)
    return redirect("/missions")

# ---------------- COFRE ----------------

@app.route("/chest")
def chest():
    db = load()
    u = db["users"][session["user"]]

    if u["coins"] < 10:
        return "No coins"

    u["coins"] -= 10
    premio = random.randint(5, 30)

    u["coins"] += premio
    save(db)

    return f"🎁 Ganaste {premio} coins <br><a href='/home'>Volver</a>"

# ---------------- CHAT ----------------

@app.route("/chat")
def chat():
    html = "<h2>💬 CHAT</h2>"

    for m in CHAT:
        html += "<p>"+m+"</p>"

    html += """
    <form method='post' action='/send'>
    <input name='msg'>
    <button>Enviar</button>
    </form>
    <a href='/home'>Volver</a>
    """

    return html

@app.route("/send", methods=["POST"])
def send():
    CHAT.append(session["user"]+": "+request.form["msg"])
    return redirect("/chat")

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
