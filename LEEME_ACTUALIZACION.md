[LEEME_ACTUALIZACION.md](https://github.com/user-attachments/files/33261557/LEEME_ACTUALIZACION.md)
# ARGOS Guatemala — Capturas y semáforo 100% en toneladas

## Antes de actualizar GitHub: EJECUTAR SQL

1. Entra a Supabase > SQL Editor.
2. **Haz una copia de seguridad de `public.inventory_records`.**
3. Ejecuta `sql/upgrade_tonnes.sql` completo. El SQL es transaccional e idempotente:
   - Añade `tonnes numeric(14,4)` sin borrar registros.
   - Convierte los valores previos `sacks * 0.0425` en TON.
   - Permite nuevos ingresos directos en TON y conserva `sacks` como columna histórica.
   - Mantiene válidos los siete productos, incluidos los tres PL.
4. Comprueba por ejemplo:

```sql
SELECT product, sacks, tonnes, created_at
FROM public.inventory_records
ORDER BY created_at DESC
LIMIT 10;
```

Un registro antiguo con `sacks = 1400` debe mostrar `tonnes = 59.5000`.

## Después: actualizar GitHub Web

Sube los archivos de este ZIP en sus **rutas exactas**:

- `app.py` — REEMPLAZAR
- `src/config.py` — REEMPLAZAR
- `src/db.py` — REEMPLAZAR
- `src/domain.py` — REEMPLAZAR
- `src/report.py` — REEMPLAZAR
- `src/odoo_integration.py` — REEMPLAZAR
- `src/style.py` — REEMPLAZAR
- `sql/upgrade_tonnes.sql` — NUEVO
- `tests/test_tonnes.py` — NUEVO (opcional, recomendado)
- `tests/test_report.py` — REEMPLAZAR (pruebas)
- `tests/test_domain.py` — REEMPLAZAR (pruebas)
- `tests/test_odoo_integration.py` — REEMPLAZAR (pruebas)

No necesitas subir el ZIP a GitHub; súbelos descomprimidos, en sus carpetas.
Streamlit Community Cloud redesplegará automáticamente después del commit.

## Comportamiento

- El formulario ahora solicita **Cantidad (TON)** directamente con cuatro decimales.
- Los registros antiguos se han normalizado en Supabase a TON usando 0.0425 ton/saco.
- Semáforo, subtotales, tarjetas, historial y CSV se muestran en TON.
- Las cifras ejecutivas del semáforo continúan **redondeadas a números enteros**, tal como se había solicitado. El valor exacto queda guardado con cuatro decimales y se consulta en el historial.
- Odoo conserva su lógica (PICK 3 / 36 / 19, estado `assigned`, todas las fechas, SKU 10002/10004 de 42.5 kg).
- **Rudy Anavisca**: acceso con PIN existente, captura eligiendo bodega, y semáforo de todas las bodegas.
- **Edwin Ramírez, Jefrie Anthony Sandoval Estrada, Pedro Chajón**: seleccionan su nombre, sin PIN incluso si `AUTH_MODE = "pin"`, y ven las pestañas Registrar toneladas / Semáforo.
- Los demás operarios conservan el acceso habitual y solo su formulario/historial.

### Seguridad

El acceso sin contraseña está implementado porque se solicitó expresamente. **No autentica realmente la identidad** de Edwin, Jefrie o Pedro: cualquier persona que seleccione sus nombres podrá abrir sus vistas de supervisión, incluyendo datos de todas las bodegas. Si se requieren permisos estrictos, debe implementarse autenticación de identidad (por ejemplo, Microsoft/Google SSO).

## Validación

Se ejecutaron pruebas automatizadas sin credenciales, además de una simulación del reporte y CSV. No fue posible comprobar una conexión real de este entorno a Supabase ni a Odoo, ni visualizar el frontend en Streamlit Cloud.

## No modificar

- No cambies las variables Secrets de Supabase / Odoo.
- Rudy conserva el `SUPERVISOR_PIN_HASH` que ya funciona.
- No ejecutes `sql/schema.sql` otra vez: solo la migración nueva.
