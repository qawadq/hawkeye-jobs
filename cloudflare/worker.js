const DATA_URL = "https://raw.githubusercontent.com/qawadq/hawkeye-jobs/main/data/jobs.json";
const ACTIONS_URL = "https://github.com/qawadq/hawkeye-jobs/actions/workflows/search-and-publish.yml";
const CONFIG_URL = "https://github.com/qawadq/hawkeye-jobs/edit/main/data/search-config.json";

const HTML = String.raw`<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b1324">
<meta name="robots" content="noindex,nofollow">
<meta name="description" content="لوحة متابعة فرص العمل من Hawkeye Jobs">
<link rel="manifest" href="__ROOT__/manifest.webmanifest">
<link rel="icon" href="__ROOT__/icon.svg" type="image/svg+xml">
<title>Hawkeye Jobs</title>
<style>
:root{color-scheme:dark;--bg:#0b1324;--panel:#121e33;--panel2:#172640;--line:#263954;--text:#edf3fb;--muted:#a8b8cc;--accent:#6da9ff;--green:#64d6a1;--yellow:#f3c86a;--red:#f58c8c}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(140deg,#0b1324,#101d32 60%,#0c1729);color:var(--text);font:15px/1.65 system-ui,-apple-system,"Segoe UI",Tahoma,Arial,sans-serif;min-height:100vh}
a{color:var(--accent);text-decoration:none}button,input,select{font:inherit}button{cursor:pointer}
.wrap{max-width:1120px;margin:auto;padding:22px 16px 60px}
header{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding:12px 0 22px;border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px}.logo{width:46px;height:46px;border-radius:14px;background:#1d3557;display:grid;place-items:center;font-size:25px}.brand h1{font-size:22px;margin:0;line-height:1.25}.brand p{margin:3px 0 0;color:var(--muted);font-size:13px}
.actions{display:flex;gap:8px;flex-wrap:wrap}.btn{border:1px solid var(--line);border-radius:11px;background:var(--panel2);color:var(--text);padding:9px 13px;font-weight:600}.btn.primary{background:#235da8;border-color:#3477c7;color:#fff}.btn:disabled{opacity:.55;cursor:wait}
.note{margin:16px 0;color:var(--muted);font-size:13px}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:18px 0}.stat{background:rgba(18,30,51,.92);border:1px solid var(--line);border-radius:15px;padding:14px}.stat span{display:block;color:var(--muted);font-size:12px}.stat strong{font-size:25px;display:block;margin-top:3px}
.filters{display:grid;grid-template-columns:1fr 190px 180px;gap:10px;margin:20px 0 12px}.field{width:100%;background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:11px 13px;color:var(--text);min-width:0;outline:none}.field:focus{border-color:var(--accent)}
.tabs{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0 18px}.tab{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:999px;padding:7px 13px}.tab.active{background:#1d3d65;color:#fff;border-color:#4679b3}
.meta{color:var(--muted);font-size:12px;display:flex;gap:10px;flex-wrap:wrap}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.job{background:rgba(18,30,51,.94);border:1px solid var(--line);border-radius:16px;padding:16px;min-width:0}.job h2{font-size:17px;line-height:1.45;margin:7px 0 8px}.desc{color:#c3d0e0;font-size:13px;margin:12px 0;white-space:pre-wrap;overflow-wrap:anywhere}.jobfoot{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:12px}.status-actions{display:flex;gap:6px;flex-wrap:wrap}.small{font-size:12px;padding:6px 9px}.pill{display:inline-block;padding:3px 8px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:11px}.source{color:#b7d4ff}.empty,.error{background:var(--panel);border:1px dashed var(--line);border-radius:15px;padding:28px;text-align:center;color:var(--muted);grid-column:1/-1}.error{color:var(--red)}
footer{color:var(--muted);font-size:12px;text-align:center;margin-top:28px}
@media(max-width:740px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.filters{grid-template-columns:1fr 1fr}.filters input{grid-column:1/-1}.grid{grid-template-columns:1fr}.wrap{padding:14px 12px 36px}.brand h1{font-size:19px}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="brand"><div class="logo">🦅</div><div><h1>Hawkeye Jobs</h1><p>لوحة متابعة فرص العمل — نسخة شخصية</p></div></div>
  <div class="actions">
    <button class="btn" id="refresh">تحديث النتائج</button>
    <a class="btn primary" href="__ACTIONS_URL__" target="_blank" rel="noopener">تشغيل بحث الآن</a>
    <a class="btn" href="__CONFIG_URL__" target="_blank" rel="noopener">إعدادات البحث</a>
  </div>
</header>
<p class="note" id="lastUpdate">جارٍ تحميل النتائج…</p>
<section class="stats">
  <div class="stat"><span>كل الوظائف</span><strong id="total">—</strong></div>
  <div class="stat"><span>جديدة</span><strong id="newCount">—</strong></div>
  <div class="stat"><span>محفوظة</span><strong id="savedCount">—</strong></div>
  <div class="stat"><span>تم التقديم</span><strong id="appliedCount">—</strong></div>
</section>
<div class="filters">
  <input id="search" class="field" type="search" placeholder="ابحث بالمسمى أو الشركة أو الدولة…">
  <select id="source" class="field"><option value="">كل المصادر</option><option value="linkedin">LinkedIn</option><option value="indeed">Indeed</option><option value="bayt">Bayt</option><option value="naukrigulf">NaukriGulf</option><option value="google_jobs">Google Jobs</option></select>
  <select id="sort" class="field"><option value="newest">الأحدث أولاً</option><option value="oldest">الأقدم أولاً</option></select>
</div>
<div class="tabs" id="tabs">
  <button class="tab active" data-status="all">الكل</button>
  <button class="tab" data-status="new">جديدة</button>
  <button class="tab" data-status="saved">محفوظة</button>
  <button class="tab" data-status="applied">تم التقديم</button>
  <button class="tab" data-status="dismissed">مستبعدة</button>
</div>
<section class="grid" id="jobs"><div class="empty">جارٍ تحميل الوظائف…</div></section>
<footer>يتم تحديث البحث تلقائيًا مرتين يوميًا. حالات الحفظ والتقديم محفوظة على هذا الجهاز فقط.</footer>
</div>
<script>
const ROOT="__ROOT__";
const STATUS_KEY="hawkeye-jobs-status-v1";
const statusNames={new:"جديدة",saved:"محفوظة",applied:"تم التقديم",dismissed:"مستبعدة"};
const sourceNames={linkedin:"LinkedIn",indeed:"Indeed",bayt:"Bayt",naukrigulf:"NaukriGulf",google_jobs:"Google Jobs"};
let data={jobs:[],summary:{},updated_at:null},activeStatus="all";
let statuses={};
try{statuses=JSON.parse(localStorage.getItem(STATUS_KEY)||"{}")||{}}catch{}
const el=id=>document.getElementById(id);
const statusOf=j=>statuses[j.id||j.url]||"new";
function saveStatuses(){localStorage.setItem(STATUS_KEY,JSON.stringify(statuses));}
function fmtDate(s){if(!s)return "التاريخ غير محدد";const d=new Date(s);return Number.isNaN(d.getTime())?s:d.toLocaleDateString("ar-EG",{year:"numeric",month:"short",day:"numeric"});}
function make(tag,cls,txt){const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n;}
function render(){
 const q=el("search").value.trim().toLowerCase(),src=el("source").value,sort=el("sort").value;
 const all=data.jobs||[];
 const counts={new:0,saved:0,applied:0,dismissed:0};
 for(const j of all)counts[statusOf(j)]=(counts[statusOf(j)]||0)+1;
 el("total").textContent=all.length.toLocaleString("ar-EG");
 el("newCount").textContent=(counts.new||0).toLocaleString("ar-EG");
 el("savedCount").textContent=(counts.saved||0).toLocaleString("ar-EG");
 el("appliedCount").textContent=(counts.applied||0).toLocaleString("ar-EG");
 let rows=all.filter(j=>(!src||j.source===src)&&
   (activeStatus==="all"||statusOf(j)===activeStatus)&&
   (!q||[j.title,j.description,j.location,j.keyword,j.source].join(" ").toLowerCase().includes(q)));
 rows.sort((a,b)=>String(a.first_seen_at||"").localeCompare(String(b.first_seen_at||""))*(sort==="newest"?-1:1));
 const container=el("jobs");container.replaceChildren();
 if(!rows.length){container.append(make("div","empty",all.length?"لا توجد نتائج مطابقة للفلاتر الحالية.":"لم تُنشر نتائج بعد. سيبدأ أول بحث تلقائي بعد نشر سير العمل على الفرع الرئيسي."));return;}
 for(const j of rows){
  const card=make("article","job"),meta=make("div","meta");
  meta.append(make("span","pill source",sourceNames[j.source]||j.source||"مصدر غير محدد"));
  if(j.location)meta.append(make("span","pill",j.location));
  if(j.published)meta.append(make("span","pill","نُشرت: "+j.published));
  card.append(meta,make("h2","",j.title||"بدون عنوان"));
  const desc=(j.description||"").trim();
  if(desc)card.append(make("p","desc",desc.slice(0,700)+(desc.length>700?"…":"")));
  const foot=make("div","jobfoot"),details=make("div","meta");
  details.append(make("span","", "أُضيفت: "+fmtDate(j.first_seen_at)));
  if(j.keyword)details.append(make("span","", "كلمة البحث: "+j.keyword));
  const actions=make("div","status-actions");
  const open=make("a","btn small","فتح الإعلان");open.href=j.url||"#";open.target="_blank";open.rel="noopener noreferrer";actions.append(open);
  for(const st of ["saved","applied","dismissed"]){
   const b=make("button","btn small",st==="saved"?"حفظ":st==="applied"?"قدمت":"استبعاد");
   if(statusOf(j)===st){b.style.borderColor="#6da9ff";b.style.color="#9fc6ff";}
   b.addEventListener("click",()=>{const key=j.id||j.url;if(statusOf(j)===st)delete statuses[key];else statuses[key]=st;saveStatuses();render();});
   actions.append(b);
  }
  foot.append(details,actions);card.append(foot);container.append(card);
 }
}
async function load(){
 const button=el("refresh");button.disabled=true;button.textContent="جارٍ التحديث…";
 try{
  const r=await fetch(ROOT+"/jobs.json?ts="+Date.now(),{cache:"no-store"});
  if(!r.ok)throw new Error("HTTP "+r.status);
  data=await r.json();
  const s=data.summary||{};
  const date=data.updated_at?new Date(data.updated_at).toLocaleString("ar-EG"):"لم يعمل البحث بعد";
  el("lastUpdate").textContent="آخر تحديث: "+date+" · نتائج آخر تشغيل: "+(s.found_this_run||0)+" · استعلامات ناجحة: "+(s.successful_queries||0)+" · تعذر تنفيذ: "+(s.failed_queries||0);
  render();
 }catch(e){el("jobs").replaceChildren(make("div","error","تعذر تحميل بيانات الوظائف. أعد المحاولة بعد قليل."));el("lastUpdate").textContent="تعذر الاتصال بملف النتائج.";}
 finally{button.disabled=false;button.textContent="تحديث النتائج";}
}
el("refresh").addEventListener("click",load);
el("search").addEventListener("input",render);
el("source").addEventListener("change",render);
el("sort").addEventListener("change",render);
el("tabs").addEventListener("click",e=>{const b=e.target.closest("button[data-status]");if(!b)return;activeStatus=b.dataset.status;document.querySelectorAll(".tab").forEach(x=>x.classList.toggle("active",x===b));render();});
if("serviceWorker" in navigator)navigator.serviceWorker.register(ROOT+"/sw.js",{scope:ROOT+"/"}).catch(()=>{});
load();
</script>
</body></html>`;

