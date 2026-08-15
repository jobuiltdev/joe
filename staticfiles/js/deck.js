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
  var videos = Array.prototype.slice.call(deck.querySelectorAll('[data-deck-video]'));

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
    // One viewport to read a panel, then a shorter run per transition. A full
    // viewport each was fine at three panels; past that the section turns into
    // a scroll tunnel, so transitions cost 70vh and the deck stays roughly the
    // length it was.
    deck.style.height = (100 + (panels.length - 1) * 70) + 'vh';
  }

  function setPinned(on) {
    if (pinned === on) return;
    pinned = on;
    deck.classList.toggle('is-pinned', on);
    // The two modes drive playback differently, so clear the old mode's
    // state rather than leave a clip running that nothing now owns.
    pauseAll();
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
    syncVideo();
  }

  /* --- demo videos ------------------------------------------------------ */

  // Which panel each clip belongs to, resolved once. Panels without a demo
  // simply aren't in this list.
  var videoPanel = videos.map(function (v) {
    return panels.indexOf(v.closest('[data-deck-panel]'));
  });
  var deckOnScreen = false;

  function play(v) {
    // Autoplay is a request, not a guarantee: Low Power Mode, a data saver or
    // a per-site policy can refuse it, and the rejection is the only signal we
    // get. Swallowing it silently is what left phones showing a dead poster,
    // so the frame keeps its play button and the refusal just means the button
    // stays up for the user to tap.
    var started = v.play();
    if (started && started.catch) started.catch(function () {});
  }

  videos.forEach(function (v) {
    // iOS gates inline autoplay on the muted property, not only the attribute.
    // Setting it explicitly removes a class of works-everywhere-but-the-phone
    // failures that are invisible on a desktop.
    v.muted = true;

    var frame = v.closest('.panel__phone');
    if (!frame) return;

    // Driven by what the element actually does, not by what we asked it to do.
    v.addEventListener('playing', function () { frame.classList.add('is-playing'); });
    v.addEventListener('pause', function () { frame.classList.remove('is-playing'); });

    var btn = frame.querySelector('[data-deck-play]');
    if (!btn) return;
    btn.addEventListener('click', function () {
      // A tap is a user gesture, so this is the one call that is never
      // refused. It is the guaranteed path wherever autoplay is blocked.
      if (v.paused) play(v); else v.pause();
    });
  });

  function pauseAll() {
    videos.forEach(function (v) { if (!v.paused) v.pause(); });
  }

  // Only the panel being read plays. Two portrait clips decoding at once
  // costs battery on a phone and frame budget on the deck's own transform.
  function syncVideo() {
    if (!videos.length) return;
    // Pinning already requires motion to be allowed, so getting this far means
    // autoplay is welcome. The stack observer owns the unpinned case.
    if (!pinned) return;
    if (!deckOnScreen) { pauseAll(); return; }

    videos.forEach(function (v, n) {
      if (videoPanel[n] === lastIndex) play(v);
      else if (!v.paused) v.pause();
    });
  }

  if (videos.length && window.IntersectionObserver) {
    // Scrolling past the deck entirely should stop playback, which panel
    // index alone can't tell us.
    new IntersectionObserver(function (entries) {
      deckOnScreen = entries[0].isIntersecting;
      syncVideo();
    }, { threshold: 0 }).observe(deck);

    // Unpinned, the panels are a vertical stack and there is no active index,
    // so each clip plays while it's the one actually on screen.
    var stack = new IntersectionObserver(function (entries) {
      if (pinned) return;
      entries.forEach(function (e) {
        // Leaving the screen always stops a clip, including one the user
        // started by hand under reduced motion. Only the starting is
        // conditional on the preference.
        if (!e.isIntersecting) {
          if (!e.target.paused) e.target.pause();
        } else if (motionOk.matches) {
          play(e.target);
        }
      });
    }, { threshold: 0.6 });
    videos.forEach(function (v) { stack.observe(v); });
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

    // Reduced motion means nothing starts on its own. The play button is
    // always there, so a deliberate tap is still a way in, and user-initiated
    // playback is not what the preference is asking us to suppress. This can
    // flip mid-session.
    if (!motionOk.matches) pauseAll();

    syncVideo();
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
