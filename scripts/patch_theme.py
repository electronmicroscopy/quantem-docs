"""Patch the downloaded book-theme template so top-level TOC sections
render expanded by default.

The stock theme opens a sidebar section only while it contains the active
page (and re-collapses it on navigation). There is no template option for
this, so we patch the compiled bundles in _build/templates. Run after the
template has been downloaded (any `myst build` or `myst start` does that),
and re-run whenever _build is cleared:

    python scripts/patch_theme.py

The deploy workflow runs this between a warm-up build and the real build.
"""

import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = os.path.normpath(
    os.path.join(HERE, "..", "_build", "templates", "site", "myst", "book-theme")
)

TARGETS = [
    os.path.join(THEME, "build", "index.js"),
    os.path.join(THEME, "public", "build", "_shared", "chunk-RUUCG5OS.js"),
]

# Runtime for the landing-page logo: inlines the layered SVG <img>s so their
# animations become part of the page, keeps them paused, and runs each
# element's animations only while the pointer is over it. Leaving an element
# pauses it in its current state. Appended to the client entry bundle.
_RUNTIME = """
;(function(){
  /* ---------- landing-page logo: inline the layers, hover to animate ---- */
  function activate(svg){
    try{svg.setCurrentTime(0);svg.pauseAnimations();}catch(e){}
    svg.style.setProperty('--qem-play','paused');
    svg.addEventListener('mouseenter',function(){
      try{svg.unpauseAnimations();}catch(e){}
      svg.style.setProperty('--qem-play','running');
    });
    svg.addEventListener('mouseleave',function(){
      try{svg.pauseAnimations();}catch(e){}
      svg.style.setProperty('--qem-play','paused');
    });
  }
  var cache={};
  function swap(img){
    var next=img.nextElementSibling;
    if(next&&next.nodeName.toLowerCase()==='svg')return;
    var t=cache[img.src];
    if(t===undefined){
      if(img.dataset.qemBusy)return;
      img.dataset.qemBusy='1';
      fetch(img.src).then(function(r){return r.text();}).then(function(txt){
        cache[img.src]=txt;delete img.dataset.qemBusy;logoTick();
      }).catch(function(){delete img.dataset.qemBusy;});
      return;
    }
    var box=document.createElement('div');
    box.innerHTML=t;
    var svg=box.querySelector('svg');
    if(!svg)return;
    svg.setAttribute('class',img.getAttribute('class')||'');
    img.style.display='none';
    img.after(svg);
    activate(svg);
  }
  function logoTick(){
    document.querySelectorAll('.qem-logo-box img').forEach(swap);
  }

  /* ---------- flat top-bar search (replaces the theme's dialog) -------- */
  var idx=null,loading=false,waiters=[];
  function load(cb){
    if(cb&&idx)return cb();
    if(cb)waiters.push(cb);
    if(idx||loading)return;
    loading=true;
    fetch('/myst.search.json').then(function(r){return r.json();})
      .then(function(d){
        idx=d.records||[];loading=false;
        var w=waiters;waiters=[];w.forEach(function(f){f();});
      })
      .catch(function(){loading=false;waiters=[];});
  }
  function titleOf(h){
    return [h.lvl3,h.lvl2,h.lvl1].filter(Boolean)[0]||'';
  }
  function crumbOf(h){
    return [h.lvl1,h.lvl2,h.lvl3].filter(Boolean).join(' > ');
  }
  function search(q){
    if(!idx)return [];
    var terms=q.toLowerCase().split(/\s+/).filter(Boolean);
    if(!terms.length)return [];
    var seen={},out=[];
    idx.forEach(function(rec){
      var h=rec.hierarchy||{};
      var title=titleOf(h),crumb=crumbOf(h);
      var hay=(crumb+' '+(rec.content||'')).toLowerCase();
      var titleHay=crumb.toLowerCase();
      var score=0;
      for(var i=0;i<terms.length;i++){
        if(hay.indexOf(terms[i])<0)return;
        if(titleHay.indexOf(terms[i])>=0)score+=3;
        score+=1;
      }
      if(rec.type!=='content')score+=2;
      var key=rec.url;
      if(seen[key]!==undefined){
        if(out[seen[key]].score>=score)return;
        out[seen[key]]={score:score,url:rec.url,title:title,crumb:crumb,
                        content:rec.content||''};
        return;
      }
      seen[key]=out.length;
      out.push({score:score,url:rec.url,title:title,crumb:crumb,
                content:rec.content||''});
    });
    out.sort(function(a,b){return b.score-a.score;});
    return out.slice(0,8);
  }
  function build(bar){
    if(!bar||bar.dataset.qemSearch)return;
    bar.dataset.qemSearch='1';
    var wrap=document.createElement('div');
    wrap.className='qem-search';
    var input=document.createElement('input');
    input.type='search';
    input.placeholder='Search';
    input.setAttribute('aria-label','Search this site');
    var list=document.createElement('div');
    list.className='qem-search-results';
    list.hidden=true;
    wrap.appendChild(input);
    wrap.appendChild(list);
    bar.style.display='none';
    bar.after(wrap);
    var active=-1,hits=[];
    function render(){
      list.innerHTML='';
      if(!hits.length){list.hidden=true;return;}
      hits.forEach(function(h,i){
        var a=document.createElement('a');
        a.href=h.url;
        a.className='qem-search-hit'+(i===active?' active':'');
        var t=document.createElement('div');
        t.className='qem-search-hit-title';
        t.textContent=h.crumb||h.title;
        a.appendChild(t);
        if(h.content){
          var c=document.createElement('div');
          c.className='qem-search-hit-text';
          c.textContent=h.content.slice(0,110);
          a.appendChild(c);
        }
        list.appendChild(a);
      });
      list.hidden=false;
    }
    function run(){
      active=-1;
      hits=search(input.value.trim());
      render();
    }
    input.addEventListener('focus',function(){load();});
    input.addEventListener('input',function(){
      load(run);   // re-runs once the index finishes loading
      run();
    });
    input.addEventListener('keydown',function(ev){
      if(ev.key==='ArrowDown'||ev.key==='ArrowUp'){
        ev.preventDefault();
        if(!hits.length)return;
        active=(active+(ev.key==='ArrowDown'?1:-1)+hits.length)%hits.length;
        render();
      }else if(ev.key==='Enter'){
        var h=hits[active<0?0:active];
        if(h){ev.preventDefault();window.location.href=h.url;}
      }else if(ev.key==='Escape'){
        input.value='';hits=[];render();input.blur();
      }
    });
    document.addEventListener('click',function(ev){
      if(!wrap.contains(ev.target)){hits=[];render();}
    });
    document.addEventListener('keydown',function(ev){
      if((ev.metaKey||ev.ctrlKey)&&ev.key.toLowerCase()==='k'){
        ev.preventDefault();ev.stopPropagation();input.focus();input.select();
      }
    },true);
  }
  function searchTick(){
    build(document.querySelector('button.myst-search-bar'));
  }

  function tick(){logoTick();searchTick();}
  function start(){
    tick();
    // React hydration replaces these nodes, so keep re-checking for a while
    var n=0,iv=setInterval(function(){tick();if(++n>40)clearInterval(iv);},250);
    new MutationObserver(function(){tick();}).observe(
      document.documentElement,{subtree:true,childList:true});
  }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',start);
  }else{start();}
})();
"""

