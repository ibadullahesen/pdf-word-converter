from flask import Flask, request, send_file, render_template_string
import PyPDF2
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
import uuid
import glob
from datetime import datetime, timedelta
from threading import Thread
import time
import logging
import io

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB maksimum fayl ölçüsü
CLEANUP_INTERVAL = 3600  # Hər 1 saat sil

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

last_cleanup_time = time.time()

def cleanup_old_files():
    """Köhnə faylları təmizləmək - background-da çalışacaq"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=1)
        for file_path in glob.glob(os.path.join(UPLOAD_FOLDER, "*")):
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        print(f"Köhnə fayl silindi: {file_path}")
                    except:
                        pass
    except Exception as e:
        print(f"Fayl təmizləmə xətası: {e}")

def background_cleanup():
    """Background-da fayl təmizliyi"""
    global last_cleanup_time
    current_time = time.time()
    if current_time - last_cleanup_time > CLEANUP_INTERVAL:
        last_cleanup_time = current_time
        cleanup_old_files()

def convert_pdf_to_docx(pdf_path, docx_path):
    """PyPDF2 istifadə edərək PDF-dən mətn çıxart və Word-ə yaz"""
    try:
        doc = Document()
        
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    # Səhifəni çıxart
                    text = page.extract_text()
                    
                    if text:
                        text = clean_text(text)
                        
                        # Səhifə başlığı əlavə et
                        if page_num > 1:
                            doc.add_page_break()
                        
                        # Mətn əlavə et
                        paragraph = doc.add_paragraph(text)
                        paragraph.style = 'Normal'
                        
                        print(f"[INFO] ({page_num}/{total_pages}) Səhifə uğurla çevrildi")
                    else:
                        print(f"[WARNING] ({page_num}/{total_pages}) Səhifədə mətn tapılmadı")
                        
                except Exception as e:
                    print(f"[ERROR] ({page_num}/{total_pages}) Səhifə xətası: {str(e)}")
                    # Xəta olsa belə, sonrakı səhifəyə geç
                    if page_num > 1:
                        doc.add_page_break()
                    doc.add_paragraph(f"[Səhifə {page_num} çevrilə bilmədi]")
        
        # Word sənədini saxla
        doc.save(docx_path)
        print(f"[INFO] Word sənədi uğurla yaradıldı: {docx_path}")
        
    except Exception as e:
        print(f"[ERROR] Çevirən xəta: {str(e)}")
        raise

def clean_text(text):
    """XML-uyğun olmayan simvolları sil/əvəz et"""
    if not text:
        return ""
    
    # NULL bytes və idarəetmə simvollarını sil
    cleaned = ""
    for char in text:
        code = ord(char)
        # XML-uyğun simvollar: 0x9, 0xA, 0xD, 0x20-0xD7FF, 0xE000-0xFFFD
        if (code == 0x9 or code == 0xA or code == 0xD or 
            (0x20 <= code <= 0xD7FF) or (0xE000 <= code <= 0xFFFD)):
            cleaned += char
        elif code < 32:
            # Idarəetmə simvollarını boşluğa çevir
            cleaned += " "
    
    # Çoxlu boşluqları tək boşluğa çevir
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    
    return cleaned.strip()

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
        <p class="text-gray-300 text-center mb-8">Bütün səhifələr tam şəkildə çevrilir</p>
        
        <form method="post" enctype="multipart/form-data" class="space-y-6" onsubmit="handleSubmit(event)">
            <div class="border-2 border-dashed border-cyan-400 rounded-2xl p-10 text-center hover:border-cyan-300 transition" id="drop-zone">
                <input type="file" name="pdf" accept=".pdf" required class="hidden" id="file">
                <label for="file" class="cursor-pointer block h-full">
                    <div class="text-6xl mb-4">↑</div>
                    <p class="text-xl text-cyan-300 font-bold" id="file-text">PDF faylı seç və ya bura sürükle</p>
                    <p class="text-sm text-gray-400 mt-2">Maksimum ölçü: 5 MB</p>
                </label>
            </div>
            
            <div id="file-info" class="hidden p-4 bg-cyan-500/20 border border-cyan-400 rounded-xl">
                <p class="text-cyan-300 font-bold text-lg">Seçilmiş fayl:</p>
                <p id="filename" class="text-white text-sm mt-1"></p>
                <p id="filesize" class="text-gray-300 text-xs mt-1"></p>
            </div>

            <div id="progress-bar" class="hidden w-full">
                <div class="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div id="progress-fill" class="bg-gradient-to-r from-cyan-500 to-purple-600 h-full w-0 transition-all duration-300"></div>
                </div>
                <p id="progress-text" class="text-cyan-300 text-sm mt-2 text-center">Yüklənilir...</p>
            </div>
            
            <button type="submit" class="w-full py-6 bg-gradient-to-r from-cyan-500 to-purple-600 text-white text-2xl font-black rounded-2xl hover:scale-105 transition transform duration-200" id="submit-btn">
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
        const submitBtn = document.getElementById('submit-btn');
        const progressBar = document.getElementById('progress-bar');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

        fileInput.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                validateAndUpdateFile(this.files[0]);
            }
        });

        function validateAndUpdateFile(file) {
            if (file.size > MAX_FILE_SIZE) {
                alert('Fayl çox böyükdür! Maksimum 5 MB qəbul edilir.');
                fileInput.value = '';
                return;
            }
            updateFileInfo(file);
        }

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
                validateAndUpdateFile(files[0]);
            } else {
                alert('Yalnız PDF faylı qəbul edilir!');
            }
        }

        function handleSubmit(e) {
            e.preventDefault();
            if (!fileInput.files[0]) return;
            
            progressBar.classList.remove('hidden');
            submitBtn.disabled = true;
            submitBtn.classList.add('opacity-50');
            
            // Simulasiya progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 30;
                if (progress > 90) progress = 90;
                progressFill.style.width = progress + '%';
            }, 500);
            
            // Formu göndər
            const formData = new FormData(e.target);
            fetch(e.target.action || '/', {
                method: 'POST',
                body: formData
            }).then(() => {
                clearInterval(interval);
                progressFill.style.width = '100%';
                progressText.textContent = 'Tamamlandı!';
                setTimeout(() => {
                    e.target.submit();
                }, 500);
            }).catch(err => {
                clearInterval(interval);
                alert('Xəta: ' + err.message);
                submitBtn.disabled = false;
                submitBtn.classList.remove('opacity-50');
            });
        }
    </script>
</body>
</html>
"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    background_cleanup()
    
    if request.method == "POST":
        pdf_file = request.files.get("pdf")
        
        if not pdf_file or pdf_file.filename == '':
            return render_template_string(HTML, error="❌ Fayl seçilməyib!")
        
        if not pdf_file.filename.endswith(".pdf"):
            return render_template_string(HTML, error="❌ Yalnız PDF faylı qəbul edilir!")
        
        if pdf_file.content_length and pdf_file.content_length > MAX_FILE_SIZE:
            return render_template_string(
                HTML, 
                error=f"❌ Fayl çox böyükdür! Maksimum {MAX_FILE_SIZE // (1024*1024)} MB qəbul edilir."
            )
        
        pdf_path = None
        docx_path = None
        
        try:
            unique_id = str(uuid.uuid4())
            pdf_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.pdf")
            docx_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.docx")
            
            pdf_file.save(pdf_path)
            
            if os.path.getsize(pdf_path) > MAX_FILE_SIZE:
                os.remove(pdf_path)
                return render_template_string(
                    HTML, 
                    error=f"❌ Fayl çox böyükdür! Maksimum {MAX_FILE_SIZE // (1024*1024)} MB qəbul edilir."
                )
            
            convert_pdf_to_docx(pdf_path, docx_path)
            
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            
            filename = f"{unique_id}.docx"
            return render_template_string(
                HTML, 
                result="✅ PDF uğurla Word sənədinə çevrildi!", 
                filename=filename
            )
            
        except Exception as e:
            logger.error(f"PDF çevirən xəta: {str(e)}")
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass
            if docx_path and os.path.exists(docx_path):
                try:
                    os.remove(docx_path)
                except:
                    pass
            
            return render_template_string(
                HTML, 
                error=f"❌ Xəta: PDF-ni Word-ə çevirərkən problem yaşandı. Zəhmət olmasa başqa fayl sınayın."
            )
    
    return render_template_string(HTML)

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path) and filename.endswith('.docx'):
        return send_file(
            file_path, 
            as_attachment=True, 
            download_name="cevirilmis_sened.docx"
        )
    return "Fayl tapılmadı", 404

@app.route("/clean")
def clean():
    cleanup_old_files()
    return "Köhnə fayllar təmizləndi!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
