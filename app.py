from flask import Flask, render_template, request, redirect, url_for, session
import time

app = Flask(__name__)
app.secret_key = "imperio_pro"

usuarios = {}

def get_user():
    user = session.get("user", "demon")
    if user not in usuarios:
        usuarios[user] = {
            "coins": 50,
            "xp": 0,
            "nivel": 1,
            "vip": 0
        }
    return usuarios[user]

@app.route("/")
def index():
    user = get_user()
    return render_template("index.html", user=user)

@app.route("/descargar", methods=["POST"])
def descargar():
    user = get_user()
    url = request.form.get("url")

    if url:
        user["coins"] += 5
        user["xp"] += 10

    return redirect(url_for("index"))

@app.route("/misiones")
def misiones():
    user = get_user()

    misiones = [
        {"nombre": "Descargar", "reward": 10},
        {"nombre": "Ganar XP", "reward": 15},
        {"nombre": "Usar web", "reward": 5}
    ]

    return render_template("misiones.html", misiones=misiones, user=user)

@app.route("/completar/<int:reward>")
def completar(reward):
    user = get_user()
    user["coins"] += reward
    return redirect(url_for("misiones"))

@app.route("/vip/<tipo>")
def vip(tipo):
    user = get_user()

    if tipo == "dia":
        user["vip"] = time.time() + 86400
    elif tipo == "mes":
        user["vip"] = time.time() + 2592000

    return redirect(url_for("index"))

@app.route("/comprar")
def comprar():
    return render_template("comprar.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

app.run(host="0.0.0.0", port=10000)
