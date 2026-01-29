# 🔥 Bah Lol

Framework API Python yang **ringan, tegas, dan langsung GAS**.

Kalau kamu capek sama framework ribet, kebanyakan config, dan teori panjang,
**Bah Lol** hadir buat satu tujuan:

> **Bikin API yang BARANG-nya jelas dan langsung jalan.**

---

## ✨ Kenapa Bah Lol?

* ⚡ Super ringan
* 📦 Tanpa dependency ribet
* 🧠 Mudah dipahami
* 😄 Serius tapi ada senyum dikit
* 🇮🇩 Lokal rasa global

Filosofi kami sederhana:

> **Kalau bisa simpel, kenapa harus ribet.**

---

## 🚀 Instalasi

```bash
pip install bah-lol
```

---

## 🔧 Contoh Paling Dasar

```python
from bah_lol import BahLol

app = BahLol()

@app.barang("/jalan")
def jalan():
    return {
        "status": "mantap",
        "pesan": "Server sudah jalan, BARANG ini jelas"
    }

app.gas()
```

Buka:

```
http://localhost:8000/jalan
```

---

## ⛽ Konsep Penting di Bah Lol

| Istilah | Artinya            |
| ------- | ------------------ |
| BARANG  | Endpoint / fitur   |
| GAS     | Menjalankan server |
| BBM     | Request / payload  |
| OPLOS   | Middleware         |
| BAHENOL | Plugin / extension |

---

## 🛠 CLI Command

```bash
bah-lol gas
bah-lol barang users
bah-lol oplos auth
bah-lol bbm
bah-lol bahenol
```

---

## 📜 Log Khas

```
🔥 GAS dibuka di port 8000
⛽ Request masuk, BBM aman
📦 BARANG siap dipakai
```

---

## 📦 Struktur Project

```
bah_lol/
├── bah_lol/
│   ├── __init__.py
│   ├── app.py          # Core App (router + server)
│   ├── router.py       # Registrasi BARANG
│   ├── gas.py          # HTTP server (async / sync ringan)
│   ├── oplos.py        # Middleware
│   ├── logger.py       # Log khas Bah Lol
│   └── cli.py          # CLI command
├── examples/
│   └── basic.py
├── tests/
│   └── test_barang.py
├── README.md
├── pyproject.toml
├── setup.cfg
└── LICENSE
```

---

## ⚠️ Catatan Penting

Bah Lol ini santai **dalam gaya**,
tapi **serius dalam fungsi**.

Cocok untuk:

* Prototype
* Internal API
* Demo
* Project cepat

---

## ❤️ Penutup

Kalau API kamu:

* Jelas
* Jalan
* Bisa dipakai

Berarti **BARANG-nya sudah benar**.

Silakan gas 🚀

# Key Features Implemented:
1. Core App (`app.py`): Main BahLol class with decorators for registering endpoints
2. Router (`router.py`): Handles route registration and matching with parameter extraction
3. Gas Server (`gas.py`): Lightweight HTTP server implementation
4. Middleware (`oplos.py`): Middleware management system
5. Logger (`logger.py`): Custom logging with Bah Lol style messages
6. CLI (`cli.py`): Command-line interface with all specified commands
7. Example (`examples/basic.py`): Shows how to use the framework
8. Tests (`tests/test_barang.py`): Unit tests for the framework
9. Configuration files: pyproject.toml, setup.cfg, and LICENSE

Framework Features:
- Decorator-based routing (@app.barang)
- Parameterized routes (/users/<id>)
- Middleware support (OPLOS)
- Custom logging with Bah Lol style messages
- CLI commands (gas, barang, oplos, bbm, bahenol)
- Lightweight design with minimal dependencies
- Indonesian-themed naming convention

The framework follows the philosophy of being simple, direct, and getting things done quickly - perfect for prototypes,
internal services, and small-to-medium APIs.