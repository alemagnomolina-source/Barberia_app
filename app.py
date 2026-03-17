from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, date, timedelta
import sqlite3
import os

from database_practica import (
    obtener_consultas,
    insertar_consulta,
    asignar_turno,
    marcar_atendido,
    marcar_ausente,
    cerrar_dia,
    estadisticas_del_dia,
    obtener_horas_ocupadas,
    obtener_turnos_semana,
    obtener_consultas_por_fecha,
    obtener_consulta_por_id,
)

from notificaciones import notificar, confirmar_turno

app = Flask(__name__)
app.secret_key = "barberia_secreta"

USUARIO = "admin"
PASSWORD = "1234"


# -----------------------
# HOME
# -----------------------
@app.route("/")
def inicio():
    return redirect(url_for("crear_consulta"))


# -----------------------
# CONSULTAS
# -----------------------
@app.route("/consultas")
def ver_consultas():
    if "logueado" not in session:
        return redirect(url_for("login"))

    consultas = obtener_consultas()
    return render_template("consultas.html", consultas=consultas)


@app.route("/consulta", methods=["GET", "POST"])
def crear_consulta():
    if request.method == "POST":
        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        servicio = request.form["servicio"]
        mensaje = request.form["mensaje"]

        insertar_consulta(nombre, telefono, servicio, mensaje)

        notificar("consulta_nueva", {
            "nombre": nombre,
            "telefono": telefono,
            "servicio": servicio,
            "mensaje": mensaje
        })

        return render_template("consulta_enviada.html")

    return render_template("nueva_consulta.html")


# -----------------------
# TURNOS
# -----------------------
@app.route("/asignar_turno/<int:consulta_id>")
def ver_form_asignar_turno(consulta_id):
    if "logueado" not in session:
        return redirect(url_for("login"))

    fecha = request.args.get("fecha") or date.today().isoformat()

    horas_ocupadas = obtener_horas_ocupadas(fecha)

    horarios = ["10:00","11:00","12:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"]

    return render_template(
        "asignar_turno.html",
        consulta_id=consulta_id,
        horarios=horarios,
        horas_ocupadas=horas_ocupadas,
        fecha=fecha
    )


@app.route("/guardar_turno/<int:consulta_id>", methods=["POST"])
def guardar_turno(consulta_id):
    if "logueado" not in session:
        return redirect(url_for("login"))

    fecha_turno = request.form["fecha_turno"]
    hora_turno = request.form["hora_turno"]

    asignar_turno(consulta_id, fecha_turno, hora_turno)

    consulta = obtener_consulta_por_id(consulta_id)

    nombre = consulta[1]
    telefono = consulta[2]
    servicio = consulta[3]

    confirmar_turno(telefono, nombre, fecha_turno, hora_turno, servicio)

    return redirect(url_for("agenda", fecha=fecha_turno))


# -----------------------
# AGENDA DIARIA
# -----------------------
@app.route("/agenda")
def agenda():
    if "logueado" not in session:
        return redirect(url_for("login"))

    fecha = request.args.get("fecha") or date.today().isoformat()

    consultas = obtener_consultas_por_fecha(fecha)

    horarios = ["10:00","11:00","12:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"]

    agenda = {h: None for h in horarios}

    for c in consultas:
        hora = c[6]
        agenda[hora] = c

    return render_template("agenda.html", fecha=fecha, horarios=horarios, agenda=agenda)


@app.route("/atendido/<int:turno_id>")
def marcar_turno_atendido(turno_id):
    if "logueado" not in session:
        return redirect(url_for("login"))

    marcar_atendido(turno_id)
    return redirect(url_for("agenda"))


@app.route("/ausente/<int:turno_id>")
def marcar_turno_ausente(turno_id):
    if "logueado" not in session:
        return redirect(url_for("login"))

    marcar_ausente(turno_id)
    return redirect(url_for("agenda"))


@app.route("/cerrar_dia")
def cerrar_dia_route():
    if "logueado" not in session:
        return redirect(url_for("login"))

    hoy = date.today().isoformat()
    cerrar_dia(hoy)

    return redirect(url_for("agenda"))


# -----------------------
# ESTADÍSTICAS
# -----------------------
@app.route("/estadisticas")
def estadisticas():
    fecha = request.args.get("fecha") or date.today().isoformat()

    stats = estadisticas_del_dia(fecha)

    return render_template("estadisticas.html", stats=stats, fecha=fecha)


# -----------------------
# AGENDA SEMANAL
# -----------------------
@app.route("/agenda_semana")
def agenda_semana():
    if "logueado" not in session:
        return redirect(url_for("login"))

    hoy = datetime.now().date()

    inicio = hoy - timedelta(days=hoy.weekday())
    fin = inicio + timedelta(days=6)

    turnos = obtener_turnos_semana(inicio.isoformat(), fin.isoformat())

    eventos = [
        {
            "title": f"{turno[1]} - {turno[3]}",
            "start": f"{turno[5]}T{turno[6]}"
        }
        for turno in turnos
    ]

    return render_template("agenda_semana.html", eventos=eventos)


# -----------------------
# DASHBOARD
# -----------------------
@app.route("/dashboard")
def dashboard():
    if "logueado" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("barberia.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT servicio, COUNT(*)
        FROM consultas
        WHERE estado = 'atendido'
        GROUP BY servicio
    """)
    data = cursor.fetchall()

    servicios = {servicio: cantidad for servicio, cantidad in data}

    precios = {
        "Corte": 12000,
        "Barba": 8000,
        "Corte + Barba": 15000
    }

    total = sum(precios.get(s, 0) * c for s, c in servicios.items())

    servicio_mas_vendido = max(servicios, key=servicios.get) if servicios else "Ninguno"

    hoy = date.today().isoformat()

    cursor.execute("""
        SELECT servicio FROM consultas
        WHERE fecha = ? AND estado = 'atendido'
    """, (hoy,))
    ingresos_hoy = sum(precios.get(s, 0) for (s,) in cursor.fetchall())

    semana = (date.today() - timedelta(days=7)).isoformat()

    cursor.execute("""
        SELECT servicio FROM consultas
        WHERE fecha >= ? AND estado = 'atendido'
    """, (semana,))
    ingresos_semana = sum(precios.get(s, 0) for (s,) in cursor.fetchall())

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        ingresos_hoy=ingresos_hoy,
        ingresos_semana=ingresos_semana,
        servicio_mas_vendido=servicio_mas_vendido,
        servicios=servicios
    )


# -----------------------
# LOGIN
# -----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["usuario"] == USUARIO and request.form["password"] == PASSWORD:
            session["logueado"] = True
            return redirect(url_for("ver_consultas"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def inicio():
    return redirect("/consulta")

# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)