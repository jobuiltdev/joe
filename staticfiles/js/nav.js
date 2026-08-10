/* Full-screen menu, scroll-spy and exact-section jumping. */
(function () {
  'use strict';

  var bar = document.getElementById('bar');
  var menu = document.getElementById('menu');
  var toggle = document.getElementById('menu-toggle');
  if (!bar || !menu || !toggle) return;

  var links = Array.prototype.slice.call(menu.querySelectorAll('[data-nav-link]'));
  var FOCUSABLE = 'a[href], button:not([disabled])';
  var isOpen = false;
  var pendingTarget = null;

  /* --- open / close ----------------------------------------------------- */

  function lockScroll(on) {
    // Compensate for the scrollbar so the page doesn't shift sideways.
    // Deliberately not `position: fixed` — that loses scroll position on iOS.
    var gap = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.paddingRight = on && gap > 0 ? gap + 'px' : '';
    document.body.classList.toggle('is-locked', on);
    document.body.classList.toggle('menu-open', on);
  }

  function open() {
    if (isOpen) return;
    isOpen = true;
    menu.dataset.state = 'open';
    toggle.setAttribute('aria-expanded', 'true');
    lockScroll(true);
    var first = menu.querySelector(FOCUSABLE);
    if (first) first.focus({ preventScroll: true });
  }

  function close(returnFocus) {
    if (!isOpen) return;
    isOpen = false;
    menu.dataset.state = 'closed';
    toggle.setAttribute('aria-expanded', 'false');
    lockScroll(false);
    if (returnFocus) toggle.focus({ preventScroll: true });
  }

  toggle.addEventListener('click', function () {
    isOpen ? close(true) : open();
  });

  document.addEventListener('keydown', function (e) {
    if (!isOpen) return;

    if (e.key === 'Escape') {
      e.preventDefault();
      close(true);
      return;
    }

    if (e.key !== 'Tab') return;

    // Trap focus inside the sheet while it's open.
    var items = Array.prototype.slice.call(menu.querySelectorAll(FOCUSABLE))
      .filter(function (el) { return el.offsetParent !== null; });
    if (!items.length) return;

    var first = items[0];
    var last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });

  /* --- jumping to a section -------------------------------------------- */

  function scrollToSection(id) {
    var target = document.getElementById(id);
    if (!target) return;

    // The deck is (n+1) x 100vh tall, so its element top is the start of the
    // pinned range — which is exactly where we want to land.
    var barH = bar.offsetHeight;
    var y = window.pageYOffset + target.getBoundingClientRect().top - barH + 1;

    window.scrollTo({
      top: Math.max(0, Math.round(y)),
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
    });
  }

  links.forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      pendingTarget = link.dataset.navLink;

      if (!isOpen) {
        scrollToSection(pendingTarget);
        pendingTarget = null;
        return;
      }

      // Close first, then scroll — otherwise you watch the page fly past
      // behind a sheet that's still wiping away.
      close(false);
      var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.setTimeout(function () {
        if (pendingTarget) {
          scrollToSection(pendingTarget);
          pendingTarget = null;
        }
      }, reduced ? 0 : 380);
    });
  });

  /* --- scroll state ----------------------------------------------------- */

  var ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      bar.classList.toggle('is-stuck', window.pageYOffset > window.innerHeight * 0.55);
      ticking = false;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* --- scroll-spy ------------------------------------------------------- */

  var sections = links
    .map(function (l) { return document.getElementById(l.dataset.navLink); })
    .filter(Boolean);

  function setCurrent(id) {
    links.forEach(function (l) {
      l.classList.toggle('is-current', l.dataset.navLink === id);
    });
  }

  if ('IntersectionObserver' in window && sections.length) {
    var visible = new Map();
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        visible.set(entry.target.id, entry.isIntersecting ? entry.intersectionRatio : 0);
      });

      var best = null;
      var bestRatio = 0;
      visible.forEach(function (ratio, id) {
        if (ratio > bestRatio) { bestRatio = ratio; best = id; }
      });
      if (best) setCurrent(best);
    }, {
      // Weight the middle band of the viewport so the "current" section is
      // the one you're actually looking at.
      rootMargin: '-45% 0px -45% 0px',
      threshold: [0, 0.01, 0.5, 1]
    });

    sections.forEach(function (s) { spy.observe(s); });
  }

  // The deck reports its own active panel while you're inside it.
  document.addEventListener('deck:panel', function (e) {
    if (!e.detail) return;
    var link = menu.querySelector('[data-nav-link="work"]');
    if (link) link.dataset.panel = e.detail.index + 1;
  });
})();
