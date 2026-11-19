"""
Datenbankzugriff auf die Pagila-Übungsdatenbank.

Dieses Modul bündelt die Verbindung zu PostgreSQL und alle Abfragefunktionen,
die aus dem Notebook ``Roadmap.ipynb`` ausgelagert wurden (Phase 9 der Roadmap).
Das Notebook importiert das Modul mit ``import database`` und ruft die
Funktionen über ``database.<funktion>()`` auf.

Inhalt:
    pagila                            -- SQLAlchemy-Engine zur Datenbank ``pagila``
    get_sales_per_month               -- Umsatz pro Monat
    get_sales_per_category            -- Umsatz pro Filmkategorie
    get_sales_per_category_and_year   -- Umsatz pro Filmkategorie und Jahr

Hinweis zu den Kategorie-Funktionen ("Variante A"):
    Ein Film kann mehreren Kategorien angehören. Sein Umsatz zählt dann voll
    in jeder seiner Kategorien. Die Summe über alle Kategorien ist deshalb
    größer als der Gesamtumsatz in ``payment``. Kategorien lassen sich
    untereinander vergleichen, ihre Summe ist aber nicht der Gesamtumsatz.
"""

import pandas
import sqlalchemy


# --- Verbindung -------------------------------------------------------
PAGILA_DB_NAME = "pagila"
PAGILA_HOST = "localhost"
PAGILA_PORT = "5432"
PAGILA_USER = "accsess_pagila"
PAGILA_PASSWORD = "pagila_password"
PAGILA_URL = (
    f"postgresql+psycopg://{PAGILA_USER}:{PAGILA_PASSWORD}"
    f"@{PAGILA_HOST}:{PAGILA_PORT}/{PAGILA_DB_NAME}"
)

pagila = sqlalchemy.create_engine(PAGILA_URL)


# --- Abfragen ---------------------------------------------------------
def get_sales_per_month():
    """
    Ermittelt den Umsatz pro Monat aus der Tabelle ``payment``.

    Die Zahlungen werden mit ``date_trunc('month', ...)`` auf den Monatsanfang
    gekürzt und anschließend in ein reines Datum (``::date``) umgewandelt.
    Dadurch gibt es keine Zeitzone, die pandas beim Laden nach UTC umrechnen
    könnte. Gruppierung und Summe passieren komplett in der Datenbank.

    Rückgabe:
        pandas.DataFrame mit einer Zeile pro Monat, chronologisch sortiert:
            month -- erster Tag des Monats (datetime.date)
            sales -- Summe aller Zahlungen in diesem Monat (float)
    """
    query = sqlalchemy.text("""
        SELECT
            date_trunc('month', payment.payment_date)::date AS month,
            sum(payment.amount) AS sales
        FROM payment
        GROUP BY month
        ORDER BY month
    """)
    return pandas.read_sql(query, pagila)


def get_sales_per_category():
    """
    Ermittelt den Gesamtumsatz pro Filmkategorie.

    Der Weg von der Zahlung zur Kategorie führt über vier JOINs:
        payment -> rental -> inventory -> film_category -> category

    Ein Film mit mehreren Kategorien zählt voll in jeder davon (Variante A,
    siehe Modul-Docstring).

    Rückgabe:
        pandas.DataFrame mit einer Zeile pro Kategorie (16 Zeilen),
        nach Umsatz **aufsteigend** sortiert, damit ``barh`` die stärkste
        Kategorie oben zeichnet:
            amount   -- Umsatz der Kategorie (float)
            category -- Name der Kategorie (str)
    """
    query = sqlalchemy.text("""
        SELECT
            sum(payment.amount) AS amount,
            category.name AS category
        FROM payment
        JOIN rental
            ON rental.rental_id = payment.rental_id
        JOIN inventory
            ON inventory.inventory_id = rental.inventory_id
        JOIN film_category
            ON film_category.film_id = inventory.film_id
        JOIN category
            ON category.category_id = film_category.category_id
        GROUP BY category.name
        ORDER BY amount, category
    """)
    return pandas.read_sql(query, pagila)


def get_sales_per_category_and_year():
    """
    Ermittelt den Umsatz pro Filmkategorie und Kalenderjahr.

    Gleiche JOIN-Kette wie ``get_sales_per_category``, zusätzlich gruppiert
    nach dem Jahr der Zahlung. ``EXTRACT(YEAR ...)::int`` liefert die
    Jahreszahl als ganze Zahl (z. B. 2022), nicht als Datum.

    Das Ergebnis ist im "langen" Format (eine Zeile pro Jahr und Kategorie).
    Für ein Liniendiagramm mit einer Linie pro Kategorie wird es im Notebook
    mit ``pivot(index="year", columns="category", values="amount")``
    umgeformt.

    Rückgabe:
        pandas.DataFrame mit einer Zeile pro Kombination aus Jahr und Kategorie:
            year     -- Kalenderjahr (int)
            category -- Name der Kategorie (str)
            amount   -- Umsatz der Kategorie in diesem Jahr (float)
    """
    query = sqlalchemy.text("""
        SELECT
            EXTRACT(YEAR FROM payment.payment_date)::int AS year,
            category.name AS category,
            sum(payment.amount) AS amount
        FROM payment
        JOIN rental
            ON rental.rental_id = payment.rental_id
        JOIN inventory
            ON inventory.inventory_id = rental.inventory_id
        JOIN film_category
            ON film_category.film_id = inventory.film_id
        JOIN category
            ON category.category_id = film_category.category_id
        GROUP BY year, category.name
        ORDER BY year, category
    """)
    return pandas.read_sql(query, pagila)
