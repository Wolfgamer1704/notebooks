"""
Datenbankzugriff auf die Pagila-Übungsdatenbank.

Dieses Modul bündelt die Verbindung zu PostgreSQL und alle Abfragefunktionen,
die aus dem Notebook ``Roadmap.ipynb`` ausgelagert wurden (Phase 9 der Roadmap).
Das Notebook importiert das Modul mit ``import database`` und ruft die
Funktionen über ``database.<funktion>()`` auf.

Inhalt:
    pagila                -- SQLAlchemy-Engine zur Datenbank ``pagila``
    get_sales_per_month   -- Umsatz pro Monat als DataFrame
"""

#Imports
import sqlalchemy
import pandas
import matplotlib.pyplot as plotter

#Pagila
name_pagila_db = "pagila"
host_pagila = "localhost"
port_pagila = "5432"
nutzer_pagila = "accsess_pagila"
passwort_pagila = "pagila_password"
pagila_adress = f"postgresql+psycopg://{nutzer_pagila}:{passwort_pagila}@{host_pagila}:{port_pagila}/{name_pagila_db}"
pagila =  sqlalchemy.create_engine(pagila_adress)


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
    action = """
            SELECT 
                date_trunc('month', payment.payment_date)::date As month,
                sum(payment.amount) AS Sales
            FROM
                payment
            GROUP BY
                month
            ORDER BY
                month, Sales
        """
    return pandas.read_sql(action, pagila)
