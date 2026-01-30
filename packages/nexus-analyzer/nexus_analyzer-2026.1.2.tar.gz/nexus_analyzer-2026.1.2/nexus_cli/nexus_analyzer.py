import os
import re
import ast
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

# --- YAPILANDIRMA ---

# Taranmayacak Klasörler
EXCLUDE_DIRS = {
    'OLDs', 'Others', 'node_modules', 'venv', '.git', '__pycache__',
    '.idea', '.vscode', 'build', 'dist', 'tmp', 'temp'
}

IGNORE_TERMS = {
    'self', 'def', 'class', 'return', 'import', 'from', 'async', 'await',
    'print', 'true', 'false', 'none', 'null', 'if', 'else', 'try', 'except',
    'str', 'int', 'float', 'bool', 'list', 'dict', 'app', 'router', 'req', 'res',
    'get', 'post', 'put', 'patch', 'delete', 'message', 'hello', 'world', 'root', 'data',
    'pass', 'break', 'continue', 'lambda', 'args', 'kwargs', 'init', 'main', 'client'
}

FILE_SIGS = {
    'Python': {'.py'},
    'Go': {'.go', 'go.mod'},
    'Lua': {'.lua'},
    'Web': {'.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.less'},
    'Config': {'.env', '.yaml', '.yml', '.toml', '.conf', 'Dockerfile', 'Makefile', 'requirements.txt', '.ini', '.xml'},
    'Data': {'.sql', '.db', '.sqlite', '.csv', '.json'}
}


