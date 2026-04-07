from flask import Flask, request, redirect, render_template, session
import os, json, time, random, string, requests

app = Flask(__name__)
app.secret_key = "imperio_pro"

DB="db.json"
CODES="codes.json"

DOWNLOADS={}
CHAT=[]

def load():
    try: return json.load(open(DB))
    except: return {"users":{}}

def save(d): json.dump(d,open(DB,"w"),indent=2)

def load_codes():
    try: return json.load(open(CODES))
    except: return {}

def save_codes(d): json.dump(d,open(CODES,"w"),indent=2)

def now(): return int(time.time())

def xp_need(lvl): return 40 + lvl*20

def vip_text(v):
    if v > now():
        dias=int((v-now())/86400)
        return f"🔥 VIP {dias} días"
    return "❌ NO VIP"

# LOGIN
@app.route("/",methods=["GET","POST"])
def login():
    db=load()

    if request.method=="POST":
        u=request.form["user"]
        p=request.form["pass"]

        if u not in db["users"]:
            db["users"][u]={
                "pass":p,"coins":20,"xp":0,"level":1,
                "vip":0,"last_mission":0
            }

        if db["users"][u]["pass"]==p:
            session["user"]=u
            save(db)
            return redirect("/home")

    return render_template("login.html")

# HOME
@app.route("/home")
def home():
    db=load()
    u=db["users"][session["user"]]

    return render_template("index.html",
        user=session["user"],
        coins=u["coins"],
        xp=u["xp"],
        level=u["level"],
        need=xp_need(u["level"]),
        vip=vip_text(u["vip"])
    )

# DESCARGA REAL
@app.route("/download",methods=["POST"])
def download():
    db=load()
    u=db["users"][session["user"]]

    url=request.form["url"]

    try:
        r=requests.get(url,stream=True,timeout=10)
        filename=url.split("/")[-1]

        os.makedirs("downloads",exist_ok=True)
        path="downloads/"+filename

        total=int(r.headers.get('content-length',0))
        down=0

        with open(path,"wb") as f:
            for c in r.iter_content(1024):
                if c:
                    f.write(c)
                    down+=len(c)
                    DOWNLOADS[session["user"]]=int((down/total)*100) if total else 0

        DOWNLOADS[session["user"]]=100

        u["coins"]+=2
        u["xp"]+=15

        if u["xp"]>=xp_need(u["level"]):
            u["xp"]=0
            u["level"]+=1

        save(db)
        return "OK"

    except:
        return "ERROR"

@app.route("/progress")
def prog():
    return str(DOWNLOADS.get(session["user"],0))

# MISIONES
@app.route("/missions")
def missions():
    db=load()
    u=db["users"][session["user"]]

    if now()-u["last_mission"]>86400:
        coins=random.randint(5,15)
        xp=random.randint(10,30)

        u["coins"]+=coins
        u["xp"]+=xp
        u["last_mission"]=now()

        save(db)
        return f"🎯 +{coins} coins +{xp} xp"

    return "Ya hiciste misión hoy"

# COFRE
@app.route("/chest")
def chest():
    db=load()
    u=db["users"][session["user"]]

    if u["coins"]<10:
        return "❌ necesitas 10"

    u["coins"]-=10

    r=random.randint(1,100)

    if r<60:
        premio=random.randint(5,20)
        u["coins"]+=premio
        msg=f"💰 {premio}"
    elif r<90:
        premio=random.randint(20,50)
        u["coins"]+=premio
        msg=f"🔥 {premio}"
    else:
        msg="💀 nada"

    save(db)
    return msg

# VIP
@app.route("/buy_vip/<t>")
def vip(t):
    db=load()
    u=db["users"][session["user"]]

    dur={"dia":86400,"mes":2592000,"año":31536000,"inf":9999999999}
    price={"dia":50,"mes":200,"año":500,"inf":1000}

    if u["coins"]<price[t]:
        return "no coins"

    u["coins"]-=price[t]
    u["vip"]=now()+dur[t]

    save(db)
    return redirect("/home")

# CODIGOS
@app.route("/gen",methods=["POST"])
def gen():
    if session["user"]!="demon":
        return "no"

    t=request.form["tipo"]
    dur={"dia":86400,"mes":2592000,"año":31536000,"inf":9999999999}

    code=''.join(random.choices(string.ascii_uppercase+string.digits,k=10))

    c=load_codes()
    c[code]=dur[t]
    save_codes(c)

    return code

@app.route("/use",methods=["POST"])
def use():
    db=load()
    u=db["users"][session["user"]]

    code=request.form["code"]
    c=load_codes()

    if code in c:
        u["vip"]=now()+c[code]
        del c[code]

    save(db)
    save_codes(c)

    return redirect("/home")

# ADMIN
@app.route("/admin",methods=["GET","POST"])
def admin():
    if session["user"]!="demon":
        return "no"

    db=load()

    if request.method=="POST":
        user=request.form["user"]
        coins=int(request.form["coins"])

        if user in db["users"]:
            db["users"][user]["coins"]+=coins

    save(db)
    return render_template("admin.html",users=db["users"])

# CHAT
@app.route("/chat")
def chat():
    return render_template("chat.html",msgs=CHAT)

@app.route("/send",methods=["POST"])
def send():
    CHAT.append(session["user"]+": "+request.form["msg"])
    return redirect("/chat")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# IMPORTANTE RENDER
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
