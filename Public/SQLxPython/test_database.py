"""
Tests für das Modul ``database``.

Ausführen im Notebook (Ordner des Notebooks ist das Arbeitsverzeichnis):

    !python -m pytest -v

pytest findet automatisch alle Dateien ``test_*.py`` und darin alle
Funktionen ``test_*``. Jede Funktion prüft mit ``assert`` eine Eigenschaft.

Die Tests laufen gegen die echte Pagila-Datenbank. PostgreSQL muss also
laufen und erreichbar sein. Die erwarteten Werte stammen aus den bisherigen
Ergebnissen im Notebook (Phase 3 und 4).
"""

import datetime

import pandas
import pytest
import sqlalchemy

import database


# --- Erwartete Werte --------------------------------------------------
EXPECTED_ROW_COUNT = 55
EXPECTED_COLUMNS = ["month", "sales"]
EXPECTED_FIRST_MONTH = datetime.date(2022, 1, 1)
EXPECTED_FIRST_SALES = 3091.79


# --- Fixture ----------------------------------------------------------
@pytest.fixture(scope="module")
def sales_per_month():
    """
    Führt ``get_sales_per_month`` einmal aus und gibt das Ergebnis an alle
    Tests weiter, die einen Parameter ``sales_per_month`` haben.

    ``scope="module"`` bedeutet: Die Abfrage läuft nur einmal für die ganze
    Datei, nicht einmal pro Test.
    """
    return database.get_sales_per_month()


# --- Tests: get_sales_per_month ---------------------------------------
def test_returns_dataframe(sales_per_month):
    """Das Ergebnis ist ein pandas-DataFrame."""
    assert isinstance(sales_per_month, pandas.DataFrame)


def test_row_count(sales_per_month):
    """Es gibt genau eine Zeile pro Monat, insgesamt 55."""
    assert len(sales_per_month) == EXPECTED_ROW_COUNT


def test_column_names(sales_per_month):
    """Die Spalten heißen ``month`` und ``sales`` (in dieser Reihenfolge)."""
    assert list(sales_per_month.columns) == EXPECTED_COLUMNS


def test_first_month(sales_per_month):
    """
    Die erste Zeile ist Januar 2022.

    Prüft auch, dass das Datum keine Zeitzonen-Verschiebung hat
    (früherer Fehler: 2021-12-31 23:00 UTC statt 2022-01-01).
    """
    assert sales_per_month["month"].iloc[0] == EXPECTED_FIRST_MONTH


def test_first_sales(sales_per_month):
    """
    Der Umsatz im Januar 2022 beträgt 3091.79.

    ``pytest.approx`` vergleicht Kommazahlen mit kleiner Toleranz, weil
    float-Werte nicht immer exakt darstellbar sind.
    """
    assert sales_per_month["sales"].iloc[0] == pytest.approx(EXPECTED_FIRST_SALES)


def test_months_sorted(sales_per_month):
    """Die Monate sind aufsteigend (chronologisch) sortiert."""
    assert sales_per_month["month"].is_monotonic_increasing


def test_months_unique(sales_per_month):
    """Jeder Monat kommt nur einmal vor (GROUP BY hat funktioniert)."""
    assert sales_per_month["month"].is_unique


def test_months_are_first_of_month(sales_per_month):
    """Jedes Datum ist der Erste eines Monats (date_trunc hat funktioniert)."""
    assert all(month.day == 1 for month in sales_per_month["month"])


def test_no_missing_values(sales_per_month):
    """Keine Spalte enthält leere Werte."""
    assert not sales_per_month.isna().any().any()


def test_sales_positive(sales_per_month):
    """Jeder Monatsumsatz ist größer als 0."""
    assert (sales_per_month["sales"] > 0).all()


def test_total_matches_payment_table(sales_per_month):
    """
    Die Summe aller Monate entspricht dem Gesamtumsatz der Tabelle ``payment``.

    Damit ist sichergestellt, dass beim Gruppieren keine Zahlung verloren
    gegangen oder doppelt gezählt worden ist.
    """
    query = sqlalchemy.text("SELECT sum(amount) FROM payment")
    with database.pagila.connect() as connection:
        total = float(connection.execute(query).scalar())

    assert sales_per_month["sales"].sum() == pytest.approx(total)