class NexusAnalyzer:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir).resolve()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.report_dir = self.root_dir / f"RAPOR_NEXUS_{timestamp}"

        self.inventory = {
            "endpoints": [],  # {method, url, params, file, line}
            "outgoing_requests": [],  # {method, url, auth, params, file, line}
            "tech_stack": set(),
            "infra_services": [],  # {type, name, file, line}
            "db_interactions": set(),
            "env_vars": set(),
            "connections": [],  # {type, value, file, line}
            "files_scanned": defaultdict(int),
            "directory_stats": Counter(),
            "file_tree": [],
            "project_type": "Bilinmiyor",

            "frontend": {
                "pages": [],
                "scripts": set(),
                "styles": set(),
                "api_calls": []
            },

            "features_detailed": [],

            "metadata": {
                "python_version": None,
                "app_title": "Bilinmiyor",
                "app_version": None,
                "async_count": 0,
                "sync_count": 0
            }
        }

        self.patterns = {
            "docker_image": re.compile(r'(?:image:|FROM)\s+([a-zA-Z0-9\/\-\:\.]+)'),
            "docker_service": re.compile(r'container_name:\s*([a-zA-Z0-9\-\_]+)'),
            "nginx_listen": re.compile(r'listen\s+(\d+);'),
            "nginx_proxy": re.compile(r'proxy_pass\s+(http[s]?://[a-zA-Z0-9\:\-\_\.]+);'),
            "env_get": re.compile(r'os\.getenv\s*\(\s*["\']([A-Z0-9_]+)["\']'),
            "sql_table": re.compile(r'CREATE TABLE\s+["`]?([a-zA-Z0-9_]+)["`]?'),
            "python_ver": re.compile(r'(?:FROM|image:)\s+python:(\d+\.\d+)'),
            "conn_uri": re.compile(r'(mongodb|postgres|postgresql|mysql|redis|rediss|amqp|rabbitmq|dragonfly|valkey):\/\/[^\s"\']+'),
            "js_fetch": re.compile(r'fetch\s*\(\s*[`\'"]([^`\'"]+)[`\'"]'),
            "js_ws": re.compile(r'new\s+WebSocket\('),

            "oauth2": (re.compile(r'OAuth2PasswordBearer'), "Auth Flow", "OAuth2 Password Flow"),
            "rate_limit": (re.compile(r'(SlowAPI|Limiter|RateLimit|CheckRequestLimit)', re.IGNORECASE), "Rate Limiting", "Kod İçi Limit"),
            "celery": (re.compile(r'@\w+\.task'), "Arka Plan", "Celery Task"),
            "mqtt": (re.compile(r'(mqtt\.Client|MqttClient)'), "Mesajlaşma", "MQTT Client"),
            "sse": (re.compile(r'text/event-stream'), "Real-Time", "SSE Stream"),
            "gateway": (re.compile(r'(gateway|reverse_proxy|upstream)', re.IGNORECASE), "Mimari", "Gateway Pattern")
        }

    def analyze(self):
        print(f"🚀 Nexus Analiz (v10.4 - Final Fix) Başlıyor: {self.root_dir}")

        if not self.report_dir.exists():
            os.makedirs(self.report_dir)

        script_name = os.path.basename(__file__)
        MAX_TREE_LINES = 2000

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith("muslu_NEXUS") and not d.startswith("RAPOR")]

            rel_path = self._get_rel_path(Path(root))
            if rel_path == ".": rel_path = ""

            level = root.replace(str(self.root_dir), '').count(os.sep)
            indent = ' ' * 4 * level

            self.inventory["file_tree"].append(f"{indent}📂 {os.path.basename(root)}/")

            for file in files:
                if file == script_name or file.startswith("muslu_NEXUS"): continue

                file_path = Path(root) / file
                dir_key = rel_path if rel_path else "./"
                self.inventory["directory_stats"][dir_key] += 1

                if len(self.inventory["file_tree"]) < MAX_TREE_LINES:
                    self.inventory["file_tree"].append(f"{indent}    📄 {file}")

                self._dispatch_analysis(file_path)

        self._infer_architecture()
        self._generate_reports()
        print(f"✅ Raporlar Oluşturuldu: {self.report_dir}")

    def _dispatch_analysis(self, path):
        ext = path.suffix.lower()
        self.inventory["files_scanned"][ext] += 1

        if ext == '.py':
            self._analyze_python(path)
        elif ext in FILE_SIGS['Web']:
            self._analyze_web(path)
        elif ext in FILE_SIGS['Config'] or path.name == 'Dockerfile':
            self._analyze_infra_config(path)
        elif ext in FILE_SIGS['Data']:
            pass

    def _read_lines(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.readlines()
        except:
            return []

    def _get_rel_path(self, path):
        try:
            return str(path.relative_to(self.root_dir))
        except ValueError:
            return str(path)

    def _add_feature(self, category, name, reason, file, line):
        self.inventory["features_detailed"].append({
            "category": category,
            "name": name,
            "reason": reason,
            "file": file,
            "line": line
        })

    def _extract_params_from_function(self, node):
        params = []
        for arg in node.args.args:
            if arg.arg in ['self', 'cls', 'request']: continue
            annotation = ""
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    annotation = f": {arg.annotation.id}"
                elif isinstance(arg.annotation, ast.Subscript):
                    try:
                        annotation = f": {ast.unparse(arg.annotation)}"
                    except:
                        annotation = ": Complex"
            params.append(f"{arg.arg}{annotation}")
        return ", ".join(params)

    def _extract_outgoing_params(self, node):
        info = []
        for kw in node.keywords:
            if kw.arg in ['params', 'json', 'data', 'headers']:
                val_type = "Var"
                if isinstance(kw.value, ast.Dict):
                    keys = [k.value for k in kw.value.keys if isinstance(k, ast.Constant)]
                    val_type = f"{{{', '.join(str(k) for k in keys)}}}"
                elif isinstance(kw.value, ast.Name):
                    val_type = f"${kw.value.id}"
                info.append(f"{kw.arg}={val_type}")
        return ", ".join(info)

    def _analyze_python(self, path):
        lines = self._read_lines(path)
        content = "".join(lines)
        if not content: return

        file_display = self._get_rel_path(path)

        for i, line in enumerate(lines, 1):
            line_str = line.strip()

            for key, val in self.patterns.items():
                if isinstance(val, tuple):
                    pattern, cat, name = val
                    if pattern.search(line_str):
                        if not any(f['file'] == file_display and f['line'] == i and f['name'] == name for f in self.inventory["features_detailed"]):
                            self._add_feature(cat, name, f"Regex: {key}", file_display, i)

            conn_match = self.patterns["conn_uri"].search(line_str)
            if conn_match:
                masked = re.sub(r'(://[^:]+):([^@]+)@', r'\1:***@', conn_match.group(0))
                self.inventory["connections"].append({"type": "URI", "value": masked, "file": file_display, "line": i})

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "FastAPI":
                    for k in node.keywords:
                        if k.arg == "title" and isinstance(k.value, ast.Constant):
                            self.inventory["metadata"]["app_title"] = k.value.value
                        elif k.arg == "version" and isinstance(k.value, ast.Constant):
                            self.inventory["metadata"]["app_version"] = k.value.value

                if isinstance(node, ast.AsyncFunctionDef):
                    self.inventory["metadata"]["async_count"] += 1
                elif isinstance(node, ast.FunctionDef):
                    self.inventory["metadata"]["sync_count"] += 1

                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_params = self._extract_params_from_function(node)

                    for arg in node.args.args:
                        if arg.annotation and isinstance(arg.annotation, ast.Name):
                            if arg.annotation.id == "WebSocket":
                                self._add_feature("Real-Time", "WebSocket Endpoint", "Argüman Tespiti", file_display, node.lineno)
                            if arg.annotation.id == "BackgroundTasks":
                                self._add_feature("Arka Plan", "FastAPI BackgroundTasks", "Argüman Tespiti", file_display, node.lineno)

                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            for k in decorator.keywords:
                                if k.arg == "dependencies":
                                    dep_str = ast.get_source_segment(content, k.value)
                                    if "role" in dep_str or "admin" in dep_str:
                                        self._add_feature("Güvenlik", "RBAC (Rol Tabanlı)", "Decorator Dependencies", file_display, node.lineno)

                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            d_attr = decorator.func.attr
                            if d_attr in ['get', 'post', 'put', 'delete', 'patch', 'websocket']:
                                method = "WS" if d_attr == "websocket" else d_attr.upper()
                                url = "/"
                                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                    url = decorator.args[0].value

                                self.inventory["endpoints"].append({
                                    "method": method,
                                    "url": url,
                                    "params": func_params,
                                    "file": file_display,
                                    "line": node.lineno
                                })

                if isinstance(node, ast.Call):
                    func_obj, func_attr = None, None
                    if isinstance(node.func, ast.Attribute):
                        func_attr = node.func.attr
                        if isinstance(node.func.value, ast.Name):
                            func_obj = node.func.value.id

                    if func_attr and func_obj:
                        if func_attr in ['get', 'post', 'put', 'delete', 'patch', 'request']:
                            lower_obj = func_obj.lower()

                            # Blacklist
                            blacklist = ['redis', 'mongo', 'db', 'repo', 'data', 'json', 'dict', 'list', 'str', 'int', 'config', 'settings', 'os', 'sys', 'env']

                            if not any(x in lower_obj for x in blacklist):
                                # Whitelist GÜNCELLENDİ: 'request' yerine 'requests'
                                whitelist = ['requests', 'httpx', 'client', 'http', 'session', 'fetch', 'axios']
                                if any(x in lower_obj for x in whitelist):
                                    req_url = "Dynamic"
                                    if node.args and isinstance(node.args[0], ast.Constant):
                                        req_url = node.args[0].value

                                    auth_info = "-"
                                    for kw in node.keywords:
                                        if kw.arg == "auth":
                                            auth_info = "Auth"
                                        elif kw.arg == "headers":
                                            auth_info = "Headers"

                                    out_params = self._extract_outgoing_params(node)

                                    self.inventory["outgoing_requests"].append({
                                        "method": func_attr.upper(),
                                        "url": req_url,
                                        "auth": auth_info,
                                        "params": out_params,
                                        "file": file_display,
                                        "line": node.lineno
                                    })

        except:
            pass

    def _analyze_infra_config(self, path):
        lines = self._read_lines(path)
        file_display = self._get_rel_path(path)

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'): continue

            conn_match = self.patterns["conn_uri"].search(line)
            if conn_match:
                masked = re.sub(r'(://[^:]+):([^@]+)@', r'\1:***@', conn_match.group(0))
                self.inventory["connections"].append({"type": "URI", "value": masked, "file": file_display, "line": i})

            if '=' in line and any(k in line.lower() for k in ['_host', '_port', '_url', '_db']):
                if 'secret' not in line.lower():
                    self.inventory["connections"].append({"type": "Config Key", "value": line, "file": file_display, "line": i})

            img_match = self.patterns["docker_image"].search(line)
            if img_match:
                img_name = img_match.group(1)
                self.inventory["infra_services"].append({"type": "Container Image", "name": img_name, "file": file_display, "line": i})
                if "redis" in img_name or "dragonfly" in img_name:
                    self._add_feature("Altyapı", "Rate Limiting / Cache", f"Image: {img_name}", file_display, i)

            svc_match = self.patterns["docker_service"].search(line)
            if svc_match:
                self.inventory["infra_services"].append({"type": "Docker Service", "name": svc_match.group(1), "file": file_display, "line": i})

            if path.suffix in ['.yaml', '.yml'] and line.endswith(':'):
                if re.match(r'^\s{2}[a-zA-Z0-9\-\_]+:$', line) and 'services:' not in line:
                    svc_name = line.strip()[:-1]
                    self.inventory["infra_services"].append({"type": "Service Key", "name": svc_name, "file": file_display, "line": i})

            nginx_port = self.patterns["nginx_listen"].search(line)
            if nginx_port:
                self.inventory["infra_services"].append({"type": "Nginx", "name": f"Port {nginx_port.group(1)}", "file": file_display, "line": i})

            if self.patterns["gateway"][0].search(line):
                self._add_feature("Mimari", "Gateway Pattern", "Config Keyword", file_display, i)

    def _analyze_web(self, path):
        lines = self._read_lines(path)
        file_display = self._get_rel_path(path)

        if path.suffix in ['.js', '.ts', '.jsx']:
            for i, line in enumerate(lines, 1):
                if "fetch(" in line or "axios" in line:
                    match = self.patterns["js_fetch"].search(line)
                    url = match.group(1) if match else "Dynamic URL"
                    self.inventory["frontend"]["api_calls"].append(f"Line {i}: {url} ({file_display})")

    def _infer_architecture(self):
        techs = str(self.inventory["tech_stack"]).lower()
        has_fe = bool(self.inventory["frontend"]["api_calls"])
        self.inventory["project_type"] = "Full-Stack Web App" if has_fe else "Backend API"

    def _write_md(self, filename, content_list):
        filepath = self.report_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_list))

    def _sort_list(self, data_list):
        return sorted(data_list, key=lambda x: (os.path.dirname(x['file']), os.path.basename(x['file']), x.get('line', 0)))

    def _generate_reports(self):
        meta = self.inventory["metadata"]
        summary = [
            f"# 🧬 Proje Kimliği ve Özet",
            f"**Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            f"**Mimari Türü:** `{self.inventory['project_type']}`",
            "",
            "## 📌 Uygulama Bilgileri",
            f"- **Uygulama Adı:** {meta['app_title']}",
            f"- **Versiyon:** v{meta['app_version']}",
            f"- **Python Sürümü:** {meta['python_version'] or 'Tespit Edilemedi'}",
            f"- **Toplam Endpoint:** {len(self.inventory['endpoints'])}",
            "",
            "## 📊 Dosya Türü Dağılımı",
            "| Uzantı | Sayı |",
            "|---|---|",
        ]
        for ext, count in self.inventory["files_scanned"].items():
            summary.append(f"| `{ext}` | {count} |")

        summary.append("")
        summary.append("## 📂 Klasör İstatistikleri")
        summary.append("| Klasör | Dosya Sayısı |")  # HATA DÜZELTİLDİ: append tek argüman
        summary.append("|---|---|")
        for d, c in self.inventory["directory_stats"].most_common():
            summary.append(f"| `{d}` | {c} |")

        self._write_md("01_Ozet_ve_Kimlik.md", summary)

        # 2. ENDPOINTLER
        endpoints_doc = [
            "# 🔗 API Endpointleri (Gelen)",
            "Kod içinde tanımlanmış (Gelen) istek karşılayıcılar:",
            "",
            "| Metod | URL | Parametreler | Dosya | Satır |",
            "|---|---|---|---|---|",
        ]
        sorted_eps = self._sort_list(self.inventory["endpoints"])
        if sorted_eps:
            for ep in sorted_eps:
                param_str = f"`{ep['params']}`" if ep['params'] else "-"
                endpoints_doc.append(f"| **{ep['method']}** | `{ep['url']}` | {param_str} | `{ep['file']}` | {ep['line']} |")
        else:
            endpoints_doc.append("| - | Bulunamadı | - | - | - |")

        self._write_md("02_API_Endpointleri.md", endpoints_doc)

        # 3. DIŞ İSTEKLER
        outgoing_doc = [
            "# 📡 Dış Servis İstekleri (Outgoing)",
            "Backend tarafından dış dünyaya atılan istekler:",
            "",
            "| Metod | URL / Hedef | Auth | Parametreler | Dosya | Satır |",
            "|---|---|---|---|---|---|",
        ]
        sorted_out = self._sort_list(self.inventory["outgoing_requests"])
        if sorted_out:
            for req in sorted_out:
                auth_str = req['auth'] if req['auth'] != "-" else "-"
                param_str = f"`{req['params']}`" if req['params'] else "-"
                outgoing_doc.append(f"| {req['method']} | `{req['url']}` | {auth_str} | {param_str} | `{req['file']}` | {req['line']} |")
        else:
            outgoing_doc.append("| - | Dış istek yok | - | - | - | - |")

        self._write_md("03_Dis_Istekler.md", outgoing_doc)

        # 4. ÖZELLİKLER
        features_doc = [
            "# ⚡ Tespit Edilen Gelişmiş Özellikler",
            "Bu özelliklerin neden tespit edildiğine dair kanıtlar:",
            "",
            "| Kategori | Özellik Adı | Tespit Sebebi (Kanıt) | Dosya | Satır |",
            "|---|---|---|---|---|",
        ]
        sorted_feats = self._sort_list(self.inventory["features_detailed"])
        if sorted_feats:
            for feat in sorted_feats:
                features_doc.append(f"| {feat['category']} | **{feat['name']}** | {feat['reason']} | `{feat['file']}` | {feat['line']} |")
        else:
            features_doc.append("| - | Özellik yok | - | - | - |")

        self._write_md("04_Gelismis_Ozellikler.md", features_doc)

        # 5. ALTYAPI
        infra_doc = [
            "# 🏗️ Altyapı ve Bağlantılar",
            "",
            "## 🐳 Docker ve Servisler",
            "| Tip | İsim / Değer | Dosya | Satır |",
            "|---|---|---|---|",
        ]
        sorted_infra = self._sort_list(self.inventory["infra_services"])
        for inf in sorted_infra:
            infra_doc.append(f"| {inf['type']} | `{inf['name']}` | `{inf['file']}` | {inf['line']} |")

        infra_doc.append("\n## 🔗 Bağlantı Stringleri (Connections)")
        infra_doc.append("| Tip | Değer (Maskelenmiş) | Dosya | Satır |")
        infra_doc.append("|---|---|---|---|")
        sorted_conn = self._sort_list(self.inventory["connections"])
        for conn in sorted_conn:
            infra_doc.append(f"| {conn['type']} | `{conn['value']}` | `{conn['file']}` | {conn['line']} |")

        self._write_md("05_Altyapi_Config.md", infra_doc)

        # 6. DOSYA AĞACI
        tree_doc = ["# 🌳 Proje Dosya Ağacı", "```text"]
        tree_doc.extend(self.inventory["file_tree"])
        tree_doc.append("```")
        self._write_md("06_Dosya_Agaci.md", tree_doc)


if __name__ == "__main__":
    NexusAnalyzer(".").analyze()