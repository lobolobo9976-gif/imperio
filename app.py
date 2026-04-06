from flask import Flask, request, redirect, render_template, session
import os, json, time, random, string, yt_dlp

app = Flask(__name__)
app.secret_key = "imperio_ultra_dios"

DB = "db.json"

def load():
    if not os.path.exists(DB):
        return {"users": {}, "codes": {}, "downloads": 0, "ips": {}, "chats": {}}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def get_ip():
    return request.remote_addr

def limit(level):
    return 5 + (level * 2)

# LOGIN + AFILIADOS
@app.route("/", methods=["GET","POST"])
def login():
    db = load()
    ip = get_ip()
    ref = request.args.get("ref")

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
                "money": 0,
                "earn": 0,
                "ref": ref,
                "level": 1,
                "xp": 0,
                "points": 0,
                "use": 0,
                "last": 0,
                "strikes": 0,
                "history": []
            }

            if ref and ref in db["users"]:
                db["users"][ref]["earn"] += 1

            db["ips"][ip] = u
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

    return render_template("index.html",
        user=session["user"],
        money=u["money"],
        earn=u["earn"],
        level=u["level"],
        xp=u["xp"],
        points=u["points"],
        total=db["downloads"],
        history=u["history"],
        last_reward=u.get("last_reward","")
    )

# DESCARGA + XP + SORTEO
@app.route("/download", methods=["POST"])
def download():
    if "user" not in session:
        return redirect("/")

    db = load()
    u = db["users"][session["user"]]
    url = request.form["url"]

    now = time.time()

    if now - u["last"] < 3:
        u["strikes"] += 1
        save(db)
        return "⚠️ Espera"

    if u["strikes"] >= 5:
        return "🚫 Baneado"

    if u["use"] >= limit(u["level"]):
        return "❌ Límite alcanzado"

    try:
        with yt_dlp.YoutubeDL({"quiet":True}) as ydl:
            info = ydl.extract_info(url, download=False)

            # stats
            u["use"] += 1
            u["xp"] += 10
            u["points"] += 1
            u["last"] = now
            db["downloads"] += 1

            # subir nivel
            if u["xp"] >= u["level"] * 100:
                u["level"] += 1
                u["xp"] = 0

            # historial
            u["history"].append({
                "url": url,
                "time": time.strftime("%H:%M")
            })

            # 🎲 sorteo VIP
            if random.randint(1,10) == 1:
                code = ''.join(random.choices(string.ascii_uppercase+string.digits, k=8))
                if "codes" not in db:
                    db["codes"] = {}
                db["codes"][code] = "1d"
                u["last_reward"] = code

            save(db)

            if "url" in info:
                return redirect(info["url"])

    except:
        return "Error"

# ACTIVAR CÓDIGO
@app.route("/activar", methods=["POST"])
def activar():
    db = load()
    code = request.form["code"]

    if code not in db["codes"]:
        return "Código inválido"

    u = db["users"][session["user"]]
    u["money"] += 5  # recompensa ejemplo

    del db["codes"][code]
    save(db)

    return redirect("/home")

# ADMIN
@app.route("/admin")
def admin():
    if session.get("user") != "demon":
        return "No admin"

    return """
    <h1>💀 ADMIN</h1>
    <form action="/gen" method="post">
    <select name="tipo">
    <option value="1d">1 día</option>
    </select>
    <button>Generar código</button>
    </form>
    """

@app.route("/gen", methods=["POST"])
def gen():
    db = load()
    code = ''.join(random.choices(string.ascii_uppercase+string.digits, k=8))
    db["codes"][code] = "1d"
    save(db)
    return f"CODIGO: {code}"

# CHAT PRIVADO
@app.route("/chat/<user>", methods=["GET","POST"])
def chat(user):
    db = load()
    me = session["user"]

    cid = "_".join(sorted([me,user]))

    if cid not in db["chats"]:
        db["chats"][cid] = []

    if request.method == "POST":
        db["chats"][cid].append({
            "from": me,
            "msg": request.form["msg"]
        })
        save(db)

    return render_template("chat.html",
        msgs=db["chats"][cid],
        other=user
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
