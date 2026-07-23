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
INLINER_MARK = "/*qem-logo-runtime*/"
INLINER = INLINER_MARK + """
;(function(){
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
  function inline(){
    document.querySelectorAll('.qem-logo-box img').forEach(function(img){
      if(img.dataset.qemDone)return;
      img.dataset.qemDone='1';
      fetch(img.src).then(function(r){return r.text();}).then(function(t){
        var svg=new DOMParser().parseFromString(t,'image/svg+xml').documentElement;
        if(!svg||svg.nodeName!=='svg'){return;}
        svg.setAttribute('class',img.getAttribute('class')||'');
        img.style.display='none';
        img.after(svg);
        activate(svg);
      }).catch(function(){delete img.dataset.qemDone;});
    });
  }
  function start(){
    inline();
    new MutationObserver(inline).observe(document.body,{subtree:true,childList:true});
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',start);}
  else{start();}
})();
"""


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
    entry = entry_client()
    if entry:
        with open(entry) as f:
            esrc = f.read()
        if INLINER_MARK in esrc:
            print(f"already patched: {os.path.relpath(entry, THEME)}")
        else:
            with open(entry, "a") as f:
                f.write(INLINER)
            total += 1
            print(f"patched {os.path.relpath(entry, THEME)} (logo runtime)")
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
