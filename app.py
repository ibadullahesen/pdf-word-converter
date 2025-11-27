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
                    <p class="text-xl text-cyan-300 font-bold">PDF faylı seç və ya bura sürükle</p>
                    <p class="text-sm text-gray-400 mt-2">Drag & drop dəstəklənir</p>
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

    <script>
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file');

        // Drag & drop dəstəyi
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
            dropZone.classList.add('bg-cyan-500/20');
        }

        function unhighlight(e) {
            dropZone.classList.remove('bg-cyan-500/20');
        }

        dropZone.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0 && files[0].type === 'application/pdf') {
                fileInput.files = files;
                // Form-u avtomatik submit et (istəyirsənsə)
                document.querySelector('form').submit();
            } else {
                alert('Yalnız PDF faylı qəbul edilir!');
            }
        }
    </script>
</body>
</html>
"""
