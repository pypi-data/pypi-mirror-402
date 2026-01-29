import sys
import os

# Lisätään projektin juurikansio hakupolkuun
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shl.engine import LocalizationEngine

engine = LocalizationEngine(lang_code="sv", base_lang="en")

# Tämä avain puuttuu fi.jsonista
# Se pitäisi kääntää automaattisesti lennosta!
uusi_teksti = engine.ui_text("welcome_msg", "Welcome to our store")

print(f"Alkuperäinen: Welcome to our store")
print(f"SHL käänsi: {uusi_teksti}")
