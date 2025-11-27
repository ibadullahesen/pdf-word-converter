from flask import Flask, request, send_file, render_template_string
import pdf2docx
from pdf2docx import Converter
import os
import uuid
import glob
from datetime import datetime, timedelta

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Köhnə faylları təmizləmək üçün funksiya
def cleanup_old_files():
    try:
        # 1 saatdan köhnə faylları tap
        cutoff_time = datetime.now() - timedelta(hours=1)
        for file_path in glob.glob(os.path.join(UPLOAD_FOLDER, "*")):
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    os.remove(file_path)
                    print(f"Köhnə fayl silindi: {file_path}")
    except Exception as e:
        print(f"Fayl təmizləmə xətası: {e}")

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
            <div class="border-2 border-dashed border-cyan-400 rounded-2xl p-10 text-center hover:border-cyan-300 transition" id="drop-zone">
                <input type="file" name="pdf" accept=".pdf" required class="hidden" id="file">
                <label for="file" class="cursor-pointer block h-full">
                    <div class="text-6xl mb-4">↑</div>
                    <p class="text-xl text-cyan-300 font-bold" id="file-text">PDF faylı seç və ya bura sürükle</p>
                    <p class="text-sm text-gray-400 mt-2">Drag & drop dəstəklənir</p>
                </label>
            </div>
            
            <div id="file-info" class="hidden p-4 bg-cyan-500/20 border border-cyan-400 rounded-xl">
                <p class="text-cyan-300 font-bold text-lg">Seçilmiş fayl:</p>
                <p id="filename" class="text-white text-sm mt-1"></p>
                <p id="filesize" class="text-gray-300 text-xs mt-1"></p>
            </div>
            
            <button type="submit" class="w-full py-6 bg-gradient-to-r from-cyan-500 to-purple-600 text-white text-2xl font-black rounded-2xl hover:scale-105 transition transform duration-200">
                WORD-Ə ÇEVİR
            </button>
        </form>
        
        {% if result %}
        <div class="mt-8 p-6 bg-green-500/20 border border-green-400 rounded-2xl text-center animate-pulse">
            <p class="text-green-300 text-xl font-bold mb-4">{{ result }}</p>
            <a href="{{ url_for('download', filename=filename) }}" class="inline-block px-8 py-4 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700 transition">
                📥 WORD FAYLINI ENDİR (.docx)
            </a>
            <p class="text-gray-300 text-sm mt-3">Yeni fayl çevirmək üçün yuxarıdan başqa PDF seçə bilərsiniz</p>
        </div>
        {% endif %}
        
        {% if error %}
        <div class="mt-8 p-6 bg-red-500/20 border border-red-400 rounded-2xl text-center">
            <p class="text-red-300 text-xl font-bold">{{ error }}</p>
        </div>
        {% endif %}
        
        <div class="mt-6 text-center">
            <a href="{{ url_for('index') }}" class="inline-block px-6 py-3 bg-gray-600 text-white font-bold rounded-xl hover:bg-gray-700 transition">
                🗑️ Yeni Fayl Yüklə
            </a>
        </div>
        
        <p class="text-center text-gray-500 mt-10 text-sm">© 2025 AxtarGet – Azərbaycanın ən sürətlisi</p>
    </div>

    <script>
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file');
        const fileText = document.getElementById('file-text');
        const fileInfo = document.getElementById('file-info');
        const fileName = document.getElementById('filename');
        const fileSize = document.getElementById('filesize');

        // Fayl seçildikdə
        fileInput.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                updateFileInfo(this.files[0]);
            }
        });

        function updateFileInfo(file) {
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileInfo.classList.remove('hidden');
            fileText.textContent = 'Fayl seçildi! Yenisini seçmək üçün yenidən klikləyin';
            dropZone.classList.add('border-green-400');
            dropZone.classList.remove('border-cyan-400');
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        // Drag & Drop funksionallığı
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            dropZone.classList.add('bg-cyan-500/20', 'border-green-400');
            dropZone.classList.remove('border-cyan-400');
        }

        function unhighlight(e) {
            dropZone.classList.remove('bg-cyan-500/20', 'border-green-400');
            dropZone.classList.add('border-cyan-400');
        }

        dropZone.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0 && files[0].type === 'application/pdf') {
                fileInput.files = files;
                updateFileInfo(files[0]);
            } else {
                alert('Yalnız PDF faylı qəbul edilir!');
            }
        }

        // Form göndərildikdə loading effekti
        document.querySelector('form').addEventListener('submit', function() {
            const button = this.querySelector('button[type="submit"]');
            button.textContent = 'ÇEVİRİLİR...';
            button.disabled = true;
            button.classList.add('opacity-50');
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    # Köhnə faylları təmizlə
    cleanup_old_files()
    
    if request.method == "POST":
        pdf_file = request.files["pdf"]
        if pdf_file and pdf_file.filename.endswith(".pdf"):
            try:
                # Unikal fayl adı yarat
                unique_id = str(uuid.uuid4())
                pdf_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.pdf")
                docx_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.docx")
                
                # PDF faylını yadda saxla
                pdf_file.save(pdf_path)
                
                # PDF-dən DOCX-ə çevir
                cv = Converter(pdf_path)
                cv.convert(docx_path, start=0, end=None)
                cv.close()
                
                # Köhnə PDF faylını sil
                os.remove(pdf_path)
                
                filename = f"{unique_id}.docx"
                return render_template_string(
                    HTML, 
                    result="✅ PDF uğurla Word sənədinə çevrildi!", 
                    filename=filename
                )
                
            except Exception as e:
                # Xəta baş verərsə, faylları təmizlə
                for file_path in [pdf_path, docx_path]:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                return render_template_string(
                    HTML, 
                    error=f"❌ Xəta: {str(e)}"
                )
        else:
            return render_template_string(
                HTML, 
                error="❌ Zəhmət olmasa etibarlı PDF faylı seçin!"
            )
    
    return render_template_string(HTML)

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        # Türkçə karakterləri təmizlə
        safe_filename = "cevirilmis_sened.docx"
        return send_file(
            file_path, 
            as_attachment=True, 
            download_name=safe_filename
        )
    return "Fayl tapılmadı", 404

# Əsas səhifəyə yönləndirmə
@app.route("/clean")
def clean():
    cleanup_old_files()
    return "Köhnə fayllar təmizləndi!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
