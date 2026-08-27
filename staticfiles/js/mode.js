/* Experience / Engineering lens switch.

   The mode itself is resolved before first paint by the blocking script in
   base.html and expressed as data-mode on the root element, with CSS hiding
   the inactive lens. None of that lives here, deliberately: by the time this
   file runs the page is already correct.

   What this handles is changing the mode: intercepting the two links so the
   page does not reload, keeping the URL shareable, remembering the choice,
   and putting the reader back where they were. With JavaScript off the links
   are ordinary navigations and the server renders the right lens, so this is
   an upgrade rather than a requirement. */
(function () {
  'use strict';

  var MODES = { experience: 1, engineering: 1 };
  var DEFAULT_MODE = 'experience';

  var root = document.documentElement;
  // No early return when the switch is absent: everything below tolerates an
  // empty list, and bailing would leave JE.mode undefined for the palette,
  // which would then need its own copy of the rules.
  var opts = Array.prototype.slice.call(document.querySelectorAll('[data-mode-set]'));

  function valid(value) {
    return MODES[value] === 1 ? value : null;
  }

  function fromLocation() {
    var found = /[?&]mode=([^&#]*)/.exec(window.location.search);
    if (!found) return null;
    try {
      return valid(decodeURIComponent(found[1]));
    } catch (e) {
      // A malformed escape sequence is not a third state either.
      return null;
    }
  }

  function current() {
    return valid(root.getAttribute('data-mode')) || DEFAULT_MODE;
  }

  /* Where each option goes from where we are now: same path, same unrelated
     parameters, mode swapped, and no parameter at all for the default so
     ordinary URLs stay clean. The fragment is carried because the server
     never sees it and would otherwise drop it. */
  function urlFor(mode) {
    var params = new URLSearchParams(window.location.search);
    if (mode === DEFAULT_MODE) params.delete('mode');
    else params.set('mode', mode);
    var query = params.toString();
    return window.location.pathname + (query ? '?' + query : '') + window.location.hash;
  }

  /* The server rendered these against the mode it could see. If the stored
     preference differed, the pre-paint script already changed the mode and
     left this markup describing the wrong one, so it is resynced on load as
     well as after every switch. */
  function sync() {
    var mode = current();
    opts.forEach(function (opt) {
      var target = opt.dataset.modeSet;
      if (target === mode) opt.setAttribute('aria-current', 'true');
      else opt.removeAttribute('aria-current');
      opt.href = urlFor(target);
    });
  }

  function restore(y) {
    if (window.pageYOffset === y) return;
    try {
      window.scrollTo({ top: y, left: 0, behavior: 'instant' });
    } catch (e) {
      // Older engines reject the options form; the jump matters more than
      // the smoothness of it.
      window.scrollTo(0, y);
    }
  }

  function apply(mode, record) {
    // Swapping one lens for another changes the height of the page under the
    // reader. Hold the scroll offset across the swap so it does not jump.
    var y = window.pageYOffset;

    root.setAttribute('data-mode', mode);

    if (record) {
      try { localStorage.setItem('mode', mode); } catch (e) {}
      window.history.pushState({ mode: mode }, '', urlFor(mode));
    }

    sync();

    // Put the reader back, synchronously. Swapping display:none relayouts
    // immediately, so the correction can happen immediately too, and it must:
    // a requestAnimationFrame here does not run in a background tab, which is
    // exactly where a silent scroll jump would go unnoticed.
    //
    // behavior:'instant' is not decoration. The stylesheet sets
    // scroll-behavior:smooth globally, so a plain scrollTo would animate the
    // correction, which reads as the page sliding away under the reader.
    restore(y);

    // A second pass after the frame, for anything that settles late, such as
    // an image that only now has a box. Cheap, and a no-op when nothing moved.
    window.requestAnimationFrame(function () { restore(y); });
  }

  opts.forEach(function (opt) {
    opt.addEventListener('click', function (e) {
      var mode = valid(opt.dataset.modeSet);
      if (!mode) return;

      // Leave the modified clicks alone; opening a lens in a new tab should
      // work exactly as the href says.
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;

      e.preventDefault();
      if (mode === current()) return;
      apply(mode, true);
    });
  });

  /* The one way anything else changes the mode. The command palette calls
     this rather than carrying its own copy of the rules: there is a single
     mode implementation and this is its front door. */
  var JE = (window.JE = window.JE || {});
  JE.mode = {
    current: current,
    set: function (mode) {
      var wanted = valid(mode);
      if (!wanted || wanted === current()) return current();
      apply(wanted, true);
      return wanted;
    },
    /* Where a path would live in the current mode. Callers building internal
       links use this instead of appending a parameter themselves. */
    urlFor: function (path, fragment) {
      var mode = current();
      var query = mode === DEFAULT_MODE ? '' : '?mode=' + mode;
      return path + query + (fragment ? '#' + fragment : '');
    }
  };

  // Back and forward move between modes, so the URL is what decides here, not
  // the stored preference. A history entry with no mode parameter means the
  // default, which is what that URL would render on a cold load.
  window.addEventListener('popstate', function (e) {
    var mode = (e.state && valid(e.state.mode)) || fromLocation() || DEFAULT_MODE;
    apply(mode, false);
  });

  sync();
})();
