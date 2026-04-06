from flask import Flask, request, redirect, render_template, session
import yt_dlp, os, json, time, random, string

app = Flask(__name__)
app.secret_key = "imperio_money"

DB = "db.json"

def load():
    if not os.path.exists(DB):
        return {"users": {}, "codes": {}, "downloads": 0, "ips": {}, "chats": {}}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def get_ip():
    return request.remote_addr

def limit(plan):
    if plan == "free": return 5
    if plan == "vip": return 50
    if plan == "lifetime": return 999999

# LOGIN
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
                "strikes": 0,
                "money": 0
            }
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
        total=db["downloads"]
    )

# ENVIAR DINERO
@app.route("/send_money", methods=["POST"])
def send_money():
    db = load()
    sender = session["user"]
    to = request.form["to"]
    amount = int(request.form["amount"])

    if to not in db["users"]:
        return "Usuario no existe"

    if db["users"][sender]["money"] < amount:
        return "Sin saldo"

    db["users"][sender]["money"] -= amount
    db["users"][to]["money"] += amount

    save(db)
    return redirect("/home")

# CHAT PRIVADO
@app.route("/chat/<user>", methods=["GET","POST"])
def private_chat(user):
    if "user" not in session:
        return redirect("/")

    db = load()
    me = session["user"]

    chat_id = "_".join(sorted([me, user]))

    if chat_id not in db["chats"]:
        db["chats"][chat_id] = []

    if request.method == "POST":
        msg = request.form["msg"]

        db["chats"][chat_id].append({
            "from": me,
            "msg": msg,
            "time": time.strftime("%H:%M")
        })

        save(db)

    return render_template("chat_private.html",
        msgs=db["chats"][chat_id],
        other=user
    )

@app.route("/chat_data/<user>")
def chat_data(user):
    db = load()
    me = session["user"]
    chat_id = "_".join(sorted([me, user]))

    return db["chats"].get(chat_id, [])

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
