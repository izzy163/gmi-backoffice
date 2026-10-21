-- GMI Equipment back office — database setup
-- Paste this whole file into Supabase → SQL Editor → New query → Run. Safe to run more than once.

create extension if not exists pgcrypto;

create or replace function public.touch_updated_at() returns trigger language plpgsql as $$
begin new.updated_at := now(); return new; end $$;

do $$
declare t text;
begin
  foreach t in array array['units','products','customers','suppliers','orders','jobs','expenses','settings'] loop
    execute format('
      create table if not exists public.%I (
        id          text primary key,
        data        jsonb not null default ''{}''::jsonb,
        created_at  timestamptz not null default now(),
        updated_at  timestamptz not null default now()
      )', t);
    execute format('alter table public.%I enable row level security', t);
    -- Signed-in staff can do everything; nobody else can touch the data.
    execute format('drop policy if exists "staff read" on public.%I', t);
    execute format('drop policy if exists "staff write" on public.%I', t);
    execute format('create policy "staff read"  on public.%I for select to authenticated using (true)', t);
    execute format('create policy "staff write" on public.%I for all    to authenticated using (true) with check (true)', t);
    -- Keep updated_at honest even if a client forgets it.
    execute format('drop trigger if exists set_updated_at on public.%I', t);
    execute format('create trigger set_updated_at before update on public.%I for each row execute function public.touch_updated_at()', t);
  end loop;
end $$;

-- Live updates between staff screens.
do $$
declare t text;
begin
  foreach t in array array['units','products','customers','suppliers','orders','jobs','expenses','settings'] loop
    if not exists (select 1 from pg_publication_tables where pubname='supabase_realtime' and schemaname='public' and tablename=t) then
      execute format('alter publication supabase_realtime add table public.%I', t);
    end if;
    execute format('alter table public.%I replica identity full', t);
  end loop;
end $$;

-- Company details (edit later in the app under Settings).
insert into public.settings (id, data) values ('company', jsonb_build_object(
  'companyName', 'GMI Equipment',
  'address', '334 Autumn Rd, Lakewood, NJ 08701',
  'phone', '732-901-1300',
  'email', 'izzy@gmiequipment.com',
  'taxRate', 6.625,
  'warrantyDays', 90,
  'terms', 'Used and open-box equipment carries a 90-day local warranty from the delivery date, covering parts and labor for defects within our local service area. Quotes are valid for 14 days. Equipment remains the property of the seller until paid in full.'
)) on conflict (id) do nothing;

-- Flat views for your accountant or any reporting tool (read-only, same security as the tables).
create or replace view public.v_units with (security_invoker = true) as
select id,
  data->>'tag' as tag, data->>'title' as description, data->>'brand' as brand, data->>'model' as model,
  data->>'serial' as serial, data->>'category' as category, data->>'condition' as condition, data->>'status' as status,
  data->>'location' as location, (data->>'cost')::numeric as purchase_cost, (data->>'freight')::numeric as freight,
  (data->>'palletizing')::numeric as palletizing, (data->>'repairLabor')::numeric as repair_labor, (data->>'repairParts')::numeric as repair_parts,
  coalesce((data->>'cost')::numeric,0)+coalesce((data->>'freight')::numeric,0)+coalesce((data->>'palletizing')::numeric,0)
    +coalesce((data->>'repairLabor')::numeric,0)+coalesce((data->>'repairParts')::numeric,0) as landed_cost,
  (data->>'price')::numeric as asking_price, data->>'dateIn' as date_in, data->>'soldDate' as sold_date, created_at, updated_at
from public.units;

create or replace view public.v_orders with (security_invoker = true) as
select o.id, (o.data->>'number')::int as number, o.data->>'status' as stage,
  coalesce(c.data->>'company', c.data->>'name') as customer, o.data->>'date' as date, o.data->>'invoiceDate' as invoice_date,
  o.data->>'deliveredDate' as delivered_date, (o.data->>'taxExempt')::boolean as tax_exempt,
  (select coalesce(sum((l->>'qty')::numeric*(l->>'price')::numeric),0) from jsonb_array_elements(coalesce(o.data->'lines','[]'::jsonb)) l) as subtotal,
  (select coalesce(sum((p->>'amount')::numeric),0) from jsonb_array_elements(coalesce(o.data->'payments','[]'::jsonb)) p) as paid,
  o.created_at, o.updated_at
from public.orders o left join public.customers c on c.id = o.data->>'customerId';
