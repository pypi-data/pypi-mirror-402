# getlibs

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