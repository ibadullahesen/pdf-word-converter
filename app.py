from flask import Flask, request, send_file, render_template_string, jsonify
import pdf2docx
from pdf2docx import Converter
import os
import uuid
import glob
from datetime import datetime, timedelta
import threading
import time
import psutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Fayl ölçü limiti (10MB)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Performans optimallaşdırmaları
class PerformanceOptimizer:
    def __init__(self):
        self.conversion_lock = threading.Lock()
        self.active_conversions = 0
        self.max_concurrent = 2  # Eyni anda maksimum çevirmə sayı
    
    def can_start_conversion(self):
        with self.conversion_lock:
            if self.active_conversions < self.max_concurrent:
                self.active_conversions += 1
                return True
            return False
    
    def conversion_finished(self):
        with self.conversion_lock:
            self.active_conversions -= 1
    
    def get_system_load(self):
        # Sistem yükünü yoxla
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        return cpu_percent, memory_percent

optimizer = PerformanceOptimizer()

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

# Optimized conversion function
def convert_pdf_to_docx(pdf_path, docx_path):
    """PDF-dən DOCX-ə çevirmə funksiyası optimallaşdırılmış"""
    try:
        # Çevirmə parametrləri
        cv = Converter(pdf_path)
        
        # Optimallaşdırılmış çevirmə parametrləri
        cv.convert(
            docx_path, 
            start=0, 
            end=None,
            multi_processing=True,  # Çox prosesli işləmə
            cpu_count=2  # İstifadə ediləcək CPU sayı
        )
        cv.close()
        return True
    except Exception as e:
        print(f"Çevirmə xətası: {e}")
        return False

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF → Word | AxtarGet</title>
    <meta charset="utf-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body class="bg-gradient-to-br from-purple-900 to-black min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/10 backdrop-blur-lg rounded-3xl p-6 md:p-10 max-w-2xl w-full shadow-2xl border border-white/20">
        <h1 class="text-3xl md:text-5xl font-black text-center bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent mb-4">
            PDF → Word Çevirici
        </h1>
        <p class="text-gray-300 text-center mb-6 md:mb-8 text-sm md:text-base">Şəkillər, cədvəllər, Azərbaycan hərfləri – hamısı qorunur</p>
        
        <form method="post" enctype="multipart/form-data" class="space-y-4 md:space-y-6" id="conversion-form">
            <div class="border-2 border-dashed border-cyan-400 rounded-2xl p-6 md:p-10 text-center hover:border-cyan-300 transition" id="drop-zone">
                <input type="file" name="pdf" accept=".pdf" required class="hidden" id="file">
                <label for="file" class="cursor-pointer block h-full">
                    <div class="text-4xl md:text-6xl mb-3 md:mb-4">↑</div>
                    <p class="text-lg md:text-xl text-cyan-300 font-bold" id="file-text">PDF faylı seç və ya bura sürükle</p>
                    <p class="text-xs md:text-sm text-gray-400 mt-2">Maksimum ölçü: 10MB</p>
                </label>
            </div>
            
            <div id="file-info" class="hidden p-4 bg-cyan-500/20 border border-cyan-400 rounded-xl">
                <p class="text-cyan-300 font-bold text-lg">Seçilmiş fayl:</p>
                <p id="filename" class="text-white text-sm mt-1"></p>
                <p id="filesize" class="text-gray-300 text-xs mt-1"></p>
                <div id="progress-bar" class="hidden mt-2">
                    <div class="bg-gray-700 rounded-full h-2">
                        <div id="progress-fill" class="bg-cyan-400 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                    </div>
                    <p id="progress-text" class="text-cyan-300 text-xs mt-1">0%</p>
                </div>
            </div>
            
            <button type="submit" id="convert-btn" class="w-full py-4 md:py-6 bg-gradient-to-r from-cyan-500 to-purple-600 text-white text-xl md:text-2xl font-black rounded-2xl hover:scale-105 transition transform duration-200 disabled:opacity-50 disabled:cursor-not-allowed">
                WORD-Ə ÇEVİR
            </button>
        </form>
        
        <div id="result-container"></div>
        
        <div class="mt-6 text-center">
            <button onclick="resetForm()" class="inline-block px-6 py-3 bg-gray-600 text-white font-bold rounded-xl hover:bg-gray-700 transition">
                🗑️ Yeni Fayl Yüklə
            </button>
        </div>
        
        <p class="text-center text-gray-500 mt-8 md:mt-10 text-xs md:text-sm">© 2025 AxtarGet – Azərbaycanın ən sürətlisi</p>
    </div>

    <script>
        let currentFile = null;

        function updateProgress(percent) {
            const progressFill = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            const progressBar = document.getElementById('progress-bar');
            
            progressBar.classList.remove('hidden');
            progressFill.style.width = percent + '%';
            progressText.textContent = percent + '%';
        }

        function showResult(message, isError = false, downloadUrl = null) {
            const resultContainer = document.getElementById('result-container');
            const bgClass = isError ? 'bg-red-500/20 border-red-400' : 'bg-green-500/20 border-green-400';
            const textClass = isError ? 'text-red-300' : 'text-green-300';
            
            let html = `
                <div class="mt-6 p-6 ${bgClass} border rounded-2xl text-center animate-pulse">
                    <p class="${textClass} text-xl font-bold mb-4">${message}</p>
            `;
            
            if (downloadUrl && !isError) {
                html += `
                    <a href="${downloadUrl}" class="inline-block px-6 py-3 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700 transition">
                        📥 WORD FAYLINI ENDİR (.docx)
                    </a>
                    <p class="text-gray-300 text-sm mt-3">Yeni fayl çevirmək üçün yuxarıdan başqa PDF seçə bilərsiniz</p>
                `;
            }
            
            html += '</div>';
            resultContainer.innerHTML = html;
        }

        function resetForm() {
            const fileInput = document.getElementById('file');
            const fileInfo = document.getElementById('file-info');
            const resultContainer = document.getElementById('result-container');
            const convertBtn = document.getElementById('convert-btn');
            const fileText = document.getElementById('file-text');
            const dropZone = document.getElementById('drop-zone');
            
            fileInput.value = '';
            fileInfo.classList.add('hidden');
            resultContainer.innerHTML = '';
            convertBtn.disabled = false;
            convertBtn.textContent = 'WORD-Ə ÇEVİR';
            convertBtn.classList.remove('opacity-50');
            fileText.textContent = 'PDF faylı seç və ya bura sürükle';
            dropZone.classList.remove('border-green-400');
            dropZone.classList.add('border-cyan-400');
            currentFile = null;
        }

        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file');
        const fileText = document.getElementById('file-text');
        const fileInfo = document.getElementById('file-info');
        const fileName = document.getElementById('filename');
        const fileSize = document.getElementById('filesize');
        const convertBtn = document.getElementById('convert-btn');

        // Fayl seçildikdə
        fileInput.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                handleFileSelection(this.files[0]);
            }
        });

        function handleFileSelection(file) {
            if (file.size > 10 * 1024 * 1024) {
                alert('Fayl ölçüsü 10MB-dan çox ola bilməz!');
                resetForm();
                return;
            }
            
            currentFile = file;
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
                handleFileSelection(files[0]);
            } else {
                alert('Yalnız PDF faylı qəbul edilir!');
            }
        }

        // Form göndərildikdə
        document.getElementById('conversion-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!currentFile) {
                alert('Zəhmət olmasa bir fayl seçin!');
                return;
            }

            const formData = new FormData();
            formData.append('pdf', currentFile);

            convertBtn.textContent = 'ÇEVİRİLİR...';
            convertBtn.disabled = true;
            convertBtn.classList.add('opacity-50');

            // Progress barı göstər
            updateProgress(10);

            try {
                const response = await fetch('/', {
                    method: 'POST',
                    body: formData
                });

                updateProgress(50);

                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                
                updateProgress(90);

                // Nəticəni yoxla
                const errorElement = doc.querySelector('.bg-red-500\\/20');
                const successElement = doc.querySelector('.bg-green-500\\/20');
                
                if (errorElement) {
                    const errorText = errorElement.querySelector('.text-red-300').textContent;
                    showResult(errorText, true);
                } else if (successElement) {
                    const successText = successElement.querySelector('.text-green-300').textContent;
                    const downloadLink = successElement.querySelector('a');
                    const downloadUrl = downloadLink ? downloadLink.href : null;
                    showResult(successText, false, downloadUrl);
                }

                updateProgress(100);

            } catch (error) {
                showResult('Şəbəkə xətası baş verdi!', true);
            } finally {
                setTimeout(() => {
                    convertBtn.textContent = 'WORD-Ə ÇEVİR';
                    convertBtn.disabled = false;
                    convertBtn.classList.remove('opacity-50');
                }, 2000);
            }
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
        # Sistem yükünü yoxla
        cpu_percent, memory_percent = optimizer.get_system_load()
        
        if cpu_percent > 80 or memory_percent > 85:
            return render_template_string(
                HTML, 
                error="❌ Sistem hazırda məşğuldur. Zəhmət olmasa bir neçə dəqiqə sonra yenidən cəhd edin."
            )
        
        # Eyni anda çevirmə limitini yoxla
        if not optimizer.can_start_conversion():
            return render_template_string(
                HTML, 
                error="❌ Sistem hazırda məşğuldur. Zəhmət olmasa gözləyin."
            )
        
        try:
            pdf_file = request.files["pdf"]
            if pdf_file and pdf_file.filename.endswith(".pdf"):
                
                # Fayl ölçüsünü yoxla
                pdf_file.seek(0, 2)  # Sonuna get
                file_size = pdf_file.tell()
                pdf_file.seek(0)  # Əvvələ qayıt
                
                if file_size > 10 * 1024 * 1024:  # 10MB limit
                    optimizer.conversion_finished()
                    return render_template_string(
                        HTML, 
                        error="❌ Fayl ölçüsü 10MB-dan çox ola bilməz!"
                    )
                
                # Unikal fayl adı yarat
                unique_id = str(uuid.uuid4())
                pdf_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.pdf")
                docx_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.docx")
                
                # PDF faylını yadda saxla
                pdf_file.save(pdf_path)
                
                # PDF-dən DOCX-ə çevir
                success = convert_pdf_to_docx(pdf_path, docx_path)
                
                # Köhnə PDF faylını sil
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                
                if success:
                    filename = f"{unique_id}.docx"
                    optimizer.conversion_finished()
                    return render_template_string(
                        HTML, 
                        result="✅ PDF uğurla Word sənədinə çevrildi!", 
                        filename=filename
                    )
                else:
                    optimizer.conversion_finished()
                    return render_template_string(
                        HTML, 
                        error="❌ PDF çevrilməsi zamanı xəta baş verdi!"
                    )
                
            else:
                optimizer.conversion_finished()
                return render_template_string(
                    HTML, 
                    error="❌ Zəhmət olmasa etibarlı PDF faylı seçin!"
                )
                
        except Exception as e:
            optimizer.conversion_finished()
            # Xəta baş verərsə, faylları təmizlə
            for file_path in [pdf_path, docx_path]:
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
            
            return render_template_string(
                HTML, 
                error=f"❌ Xəta: {str(e)}"
            )
    
    return render_template_string(HTML)

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        # Təhlükəsiz fayl adı
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
