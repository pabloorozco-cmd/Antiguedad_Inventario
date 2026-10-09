[LEEME_ACTUALIZACION.md](https://github.com/user-attachments/files/33229977/LEEME_ACTUALIZACION.md)
# ARGOS Guatemala — Mejor legibilidad del semáforo

Actualización incremental para GitHub Web. Reemplaza solamente los archivos siguientes, conservando sus rutas:

- `app.py`
- `src/style.py`

## Cambios

1. La tabla del supervisor tiene encabezados, cifras, bodegas, productos, subtotales y total general con tipografías mayores. En escritorio y TV conserva las diez columnas; si el ancho disponible es insuficiente se puede desplazar horizontalmente, sin cortar las cifras.
2. La presentación en tabletas y smartphones continúa en tarjetas, con letras y valores mejorados.
3. Se eliminan solamente los subtítulos bajo «SACOS REGISTRADOS» y «TONELADAS REGISTRADAS». Se conserva «Antigüedad al día de registro» bajo «MÁS DE 10 DÍAS».
4. Se conservan colores ARGOS y Odoo, agrupación por bodega, subtotales, TOTAL GENERAL y cálculos existentes.

## Cómo subir desde GitHub Web

1. Abre tu repositorio `Antiguedad_Inventario` en la rama `main`.
2. Abre `app.py` y sustituye su contenido por el incluido en el ZIP; confirma el cambio.
3. Abre `src/style.py` y sustituye su contenido por el incluido en el ZIP; confirma el cambio.
4. Espera el redespliegue de Streamlit y recarga la aplicación.

No requiere migraciones SQL, cambios de Supabase ni modificaciones a Secrets.

## Verificación

Se ejecutaron 46 pruebas automatizadas del proyecto: satisfactorias. Se comprobó la sintaxis Python y la presencia de los estilos de aumento de tipografía. No se realizó verificación visual en un navegador de producción.
