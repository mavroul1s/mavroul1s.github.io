# Archived startup screen

The original NAVI / WIRED UPLINK entrance screen is saved here and is not loaded by the homepage. This includes the “Present day. Present time.” opener, progress log, access message, and click / keyboard entry behavior.

## Restore it

1. Add the CSS below near the end of the stylesheet in `index.html`, before the reduced-motion rules. It uses the site's existing theme tokens and `blink` animation.
2. Put the HTML below immediately before `<nav class="nav">`.
3. Replace the immediate `startHero();` call marked “Startup overlay” with the JavaScript below, inside the existing page script. Keep the existing `startHero`, `paintRepos`, and `reduce` definitions; the controller calls them.

The news count is read from the current page, so restoring this screen does not restore removed repository announcements.

## CSS

```css
/* ============================================================
   BOOT
   ============================================================ */
#boot{
  position:fixed;inset:0;z-index:120;background:var(--bg);
  display:flex;align-items:center;justify-content:center;
  padding:var(--gut);
}
#boot-frame{
  position:relative;width:min(560px,100%);
  border:1px solid rgba(var(--grid-rgb),.55);background:rgba(var(--surface-rgb),.6);padding:20px 22px;
}
#boot-frame::before,#boot-frame::after{
  content:"";position:absolute;width:14px;height:14px;border:2px solid var(--primary);
}
#boot-frame::before{top:-1px;left:-1px;border-right:0;border-bottom:0}
#boot-frame::after{bottom:-1px;right:-1px;border-left:0;border-top:0}
#boot .hdr{
  font-family:var(--hud);font-size:11px;letter-spacing:.28em;text-transform:uppercase;
  color:var(--muted);display:flex;justify-content:space-between;gap:12px;
  border-bottom:1px solid rgba(var(--grid-rgb),.4);padding-bottom:8px;margin-bottom:12px;
}
#boot pre{
  margin:0;font-size:clamp(10px,2.4vw,13px);color:var(--primary);
  line-height:1.75;white-space:pre-wrap;
}
#boot .ok{color:var(--muted)}
#boot .bar{height:6px;margin-top:14px;border:1px solid rgba(var(--grid-rgb),.5);padding:1px}
#boot .bar span{display:block;height:100%;width:0;background:var(--primary);transition:width .16s steps(4)}
#boot .grant{
  margin-top:12px;font-family:var(--hud);font-size:13px;letter-spacing:.3em;
  color:var(--accent);opacity:0;
}
#boot.granted .grant{opacity:1;animation:blink .28s steps(1) 3}
/* the line the whole site is named after — it lands last, after the lock opens */
#boot .wired{
  margin-top:9px;font-family:var(--hud);font-size:11px;letter-spacing:.19em;
  text-transform:uppercase;color:var(--muted);
  opacity:0;transition:opacity .5s steps(5) .18s;
}
#boot.granted .wired{opacity:1}
/* the door: dim while the log is still printing, then lit and waiting.
   Nothing dismisses the boot screen on a timer — the visitor opens it. */
#boot .skip{
  position:absolute;bottom:calc(var(--gut) - 4px);left:0;right:0;text-align:center;
  font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--grid);
  transition:color .3s steps(4),letter-spacing .3s steps(4);
}
#boot.ready .skip{
  color:var(--accent);letter-spacing:.3em;
  animation:enterpulse 1.5s ease-in-out infinite;
}
#boot.ready .skip::before{content:"▸ "}
#boot.ready .skip::after{content:" ◂"}
@keyframes enterpulse{0%,100%{opacity:1}50%{opacity:.34}}
#boot{cursor:pointer}
#boot.done{opacity:0;visibility:hidden;transition:opacity .45s steps(6),visibility 0s .45s}

/* the episode opener: top left, on arrival, then gone. Sits above the boot
   screen while that is up and clears itself a couple of seconds after it */
#pdpt{
  position:fixed;z-index:121;left:var(--gut);
  top:calc(var(--bar-h,31px) + var(--nav-h,39px) + var(--tick-h,33px) + 16px);
  font-family:var(--hud);font-size:11px;line-height:1.7;letter-spacing:.3em;
  text-transform:uppercase;color:var(--muted);pointer-events:none;
  text-shadow:0 0 12px rgba(var(--primary-rgb),.25);
  opacity:0;animation:pdpt 1.1s steps(1) both;
}
@keyframes pdpt{0%{opacity:0}18%{opacity:1}30%{opacity:.2}44%{opacity:1}62%{opacity:.35}100%{opacity:1}}
#pdpt.out{opacity:0;animation:none;transition:opacity .8s steps(5)}
html[data-motion="off"] #pdpt{opacity:1;animation:none}

#boot-frame{
  --fg:var(--window-fg);
  --primary:var(--window-primary);
  --primary-lo:var(--window-primary);
  --primary-rgb:var(--window-primary-rgb);
  --primary-lo-rgb:var(--window-primary-rgb);
  --muted:var(--window-muted);
  --muted-rgb:var(--window-muted-rgb);
  --grid:var(--window-grid);
  --grid-rgb:var(--window-grid-rgb);
  --accent:var(--window-accent);
  --accent-rgb:var(--window-accent-rgb);
  --alert:var(--window-alert);
  --alert-rgb:var(--window-alert-rgb);
}
#boot-frame{
  background:rgba(var(--window-rgb),var(--win-a));
  color:var(--window-fg);
  border-color:var(--window-border);
  box-shadow:0 8px 22px rgba(var(--shade-rgb),.18),inset 0 1px 0 rgba(var(--primary-rgb),.12);
}
/* a light blur keeps text readable over the glyph rain and wires */
#boot-frame{
  -webkit-backdrop-filter:blur(5px);backdrop-filter:blur(5px);
}
```

