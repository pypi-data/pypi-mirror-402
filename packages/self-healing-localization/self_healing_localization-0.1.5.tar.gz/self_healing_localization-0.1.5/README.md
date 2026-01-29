# Self‑Healing Localization Layer
### Automatic, self‑maintaining localization for any Python project  
**Author:** Tuomas Lähteenmäki  
**License:** MIT  
**Version:** 0.1.5

---

## 🌍 Overview

Self‑Healing Localization Layer (SHL) is a lightweight, dependency‑free Python library that eliminates missing translations forever.

It provides:
- Automatic creation of missing language files  
- Automatic creation of missing keys  
- Fallback to a base language (default: English)  
- Unified support for both UI text and optional AI prompt templates  

---

## ✨ Key Features

### ✔ Self‑healing UI localization  
- Missing language files are created automatically  
- Missing keys are added on the fly  
- Base language is used as fallback  

### ✔ Self‑healing AI prompt template localization  
- Missing template files are generated automatically  
- Base templates are copied as fallback  
- Missing template keys are added automatically  

### ✔ Unified high‑level engine  
The `LocalizationEngine` ties everything together:
- ensures languages exist  
- synchronizes all languages with the base language  
- provides clean access to UI text and templates  

### ✔ Zero dependencies  
Pure Python. Works everywhere.

---


## 📦 Installation

Currently available via TestPyPI (v0.1.5):

```bash
pip install --index-url [https://test.pypi.org/simple/](https://test.pypi.org/simple/) self-healing-localization==0.1.5
```

Self‑Healing Localization Layer (SHL) is a lightweight, dependency‑free Python library that eliminates missing translations forever.

It provides:

- automatic creation of missing language files  
- automatic creation of missing keys  
- fallback to a base language (default: English)  
- unified support for both UI text and AI prompt templates  
 
This library is designed to be **dropped into any project** — from small scripts to full applications — and it will maintain localization files automatically as the project grows.

No more manual JSON editing.  
No more “missing translation” errors.  
No more incomplete language packs.

---


## 🚀 Quick Start

### 1. Basic UI Localization
Initialize the engine and start retrieving text. If the key doesn't exist, it is added to your JSON files automatically.

```python
from shl.engine import LocalizationEngine

# Initialize the engine (e.g., set user language to Finnish)
engine = LocalizationEngine(lang_code="fi", base_lang="en")

# Retrieve UI text. If 'welcome_msg' is missing, it's created with the default value.
title = engine.ui_text("welcome_msg", "Welcome to the App!")

print(title)
```

### 2. Retrieve UI text

```python
title = engine.ui_text("app_title", "My Application")
```

If `"app_title"` does not exist in `locales/lang_en.json`, it will be added automatically.

### 3. Retrieve prompt templates

```python
summary_prompt = engine.template("summary_short", "Summarize the text:")
```

If `prompts/fi.json` does not exist, it will be created automatically using `prompts/en.json` as the base.

### 4. AI Prompt Templates
Keep your AI prompts localized just like your UI strings.

```python
# Retrieve a localized prompt template
prompt = engine.template("summarize_task", "Please summarize the following text:")
```

---

## 🧩 Project Structure
The library follows a modular design to keep the core logic separate from your application code:

```
self-healing-localization/
│
├─ shl/
│  └─ engine/                 # Core modular engine
│     ├─ core.py              # Main LocalizationEngine
│     ├─ localizer.py         # UI text logic
│     ├─ template_localizer.py # AI template logic
│     ├─ ai_translation.py    # (Coming in v0.2)
│     └─ __init__.py          # Internal package exports
│
├─ pyproject.toml             # Package configuration
└─ README.md                  # Project documentation
```

---

## 🔧 API Reference (v0.1.x)

### Initialize

```python
engine = LocalizationEngine(lang_code="en")
```

### UI text

```python
engine.ui_text(key, default="")
```

### Template text
Template localization is available in v0.1.x but considered experimental and subject to change.

```python
engine.template(key)
```

### Ensure language exists

```python
engine.ensure_language("de")
```

### Sync all languages with base language

```python
engine.sync()
```

- SHL is currently focused on UI localization. 
- Prompt template localization is considered an advanced / experimental feature in v0.1.x.
---

## 🛠 Roadmap

### v0.1.x: 
- Core self-healing logic and modular engine.

### v0.1.4
- Basic automatic translation engine (e.g., English -> Finnish).

### v0.3.0
- AI‑powered translation (Gemini / Groq / OpenAI)
- CLI tool (`selfheal sync`, `selfheal translate`)
- Automatic detection of missing keys across all languages

### v0.4.0
- Web‑based Localization Studio
- Visual diffing of translations
- Export/import language packs

### v1.0
- Full ecosystem integrations (Flask, FastAPI, Django, Flet)
- Community templates
- Official PyPI release


---

## 🤝 Contributing

Contributions are welcome.  
This project aims to become a new standard for open‑source localization — simple, automatic, and self‑maintaining.

---

## 📄 License

MIT License — free for personal and commercial use.

---

## ⭐ Vision

Localization should never be a burden.

With SHL, any project can become multilingual — automatically, reliably, and without manual maintenance.

**No more missing translations.  
No more incomplete language packs.  
Localization that heals itself.**


#localization • #i18n • #l10n • #self-healing • #translation • #multilingual  
#json • #python • #developer-tools • #automation • #templates • #cli  
#ai-assisted • #language-files • #internationalization • #localization-engine

