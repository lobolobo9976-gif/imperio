from flask import Flask, request, redirect, render_template, session
import os, json

app = Flask(__name__)
app.secret_key = "imperio_total"

DB = "db.json"

def load():
    if not os.path.exists(DB):
        return {"users": {}, "downloads": 0}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=2)

# LOGIN + AFILIADOS
@app.route("/", methods=["GET","POST"])
def login():
    db = load()
    ref = request.args.get("ref")

    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        if u in db["users"]:
            if db["users"][u]["pass"] == p:
                session["user"] = u
        else:
            db["users"][u] = {
                "pass": p,
                "money": 0,
                "earn": 0,
                "ref": ref
            }

            if ref and ref in db["users"]:
                db["users"][ref]["earn"] += 1

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
        total=db["downloads"]
    )

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
