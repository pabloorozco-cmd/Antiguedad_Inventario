-- ARGOS Guatemala | Ejecutar una sola vez en Supabase > SQL Editor.
-- La fecha y hora se guardan en UTC (timestamptz) y se muestran en America/Guatemala.

create extension if not exists pgcrypto;

create table if not exists public.inventory_records (
    id uuid primary key default gen_random_uuid(),
    request_id uuid not null unique,
    created_at timestamptz not null default now(),
    employee_name text not null check (length(trim(employee_name)) > 0),
    home_warehouse text not null check (home_warehouse in ('Morales', 'Morales 2', 'Bárcenas')),
    warehouse text not null check (warehouse in ('Morales', 'Morales 2', 'Bárcenas')),
    is_support boolean not null default false,
    product text not null check (product in ('UNO', 'ECO', 'GU', 'HE')),
    sacks integer not null check (sacks between 1 and 100000),
    production_date date not null check (production_date >= date '2000-01-01'),
    constraint support_matches_warehouse check (is_support = (home_warehouse <> warehouse))
);

create index if not exists idx_inventory_records_warehouse_created
    on public.inventory_records(warehouse, created_at desc);
create index if not exists idx_inventory_records_product_date
    on public.inventory_records(product, production_date);

-- Seguridad: la aplicación utiliza la clave service_role SOLO EN EL SERVIDOR.
-- Sin políticas para anon / authenticated, esos roles no pueden leer ni escribir.
alter table public.inventory_records enable row level security;
revoke all on table public.inventory_records from public, anon, authenticated;
grant select, insert on table public.inventory_records to service_role;

-- No se agregan políticas de RLS públicas deliberadamente.
-- Si ya se habían creado políticas sobre esta tabla, auditarlas/eliminarlas.

comment on table public.inventory_records is 'Capturas de producción de cemento por usuario y bodega de operación, Guatemala';
comment on column public.inventory_records.created_at is 'Timestamp autoritativo del servidor, guardado como timestamptz UTC';
comment on column public.inventory_records.production_date is 'Fecha de producción observada/seleccionada, no fecha de vencimiento';
comment on column public.inventory_records.request_id is 'Identificador de idempotencia para reintentos de captura';
