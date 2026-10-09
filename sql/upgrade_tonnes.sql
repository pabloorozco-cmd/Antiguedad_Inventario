-- ARGOS Guatemala | Ejecutar ANTES de publicar la aplicación nueva.
-- Preserva datos existentes. Convierte histórico sacks * 0.0425 a toneladas.
-- Nuevos registros almacenan toneladas directamente en public.inventory_records.tonnes.
BEGIN;
-- Conservar en el mismo cambio todos los productos actualmente habilitados en el formulario.
ALTER TABLE public.inventory_records
  DROP CONSTRAINT IF EXISTS inventory_records_product_check;
ALTER TABLE public.inventory_records
  ADD CONSTRAINT inventory_records_product_check
  CHECK (product IN ('UNO', 'ECO', 'GU', 'HE', 'ECO PL', 'UNO PL', 'GU PL'));
ALTER TABLE public.inventory_records
  ADD COLUMN IF NOT EXISTS tonnes numeric(14,4);
UPDATE public.inventory_records
   SET tonnes = round(sacks::numeric * 0.0425, 4)
 WHERE tonnes IS NULL AND sacks IS NOT NULL;
-- Las capturas nuevas ya no requieren el campo legado sacks.
ALTER TABLE public.inventory_records ALTER COLUMN sacks DROP NOT NULL;
ALTER TABLE public.inventory_records
  DROP CONSTRAINT IF EXISTS inventory_records_tonnes_positive;
ALTER TABLE public.inventory_records
  ADD CONSTRAINT inventory_records_tonnes_positive CHECK (tonnes > 0);
ALTER TABLE public.inventory_records
  ALTER COLUMN tonnes SET NOT NULL;
COMMENT ON COLUMN public.inventory_records.tonnes IS 'Captura real en toneladas; histórico convertido desde sacks*0.0425.';
COMMENT ON COLUMN public.inventory_records.sacks IS 'Campo legado (solo capturas previas), no se utiliza en nuevas capturas.';
COMMIT;
