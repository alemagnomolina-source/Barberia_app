import sqlite3
from datetime import date

def cerrar_dia():
    conn = sqlite3.connect("barberia.db")
    cur = conn.cursor()

    hoy = date.today().isoformat()

    cur.execute("""
        UPDATE consultas_v2
        SET estado = 'ausente'
        WHERE fecha LIKE ?
    """, (hoy + "%",))

    conn.commit()
    conn.close()