import logging

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse

from . import content, layout
from .mail import send_contact_message

logger = logging.getLogger(__name__)

CONTACT_ANCHOR = "/#contact"

# The two lenses over the same content. One global viewing preference, not two
# sites and not two URL trees.
MODES = ("experience", "engineering")
DEFAULT_MODE = "experience"

# The landing registry. One entry today; a replacement landing adds a second
# and settings.LANDING selects it, so the home page never has to fork.
#
# "intro" says whether that landing shows the loading layer. The preloader
# belongs to the page, not to any one landing; the typing sequence that follows
# it belongs to the hero, and intro.js only runs that half where there is a
# hero to run it on. A landing can therefore opt out of the loading layer
# without that meaning anything about what comes after it.
#
# "work" is the template for the work section below the landing. Both
# landings have one; they present it differently. The legacy hero introduces
# the pinned horizontal deck. The Build Space is the discovery surface, so the
# section under it is a calm, readable index instead of a second interactive
# one — the same projects, the same media, browsable rather than driven.
LANDINGS = {
    "legacy": {
        "template": "pages/partials/hero.html",
        "intro": True,
        "work": "pages/partials/work.html",
    },
    "build": {
        "template": "pages/partials/build_space.html",
        "intro": True,
        "work": "pages/partials/work_index.html",
    },
}
# The fallback for a missing or unrecognised setting. Kept in step with the
# default in settings, so a typo in JOE_LANDING serves the same page an unset
# one does rather than quietly reverting to the old landing.
DEFAULT_LANDING = "build"


def _landing():
    """Resolve the configured landing, falling back rather than failing."""
    return LANDINGS.get(getattr(settings, "LANDING", DEFAULT_LANDING),
                        LANDINGS[DEFAULT_LANDING])


def _work_template():
    """The work section this landing uses, with a safe fallback."""
    return _landing().get("work", LANDINGS[DEFAULT_LANDING]["work"])


def _landing_context():
    """What the home page needs to render whichever landing is configured.

    The Build Space's node and link data is only computed when it is the
    landing being rendered, so the legacy page pays nothing for it.
    """
    landing = _landing()
    context = {
        "landing_template": landing["template"],
        "show_intro": landing["intro"],
        "work_template": _work_template(),
    }

    if landing is LANDINGS.get("build"):
        nodes = _build_space_nodes()
        context["build_nodes"] = nodes
        context["build_links"] = _build_space_links(nodes)
        context["build_core"] = layout.CORE

    return context


SITE_TITLE = "Joseph Edward, Full-stack web & mobile engineer"
SITE_DESCRIPTION = (
    "Joseph Edward is a full-stack web and mobile engineer building secure, "
    "scalable products for startups and businesses with Django, Next.js and "
    "React Native."
)
SITE_SHARE_TEXT = (
    "Secure, scalable products for startups and businesses. Django, Next.js, "
    "React Native and Expo."
)
# Used when a page has no image of its own, and as the fallback if a project's
# own media is somehow not in the static manifest.
FALLBACK_SHARE_IMAGE = "images/marketbrainers"

MAX_DESCRIPTION = 155


def _resolve_mode(request):
    """Server-side half of the mode resolution.

    The server can only see the URL; a stored preference lives in the browser
    and is applied by the pre-paint script in base.html. So the order here is
    explicit parameter, then default, and the script fills in the middle step.

    Anything unrecognised falls back to the default rather than becoming a
    third state, so ?mode=nonsense renders a normal page.
    """
    requested = request.GET.get("mode")
    return requested if requested in MODES else DEFAULT_MODE


def _mode_urls(request):
    """One URL per mode, same page.

    Keeps the path and any unrelated query parameters, and leaves the
    parameter off entirely for the default so ordinary URLs stay clean.
    Fragments never reach the server, so the script preserves those.
    """
    urls = {}
    for mode in MODES:
        params = request.GET.copy()
        if mode == DEFAULT_MODE:
            params.pop("mode", None)
        else:
            params["mode"] = mode
        query = params.urlencode()
        urls[mode] = f"{request.path}?{query}" if query else request.path
    return urls


# Words people search by that no project actually spells out. Someone typing
# "mobile" means the Expo apps, but the data says "Expo" and "React Native"
# and never "mobile". Derived from the technologies each project genuinely
# lists rather than tagged by hand, so it cannot drift from the data.
TECH_KEYWORDS = (
    (("expo", "react native"), "mobile app ios android"),
    # Next.js only. "react" would also match "React Native", and TypeScript is
    # written on both sides of this stack, so neither separates web from mobile.
    (("next.js",), "web frontend"),
    (("django", "drf", "python"), "backend api server"),
    (("postgresql", "sqlite", "redis"), "database data"),
    (("paystack", "solana"), "payments"),
)