function headers(type) {
  return {
    "Content-Type": type,
    "Cache-Control": "no-store, max-age=0",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
  };
}

export default {
  async fetch(request, env) {
    const key = env.ACCESS_KEY;
    if (!key) return new Response("Service not configured", {status:503});
    const root = "/s/" + key;
    const url = new URL(request.url);
    const path = url.pathname;
    if (path !== root && path !== root + "/" && !path.startsWith(root + "/")) {
      return new Response("Not found", {status:404});
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", {status:405});
    }
    if (path === root || path === root + "/") {
      const page = HTML.replaceAll("__ROOT__", root).replaceAll("__ACTIONS_URL__", ACTIONS_URL).replaceAll("__CONFIG_URL__", CONFIG_URL);
      return new Response(page, {headers:headers("text/html; charset=utf-8")});
    }
    if (path === root + "/jobs.json") {
      try {
        const upstream = await fetch(DATA_URL + "?v=" + Date.now(), {headers:{"Cache-Control":"no-cache"}});
        if (!upstream.ok) return new Response(JSON.stringify({jobs:[],summary:{},updated_at:null,error:"data_not_ready"}), {status:200,headers:headers("application/json; charset=utf-8")});
        const body = await upstream.text();
        return new Response(body, {headers:headers("application/json; charset=utf-8")});
      } catch {
        return new Response(JSON.stringify({jobs:[],summary:{},updated_at:null,error:"data_unavailable"}), {headers:headers("application/json; charset=utf-8")});
      }
    }
    if (path === root + "/manifest.webmanifest") {
      const manifest = {
        name:"Hawkeye Jobs",short_name:"Hawkeye",start_url:root+"/",scope:root+"/",
        display:"standalone",background_color:"#0b1324",theme_color:"#0b1324",
        lang:"ar",dir:"rtl",icons:[{src:root+"/icon.svg",sizes:"any",type:"image/svg+xml",purpose:"any"}]
      };
      return new Response(JSON.stringify(manifest), {headers:headers("application/manifest+json; charset=utf-8")});
    }
    if (path === root + "/icon.svg") {
      const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#1d3557"/><text x="32" y="45" font-size="40" text-anchor="middle">🦅</text></svg>';
      return new Response(svg,{headers:headers("image/svg+xml")});
    }
    if (path === root + "/sw.js") {
      const js = `const ROOT=${JSON.stringify(root)};const CACHE="hawkeye-shell-v1";self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>c.add(ROOT+"/"))));self.addEventListener("activate",e=>e.waitUntil(self.clients.claim()));self.addEventListener("fetch",e=>{const u=new URL(e.request.url);if(u.origin!==location.origin||u.pathname===ROOT+"/jobs.json"||e.request.method!=="GET")return;e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));});`;
      return new Response(js,{headers:{...headers("application/javascript; charset=utf-8"),"Service-Worker-Allowed":root+"/"}});
    }
    return new Response("Not found",{status:404});
  }
};
