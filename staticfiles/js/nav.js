/* Rail navigation: exact-section jumping and scroll-spy.

   The rail is always on screen, so there's no overlay to trap focus in and no
   scroll to lock — it's just anchors plus a current-section indicator. */
(function () {
  'use strict';

  var bar = document.getElementById('bar');
  var links = Array.prototype.slice.call(document.querySelectorAll('[data-nav-link]'));
  if (!links.length) return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* --- jumping to a section -------------------------------------------- */

  function scrollToSection(id) {
    if (id === 'top') {
      window.scrollTo({ top: 0, behavior: reduced.matches ? 'auto' : 'smooth' });
      return;
    }

    var target = document.getElementById(id);
    if (!target) return;

    // The deck is (n+1) x 100vh tall, so its element top is the start of the
    // pinned range — which is exactly where we want to land.
    var offset = bar ? bar.offsetHeight : 0;
    var y = window.pageYOffset + target.getBoundingClientRect().top - offset + 1;

    window.scrollTo({
      top: Math.max(0, Math.round(y)),
      behavior: reduced.matches ? 'auto' : 'smooth'
    });
  }

  links.forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      scrollToSection(link.dataset.navLink);
    });
  });

  /* --- bar backing ------------------------------------------------------ */

  var ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      try {
        if (bar) {
          bar.classList.toggle('is-stuck', window.pageYOffset > window.innerHeight * 0.55);
        }
      } finally {
        // Always clear the guard — a throw here would freeze every later frame.
        ticking = false;
      }
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* --- scroll-spy ------------------------------------------------------- */

  var railItems = links.filter(function (l) { return l.classList.contains('rail__item'); });

  var sections = railItems
    .map(function (l) { return document.getElementById(l.dataset.navLink); })
    .filter(Boolean);

  function setCurrent(id) {
    railItems.forEach(function (l) {
      var on = l.dataset.navLink === id;
      l.classList.toggle('is-current', on);
      if (on) l.setAttribute('aria-current', 'true');
      else l.removeAttribute('aria-current');
    });
  }

  if ('IntersectionObserver' in window && sections.length) {
    var ratios = {};

    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        ratios[entry.target.id] = entry.isIntersecting ? entry.intersectionRatio : 0;
      });

      var best = null;
      var bestRatio = 0;
      Object.keys(ratios).forEach(function (id) {
        if (ratios[id] > bestRatio) { bestRatio = ratios[id]; best = id; }
      });
      setCurrent(best);            // null above the first section clears it
    }, {
      // Weight the middle band so "current" is what you're actually reading.
      rootMargin: '-45% 0px -45% 0px',
      threshold: [0, 0.01, 0.5, 1]
    });

    sections.forEach(function (s) { spy.observe(s); });
  }
})();
