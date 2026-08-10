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

  /* --- dismissible flash messages --------------------------------------- */

  Array.prototype.forEach.call(document.querySelectorAll('[data-dismiss]'), function (btn) {
    btn.addEventListener('click', function () {
      var note = btn.closest('.note');
      if (note) note.remove();
    });
  });
})();
