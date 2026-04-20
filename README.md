# SG-Verwaltung - Django Projekt

Ein Django-basiertes Verwaltungssystem mit MySQL-Datenbank für die Verwaltung von Studierenden, Personal, Forschungsprojekten und Inventar.

## 📋 Voraussetzungen

- Python 3.8 oder höher
- MySQL 8.0+ oder MariaDB 10.5+
- Git

## 🚀 Installation auf einem neuen System

### 1. Repository klonen

```bash
git clone <repository-url>
cd sg-verwaltung
```

### 2. Virtuelle Umgebung erstellen und aktivieren

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen konfigurieren

1. Kopiere die `.env.example` Datei zu `.env`:
   ```bash
   copy .env.example .env    # Windows
   cp .env.example .env      # macOS/Linux
   ```

2. Generiere einen neuen SECRET_KEY:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. Öffne `.env` und fülle die Werte aus:

### 5. Datenbank einrichten

#### MySQL/MariaDB Datenbank erstellen

Öffne MySQL/MariaDB CLI oder phpMyAdmin:

```sql
CREATE DATABASE sg_verwaltung CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dj-sg-verwaltung'@'localhost' IDENTIFIED BY 'dein_passwort';
GRANT ALL PRIVILEGES ON sg_verwaltung.* TO 'dj-sg-verwaltung'@'localhost';
FLUSH PRIVILEGES;
```

#### Datenbank migrieren 

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Server starten

```bash
python manage.py runserver
```

Die Anwendung ist nun unter `http://127.0.0.1:8000/` erreichbar.

Admin-Panel: `http://127.0.0.1:8000/admin/`

## 📦 Projektstruktur

```
sg-verwaltung/
├── sgverwaltung/              # Django Projekt-Einstellungen
│   ├── __init__.py
│   ├── settings.py        # Haupt-Konfigurationsdatei
│   ├── urls.py            # URL-Routing
│   ├── wsgi.py
│   └── asgi.py
├── venv/                  # Virtuelle Umgebung (nicht im Git)
├── .env                   # Umgebungsvariablen (nicht im Git)
├── .env.example           # Template für Umgebungsvariablen
├── .gitignore
├── manage.py              # Django Management-Script
├── requirements.txt       # Python-Abhängigkeiten
└── README.md             # Diese Datei
```

## 👥 Support

Bei Fragen oder Problemen erstelle ein Issue im Repository oder kontaktiere das Entwicklungsteam.

---

**Letzte Aktualisierung:** Dezember 2025