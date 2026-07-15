# Adressbuch - Projektinstruktionen

## Projektziel
Linux-Adressbuch-App mit vollständiger vCard-Unterstützung.

## Technologie-Stack
- **Aktuell:** Python 3 + tkinter (GUI)
- **Ziel:** GTK4 (Migration geplant)
- **Datenbank:** SQLite (lokale Speicherung)
- **Format:** vCard 4.0 (Import/Export)

## Architektur
```
adressbuch/
├── models/contact.py          # Kontaktmodell (alle vCard-Felder)
├── storage/database.py        # SQLite-Persistenz
├── storage/vcard.py           # vCard 4.0 Import/Export
├── storage/csv_import.py      # Thunderbird-CSV-Import
├── storage/fritzbox_export.py # Fritzbox-Telefonbuch-Export (XML)
├── storage/speedport_export.py # Speedport-Telefonbuch-Export (CSV)
└── gui/                       # GUI-Schicht (tkinter → GTK4)
```

## Wichtige Designentscheidungen
- GUI-Schicht ist austauschbar (tkinter → GTK4), Logik bleibt
- Alle vCard 4.0 Felder werden unterstützt inkl. DEATHDATE
- SQLite-Schema orientiert sich an vCard-Struktur
- vCard-Import ist tolerant (vCard 3.0 und 4.0)

## Geplante Features
- [x] Kontaktmodell mit allen vCard-Feldern
- [x] SQLite-Datenbank
- [x] vCard Import/Export
- [x] Tkinter-GUI (Basis)
- [x] Thunderbird-CSV-Import
- [x] Gruppenverwaltung / Kategorien
- [x] Suche und Filter
- [x] Fritzbox-/Speedport-Telefonbuch-Export
- [ ] Foto-Unterstützung
- [ ] CardDAV-Schnittstelle
- [ ] GTK4-Migration

## Konventionen
- Ausgaben und Kommentare auf Deutsch
- Type hints überall
- Keine unnötigen Abhängigkeiten
