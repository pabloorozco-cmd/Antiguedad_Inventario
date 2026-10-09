# ARGOS Guatemala — Corrección captura en sacos / reporte en toneladas

## Qué cambia
- El formulario solicita una **cantidad entera de sacos** (por defecto 40).
- El servidor valida la cantidad y calcula exactamente: `tonnes = sacks × 0.0425`.
- Se guardan **ambas** columnas `sacks` (cantidad física) y `tonnes` (valor convertido) en Supabase.
- El semáforo, KPIs, subtotales, histórico y CSV siguen mostrando **toneladas**.
- La lectura usa `select('*')` para reducir problemas de proyección de columnas tras la migración.
- Los errores de Supabase informan un código seguro en la pantalla, sin mostrar llaves o URL.

## Cómo actualizar desde GitHub Web
1. Abre el repositorio en la rama `main`.
2. Reemplaza **únicamente** los siguientes archivos con los contenidos del ZIP:
   - `app.py`
   - `src/db.py`
   - `src/domain.py`
3. Guarda/confirmar (Commit changes).
4. En Streamlit Community Cloud, espera el despliegue y utiliza `Manage app → Reboot app` si necesitas recargar.
5. Comprueba primero el semáforo, luego registra una prueba: `40` sacos de `UNO` (o la referencia que corresponda) = `1.7000` ton.

**No vuelvas a ejecutar** `sql/schema.sql` ni `sql/upgrade_tonnes.sql`: la migración de toneladas ya apareció como ejecutada correctamente en tu captura.

## Si sigue apareciendo error
Ahora el mensaje debería mostrar un **código** identificable, p. ej. 42703, 42501 o PGRST204. Envía el código, sin tus Secrets. Para más información abre `Manage app → Logs` y copia solo el texto técnico del error, ocultando credenciales o datos de clientes.

No se cambió Odoo, los permisos, las tablas del reporte ni los archivos de estilo.
