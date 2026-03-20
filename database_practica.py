import sqlite3


def conectar():
    return sqlite3.connect("barberia.db")


# -------------------------
# CREAR TABLA 
# -------------------------
def crear_tabla():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    DROP TABLE IF EXISTS consultas
    """)

    cursor.execute ("""
    CREATE TABLE consultas
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    telefono TEXT,
    servicio TEXT,
    mensaje TEXT,
    fecha TEXT,
    hora TEXT,
    estado TEXT,
    usuario TEXT
""")

    conn.commit()
    conn.close()


# -------------------------------
# INSERTAR CONSULTA
# -------------------------------

def insertar_consulta(nombre, telefono, servicio, mensaje, usuario):
    conn = sqlite3.connect("barberia.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO consultas (nombre, telefono, servicio, mensaje, fecha, estado, usuario)
        VALUES (?, ?, ?, ?, date('now'), 'nuevo', ?)
    """, (nombre, telefono, servicio, mensaje, usuario))

    conn.commit()
    conn.close()


# -------------------------------
# OBTENER CONSULTAS PENDIENTES
# -------------------------------

def obtener_consultas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM consultas
    WHERE estado = 'pendiente'
    ORDER BY id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data


# -------------------------------
# ASIGNAR TURNO
# -------------------------------

def asignar_turno(consulta_id, fecha, hora):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE consultas
    SET fecha = ?, hora = ?, estado = 'confirmado'
    WHERE id = ?
    """, (fecha, hora, consulta_id))

    conn.commit()
    conn.close()


# -------------------------------
# HORAS OCUPADAS
# -------------------------------

def obtener_horas_ocupadas(fecha):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT hora
    FROM consultas
    WHERE fecha = ? AND estado = 'confirmado'
    """, (fecha,))

    horas = [h[0] for h in cursor.fetchall()]

    conn.close()

    return horas


# -------------------------------
# CONSULTAS POR FECHA (AGENDA)
# -------------------------------

def obtener_consultas_por_fecha(fecha):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM consultas
    WHERE fecha = ?
    AND estado IN ('confirmado','atendido','ausente')
    ORDER BY hora
    """, (fecha,))

    data = cursor.fetchall()

    conn.close()

    return data


# -------------------------------
# MARCAR ATENDIDO
# -------------------------------

def marcar_atendido(turno_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE consultas
    SET estado = 'atendido'
    WHERE id = ?
    """, (turno_id,))

    conn.commit()
    conn.close()


# -------------------------------
# MARCAR AUSENTE
# -------------------------------

def marcar_ausente(turno_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE consultas
    SET estado = 'ausente'
    WHERE id = ?
    """, (turno_id,))

    conn.commit()
    conn.close()


# -------------------------------
# CERRAR DIA
# -------------------------------

def cerrar_dia(fecha):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE consultas
    SET estado = 'ausente'
    WHERE fecha = ?
    AND estado = 'confirmado'
    """, (fecha,))

    conn.commit()
    conn.close()


# -------------------------------
# ESTADISTICAS
# -------------------------------

def estadisticas_del_dia(fecha):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT estado, COUNT(*)
    FROM consultas
    WHERE fecha = ?
    GROUP BY estado
    """, (fecha,))

    data = cursor.fetchall()

    conn.close()

    stats = {
        "nuevo": 0,
        "confirmado": 0,
        "atendido": 0,
        "ausente": 0,
        "total": 0
    }

    for estado, cantidad in data:
        stats[estado] = cantidad
        stats["total"] += cantidad

    return stats

# -------------------------------
# AGENDA SEMANAL
# -------------------------------

def obtener_turnos_semana(inicio, fin):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM consultas
    WHERE fecha BETWEEN ? AND ?
    AND estado IN ('confirmado','atendido','ausente')
    ORDER BY fecha, hora
    """, (inicio, fin))

    data = cursor.fetchall()

    conn.close()

    return data

# --------------------------
# CONSULTA POR ID
# --------------------------
def obtener_consulta_por_id(consulta_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM consultas
    WHERE id = ?
    """, (consulta_id,))

    consulta = cursor.fetchone()

    conn.close()

    return consulta

# -------------------------------
# SERVICIOS MAS VENDIDOS
# -------------------------------

def estadisticas_servicios():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT servicio, COUNT(*)
    FROM consultas
    WHERE estado = 'atendido'
    GROUP BY servicio
    """)

    data = cursor.fetchall()

    conn.close()

    servicios = {
        "Corte": 0,
        "Barba": 0,
        "Corte + Barba": 0
    }

    for servicio, cantidad in data:
        servicios[servicio] = cantidad

    return servicios

# --------------------------
# TEMPORAL
# --------------------------

if __name__ == "__main__":
    crear_tabla()