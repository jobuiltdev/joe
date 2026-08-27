/* Command palette.

   The dialog element does the heavy lifting: showModal() traps focus, makes
   the page behind it inert, and handles Escape. None of that is reimplemented
   here. What is left is search, arrow navigation, and activation.

   Mode is not reimplemented either. Switching goes through JE.mode.set and
   internal links are built with JE.mode.urlFor, so there is one implementation
   of the rules and the palette is a caller of it. */
(function () {
  'use strict';

  var dialog = document.getElementById('palette');
  var data = document.getElementById('palette-data');
  if (!dialog || !data || typeof dialog.showModal !== 'function') return;

  var input = document.getElementById('palette-input');
  var list = document.getElementById('palette-list');
  var empty = document.getElementById('palette-empty');

  var COMMANDS = [];
  try {
    COMMANDS = JSON.parse(data.textContent) || [];
  } catch (e) {
    return;
  }

  var results = [];
  var active = -1;
  var opener = null;

  var mode = function () { return (window.JE || {}).mode; };

  /* --- search ----------------------------------------------------------- */

  /* Every token in the query has to appear somewhere in the command's terms.
     That makes "django mobile" narrower than either word alone, which is what
     someone typing two words means. Substring rather than whole-word, so
     "postgres" still finds "PostgreSQL".

     Deliberately not fuzzy. Fuzzy matching earns its complexity when the set
     is large and the names are unfamiliar; seventeen commands the owner named
     himself is neither. */
  function score(command, tokens) {
    var terms = command.terms || '';
    var label = (command.label || '').toLowerCase();

    for (var i = 0; i < tokens.length; i++) {
      if (terms.indexOf(tokens[i]) === -1) return -1;
    }

    // Rank: a name that starts with the query beats one that merely contains
    // it, which beats a match found only in the tech list.
    if (!tokens.length) return 0;
    if (label.indexOf(tokens[0]) === 0) return 3;
    if (label.indexOf(tokens[0]) !== -1) return 2;
    return 1;
  }

  function search(query) {
    var tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
    var scored = [];

    COMMANDS.forEach(function (command, index) {
      var rank = score(command, tokens);
      if (rank >= 0) scored.push({ command: command, rank: rank, index: index });
    });

    // Stable: equal ranks keep the order the server sent, which is projects
    // first and the owner's own ordering within them.
    scored.sort(function (a, b) {
      return b.rank - a.rank || a.index - b.index;
    });

    return scored.map(function (entry) { return entry.command; });
  }

  /* --- rendering -------------------------------------------------------- */

  function render(query) {
    results = search(query);
    list.textContent = '';

    var group = null;
    results.forEach(function (command, i) {
      if (command.group !== group) {
        group = command.group;
        var heading = document.createElement('li');
        heading.className = 'palette__group mono';
        // Presentational: the group name is a visual grouping, and announcing
        // it as an option would put a non-choice in the listbox.
        heading.setAttribute('role', 'presentation');
        heading.textContent = group;
        list.appendChild(heading);
      }

      var item = document.createElement('li');
      item.className = 'palette__item';
      item.id = 'palette-option-' + i;
      item.setAttribute('role', 'option');
      item.setAttribute('aria-selected', 'false');
      item.dataset.index = String(i);

      var label = document.createElement('span');
      label.className = 'palette__label';
      label.textContent = command.label;
      item.appendChild(label);

      if (command.hint) {
        var hint = document.createElement('span');
        hint.className = 'palette__hint';
        hint.textContent = command.hint;
        item.appendChild(hint);
      }

      if (command.external) {
        var mark = document.createElement('span');
        mark.className = 'palette__ext mono';
        mark.setAttribute('aria-hidden', 'true');
        mark.textContent = 'external';
        item.appendChild(mark);
      }

      list.appendChild(item);
    });

    empty.hidden = results.length > 0;
    setActive(results.length ? 0 : -1);
  }

  function setActive(next) {
    var previous = list.querySelector('.is-active');
    if (previous) {
      previous.classList.remove('is-active');
      previous.setAttribute('aria-selected', 'false');
    }

    active = next;
    if (active < 0) {
      input.setAttribute('aria-activedescendant', '');
      return;
    }

    var item = document.getElementById('palette-option-' + active);
    if (!item) return;
    item.classList.add('is-active');
    item.setAttribute('aria-selected', 'true');
    // The input keeps focus throughout; this is how the selection is announced.
    input.setAttribute('aria-activedescendant', item.id);
    item.scrollIntoView({ block: 'nearest' });
  }

  function move(delta) {
    if (!results.length) return;
    var next = active + delta;
    if (next < 0) next = results.length - 1;
    if (next >= results.length) next = 0;
    setActive(next);
  }

  /* --- activation ------------------------------------------------------- */

  function activate(index, event) {
    var command = results[index];
    if (!command) return;

    if (command.action === 'mode') {
      var api = mode();
      if (api) api.set(command.value);
      close();
      return;
    }

    var url = command.url;
    if (!url) {
      // Internal: the mode belongs in the URL, and JE.mode owns that rule.
      var api2 = mode();
      url = api2 ? api2.urlFor(command.path, command.fragment)
                 : command.path + (command.fragment ? '#' + command.fragment : '');
    }

    // Honour the intent behind a modified click even though these are options
    // rather than anchors.
    var newTab = event && (event.metaKey || event.ctrlKey || event.button === 1);
    if (newTab || command.external) {
      window.open(url, '_blank', 'noopener');
      if (!newTab) close();
      return;
    }

    close();
    window.location.assign(url);
  }

  /* --- open and close --------------------------------------------------- */

  function lockScroll(on) {
    var root = document.documentElement;
    if (on) {
      // Compensate for the scrollbar so locking does not shift the page.
      var gap = window.innerWidth - root.clientWidth;
      if (gap > 0) root.style.setProperty('--palette-gap', gap + 'px');
      root.classList.add('palette-open');
    } else {
      root.classList.remove('palette-open');
      root.style.removeProperty('--palette-gap');
    }
  }

  function open() {
    if (dialog.open) return;
    opener = document.activeElement;
    input.value = '';
    render('');
    lockScroll(true);
    dialog.showModal();
    input.focus();
  }

  /* Unlock the page and give focus back. Written to be safe to call twice,
     because it is: once from close() and once from the dialog's own event. */
  function teardown() {
    lockScroll(false);
    if (opener && typeof opener.focus === 'function' && document.contains(opener)) {
      opener.focus();
    }
    opener = null;
  }

  function close() {
    if (!dialog.open) return;
    dialog.close();
    // Not left to the close event. That event did not fire on a scripted
    // close during testing, which left the page scroll-locked with the
    // palette already gone: the worst kind of bug, because the thing that
    // caused it is no longer on screen.
    teardown();
  }

  // Still listened for, because Escape and the backdrop close the dialog
  // natively without going through close() above.
  dialog.addEventListener('close', teardown);
  dialog.addEventListener('cancel', teardown);

  // Clicking the backdrop closes. The dialog fills the viewport, so the test
  // is whether the click landed outside the panel rather than on the dialog.
  dialog.addEventListener('click', function (e) {
    if (e.target === dialog) close();
  });

  /* --- input ------------------------------------------------------------ */

  input.addEventListener('input', function () { render(input.value); });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Home') { e.preventDefault(); setActive(0); }
    else if (e.key === 'End') { e.preventDefault(); setActive(results.length - 1); }
    else if (e.key === 'Enter') { e.preventDefault(); activate(active, e); }
  });

  list.addEventListener('click', function (e) {
    var item = e.target.closest('.palette__item');
    if (!item) return;
    activate(Number(item.dataset.index), e);
  });

  // Pointer highlight without depending on hover for anything functional.
  list.addEventListener('mousemove', function (e) {
    var item = e.target.closest('.palette__item');
    if (item) setActive(Number(item.dataset.index));
  });

  Array.prototype.forEach.call(
    document.querySelectorAll('[data-palette-open]'),
    function (button) { button.addEventListener('click', open); }
  );
  Array.prototype.forEach.call(
    document.querySelectorAll('[data-palette-close]'),
    function (button) { button.addEventListener('click', close); }
  );

  /* --- invocation ------------------------------------------------------- */

  function isTyping(target) {
    if (!target) return false;
    if (target.isContentEditable) return true;
    var tag = target.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'k' || e.key === 'K') {
      if (e.metaKey || e.ctrlKey) {
        e.preventDefault();
        if (dialog.open) close(); else open();
      }
      return;
    }

    // Slash is only a shortcut where a slash is not a character someone is
    // trying to type. Anywhere editable, it is just a slash.
    if (e.key === '/' && !e.metaKey && !e.ctrlKey && !e.altKey) {
      if (dialog.open || isTyping(e.target)) return;
      e.preventDefault();
      open();
    }
  });

  // The hint in the trigger should name the key this visitor actually has.
  if (/Mac|iPhone|iPad/.test(navigator.platform || '')) {
    Array.prototype.forEach.call(
      document.querySelectorAll('[data-palette-mod]'),
      function (el) { el.textContent = '⌘'; }
    );
  }
})();
