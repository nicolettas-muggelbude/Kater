# Changelog

Alle nennenswerten Änderungen an Kater werden hier dokumentiert.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

## [1.4.0] - 2026-09-28

### Hinzugefügt
- Konfigurierbarer CSV-Export: Felder frei auswählen und die Spaltenreihenfolge per ↑/↓ anordnen
- Trennzeichen für CSV-Export wählbar (Semikolon oder Komma)
- Dubletten-Erkennung: findet Kontakte mit gleichem Namen, gleicher E-Mail oder gleicher Telefonnummer (Menü „Extras → Dubletten finden...")
- Seite-an-Seite-Vergleich beim Zusammenführen von Dubletten – abweichende Felder einzeln auswählbar, Telefonnummern/E-Mails/Adressen werden automatisch dedupliziert vereint, Gruppenzugehörigkeit bleibt erhalten

### Geändert
- Menüstruktur überarbeitet: neuer Menüpunkt „Export" bündelt vCard-, CSV-, Fritzbox- und Speedport-Export; Importfunktionen jetzt unter „Datei → Import"

## [1.3.0] - 2026-07-15

### Hinzugefügt
- Fritzbox-Telefonbuch-Export (XML), importierbar über die Fritzbox-Weboberfläche
- Speedport-Telefonbuch-Export (CSV) im Format der Telekom Speedport-Router
- Menü "Datei → Fritzbox" und "Datei → Speedport" mit Export für markierte oder alle Kontakte

## [1.2.4] - siehe Git-Historie
Frühere Versionen wurden nicht in diesem Changelog erfasst; siehe `git log` bzw. die [GitHub Releases](https://github.com/nicolettas-muggelbude/Kater/releases).
