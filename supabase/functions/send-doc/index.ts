// Supabase Edge Function: send-doc
// Sends a quote / order / invoice email to a customer through Resend, on behalf of a signed-in staff member.
// Secrets required (Edge Functions → Secrets): RESEND_API_KEY, FROM_EMAIL. Optional: BCC_EMAIL.
import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  // Only signed-in staff may send.
  const authHeader = req.headers.get("Authorization") ?? "";
  const supa = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_ANON_KEY")!, {
    global: { headers: { Authorization: authHeader } },
  });
  const { data: { user }, error: uerr } = await supa.auth.getUser();
  if (uerr || !user) return json({ error: "Not signed in" }, 401);

  const key = Deno.env.get("RESEND_API_KEY");
  const from = Deno.env.get("FROM_EMAIL");
  if (!key || !from) return json({ error: "Email isn't configured yet: set RESEND_API_KEY and FROM_EMAIL in Edge Function secrets." }, 500);

  let body: { to?: string; subject?: string; html?: string; text?: string; fromName?: string; replyTo?: string; cc?: string[] };
  try { body = await req.json(); } catch { return json({ error: "Bad request" }, 400); }
  const to = (body.to ?? "").trim();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(to)) return json({ error: "Enter a valid customer email address." }, 400);
  if (!body.subject || !body.html) return json({ error: "Missing subject or message." }, 400);

  const payload: Record<string, unknown> = {
    from: body.fromName ? `${body.fromName.replace(/[<>"]/g, "")} <${from}>` : from,
    to: [to],
    subject: body.subject.slice(0, 200),
    html: body.html,
    text: body.text ?? undefined,
    reply_to: body.replyTo || user.email || undefined,
  };
  const bcc = Deno.env.get("BCC_EMAIL");
  if (bcc) payload.bcc = [bcc];
  if (body.cc?.length) payload.cc = body.cc.slice(0, 5);

  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const out = await r.json().catch(() => ({}));
  if (!r.ok) return json({ error: out?.message || `Resend refused the message (${r.status})` }, 502);
  return json({ ok: true, id: out.id, sentBy: user.email });
});
