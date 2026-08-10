/* Preloader → IDE typing intro.
   One file because they're a single choreographed handoff: the hero starts
   revealing as the preloader wipes away, not after it.

   The "should this play at all" decision was already made pre-paint by the
   blocking script in base.html, which sets html.intro-pending. Deciding it
   here would mean a visible flash of the finished hero first. */
(function () {
  'use strict';

  var root = document.documentElement;
  var hero = document.querySelector('.hero');
  var pre = document.getElementById('preloader');
  var card = document.getElementById('code-card');
  var out = document.getElementById('code-out');
  var ac = document.getElementById('code-ac');
  var fill = document.getElementById('pre-fill');
  var count = document.getElementById('pre-count');

  if (!hero || !out) return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- the snippet ------------------------------------------------------ */

  // [text, token class]; null = plain.
  // Broken across lines the way it actually would be in an editor, so a
  // narrow card never wraps a string mid-word.
  var SNIPPET = [
    ['const', 'tok-key'], [' joseph ', null], ['=', 'tok-punc'], [' {', 'tok-punc'], ['\n', null],
    ['  name', 'tok-prop'], [': ', 'tok-punc'], ['"Joseph Edward"', 'tok-str'], [',', 'tok-punc'], ['\n', null],
    ['  role', 'tok-prop'], [': ', 'tok-punc'], ['"Full-stack engineer"', 'tok-str'], [',', 'tok-punc'], ['\n', null],
    ['  stack', 'tok-prop'], [': ', 'tok-punc'], ['[', 'tok-punc'], ['\n', null],
    ['    "Django"', 'tok-str'], [', ', 'tok-punc'], ['"Next.js"', 'tok-str'], [',', 'tok-punc'], ['\n', null],
    ['    "React Native"', 'tok-str'], [', ', 'tok-punc'], ['"Expo"', 'tok-str'], [',', 'tok-punc'], ['\n', null],
    ['  ]', 'tok-punc'], [',', 'tok-punc'], ['\n', null],
    ['  open', 'tok-prop'], [': ', 'tok-punc'], ['"contract & remote"', 'tok-str'], [',', 'tok-punc'], ['\n', null],
    ['}', 'tok-punc']
  ];

  // Flatten to characters, each carrying its token class, so colour appears
  // as a character is typed rather than being repainted afterwards.
  var CHARS = [];
  SNIPPET.forEach(function (part) {
    for (var i = 0; i < part[0].length; i++) CHARS.push([part[0][i], part[1]]);
  });

  // Where the autocomplete popup flashes: right after `stack:   [`.
  var AC_AT = (function () {
    var n = 0;
    for (var i = 0; i < SNIPPET.length; i++) {
      n += SNIPPET[i][0].length;
      if (SNIPPET[i][0] === '[') return n;
    }
    return -1;
  })();

  function renderFull() {
    out.textContent = '';
    SNIPPET.forEach(function (part) {
      var node = document.createTextNode(part[0]);
      if (part[1]) {
        var span = document.createElement('span');
        span.className = part[1];
        span.appendChild(node);
        out.appendChild(span);
      } else {
        out.appendChild(node);
      }
    });
  }

  /* --- typing ----------------------------------------------------------- */

  var timer = null;
  var finished = false;

  function finish() {
    if (finished) return;
    finished = true;
    window.clearTimeout(timer);
    renderFull();
    if (card) { card.classList.remove('is-typing'); card.classList.add('is-done'); }
    if (ac) ac.classList.remove('is-on');
  }

  function type() {
    if (finished) return;
    if (card) card.classList.add('is-typing');

    var i = 0;
    var span = null;
    var spanClass;

    function step() {
      if (finished) return;
      if (i >= CHARS.length) { finish(); return; }

      var ch = CHARS[i][0];
      var cls = CHARS[i][1];

      if (cls !== spanClass || (cls && !span)) {
        if (cls) {
          span = document.createElement('span');
          span.className = cls;
          out.appendChild(span);
        } else {
          span = null;
        }
        spanClass = cls;
      }

      (span || out).appendChild(document.createTextNode(ch));
      i++;

      if (i === AC_AT && ac) {
        ac.classList.add('is-on');
        window.setTimeout(function () { ac.classList.remove('is-on'); }, 900);
      }

      // Jittered cadence — perfectly even typing is the tell.
      var delay = 17 + Math.random() * 34;
      if (ch === '\n') delay = 150 + Math.random() * 90;
      else if (ch === ',' || ch === '{') delay = 90 + Math.random() * 60;
      else if (ch === ' ') delay = 22 + Math.random() * 30;
      if (i === AC_AT) delay = 620;

      timer = window.setTimeout(step, delay);
    }

    step();
  }

  /* --- reveal / skip ---------------------------------------------------- */

  function reveal() {
    root.classList.remove('intro-pending');
    void hero.offsetWidth;            // flush, so the transition runs
    hero.classList.add('is-revealing');
  }

  var SKIP_EVENTS = ['pointerdown', 'keydown', 'wheel', 'touchstart'];

  function onSkip(e) {
    // A Tab into the skip-link, or a modifier chord, isn't "skip".
    if (e.type === 'keydown' && (e.key === 'Tab' || e.metaKey || e.ctrlKey || e.altKey)) return;
    skipAll();
  }

  function detachSkip() {
    SKIP_EVENTS.forEach(function (t) { window.removeEventListener(t, onSkip); });
  }

  function skipAll() {
    detachSkip();
    dismissPre(true);
    reveal();
    finish();
  }

  /* --- preloader -------------------------------------------------------- */

  var preDone = false;

  function dismissPre(instant) {
    if (preDone || !pre) return;
    preDone = true;
    pre.classList.add('is-done');
    window.setTimeout(function () { pre.style.display = 'none'; },
      instant || reduced ? 0 : 950);
  }

  function runPreloader(done) {
    if (!pre || !fill || !count) { done(); return; }

    var START = Date.now();
    var FLOOR = 700;    // no ugly flash on a warm cache
    var CEIL = 2500;    // always dismisses, even if an asset hangs
    var shown = 0;
    var signals = 0;
    var TOTAL = 3;
    var settled = false;

    function bump() { signals = Math.min(TOTAL, signals + 1); }

    function settle() {
      if (settled) return;
      settled = true;
      window.clearTimeout(hardStop);
      fill.style.width = '100%';
      count.textContent = '100';
      window.setTimeout(function () { dismissPre(false); done(); }, 180);
    }

    // rAF is paused in background tabs, so the ceiling can't live in the
    // animation loop — a page opened in a background tab would sit on the
    // preloader until it was focused. This timer always fires.
    var hardStop = window.setTimeout(settle, CEIL + 400);

    // Real signals: fonts, the first project image, and window load.
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(bump, bump);
    } else { bump(); }

    var src = pre.getAttribute('data-preload');
    if (src) {
      var img = new Image();
      img.onload = img.onerror = bump;
      img.src = src;
    } else { bump(); }

    if (document.readyState === 'complete') bump();
    else window.addEventListener('load', bump, { once: true });

    (function tick() {
      if (settled) return;

      var elapsed = Date.now() - START;
      var loaded = signals / TOTAL;
      var ready = loaded >= 1 || elapsed >= CEIL;

      // Take whichever is further along: real loading, or a slow ramp so the
      // bar never sits frozen. Hold below 100 until we're allowed to finish.
      var target = Math.max(loaded, Math.min(1, elapsed / CEIL));
      if (!(ready && elapsed >= FLOOR)) target = Math.min(target, 0.93);

      shown += (target - shown) * 0.12;
      var pct = Math.round(shown * 100);
      fill.style.width = (shown * 100).toFixed(2) + '%';
      count.textContent = pct < 10 ? '0' + pct : String(pct);

      if (ready && elapsed >= FLOOR && pct >= 99) { settle(); return; }

      window.requestAnimationFrame(tick);
    })();
  }

  /* --- go --------------------------------------------------------------- */

  if (!root.classList.contains('intro-pending')) {
    // Already seen this session, or reduced motion: resting state, no motion.
    hero.classList.add('is-revealing');
    finish();
    if (pre) pre.style.display = 'none';
    return;
  }

  SKIP_EVENTS.forEach(function (t) {
    window.addEventListener(t, onSkip, { passive: true });
  });

  runPreloader(function () {
    reveal();
    window.setTimeout(type, 520);
    window.setTimeout(detachSkip, 400);
  });
})();
