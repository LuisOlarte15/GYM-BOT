# GYM BOT V16 — Wompi Checkout

Entrega de continuidad sobre GYM BOT V15. La aplicación conserva SQLite local y añade módulo de pagos Wompi Web Checkout y webhook firmado.

## Arranque
```powershell
python -m pip install -r requirements_V16.txt
.\configurar_GYM_BOT_V16.ps1
# Completa .env con Sandbox, URL HTTPS y precio.
python .\GYM_BOT_V16_WOMPI.py
```
Acceso local: `http://127.0.0.1:8000/app`

Consulta `DOCUMENTACION/INTEGRACION_WOMPI_V16.md` antes de configurar Wompi.

**Importante:** este paquete no debe publicarse aún como servicio comercial abierto. La integración de pagos está preparada, pero el resto de la aplicación heredada necesita completar la autorización backend y el endurecimiento de seguridad. La integración no está probada con una transacción real ni con credenciales de tu comercio.