# The marker embeds a hash of the runtime, so editing the code above is
# enough to make the next patch run replace an older injected copy.
INLINER_MARK = (
    "/*qem-runtime-" + hashlib.sha1(_RUNTIME.encode()).hexdigest()[:8] + "*/"
)
INLINER = INLINER_MARK + _RUNTIME


def entry_client():
    import glob
    hits = glob.glob(os.path.join(THEME, "public", "build", "entry.client-*.js"))
    return hits[0] if hits else None

# Matches the collapsible-section state hook in both the server and client
# bundles (minified variable names differ between them):
#   [s,o]=X.useState(r); useEffect(()=>{n.state==="idle"&&o(r)},[n.state]);
#   let a=fn(e,i,t); return !i.children ...
PATTERN = re.compile(
    r'\[(\w),(\w)\]=([\w$]+(?:\.default)?)\.useState\((\w)\);'
    r'\(0,([\w$]+)\.useEffect\)\(\(\)=>\{(\w)\.state==="idle"&&\2\(\4\)\},'
    r'\[\6\.state\]\);let (\w)=[\w$]+\(([^)]*)\);return!(\w)\.c'
)


def patched(src):
    def repl(m):
        s, o, hook, active, eff, nav, let_var, fn_args, heading = m.groups()
        keep_open = f'({heading}.level===1||{active})'
        return (
            f'[{s},{o}]={hook}.useState({keep_open});'
            f'(0,{eff}.useEffect)(()=>{{{nav}.state==="idle"&&{o}({keep_open})}},'
            f'[{nav}.state]);let {let_var}='
            + m.group(0).split(f'let {let_var}=', 1)[1]
        )

    return PATTERN.subn(repl, src)


