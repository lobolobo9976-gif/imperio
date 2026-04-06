from flask import Flask, request, redirect, render_template, session
import yt_dlp, os, json, time, random, string

app = Flask(__name__)
app.secret_key = "imperio_dios"

DB = "db.json"

def load():
    if not os.path.exists(DB):
        return {"users": {}, "codes": {}, "downloads": 0}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def limit(plan):
    if plan == "free": return 5
    if plan == "vip": return 50
    if plan == "lifetime": return 999999

@app.route("/", methods=["GET","POST"])
def login():
    db = load()

    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        if u in db["users"]:
            if db["users"][u]["pass"] == p:
                session["user"] = u
                return redirect("/home")
        else:
            db["users"][u] = {
                "pass": p,
                "plan": "free",
                "exp": 0,
                "ban": False,
                "use": 0
            }
            save(db)
            session["user"] = u
            return redirect("/home")

    return render_template("login.html")

@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    db = load()
    u = db["users"][session["user"]]

    # ban
    if u.get("ban"):
        return "🚫 Baneado"

    # expiración
    if u["plan"] == "vip" and time.time() > u["exp"]:
        u["plan"] = "free"

    return render_template("index.html",
        user=session["user"],
        plan=u["plan"],
        total=db["downloads"],
        limite=limit(u["plan"]),
        uso=u["use"]
    )

@app.route("/download", methods=["POST"])
def download():
    if "user" not in session:
        return redirect("/")

    url = request.form["url"]
    db = load()
    u = db["users"][session["user"]]

    if u["use"] >= limit(u["plan"]):
        return "❌ Límite alcanzado"

    ydl_opts = {
        "quiet": True,
        "format": "best",
        "noplaylist": True,
        "extractor_args": {
            "youtube": {"player_client": ["android"]}
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            u["use"] += 1
            db["downloads"] += 1
            save(db)

            if "url" in info:
                return redirect(info["url"])

            for f in reversed(info.get("formats", [])):
                if f.get("url"):
                    return redirect(f["url"])

    except:
        return redirect(f"https://www.y2mate.is/youtube?url={url}")

@app.route("/activar", methods=["POST"])
def activar():
    db = load()
    code = request.form["code"]
    u = db["users"][session["user"]]

    if code in db["codes"]:
        tipo = db["codes"][code]

        if tipo == "1d": u["exp"] = time.time()+86400
        elif tipo == "30d": u["exp"] = time.time()+86400*30
        elif tipo == "365d": u["exp"] = time.time()+86400*365
        elif tipo == "life": u["plan"] = "lifetime"

        if tipo != "life":
            u["plan"] = "vip"

        del db["codes"][code]
        save(db)

    return redirect("/home")

@app.route("/admin")
def admin():
    if session.get("user") != "demon":
        return "No admin"

    db = load()

    html = "<h1>ADMIN PANEL 💀</h1>"

    for u in db["users"]:
        html += f"{u} - {db['users'][u]['plan']} <a href='/ban/{u}'>BAN</a><br>"

    html += """
    <form action="/gen" method="post">
    <select name="tipo">
    <option value="1d">1 día</option>
    <option value="30d">1 mes</option>
    <option value="365d">1 año</option>
    <option value="life">∞</option>
    </select>
    <button>Generar código</button>
    </form>
    """

    return html

@app.route("/ban/<user>")
def ban(user):
    db = load()
    db["users"][user]["ban"] = True
    save(db)
    return redirect("/admin")

@app.route("/gen", methods=["POST"])
def gen():
    db = load()
    tipo = request.form["tipo"]

    code = ''.join(random.choices(string.ascii_uppercase+string.digits, k=10))
    db["codes"][code] = tipo

    save(db)
    return f"CODIGO: {code}"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
