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

**Use Python 3.12.** Django 4.2 supports 3.8 through 3.12, and this project is
pinned to 4.2. Newer interpreters are not merely unsupported in theory: on
Python 3.14 the Django test client raises `AttributeError` from
`Context.__copy__` as soon as the test runner instruments template rendering,
which takes down every request-based test with a misleading traceback.

```bash
py -3.12 -m venv .venv        # or your 3.12 interpreter of choice
.venv/Scripts/python -m pip install -r requirements.txt   # .venv/bin on macOS and Linux
cp .env.example .env          # then add your RESEND_API_KEY
DJANGO_DEBUG=1 .venv/Scripts/python manage.py runserver
.venv/Scripts/python manage.py test pages                 # regression suite
```

One thing the interpreter version decides for you: `{% include ... only %}`
also copies the Context and so fails on 3.14. The templates avoid `only` and
pass explicit `with` arguments instead, because production runs Python 3.13 and
that combination has not been verified there. Keep it that way unless you test
it on the deployment runtime.

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

Append a dict to `PROJECTS` in `pages/content.py`. The deck picks it up, and the
panel count, counter and progress segments are all derived.

Media is optional, and the panel takes whichever of these it finds first:

- `"video": "video/<slug>-demo"` for the mobile apps. Needs `<slug>-demo.mp4`
  plus a `<slug>-demo.jpg` poster in `static/video/`. Renders in a phone frame,
  and only the panel you're looking at plays.
- `"image": "images/<slug>"` for everything else. Needs `<slug>.webp` and
  `<slug>.jpg` in `static/images/`.
- Neither, which renders a typographic plate so a project can ship before its
  screenshot does.

`links` and `repos` are both lists and both may be empty: a mobile app has no
site to visit, and a private repo has no source worth linking to a 404.

Copy is split into two lenses over the same shared facts:

- `experience` holds `summary` and `features`, the product-facing story. This is
  what the work panel renders today.
- `engineering` holds how it is actually built, and every key in it is optional:
  `overview`, `stack`, `architecture`, `api`, `data`, `auth`, `integrations`,
  `capabilities`, `testing`, `infra`, `decisions`. `architecture` is a graph of
  `nodes` and `edges` so it can be drawn generically rather than per project.

Engineering values come from each project's own repository: dependency
manifests, app layout, deploy descriptors, or the running deployment. If it is
not verified, the key is left out. The top-level `tech` list is separate on
purpose: it is the product-facing chip row, and it is allowed to differ from
`engineering.stack`, which is the verified implementation.

Images are committed pre-optimized (resized to display size, webp + jpg pairs,
lowercase names because Vercel's filesystem is case-sensitive).

### Adding a demo video

Screen recordings go through ffmpeg first. Audio is stripped since the clips
autoplay muted, and `+faststart` puts the index at the front so playback can
begin before the whole file arrives:

```bash
ffmpeg -i raw.mp4 -an -c:v libx264 -profile:v main -pix_fmt yuv420p \
  -crf 30 -preset veryslow -movflags +faststart static/video/<slug>-demo.mp4
ffmpeg -ss 5 -i static/video/<slug>-demo.mp4 -frames:v 1 -q:v 5 \
  static/video/<slug>-demo.jpg
```

That took the two current demos from 8.1 MB to 1.2 MB with the UI text still
legible. Check the poster frame actually shows something worth looking at.

## Performance baseline

Recorded before any Build Space work, so a later claim that performance is fine
has something to be measured against. Source sizes, uncompressed.

| | Home | Case study |
|---|---|---|
| Initial HTML | 57.7 KB | 22.8 KB |
| Stylesheets | 7 (52.3 KB total) | same |
| Scripts | 6 (32.0 KB total) | same |
| Third-party requests | 3 (Google Fonts) | same |

Media on disk: 0.83 MB of images, 1.58 MB of video. The home page loads no
image eagerly, lazy-loads five, and holds three `<video>` elements at
`preload="metadata"`, so only posters arrive until a clip is played.

Eight projects, eight deck panels, and sixteen lens blocks because both lenses
ship in the HTML and CSS hides one.

Frame systems: one shared scroll scheduler in `motion.js` serving `nav.js` and
`deck.js`; `intro.js` runs its own progress loop with its own hard stop;
`mode.js` uses a one-shot frame to correct scroll after a lens swap.

The preloader runs on the home page only, once per session, with a 700 ms floor
and a 2.5 s ceiling.

## The contact contract

The contact form is the only part of this site that does real work, and it is
the part a redesign is most likely to break silently: a renamed field costs an
enquiry and raises no error anywhere. Any future contact UI has to keep all of
this, and `pages/tests.py` fails if it does not.

| | Contract |
|---|---|
| Endpoint | `POST /` (the home view). Not a separate URL. |
| Action | `{% url 'home' %}#contact`, so the reply lands back at the form |
| Fields | `name`, `email`, `subject`, `message` (exactly these names) |
| Required | `name`, `email`, `message`. `subject` is optional |
| CSRF | `{% csrf_token %}` required; enforced by middleware, tested at 403 |
| Whitespace | Values are stripped; whitespace-only counts as missing |
| Success | 302 to `/#contact` and a success message naming the sender |
| Validation failure | 200, re-rendered in place, error message, nothing sent |
| Send failure | 200, re-rendered, error message offering the direct address |
| GET | Never sends mail |

Nothing is hidden in the form and there are no other assumptions: the view
reads those four `request.POST` keys and nothing else.

The mail boundary is `pages/mail.py`. `send_contact_message(name, email,
subject, message)` raises on any failure and the view decides what the visitor
sees. That split exists so the contact path can be tested without sending real
mail, and so a future UI keeps talking to the same proven backend.

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

`vercel.json` routes `/static/*` to Vercel's static layer rather than through
the Python function. Everything under `/static/` is content-hashed, so it is
served `immutable` with a one year cache. Without that route the video would
stream out of the lambda on every view, which costs a cold start, forfeits CDN
caching and pushes against the function response size limit.

## Known issues

- Mail from `onboarding@resend.dev` can land in spam. Verify a custom domain in
  Resend to fix it properly.
- `SECRET_KEY` and `ALLOWED_HOSTS` are still hardcoded in `joe_webs/settings.py`.
  Both should move to environment variables. Set them in Vercel first, or the
  deploy will break.

## Contact

josephedward201@gmail.com · [github.com/zazajo](https://github.com/zazajo) ·
[linkedin](https://www.linkedin.com/in/joseph-edward-94b7a3322)
