from flask import Flask, request, redirect, render_template
import yt_dlp
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")

    if not url:
        return "❌ URL inválida"

    ydl_opts = {
        "quiet": True,
        "noplaylist": True,

        # 🔥 velocidad + compatibilidad
        "format": "bv*+ba/best",
        
        "nocheckcertificate": True,

        # 🔥 truco para YouTube
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # 🔥 coger mejor formato real
            formats = info.get("formats", [])
            best = None

            for f in formats[::-1]:
                if f.get("url"):
                    best = f["url"]
                    break

            if not best:
                return "❌ No se pudo obtener enlace"

            return redirect(best)

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
