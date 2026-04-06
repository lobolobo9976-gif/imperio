from flask import Flask, request, redirect, render_template, session, jsonify
import os, json, time, random, string, threading
import yt_dlp

app = Flask(__name__)
app.secret_key = "imperio_full"

DB = "db.json"
CODES = "codes.json"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

queue = []
progress_data = {}

def load():
    try:
        return json.load(open(DB))
    except:
        return {"users": {}}

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def now():
    return int(time.time())

def xp_needed(level):
    return 40 + level*20

# -------- WORKER DESCARGA --------
def worker():
    while True:
        if queue:
            task = queue.pop(0)
            url = task["url"]
            pid = task["id"]

            try:
                ydl_opts = {
                    'outtmpl': DOWNLOAD_FOLDER + "/%(title)s.%(ext)s",
                    'format': 'mp4',
                    'quiet': True,
                    'progress_hooks': [task["hook"]]
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                progress_data[pid]["status"] = "done"

            except:
                progress_data[pid]["status"] = "error"

        time.sleep(1)

threading.Thread(target=worker, daemon=True).start()

# -------- LOGIN --------
@app.route("/", methods=["GET","POST"])
def login():
    db = load()

    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        if u not in db["users"]:
            db["users"][u] = {
                "pass":p,
                "coins":10,
                "xp":0,
                "level":1,
                "vip":0
            }

        if db["users"][u]["pass"] == p:
            session["user"] = u
            save(db)
            return redirect("/home")

    return render_template("login.html")

# -------- HOME --------
@app.route("/home")
def home():
    db = load()
    u = db["users"][session["user"]]

    return render_template("index.html",
        user=session["user"],
        coins=u["coins"],
        xp=u["xp"],
        level=u["level"],
        need=xp_needed(u["level"])
    )

# -------- DESCARGA --------
@app.route("/download", methods=["POST"])
def download():
    db = load()
    u = db["users"][session["user"]]

    urls = [request.form.get(f"url{i}") for i in range(1,7)]
    urls = [x for x in urls if x]

    ids = []

    for url in urls:
        pid = str(time.time()) + str(random.randint(1,999))
        progress_data[pid] = {"progress":"0%","status":"downloading"}

        def hook(d, pid=pid):
            if d['status'] == 'downloading':
                progress_data[pid]["progress"] = d.get('_percent_str',"0%")
            if d['status'] == 'finished':
                progress_data[pid]["progress"] = "100%"

        queue.append({"url":url,"hook":hook,"id":pid})
        ids.append(pid)

    u["xp"] += len(ids)*10
    u["coins"] += len(ids)

    if u["xp"] >= xp_needed(u["level"]):
        u["xp"] = 0
        u["level"] += 1

    save(db)
    return jsonify(ids)

@app.route("/progress/<pid>")
def progress(pid):
    return jsonify(progress_data.get(pid,{}))

# -------- CASINO --------
@app.route("/casino")
def casino():
    return render_template("casino.html")

@app.route("/spin")
def spin():
    db = load()
    u = db["users"][session["user"]]

    if u["coins"] < 5:
        return "No coins"

    u["coins"] -= 5
    r = random.choice([0,2,5,10,20])

    if r > 0:
        u["coins"] += r

    save(db)
    return str(r)

# -------- TIENDA --------
@app.route("/shop")
def shop():
    db = load()
    return render_template("shop.html", coins=db["users"][session["user"]]["coins"])

@app.route("/buy_vip/<tipo>")
def buy_vip(tipo):
    db = load()
    u = db["users"][session["user"]]

    precios = {"dia":50,"mes":200,"inf":1000}
    tiempos = {"dia":86400,"mes":2592000,"inf":9999999999}

    if u["coins"] < precios[tipo]:
        return "No coins"

    u["coins"] -= precios[tipo]
    u["vip"] = now() + tiempos[tipo]

    save(db)
    return redirect("/home")

# -------- COFRES --------
@app.route("/chest")
def chest():
    db = load()
    u = db["users"][session["user"]]

    if u["coins"] < 10:
        return "No coins"

    u["coins"] -= 10

    premio = random.choice(["coins","xp","vip"])

    if premio == "coins":
        u["coins"] += random.randint(5,20)

    elif premio == "xp":
        u["xp"] += 20

    elif premio == "vip":
        u["vip"] = now() + 60

    save(db)
    return redirect("/home")

# -------- ADMIN --------
@app.route("/admin", methods=["GET","POST"])
def admin():
    if session.get("user") != "demon":
        return "No admin"

    db = load()

    if request.method == "POST":
        user = request.form["user"]
        coins = int(request.form["coins"])

        if user in db["users"]:
            db["users"][user]["coins"] += coins

    save(db)
    return render_template("admin.html", users=db["users"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
