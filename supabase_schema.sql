-- Saark Operating System: shared, multi-user cloud foundation.
-- Run this once in Supabase Dashboard -> SQL Editor -> New query.
-- The desktop application uses a publishable key and authenticated staff users;
-- never use the service-role key in the .exe.

create extension if not exists pgcrypto;

create table if not exists public.company_profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    username text unique not null,
    full_name text,
    role text not null default 'User',
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);

create or replace function public.create_company_profile()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.company_profiles (id, username, full_name)
    values (
        new.id,
        coalesce(new.raw_user_meta_data ->> 'username', split_part(new.email, '@', 1), new.id::text),
        coalesce(new.raw_user_meta_data ->> 'full_name', '')
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.create_company_profile();

create or replace function public.is_active_company_user()
returns boolean
language sql
stable
security definer set search_path = public
as $$
    select exists (
        select 1 from public.company_profiles
        where id = auth.uid() and is_active = true
    );
$$;

-- This common record store is the migration target for all existing CSV
-- collections and the two local SQLite databases. Each save is a single row,
-- allowing records to be updated independently by different users.
create table if not exists public.company_records (
    id uuid primary key default gen_random_uuid(),
    domain text not null,
    collection text not null,
    source_key text not null,
    data jsonb not null default '{}'::jsonb,
    record_version integer not null default 1,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    created_by uuid references auth.users(id),
    updated_by uuid references auth.users(id),
    unique (domain, collection, source_key)
);

create index if not exists company_records_lookup
    on public.company_records (domain, collection, updated_at desc);

create or replace function public.set_company_record_audit_fields()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    new.updated_at = now();
    new.updated_by = auth.uid();
    if tg_op = 'INSERT' then
        new.created_by = auth.uid();
    end if;
    return new;
end;
$$;

drop trigger if exists company_records_audit on public.company_records;
create trigger company_records_audit
before insert or update on public.company_records
for each row execute procedure public.set_company_record_audit_fields();

alter table public.company_profiles enable row level security;
alter table public.company_records enable row level security;

drop policy if exists "staff can view profiles" on public.company_profiles;
create policy "staff can view profiles" on public.company_profiles
for select to authenticated using (public.is_active_company_user());

drop policy if exists "staff can view company data" on public.company_records;
create policy "staff can view company data" on public.company_records
for select to authenticated using (public.is_active_company_user());

drop policy if exists "staff can add company data" on public.company_records;
create policy "staff can add company data" on public.company_records
for insert to authenticated with check (public.is_active_company_user());

drop policy if exists "staff can update company data" on public.company_records;
create policy "staff can update company data" on public.company_records
for update to authenticated
using (public.is_active_company_user())
with check (public.is_active_company_user());

drop policy if exists "staff can delete company data" on public.company_records;
create policy "staff can delete company data" on public.company_records
for delete to authenticated using (public.is_active_company_user());
