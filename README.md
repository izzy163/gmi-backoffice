# GMI Equipment — Back Office

Inventory, catalog, quotes/orders/invoices, customers, suppliers, service jobs and day-to-day books.
One static page (`index.html`) backed by a Supabase project (Postgres + logins + live sync).

## Setup (one time)

1. **Supabase project** — supabase.com → New project. Then run `schema.sql` in SQL Editor.
2. **Keys** — Project Settings → API: paste the Project URL and anon key into the two
   `window.SUPABASE_*` lines near the top of `index.html`.
3. **Logins** — Authentication → Providers → Email: turn **off** "Allow new users to sign up"
   (staff are invited, never self-registered). Authentication → URL Configuration: set
   **Site URL** to the page's address (e.g. `https://<user>.github.io/gmi-backoffice/`).
   Authentication → Users → **Invite user** for yourself and each staff member.
4. **Hosting** — push this folder to GitHub, Settings → Pages → deploy from `main` / root.

## Changing things later

Edit `index.html`, commit, push. GitHub Pages redeploys in about a minute.
Database changes go in `schema.sql` (it is safe to re-run) so they stay tracked.

## Data

Each table is `id, data (jsonb), created_at, updated_at`. The flat views `v_units` and
`v_orders` are for reporting tools or an accountant. Supabase → Database → Backups holds
daily backups; the app's Settings page also exports every list as CSV.

## Direct email (Resend)

`supabase/functions/send-doc/index.ts` sends quotes/invoices from the app. Deploy it as an Edge
Function named `send-doc` (dashboard editor or `supabase functions deploy send-doc`), and set
secrets `RESEND_API_KEY`, `FROM_EMAIL` (an address on the verified domain) and optionally `BCC_EMAIL`.