## HTML

```html
<div id="pdpt" aria-hidden="true">Present day.<br>Present time.</div>

<!-- ===================== BOOT ===================== -->
<div id="boot" aria-hidden="true">
  <div id="boot-frame">
    <div class="hdr"><span>NAVI // WIRED UPLINK</span><span>LAYER 07</span></div>
    <pre id="bootlog"></pre>
    <div class="bar"><span id="bootbar"></span></div>
    <div class="grant">ACCESS GRANTED</div>
    <div class="wired">No matter where you are, we are always connected.</div>
  </div>
  <div class="skip">click anywhere to enter</div>
</div>
```

## JavaScript

```javascript
  /* ---------- boot ---------- */
  var boot = document.getElementById('boot'), log = document.getElementById('bootlog');
  var bar = document.getElementById('bootbar');
  /* the entry count is read off the log itself, so the boot screen cannot
     claim a number the page does not have */
  var NEWSN = document.querySelectorAll('.news li').length;
  var lines = [
    '> connect :: protocol seven ...... <span class="ok">LINKED</span>',
    '> pull latest updates ............ <span class="ok">OK</span>',
    '> mount /dev/portfolio ........... <span class="ok">OK</span>',
    '> load identity.dat .............. <span class="ok">OK</span>',
    '> load projects.idx  [<span data-repo-count="18">18</span> REPOS] .. <span class="ok">OK</span>',
    '> sync news.log  ['+NEWSN+' ENTRIES] .... <span class="ok">OK</span>',
    '> link neow.orbital .............. <span class="ok">READY</span>',
    '> verify checksums ............... <span class="ok">OK</span>',
    '> render'
  ];
  /* the opener goes out with the boot screen it was printed on, so it never
     sits over the hero. With the boot skipped it simply holds a beat. */
  var pdpt = document.getElementById('pdpt');
  function dropPdpt(hold){
    if(!pdpt) return;
    setTimeout(function(){
      pdpt.classList.add('out');
      setTimeout(function(){ if(pdpt.parentNode) pdpt.parentNode.removeChild(pdpt); }, 900);
    }, hold);
  }
  /* Entering is a deliberate act: the boot screen has no timer on it. It
     prints its log, the door lights up, and it waits. A click anywhere opens
     it — so does any key, so nobody who cannot reach a pointer is shut out,
     and so does a long stall, which is the one case where waiting would be
     the wrong answer. */
  var entered = false, standby;
  function onKey(e){
    if(e.metaKey || e.ctrlKey || e.altKey) return;   /* not a browser shortcut */
    finishBoot();
  }
  function finishBoot(){
    if(entered) return;
    entered = true;
    clearTimeout(standby);
    window.removeEventListener('keydown', onKey);
    boot.classList.add('done');
    startHero();
    dropPdpt(0);
  }
  if(reduce){ entered = true; boot.style.display='none'; startHero(); dropPdpt(2200); }
  else {
    var i = 0;
    (function next(){
      if(entered) return;
      if(i >= lines.length){
        bar.style.width = '100%';
        boot.classList.add('granted');
        /* the sign-off lands first, then the prompt lights up under it */
        setTimeout(function(){ if(!entered) boot.classList.add('ready'); }, 620);
        standby = setTimeout(finishBoot, 45000);   /* left open, not left stuck */
        return;
      }
      log.innerHTML += lines[i++] + '\n';
      paintRepos();                          /* the log is rebuilt on each line */
      bar.style.width = Math.round(i/lines.length*100) + '%';
      setTimeout(next, 260);
    })();
    boot.addEventListener('click', finishBoot);
    window.addEventListener('keydown', onKey);
  }
```
