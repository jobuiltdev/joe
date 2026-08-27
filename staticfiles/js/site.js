/* Theme toggle + contact form submit state. */
(function () {
  'use strict';

  /* --- theme ------------------------------------------------------------ */

  var toggle = document.getElementById('theme-toggle');

  function current() {
    var stored = null;
    try { stored = localStorage.getItem('theme'); } catch (e) {}
    if (stored === 'dark' || stored === 'light') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  if (toggle) {
    toggle.addEventListener('click', function () {
      var next = current() === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) {}
      toggle.setAttribute('aria-label',
        next === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
    });
  }

  /* --- contact form ----------------------------------------------------- */

  var form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function () {
      var btn = form.querySelector('[data-submit]');
      if (!btn) return;
      // Let the native POST proceed; just stop double-sends and show progress.
      btn.disabled = true;
      btn.dataset.state = 'sending';
      var label = btn.querySelector('[data-submit-label]');
      if (label) label.textContent = 'Sending';
    });
  }

  /* --- scroll reveal ---------------------------------------------------- */

  /* Entries in the work index rise in as they arrive. Purely additive: the
     CSS default is the finished state, and the hidden start is scoped to
     .has-js, so nothing here is load-bearing.

     IntersectionObserver rather than a scroll subscription because this is a
     one-shot per element and there is no per-frame work to do. */
  (function reveal() {
    var items = document.querySelectorAll('[data-reveal]');
    if (!items.length) return;

    var motion = (window.JE || {}).motion;
    var reduced = motion ? motion.reduced()
      : window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Reduced motion, or an engine without the observer: leave the section
    // alone entirely. Nothing has been hidden at this point, because the
    // hidden state is scoped to .is-revealing and only added below.
    if (reduced || !('IntersectionObserver' in window)) return;

    // Opt in only now that there is definitely something to undo it.
    Array.prototype.forEach.call(document.querySelectorAll('.index'), function (section) {
      section.classList.add('is-revealing');
    });

    var fired = false;

    var seen = new IntersectionObserver(function (entries) {
      fired = true;
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        // One-shot: an entry does not un-reveal on the way back up.
        seen.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.05 });

    Array.prototype.forEach.call(items, function (el) { seen.observe(el); });

    /* Safety net. An observer that never reports leaves every entry at
       opacity 0, which turns a decorative reveal into a blank section — a
       far worse outcome than an unanimated one. If nothing has been reported
       at all by now, assume it will not be and show the work.

       Deliberately keyed on "never fired once" rather than a blanket timer,
       so a reader who simply has not scrolled yet still gets the effect. */
    window.setTimeout(function () {
      if (fired) return;
      Array.prototype.forEach.call(items, function (el) { el.classList.add('is-in'); });
    }, 3000);
  })();

  /* --- work index video ------------------------------------------------- */

  /* Demo clips in Selected Work play as they come into view and stop as they
     leave, so scrolling the list reads like a showreel rather than a wall of
     posters waiting to be clicked.

     Scoped to .index__item on purpose. The Build Space hero drives its own
     clips from build.js on hover and focus, and the legacy deck drives its own
     from deck.js; neither has an .index__item above it, so neither can be
     reached from here.

     Everything is additive. The markup already carries muted/loop/playsinline
     and native controls, so with this file absent the clips are still ordinary
     videos a visitor can play. */
  (function indexVideo() {
    var videos = document.querySelectorAll('.index__item video');
    if (!videos.length) return;

    var motion = (window.JE || {}).motion;
    var reduced = motion ? motion.reduced()
      : window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Reduced motion, or no observer: leave the clips exactly as the markup
    // left them — poster, controls, and playback on request.
    if (reduced || !('IntersectionObserver' in window)) return;

    // How much of a clip has to be on screen before it earns playback. High
    // enough that a strip at the edge of the viewport does not start it.
    var PLAY_AT = 0.6;

    var state = Array.prototype.map.call(videos, function (el) {
      return { el: el, ratio: 0 };
    });
    var playing = null;

    function pause(el) {
      if (el && !el.paused) el.pause();
    }

    function start(el) {
      if (playing === el) return;   // already the subject; do not fight a manual pause
      pause(playing);
      playing = el;

      // Both are set in the markup; re-asserting them is what keeps autoplay
      // permitted if anything else ever changes them.
      el.muted = true;
      el.playsInline = true;

      var started = el.play();
      if (!started || !started.catch) return;
      started.catch(function () {
        // Blocked by policy, or scrolled away before it was ready. The poster
        // and the controls are still there, so there is nothing to recover.
        if (playing === el) playing = null;
      });
    }

    /* One clip at a time. Whichever is most visible wins, so two entries on
       screen together cannot both run. */
    function refresh() {
      var best = null;
      state.forEach(function (s) {
        if (s.ratio >= PLAY_AT && (!best || s.ratio > best.ratio)) best = s;
      });

      if (!best) {
        pause(playing);
        playing = null;
        return;
      }
      start(best.el);
    }

    var visibility = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        state.forEach(function (s) {
          if (s.el === entry.target) s.ratio = entry.intersectionRatio;
        });
      });
      refresh();
    }, { threshold: [0, 0.25, 0.5, PLAY_AT, 0.8, 1] });

    /* Rewinding is a separate question from pausing. A clip that has merely
       scrolled off the edge should keep its position, so coming back does not
       restart it mid-gesture; one that is a viewport and a half away is not
       coming back soon and may as well start from the top. */
    var distant = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) return;
        try { entry.target.currentTime = 0; } catch (e) {}
      });
    }, { rootMargin: '150% 0px 150% 0px', threshold: 0 });

    state.forEach(function (s) {
      visibility.observe(s.el);
      distant.observe(s.el);

      // Playing one by hand is still playing one: hold the invariant however
      // playback started, and let a manual play take over as the subject.
      s.el.addEventListener('play', function () {
        state.forEach(function (other) {
          if (other.el !== s.el) pause(other.el);
        });
        playing = s.el;
      });
    });
  })();

  /* --- dismissible flash messages --------------------------------------- */

  Array.prototype.forEach.call(document.querySelectorAll('[data-dismiss]'), function (btn) {
    btn.addEventListener('click', function () {
      var note = btn.closest('.note');
      if (note) note.remove();
    });
  });
})();
