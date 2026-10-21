import re, sys
src = open('/home/claude/gmi-backoffice/src.html').read()

def swap(old, new, count=1):
    global src
    assert src.count(old) == count, f"expected {count} match for: {old[:60]!r}, got {src.count(old)}"
    src = src.replace(old, new)

# --- head: real document skeleton -------------------------------------------
swap('<title>QPS Back Office</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n',
'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>GMI Back Office</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%2313213a'/%3E%3Cpath d='M8 22V12l8-4 8 4v10' fill='none' stroke='%23e6b45a' stroke-width='3' stroke-linejoin='round'/%3E%3C/svg%3E">
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js"></script>
<script>
  // Fill these two in from Supabase → Project Settings → API. Both are public values.
  window.SUPABASE_URL = "__SUPABASE_URL__";
  window.SUPABASE_ANON_KEY = "__SUPABASE_ANON_KEY__";
</script>
''')

swap('<style>\n/* Layout:', '<style>\nhtml{color-scheme:light}\nbody{margin:0;font-size:14px}\nimg{max-width:100%}\n[hidden]{display:none!important}\n/* Layout:')

# login + account styles
swap('@media (prefers-reduced-motion:no-preference)',
'''.auth{min-height:100vh;display:grid;place-items:center;padding:24px max(16px,env(safe-area-inset-right,0px)) 24px max(16px,env(safe-area-inset-left,0px));background:var(--nav-bg)}
.authcard{width:min(400px,100%);background:var(--surface);border-radius:12px;padding:28px 26px;box-shadow:var(--shadow)}
.authcard .brand{padding:0 0 18px;font-size:24px}
.authcard .brand small{color:var(--muted)}
.authcard .fgrid{grid-template-columns:1fr}
.authcard .fld{grid-column:span 1}
.authcard .btn{width:100%;justify-content:center;padding:10px}
.authmsg{margin-top:12px;font-size:13px;color:var(--muted)}
.authmsg.err{color:var(--bad)}
.authlink{all:unset;cursor:pointer;color:var(--accent);font-size:13px;margin-top:14px;display:inline-block}
.who{font-size:11.5px;color:var(--nav-muted);padding:4px 10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media (prefers-reduced-motion:no-preference)''')

swap('<div class="shell">\n  <nav class="nav" id="nav" aria-label="Sections"></nav>\n  <main id="main"></main>\n</div>',
'''<div id="auth" class="auth" hidden></div>
<div class="shell" id="shell" hidden>
  <nav class="nav" id="nav" aria-label="Sections"></nav>
  <main id="main"></main>
</div>''')

# nav footer: who + sign out
swap('''   `<div class="spacer"></div><div class="conn"><span class="dot ${conn==='ok'?'ok':conn==='off'?'bad':''}"></span>${conn==='ok'?(canWrite?'Synced':'Read only'):conn==='off'?'Not connected':'Connecting…'}</div>`;''',
'''   `<div class="spacer"></div><div class="who" title="${esc(me&&me.email||'')}">${esc(me&&me.email||'')}</div><div class="conn"><span class="dot ${conn==='ok'?'ok':conn==='off'?'bad':''}"></span>${conn==='ok'?'Synced':conn==='off'?'Offline — retrying':'Connecting…'}</div><button data-act="signout">Sign out</button>`;''')
swap('''$('#nav').addEventListener('click',e=>{const b=e.target.closest('[data-view]');if(!b)return;''',
'''$('#nav').addEventListener('click',e=>{const so=e.target.closest('[data-act="signout"]');if(so){signOut();return}const b=e.target.closest('[data-view]');if(!b)return;''')
swap(".brand small,.nav .spacer,.conn,.nav .count{display:none}", ".brand small,.nav .spacer,.conn,.who,.nav .count{display:none}")

# banners no longer about claude.ai
swap('''  if(conn==='off')banner=`<div class="banner">The shared database isn't reachable in this view. Open this page in claude.ai while signed in to see and edit your records.</div>`;
  else if(conn==='ok'&&!canWrite)banner=`<div class="banner">You can view records but not change them. Ask the owner to share this page with you as a Contributor.</div>`;''',
'''  if(conn==='off')banner=`<div class="banner">Can't reach the database right now. Check your connection; this page retries on its own.</div>`;''')

swap('''    <h2 style="margin-top:22px">Staff access</h2>
    <p class="small muted">Share this page with staff as <strong>Contributor</strong> so they can add and update records. Viewers can look but not change anything.</p>''',
'''    <h2 style="margin-top:22px">Staff access</h2>
    <p class="small muted">Add or remove staff logins in your Supabase dashboard under <strong>Authentication → Users → Invite user</strong>. Each person gets an email to set their own password. Everyone who can sign in can see and edit all records.</p>
    <h2 style="margin-top:22px">Your password</h2>
    <div class="inline"><input id="pw_new" type="password" placeholder="New password (8+ characters)" autocomplete="new-password"><button class="btn" data-changepw>Change password</button></div>''')
swap("else if(t.dataset.export){exportCsv(t.dataset.export)}",
     "else if(t.dataset.export){exportCsv(t.dataset.export)}\n  else if(t.hasAttribute('data-changepw')){changePassword()}")
swap("[data-chip],[data-new],[data-neworder],[data-open],[data-cmode],[data-mtab],[data-savesettings],[data-export]",
     "[data-chip],[data-new],[data-neworder],[data-open],[data-cmode],[data-mtab],[data-savesettings],[data-export],[data-changepw]")

# downloads: plain browser download
swap('''async function saveFile(name,data){
  if(!downloads){toast('Downloads are not available in this view');return}
  try{await downloads.save({filename:name,data});}catch(err){if(err&&err.code==='declined')return;toast(err&&err.code==='rate_limited'?'A save is already waiting for your answer':'Could not save the file')}
}''',
'''function saveFile(name,data){
  const type=name.endsWith('.csv')?'text/csv;charset=utf-8':'text/html;charset=utf-8';
  const blob=new Blob([data],{type});const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),4000);
}''')
swap("function need(){if(!db){toast('Not connected to the database');return false}if(!canWrite){toast('You have view-only access');return false}return true}",
     "function need(){if(!db){toast('Not connected to the database');return false}return true}")

# --- boot: Supabase adapter + auth -------------------------------------------
boot_old = src[src.index('/* ---------- boot ---------- */'):src.index('})();\n})();\n</script>')]
boot_new = r'''/* ---------- Supabase data layer (same shape the app was written against) ---------- */
let sb=null, me=null, authMode='login';
const TABLES=[...Object.keys(S),'settings'];
const cache={};TABLES.forEach(t=>cache[t]=new Map());
const listeners={};TABLES.forEach(t=>listeners[t]=new Set());
function row2doc(r){return {id:r.id,exists:true,data:()=>r.data||{}}}
function emit(t){const docs=[...cache[t].values()].map(row2doc);const snap={docs,size:docs.length,empty:!docs.length};listeners[t].forEach(fn=>{try{fn(snap)}catch(e){console.error(e)}})}
function uuid(){return crypto.randomUUID?crypto.randomUUID():'x'+Date.now().toString(36)+Math.random().toString(36).slice(2,10)}
function fail(e){const err=new Error(e&&e.message||'Request failed');err.code=e&&e.code||'unavailable';return err}
function split(path){const p=path.split('/');if(p.length!==2||!TABLES.includes(p[0]))throw new TypeError('Bad path '+path);return p}
function docRef(t,id){
  id=id||uuid();
  return {id,path:t+'/'+id,
    async get(){const r=cache[t].get(id);if(r)return row2doc(r);const {data,error}=await sb.from(t).select('*').eq('id',id).maybeSingle();if(error)throw fail(error);return data?row2doc(data):{id,exists:false,data:()=>undefined}},
    async set(data){const row={id,data,updated_at:new Date().toISOString()};const {error}=await sb.from(t).upsert(row);if(error)throw fail(error);cache[t].set(id,row);emit(t)},
    async update(patch){const cur=cache[t].get(id);let base=cur?cur.data:null;if(!base){const {data,error}=await sb.from(t).select('data').eq('id',id).maybeSingle();if(error)throw fail(error);if(!data)throw Object.assign(new Error('No such record'),{code:'invalid_argument'});base=data.data}const merged={...base,...patch};const row={id,data:merged,updated_at:new Date().toISOString()};const {error}=await sb.from(t).update(row).eq('id',id);if(error)throw fail(error);cache[t].set(id,row);emit(t)},
    async delete(){const {error}=await sb.from(t).delete().eq('id',id);if(error)throw fail(error);cache[t].delete(id);emit(t)},
    onSnapshot(next,err){const fn=()=>{const r=cache[t].get(id);next(r?row2doc(r):{id,exists:false,data:()=>undefined})};listeners[t].add(fn);if(loaded[t])fn();return ()=>listeners[t].delete(fn)}
  };
}
const loaded={};
const dbApi={
  doc(path){const [t,id]=split(path);return docRef(t,id)},
  collection(t){if(!TABLES.includes(t))throw new TypeError('Bad collection '+t);return {path:t,doc:id=>docRef(t,id),add:d=>{const r=docRef(t);return r.set(d).then(()=>r)},onSnapshot(next,err){listeners[t].add(next);if(loaded[t])next({docs:[...cache[t].values()].map(row2doc)});return ()=>listeners[t].delete(next)}}}
};
async function loadTable(t){
  const {data,error}=await sb.from(t).select('*').order('created_at',{ascending:true});
  if(error)throw fail(error);
  cache[t]=new Map(data.map(r=>[r.id,r]));loaded[t]=true;emit(t);
}
let channel=null, pollTimer=0;
async function connectData(){
  conn='connecting';render();
  try{await Promise.all(TABLES.map(loadTable));conn='ok'}catch(e){console.error(e);conn='off'}
  render();
  if(channel){sb.removeChannel(channel)}
  channel=sb.channel('all-tables');
  TABLES.forEach(t=>channel.on('postgres_changes',{event:'*',schema:'public',table:t},p=>{
    if(p.eventType==='DELETE'){cache[t].delete(p.old.id)}else{cache[t].set(p.new.id,p.new)}
    emit(t);
  }));
  channel.subscribe(status=>{if(status==='SUBSCRIBED'&&conn!=='ok'){conn='ok';schedule()}if(status==='CHANNEL_ERROR'||status==='TIMED_OUT'){conn='off';schedule()}});
  clearInterval(pollTimer);pollTimer=setInterval(refreshAll,60000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshAll()});
}
async function refreshAll(){if(!sb||!me)return;try{await Promise.all(TABLES.map(loadTable));if(conn!=='ok'){conn='ok';schedule()}}catch(e){conn='off';schedule()}}

/* ---------- auth screens ---------- */
function showAuth(mode,msg,isErr){
  authMode=mode;$('#shell').hidden=true;const a=$('#auth');a.hidden=false;
  const brand=`<div class="brand">GMI Equipment<small>Back office</small></div>`;
  let form='';
  if(mode==='login')form=`<form id="authform"><div class="fgrid"><div class="fld"><label for="a_email">Email</label><input id="a_email" type="email" autocomplete="username" required></div><div class="fld"><label for="a_pw">Password</label><input id="a_pw" type="password" autocomplete="current-password" required></div></div><div style="margin-top:16px"><button class="btn primary" type="submit">Sign in</button></div></form><button class="authlink" data-amode="forgot">Forgot your password?</button>`;
  else if(mode==='forgot')form=`<form id="authform"><div class="fgrid"><div class="fld"><label for="a_email">Email</label><input id="a_email" type="email" required></div></div><div style="margin-top:16px"><button class="btn primary" type="submit">Email me a reset link</button></div></form><button class="authlink" data-amode="login">Back to sign in</button>`;
  else if(mode==='setpw')form=`<p class="small muted">Choose a password for your account.</p><form id="authform"><div class="fgrid"><div class="fld"><label for="a_pw">New password</label><input id="a_pw" type="password" autocomplete="new-password" minlength="8" required></div></div><div style="margin-top:16px"><button class="btn primary" type="submit">Save password and continue</button></div></form>`;
  a.innerHTML=`<div class="authcard">${brand}${form}<div class="authmsg ${isErr?'err':''}" id="authmsg">${esc(msg||'')}</div></div>`;
  const f=$('#authform');if(f)f.onsubmit=async ev=>{ev.preventDefault();const btn=f.querySelector('button');btn.disabled=true;const m=$('#authmsg');m.className='authmsg';m.textContent='';
    try{
      if(mode==='login'){const {error}=await sb.auth.signInWithPassword({email:$('#a_email').value.trim(),password:$('#a_pw').value});if(error)throw error}
      else if(mode==='forgot'){const {error}=await sb.auth.resetPasswordForEmail($('#a_email').value.trim(),{redirectTo:location.origin+location.pathname});if(error)throw error;m.textContent='If that address has an account, a reset link is on its way.'}
      else if(mode==='setpw'){const {error}=await sb.auth.updateUser({password:$('#a_pw').value});if(error)throw error;pendingSetPw=false;enterApp()}
    }catch(err){m.className='authmsg err';m.textContent=err.message==='Invalid login credentials'?'Wrong email or password.':(err.message||'Something went wrong')}
    btn.disabled=false};
  a.querySelectorAll('[data-amode]').forEach(b=>b.onclick=()=>showAuth(b.dataset.amode));
  const first=a.querySelector('input');if(first)first.focus();
}
let pendingSetPw=false;
function enterApp(){$('#auth').hidden=true;$('#shell').hidden=false;db=dbApi;render();connectData()}
async function signOut(){await sb.auth.signOut();location.reload()}
async function changePassword(){const pw=$('#pw_new').value;if(pw.length<8){toast('Use at least 8 characters');return}const {error}=await sb.auth.updateUser({password:pw});toast(error?error.message:'Password changed');if(!error)$('#pw_new').value=''}

/* ---------- boot ---------- */
const VALID=VIEWS.map(v=>v[0]);
const h0=location.hash||'';
try{const h=h0.slice(1);if(VALID.includes(h))UI.view=h}catch(_){}
if(/type=(invite|recovery|signup|magiclink)/.test(h0))pendingSetPw=/type=(invite|recovery)/.test(h0);
(async()=>{
  if(!window.supabase||!window.SUPABASE_URL||window.SUPABASE_URL.startsWith('__')){showAuth('login','This page is not configured yet: the Supabase URL and key are missing.',true);return}
  sb=window.supabase.createClient(window.SUPABASE_URL,window.SUPABASE_ANON_KEY);
  sb.auth.onAuthStateChange((ev,session)=>{
    me=session?session.user:null;
    if(ev==='PASSWORD_RECOVERY'){pendingSetPw=true}
    if(!me){if(!$('#auth').hidden&&authMode!=='login'&&ev!=='SIGNED_OUT')return;showAuth('login');return}
    if(pendingSetPw){showAuth('setpw');return}
    if($('#shell').hidden)enterApp();
  });
  const {data:{session}}=await sb.auth.getSession();
  if(!session)showAuth('login');
})();
'''
src = src.replace(boot_old, boot_new)
swap('})();\n})();\n</script>', '})();\n</script>\n</body>\n</html>')
swap('<div class="shell" id="shell" hidden>', '</head>\n<body>\n<div id="auth" class="auth" hidden></div>\n<div class="shell" id="shell" hidden>'.replace('<div id="auth" class="auth" hidden></div>\n',''))
# the auth div precedes </head> now; move </head><body> before it
src = src.replace('<div id="auth" class="auth" hidden></div>\n</head>\n<body>\n', '</head>\n<body>\n<div id="auth" class="auth" hidden></div>\n')
# leftover references
assert 'downloads' not in src.split('/* ---------- Supabase')[1], 'downloads ref left'
src = src.replace("let db=null, downloads=null, canWrite=true, conn='connecting';", "let db=null, canWrite=true, conn='connecting';")
open('/home/claude/gmi-backoffice/index.html','w').write(src)
print('ok', len(src))
