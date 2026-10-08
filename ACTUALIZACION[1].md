# Actualización ARGOS · Responsive + Supervisor + Salir

## Archivos que debes reemplazar/agregar

Copia al repositorio **únicamente los archivos de este paquete**, respetando las rutas. No elimines los demás archivos del repositorio ni vuelvas a ejecutar `sql/schema.sql`: esta versión utiliza la misma tabla `inventory_records` y **no requiere cambios de esquema**.

| Archivo | Acción |
|---|---|
| `app.py` | Reemplazar |
| `src/config.py` | Reemplazar |
| `src/db.py` | Reemplazar |
| `src/style.py` | Reemplazar |
| `src/report.py` | Agregar |
| `.streamlit/secrets.toml.example` | Reemplazar (solo plantilla) |
| `tests/test_report.py` | Agregar (pruebas) |
| `ACTUALIZACION.md` | Agregar (estas instrucciones) |

## 1. Configurar acceso de Rudy Anavisca

En la pantalla inicial selecciona **Supervisión** en «Bodega habitual / tipo de acceso». Se mostrará el perfil **Rudy Anavisca**. Para que no baste escoger su nombre y obtener acceso a todas las bodegas, este perfil **siempre exige un PIN**, aunque los operarios ingresen mediante selector.

Genera un hash con la herramienta que **ya existe** en tu repositorio:

```bash
python scripts/generate_pin_hash.py
```

- Nombre que te pregunta el script: `Rudy Anavisca`.
- Introduce un PIN de al menos 6 caracteres y confirma.
- El script imprimirá `"Rudy Anavisca" = "pbkdf2_sha256$..."`.
- En Streamlit Community Cloud → **Manage app → Settings → Secrets** agrega:

```toml
SUPERVISOR_PIN_HASH = "pbkdf2_sha256$450000$...$..."
```

Pega **solo el hash generado**, no el PIN, y conserva tus secretos existentes `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y `AUTH_MODE`.

> No copies los valores de ejemplo de `.streamlit/secrets.toml.example` como si fueran credenciales reales. **No subas** `.streamlit/secrets.toml` a GitHub.

## 2. Semáforo supervisor

Elige **Día de registro** y **Bodega** (predeterminado «Todas»). La consulta a Supabase filtra por fecha de captura en horario `America/Guatemala`, incluyendo registros de todo el día seleccionado, con paginación.

- Agrupación: Bodega × Producto UNO/ECO/GU/HE.
- Verde: 0–10 días de edad desde producción.
- Amarillo: 11–15 días.
- Naranja: 16–20 días.
- Rojo: 21 días o más (incluye edades superiores a 30 días).
- Vista ancha en TV y computadores; tarjetas adaptadas para tabletas y móviles.
- Exporta semáforo y detalle CSV, con fecha, hora local, producto, sacos y operador.
- El botón **Salir** está visible en la vista operativa y en la de supervisión.

**Importante:** la tabla muestra los **sacos capturados ese día**, agrupados por la edad que tenían el día del registro. NO representa el saldo real de inventario, porque el sistema todavía no registra salidas, pedidos, ni ajustes. Tampoco se muestran columnas «Pedidos» y «TN pedidos» porque esa información no existe en Supabase. El reporte no inventa esos valores.

## 3. Mostrar toneladas (opcional)

Como el peso por saco de los diferentes productos **no se confirmó**, el semáforo muestra sacos de forma predeterminada. Para habilitar toneladas, declara pesos reales (kg por saco) en Streamlit Secrets, por ejemplo:

```toml
[PRODUCT_WEIGHT_KG]
UNO = 42.5
ECO = 42.5
GU = 42.5
HE = 42.5
```

**Estos cuatro 42.5 son exclusivamente un ejemplo técnico**, no una afirmación del peso comercial de ARGOS. Verifica cada peso con Calidad antes de usarlo. Si existe un producto capturado ese día sin peso configurado, el reporte completo seguirá mostrando sacos (evita sumar unidades mezcladas). Si los pesos varían por presentación, necesitarás registrar la presentación/peso en cada captura antes de convertir exactamente a toneladas.

## 4. Despliegue

1. Sube o reemplaza los archivos indicados en GitHub, manteniendo las carpetas `src/`, `.streamlit/` y `tests/`.
2. No cambies el archivo principal de Streamlit: continúa siendo **`app.py`**.
3. Añade el secret `SUPERVISOR_PIN_HASH` y guarda.
4. Streamlit redeplegará la aplicación tras el push a la rama de despliegue. Desde la app, selecciona Supervisión → Rudy Anavisca e introduce su PIN.
5. Comprueba en un teléfono, una tableta y una pantalla grande. Las tablas detalladas pueden desplazarse horizontalmente dentro de su contenedor, mientras que el semáforo cambia a tarjetas.

Para pruebas locales (si tienes dependencias instaladas):

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest -q
streamlit run app.py
```

**Sin cambios:** `sql/schema.sql`, `src/auth.py`, `src/domain.py`, `requirements.txt`, `.streamlit/config.toml`.
