/* Shared frame scheduling.

   Two files were running the same pattern: a passive scroll listener, a
   ticking flag, and a requestAnimationFrame callback that does the real work.
   That is one scroll listener and one frame request each, and the Build Space
   would have made it three. This gives them one of each between them.

   Deliberately small, and deliberately not compulsory. Anything event-driven,
   IntersectionObserver-based, CSS-driven, or a genuine one-shot stays where it
   is: intro.js runs a progress animation with its own lifecycle and its own
   hard stop, and mode.js corrects a scroll offset once. Neither belongs here.

   Two protections are carried over from the code this replaces, both of which
   were paid for in bugs:

     * the ticking flag is cleared in a finally, because a throw that skipped
       the reset froze every later frame;
     * a subscriber that throws is contained, so one broken consumer cannot
       take the scheduler down with it.

   requestAnimationFrame does not run in a background tab. That is correct for
   scroll work, which has nothing to respond to there, but anything that must
   finish regardless needs its own timer, as intro.js has. */
(function () {
  'use strict';

  var JE = (window.JE = window.JE || {});

  var scrollSubs = [];
  var frameSubs = [];
  var scrolling = false;
  var framing = false;
  var listening = false;

  function report(error) {
    // Contained, not swallowed: a broken subscriber should be visible in the
    // console without stopping the ones next to it.
    if (window.console && console.error) console.error('motion subscriber failed', error);
  }

  function run(subs) {
    // Iterate a copy: a subscriber may unsubscribe itself mid-flight.
    subs.slice().forEach(function (fn) {
      try {
        fn();
      } catch (error) {
        report(error);
      }
    });
  }

  function onScrollEvent() {
    if (scrolling) return;
    scrolling = true;
    window.requestAnimationFrame(function () {
      try {
        run(scrollSubs);
      } finally {
        scrolling = false;
      }
    });
  }

  function listen() {
    if (listening) return;
    window.addEventListener('scroll', onScrollEvent, { passive: true });
    listening = true;
  }

  function tick() {
    if (!frameSubs.length) {
      framing = false;
      return;
    }
    try {
      run(frameSubs);
    } finally {
      window.requestAnimationFrame(tick);
    }
  }

  function remove(subs, fn) {
    var at = subs.indexOf(fn);
    if (at !== -1) subs.splice(at, 1);
  }

  JE.motion = {
    /* Run fn after a scroll, coalesced to one frame. Returns an unsubscribe.
       This is not per-frame: it fires when the page has scrolled, which is
       what scroll-driven work actually wants. */
    onScroll: function (fn) {
      scrollSubs.push(fn);
      listen();
      return function () { remove(scrollSubs, fn); };
    },

    /* Run fn every frame until unsubscribed. The loop only exists while
       something is subscribed, so an idle page schedules nothing. */
    onFrame: function (fn) {
      frameSubs.push(fn);
      if (!framing) {
        framing = true;
        window.requestAnimationFrame(tick);
      }
      return function () { remove(frameSubs, fn); };
    },

    /* Ask once, in one place, rather than each file constructing its own
       query. Read at call time so a preference changed mid-session counts. */
    reduced: function () {
      return !!(window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    }
  };
})();
