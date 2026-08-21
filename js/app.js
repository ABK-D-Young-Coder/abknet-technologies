const toggle=document.querySelector(".menu-toggle"),nav=document.querySelector(".nav");
if(toggle){toggle.addEventListener("click",()=>{const open=nav.classList.toggle("open");toggle.setAttribute("aria-expanded",open)})}
document.querySelectorAll(".nav a").forEach(a=>a.addEventListener("click",()=>nav?.classList.remove("open")));
const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add("visible")}),{threshold:.08});
document.querySelectorAll(".reveal").forEach(el=>observer.observe(el));

const searchable=[
["JSON Formatter","tool","tools/json-formatter.html"],["QR Generator","tool","tools/qr-generator.html"],
["Password Generator","tool","tools/password-generator.html"],["Word Counter","tool","tools/word-counter.html"],
["Unit Converter","tool","tools/unit-converter.html"],["HTML First Website","tutorial","tutorials/html-first-website.html"],
["JavaScript Interactivity","tutorial","tutorials/javascript-interactivity.html"],["Python Basics","tutorial","tutorials/python-basics.html"],
["Projects","project","projects/index.html"],["Downloads","download","downloads/index.html"],["Blog","article","blog/index.html"]
];
function searchSite(){
 const q=(document.querySelector("#globalSearch")?.value||"").trim().toLowerCase(), box=document.querySelector("#searchResults");
 if(!box)return;if(!q){box.innerHTML="";return}
 const found=searchable.filter(x=>x[0].toLowerCase().includes(q)||x[1].includes(q));
 box.innerHTML=found.length?found.map(x=>`<a class="result" href="${x[2]}"><b>${x[1].toUpperCase()}</b> · ${x[0]} →</a>`).join(""):`<p style="color:#7893aa">No matching ABKNET content found.</p>`;
}
document.querySelector("#searchBtn")?.addEventListener("click",searchSite);
document.querySelector("#globalSearch")?.addEventListener("keydown",e=>{if(e.key==="Enter")searchSite()});


// ABKNET backend integrations
const backendSearch = document.querySelector('#globalSearch');
const backendButton = document.querySelector('#searchBtn');
async function runBackendSearch(){
  const q=(backendSearch?.value||'').trim(); const box=document.querySelector('#searchResults');
  if(!box)return;
  if(!q){box.innerHTML='';return;}
  box.innerHTML='<p style="color:#7893aa">Searching ABKNET…</p>';
  try{
    const r=await fetch('/api/search?q='+encodeURIComponent(q)); const out=await r.json();
    box.innerHTML=out.results.length?out.results.map(x=>`<a class="result" href="${x.url}"><b>${x.type.toUpperCase()}</b> · ${x.title} — ${x.description} →</a>`).join(''):'<p style="color:#7893aa">No matching ABKNET content found.</p>';
  }catch(e){box.innerHTML='<p style="color:#ff9d9d">Search backend unavailable. The site can still be browsed normally.</p>'}
}
if(backendButton)backendButton.onclick=runBackendSearch;
if(backendSearch)backendSearch.onkeydown=e=>{if(e.key==='Enter')runBackendSearch()};

const newsletterForm=document.querySelector('#newsletterForm');
if(newsletterForm)newsletterForm.addEventListener('submit',async e=>{
 e.preventDefault(); const out=document.querySelector('#newsletterResult'); const email=new FormData(newsletterForm).get('email');
 out.textContent='Subscribing…';
 try{const r=await fetch('/api/newsletter',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})});const data=await r.json();if(!r.ok)throw new Error(data.error||'Unable to subscribe.');out.textContent='✓ '+data.message;newsletterForm.reset()}catch(err){out.textContent='✕ '+err.message}
});
