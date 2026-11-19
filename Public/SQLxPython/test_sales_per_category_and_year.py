"""
Tests für ``database.get_sales_per_category_and_year`` (Abschlussprojekt, Teil 3).

Ausführen im Notebook (Ordner des Notebooks ist das Arbeitsverzeichnis):

    import sys
    !{sys.executable} -m pytest -v test_sales_per_category_and_year.py

Ohne Dateinamen (``-m pytest -v``) laufen alle Testdateien im Ordner.

Die Tests laufen gegen die echte Pagila-Datenbank. PostgreSQL muss also
laufen und erreichbar sein.

Wie in Teil 2 gilt "Variante A": Ein Film mit mehreren Kategorien zählt voll
in jeder seiner Kategorien. Die Tests vergleichen die Jahreswerte deshalb mit
``get_sales_per_category`` (gleiche Regel) und nicht mit dem Gesamtumsatz.
"""

import pandas
import pytest
import sqlalchemy

import database


# --- Erwartete Werte --------------------------------------------------
EXPECTED_COLUMNS = ["year", "category", "amount"]
EXPECTED_CATEGORY_COUNT = 16


# --- Hilfsfunktion ----------------------------------------------------
def query_scalar(sql):
    """
    Führt eine SQL-Abfrage aus, die genau einen Wert liefert, und gibt
    diesen Wert zurück (z. B. für ``SELECT sum(...)`` oder ``count(*)``).
    """
    with database.pagila.connect() as connection:
        return connection.execute(sqlalchemy.text(sql)).scalar()


# --- Fixtures ---------------------------------------------------------
@pytest.fixture(scope="module")
def sales_per_category_and_year():
    """Ergebnis von ``get_sales_per_category_and_year``, einmal pro Datei abgefragt."""
    return database.get_sales_per_category_and_year()


@pytest.fixture(scope="module")
def payment_years():
    """
    Alle Jahre, in denen es Zahlungen gibt, aufsteigend sortiert.

    Wird direkt aus ``payment`` gelesen, damit die Tests nicht von fest
    eingetragenen Jahreszahlen abhängen.
    """
    sql = """
        SELECT DISTINCT EXTRACT(YEAR FROM payment_date)::int AS year
        FROM payment
        ORDER BY year
    """
    with database.pagila.connect() as connection:
        return [row.year for row in connection.execute(sqlalchemy.text(sql))]


# --- Tests: Form des Ergebnisses --------------------------------------
def test_returns_dataframe(sales_per_category_and_year):
    """Das Ergebnis ist ein pandas-DataFrame."""
    assert isinstance(sales_per_category_and_year, pandas.DataFrame)


def test_column_names(sales_per_category_and_year):
    """Die Spalten heißen ``year``, ``category`` und ``amount``."""
    assert list(sales_per_category_and_year.columns) == EXPECTED_COLUMNS


def test_no_missing_values(sales_per_category_and_year):
    """Keine Spalte enthält leere Werte."""
    assert not sales_per_category_and_year.isna().any().any()


def test_year_is_integer(sales_per_category_and_year):
    """
    Das Jahr ist eine ganze Zahl (z. B. 2022) und kein Datum oder 2022.0.

    Sonst setzt matplotlib Achsenmarkierungen bei halben Jahren (2022.5).
    """
    assert pandas.api.types.is_integer_dtype(sales_per_category_and_year["year"])


# --- Tests: Jahre und Kategorien --------------------------------------
def test_years_match_payment_table(sales_per_category_and_year, payment_years):
    """Es sind genau die Jahre enthalten, in denen es Zahlungen gibt."""
    assert sorted(sales_per_category_and_year["year"].unique()) == payment_years


def test_every_year_has_all_categories(sales_per_category_and_year):
    """Jedes Jahr hat einen Wert für alle 16 Kategorien (keine Lücke im Diagramm)."""
    categories_per_year = sales_per_category_and_year.groupby("year")["category"].nunique()
    assert (categories_per_year == EXPECTED_CATEGORY_COUNT).all()


def test_year_category_pairs_unique(sales_per_category_and_year):
    """Jede Kombination aus Jahr und Kategorie kommt nur einmal vor."""
    assert not sales_per_category_and_year.duplicated(subset=["year", "category"]).any()


def test_row_count(sales_per_category_and_year, payment_years):
    """Anzahl Zeilen = Anzahl Jahre x 16 Kategorien."""
    assert len(sales_per_category_and_year) == len(payment_years) * EXPECTED_CATEGORY_COUNT


def test_pivot_works(sales_per_category_and_year, payment_years):
    """
    Das Ergebnis lässt sich so umformen, wie es das Notebook für das
    Liniendiagramm tut: eine Zeile pro Jahr, eine Spalte pro Kategorie.
    """
    pivot = sales_per_category_and_year.pivot(index="year", columns="category", values="amount")
    assert pivot.shape == (len(payment_years), EXPECTED_CATEGORY_COUNT)


# --- Tests: Umsätze ---------------------------------------------------
def test_amounts_positive(sales_per_category_and_year):
    """Jeder Jahreswert ist größer als 0."""
    assert (sales_per_category_and_year["amount"] > 0).all()


def test_years_add_up_to_category_totals(sales_per_category_and_year):
    """
    Die Jahreswerte einer Kategorie ergeben zusammen ihren Gesamtumsatz.

    Vergleich mit ``get_sales_per_category`` (Teil 2): Beide Funktionen
    nutzen dieselbe JOIN-Kette, die Aufteilung nach Jahren darf also keinen
    Umsatz verlieren oder hinzufügen.
    """
    per_year_summed = sales_per_category_and_year.groupby("category")["amount"].sum()
    totals = database.get_sales_per_category().set_index("category")["amount"]

    for category, total in totals.items():
        assert per_year_summed[category] == pytest.approx(total), category


def test_total_matches_category_total(sales_per_category_and_year):
    """Die Summe aller Zeilen entspricht der Summe aus Teil 2."""
    category_total = database.get_sales_per_category()["amount"].sum()
    assert sales_per_category_and_year["amount"].sum() == pytest.approx(category_total)
