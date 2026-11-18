# Roadmap: SQL und Python im Jupyter Notebook

Ziel: PostgreSQL-Daten aus Python heraus abfragen, auswerten, darstellen und verändern. Alles in Jupyter Notebooks, mit Pagila als Übungsdatenbank.

**Arbeitsweise**

- Pro Phase ein eigenes Notebook, z. B. `phase_00_umgebung.ipynb`, `phase_01_sql_magics.ipynb` usw.
- Die Aufgaben setzt du selbst um. Es gibt zu jeder Phase Ziel, Inhalt, Übung und ein Abschlusskriterium.
- Zugangsdaten stehen nie im Notebook, sondern in einer `.env`-Datei (in der `.gitignore`).
- Reihenfolge einhalten. Jede Phase baut auf der vorherigen auf.

**Voraussetzungen**

- SQL: `SELECT`, `WHERE`, `ORDER BY`, `JOIN`, `GROUP BY` sicher. Mehr brauchst du für den Einstieg nicht, den Rest holst du dir in den passenden Phasen.
- Python: Funktionen, Listen, Dictionaries, Module importieren, Fehlerbehandlung mit `try`/`except`.

---

## Phase 0 – Umgebung

**Ziel:** Ein Notebook, das sich mit PostgreSQL verbinden kann, ohne dass ein Passwort im Notebook steht.

**Inhalt**

- Lokale venv mit `uv`, Jupyter und Kernel-Auswahl im Notebook
- Pakete: `psycopg` (Treiber), `jupysql`, `pandas`, `sqlalchemy`, `matplotlib`, `python-dotenv`
- PostgreSQL erreichbar (lokal oder Server), Pagila geladen
- `.env` mit Verbindungsdaten, Einlesen mit `python-dotenv` oder `os.environ`
- `.gitignore` (`.venv/`, `.env`, `.ipynb_checkpoints/`), `nbstripout` für Git

**Übung:** Eine Zelle, die die Umgebungsvariablen liest und nur ausgibt, ob sie gesetzt sind (nicht ihren Wert).

**Abschluss:** `SELECT version();` läuft aus dem Notebook, und im Repository liegt weder `.env` noch ein Passwort.

---

## Phase 1 – SQL direkt im Notebook (JupySQL)

**Ziel:** SQL in Zellen schreiben, ohne Python-Code drumherum.

**Inhalt**

- `%load_ext sql`, Verbindung mit `%sql`
- Einzeilig (`%sql`) und mehrzeilig (`%%sql`)
- Python-Variablen in Abfragen verwenden
- Ergebnis als Tabelle, Umwandlung in einen DataFrame
- Wann JupySQL reicht und wann du Python-Code brauchst

**Übung:** Drei Abfragen auf Pagila (z. B. Filme einer Kategorie, Kunden mit den meisten Ausleihen, Umsatz je Filiale). Das Ergebnis der dritten als DataFrame weiterverwenden.

**Abschluss:** Du kannst eine Abfrage im Notebook ändern und das Ergebnis in Python weiterverarbeiten.

---

## Phase 2 – Datenbankzugriff mit psycopg

**Ziel:** Verstehen, was hinter `%sql` passiert, und den Zugriff selbst in Python schreiben.

**Inhalt**

- Verbindung (`connect`), Cursor, `execute`, `fetchone`, `fetchall`, `fetchmany`
- Verbindungen mit `with` sauber schließen
- **Parameter statt Textverkettung** (SQL-Injection, warum das wichtig ist)
- Zeilen als Tupel oder Dictionary
- Fehler abfangen (Verbindung weg, SQL-Fehler)

**Übung:** Eine Funktion `filme_nach_kategorie(name)`, die die Kategorie als Parameter bekommt und eine Liste von Dictionaries zurückgibt.

**Abschluss:** Die Funktion läuft auch mit Eingaben wie `Action'; --` ohne Fehler und ohne Wirkung auf die Datenbank.

---

## Phase 3 – Auswerten mit pandas

**Ziel:** Entscheiden können, was in SQL und was in pandas gerechnet wird.

**Inhalt**

- `pandas.read_sql` und DataFrames aus Abfragen
- Spalten, Filter, `groupby`, `merge`, Sortieren
- Gegenüberstellung: `WHERE` und `GROUP BY` in SQL, Filter und `groupby` in pandas
- Faustregel: so viel wie möglich in der Datenbank filtern und aggregieren, nur das Ergebnis laden
- Datentypen (Datum, Zahlen, `NULL` wird zu `NaN`/`None`)

**Übung:** Dieselbe Auswertung (Umsatz pro Monat) einmal komplett in SQL und einmal mit rohen Zahlen aus SQL plus `groupby`. Ergebnisse vergleichen.

**Abschluss:** Beide Wege liefern dasselbe Ergebnis, und du kannst begründen, welcher bei großen Datenmengen besser ist.

---

## Phase 4 – SQLAlchemy Core

**Ziel:** Eine Verbindung, die sich für pandas, JupySQL und eigenen Code teilen lässt.

**Inhalt**

- `create_engine`, Verbindungsadresse aus der `.env` bauen
- `text()` mit benannten Parametern
- Verbindungen und Transaktionen (`begin`, `commit`, `rollback`)
- Engine an `pandas.read_sql` übergeben

