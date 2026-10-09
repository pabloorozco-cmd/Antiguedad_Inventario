[LEEME.md](https://github.com/user-attachments/files/33229644/LEEME.md)
# ARGOS Guatemala — Subtotales por bodega

Actualización incremental del repositorio `Antiguedad_Inventario`.

## Archivos a reemplazar en GitHub Web

1. `app.py` — reemplazar en la raíz de la rama `main`.
2. `src/style.py` — reemplazar dentro de la carpeta `src`.

**No subir la carpeta `ARGOS_Subtotales_por_Bodega` como una carpeta adicional al repositorio:** colocar cada archivo en la ruta exacta indicada arriba.

## Funcionalidad

- El nombre de cada bodega aparece una sola vez, centrado verticalmente, abarcando todas sus filas de productos y la fila subtotal.
- Al final de cada bodega aparece una fila **SUBTOTAL**, con sumas de verde, amarillo, naranja, rojo y total de sacos.
- **TOTAL (TON)** = total de sacos de la bodega × 0.0425, redondeado al entero más cercano (mitades hacia arriba). Se redondea el subtotal agregado, NO se suman toneladas previamente redondeadas de cada producto.
- **PEDIDOS** y **PEDIDOS (TON)** permanecen vacíos hasta la integración con Odoo.
- **TOTAL GENERAL** continúa apareciendo al final y sigue calculado a partir de todos los sacos registrados.
- En teléfonos y tabletas pequeñas, los productos se muestran como tarjetas y cada bodega incluye una tarjeta de subtotal.
- El archivo CSV descargable incorpora las filas SUBTOTAL por bodega.

## Ejemplo con datos ilustrativos

| Bodega | Subtotal sacos | Subtotal ton |
|---|---:|---:|
| Morales 2 | 3,200 | 136 |
| Morales | 440 | 19 |
| TOTAL GENERAL | 3,640 | 155 |

## Pasos de despliegue sin GitHub Desktop

1. Descomprime el ZIP.
2. En GitHub Web, abre `app.py`, pulsa el ícono de editar, reemplaza el contenido y guarda con **Commit changes**.
3. Repite en `src/style.py`.
4. Espera a que Streamlit vuelva a desplegar. Actualiza la página (Ctrl+F5 si es necesario).

No necesitas ejecutar SQL ni actualizar Supabase o los Secrets.

**Nota:** los reportes consolidan CAPTURAS del día seleccionado, no saldo de inventario neto; aún no hay movimientos de salida cargados.
