import itertools
import string
import os
import sys
import time
import gnupg
from multiprocessing import Pool, cpu_count, Manager

ARCHIVO_CIFRADO = "archive.pdf.gpg"
SALIDA_DESCIFRADA = "salida.pdf"
LONGITUD_MIN = 1
LONGITUD_MAX = 12
NUM_PROCESOS = cpu_count()  # para usar todos los núcleos disponibles

gpg = gnupg.GPG()

def probar_clave(args):  # función que va a probar todas las posibles combinaciones
    clave, stop_event = args

    # Si otro proceso ya encontró la clave, parar
    if stop_event.is_set():
        return False

    # combinaciones viene como tupla de caracteres; la convertimos a string
    clave = ''.join(clave)

    # Abrimos el archivo en modo binario con 'with' para que se cierre siempre correctamente
    with open(ARCHIVO_CIFRADO, "rb") as f:
        resultado = gpg.decrypt_file(f, passphrase=clave, output=SALIDA_DESCIFRADA)
        if resultado.ok:
            print(f"\nClave encontrada: {clave}")
            stop_event.set()
            return True

    return False

def fuerza_bruta():
    caracteres = string.ascii_lowercase  # solo letras minúsculas
    inicio = time.time()

    # Manager crea un Event compartido para señalizar parada entre procesos
    with Manager() as manager:
        stop_event = manager.Event()

        # iteramos por cada longitud de clave
        for longitud in range(LONGITUD_MIN, LONGITUD_MAX + 1):
            # comprobamos si ya encontramos la clave y salimos
            if stop_event.is_set():
                break

            print(f"Probando claves de longitud {longitud}")

            # se generan todas las posibles combinaciones
            combinaciones = itertools.product(caracteres, repeat=longitud)

            # Para cada combinación c genera la tupla (c, stop_event). el mismo evento para todas las c
            combinaciones_con_evento = ((c, stop_event) for c in combinaciones)

            # Crea un Pool de procesos hijos; 'with' asegura cierre correcto del pool
            with Pool(processes=NUM_PROCESOS) as pool:
                # Reparte las tareas entre los procesos: por cada elemento del generador
                # se invoca probar_clave
                pool.map(probar_clave, combinaciones_con_evento)

        fin = time.time()
        duracion = fin - inicio
        minutos = int(duracion // 60)
        segundos = int(duracion % 60)

        if not stop_event.is_set():
            print("No se encontró la clave.")
        print(f"\nTiempo total: {minutos} min {segundos} s")

if __name__ == "__main__":
    if not os.path.exists(ARCHIVO_CIFRADO):
        print(f"No se encuentra el archivo: {ARCHIVO_CIFRADO}")
        sys.exit(1)
    fuerza_bruta()

