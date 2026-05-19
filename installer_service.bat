C:\Servicios\nssm.exe install PLC_Server "C:\Servicios\PLC_Server\PLC_Server.exe"

C:\Servicios\nssm.exe set PLC_Server DisplayName "PLC Server - Registro de Accesos"
C:\Servicios\nssm.exe set PLC_Server Description "Recibe y registra datos de acceso desde PLC Siemens"
C:\Servicios\nssm.exe set PLC_Server Start SERVICE_AUTO_START
C:\Servicios\nssm.exe set PLC_Server AppRestartDelay 5000

sc failure PLC_Server reset= 86400 actions= restart/5000/restart/5000/restart/5000

C:\Servicios\nssm.exe start PLC_Server