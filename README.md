# Joseph Edward, portfolio

A single-page portfolio for a full-stack web and mobile engineer. Django on the
back, hand-authored CSS on the front, no build step.

Live: https://joewebs.vercel.app

## What's here

- **One page.** Hero, about, work, contact. The old `/about/`, `/projects/` and
  `/contact/` URLs 301 to the matching anchor.
- **Preloader into a typing intro.** The preloader tracks real asset loading
  (fonts, hero image, `load`) with a 700 ms floor and a 2.5 s hard ceiling,
  stepping a status line from "Loading portfolio" through to "Ready", then
  wipes up into an IDE card that types itself out. Skippable on any input,
  plays once per session, and reduced-motion goes straight to the finished
  state.
- **Floating rail nav.** A pill fixed to the right edge: avatar, section dots,
  theme toggle. Hover or keyboard focus expands it to labels. Below 56rem it
  becomes a dock at the bottom of the screen, in thumb reach, with labels
  shown outright since touch has no hover to expand them.
- **Pinned project deck.** The work section is `(panels + 1) × 100vh`; scroll
  progress through that range drives a horizontal track. Unpins into a plain
  vertical stack below 900×620 or under reduced motion.
- **Light and dark**, with the theme resolved by a blocking head script so there
  is no flash of the wrong palette.

Everything degrades: with JavaScript off the preloader never shows, the hero is
already in its final state, the deck is a vertical stack, and the nav is a plain
list of anchors.

## Stack

Django 4.2 · Whitenoise · Resend (contact form) · vanilla CSS and JS ·
Schibsted Grotesk / Instrument Serif / JetBrains Mono.

No Tailwind, no bundler, no `package.json`. The design system lives in
`static/css/main.css` as CSS custom properties.

## Local setup

```bash
pip install -r requirements.txt
cp .env.example .env          # then add your RESEND_API_KEY
DJANGO_DEBUG=1 python manage.py runserver
```

`DJANGO_DEBUG=1` matters locally: with it off, Django caches templates and your
edits stay invisible until you restart.

## Layout

```
pages/content.py                  all copy and project data. Edit this, not the templates
pages/views.py                    one view; GET renders the page, POST is the contact form
templates/base.html               head, nav include, footer
pages/templates/pages/partials/   preloader, nav, hero, about, work, contact
static/css/main.css               the whole design system
static/js/                        intro.js, nav.js, deck.js, site.js
```

### Adding a project

Append a dict to `PROJECTS` in `pages/content.py` and drop
`<slug>.webp` + `<slug>.jpg` into `static/images/`. The deck picks it up, and the
panel count, counter and progress segments are all derived.

Images are committed pre-optimized (resized to display size, webp + jpg pairs,
lowercase names because Vercel's filesystem is case-sensitive).

## Deploying

```bash
python manage.py collectstatic --noinput
git commit -am "..." && git push
```

`collectstatic` **must** run before you push. Static files are content-hashed
(`CompressedManifestStaticFilesStorage`) so a deploy can never serve a visitor
stale CSS out of cache. That does mean `staticfiles/` and its
`staticfiles.json` manifest are committed, since Vercel's `@vercel/python`
builder runs no build step of its own. If you change CSS or JS and forget to
re-run it, `{% static %}` will raise for the missing manifest entry.

`RESEND_API_KEY` must be set as an environment variable in the Vercel dashboard.

## Known issues

- Mail from `onboarding@resend.dev` can land in spam. Verify a custom domain in
  Resend to fix it properly.
- `SECRET_KEY` and `ALLOWED_HOSTS` are still hardcoded in `joe_webs/settings.py`.
  Both should move to environment variables. Set them in Vercel first, or the
  deploy will break.

## Contact

josephedward201@gmail.com · [github.com/zazajo](https://github.com/zazajo) ·
[linkedin](https://www.linkedin.com/in/joseph-edward-94b7a3322)
