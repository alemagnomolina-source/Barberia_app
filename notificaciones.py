import webbrowser
import urllib.parse


def notificar(tipo, datos):

    if tipo == "consulta_nueva":

        nombre = datos["nombre"]
        telefono = datos["telefono"]
        servicio = datos["servicio"]

        mensaje = f"""
Nueva consulta recibida

Cliente: {nombre}
Tel: {telefono}
Servicio: {servicio}
"""

        numero_barberia = "5492302616904"

        mensaje_codificado = urllib.parse.quote(mensaje)

        url = f"https://wa.me/{numero_barberia}?text={mensaje_codificado}"

        webbrowser.open(url)
        
def confirmar_turno(telefono, nombre, fecha, hora, servicio):

    import urllib.parse

    mensaje = f"""
Hola {nombre} 👋

Tu turno fue confirmado

Fecha: {fecha}
Hora: {hora}
Servicio: {servicio}

Te esperamos en la barbería.
"""

    mensaje_codificado = urllib.parse.quote(mensaje)

    url = f"https://wa.me/549{telefono}?text={mensaje_codificado}"

    webbrowser.open(url)