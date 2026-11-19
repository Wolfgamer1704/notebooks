"""
Tests für ``database.get_sales_per_category`` (Abschlussprojekt, Teil 2).

Ausführen im Notebook (Ordner des Notebooks ist das Arbeitsverzeichnis):

    import sys
    !{sys.executable} -m pytest -v test_sales_per_category.py

Ohne Dateinamen (``-m pytest -v``) laufen alle Testdateien im Ordner,
also auch ``test_database.py``.

Die Tests laufen gegen die echte Pagila-Datenbank. PostgreSQL muss also
laufen und erreichbar sein.

Wichtig zum Verständnis (Entscheidung "Variante A"):
    Ein Film kann mehreren Kategorien angehören. Der Umsatz eines Films
    zählt dann **voll in jeder seiner Kategorien**. Die Summe über alle
    Kategorien ist deshalb absichtlich größer als der Gesamtumsatz in
    ``payment``. Die Tests im Abschnitt "Umsatzsummen" prüfen genau diese
    Regel, statt Gleichheit mit dem Gesamtumsatz zu erwarten.
"""

import pandas
import pytest
import sqlalchemy

import database


# --- Erwartete Werte --------------------------------------------------
EXPECTED_ROW_COUNT = 16
EXPECTED_COLUMNS = ["amount", "category"]
EXPECTED_CATEGORIES = {
    "Action", "Animation", "Children", "Classics", "Comedy", "Documentary",
    "Drama", "Family", "Foreign", "Games", "Horror", "Music", "New",
    "Sci-Fi", "Sports", "Travel",
}


# --- Hilfsfunktion ----------------------------------------------------
def query_scalar(sql):
    """
    Führt eine SQL-Abfrage aus, die genau einen Wert liefert, und gibt
    diesen Wert zurück (z. B. für ``SELECT sum(...)`` oder ``count(*)``).
    """
    with database.pagila.connect() as connection:
        return connection.execute(sqlalchemy.text(sql)).scalar()


# --- Fixture ----------------------------------------------------------
@pytest.fixture(scope="module")
def sales_per_category():
    """
    Führt ``get_sales_per_category`` einmal aus und gibt das Ergebnis an alle
    Tests weiter, die einen Parameter ``sales_per_category`` haben.

    ``scope="module"`` bedeutet: Die Abfrage läuft nur einmal für die ganze
    Datei, nicht einmal pro Test.
    """
    return database.get_sales_per_category()


# --- Tests: Form des Ergebnisses --------------------------------------
def test_returns_dataframe(sales_per_category):
    """Das Ergebnis ist ein pandas-DataFrame."""
    assert isinstance(sales_per_category, pandas.DataFrame)


def test_row_count(sales_per_category):
    """Es gibt genau eine Zeile pro Kategorie, insgesamt 16."""
    assert len(sales_per_category) == EXPECTED_ROW_COUNT


def test_column_names(sales_per_category):
    """Die Spalten heißen ``amount`` und ``category`` (in dieser Reihenfolge)."""
    assert list(sales_per_category.columns) == EXPECTED_COLUMNS


def test_no_missing_values(sales_per_category):
    """Keine Spalte enthält leere Werte."""
    assert not sales_per_category.isna().any().any()


def test_sorted_ascending(sales_per_category):
    """
    Die Kategorien sind nach Umsatz aufsteigend sortiert (kleinster zuerst).

    Die Funktion sortiert bewusst aufsteigend, damit ``barh`` die stärkste
    Kategorie oben zeichnet (``barh`` setzt die erste Zeile nach unten).
    """
    assert sales_per_category["amount"].is_monotonic_increasing


# --- Tests: Kategorien ------------------------------------------------
def test_categories_unique(sales_per_category):
    """Jede Kategorie kommt nur einmal vor (GROUP BY hat funktioniert)."""
    assert sales_per_category["category"].is_unique


def test_all_categories_present(sales_per_category):
    """
    Genau die 16 Pagila-Kategorien sind enthalten, keine fehlt, keine ist zu viel.

    Fehlt eine Kategorie, wurde ihr Umsatz durch einen JOIN verloren.
    """
    assert set(sales_per_category["category"]) == EXPECTED_CATEGORIES


def test_amounts_positive(sales_per_category):
    """Jede Kategorie hat einen Umsatz größer als 0."""
    assert (sales_per_category["amount"] > 0).all()


# --- Tests: Umsatzsummen (Variante A) ---------------------------------
def test_total_at_least_payment_total(sales_per_category):
    """
    Die Summe aller Kategorien ist mindestens so groß wie der Gesamtumsatz.

    Größer ist erlaubt und erwartet (Filme mit mehreren Kategorien zählen
    mehrfach). Kleiner wäre ein Fehler: Dann ginge über die JOINs Umsatz
    verloren.
    """
    payment_total = float(query_scalar("SELECT sum(amount) FROM payment"))

    assert sales_per_category["amount"].sum() >= payment_total


def test_total_matches_weighted_payment_total(sales_per_category):
    """
    Die Summe aller Kategorien entspricht exakt der Regel von Variante A.

    Jede Zahlung wird mit der Anzahl der Kategorien ihres Films multipliziert
    und dann aufsummiert. Genau das muss die Summe über alle Kategorien
    ergeben, nicht mehr und nicht weniger.
    """
    weighted_total = float(query_scalar("""
        SELECT sum(payment.amount * film_categories.category_count)
        FROM payment
        JOIN rental
            ON rental.rental_id = payment.rental_id
        JOIN inventory
            ON inventory.inventory_id = rental.inventory_id
        JOIN (
            SELECT film_id, count(*) AS category_count
            FROM film_category
            GROUP BY film_id
        ) AS film_categories
            ON film_categories.film_id = inventory.film_id
    """))

    assert sales_per_category["amount"].sum() == pytest.approx(weighted_total)


def test_every_payment_has_category():
    """
    Jede Zahlung lässt sich über die JOIN-Kette einer Kategorie zuordnen.

    ``LEFT JOIN`` behält auch Zahlungen, für die es keinen Partner gibt.
    Dort ist ``film_category.film_id`` dann leer (NULL). Diese Zahlungen
    würden in ``get_sales_per_category`` (normale JOINs) stillschweigend
    wegfallen.
    """
    payments_without_category = query_scalar("""
        SELECT count(*)
        FROM payment
        LEFT JOIN rental
            ON rental.rental_id = payment.rental_id
        LEFT JOIN inventory
            ON inventory.inventory_id = rental.inventory_id
        LEFT JOIN film_category
            ON film_category.film_id = inventory.film_id
        WHERE film_category.film_id IS NULL
    """)

    assert payments_without_category == 0


def test_films_can_have_multiple_categories():
    """
    In dieser Pagila-Version gehören Filme zu mehreren Kategorien.

    Dokumentiert die Datengrundlage für Variante A: Gäbe es nur eine
    Kategorie pro Film, wäre die Mehrfachzählung überflüssig und die Summe
    über alle Kategorien müsste genau dem Gesamtumsatz entsprechen.
    """
    category_assignments = query_scalar("SELECT count(*) FROM film_category")
    films_with_category = query_scalar("SELECT count(DISTINCT film_id) FROM film_category")

    assert category_assignments > films_with_category
