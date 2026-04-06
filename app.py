from flask import Flask, request, redirect, render_template, session, url_for
import os, json, time, random, string

app = Flask(__name__)
app.secret_key = "imperio_pro"

DB = "db.json"

# -------- DB --------
def load():
    if not os.path.exists(DB):
        return {"users": {}, "codes": {}, "downloads": 0, "ips": {}, "chats": {}}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def get_ip():
    return request.headers.get("x-forwarded-for", request.remote_addr)

def limit(level):
    return 5 + level * 2

def now():
    return int(time.time())

# -------- LOGIN / REGISTER --------
@app.route("/", methods=["GET","POST"])
def login():
    db = load()
    ip = get_ip()

    if request.method == "POST":
        u = request.form.get("user","").strip()
        p = request.form.get("pass","").strip()

        if not u or not p:
            return "Faltan datos"

        # anti multi cuenta por IP simple
        if ip in db["ips"] and db["ips"][ip] != u:
            return "🚫 Solo 1 cuenta por dispositivo"

        if u not in db["users"]:
            db["users"][u] = {
                "pass": p,
                "level": 1,
                "xp": 0,
                "use": 0,
                "last": 0,
                "strikes": 0,
                "history": [],
                "vip_until": 0,
                "money": 0,
                "last_reward": ""
            }
            db["ips"][ip] = u
            save(db)
            session["user"] = u
            return redirect("/home")

        if db["users"][u]["pass"] == p:
            session["user"] = u
            db["ips"][ip] = u
            save(db)
            return redirect("/home")

        return "❌ Contraseña incorrecta"

    return render_template("login.html")

# -------- HOME --------
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    db = load()
    u = db["users"][session["user"]]

    is_vip = u.get("vip_until",0) > now()

    return render_template("index.html",
        user=session["user"],
        level=u["level"],
        xp=u["xp"],
        use=u["use"],
        limit=limit(u["level"]),
        total=db["downloads"],
        history=u["history"][-10:][::-1],
        vip=is_vip,
        last_reward=u.get("last_reward","")
    )

# -------- DESCARGA (ESTABLE / SIMULADA) --------
@app.route("/download", methods=["POST"])
def download():
    if "user" not in session:
        return redirect("/")

    db = load()
    u = db["users"][session["user"]]
    url = request.form.get("url","").strip()
    t = now()

    if not url:
        return "URL vacía"

    # anti spam
    if t - u["last"] < 2:
        u["strikes"] += 1
        save(db)
        return "⚠️ Espera 2s"

    if u["strikes"] >= 5:
        return "🚫 Bloqueado por abuso"

    # límite (VIP ignora límite)
    if u.get("vip_until",0) < t:
        if u["use"] >= limit(u["level"]):
            return "❌ Límite alcanzado"

    # sumar stats
    u["use"] += 1
    u["xp"] += 10
    u["last"] = t
    db["downloads"] += 1

    # subir nivel
    if u["xp"] >= u["level"] * 100:
        u["level"] += 1
        u["xp"] = 0

    # historial
    u["history"].append({"url": url, "time": time.strftime("%H:%M")})

    # 🎲 sorteo código 1 día (10%)
    if random.randint(1,10) == 1:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        db["codes"][code] = "1d"
        u["last_reward"] = code

    save(db)

    # aquí no rompemos: redirige a la URL (simula descarga)
    return redirect(url)

# -------- ACTIVAR CÓDIGO --------
@app.route("/activar", methods=["POST"])
def activar():
    if "user" not in session:
        return redirect("/")

    db = load()
    code = request.form.get("code","").strip()

    if code not in db["codes"]:
        return "Código inválido"

    tipo = db["codes"][code]
    u = db["users"][session["user"]]

    if tipo == "1d":
        u["vip_until"] = now() + 86400
    elif tipo == "30d":
        u["vip_until"] = now() + 86400*30

    del db["codes"][code]
    save(db)
    return redirect("/home")

# -------- ADMIN --------
@app.route("/admin")
def admin():
    if session.get("user") != "demon":
        return "No admin"

    return """
    <h1>💀 ADMIN</h1>
    <form action="/gen" method="post">
      <select name="tipo">
        <option value="1d">1 día</option>
        <option value="30d">1 mes</option>
      </select>
      <button>Generar código</button>
    </form>
    <br><a href="/home">Volver</a>
    """

@app.route("/gen", methods=["POST"])
def gen():
    if session.get("user") != "demon":
        return "No admin"

    db = load()
    tipo = request.form.get("tipo","1d")
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    db["codes"][code] = tipo
    save(db)
    return f"CODIGO: {code}"

# -------- CHAT SIMPLE --------
@app.route("/chat/<other>", methods=["GET","POST"])
def chat(other):
    if "user" not in session:
        return redirect("/")

    db = load()
    me = session["user"]
    cid = "_".join(sorted([me, other]))

    if cid not in db["chats"]:
        db["chats"][cid] = []

    if request.method == "POST":
        msg = request.form.get("msg","").strip()
        if msg:
            db["chats"][cid].append({"from": me, "msg": msg})
            save(db)

    return render_template("chat.html", msgs=db["chats"][cid][-50:], other=other)

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------- START --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
