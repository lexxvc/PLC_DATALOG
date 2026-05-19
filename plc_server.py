import socket
import csv
import logging
import sys
import time
import signal
from datetime import datetime
from pathlib import Path

# ── Configuración ────────────────────────────────────────────
HOST        = '0.0.0.0'
PORT        = 2000
CSV_PATH    = Path(r'D:\log_plc.csv')
LOG_PATH    = Path(r'D:\log_plc_errores.log')
BUFFER_SIZE = 256
RETRY_DELAY = 5  # segundos entre reintentos si el socket falla
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log(msg, nivel='info'):
    getattr(logging, nivel)(msg)
    print(f"[{datetime.now():%H:%M:%S}] {msg}")

def inicializar_csv():
    if not CSV_PATH.exists():
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'SECOND', 'ID', 'NAME', 'RANGE'])
        log("CSV creado en " + str(CSV_PATH))

def guardar_dato(dato: str):
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # El dato ya viene como CSV desde el PLC, solo separamos
        campos = dato.strip().split(',')
        writer.writerow(campos)

def manejar_conexion(conn, addr):
    """CAPA 2 — errores aislados por conexión, el servidor nunca se cae"""
    ip = addr[0]
    try:
        chunks = []
        while True:
            parte = conn.recv(BUFFER_SIZE)
            if not parte:
                break
            chunks.append(parte)

        if chunks:
            raw = b''.join(chunks)
            dato = raw.decode('utf-8', errors='replace').strip()
            if dato:
                guardar_dato(dato)
                log(f"Guardado desde {ip}: {dato}")

    except Exception as e:
        log(f"Error en conexión de {ip}: {e}", 'error')
    finally:
        conn.close()

def crear_socket():
    """CAPA 1 — el socket se recrea si falla, nunca abandona"""
    while True:
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen(5)
            log(f"Escuchando en puerto {PORT}")
            return server
        except Exception as e:
            log(f"No se pudo abrir socket: {e} — reintentando en {RETRY_DELAY}s", 'warning')
            time.sleep(RETRY_DELAY)

def iniciar_servidor():
    inicializar_csv()
    log("Servicio PLC_Server iniciado")

    # Cierre limpio ante señal del sistema (NSSM lo usa al detener el servicio)
    def salir(sig, frame):
        log("Servicio detenido correctamente")
        sys.exit(0)

    signal.signal(signal.SIGINT, salir)
    signal.signal(signal.SIGTERM, salir)

    server = crear_socket()

    while True:
        try:
            conn, addr = server.accept()
            manejar_conexion(conn, addr)

        except OSError:
            # Socket cerrado intencionalmente (señal de stop)
            break

        except Exception as e:
            # CAPA 1 — cualquier fallo en accept() recrea el socket
            log(f"Error en servidor, recreando socket: {e}", 'error')
            time.sleep(RETRY_DELAY)
            server = crear_socket()

if __name__ == '__main__':
    iniciar_servidor()