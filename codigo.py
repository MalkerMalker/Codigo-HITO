import json
import os

# 1. ARCHIVOS (Persistencia de datos)
def cargar_datos():
    # Si el archivo existe, lo leemos
    if os.path.exists("datos.json"):
        archivo = open("datos.json", "r")
        datos = json.load(archivo)
        archivo.close()
        return datos
    else:
        datos_nuevos = {
            "estacionamientos": {
                "E01": "ocupado",
                "E02": "ocupado",
                "E03": "libre"
            },
            # Horas ficticias de ejemplo, solo para que el cliente pueda
            # previsualizar que horas suelen estar libres antes de reservar.
            # No reemplazan el estado real (libre/reservado/ocupado).
            "horarios_disponibles": {
                "E01": [6, 7, 8, 9, 19, 20],
                "E02": [11, 12, 13, 14, 15],
                "E03": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                        14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            },
            "reservas": [],
            "incidencias": [],
            "plata_total": 0,
            "plata_propietarios": 0,
            "plata_admin": 0,
            "plata_operador": 0
        }
        return datos_nuevos

def guardar_datos(datos):
    archivo = open("datos.json", "w")
    json.dump(datos, archivo, indent=4)
    archivo.close()

# 2. FUNCIONES DE NEGOCIO
def calcular_tarifa(hora, cantidad_horas):
    precio_hora = 0
    # Entre 8 y 18 hrs vale $1000 los 30 min (2000 la hora)
    if hora >= 8 and hora < 18:
        precio_hora = 2000
    # Entre 6 y 8, y entre 18 y 21 hrs vale $700 los 30 min (1400 la hora)
    elif hora >= 6 and hora < 8:
        precio_hora = 1400
    elif hora >= 18 and hora < 21:
        precio_hora = 1400
    # Resto del dia vale $500 los 30 min (1000 la hora)
    else:
        precio_hora = 1000

    return precio_hora * cantidad_horas

# 3. FUNCIONES DEL PROPIETARIO
def registrar_estacionamiento(datos, estacionamiento):
    if estacionamiento in datos["estacionamientos"]:
        print("Error: ese estacionamiento ya esta registrado.")
        return

    datos["estacionamientos"][estacionamiento] = "ocupado"
    datos["horarios_disponibles"][estacionamiento] = [8, 9, 17, 18]
    guardar_datos(datos)
    print("Exito: se registro " + estacionamiento + ". Queda 'ocupado' hasta que lo ofrezcas.")

def ofrecer_estacionamiento(datos, estacionamiento):
    estado_actual = datos["estacionamientos"][estacionamiento]

    if estado_actual == "ocupado":
        datos["estacionamientos"][estacionamiento] = "libre"
        guardar_datos(datos)
        print("Exito: El estacionamiento " + estacionamiento + " ahora esta libre.")
    else:
        print("Error: El estacionamiento ya esta libre o lo tiene un cliente.")

def boton_lo_necesito(datos, estacionamiento):
    estado = datos["estacionamientos"][estacionamiento]

    if estado == "libre":
        datos["estacionamientos"][estacionamiento] = "ocupado"
        guardar_datos(datos)
        print("Exito: Recuperaste tu estacionamiento. Nadie lo estaba usando.")
        return

    if estado == "reservado":
        # Buscar cual es la reserva activa de este lugar
        reserva_encontrada = None
        for reserva in datos["reservas"]:
            if reserva["estacionamiento"] == estacionamiento and reserva["activa"] == True:
                reserva_encontrada = reserva
                break

        if reserva_encontrada is None:
            print("Error: hay una inconsistencia, no se encontro la reserva activa.")
            return

        # Buscar un lugar libre para mover al cliente
        nuevo_lugar = ""
        for est in datos["estacionamientos"]:
            if datos["estacionamientos"][est] == "libre":
                nuevo_lugar = est
                break

        # Si encontramos lugar, lo movemos
        if nuevo_lugar != "":
            reserva_encontrada["estacionamiento"] = nuevo_lugar
            datos["estacionamientos"][nuevo_lugar] = "reservado"
            mensaje = "Cliente movido al estacionamiento " + nuevo_lugar
        else:
            # Si no hay lugar, cancelamos la reserva
            reserva_encontrada["activa"] = False
            mensaje = "Reserva cancelada por falta de cupo."

        # Devolvemos el lugar al dueño y le damos la compensacion
        datos["estacionamientos"][estacionamiento] = "ocupado"
        datos["plata_propietarios"] = datos["plata_propietarios"] + 2000
        datos["incidencias"].append(mensaje)

        guardar_datos(datos)
        print("Alerta: " + mensaje)
        print("Se te sumaron $2000 de compensacion.")
        return

    # Si llega aca, el estado ya era "ocupado" (el dueño ya lo tenia)
    print("Error: El estacionamiento ya esta ocupado por ti.")

def ver_ingresos_propietarios(datos):
    plata = int(datos["plata_propietarios"])
    print("Plata acumulada para propietarios: $" + str(plata))

# 4. FUNCIONES DEL CLIENTE
def consultar_horas_libres(datos):
    print("\n--- HORAS LIBRES (referenciales) ---")
    for est in datos["estacionamientos"]:
        estado = datos["estacionamientos"][est]
        horas = datos["horarios_disponibles"].get(est, [])
        horas_texto = ", ".join(str(h) + ":00" for h in horas)
        if horas_texto == "":
            horas_texto = "sin datos"
        print(est + " (estado actual: " + estado + ") -> horas habituales libres: " + horas_texto)
    print("Nota: estas horas son referenciales. La disponibilidad real depende del estado actual del lugar.")

