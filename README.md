# PLC Server — Registro de Accesos Siemens

Servicio Windows que escucha conexiones TCP de un PLC Siemens y registra los datos de acceso de usuarios en un archivo CSV. Corre 24/7 como servicio nativo de Windows vía NSSM, con reconexión automática y tres capas de robustez.

---

## ¿Qué hace?

Cuando el PLC detecta un evento de acceso (pulso de disparo), envía por TCP una trama con los datos del usuario almacenados en el DB del PLC. Este servidor los recibe, los parsea y los guarda en un CSV en disco.

```
PLC Siemens (TSEND_C) ──TCP:2000──► PLC_Server.exe ──► D:\log_plc.csv
```

---

## Estructura del proyecto

```
PLC_Server/
├── plc_server.py          # Script principal
├── requirements.txt       # Dependencias Python
├── dist/
│   └── PLC_Server.exe     # Ejecutable compilado (se puede poner en carpeta inicio si no se quiere hacer como servicio)
└── README.md
```

---

## Formato de datos

El PLC envía una sola trama CSV de máximo 50 caracteres por conexión con el siguiente formato:

```
AÑO,MES,DIA,HORA,MIN,SEG,ID_USUARIO,NOMBRE,RANGO
```

**Ejemplo:**
```
2024,05,19,08,30,45,12,GARCIA,3
```

El timestamp es responsabilidad del PLC (reloj interno del Siemens), no de la PC receptora.

---

## Requisitos

- Windows 10 / 11
- Python 3.8+ *(solo en la máquina de desarrollo para compilar)*
- [PyInstaller](https://pyinstaller.org/) *(solo para compilar el `.exe`)*
- [NSSM](https://nssm.cc/) *(para registrar el servicio Windows)*

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/PLC_Server.git
cd PLC_Server
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Compilar el ejecutable

```bash
python -m PyInstaller --onefile --noconsole --name PLC_Server plc_server.py
```

El `.exe` quedará en `dist\PLC_Server.exe`. Cópialo a:

```
C:\Servicios\PLC_Server\PLC_Server.exe
```

### 4. Descargar NSSM

Descarga NSSM desde [nssm.cc/download](https://nssm.cc/download), extrae `nssm.exe` de la carpeta `win64` y cópialo a:

```
C:\Servicios\nssm.exe
```

### 5. Registrar el servicio Windows

Abre CMD **como administrador** y ejecuta:

```cmd
C:\Servicios\nssm.exe install PLC_Server "C:\Servicios\PLC_Server\PLC_Server.exe"
C:\Servicios\nssm.exe set PLC_Server DisplayName "PLC Server - Registro de Accesos"
C:\Servicios\nssm.exe set PLC_Server Description "Recibe y registra datos de acceso desde PLC Siemens"
C:\Servicios\nssm.exe set PLC_Server Start SERVICE_AUTO_START
C:\Servicios\nssm.exe set PLC_Server AppRestartDelay 5000
sc failure PLC_Server reset= 86400 actions= restart/5000/restart/5000/restart/5000
```

### 6. Iniciar el servicio

```cmd
C:\Servicios\nssm.exe start PLC_Server
```

Respuesta esperada:
```
PLC_Server: START: The operation completed successfully.
```

---

## Configuración

Las variables de configuración están al inicio de `plc_server.py`:

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `HOST` | `0.0.0.0` | Escucha en todas las interfaces de red |
| `PORT` | `2000` | Puerto TCP (debe coincidir con el TSEND_C del PLC) |
| `CSV_PATH` | `D:\log_plc.csv` | Ruta del archivo de registros |
| `LOG_PATH` | `D:\log_plc_errores.log` | Ruta del log de errores |
| `BUFFER_SIZE` | `256` | Tamaño máximo del buffer de recepción en bytes |
| `RETRY_DELAY` | `5` | Segundos entre reintentos si el socket falla |

---

## Archivos generados en disco

| Archivo | Descripción |
|---|---|
| `D:\log_plc.csv` | Registro de accesos. Se crea automáticamente si no existe. |
| `D:\log_plc_errores.log` | Log de errores y eventos del servicio. |

**Cabeceros del CSV:**
```
año,mes,dia,hora,min,seg,id_usuario,nombre,rango
```

---

## Arquitectura de robustez

El servicio opera con tres capas de protección para garantizar disponibilidad 24/7:

| Capa | Evento | Respuesta |
|---|---|---|
| **1** | Conexión PLC cae o falla de red | El socket espera nuevas conexiones sin reiniciar el proceso |
| **2** | Error en un dato recibido | Se descarta solo esa conexión, el servidor sigue activo |
| **3** | El proceso muere (caso extremo) | NSSM reinicia el servicio automáticamente en 5 segundos |

---

## Control del servicio

```cmd
# Ver estado
C:\Servicios\nssm.exe status PLC_Server

# Detener
C:\Servicios\nssm.exe stop PLC_Server

# Iniciar
C:\Servicios\nssm.exe start PLC_Server

# Desinstalar completamente
C:\Servicios\nssm.exe remove PLC_Server confirm
```

También puedes controlarlo desde la interfaz gráfica:
`Windows + R` → `services.msc` → buscar **"PLC Server - Registro de Accesos"**

> **Nota:** Al desinstalar el servicio, el archivo CSV y el log de errores **no se eliminan**. Los datos quedan intactos en `D:\`.

---

## Lado PLC (Siemens TIA Portal)

El bloque SCL del PLC construye la trama con `VAL_STRG` y `CONCAT`, la almacena en `"MA300".BUFFER` (STRING de 50 caracteres) y la envía mediante `TSEND_C` al puerto 2000 de la PC cuando se activa la señal de disparo `#START`.

Los datos origen son:
- `"MA300".FECHA` — estructura DTL con año, mes, día, hora, minuto y segundo
- `"MA300".ID_USUARIO` — INT con el identificador del usuario
- `"MA300".NOMBRE["MA300".X]` — STRING con el nombre del usuario
- `"MA300".RANGO["MA300".X]` — INT con el nivel de acceso

---

## Licencia

MIT