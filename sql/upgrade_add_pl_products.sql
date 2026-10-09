-- ARGOS Guatemala | ACTUALIZACIÓN SOBRE TABLA EXISTENTE (NO BORRA DATOS)
-- Ejecutar una sola vez en Supabase > SQL Editor > New query.
-- Esta migración permite guardar ECO PL, UNO PL y GU PL conservando los anteriores.
-- No volver a ejecutar sql/schema.sql para actualizar el catálogo existente.
BEGIN;

ALTER TABLE public.inventory_records
    DROP CONSTRAINT IF EXISTS inventory_records_product_check;

ALTER TABLE public.inventory_records
    ADD CONSTRAINT inventory_records_product_check
    CHECK (product IN (
        'UNO', 'ECO', 'GU', 'HE',
        'ECO PL', 'UNO PL', 'GU PL'
    ));

COMMIT;

-- Consulta opcional de verificación tras aplicar la migración:
-- SELECT product, count(*) AS capturas
-- FROM public.inventory_records GROUP BY product ORDER BY product;
