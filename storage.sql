-- Photo storage for the back office. Paste into Supabase → SQL Editor → Run (safe to re-run).
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('photos', 'photos', true, 10485760, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = true;

drop policy if exists "photos public read" on storage.objects;
drop policy if exists "photos staff upload" on storage.objects;
drop policy if exists "photos staff update" on storage.objects;
drop policy if exists "photos staff delete" on storage.objects;
create policy "photos public read"  on storage.objects for select using (bucket_id = 'photos');
create policy "photos staff upload" on storage.objects for insert to authenticated with check (bucket_id = 'photos');
create policy "photos staff update" on storage.objects for update to authenticated using (bucket_id = 'photos');
create policy "photos staff delete" on storage.objects for delete to authenticated using (bucket_id = 'photos');