**Übung:** Eine zentrale Engine im Notebook, die in allen späteren Phasen verwendet wird.

**Abschluss:** Dieselbe Abfrage läuft über Engine, `read_sql` und `%sql` mit gleichem Ergebnis.

---

## Phase 5 – Darstellen

**Ziel:** Aus einer Abfrage ein lesbares Diagramm machen.

**Inhalt**

- `matplotlib` (Balken, Linien), wahlweise `plotly` für Interaktivität
- Achsen, Beschriftung, Titel, sinnvolle Sortierung
- Zeitreihen aus SQL (`date_trunc`) als Linie
- Wann welche Diagrammart passt

**Übung:** Drei Diagramme zu Pagila: Filme pro Kategorie, Umsatz pro Monat, Top-10-Kunden.

**Abschluss:** Jedes Diagramm ist ohne weitere Erklärung verständlich (Titel, Achsen, Einheit).

---

## Phase 6 – Daten schreiben

**Ziel:** Daten aus Python in die Datenbank bringen, ohne Schaden anzurichten.

**Inhalt**

- `INSERT`, `UPDATE`, `DELETE` aus Python, immer mit Parametern
- Transaktionen: erst `commit`, wenn alles stimmt, bei Fehlern `rollback`
- Mehrere Zeilen auf einmal (`executemany`)
- `DataFrame.to_sql` und seine Grenzen
- **Eigenes Schema** (z. B. `uebung`) statt Pagila-Tabellen zu verändern

**Übung:** Eine Tabelle `uebung.auswertung` anlegen, Ergebnisse aus Phase 3 hineinschreiben und gezielt einen Fehler provozieren, um das `rollback` zu sehen.

**Abschluss:** Nach einem absichtlichen Fehler mitten im Schreiben ist die Tabelle unverändert.

---

## Phase 7 – Daten laden und bereinigen

**Ziel:** Eine fremde Datei sauber in die Datenbank bringen.

**Inhalt**

- CSV mit pandas lesen, Spaltentypen festlegen
- Bereinigen: fehlende Werte, Duplikate, Leerzeichen, falsche Datumsformate
- Prüfen, bevor geschrieben wird (Anzahl, Pflichtfelder)
- Laden mit `to_sql` oder schneller mit `COPY`
- Nachprüfen: Zeilenzahl und Stichproben in SQL

**Übung:** Eine CSV-Datei mit absichtlich schmutzigen Daten bereinigen und in `uebung` laden.

**Abschluss:** Die Zeilenzahl in der Datenbank stimmt mit dem bereinigten DataFrame überein, und die Stichproben passen.

---

## Phase 8 – Performance

**Ziel:** Langsame Abfragen erkennen und große Ergebnisse handhaben.

**Inhalt**

- `EXPLAIN` und `EXPLAIN ANALYZE` aus dem Notebook
- Indizes und wie du ihre Wirkung misst
- Große Ergebnisse stückweise lesen (`chunksize`, `fetchmany`)
- Zeitmessung mit `%timeit` und `%%time`

**Übung:** Eine bewusst langsame Abfrage messen, einen Index anlegen und erneut messen.

**Abschluss:** Du kannst die Zeiten vorher und nachher belegen und den Plan in `EXPLAIN` erklären.

---

## Phase 9 – Vom Notebook zum Modul

**Ziel:** Wiederverwendbaren Code aus dem Notebook herauslösen.

**Inhalt**

- Eigenes Modul `db.py` mit Engine, Abfragefunktionen und Konfiguration
- Notebook importiert das Modul, enthält nur noch Aufruf, Ergebnis und Erklärung
- Einfache Tests (z. B. mit `pytest`) für die Funktionen
- Notebook als Bericht: von oben nach unten lauffähig (Restart & Run All)

**Übung:** Alle Funktionen aus Phase 2 bis 7 in ein Modul verschieben und ein Notebook schreiben, das nur noch das Modul nutzt.

**Abschluss:** „Restart & Run All“ läuft fehlerfrei durch, und die Tests sind grün.

---

## Phase 10 – Abschlussprojekt

Eine Variante wählen:

- **A: Auswertungsbericht zu Pagila.** Ein Notebook mit Fragestellung, Abfragen, Diagrammen und Fazit.
- **B: Lade-Pipeline.** Daten aus CSV oder API holen, bereinigen, prüfen und in die Datenbank schreiben, mit Log und Fehlerbehandlung.
- **C: Eigene Daten.** Ein selbst gewähltes Thema mit eigener Tabellenstruktur, Daten laden, auswerten, darstellen.

**Abschluss:** Das Projekt liegt in einem eigenen Repository, ist ohne Passwörter eingecheckt, und ein zweites Gerät kann es mit `uv sync` und eigener `.env` nachbauen.

---

## Optional

- **SQLAlchemy ORM:** Tabellen als Python-Klassen. Sinnvoll, wenn du mehr schreibst als abfragst.
- **Eigener SQL-Kernel (`xeus-sql`):** Ganze Zellen in reinem SQL.
- **Dashboards:** Interaktive Auswahl mit `ipywidgets`.
- **Mehrere Datenbanken:** SQLite für lokale Tests, PostgreSQL für den echten Betrieb.
