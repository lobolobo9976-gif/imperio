from flask import Flask, request, redirect, render_template
import yt_dlp
import os

app = Flask(__name__)

# usuarios (simple)
users = {
    "demon": {"vip": True}
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")

    if not url:
        return "❌ URL inválida"

    ydl_opts = {
        "format": "best",
        "quiet": True,
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get("url")

            if not video_url:
                return "❌ No se pudo obtener el enlace"

            # 🔥 descarga directa
            return redirect(video_url)

    except Exception as e:
        return f"❌ Error: {str(e)}"

# render compatible
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
