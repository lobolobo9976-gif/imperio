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

    try:
        # 🔥 CONFIG PRINCIPAL (rápido)
        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "format": "best[ext=mp4]/best",
            "nocheckcertificate": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"]
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # 🔥 buscar mejor enlace válido
            if "formats" in info:
                for f in reversed(info["formats"]):
                    if f.get("url"):
                        return redirect(f["url"])

            if "url" in info:
                return redirect(info["url"])

            return "❌ No se pudo obtener enlace"

    except Exception:
        # 💣 FALLBACK (cuando YouTube falla)
        return redirect(f"https://www.y2mate.is/youtube?url={url}")

# Render compatible
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
