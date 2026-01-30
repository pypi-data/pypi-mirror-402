getlibs
=======

**getlibs** is a **dependency analysis tool** for Python projects that inspects all `import` statements and detects:

-   Local modules

-   Built-in (standard library) modules

-   3rd-party (pip) packages

-   Missing / unknown imports

It is specifically designed to:

-   Generate a `requirements.txt` from an existing project

-   Check dependencies in CI/CD pipelines

-   Ensure compatibility across different Python environments

* * * * *

Features
--------

-   🔍 AST-based **real import analysis** (not regex)

-   🧠 Uses `top_level.txt` for **import name → pip package mapping**

-   🐍 Analyzes using the **target Python executable** (avoids environment mismatch issues)

-   📄 Produces **4 output formats**:

    -   Detailed TXT report

    -   CI-friendly JSON report

    -   `requirements.txt` containing only used packages

    -   `constraints.txt` covering the entire environment

-   🧩 Clearly separates **local / built-in / 3rd-party** imports

* * * * *

Installation
------------

`pip3.13 install getlibs`

* * * * *

Usage
-----

`cd /project/path/

getlibs --project-dir . --python-exec python3.13`

This will analyze your project and generate all output files in a timestamped report folder:

-   Detailed TXT report

-   JSON for CI/CD

-   Requirements file with used packages

-   Constraints file with all installed packages

# Sample Output
### ANALİZ RAPORU: **
**Target Python:** python3.13

======================================================================

## Dosya: base_engine.py

----------------------------------------
- **Bilinmiyor** `bson` : Yüklü Değil / Bulunamadı
- **Built-in** `datetime` : Std Lib
- **Built-in** `functools` : Std Lib
- **Built-in** `json` : Std Lib
- **Built-in** `os` : Std Lib
- **3. Parti** `pymongo` : pymongo==4.15.5
- **Built-in** `re` : Std Lib
- **Built-in** `subprocess` : Std Lib


## Dosya: main.py

----------------------------------------
- **Built-in** `base64` : Std Lib
- **Yerel** `base_engine` : Local Module
- **3. Parti** `fastapi` : fastapi==0.128.0
- **Bilinmiyor** `functions` : Yüklü Değil / Bulunamadı
- **Built-in** `importlib` : Std Lib
- **Built-in** `os` : Std Lib
- **3. Parti** `psycopg2cffi` : psycopg2cffi==2.9.0
- **3. Parti** `starlette` : starlette==0.50.0


# Türkçe

**getlibs**, bir Python projesindeki tüm `import` ifadelerini analiz ederek:

- Yerel modülleri
- Built-in (standart kütüphane) modülleri
- 3. parti (pip) paketleri
- Eksik / bilinmeyen import’ları

tespit eden bir **dependency analiz aracıdır**.

Özellikle:
- Mevcut bir projeden `requirements.txt` çıkarmak
- CI/CD süreçlerinde dependency denetimi yapmak
- Farklı Python ortamları için uyumluluk kontrolü yapmak

amacıyla tasarlanmıştır.

---

## Özellikler

- 🔍 AST tabanlı gerçek import analizi (regex değil)
- 🧠 `top_level.txt` kullanarak **import adı → pip paket adı** eşlemesi
- 🐍 Hedef Python executable üzerinden analiz (env farkı sorunu yok)
- 📄 4 farklı çıktı üretir:
  - Detaylı TXT rapor
  - CI uyumlu JSON
  - Sadece kullanılan paketlerden `requirements.txt`
  - Tüm ortamı kapsayan `constraints.txt`
- 🧩 Yerel / built-in / 3. parti ayrımı net şekilde yapılır

---

## Kurulum

```bash
pip3.13 install getlibs

cd /project/path/

getlibs --project-dir . --python-exec python3.13
```