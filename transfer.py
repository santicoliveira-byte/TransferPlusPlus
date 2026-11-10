#!/usr/bin/env python3
"""
Transfer++ : High-Speed PC-to-PC LAN File Transfer
Simple, secure, and fast file sharing over local network without cloud limits.
Zero external dependencies required (Pure Python 3).
"""

import os
import sys
import socket
import threading
import json
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 7777
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RECEIVE_DIR = os.path.join(BASE_DIR, "received")
os.makedirs(RECEIVE_DIR, exist_ok=True)

def get_local_ip():
    """Finds the primary local LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def format_size(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transfer++ | PC-to-PC LAN Transfer</title>
    <style>
        :root {
            --bg: #0b0e14;
            --card: #131722;
            --card-border: #202738;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.2);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --success: #10b981;
            --danger: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }
        .header {
            width: 100%;
            max-width: 900px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--card-border);
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo {
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            color: #fff;
            font-weight: 800;
            font-size: 18px;
            padding: 6px 14px;
            border-radius: 8px;
            box-shadow: 0 0 15px var(--accent-glow);
        }
        .title h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }
        .title p { font-size: 13px; color: var(--text-muted); }
        .pill {
            background: #1e293b;
            border: 1px solid #334155;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success); }
        .main-container {
            width: 100%;
            max-width: 900px;
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
        }
        .card {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 24px;
        }
        .dropzone {
            border: 2px dashed #334155;
            border-radius: 10px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background: rgba(19, 23, 34, 0.6);
        }
        .dropzone:hover, .dropzone.dragover {
            border-color: var(--accent);
            background: var(--accent-glow);
        }
        .dropzone-icon {
            font-size: 40px;
            margin-bottom: 12px;
            display: block;
        }
        .dropzone h3 { font-size: 16px; margin-bottom: 6px; }
        .dropzone p { font-size: 13px; color: var(--text-muted); }
        input[type="file"] { display: none; }
        .progress-box {
            margin-top: 20px;
            display: none;
        }
        .progress-header {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            margin-bottom: 8px;
        }
        .progress-bar-bg {
            background: #1e293b;
            border-radius: 6px;
            height: 10px;
            width: 100%;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #0284c7, #38bdf8);
            border-radius: 6px;
            transition: width 0.15s ease;
        }
        .files-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .files-header h2 { font-size: 16px; font-weight: 600; }
        .file-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: #0f131c;
            border: 1px solid var(--card-border);
            border-radius: 8px;
        }
        .file-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .file-name { font-size: 14px; font-weight: 500; }
        .file-size { font-size: 12px; color: var(--text-muted); }
        .btn-dl {
            background: #1e293b;
            color: var(--accent);
            text-decoration: none;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid #334155;
            transition: all 0.2s;
        }
        .btn-dl:hover {
            background: var(--accent);
            color: #0b0e14;
        }
        .empty-msg {
            color: var(--text-muted);
            text-align: center;
            padding: 24px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="brand">
            <div class="logo">T++</div>
            <div class="title">
                <h1>Transfer++</h1>
                <p>Transferência Direta de Ficheiros PC para PC</p>
            </div>
        </div>
        <div class="pill">
            <div class="dot"></div>
            <span id="host-ip">Conectado na LAN</span>
        </div>
    </div>

    <div class="main-container">
        <!-- Upload Card -->
        <div class="card">
            <div class="dropzone" id="dropzone" onclick="document.getElementById('file-input').click()">
                <span class="dropzone-icon">📁</span>
                <h3>Arrasta ficheiros para aqui ou clica para procurar</h3>
                <p>Envia diretamente para qualquer PC conectado na tua rede local sem limites de tamanho</p>
            </div>
            <input type="file" id="file-input" multiple onchange="handleFiles(this.files)">

            <div class="progress-box" id="progress-box">
                <div class="progress-header">
                    <span id="progress-filename">A transferir...</span>
                    <span id="progress-pct">0%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" id="progress-fill"></div>
                </div>
            </div>
        </div>

        <!-- Files List Card -->
        <div class="card">
            <div class="files-header">
                <h2>Ficheiros Recebidos</h2>
                <button onclick="loadFiles()" style="background:none; border:none; color:var(--accent); cursor:pointer; font-size:13px;">Atualizar Lista</button>
            </div>
            <div class="file-list" id="file-list">
                <div class="empty-msg">Nenhum ficheiro recebido ainda.</div>
            </div>
        </div>
    </div>

    <script>
        const dropzone = document.getElementById('dropzone');
        const progressBox = document.getElementById('progress-box');
        const progressFill = document.getElementById('progress-fill');
        const progressPct = document.getElementById('progress-pct');
        const progressFilename = document.getElementById('progress-filename');

        dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
        dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });

        function handleFiles(files) {
            if (!files || files.length === 0) return;
            uploadFile(files[0]);
        }

        function uploadFile(file) {
            progressBox.style.display = 'block';
            progressFilename.innerText = file.name;
            progressFill.style.width = '0%';
            progressPct.innerText = '0%';

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/upload', true);
            xhr.setRequestHeader('X-Filename', encodeURIComponent(file.name));

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const pct = Math.round((e.loaded / e.total) * 100);
                    progressFill.style.width = pct + '%';
                    progressPct.innerText = pct + '%';
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200) {
                    progressFilename.innerText = 'Transferência concluída: ' + file.name;
                    progressFill.style.background = '#10b981';
                    loadFiles();
                    setTimeout(() => { progressBox.style.display = 'none'; }, 3000);
                } else {
                    alert('Erro no envio do ficheiro!');
                }
            };

            xhr.send(file);
        }

        function loadFiles() {
            fetch('/api/files')
                .then(res => res.json())
                .then(data => {
                    const list = document.getElementById('file-list');
                    if (!data || data.length === 0) {
                        list.innerHTML = '<div class="empty-msg">Nenhum ficheiro recebido ainda.</div>';
                        return;
                    }
                    list.innerHTML = '';
                    data.forEach(f => {
                        const div = document.createElement('div');
                        div.className = 'file-item';
                        div.innerHTML = `
                            <div class="file-info">
                                <div class="file-name">${f.name}</div>
                                <div class="file-size">${f.size}</div>
                            </div>
                            <a class="btn-dl" href="/api/download/${encodeURIComponent(f.name)}" download>Descarregar</a>
                        `;
                        list.appendChild(div);
                    });
                });
        }

        // Auto load files on open
        loadFiles();
    </script>
</body>
</html>
"""

class TransferHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging
        sys.stdout.write(f"[*] {self.address_string()} - {format % args}\n")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return

        elif path == "/api/files":
            files_list = []
            if os.path.exists(RECEIVE_DIR):
                for fname in os.listdir(RECEIVE_DIR):
                    fpath = os.path.join(RECEIVE_DIR, fname)
                    if os.path.isfile(fpath):
                        sz = os.path.getsize(fpath)
                        files_list.append({
                            "name": fname,
                            "size": format_size(sz),
                            "bytes": sz
                        })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(files_list).encode("utf-8"))
            return

        elif path.startswith("/api/download/"):
            fname = urllib.parse.unquote(path[len("/api/download/"):])
            fpath = os.path.join(RECEIVE_DIR, fname)
            if os.path.isfile(fpath):
                fsize = os.path.getsize(fpath)
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.send_header("Content-Length", str(fsize))
                self.end_headers()

                with open(fpath, "rb") as f:
                    while chunk := f.read(64 * 1024):
                        self.wfile.write(chunk)
                return
            else:
                self.send_error(404, "Ficheiro nao encontrado.")
                return

        self.send_error(404, "Pagina nao encontrada.")

    def do_POST(self):
        if self.path == "/api/upload":
            raw_filename = self.headers.get("X-Filename", "transfer_file.bin")
            filename = urllib.parse.unquote(raw_filename)
            filename = os.path.basename(filename) # Prevent directory traversal

            content_len = int(self.headers.get("Content-Length", 0))
            dest_path = os.path.join(RECEIVE_DIR, filename)

            print(f"[+] Recebendo ficheiro: {filename} ({format_size(content_len)})")
            remaining = content_len

            with open(dest_path, "wb") as f:
                while remaining > 0:
                    read_size = min(remaining, 64 * 1024)
                    chunk = self.rfile.read(read_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)

            print(f"[+] Guardado com sucesso em: {dest_path}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            return

        self.send_error(404, "Endpoint desconhecido.")


def main():
    local_ip = get_local_ip()
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, TransferHandler)

    print("=" * 60)
    print("           TRANSFER++  |  PC-TO-PC FILE TRANSFER")
    print("=" * 60)
    print(f"[+] Servidor ativo!")
    print(f"[+] Acede neste PC ou em qualquer outro PC da rede atraves de:")
    print(f"    --> http://{local_ip}:{PORT}")
    print(f"[+] Pasta de rececao: {RECEIVE_DIR}")
    print("=" * 60)
    print("[*] A abrir o browser automaticamente...")
    print("[*] Pressiona Ctrl+C para encerrar.")

    # Automatically open web UI in default browser
    threading.Timer(0.6, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Servidor encerrado.")
        httpd.server_close()

if __name__ == "__main__":
    main()
