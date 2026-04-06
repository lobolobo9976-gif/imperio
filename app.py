from flask import Flask, render_template, request, redirect, session, send_from_directory
import os, json, time, random, string
import yt_dlp

app = Flask(__name__)
app.secret_key = "demon"

DB = "db.json"
DOWNLOADS = "downloads"

def load_db():
    return json.load(open(DB))

def save_db(db):
    json.dump(db, open(DB, "w"), indent=2)

def limit(plan):
    if plan == "free": return 5
    if plan == "vip": return 50
    if plan == "lifetime": return 999999
    return 5

@app.route("/", methods=["GET", "POST"])
def login():
    db = load_db()

    if request.method == "POST":
        user = request.form["user"]
        pw = request.form["pass"]

        if "login" in request.form:
            if user in db["usuarios"] and db["usuarios"][user]["pass"] == pw:
                session["user"] = user
                return redirect("/home")

        if "register" in request.form:
            db["usuarios"][user] = {
                "pass": pw,
                "plan": "free",
                "uso": 0,
                "reset": time.time(),
                "vip_expira": 0
            }
            save_db(db)

    return render_template("login.html")

@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    db = load_db()
    u = db["usuarios"][session["user"]]

    if "plan" not in u:
        u["plan"] = "free"

    if time.time() - u["reset"] > 86400:
        u["uso"] = 0
        u["reset"] = time.time()

    # expiración VIP
    if u["plan"] == "vip" and time.time() > u.get("vip_expira", 0):
        u["plan"] = "free"

    restante = int((u.get("vip_expira",0) - time.time()) / 86400)
    if restante < 0: restante = 0

    save_db(db)

    carpeta = f"{DOWNLOADS}/{session['user']}"
    os.makedirs(carpeta, exist_ok=True)
    archivos = os.listdir(carpeta)

    return render_template("index.html",
        user=session["user"],
        plan=u["plan"],
        uso=u["uso"],
        limite=limit(u["plan"]),
        archivos=archivos,
        restante=restante
    )

@app.route("/descargar", methods=["POST"])
def descargar():
    if "user" not in session:
        return redirect("/")

    url = request.form["url"]
    db = load_db()
    u = db["usuarios"][session["user"]]

    if u["uso"] >= limit(u["plan"]):
        return "Límite alcanzado"

    carpeta = f"{DOWNLOADS}/{session['user']}"
    os.makedirs(carpeta, exist_ok=True)

    ydl_opts = {
        'outtmpl': f'{carpeta}/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except:
        return "Error descargando"

    u["uso"] += 1
    save_db(db)

    return redirect("/home")

@app.route("/ver/<path:nombre>")
def ver(nombre):
    if "user" not in session:
        return redirect("/")
    return send_from_directory(f"{DOWNLOADS}/{session['user']}", nombre)

@app.route("/borrar/<path:nombre>")
def borrar(nombre):
    if "user" not in session:
        return redirect("/")
    os.remove(f"{DOWNLOADS}/{session['user']}/{nombre}")
    return redirect("/home")

@app.route("/activar", methods=["POST"])
def activar():
    db = load_db()
    codigo = request.form["codigo"]

    if codigo in db["codigos"]:
        tipo = db["codigos"][codigo]
        user = db["usuarios"][session["user"]]

        if tipo == "1d": user["vip_expira"] = time.time() + 86400
        elif tipo == "7d": user["vip_expira"] = time.time() + 86400*7
        elif tipo == "30d": user["vip_expira"] = time.time() + 86400*30
        elif tipo == "365d": user["vip_expira"] = time.time() + 86400*365
        elif tipo == "life": user["plan"] = "lifetime"

        if tipo != "life":
            user["plan"] = "vip"

        del db["codigos"][codigo]
        save_db(db)

    return redirect("/home")

@app.route("/admin")
def admin():
    if session.get("user") != "demon":
        return "No admin"

    db = load_db()
    html = "<h1>PANEL ADMIN 🔥</h1>"

    for u in db["usuarios"]:
        html += f"{u} - {db['usuarios'][u].get('plan','free')} <a href='/ban/{u}'>BAN</a><br>"

    html += """
    <h3>Generar código</h3>
    <form action="/gen" method="post">
    <select name="tipo">
      <option value="1d">1 día</option>
      <option value="7d">7 días</option>
      <option value="30d">1 mes</option>
      <option value="365d">1 año</option>
      <option value="life">INFINITO</option>
    </select>
    <button>Generar</button>
    </form>
    """

    return html

@app.route("/ban/<user>")
def ban(user):
    db = load_db()
    if user in db["usuarios"]:
        del db["usuarios"][user]
        save_db(db)
    return redirect("/admin")

@app.route("/gen", methods=["POST"])
def gen():
    if session.get("user") != "demon":
        return "No admin"

    tipo = request.form["tipo"]
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    db = load_db()
    db["codigos"][code] = tipo
    save_db(db)

    return f"CODIGO: {code} ({tipo})"

app.run(host="0.0.0.0", port=5000)
