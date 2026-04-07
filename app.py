from flask import Flask, render_template, request, redirect, session, url_for
import time

app = Flask(__name__)
app.secret_key = "imperio_pro"

users = {}

def get_user():
    if "user" not in session:
        return None
    return users.get(session["user"])

def create_user(username, password):
    users[username] = {
        "password": password,
        "coins": 50,
        "xp": 0,
        "nivel": 1,
        "vip": 0,
        "last_mission": 0
    }

def add_xp(user, amount):
    user["xp"] += amount
    while user["xp"] >= user["nivel"] * 50 and user["nivel"] < 300:
        user["xp"] -= user["nivel"] * 50
        user["nivel"] += 1

@app.route("/", methods=["GET"])
def index():
    user = get_user()
    if not user:
        return redirect("/login")
    return render_template("index.html", user=user, time=time.time())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        if u not in users:
            create_user(u, p)

        if users[u]["password"] == p:
            session["user"] = u
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/misiones")
def misiones():
    user = get_user()
    now = time.time()

    cooldown = 30  # 30 segundos anti abuso

    if now - user["last_mission"] > cooldown:
        user["coins"] += 10
        add_xp(user, 10)
        user["last_mission"] = now
        msg = "Recompensa obtenida"
    else:
        msg = "Espera..."

    return render_template("misiones.html", msg=msg)

@app.route("/vip/<tipo>")
def vip(tipo):
    user = get_user()

    if tipo == "dia" and user["coins"] >= 50:
        user["coins"] -= 50
        user["vip"] = time.time() + 86400

    if tipo == "mes" and user["coins"] >= 200:
        user["coins"] -= 200
        user["vip"] = time.time() + 2592000

    return redirect("/")

@app.route("/admin", methods=["GET","POST"])
def admin():
    user = get_user()

    if session.get("user") != "admin":
        return "No autorizado"

    if request.method == "POST":
        target = request.form["user"]
        coins = int(request.form["coins"])
        if target in users:
            users[target]["coins"] += coins

    return render_template("admin.html")

@app.route("/chat", methods=["GET","POST"])
def chat():
    if "chat" not in app.config:
        app.config["chat"] = []

    if request.method == "POST":
        msg = request.form["msg"]
        app.config["chat"].append(msg)

    return render_template("chat.html", chat=app.config["chat"])

app.run(host="0.0.0.0", port=10000)
