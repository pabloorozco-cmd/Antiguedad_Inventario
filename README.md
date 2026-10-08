# ARGOS Guatemala — Registro de inventario y producción

**Streamlit + Supabase + GitHub · Pantone 382 C, 2768 C y blanco**

Aplicación operativa para registrar **producto, cantidad de sacos y fecha de producción** con **usuario, bodega, modalidad de apoyo y fecha/hora de captura automáticos**. Incluye pantalla de acceso, formulario responsivo, resumen de últimas capturas e historial por bodega.

> **Alcance importante:** esta versión registra capturas, **no inventario neto disponible**. Aún no descuenta despachos, ajustes, roturas ni traslados de estibas. La edad en pantalla es la edad desde la fecha de producción informada, no una certificación de existencia física o de calidad.

## 1. Funcionalidades incluidas

- **Acceso:** el operario elige su bodega habitual y su nombre de una lista dependiente.
- **Apoyo temporal:** activa `Apoyo` para registrar en otra bodega; guarda tanto bodega habitual como bodega de operación.
- **Productos:** UNO, ECO, GU y HE. Colores corporativos de identificación provistos.
- **Captura:** sacos (entero positivo) y fecha `Producción` seleccionada desde calendario.
- **Fecha/hora:** `created_at` lo asigna automáticamente el servidor PostgreSQL de Supabase al guardar. Se almacena en UTC y se **muestra** en hora de Guatemala (`dd/mm/yyyy hh:mm:ss`, 24 horas).
- **Equivalencia:** referencia de 40 sacos por estiba, sin obligar múltiplos de 40.
- **Historial:** 12 últimas capturas de la bodega de operación, sus cantidades y edad en días.
- **Idempotencia:** `request_id` permite reintentar envíos sin duplicar la captura.
- **Seguridad:** secretos exclusivamente en servidor; RLS habilitado y roles públicos sin permiso sobre la tabla. PIN personal opcional, ver apartado de seguridad.
- **Diseño:** aplicación responsive inspirada en ARGOS, con azul marino `#071D49`, lima `#C4D600` y blanco.

### Personal configurado

| Bodega habitual | Usuarios |
|---|---|
| Morales 2 | Edwin Ramírez |
| Morales | Jefrie Anthony Sandoval Estrada; Oscar Ovidio Molina Montesinos; Henry Geovanni Ramírez; Mateo Adonai Santiago; Sergio Gustavo Pascual; Julio Cesar Hernández; Lester Iván Alvarado López |
| Bárcenas | Pedro Chajón; Herbert Estuardo Méndez Paiz; Edsson Alexander Vargas Puluc; Emerson Alexander Chavarria Zamora |

## 2. Estructura del repositorio

```text
argos-inventario/
├── app.py                          # App Streamlit: acceso, apoyo, captura, historial
├── src/
│   ├── __init__.py
│   ├── auth.py                     # Hash / validación opcional de PIN
│   ├── config.py                   # Bodegas, nombres, productos, paleta
│   ├── db.py                       # Supabase: inserción y consultas
│   ├── domain.py                   # Validación, antigüedad, hora Guatemala
│   └── style.py                    # Diseño premium corporativo
├── assets/
│   └── brand-mark.svg              # Icono de la app, no logo oficial
├── sql/
│   └── schema.sql                  # Esquema e índices Supabase
├── scripts/
│   └── generate_pin_hash.py        # Configuración opcional de PIN
├── tests/
│   ├── test_auth.py
│   └── test_domain.py
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example       # Plantilla; NO contiene claves reales
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## 3. Crear la base de datos Supabase

1. Entra a [Supabase](https://supabase.com/dashboard) y crea un proyecto.
2. Abre **SQL Editor** → **New query**.
3. Copia **todo** `sql/schema.sql` y ejecuta **Run**.
4. Verifica en **Table Editor** que exista `public.inventory_records`.
5. En **Project Settings → API Keys**, obtén la URL del proyecto y una clave de servidor con privilegios `service_role` (los nombres de los controles pueden variar). La clave **nunca va en GitHub ni en el navegador**.
6. En **Data API → Settings**, verifica que la API de datos esté disponible y que `public` esté expuesto. La tabla tiene RLS y `anon`/`authenticated` no reciben privilegios de lectura o escritura.

Las columnas almacenadas son `id`, `request_id`, `created_at`, `employee_name`, `home_warehouse`, `warehouse`, `is_support`, `product`, `sacks`, `production_date`.

> **No compartas la clave `service_role`**. Esta llave permite operaciones privilegiadas sobre tu base de datos. Sólo debe permanecer en Secrets del servidor Streamlit. Para entornos corporativos se recomienda una API backend con permisos mínimos y autenticación empresarial.

## 4. Instalar y ejecutar localmente

Necesitas **Python 3.11 o 3.12** y conexión a Supabase.

En **Windows PowerShell**:

```powershell
cd argos-inventario
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
notepad .streamlit\secrets.toml
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Si no tienes Python 3.12, puedes usar `py -3.11` en los comandos correspondientes.

