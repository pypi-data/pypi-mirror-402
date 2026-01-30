import ast
import json
import os
import subprocess
import sys
import argparse
from datetime import datetime
from pathlib import Path


def probe_target_environment(python_executable):
    """
    Verilen Python executable üzerinde çalışan bir probe script ile:
    - Built-in modülleri
    - Kurulu pip paketlerini ve versiyonlarını
    - Import adı -> Paket adı eşleşmelerini
    toplar.
    """
    print(f"[{python_executable}] ortamı taranıyor...")

    probe_code = """
import sys
import json
import importlib.metadata

data = {
    "builtins": [],
    "installed": {},
    "import_map": {}
}

# Built-in modüller
try:
    data["builtins"] = list(getattr(sys, 'stdlib_module_names', sys.builtin_module_names))
except:
    data["builtins"] = list(sys.builtin_module_names)

# Kurulu paketler ve import eşleşmeleri
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
        print("KRİTİK HATA: Hedef Python çalıştırılamadı")
        print(e.stderr)
        sys.exit(1)


def get_local_modules(directory):
    """Projedeki yerel modül isimlerini çıkarır."""
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
    """Bir Python dosyasındaki üst seviye import'ları AST ile çıkarır."""
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


def analyze_project(project_dir, python_exec):
    env = probe_target_environment(python_exec)

    builtins = set(env.get("builtins", []))
    installed = env.get("installed", {})
    import_map = env.get("import_map", {})

    local_modules = get_local_modules(project_dir)

    used_packages = {}
    report_lines = []
    json_output = {
        "project": str(project_dir),
        "target_python": python_exec,
        "files": {},
        "summary": {}
    }

    report_lines.append(f"ANALİZ RAPORU: {project_dir}")
    report_lines.append(f"Target Python: {python_exec}")
    report_lines.append("=" * 70)

    for root, _, files in os.walk(project_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            imports = get_imports_from_file(file_path)
            if not imports:
                continue

            rel = os.path.relpath(file_path, project_dir)
            report_lines.append(f"\nDosya: {rel}")
            report_lines.append("-" * 40)

            deps = []

            for lib in sorted(imports):
                # Yerel
                if lib in local_modules:
                    report_lines.append(f"[Yerel]       {lib}")
                    deps.append({"name": lib, "type": "local"})

                # Built-in
                elif lib in builtins:
                    report_lines.append(f"[Built-in]    {lib}")
                    deps.append({"name": lib, "type": "builtin"})

                # 3. parti
                else:
                    pkg = import_map.get(lib, lib)
                    key = pkg.lower()

                    if key in installed:
                        ver = installed[key]
                        report_lines.append(f"[3. Parti]    {lib} -> {pkg}=={ver}")
                        deps.append({
                            "name": lib,
                            "type": "3rd-party",
                            "package": pkg,
                            "version": ver
                        })
                        used_packages[pkg] = ver
                    else:
                        report_lines.append(f"[Bilinmiyor]  {lib}")
                        deps.append({"name": lib, "type": "unknown"})

            json_output["files"][rel] = deps

    json_output["summary"] = used_packages

    # ÇIKTILAR
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_dir = Path(f"RAPOR_getlibs_{timestamp}")
    out_dir.mkdir(exist_ok=True)

    (out_dir / "report_detailed.txt").write_text("\n".join(report_lines), encoding="utf-8")
    (out_dir / "report_ci.json").write_text(json.dumps(json_output, indent=4), encoding="utf-8")
    (out_dir / "requirements.txt").write_text(
        "\n".join(f"{k}=={v}" for k, v in sorted(used_packages.items())),
        encoding="utf-8"
    )
    (out_dir / "constraints.txt").write_text(
        "\n".join(f"{k}=={v}" for k, v in sorted(installed.items())),
        encoding="utf-8"
    )

    print("\nAnaliz tamamlandı ✔")
    print(f"Rapor dizini: {out_dir}")


def main():
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
    analyze_project(project_dir, args.python_exec)


if __name__ == "__main__":
    main()
