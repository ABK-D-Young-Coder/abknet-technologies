(() => {
  const qs = (s, root=document) => root.querySelector(s);
  const qsa = (s, root=document) => [...root.querySelectorAll(s)];

  // Mobile navigation + accessibility
  const toggle = qs('.menu-toggle'), nav = qs('.nav');
  if (toggle && nav) {
    toggle.setAttribute('aria-expanded', 'false');
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    qsa('.nav a').forEach(a => a.addEventListener('click', () => {
      nav.classList.remove('open'); toggle.setAttribute('aria-expanded','false');
    }));
  }

  // Current-page navigation state
  const path = location.pathname.replace(/\\/g,'/');
  qsa('.nav a').forEach(a => {
    const href = a.getAttribute('href') || '';
    if (href.startsWith('#') || href.includes('javascript:')) return;
    try {
      const target = new URL(href, location.href).pathname.replace(/\\/g,'/');
      if (target === path || (path.endsWith('/') && target === path + 'index.html')) a.classList.add('active');
    } catch {}
  });

  // Scroll progress + reveal effects
  const progress = document.createElement('div'); progress.className='scroll-progress'; document.body.prepend(progress);
  const updateScroll = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    progress.style.width = (max > 0 ? Math.min(100, scrollY / max * 100) : 0) + '%';
    qs('.back-to-top')?.classList.toggle('show', scrollY > 500);
  };
  addEventListener('scroll', updateScroll, {passive:true}); updateScroll();
  const observer = new IntersectionObserver(entries => entries.forEach(e => { if(e.isIntersecting) e.target.classList.add('visible'); }), {threshold:.08});
  qsa('.reveal').forEach(el => observer.observe(el));

  // Back to top
  qs('.back-to-top')?.addEventListener('click', () => scrollTo({top:0, behavior:'smooth'}));

  // Global search modal, available from every page
  const searchable = [
    ['JSON Formatter','Tool','tools/json-formatter.html','Format and validate JSON in your browser.'],
    ['QR Generator','Tool','tools/qr-generator.html','Create QR codes from text or URLs.'],
    ['Password Generator','Tool','tools/password-generator.html','Generate strong passwords locally.'],
    ['Word Counter','Tool','tools/word-counter.html','Count words, characters and sentences.'],
    ['Unit Converter','Tool','tools/unit-converter.html','Convert common length, weight and temperature units.'],
    ['HTML First Website','Tutorial','tutorials/html-first-website.html','Build your first website step by step.'],
    ['JavaScript Interactivity','Tutorial','tutorials/javascript-interactivity.html','Make web pages interactive with DOM events.'],
    ['Python Basics','Tutorial','tutorials/python-basics.html','Learn Python through practical examples.'],
    ['Projects','Project','projects/index.html','Explore ABKNET projects.'],
    ['Downloads','Software','downloads/index.html','Explore the ABKNET software center.'],
    ['Blog','Article','blog/index.html','Read technology articles and updates.'],
    ['About ABKNET','Company','about/index.html','Learn about ABKNET TECHNOLOGIES.'],
    ['Contact & Support','Support','contact/index.html','Send a support request or report a bug.'],
    ['YouTube Hub','Video','youtube.html','ABKNET technology videos and learning content.'],
    ['Privacy Policy','Legal','privacy.html','Read the ABKNET privacy policy.'],
    ['Terms of Use','Legal','terms.html','Read the ABKNET terms of use.']
  ];
  const resolve = rel => new URL('/' + rel.replace(/^\/+/, ''), location.origin).href;
  const modal = document.createElement('div');
  modal.className='site-search-modal'; modal.id='siteSearchModal'; modal.setAttribute('aria-hidden','true');
  modal.innerHTML=`<div class="site-search-backdrop" data-search-close></div><div class="site-search-dialog" role="dialog" aria-modal="true" aria-label="Search ABKNET"><div class="site-search-head"><span class="eyebrow">SEARCH</span><input id="siteSearchInput" type="search" placeholder="Search tools, tutorials, projects…" autocomplete="off"><button class="site-search-close" type="button" data-search-close>Esc</button></div><div class="site-search-results" id="siteSearchResults"><div class="search-hint">Start typing to search the ABKNET library.</div></div></div>`;
  document.body.append(modal);
  const searchInput=qs('#siteSearchInput'), searchResults=qs('#siteSearchResults');
  const renderSearch = value => {
    const q=value.trim().toLowerCase();
    const found=q ? searchable.filter(x=>(x[0]+' '+x[1]+' '+x[3]).toLowerCase().includes(q)) : searchable.slice(0,6);
    searchResults.innerHTML = found.length ? found.map(x=>`<a class="result" href="${resolve(x[2])}"><b>${x[1].toUpperCase()}</b> · ${x[0]}<br><small>${x[3]}</small> →</a>`).join('') : '<div class="search-hint">No matching ABKNET content found.</div>';
  };
  const openSearch = () => { modal.classList.add('open'); modal.setAttribute('aria-hidden','false'); renderSearch(''); setTimeout(()=>searchInput.focus(),20); };
  const closeSearch = () => { modal.classList.remove('open'); modal.setAttribute('aria-hidden','true'); };
  qsa('.nav-search').forEach(a=>a.addEventListener('click', e=>{e.preventDefault();openSearch();}));
  qsa('[data-search-close]', modal).forEach(el=>el.addEventListener('click', closeSearch));
  searchInput.addEventListener('input', e=>renderSearch(e.target.value));
  document.addEventListener('keydown', e => { if(e.key==='Escape') {closeSearch(); closeFeedback();} if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();openSearch();} });

  // Legacy homepage search becomes the same richer search experience
  const homeSearch=qs('#globalSearch'), homeBtn=qs('#searchBtn');
  if(homeSearch && homeBtn){
    const doHomeSearch=()=>{openSearch();searchInput.value=homeSearch.value;renderSearch(homeSearch.value);};
    homeBtn.onclick=doHomeSearch; homeSearch.onkeydown=e=>{if(e.key==='Enter')doHomeSearch();};
  }

  // Feedback modal
  const feedbackModal=qs('#feedbackModal'), feedbackForm=qs('#feedbackForm'), feedbackRating=qs('#feedbackRating'), feedbackResult=qs('#feedbackResult');
  const closeFeedback=()=>{feedbackModal?.classList.remove('open');feedbackModal?.setAttribute('aria-hidden','true');};
  qsa('[data-feedback-open]').forEach(b=>b.addEventListener('click',()=>{feedbackModal?.classList.add('open');feedbackModal?.setAttribute('aria-hidden','false');qs('[data-rating="5"]')?.focus();}));
  qsa('[data-feedback-close]').forEach(b=>b.addEventListener('click',closeFeedback));
  qsa('[data-rating]').forEach(b=>b.addEventListener('click',()=>{const r=b.dataset.rating;feedbackRating.value=r;qsa('[data-rating]').forEach(x=>x.classList.toggle('selected',x.dataset.rating===r));}));
  if(feedbackForm) feedbackForm.addEventListener('submit',async e=>{
    e.preventDefault(); const rating=Number(feedbackRating.value); if(!rating){feedbackResult.textContent='Choose a rating from 1 to 5.';return;}
    const btn=qs('button[type="submit"]',feedbackForm); btn.disabled=true; feedbackResult.textContent='Sending…';
    try{const data=Object.fromEntries(new FormData(feedbackForm).entries());data.page=location.pathname;const r=await fetch(window.abknetApi ? window.abknetApi('/api/feedback') : '/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const out=await r.json();if(!r.ok)throw new Error(out.error||'Unable to send feedback.');feedbackResult.textContent='✓ '+out.message;setTimeout(()=>{feedbackForm.reset();feedbackRating.value='0';qsa('[data-rating]').forEach(x=>x.classList.remove('selected'));closeFeedback();feedbackResult.textContent='';},900);}catch(err){feedbackResult.textContent='✕ '+err.message;}finally{btn.disabled=false;}
  });

  // Copy-to-clipboard for code panels
  qsa('.code-panel').forEach(panel=>{
    const pre=qs('pre',panel), top=qs('.code-top',panel); if(!pre||!top)return;
    const btn=document.createElement('button'); btn.type='button'; btn.className='code-copy'; btn.textContent='Copy'; btn.setAttribute('aria-label','Copy code'); top.append(btn);
    btn.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(pre.innerText);btn.textContent='Copied';setTimeout(()=>btn.textContent='Copy',1200);}catch{btn.textContent='Unavailable';setTimeout(()=>btn.textContent='Copy',1200);}});
  });

  // Newsletter and other existing forms
  const newsletterForm=qs('#newsletterForm');
  if(newsletterForm) newsletterForm.addEventListener('submit',async e=>{
    e.preventDefault();const out=qs('#newsletterResult'),button=qs('button[type="submit"]',newsletterForm),email=new FormData(newsletterForm).get('email');button.disabled=true;out.textContent='Subscribing…';
    try{const r=await fetch(window.abknetApi ? window.abknetApi('/api/newsletter') : '/api/newsletter',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})});const data=await r.json();if(!r.ok)throw new Error(data.error||'Unable to subscribe.');out.textContent='✓ '+data.message;newsletterForm.reset();}catch(err){out.textContent='✕ '+err.message;}finally{button.disabled=false;}
  });

  // Improve standalone filter pages with a friendly empty state
  const filter=qs('#filter'), grid=qs('#toolGrid');
  if(filter&&grid){const empty=document.createElement('p');empty.className='search-empty';empty.textContent='No tools match your search.';empty.hidden=true;grid.after(empty);filter.addEventListener('input',()=>{let visible=0;qsa('.tool-card',grid).forEach(x=>{const show=x.dataset.name.includes(filter.value.toLowerCase());x.style.display=show?'grid':'none';if(show)visible++;});empty.hidden=visible>0;});}

  // Theme preference: stays on the device and works across the whole site.
  const headerNav = qs('.nav');
  if (headerNav && !qs('.theme-toggle', headerNav)) {
    const themeBtn = document.createElement('button');
    themeBtn.type='button'; themeBtn.className='theme-toggle'; themeBtn.setAttribute('aria-label','Toggle light and dark theme');
    headerNav.append(themeBtn);
    const applyTheme = mode => {
      document.body.classList.toggle('light-theme', mode === 'light');
      themeBtn.textContent = mode === 'light' ? '☾ Dark' : '☀ Light';
      themeBtn.setAttribute('aria-pressed', String(mode === 'light'));
    };
    const saved = localStorage.getItem('abknet-theme');
    applyTheme(saved || 'dark');
    themeBtn.addEventListener('click',()=>{const next=document.body.classList.contains('light-theme')?'dark':'light';localStorage.setItem('abknet-theme',next);applyTheme(next);});
  }

  // PWA install button appears only when the browser supports installation.
  let installPrompt = null;
  addEventListener('beforeinstallprompt', e => {
    e.preventDefault(); installPrompt=e;
    const navEl=qs('.nav'); if(!navEl || qs('.install-app',navEl)) return;
    const b=document.createElement('button'); b.type='button'; b.className='install-app'; b.textContent='Install';
    navEl.append(b); b.addEventListener('click',async()=>{if(!installPrompt)return;installPrompt.prompt();await installPrompt.userChoice;installPrompt=null;b.remove();});
  });
  addEventListener('appinstalled',()=>qs('.install-app')?.remove());

  // Offline-ready progressive web app.
  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
    navigator.serviceWorker.register(new URL('sw.js', document.baseURI)).catch(()=>{});
  }

  // Tool directory filters: search + category.
  const toolFilter=qs('#filter'), toolGrid=qs('#toolGrid'), toolButtons=qsa('[data-tool-filter]');
  if(toolFilter && toolGrid){
    let category='all';
    const applyTools=()=>{
      const q=toolFilter.value.trim().toLowerCase(); let visible=0;
      qsa('.tool-card',toolGrid).forEach(card=>{const show=(category==='all'||card.dataset.category===category) && card.dataset.name.includes(q);card.style.display=show?'grid':'none';if(show)visible++;});
      let empty=qs('#toolEmpty'); if(!empty){empty=document.createElement('p');empty.id='toolEmpty';empty.className='search-empty';toolGrid.after(empty);} empty.textContent=visible?'':'No tools match your search or category.';empty.hidden=visible>0;
    };
    toolFilter.addEventListener('input',applyTools); toolButtons.forEach(b=>b.addEventListener('click',()=>{category=b.dataset.toolFilter;toolButtons.forEach(x=>x.classList.toggle('active',x===b));applyTools();})); applyTools();
  }

  // Tutorial directory filters.
  const tutorialFilter=qs('#tutorialFilter'), tutorialFilters=qsa('[data-tutorial-filter]');
  if(tutorialFilter){
    let category='all'; const cards=qsa('.article-card[data-tutorial]');
    const applyTutorials=()=>{const q=tutorialFilter.value.trim().toLowerCase();let visible=0;cards.forEach(c=>{const show=(category==='all'||c.dataset.tutorial===category)&&c.dataset.name.includes(q);c.style.display=show?'block':'none';if(show)visible++;});let empty=qs('#tutorialEmpty');if(!empty){empty=document.createElement('p');empty.id='tutorialEmpty';empty.className='search-empty';qs('#tutorialFilter').closest('section')?.append(empty);}empty.hidden=visible>0;empty.textContent=visible?'':'No tutorials match your search or category.';};
    tutorialFilter.addEventListener('input',applyTutorials);tutorialFilters.forEach(b=>b.addEventListener('click',()=>{category=b.dataset.tutorialFilter;tutorialFilters.forEach(x=>x.classList.toggle('active',x===b));applyTutorials();}));applyTutorials();
  }

  // Reading progress + share/copy-link tools on individual tutorial pages.
  const article=qs('main article');
  if(article && location.pathname.includes('/tutorials/')){
    const bar=document.createElement('div');bar.className='reading-progress';document.body.prepend(bar);
    const updateReading=()=>{const max=document.documentElement.scrollHeight-innerHeight;bar.style.width=(max>0?Math.min(100,scrollY/max*100):0)+'%';};addEventListener('scroll',updateReading,{passive:true});updateReading();
    const h1=qs('h1',article); if(h1){const tools=document.createElement('div');tools.className='article-tools';const share=document.createElement('button');share.textContent='↗ Share tutorial';const copy=document.createElement('button');copy.textContent='🔗 Copy link';tools.append(share,copy);h1.after(tools);share.onclick=async()=>{try{if(navigator.share){await navigator.share({title:document.title,url:location.href});}else{await navigator.clipboard.writeText(location.href);share.textContent='✓ Link copied';setTimeout(()=>share.textContent='↗ Share tutorial',1400);}}catch{}};copy.onclick=async()=>{try{await navigator.clipboard.writeText(location.href);copy.textContent='✓ Link copied';setTimeout(()=>copy.textContent='🔗 Copy link',1400);}catch{copy.textContent='Copy unavailable';}};}
  }

  // Always expose the real current year without requiring manual edits.
  qsa('.footer-bottom span').forEach(el=>{if(el.textContent.includes('©'))el.textContent=el.textContent.replace(/©\s*\d{4}/,'© '+new Date().getFullYear());});
})();
