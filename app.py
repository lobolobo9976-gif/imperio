from flask import Flask, request, redirect, render_template, session, jsonify
import os, json, time, random, string, threading
import yt_dlp

app = Flask(__name__)
app.secret_key = "imperio_ultra"

DB = "db.json"
CODES = "codes.json"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

queue = []
progress_data = {}

def load():
    if not os.path.exists(DB):
        return {"users": {}}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

def load_codes():
    if not os.path.exists(CODES):
        return {}
    return json.load(open(CODES))

def save_codes(data):
    json.dump(data, open(CODES, "w"), indent=2)

def now():
    return int(time.time())

def xp_needed(level):
    return int(40 + (level-1)*15)

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase+string.digits, k=10))

# WORKER DESCARGA
def worker():
    while True:
        if queue:
            task = queue.pop(0)
            url = task["url"]

            ydl_opts = {
                'outtmpl': DOWNLOAD_FOLDER + "/%(title)s.%(ext)s",
                'format': 'mp4',
                'quiet': True,
                'progress_hooks': [task["hook"]]
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except:
                task["progress"]["status"] = "error"
        time.sleep(1)

threading.Thread(target=worker, daemon=True).start()

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
                "vip":0,
                "banned":False
            }

        if db["users"][u]["pass"] == p:
            session["user"] = u
            save(db)
            return redirect("/home")

    return render_template("login.html")

# HOME
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

# DESCARGA
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
                progress_data[pid]["status"] = "done"

        queue.append({"url":url,"hook":hook})
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

# CASINO
@app.route("/spin")
def spin():
    db = load()
    u = db["users"][session["user"]]

    if u["coins"] < 5:
        return "No coins"

    u["coins"] -= 5
    r = random.choice([0,2,5,10])

    if r > 0:
        u["coins"] += r

    save(db)
    return str(r)

# ADMIN
@app.route("/admin", methods=["GET","POST"])
def admin():
    if session.get("user") != "demon":
        return "No admin"

    db = load()
    codes = load_codes()

    if request.method == "POST":
        user = request.form.get("user")
        coins = request.form.get("coins")

        if user and coins:
            if user in db["users"]:
                db["users"][user]["coins"] += int(coins)

        if request.form.get("gen"):
            t = int(request.form["time"])
            unit = request.form["unit"]

            sec = {
                "seg":t,
                "min":t*60,
                "dia":t*86400,
                "mes":t*2592000,
                "inf":9999999999
            }[unit]

            code = gen_code()
            codes[code] = {"time":sec,"used":False}
            save_codes(codes)

    save(db)

    return render_template("admin.html", users=db["users"], codes=codes)

# CANJEAR
@app.route("/redeem", methods=["POST"])
def redeem():
    db = load()
    codes = load_codes()

    code = request.form["code"]

    if code in codes and not codes[code]["used"]:
        db["users"][session["user"]]["vip"] = now()+codes[code]["time"]
        codes[code]["used"] = True

    save(db)
    save_codes(codes)

    return redirect("/home")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