def reservar(datos, nombre, hora, duracion):
    # Buscar estacionamiento libre
    lugar_elegido = ""
    for est in datos["estacionamientos"]:
        if datos["estacionamientos"][est] == "libre":
            lugar_elegido = est
            break

    if lugar_elegido == "":
        print("Lo sentimos, no hay lugares libres.")
        return

    costo = calcular_tarifa(hora, duracion)

    # Crear los datos de la reserva
    nueva_reserva = {
        "id": len(datos["reservas"]) + 1,
        "cliente": nombre,
        "estacionamiento": lugar_elegido,
        "hora_llegada": hora,
        "duracion": duracion,
        "monto": costo,
        "activa": True
    }

    # Guardar todo
    datos["reservas"].append(nueva_reserva)
    datos["estacionamientos"][lugar_elegido] = "reservado"
    guardar_datos(datos)

    print("Exito: Se reservo el lugar " + lugar_elegido)
    print("Tu ID de reserva es " + str(nueva_reserva["id"]))
    print("Total a pagar: $" + str(costo))

def checkout(datos, id_reserva):
    for reserva in datos["reservas"]:
        if reserva["id"] == id_reserva and reserva["activa"] == True:
            reserva["activa"] = False

            # Liberar el lugar
            lugar = reserva["estacionamiento"]
            datos["estacionamientos"][lugar] = "libre"

            # Repartir la plata
            monto = reserva["monto"]
            datos["plata_total"] = datos["plata_total"] + monto
            datos["plata_propietarios"] = datos["plata_propietarios"] + (monto * 0.65)
            datos["plata_admin"] = datos["plata_admin"] + (monto * 0.10)
            datos["plata_operador"] = datos["plata_operador"] + (monto * 0.25)

            guardar_datos(datos)
            print("Checkout listo. Se pagaron $" + str(monto))
            return

    print("Error: Reserva no encontrada.")

# 5. FUNCIONES DE ADMINISTRACION
def ver_ocupacion(datos):
    libres = 0
    reservados = 0
    ocupados = 0

    for est in datos["estacionamientos"]:
        estado = datos["estacionamientos"][est]
        print(est + " esta " + estado)

        if estado == "libre":
            libres = libres + 1
        elif estado == "reservado":
            reservados = reservados + 1
        else:
            ocupados = ocupados + 1

    print("Resumen: " + str(libres) + " libres, " + str(reservados) + " reservados, " + str(ocupados) + " ocupados por dueños.")

def ver_plata(datos):
    total = int(datos["plata_total"])
    propietarios = int(datos["plata_propietarios"])
    admin = int(datos["plata_admin"])
    operador = int(datos["plata_operador"])

    print("Total transado: $" + str(total))
    print("Propietarios (65%): $" + str(propietarios))
    print("Administracion (10%): $" + str(admin))
    print("Operador (25%): $" + str(operador))

def ver_incidencias(datos):
    if len(datos["incidencias"]) == 0:
        print("No hay problemas registrados.")
    else:
        for problema in datos["incidencias"]:
            print("- " + problema)

# 6. MENU
def iniciar_programa():
    datos = cargar_datos()

    while True:
        print("\n--- SISTEMA DE ESTACIONAMIENTOS ---")
        print("1. Propietario")
        print("2. Cliente")
        print("3. Administracion")
        print("4. Salir")

        opcion = input("Elige una opcion: ")

        if opcion == "1":
            print("1. Registrar nuevo estacionamiento")
            print("2. Ofrecer lugar")
            print("3. Boton LO NECESITO")
            print("4. Ver mis ingresos")
            sub = input("Que quieres hacer: ")

            if sub == "1":
                est = input("Nombre de tu nuevo estacionamiento (ej E04): ")
                registrar_estacionamiento(datos, est)
            elif sub == "2":
                est = input("Nombre de tu estacionamiento (ej E01): ")
                if est in datos["estacionamientos"]:
                    ofrecer_estacionamiento(datos, est)
                else:
                    print("Error: ese estacionamiento no existe. Registralo primero.")
            elif sub == "3":
                est = input("Nombre de tu estacionamiento (ej E01): ")
                if est in datos["estacionamientos"]:
                    boton_lo_necesito(datos, est)
                else:
                    print("Error: ese estacionamiento no existe.")
            elif sub == "4":
                ver_ingresos_propietarios(datos)

        elif opcion == "2":
            print("1. Consultar horas libres")
            print("2. Reservar")
            print("3. Pagar (Checkout)")
            sub = input("Que quieres hacer: ")

            if sub == "1":
                consultar_horas_libres(datos)
            elif sub == "2":
                nombre = input("Tu nombre: ")
                hora = int(input("Hora de llegada (0-23): "))
                duracion = int(input("Cantidad de horas: "))
                reservar(datos, nombre, hora, duracion)
            elif sub == "3":
                id_res = int(input("Tu ID de reserva: "))
                checkout(datos, id_res)

        elif opcion == "3":
            print("1. Ver ocupacion")
            print("2. Ver plata repartida")
            print("3. Ver incidencias")
            sub = input("Que quieres hacer: ")

            if sub == "1": ver_ocupacion(datos)
            elif sub == "2": ver_plata(datos)
            elif sub == "3": ver_incidencias(datos)

        elif opcion == "4":
            print("Saliendo del programa...")
            break

# Arrancar el codigo
iniciar_programa()
