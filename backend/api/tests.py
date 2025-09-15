# generate_filtered_calendar.py
# Variables en anglais, commentaires en français

import re
import requests
from icalendar import Calendar, Event
from datetime import timedelta

# --- CONFIG --- #
ics_url = "https://edt.univ-angers.fr/edt/ics?id=GFCFAFB7802F0597FE0532110A8C0C9F8"
output_file = "mon_calendrier.ics"
# ---------------- #

def fetch_ics(url):
    """Télécharge le flux ICS et retourne un objet Calendar."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return Calendar.from_ical(resp.text)

def text_contains_group(text, group_type, group_number):
    """Vérifie si le texte correspond à TD2 ou TP4."""
    if not text:
        return False
    t = text.lower()
    if group_type == "td":
        return bool(re.search(r"\btd[\s\-]*2\b", t))
    if group_type == "tp":
        return bool(re.search(r"\btp[\s\-]*4\b", t))
    return False

def is_cm(event):
    """Détecte si l'événement est un CM."""
    for attr in ("summary", "description", "location"):
        val = str(event.get(attr, "") or "")
        if re.search(r"\bcm\b", val, flags=re.IGNORECASE) or "cours magistral" in val.lower():
            return True
    return False

def matches_filters(event):
    """Retourne True si l'événement est CM, TD2 ou TP4."""
    summary = str(event.get("summary", "") or "")
    description = str(event.get("description", "") or "")
    location = str(event.get("location", "") or "")
    combined = " ".join([summary, description, location])

    return (
        is_cm(event)
        or text_contains_group(combined, "td", 2)
        or text_contains_group(combined, "tp", 4)
    )

def generate_filtered_calendar(cal):
    """Crée un nouvel objet Calendar avec uniquement les cours filtrés."""
    new_cal = Calendar()
    new_cal.add("prodid", "-//Filtered Calendar//Samsung//")
    new_cal.add("version", "2.0")

    for component in cal.walk():
        if component.name == "VEVENT" and matches_filters(component):
            new_event = Event()
            for key, value in component.items():
                new_event.add(key, value)
            new_cal.add_component(new_event)
    return new_cal

def main():
    print("Téléchargement de l'emploi du temps...")
    cal = fetch_ics(ics_url)
    print("Filtrage des événements...")
    new_cal = generate_filtered_calendar(cal)

    with open(output_file, "wb") as f:
        f.write(new_cal.to_ical())

    print(f"Calendrier généré : {output_file}")
    print("➡️ Tu peux maintenant importer ce fichier dans Samsung Calendar.")

if __name__ == "__main__":
    main()
