from flask import Flask, request, send_file, render_template_string
import pdf2docx
from pdf2docx import Converter
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF → Word | AxtarGet</title>
    <meta charset="utf-8">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-purple-900 to-black min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/10 backdrop-blur-lg rounded-3xl p-10 max-w-2xl w-full shadow-2xl border border-white/20">
        <h1 class="text-5xl font-black text-center bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent mb-4">
            PDF → Word Çevirici
        </h1>
        <p class="text-gray-300 text-center mb-8">Şəkillər, cədvəllər, Azərbaycan hərfləri – hamısı qorunur</p>
        
        <form method="post" enctype="multipart/form-data" class="space-y-6">
            <div class="border-2 border-dashed border-cyan-400 rounded-2xl p-10 text-center">
                <input type="file" name="pdf" accept=".pdf" required class="hidden" id="file">
                <label for="file" class="cursor-pointer">
                    <div class="text-6xl mb-4">↑</div>
                    <p class="text-xl text-cyan-300 font-bold">PDF faylı seç və ya bura at</p>
                </label>
            </div>
            <button type="submit" class="w-full py-6 bg-gradient-to-r from-cyan-500 to-purple-600 text-white text-2xl font-black rounded-2xl hover:scale-105 transition">
                WORD-Ə ÇEVİR
            </button>
        </form>
        
        {% if result %}
        <div class="mt-8 p-6 bg-green-500/20 border border-green-400 rounded-2xl text-center">
            <p class="text-green-300 text-xl font-bold mb-4">{{ result }}</p>
            <a href="{{ url_for('download', filename=filename) }}" class="inline-block px-8 py-4 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700">
                WORD FAYLINI ENDİR (.docx)
            </a>
        </div>
        {% endif %}
        
        <p class="text-center text-gray-500 mt-10 text-sm">© 2025 AxtarGet – Azərbaycanın ən sürətlisi</p>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pdf_file = request.files["pdf"]
        if pdf_file and pdf_file.filename.endswith(".pdf"):
            pdf_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
            docx_path = pdf_path.replace(".pdf", ".docx")
            pdf_file.save(pdf_path)
            
            cv = Converter(pdf_path)
            cv.convert(docx_path)
            cv.close()
            
            filename = os.path.basename(docx_path)
            return render_template_string(HTML, result="Uğurla çevrildi!", filename=filename)
    
    return render_template_string(HTML)

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=True, download_name="çevirilmiş_sənəd.docx")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
