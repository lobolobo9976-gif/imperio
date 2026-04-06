from flask import Flask, request, redirect, render_template, session
import yt_dlp, os, json

app = Flask(__name__)
app.secret_key = "imperio"

DB = "db.json"

def load():
    if not os.path.exists(DB):
        return {"users": {}, "downloads": 0}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

@app.route("/", methods=["GET","POST"])
def login():
    db = load()

    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        if u in db["users"]:
            if db["users"][u] == p:
                session["user"] = u
                return redirect("/home")
        else:
            db["users"][u] = p
            save(db)
            session["user"] = u
            return redirect("/home")

    return render_template("login.html")

@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")

    db = load()
    return render_template("index.html",
        user=session["user"],
        total=db["downloads"]
    )

@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    db = load()

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

            db["downloads"] += 1
            save(db)

            if "url" in info:
                return redirect(info["url"])

            for f in reversed(info.get("formats", [])):
                if f.get("url"):
                    return redirect(f["url"])

    except:
        return redirect(f"https://www.y2mate.is/youtube?url={url}")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