def _derived_keywords(technologies):
    """Search words implied by a project's stack, never invented for it."""
    lowered = " ".join(technologies).lower()
    words = []
    for triggers, keywords in TECH_KEYWORDS:
        if any(trigger in lowered for trigger in triggers):
            words.append(keywords)
    return words


def _search_terms(*parts):
    """One lowercase haystack per command, built once on the server.

    Doing it here keeps the client to a substring test and keeps the payload
    to a single string per command rather than nested arrays.
    """
    words = []
    for part in parts:
        if not part:
            continue
        if isinstance(part, str):
            words.append(part)
        else:
            words.extend(str(item) for item in part if item)
    return " ".join(words).lower()


def _palette_commands():
    """Everything the command palette can do, derived from the content module.

    Projects come from PROJECTS, sections from NAV and links from SOCIALS, so
    adding a project adds a command and nothing here needs updating. Paths and
    fragments are kept apart because the mode parameter goes between them, and
    the client is what knows the current mode.
    """
    commands = []

    for project in content.PROJECTS:
        engineering = project.get("engineering") or {}
        technologies = list(project.get("tech") or []) + [
            item.get("name", "") for item in engineering.get("stack", [])
        ]
        commands.append({
            "id": f"project:{project['slug']}",
            "group": "Projects",
            "label": project["name"],
            "hint": project["kind"],
            "path": reverse("project_detail", args=[project["slug"]]),
            "terms": _search_terms(
                project["name"],
                project["kind"],
                project.get("role"),
                technologies,
                _derived_keywords(technologies),
                "project work",
            ),
        })

    for item in content.NAV:
        commands.append({
            "id": f"section:{item['slug']}",
            "group": "Sections",
            "label": item["label"],
            "hint": "Section",
            "path": "/",
            "fragment": item["slug"],
            "terms": _search_terms(item["label"], "section jump"),
        })

    for mode in MODES:
        commands.append({
            "id": f"mode:{mode}",
            "group": "View",
            "label": f"Switch to {mode.capitalize()}",
            "hint": "Experience shows what was built, Engineering shows how"
                    if mode == "engineering" else "Back to the product view",
            "action": "mode",
            "value": mode,
            "terms": _search_terms(mode, "mode lens switch view toggle"),
        })

    # The CV, as two commands rather than one: viewing it and saving it are
    # different intents, and the palette is where someone types "resume"
    # rather than scrolling to find the band.
    cv_url = static(content.CV["file"])
    for verb, ident in (("View", "view"), ("Download", "download")):
        commands.append({
            "id": f"cv:{ident}",
            "group": "Elsewhere",
            "label": f"{verb} CV",
            "hint": " · ".join(content.CV["meta"]),
            "url": cv_url,
            # Not "external": the file is served from this origin. Viewing it
            # wants a new tab because it is a PDF, and saving it wants the
            # readable name; those are different flags, not the same one.
            "blank": ident == "view",
            "download": content.CV["download_as"] if ident == "download" else None,
            # Deliberately not the role: it reads "Full-stack web & mobile
            # engineer", and folding that in would make the CV answer a search
            # for "mobile" or "web" alongside the projects those words mean.
            "terms": _search_terms(
                verb, "cv resume curriculum vitae pdf", content.PROFILE["name"],
            ),
        })

    for social in content.SOCIALS:
        commands.append({
            "id": f"social:{social['label'].lower()}",
            "group": "Elsewhere",
            "label": social["label"],
            "hint": social["url"].replace("https://", ""),
            "url": social["url"],
            "external": True,
            "terms": _search_terms(social["label"], social["url"]),
        })

    commands.append({
        "id": "contact:email",
        "group": "Elsewhere",
        "label": "Email Joseph",
        "hint": content.PROFILE["email"],
        "url": f"mailto:{content.PROFILE['email']}",
        "external": True,
        "terms": _search_terms("email mail contact", content.PROFILE["email"]),
    })

    return commands


# The order a stack is read in: what the user touches, then what serves it,
# then what it keeps, then what it talks to, then what it runs on. Anything
# with an unrecognised layer still renders, at the end, rather than vanishing.
STACK_LAYER_ORDER = ("client", "backend", "data", "integration", "infra")


def _stack_groups(stack):
    """A project's verified stack, grouped by layer and kept in reading order.

    Engineering Mode shows this in place of the product chips. Grouping is
    what makes it read as a stack rather than a bag of names, and it is done
    here rather than in the template because ordering by a fixed vocabulary
    is logic, not markup.
    """
    buckets = {}
    for item in stack:
        buckets.setdefault(item.get("layer") or "other", []).append(item["name"])

    ordered = [layer for layer in STACK_LAYER_ORDER if layer in buckets]
    ordered += sorted(layer for layer in buckets if layer not in STACK_LAYER_ORDER)

    return [{"layer": layer, "items": buckets[layer]} for layer in ordered]