En **Linux/macOS**:

```bash
cd argos-inventario
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

Completa `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "TU_CLAVE_PRIVADA_DE_SERVIDOR"
AUTH_MODE = "selector"
```

Sin los secretos, la interfaz funciona **en modo vista previa**, pero **no guarda registros**.

## 5. Subir manualmente a GitHub

1. Descomprime el ZIP.
2. Crea un repositorio nuevo en [github.com/new](https://github.com/new), por ejemplo `argos-inventario-guatemala`.
3. Abre tu repositorio y selecciona **Add file → Upload files**.
4. Sube el **contenido de la carpeta** `argos-inventario` (no solamente el archivo ZIP). Mantén carpetas y rutas, incluyendo `.streamlit/config.toml`.
5. Verifica que **`app.py` y `requirements.txt` estén en la raíz del repositorio**.
6. Confirma el commit.
7. **No subas** `.streamlit/secrets.toml`, claves Supabase ni archivos `.env`.

GitHub puede no mantener carpetas vacías, pero todos los directorios de este repo tienen archivos.

## 6. Desplegar con Streamlit Community Cloud

1. Ingresa a [share.streamlit.io](https://share.streamlit.io/).
2. Pulsa **Create app**, conecta GitHub y selecciona el repositorio.
3. Configura la rama `main` y **Main file path:** `app.py`.
4. En **Advanced settings → Secrets**, pega los valores de Supabase en formato TOML:

```toml
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "TU_CLAVE_PRIVADA_DE_SERVIDOR"
AUTH_MODE = "selector"
```

5. Elige **Python 3.12**, si aparece en la selección de versión.
6. Pulsa **Deploy**. Streamlit instala `requirements.txt` automáticamente.
7. Abre la URL `*.streamlit.app`, elige usuario, prueba un registro y revisa la fila en Supabase.
8. Controla quién puede **acceder a la app** con la configuración de compartición de Streamlit o redes corporativas; de ser público, activa como mínimo el PIN, aunque para uso empresarial es mejor SSO.

Documentación oficial: [Deploy Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) · [Secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## 7. Seguridad del inicio de sesión

Por petición, `AUTH_MODE = "selector"` permite que el empleado se identifique **seleccionando su nombre**. Este modo **no autentica** al usuario: cualquier persona que tenga acceso a la app podría escoger el nombre de otro. **No se recomienda para producción sin restricción de acceso.**

Puedes activar un PIN personal:

1. Ejecuta `python scripts/generate_pin_hash.py` por cada empleado.
2. Introduce el nombre exacto y un PIN. El script devuelve una línea TOML con el **hash**, sin guardar el PIN en texto claro.
3. Modifica tus Secrets **sin subirlos al repositorio**:

```toml
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "CLAVE_PRIVADA"
AUTH_MODE = "pin"

[PIN_HASHES]
"Edwin Ramírez" = "pbkdf2_sha256$450000$..."
"Jefrie Anthony Sandoval Estrada" = "pbkdf2_sha256$450000$..."
# Completar hashes para TODOS los demás usuarios.
```

4. Guarda los secretos. Si falta un hash, ese usuario no podrá iniciar sesión en modo PIN.

**Límite del PIN:** esta implementación no tiene protección de identidad empresarial ni un control global de intentos entre sesiones. Para datos críticos o acceso público se recomienda integrar SSO corporativo/Entra ID con control de acceso y auditoría centralizada.

## 8. Cómo opera un registro

1. Operario de Morales inicia sesión; por defecto, su bodega activa es **Morales**.
2. Si va a **Bárcenas** de apoyo, activa `Apoyo` antes de ingresar y escoge **Bárcenas**.
3. Selecciona `ECO`, registra `80` sacos y una fecha en `Producción`.
4. Al guardar, Postgres genera automáticamente `created_at` en UTC. La interfaz lo muestra en hora de Guatemala: `08/10/2026 16:30:00` (ejemplo).
5. El registro contiene `home_warehouse="Morales"`, `warehouse="Bárcenas"` e `is_support=true`.
6. En **Actividad de la bodega** se muestran los 12 registros más recientes de Bárcenas.

## 9. Pruebas automáticas

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Cobertura de catálogo, validación de usuario/bodega, regla de apoyo, producto, cantidad, fecha futura, timezone de Guatemala, cálculo de edad y verificación de PIN.

## 10. Evolución recomendada para el control real de inventario

Este primer alcance cumple exactamente los campos pedidos. Para el control de **existencia y vejez física** en los almacenes se necesitaría agregar posteriormente: identificador de estiba (40 sacos), ubicación/torre, ingresos y salidas, movimientos de apoyo, conteos cíclicos, lote y/o documento de origen, bloqueo de Calidad y saldo de inventario por estiba. **No interpretar las capturas registradas en esta versión como stock disponible.**
