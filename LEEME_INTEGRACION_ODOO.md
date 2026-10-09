# ARGOS Guatemala — Integración Odoo 17 (PICK Listos)

## Qué archivos cargar en GitHub Web

Conserva la estructura de carpetas al subirlos a la rama `main`:

| Ruta en GitHub | Acción |
|---|---|
| `app.py` | Reemplazar archivo existente |
| `src/style.py` | Reemplazar archivo existente |
| `src/odoo_integration.py` | Crear archivo nuevo |
| `tests/test_odoo_integration.py` | Crear archivo de pruebas (recomendado) |

**No reemplazar** `src/db.py`, `src/report.py`, `src/config.py`, otros archivos ni tablas de Supabase.

## Secrets de Streamlit Community Cloud

Agregar las siguientes variables **en el nivel raíz** a los Secrets de la aplicación Streamlit, sin borrar los secretos que ya funcionan para Supabase o el PIN del supervisor:

```toml
ODOO_URL = "https://TU_SERVIDOR_ODOO"
ODOO_DB = "NOMBRE_DE_TU_BASE"
ODOO_USERNAME = "TU_USUARIO_DE_ODOO"
ODOO_API_KEY = "TU_API_KEY_OD00"
```

Reemplaza los cuatro valores con tus credenciales **reales**. La API Key no debe guardarse en GitHub ni compartirse por mensajes.

Después de guardar Secrets, reinicia el despliegue si Streamlit no toma los cambios.

## Criterios funcionales

- **Morales**: `stock.picking.picking_type_id = 3`.
- **Morales 2**: `picking_type_id = 36`.
- **Bárcenas**: `picking_type_id = 19`.
- Solo operaciones `state = 'assigned'` (estado **Listo**).
- **Sin filtro `scheduled_date`**: todas las fechas y pedidos listos actualmente.
- Conteo por producto = número de operaciones únicas que contienen el SKU.
- Total/subtotal PEDIDOS = número de operaciones PICK únicas de la bodega, sin duplicar una operación que contenga varios productos.
- **ECO**: SKU `10002` y **UNO**: SKU `10004`, unidad `Sacos`, 42.5 kg por saco.
- PEDIDOS (TON) = demanda en sacos × `0.0425`; redondeo al entero más cercano, después de agregar.
- Unidades o SKUs no confirmados no se convierten. Se presenta advertencia si existen.
- Odoo solo se consulta desde el servidor y solo con llamadas XML-RPC de lectura.
- Consulta reutilizada hasta un máximo de 120 segundos mediante caché; botón de actualización manual en el panel del supervisor.

## Diferencia de fechas (importante)

- El calendario de **Streamlit/Supabase** determina qué capturas aparecen en el semáforo.
- Los pedidos de **Odoo** representan un **estado actual**, consultado al abrir/actualizar el panel, y **NO se filtran por el calendario**.
- Si abres un día antiguo, Odoo muestra pedidos listos **ahora**, no los que estaban listos aquel día. Para reportes históricos fiables deben programarse snapshots de Odoo en Supabase (no incluidos en esta actualización).

## Si no aparecen valores de Odoo

El panel indica explícitamente cuando faltan Secrets o cuando Odoo no responde. Las celdas moradas permanecen en blanco, **no en cero**, si falta la conexión. Si Streamlit Community Cloud no tiene acceso de red al host corporativo de Odoo, solicita al equipo de redes una ruta o integración de lectura autorizada; no modifiques secretos ni expongas la API Key.

## Validación

El ZIP incluye las pruebas `tests/test_odoo_integration.py` que comprueban conteo de operaciones únicas, cantidades, subgrupos, SKU desconocido, redondeos y errores de conexión. No cambia estructura SQL.
