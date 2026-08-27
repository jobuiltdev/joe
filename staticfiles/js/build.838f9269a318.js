/* Build Space.

   Owns one thing: which node is active, and what that implies for the wires,
   the detail panel and the video. Everything else is borrowed:

     JE.motion  reduced-motion preference and the shared frame scheduler
     JE.mode    the Experience / Engineering lens
     CSS        every transition, the ambient drift, both layouts

   No state of its own beyond the active node, and no navigation of its own:
   the nodes are ordinary anchors to ordinary routes, so the map works with
   this file absent entirely. */
(function () {
  'use strict';

  var root = document.querySelector('[data-build]');
  if (!root) return;

  var motion = (window.JE || {}).motion;
  var nodes = Array.prototype.slice.call(root.querySelectorAll('[data-node]'));
  var wires = Array.prototype.slice.call(root.querySelectorAll('[data-wire]'));
  if (!nodes.length) return;

  var field = root.querySelector('[data-build-field]');
  var nodeLayer = root.querySelector('[data-build-nodes]');
  var active = null;

  // Touch gets a different contract: the first tap opens a project, the
  // second follows it. On a pointer device hover does the opening, so the
  // first click should just go.
  var canHover = window.matchMedia('(hover: hover)').matches;
  var reduced = function () { return motion ? motion.reduced() : false; };

  /* --- active state ----------------------------------------------------- */

  function video(node) {
    return node.querySelector('[data-build-video]');
  }

  function stop(node) {
    var clip = video(node);
    if (!clip) return;
    if (!clip.paused) clip.pause();
    // Rewound, so reopening a project starts the demo from the beginning
    // rather than resuming halfway through a gesture nobody saw.
    try { clip.currentTime = 0; } catch (e) {}
    node.removeAttribute('data-clip');
  }

  function start(node) {
    var clip = video(node);
    if (!clip || reduced()) return;

    // Autoplay is only permitted for muted inline video, and both are already
    // set in the markup. Re-asserting them here means a clip still plays if
    // something else ever unmutes it, which is the difference between the
    // demo running on a phone and silently not.
    clip.muted = true;
    clip.playsInline = true;

    // Nothing is loaded until a project is actually opened, and a refusal is
    // survivable: the poster is already the right frame. The attribute lets
    // CSS show the still is deliberate rather than broken.
    node.setAttribute('data-clip', 'loading');
    var started = clip.play();
    if (!started || !started.then) return;

    started.then(function () {
      node.setAttribute('data-clip', 'playing');
    }).catch(function () {
      // Blocked by policy, or the node closed before the clip was ready.
      node.setAttribute('data-clip', 'blocked');
    });
  }

  /* The usable stage. Above 56rem the node layer stops short of the floating
     rail, so it — not the section — is what a panel has to stay inside. */
  function stageBox() {
    var box = (nodeLayer || root).getBoundingClientRect();
    var pad = 10;
    return {
      left: box.left + pad, right: box.right - pad,
      top: box.top + pad, bottom: box.bottom - pad
    };
  }

  /* Where the panel opens, in two passes.

     First a flip: open away from whichever edge the node sits near, so the
     panel grows into the empty half of the stage rather than across the
     composition. Then a clamp, because a flip is only a guess that there is
     room in that direction — whatever still hangs outside the stage is
     corrected in pixels. A node in a corner needs both, which is precisely
     the case the previous two-flag version could not express.

     Positions are computed from the panel's untransformed layout box rather
     than a measured rect, so a correction still in flight from the last time
     this panel opened cannot feed back into the next measurement. */
  function placePanel(node) {
    var panel = node.querySelector('[data-detail]');
    if (!panel) return;

    // Static panels are in the flow (the mobile layout); there is nothing to
    // position and a transform would only fight the stacking.
    if (getComputedStyle(panel).position === 'static') {
      delete node.dataset.edge;
      panel.style.removeProperty('--shift-x');
      panel.style.removeProperty('--shift-y');
      return;
    }

    var stage = stageBox();
    var box = node.getBoundingClientRect();
    var w = panel.offsetWidth;
    var h = panel.offsetHeight;
    var gap = 10;

    var flags = [];
    if ((box.left + box.right) / 2 > stage.left + (stage.right - stage.left) * 0.6) flags.push('right');
    if (box.bottom > stage.top + (stage.bottom - stage.top) * 0.58) flags.push('bottom');
    node.dataset.edge = flags.join(' ');

    // Where the flip alone would put it.
    var left = flags.indexOf('right') > -1 ? box.right - w : box.left;
    var top = flags.indexOf('bottom') > -1 ? box.top - gap - h : box.bottom + gap;

    // Where it is actually allowed to be. Clamping low-then-high means a panel
    // taller than the stage pins to the top edge instead of the bottom.
    var clampedLeft = Math.min(Math.max(left, stage.left), Math.max(stage.right - w, stage.left));
    var clampedTop = Math.min(Math.max(top, stage.top), Math.max(stage.bottom - h, stage.top));

    panel.style.setProperty('--shift-x', Math.round(clampedLeft - left) + 'px');
    panel.style.setProperty('--shift-y', Math.round(clampedTop - top) + 'px');
  }

  function lightWires(slug) {
    wires.forEach(function (wire) {
      var touches = wire.dataset.source === slug || wire.dataset.target === slug;
      wire.classList.toggle('is-lit', !!slug && touches);
    });
  }

  function setActive(node) {
    if (active === node) return;

    if (active) {
      active.classList.remove('is-active');
      stop(active);
    }

    active = node;
    root.classList.toggle('has-active', !!node);
    lightWires(node ? node.dataset.node : null);

    if (!node) return;

    node.classList.add('is-active');
    placePanel(node);
    start(node);
  }

  /* --- mode-aware links ------------------------------------------------- */

  /* The server can only stamp the mode onto these hrefs when it was in the
     URL. When the lens came from the stored preference instead, the server
     rendered plain paths and the links would drop the reader back into
     Experience on arrival. JE.mode owns the rule for what a URL looks like in
     the current mode, so the hrefs are rewritten through it rather than by
     appending a parameter here. */
  function syncLinks() {
    var mode = (window.JE || {}).mode;
    if (!mode || !mode.urlFor) return;
    nodes.forEach(function (node) {
      var link = node.querySelector('[data-node-link]');
      if (link && link.dataset.path) link.href = mode.urlFor(link.dataset.path);
    });
  }

  /* --- wiring ----------------------------------------------------------- */

  nodes.forEach(function (node) {
    var link = node.querySelector('[data-node-link]');
    if (!link) return;

    if (canHover) {
      node.addEventListener('mouseenter', function () { setActive(node); });
      node.addEventListener('mouseleave', function () {
        if (active === node && !node.contains(document.activeElement)) setActive(null);
      });
    }

    // Focus has to reach the same state hover does, or the map is only half
    // usable from a keyboard.
    link.addEventListener('focus', function () { setActive(node); });
    link.addEventListener('blur', function () {
      if (active === node) setActive(null);
    });

    link.addEventListener('click', function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;

      // Touch: open the project in place first. Someone who wants the case
      // study taps the same node again.
      if (!canHover && active !== node) {
        e.preventDefault();
        setActive(node);
        return;
      }

      handoff(node);
    });
  });

  // Clicking the empty field clears the selection on touch, which is the only
  // way back out of an opened node.
  root.addEventListener('click', function (e) {
    if (!canHover && active && !e.target.closest('[data-node]')) setActive(null);
  });

  /* --- navigation ------------------------------------------------------- */

  /* Cross-document view transitions are declared in CSS and run without any
     help from here. All this does is name the element being carried across,
     so the browser has something to match against the case study's media.
     Unsupported browsers ignore the property and navigate normally. */
  function handoff(node) {
    if (reduced() || !('startViewTransition' in document)) return;
    var media = node.querySelector('.build__media > *');
    if (media) media.style.viewTransitionName = 'project-media';
  }

  /* --- pointer response ------------------------------------------------- */

  /* The field moves a few pixels with the pointer. Not the nodes: moving them
     individually would pull the composition apart, and the arrangement is the
     one thing that was art-directed. */
  if (canHover && !reduced() && field && nodeLayer) {
    var pending = false;
    var px = 0;
    var py = 0;

    window.addEventListener('mousemove', function (e) {
      // Range is deliberately tiny. Felt, not noticed.
      px = ((e.clientX / window.innerWidth) - 0.5) * -14;
      py = ((e.clientY / window.innerHeight) - 0.5) * -10;

      if (pending) return;
      pending = true;
      window.requestAnimationFrame(function () {
        try {
          root.style.setProperty('--px', px.toFixed(2));
          root.style.setProperty('--py', py.toFixed(2));
        } finally {
          pending = false;
        }
      });
    }, { passive: true });
  }

  /* --- lens changes ----------------------------------------------------- */

  /* Switching lens changes what the panel says, and the panel may now sit
     differently. Nothing else moves: it is the same map either way. */
  new MutationObserver(function () {
    syncLinks();
    if (active) placePanel(active);
  }).observe(document.documentElement, {
    attributes: true, attributeFilter: ['data-mode']
  });

  /* A resize changes which side of the stage has room, so a panel left open
     across one has to be re-placed or it can end up clipped. */
  window.addEventListener('resize', function () {
    if (active) placePanel(active);
  }, { passive: true });

  syncLinks();
})();
