/* Pointer hit test for every interactive control on a page.

   Why this exists
   ---------------
   The Experience / Engineering switch and the command palette trigger were
   both unclickable with a mouse for several phases while 200 Django tests
   passed. Nothing was wrong with the markup: `.bar { pointer-events: none }`
   made the header transparent to the pointer and neither control opted back
   in, so real clicks fell through to whatever was underneath.

   No DOM-level test can catch that, because the DOM is correct. `pointer-events`
   blocks hit-testing only — focus, keyboard activation and `element.click()`
   all still reach the element and all still work. Every automated check drove
   those paths, so every automated check passed.

   The assertion that catches it is this one: for each interactive control,
   the element the browser would actually deliver a click to at that control's
   own centre must be the control itself or something inside it.

   Usage
   -----
   Paste into the DevTools console on any page of the site, or run it through
   a browser automation tool. Returns a report object and logs a table.

       hitTest()                       // the default control set
       hitTest('.my-thing, button')    // a specific selector

   Exit shape: { pass, fail, skipped, results[] }. `fail` is non-zero if any
   control cannot receive a pointer event at its own centre.
*/
(function (global) {
  'use strict';

  // Everything a visitor is expected to be able to click. Kept as one list so
  // a control added to the bar, the rail or the Build Space is covered by
  // being interactive rather than by being remembered here.
  var DEFAULT_SELECTOR = [
    'a[href]',
    'button',
    'input:not([type="hidden"])',
    'textarea',
    'select',
    '[role="button"]',
    '[tabindex]:not([tabindex="-1"])'
  ].join(',');

  function describe(el) {
    if (!el) return 'null';
    var cls = el.className;
    if (cls && cls.baseVal !== undefined) cls = cls.baseVal;   // SVG elements
    cls = String(cls || '').trim().split(/\s+/).slice(0, 2).join('.');
    return el.tagName.toLowerCase() + (cls ? '.' + cls : '');
  }

  function label(el) {
    var text = (el.getAttribute('aria-label') || el.textContent || '').trim();
    return text.replace(/\s+/g, ' ').slice(0, 40) || describe(el);
  }

  /* A control is only testable if it is on screen and actually rendered.
     Something scrolled out of view or deliberately hidden is not a failure,
     it is simply not a hit target right now — those are reported separately
     so a green run cannot be produced by hiding everything. */
  function testable(el, box) {
    var cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') return 'hidden';
    if (!box.width || !box.height) return 'zero-size';
    var cx = box.left + box.width / 2;
    var cy = box.top + box.height / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) return 'offscreen';
    return null;
  }

  function hitTest(selector) {
    var controls = Array.prototype.slice.call(
      document.querySelectorAll(selector || DEFAULT_SELECTOR)
    );

    var results = [];
    var pass = 0, fail = 0, skipped = 0;

    controls.forEach(function (el) {
      var box = el.getBoundingClientRect();
      var skip = testable(el, box);

      if (skip) {
        skipped++;
        results.push({ control: label(el), status: 'skip', reason: skip });
        return;
      }

      var cx = box.left + box.width / 2;
      var cy = box.top + box.height / 2;
      var hit = document.elementFromPoint(cx, cy);
      // A descendant counts: clicking the label inside a link is still a click
      // on the link, which is what the browser will dispatch.
      var reaches = !!hit && (hit === el || el.contains(hit));

      if (reaches) {
        pass++;
        results.push({ control: label(el), status: 'pass' });
      } else {
        fail++;
        results.push({
          control: label(el),
          status: 'FAIL',
          at: Math.round(cx) + ',' + Math.round(cy),
          pointerEvents: getComputedStyle(el).pointerEvents,
          blockedBy: describe(hit)
        });
      }
    });

    var report = { pass: pass, fail: fail, skipped: skipped, results: results };

    if (global.console && console.table) {
      console.table(results.filter(function (r) { return r.status !== 'pass'; }));
      console.log('hitTest: ' + pass + ' pass, ' + fail + ' FAIL, ' + skipped + ' skipped');
    }
    return report;
  }

  global.hitTest = hitTest;
})(window);