def _build_space_nodes():
    """One node per project: facts from PROJECTS, position from layout.

    The two are joined here and nowhere else. A project with no coordinate is
    still rendered, spaced around a ring, because an unplaced project is a
    layout oversight and dropping it would hide the mistake.
    """
    import math

    unplaced = [p for p in content.PROJECTS if p["slug"] not in layout.POSITIONS]
    nodes = []

    for index, project in enumerate(content.PROJECTS):
        placement = layout.POSITIONS.get(project["slug"])
        if placement is None:
            spare = unplaced.index(project)
            angle = (2 * math.pi * spare) / max(len(unplaced), 1)
            placement = {
                "x": round(layout.CORE["x"] + layout.FALLBACK_RING["radius"] * math.cos(angle)),
                "y": round(layout.CORE["y"] + layout.FALLBACK_RING["radius"] * math.sin(angle)),
                "tier": layout.FALLBACK_RING["tier"],
            }

        engineering = project.get("engineering") or {}
        architecture = engineering.get("architecture") or {}

        nodes.append({
            "slug": project["slug"],
            "name": project["name"],
            "kind": project["kind"],
            "status": project["status"],
            "year": project["year"],
            "url": reverse("project_detail", args=[project["slug"]]),
            "x": placement["x"],
            "y": placement["y"],
            "tier": placement["tier"],
            "index": index,
            "image": project.get("image"),
            "video": project.get("video"),
            "media_alt": project.get("media_alt", ""),
            "tech": (project.get("tech") or [])[:4],
            # Engineering Mode only. Absent where it was never verified, which
            # is how MarketBrainers stays a project with no invented internals.
            "stack": [item["name"] for item in engineering.get("stack", [])][:5],
            # The same record, grouped, for the preview panel.
            "stack_groups": _stack_groups(engineering.get("stack", [])),
            "satellites": [
                {"label": node["label"], "kind": node["kind"]}
                for node in architecture.get("nodes", [])
                if node.get("kind") in ("service", "datastore", "external")
            ][:4],
            "has_engineering": bool(engineering),
        })

    return nodes


def _clear_core(core, toward):
    """Move a core endpoint out to the edge of the identity block.

    Solves for where the line from the core to `toward` crosses the clearance
    ellipse, so every connection stops at the same boundary regardless of the
    direction it leaves in. Degenerate input keeps the centre rather than
    dividing by zero, which can only happen if a node is placed on the core.
    """
    dx = toward["x"] - core["x"]
    dy = toward["y"] - core["y"]
    rx = layout.CORE_CLEARANCE["x"]
    ry = layout.CORE_CLEARANCE["y"]

    scale = ((dx / rx) ** 2 + (dy / ry) ** 2) ** 0.5
    if not scale:
        return core

    return {"x": core["x"] + dx / scale, "y": core["y"] + dy / scale}


def _build_space_links(nodes):
    """Resolve the composition's connections to drawable coordinates."""
    points = {node["slug"]: node for node in nodes}
    links = []

    for source, target in layout.CONNECTIONS:
        a = layout.CORE if source == "core" else points.get(source)
        b = layout.CORE if target == "core" else points.get(target)
        if not a or not b:
            continue

        # Only the core end is pulled back; a node end terminates on the node.
        if source == "core":
            a = _clear_core(a, b)
        if target == "core":
            b = _clear_core(b, a)
        # A connection carries the weight of the heavier end. The three lines
        # out of the core to the current products are the spine of the
        # composition and are drawn as such; the rest are secondary structure.
        ends = [
            "primary" if end == "core" else points.get(end, {}).get("tier")
            for end in (source, target)
        ]
        links.append({
            # Rounded because clearing the core produces irrationals and the
            # markup should not carry seventeen digits of them.
            "x1": round(a["x"], 2), "y1": round(a["y"], 2),
            "x2": round(b["x"], 2), "y2": round(b["y"], 2),
            "source": source, "target": target,
            "tier": "primary" if "primary" in ends else "secondary",
        })

    return links


def _find_project(slug):
    """Linear scan rather than a slug index.

    Eight projects, and building a second mapping would mean project data
    living in two places, which is the thing content.py exists to prevent.
    """
    for project in content.PROJECTS:
        if project.get("slug") == slug:
            return project
    return None


