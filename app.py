from flask import Flask, render_template, request, redirect, url_for, session
from datetime  import date
import sqlite3
import datetime

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
    estadisticas_servicios
)

from notificaciones import notificar, confirmar_turno

PRECIOS = {
    "corte": 10000,
    "barba": 7000,
    "corte y barba": 13000
}


app = Flask(__name__)
app.secret_key = "barberia_secreta"
USUARIO = "admin"
PASSWORD = "1234"


@app.route("/consultas")
def ver_consultas():
    
    if "logueado" not in session:
     return redirect(url_for("login"))

    consultas = obtener_consultas()

    return render_template("consultas.html", consultas=consultas)


@app.route("/consulta", methods=["GET","POST"])
def crear_consulta():

    if request.method == "POST":

        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        servicio = request.form["servicio"]
        mensaje = request.form["mensaje"]

        insertar_consulta(nombre, telefono, servicio, mensaje)

        notificar(
            "consulta_nueva",
            {
                "nombre": nombre,
                "telefono": telefono,
                "servicio": servicio,
                "mensaje": mensaje
            }
        )

        return render_template("consulta_enviada.html")

    return render_template("nueva_consulta.html")


@app.route("/asignar_turno/<int:consulta_id>")
def ver_form_asignar_turno(consulta_id):

    fecha = request.args.get("fecha")

    if not fecha:
        fecha = date.today().isoformat()

    horas_ocupadas = obtener_horas_ocupadas(fecha)

    horarios = [
        "10:00",
        "11:00",
        "12:00",
        "16:00",
        "17:00",
        "18:00",
        "19:00",
        "20:00",
        "21:00",
        "22:00"
    ]

    return render_template(
    "asignar_turno.html",
    consulta_id=consulta_id,
    horarios=horarios,
    horas_ocupadas=horas_ocupadas,
    fecha=fecha
)


@app.route("/guardar_turno/<int:consulta_id>", methods=["POST"])
def guardar_turno(consulta_id):

    fecha_turno = request.form["fecha_turno"]
    hora_turno = request.form["hora_turno"]

    asignar_turno(consulta_id, fecha_turno, hora_turno)

    consulta = obtener_consulta_por_id(consulta_id)

    nombre = consulta[1]
    telefono = consulta[2]
    servicio = consulta[3]

    confirmar_turno(telefono, nombre, fecha_turno, hora_turno, servicio)

    return redirect(url_for("agenda", fecha=fecha_turno))

@app.route("/agenda")
def agenda():
    if "logueado" not in session:
     return redirect(url_for("login"))
    

    fecha = request.args.get("fecha")

    if not fecha:
        fecha = date.today().isoformat()

    consultas = obtener_consultas_por_fecha(fecha)

    horarios = [
        "10:00",
        "11:00",
        "12:00",
        "16:00",
        "17:00",
        "18:00",
        "19:00",
        "20:00",
        "21:00",
        "22:00"
    ]

    agenda = {}

    for h in horarios:
        agenda[h] = None

    for c in consultas:
        hora = c[6]
        agenda[hora] = c

    return render_template(
        "agenda.html",
        fecha=fecha,
        horarios=horarios,
        agenda=agenda
    )

@app.route("/atendido/<int:turno_id>")
def marcar_turno_atendido(turno_id):

    marcar_atendido(turno_id)

    return redirect(url_for("agenda"))


@app.route("/ausente/<int:turno_id>")
def marcar_turno_ausente(turno_id):

    marcar_ausente(turno_id)

    return redirect(url_for("agenda"))


@app.route("/cerrar_dia")
def cerrar_dia_route():

    hoy = date.today().isoformat()

    cerrar_dia(hoy)

    return redirect(url_for("agenda"))


@app.route("/estadisticas")
def estadisticas():

    fecha = request.args.get("fecha")

    if not fecha:
        fecha = date.today().isoformat()

    stats = estadisticas_del_dia(fecha)

    return render_template(
        "estadisticas.html",
        stats=stats,
        fecha=fecha
    )


@app.route("/agenda_semanal")
def agenda_semanal():

    from datetime import datetime, timedelta

    hoy = datetime.now().date()
    fin_semana = hoy + timedelta(days=7)

    turnos = obtener_turnos_semana(hoy, fin_semana)

    return render_template("agenda_semanal.html", turnos=turnos)

# --------------------------
# AGENDA SEMANA
# --------------------------
@app.route("/agenda_semana")
def agenda_semana():

    if "logueado" not in session:
        return redirect(url_for("login"))

    hoy = datetime.date.today()

    inicio = hoy - datetime.timedelta(days=hoy.weekday())
    fin = inicio + datetime.timedelta(days=6)

    turnos = obtener_turnos_semana(
        inicio.isoformat(),
        fin.isoformat()
    )

    eventos = []

    for turno in turnos:

        eventos.append({
            "title": f"{turno[1]} - {turno[3]}",
            "start": f"{turno[5]}T{turno[6]}"
        })

    return render_template(
        "agenda_semana.html",
        eventos=eventos
    )

# --------------------------
# DASHBOARD
# --------------------------
@app.route("/dashboard")
def dashboard():
    
    if "logueado" not in session:
     return redirect(url_for("login"))

    conn = sqlite3.connect("barberia.db")
    cursor = conn.cursor()

    # servicios realizados
    cursor.execute("""
    SELECT servicio, COUNT(*)
    FROM consultas
    WHERE estado = 'atendido'
    GROUP BY servicio
    """)

    data = cursor.fetchall()

    servicios = {}

    for servicio, cantidad in data:
        servicios[servicio] = cantidad


    # PRECIOS
    precios = {
        "Corte": 12000,
        "Barba": 8000,
        "Corte + Barba": 15000
    }


    # calcular ingresos totales
    total = 0

    for servicio, cantidad in servicios.items():
        total += precios.get(servicio, 0) * cantidad


    # servicio mas vendido
    servicio_mas_vendido = "Ninguno"

    if servicios:
        servicio_mas_vendido = max(servicios, key=servicios.get)


    # ingresos hoy
    hoy = datetime.date.today().isoformat()

    cursor.execute("""
    SELECT servicio
    FROM consultas
    WHERE fecha = ?
    AND estado = 'atendido'
    """, (hoy,))

    data_hoy = cursor.fetchall()

    ingresos_hoy = 0

    for (servicio,) in data_hoy:
        ingresos_hoy += precios.get(servicio, 0)


    # ingresos semana
    semana = datetime.date.today() - datetime.timedelta(days=7)

    cursor.execute("""
    SELECT servicio
    FROM consultas
    WHERE fecha >= ?
    AND estado = 'atendido'
    """, (semana.isoformat(),))

    data_semana = cursor.fetchall()

    ingresos_semana = 0

    for (servicio,) in data_semana:
        ingresos_semana += precios.get(servicio, 0)


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
# LOGIN DE BARBERO
# -----------------------
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        if usuario == USUARIO and password == PASSWORD:

            session["logueado"] = True

            return redirect(url_for("ver_consultas"))

    return render_template("login.html")

# ---------------------
# LOGOUT
# ---------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)