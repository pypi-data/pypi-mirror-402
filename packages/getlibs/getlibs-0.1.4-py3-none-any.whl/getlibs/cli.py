import ast
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import argparse


def probe_target_environment(python_executable):
    """Hedef Python ortamını tarar."""
    print(f"[{python_executable}] ortamı taranıyor ve metadata okunuyor...")

    probe_code = """
import sys
import json
import importlib.metadata

data = {"builtins": [], "installed": {}, "import_map": {}}
try:
    data["builtins"] = list(getattr(sys, 'stdlib_module_names', sys.builtin_module_names))
except:
    data["builtins"] = list(sys.builtin_module_names)

for dist in importlib.metadata.distributions():
    try:
        name = dist.metadata['Name']
        version = dist.version
        data["installed"][name.lower()] = version
        toplevels = dist.read_text('top_level.txt')
        if toplevels:
            for imp in toplevels.split():
                clean = imp.replace('/', '.').replace('\\\\', '.').split('.')[0]
                if clean:
                    data["import_map"][clean] = name
    except:
        continue

print(json.dumps(data))
"""
    try:
        output = subprocess.check_output(
            [python_executable, "-c", probe_code],
            text=True,
            stderr=subprocess.PIPE
        )
        return json.loads(output)
    except subprocess.CalledProcessError as e:
        print(f"KRİTİK HATA: Hedef Python çalıştırılamadı.\n{e.stderr}")
        sys.exit(1)


def get_local_modules(directory):
    modules = set()
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                modules.add(f[:-3])
        for d in dirs:
            if os.path.exists(os.path.join(root, d, "__init__.py")):
                modules.add(d)
    return modules


def get_imports_from_file(file_path):
    imports = set()
    try:
        tree = ast.parse(Path(file_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
    except Exception:
        pass
    return imports


def analyze_project(project_dir, python_exec,
                    out_md="report_detailed.md",
                    out_json="report_ci.json",
                    out_req="requirements.txt",
                    out_const="constraints.txt"):
    """Ana analiz fonksiyonu."""
    # Ortam verilerini al
    env_data = probe_target_environment(python_exec)
    target_builtins = set(env_data.get("builtins", []))
    target_installed = env_data.get("installed", {})
    import_map = env_data.get("import_map", {})

    local_modules = get_local_modules(project_dir)

    report_lines = []
    report_lines.append(f"# ANALİZ RAPORU: {os.path.abspath(project_dir)}")
    report_lines.append(f"**Target Python:** {python_exec}")
    report_lines.append("\n" + "=" * 70 + "\n")

    json_output = {
        "project": os.path.abspath(project_dir),
        "target_python": python_exec,
        "files": {},
        "summary": {}
    }

    used_packages = {}

    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith(".py") and file != os.path.basename(__file__):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)

                imports = get_imports_from_file(file_path)
                if imports:
                    report_lines.append(f"## Dosya: {rel_path}\n")
                    report_lines.append("-" * 40)

                    file_deps = []
                    for lib in sorted(imports):
                        lib_status = {}
                        if lib in local_modules:
                            lib_type = "Yerel"
                            info = "Local Module"
                            lib_status = {"name": lib, "type": "local"}
                        elif lib in target_builtins:
                            lib_type = "Built-in"
                            info = "Std Lib"
                            lib_status = {"name": lib, "type": "builtin"}
                        else:
                            pip_package_name = import_map.get(lib, lib)
                            pip_name_lower = pip_package_name.lower()
                            if pip_name_lower in target_installed:
                                version = target_installed[pip_name_lower]
                                lib_type = "3. Parti"
                                info = f"{pip_package_name}=={version}"
                                lib_status = {
                                    "name": lib,
                                    "type": "3rd-party",
                                    "package": pip_package_name,
                                    "version": version
                                }
                                used_packages[pip_package_name] = version
                            else:
                                lib_type = "Bilinmiyor"
                                info = "Yüklü Değil / Bulunamadı"
                                lib_status = {"name": lib, "type": "unknown"}

                        report_lines.append(f"- **{lib_type}** `{lib}` : {info}")
                        file_deps.append(lib_status)

                    report_lines.append("\n")
                    json_output["files"][rel_path] = file_deps

    report_lines.append("\n" + "=" * 70)
    report_lines.append("### 3. PARTİ KÜTÜPHANE ÖZETİ (requirements format)")
    report_lines.append("-" * 70)

    req_content = []
    if used_packages:
        for pkg_name in sorted(used_packages.keys(), key=str.lower):
            ver = used_packages[pkg_name]
            line = f"{pkg_name}=={ver}"
            report_lines.append(f"- {line}")
            req_content.append(line)
    else:
        report_lines.append("Harici kütüphane bulunamadı.")

    json_output["summary"] = used_packages

    root_dir = Path(".")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_dir = root_dir / f"RAPOR_getlibs_{timestamp}"
    if not report_dir.exists():
        os.makedirs(report_dir)

    # Çıktılar
    (report_dir / out_md).write_text("\n".join(report_lines), encoding="utf-8")
    (report_dir / out_json).write_text(json.dumps(json_output, indent=4), encoding="utf-8")
    (report_dir / out_req).write_text("\n".join(req_content), encoding="utf-8")
    (report_dir / out_const).write_text(
        "\n".join(f"{k}=={v}" for k, v in target_installed.items()),
        encoding="utf-8"
    )

    print(f"\nİşlem Tamamlandı!")
    print(f"1. Detaylı Rapor : {out_md}")
    print(f"2. JSON Data     : {out_json}")
    print(f"3. Requirements  : {out_req}")
    print(f"4. Constraints   : {out_const}")


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(description="Python proje dependency analiz aracı")
    parser.add_argument(
        "--project-dir",
        help="Analiz edilecek proje dizini (varsayılan: script dizini)"
    )
    parser.add_argument(
        "--python-exec",
        help="Hedef Python executable (varsayılan: mevcut Python)",
        default=sys.executable
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path(__file__).parent.resolve()
    python_exec = args.python_exec

    analyze_project(
        project_dir=project_dir,
        python_exec=python_exec
    )


if __name__ == "__main__":
    main()
