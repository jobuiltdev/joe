/* Pinned horizontal project deck.

   The section is (panels + 1) viewports tall; its inner wrapper sticks for
   that whole range, and scroll progress through the range drives the track's
   translateX. Below the breakpoint, or under reduced motion, none of this
   engages and the panels are a plain vertical stack. */
(function () {
  'use strict';

  var deck = document.querySelector('[data-deck]');
  if (!deck) return;

  var track = deck.querySelector('[data-deck-track]');
  var panels = Array.prototype.slice.call(deck.querySelectorAll('[data-deck-panel]'));
  var shots = Array.prototype.slice.call(deck.querySelectorAll('[data-deck-parallax] img'));
  var segs = Array.prototype.slice.call(deck.querySelectorAll('[data-deck-go]'));
  var current = deck.querySelector('[data-deck-current]');

  if (!track || panels.length < 2) return;

  // Height matters as much as width here: a short window can't fit a panel,
  // and a cramped pinned panel is worse than an honest vertical stack. 620px
  // keeps 1366x768 laptops, a very common size, on the pinned version.
  var wide = window.matchMedia('(min-width: 900px) and (min-height: 620px)');
  var motionOk = window.matchMedia('(prefers-reduced-motion: no-preference)');

  var pinned = false;
  var ticking = false;
  var lastIndex = -1;

  function canPin() { return wide.matches && motionOk.matches; }

  /* --- layout ----------------------------------------------------------- */

  function measure() {
    if (!pinned) {
      deck.style.height = '';
      track.style.transform = '';
      shots.forEach(function (img) { img.style.transform = ''; });
      return;
    }
    // One viewport of scroll per transition, plus one to read the first panel.
    deck.style.height = (panels.length * 100) + 'vh';
  }

  function setPinned(on) {
    if (pinned === on) return;
    pinned = on;
    deck.classList.toggle('is-pinned', on);
    measure();
    render();
  }

  /* --- scroll → transform ----------------------------------------------- */

  function progress() {
    var rect = deck.getBoundingClientRect();
    var range = deck.offsetHeight - window.innerHeight;
    if (range <= 0) return 0;
    return Math.min(1, Math.max(0, -rect.top / range));
  }

  function render() {
    if (!pinned) {
      setIndex(0);
      return;
    }

    var p = progress();
    var span = panels.length - 1;
    var x = -p * span * 100;

    // Percent of the track, not vw. vw includes the scrollbar, which would
    // drift each panel a scrollbar's width off centre.
    track.style.transform = 'translate3d(' + x + '%, 0, 0)';

    // Imagery trails the panel slightly, which reads as depth.
    shots.forEach(function (img, i) {
      var local = p * span - i;             // -1..1 around this panel
      var offset = Math.max(-1, Math.min(1, local)) * 12;
      img.style.transform = 'translate3d(' + offset + '%, 0, 0) scale(1.06)';
    });

    setIndex(Math.round(p * span));
  }

  function setIndex(i) {
    if (i === lastIndex) return;
    lastIndex = i;

    if (current) current.textContent = i < 9 ? '0' + (i + 1) : String(i + 1);
    segs.forEach(function (s, n) { s.classList.toggle('is-on', n === i); });
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      try {
        render();
      } finally {
        // Always clear the guard. A throw here would freeze every later frame.
        ticking = false;
      }
    });
  }

  /* --- jumping ---------------------------------------------------------- */

  function goTo(i) {
    if (!pinned) {
      panels[i].scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    var range = deck.offsetHeight - window.innerHeight;
    var top = deck.offsetTop + (i / (panels.length - 1)) * range;
    window.scrollTo({ top: Math.round(top), behavior: 'smooth' });
  }

  segs.forEach(function (seg) {
    seg.addEventListener('click', function () {
      goTo(parseInt(seg.dataset.deckGo, 10) || 0);
    });
  });

  // Arrow keys move between panels, but only while the deck is on screen and
  // the user isn't typing into the contact form.
  document.addEventListener('keydown', function (e) {
    if (!pinned) return;
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;

    var tag = document.activeElement && document.activeElement.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    if (document.body.classList.contains('menu-open')) return;

    var rect = deck.getBoundingClientRect();
    if (rect.top > 0 || rect.bottom < window.innerHeight) return;

    e.preventDefault();
    var next = lastIndex + (e.key === 'ArrowRight' ? 1 : -1);
    goTo(Math.max(0, Math.min(panels.length - 1, next)));
  });

  /* --- wiring ----------------------------------------------------------- */

  function sync() {
    setPinned(canPin());
    measure();
    render();
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', sync);
  window.addEventListener('orientationchange', sync);

  // Safari <14 only has the deprecated listener API.
  if (wide.addEventListener) {
    wide.addEventListener('change', sync);
    motionOk.addEventListener('change', sync);
  } else if (wide.addListener) {
    wide.addListener(sync);
    motionOk.addListener(sync);
  }

  sync();
})();
