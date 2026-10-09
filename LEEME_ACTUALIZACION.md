# ARGOS Guatemala — Ajustes visuales del supervisor

## Contenido

Solo se modificaron estos dos archivos:

- `app.py`
- `src/style.py`

## Cambios

1. El botón superior **⏻ Salir** (supervisor y operarios) ahora tiene fondo rojo ARGOS complementario, letras blancas, mayor altura, tipografía reforzada, efecto al pasar el cursor y contorno de foco para accesibilidad.
2. En **TOTAL GENERAL**, todos los valores numéricos (incluido VERDE) quedan alineados a la derecha, igual que los de las filas normales.
3. Títulos, valores y textos inferiores de las tres tarjetas se muestran en tamaños más grandes y legibles, con ajustes específicos para pantallas grandes y teléfonos.
4. La paleta ARGOS y el resto de la interfaz se mantienen.

## Actualizar usando solo GitHub Web

1. Descomprime este ZIP.
2. En el repositorio, reemplaza **`app.py`** por el que se incluye en la raíz del ZIP.
3. Reemplaza **`src/style.py`** conservando la carpeta `src`.
4. Confirma los cambios en la rama `main`. Streamlit redeplegará la aplicación automáticamente.
5. Si parece igual, recarga forzosamente la página del navegador (`Ctrl + Shift + R`).

No es necesario ejecutar SQL, cambiar credenciales de Supabase ni instalar nuevas dependencias.

## Verificación

- 44 pruebas existentes: superadas.
- 9 verificaciones de estilos/estructura: superadas.
- CSS analizado: 132 reglas, cero errores sintácticos detectados.
- Pendiente: validación visual en la app desplegada (no disponible en este entorno).