def main():
    if not os.path.isdir(THEME):
        sys.exit("book-theme template not found; run `myst build` first")
    total = 0
    # dev server: drop the 1-year immutable cache so patched bundles reload
    server_js = os.path.join(THEME, "server.js")
    if os.path.exists(server_js):
        with open(server_js) as f:
            ssrc = f.read()
        fixed = ssrc.replace(
            "{ immutable: true, maxAge: '1y' }", "{ maxAge: '5m' }"
        )
        if fixed != ssrc:
            with open(server_js, "w") as f:
                f.write(fixed)
            print("patched server.js (cache headers)")
    # inject the logo runtime into the server-rendered HTML itself; the
    # document is never long-cached, unlike the fingerprinted JS bundles
    import json
    server_bundle = os.path.join(THEME, "build", "index.js")
    with open(server_bundle) as f:
        bsrc = f.read()
    tag = json.dumps("<script>" + INLINER + "</script></body>")
    if INLINER_MARK in bsrc:
        print("already patched: build/index.js (logo runtime)")
    elif "qem-logo-runtime" in bsrc or "qem-runtime-v" in bsrc:  # older runtime version: swap it out
        new_bsrc, n = re.subn(
            r'"<script>[^"]*qem-(?:logo-)?runtime[^"]*</script></body>"',
            lambda m: tag,
            bsrc,
        )
        with open(server_bundle, "w") as f:
            f.write(new_bsrc)
        total += n
        print(f"updated build/index.js runtime ({n} site)")
    else:
        new_bsrc, n = re.subn(
            r'new Response\("<!DOCTYPE html>"\+(\w+),',
            lambda m: (
                'new Response("<!DOCTYPE html>"+'
                f'{m.group(1)}.replace("</body>",{tag}),'
            ),
            bsrc,
        )
        if n == 0:
            sys.exit("SSR injection point not found; theme version changed?")
        with open(server_bundle, "w") as f:
            f.write(new_bsrc)
        total += n
        print(f"patched build/index.js (logo runtime, {n} site)")
    # rename the patched entry + manifest so browsers that cached the stock
    # bundles (1-year immutable) fetch the patched versions
    rename = [("entry.client-PCJPW7TK", "entry.client-QEMRT1"),
              ("manifest-C732C875", "manifest-QEMRT1")]
    pub = os.path.join(THEME, "public", "build")
    if not os.path.exists(os.path.join(pub, "entry.client-QEMRT1.js")):
        import shutil
        for old, new in rename:
            shutil.copyfile(
                os.path.join(pub, f"{old}.js"), os.path.join(pub, f"{new}.js")
            )
        for path in [os.path.join(THEME, "build", "index.js")] + [
            os.path.join(pub, "manifest-QEMRT1.js")
        ]:
            with open(path) as f:
                s = f.read()
            for old, new in rename:
                s = s.replace(old, new)
            with open(path, "w") as f:
                f.write(s)
        print("renamed entry.client + manifest (cache bust)")

    for path in TARGETS:
        with open(path) as f:
            src = f.read()
        if ".level===1||" in src:
            print(f"already patched: {os.path.relpath(path, THEME)}")
            continue
        out, n = patched(src)
        if n == 0:
            sys.exit(f"pattern not found in {path}; theme version changed?")
        with open(path, "w") as f:
            f.write(out)
        total += n
        print(f"patched {os.path.relpath(path, THEME)} ({n} site)")
    print(f"done ({total} replacements)")


if __name__ == "__main__":
    main()