def _trim(text, limit=MAX_DESCRIPTION):
    """Shorten to a word boundary. Meta descriptions get cut off anyway."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "..."


def _share_image_url(request, project=None):
    """Absolute URL for og:image, which relative paths are not valid for.

    Branches over the media keys the same way the template does: under
    manifest static storage an unknown path raises rather than degrading, so
    every lookup needs a way to fall back.
    """
    candidates = []
    if project:
        if project.get("image"):
            candidates.append(project["image"])
        elif project.get("video"):
            candidates.append(project["video"])
    candidates.append(FALLBACK_SHARE_IMAGE)

    for base in candidates:
        try:
            return request.build_absolute_uri(static(base + ".jpg"))
        except ValueError:
            continue
    return ""


def _page_context(request, project=None, **extra):
    """Shared context plus the meta block, so no page rebuilds the head.

    A project supplies its own title, description and share image; without one
    these fall back to the site defaults.
    """
    mode = _resolve_mode(request)

    if project:
        title = f"{project['name']}, {project['kind']} | Joseph Edward"
        description = _trim(project.get("experience", {}).get("summary", SITE_DESCRIPTION))
    else:
        title = SITE_TITLE
        description = SITE_DESCRIPTION

    context = {
        "profile": content.PROFILE,
        "nav_items": content.NAV,
        "socials": content.SOCIALS,
        "cv": content.CV,
        "about": content.ABOUT,
        "about_close": content.ABOUT_CLOSE,
        "help_with": content.HELP_WITH,
        "stack": content.STACK,
        "projects": content.PROJECTS,
        # The selected project, when there is one. The detail template reads
        # this; the home page leaves it None and never looks.
        "project": project,
        # The preloader hands off to the hero's typing intro, so it only
        # belongs on a page that has one. Opt in rather than out: any future
        # page that isn't the home page should not have to remember to
        # suppress a full-viewport overlay.
        "show_intro": False,
        # Repopulates the contact form after a failed submission. Empty on a
        # GET, which is what an untouched form wants.
        "submitted": {},
        "mode": mode,
        "mode_urls": _mode_urls(request),
        "palette_commands": _palette_commands(),
        # Appended to internal links so an explicitly chosen mode survives a
        # navigation with JavaScript off. With JavaScript the stored
        # preference does that job, and this stays empty on the default.
        "mode_query": f"?mode={mode}" if mode != DEFAULT_MODE else "",
        "meta_title": title,
        "meta_description": description,
        "meta_share_text": description if project else SITE_SHARE_TEXT,
        "meta_image": _share_image_url(request, project),
        "meta_url": request.build_absolute_uri(request.path),
        "meta_type": "article" if project else "website",
    }
    context.update(extra)
    return context


def home(request):
    """The whole site. GET renders the page; POST is the contact form."""
    if request.method != "POST":
        return render(request, "pages/home.html", _page_context(request, **_landing_context()))

    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    subject = request.POST.get("subject", "").strip()
    message = request.POST.get("message", "").strip()

    # Whatever happens from here, the visitor gets their words back. A failed
    # send that also wipes the message costs them the enquiry twice.
    submitted = {"name": name, "email": email, "subject": subject, "message": message}

    def reject(reason):
        messages.error(request, reason)
        return render(
            request,
            "pages/home.html",
            _page_context(request, submitted=submitted, **_landing_context()),
        )

    if not name or not email or not message:
        return reject("Please fill in your name, email and message.")

    # Django's own validator rather than a hand-rolled pattern: getting email
    # syntax right is famously not a one-line regex, and a bad address is worse
    # than useless here. It either bounces at Resend, where the visitor is told
    # something generic went wrong, or it is accepted and the reply-to is dead,
    # so the enquiry arrives with no way to answer it.
    try:
        validate_email(email)
    except ValidationError:
        # The address is not echoed back: the field still holds it, and
        # reflecting arbitrary input into the page buys nothing.
        return reject("That email address does not look right. Check it and send again.")

    try:
        send_contact_message(name, email, subject, message)
    except Exception:  # noqa: BLE001, surface anything as a form error
        # Logged rather than printed so the traceback survives into whatever
        # collects logs, and never shown to the visitor.
        logger.exception("Contact form: failed to send via Resend")
        messages.error(
            request,
            "Something went wrong sending that. Please email me directly at "
            f"{settings.CONTACT_EMAIL}.",
        )
        return render(
            request,
            "pages/home.html",
            _page_context(request, submitted=submitted, **_landing_context()),
        )

    messages.success(
        request,
        f"Thanks {name}, message sent. I'll get back to you within 24 hours.",
    )
    # Redirect after POST so a refresh doesn't resubmit, and land on the form.
    return redirect(CONTACT_ANCHOR)


def project_detail(request, slug):
    """One project, one URL, straight out of PROJECTS.

    Deliberately not two views or two templates: Experience and Engineering
    are lenses over the same resource, and splitting them into separate pages
    now would have to be undone when the mode switch lands.
    """
    project = _find_project(slug)
    if project is None:
        raise Http404(f"No project with the slug {slug!r}")

    return render(request, "pages/project.html", _page_context(request, project=project))
