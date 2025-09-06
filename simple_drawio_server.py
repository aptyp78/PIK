#!/usr/bin/env python3
"""
Simple Draw.io File Server
==========================

Простой HTTP сервер для раздачи Draw.io файлов
"""

import http.server
import socketserver
import webbrowser
import os
import threading
import time
from pathlib import Path

class DrawIOHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик для Draw.io файлов"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path.cwd()), **kwargs)
    
    def end_headers(self):
        # Добавляем CORS заголовки для работы с Draw.io
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/':
            # Главная страница с файлами
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = self.create_file_list()
            self.wfile.write(html_content.encode('utf-8'))
            
        elif self.path.startswith('/download/'):
            # Скачивание файла
            filename = self.path.replace('/download/', '')
            file_path = Path('output/drawio') / filename
            
            if file_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, f'File {filename} not found')
                
        elif self.path.startswith('/view/'):
            # Просмотр файла
            filename = self.path.replace('/view/', '')
            file_path = Path('output/drawio') / filename
            
            if file_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'application/xml')
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, f'File {filename} not found')
        else:
            super().do_GET()
    
    def create_file_list(self):
        """Создает HTML список файлов"""
        drawio_dir = Path('output/drawio')
        files = list(drawio_dir.glob('*.drawio')) if drawio_dir.exists() else []
        
        # Информация о файлах
        file_info = {
            "pik_20250906_192036_2ed9d0bf_diagram.drawio": {
                "name": "TOUCHPOINTS",
                "type": "Business Model Canvas",
                "elements": "545 элементов",
                "size": "1.2MB"
            },
            "pik_20250906_192040_9f20687b_diagram.drawio": {
                "name": "MOTIVATION", 
                "type": "Ecosystem Forces",
                "elements": "346 элементов",
                "size": "784KB"
            },
            "pik_20250906_192042_43f6d2f9_diagram.drawio": {
                "name": "SUSTAINABILITY",
                "type": "NFX Reinforcement",
                "elements": "80 элементов",
                "size": "76KB"
            },
            "pik_20250906_192045_fab9493e_diagram.drawio": {
                "name": "ENVIRONMENT",
                "type": "Forces Scan", 
                "elements": "191 элемент",
                "size": "408KB"
            },
            "pik_20250906_192047_d4b8a70e_diagram.drawio": {
                "name": "CONSUMERS",
                "type": "Value Network",
                "elements": "71 элемент",
                "size": "64KB"
            }
        }
        
        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PIK Draw.io Files - Local Server</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .content {
            padding: 40px;
        }
        
        .instructions {
            background: #e7f3ff;
            border-left: 4px solid #4facfe;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 0 8px 8px 0;
        }
        
        .file-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            border: 1px solid #e9ecef;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .file-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .file-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .file-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        
        .file-type {
            font-size: 0.9em;
            color: #666;
            background: #e9ecef;
            padding: 4px 8px;
            border-radius: 12px;
        }
        
        .file-details {
            color: #666;
            margin-bottom: 15px;
        }
        
        .file-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.9em;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-1px);
        }
        
        .btn.primary {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .btn.success {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        }
        
        .status {
            color: #28a745;
            font-weight: bold;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 PIK Draw.io Files</h1>
            <p>Локальный сервер для работы с файлами</p>
        </div>
        
        <div class="content">
            <div class="instructions">
                <h3>🚀 Как открыть файлы в Draw.io:</h3>
                <ol>
                    <li><strong>Скачайте</strong> нужный файл кнопкой "💾 Скачать"</li>
                    <li><strong>Откройте</strong> <a href="https://app.diagrams.net/?splash=0&libs=general" target="_blank">Draw.io</a> в новой вкладке</li>
                    <li><strong>Нажмите</strong> "Open Existing Diagram" → "Device"</li>
                    <li><strong>Выберите</strong> скачанный файл</li>
                </ol>
                <p><strong>✅ Работает без авторизации Google!</strong></p>
            </div>
"""
        
        for file_path in files:
            filename = file_path.name
            info = file_info.get(filename, {
                "name": filename.replace('.drawio', ''),
                "type": "PIK Framework",
                "elements": "Неизвестно",
                "size": f"{file_path.stat().st_size // 1024}KB"
            })
            
            html += f"""
            <div class="file-card">
                <div class="file-header">
                    <div class="file-title">🎯 {info['name']}</div>
                    <div class="file-type">{info['type']}</div>
                </div>
                <div class="file-details">
                    📊 {info['elements']} • 💾 {info['size']} • 📄 {filename}
                </div>
                <div class="file-actions">
                    <a href="/download/{filename}" class="btn success">💾 Скачать</a>
                    <a href="https://app.diagrams.net/?splash=0&libs=general" target="_blank" class="btn primary">🚀 Открыть Draw.io</a>
                    <button class="btn" onclick="copyInstructions('{filename}')">📋 Инструкция</button>
                </div>
            </div>
"""
        
        html += f"""
            <div class="status">
                ✅ Найдено {len(files)} Draw.io файлов
                <br>🌐 Сервер запущен на http://localhost:8080
            </div>
        </div>
    </div>
    
    <script>
        function copyInstructions(filename) {{
            const instructions = `Инструкция для файла ${{filename}}:

1. Скачайте файл: http://localhost:8080/download/${{filename}}
2. Откройте Draw.io: https://app.diagrams.net/?splash=0
3. Нажмите "Open Existing Diagram" → "Device"
4. Выберите скачанный файл
5. Готово! ✅`;
            
            navigator.clipboard.writeText(instructions).then(() => {{
                alert('📋 Инструкция скопирована в буфер обмена!');
            }});
        }}
        
        // Автоматически открываем Draw.io при первом заходе
        if (!sessionStorage.getItem('drawio_opened')) {{
            sessionStorage.setItem('drawio_opened', 'true');
            setTimeout(() => {{
                if (confirm('🚀 Открыть Draw.io в новой вкладке?')) {{
                    window.open('https://app.diagrams.net/?splash=0&libs=general', '_blank');
                }}
            }}, 1000);
        }}
    </script>
</body>
</html>"""
        
        return html

def start_server(port=8080):
    """Запускает сервер"""
    print(f"🌐 Запуск сервера на порту {port}...")
    
    try:
        with socketserver.TCPServer(("", port), DrawIOHandler) as httpd:
            server_url = f"http://localhost:{port}"
            print(f"✅ Сервер запущен: {server_url}")
            print(f"📁 Раздача файлов из: {Path.cwd()}")
            print("🛑 Для остановки нажмите Ctrl+C")
            
            # Открываем браузер через секунду
            def open_browser():
                time.sleep(1)
                webbrowser.open(server_url)
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Порт {port} уже используется")
            print("💡 Попробуйте другой порт или остановите другой сервер")
        else:
            print(f"❌ Ошибка: {e}")

def main():
    """Главная функция"""
    print("""
🌐 PIK Draw.io File Server
==========================

Локальный HTTP сервер для работы с Draw.io файлами
без необходимости авторизации в Google.
""")
    
    # Проверяем наличие файлов
    drawio_dir = Path('output/drawio')
    if not drawio_dir.exists():
        print("❌ Папка output/drawio не найдена")
        return
    
    files = list(drawio_dir.glob('*.drawio'))
    if not files:
        print("❌ Draw.io файлы не найдены")
        return
    
    print(f"📁 Найдено {len(files)} Draw.io файлов")
    
    # Запускаем сервер
    start_server()

if __name__ == "__main__":
    main()
