"""Regression tests for project data and page rendering.

Deliberately narrow. These cover the two things that have actually broken this
codebase before, and the one that would break it next:

  * the page rendering at all under manifest static storage, where a missing
    file raises instead of degrading;
  * project data keeping the shape the template expects;
  * a partially filled project rendering rather than 500ing, which is the whole
    premise of the optional engineering fields.

No database is touched, so these run as SimpleTestCase.

Requests go through RequestFactory and the URL resolver rather than
django.test.Client. On the supported Python 3.12 the Client works fine; this
stays because it also turns Http404 into a real 404 response, which is what the
project routes need to assert on. It additionally keeps the suite runnable on
newer interpreters, where the Client's template instrumentation copies the
template Context and Context.__copy__ raises.
"""

import json
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import Http404
from django.template.loader import get_template
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import Resolver404, resolve, reverse
from django.views.defaults import page_not_found

from . import content, layout, mail, views

_ROOT = Path(__file__).resolve().parent.parent
CSS_DIR = _ROOT / "static" / "css"
JS_DIR = _ROOT / "static" / "js"
TEMPLATES_DIR = _ROOT / "templates"
# The mode and lens rules live in the foundation sheet, which everything
# else is layered on top of.
BASE_CSS = CSS_DIR / "foundation.css"

# Controlled vocabularies. A renderer will switch on these, so a typo here is a
# silently unstyled node rather than an error, which makes it worth asserting.
NODE_KINDS = {"client", "service", "datastore", "external"}
STACK_LAYERS = {"client", "backend", "data", "infra", "integration"}

SHARED_KEYS = ("slug", "name", "kind", "year", "role", "status")

# The Build Space is the default landing now, so the legacy hero and its pinned
# deck are the ones that have to be asked for. Tests about that page select it
# explicitly, the same way Build Space tests used to.
LEGACY = override_settings(LANDING="legacy")

def css_rule(css, selector):
    """The declaration block for `selector`, without its braces.

    A declaration block has no nested braces, so the first closing brace after
    the opening one ends it.
    """
    start = css.index(selector + " {") + len(selector) + 2
    return css[start:css.index("}", start)]


# A stand-in for the renderer's absent-engineering branch.
#
# Every project in PROJECTS now carries a verified record, so this branch has
# no volunteer from the content module. Using a fixture is better anyway: the
# branch should be covered because it exists, not because some project happens
# to be unaudited and would silently stop covering it once audited.
UNVERIFIED = {
    "slug": "unverified-demo",
    "name": "Unverified Demo",
    "kind": "Placeholder project",
    "year": "2020",
    "role": "Solo",
    "status": "archived",
    "tech": ["Django"],
    "media_alt": "",
    "links": [],
    "repos": [],
    "experience": {
        "summary": "A project whose implementation has not been audited.",
        "features": ["Something it does"],
    },
}


def with_unverified():
    """PROJECTS plus one project that has no engineering key."""
    return patch.object(content, "PROJECTS", list(content.PROJECTS) + [UNVERIFIED])


class ProjectSchemaTests(SimpleTestCase):
    """The shape of PROJECTS, independent of how it is rendered."""

    def test_every_project_has_the_shared_identity_keys(self):
        for p in content.PROJECTS:
            for key in SHARED_KEYS:
                with self.subTest(project=p.get("slug"), key=key):
                    self.assertTrue(p.get(key), f"{p.get('slug')} is missing {key}")

    def test_slugs_are_unique(self):
        slugs = [p["slug"] for p in content.PROJECTS]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_media_is_at_most_one_kind_and_always_described(self):
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                self.assertFalse(
                    p.get("image") and p.get("video"),
                    "a panel renders one medium; both means the video silently wins",
                )
                if p.get("image") or p.get("video"):
                    self.assertTrue(p.get("media_alt"), "media without alt text")

    def test_media_files_resolve_in_the_static_manifest(self):
        """The failure this guards is a 500, not a broken image.

        Under CompressedManifestStaticFilesStorage an unknown path raises, so a
        media reference with no collected file takes the whole page down.
        """
        for p in content.PROJECTS:
            paths = []
            if p.get("image"):
                paths += [p["image"] + ".webp", p["image"] + ".jpg"]
            if p.get("video"):
                paths += [p["video"] + ".mp4", p["video"] + ".jpg"]
            for path in paths:
                with self.subTest(project=p["slug"], path=path):
                    try:
                        staticfiles_storage.url(path)
                    except ValueError as exc:
                        self.fail(f"{p['slug']}: {path} is not in the manifest ({exc})")

    def test_links_and_repos_are_label_url_pairs(self):
        for p in content.PROJECTS:
            for field in ("links", "repos"):
                for entry in p.get(field, []):
                    with self.subTest(project=p["slug"], field=field):
                        self.assertTrue(entry.get("label"))
                        self.assertTrue(entry.get("url", "").startswith("http"))

    def test_experience_carries_the_product_facing_copy(self):
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                experience = p.get("experience", {})
                self.assertTrue(experience.get("summary"))
                self.assertIsInstance(experience.get("features", []), list)


class EngineeringSchemaTests(SimpleTestCase):
    """Engineering data is optional, but what is present must be well formed."""

    def test_stack_entries_name_a_known_layer(self):
        for p in content.PROJECTS:
            for entry in p.get("engineering", {}).get("stack", []):
                with self.subTest(project=p["slug"], entry=entry):
                    self.assertTrue(entry.get("name"))
                    self.assertIn(entry.get("layer"), STACK_LAYERS)

    def test_architecture_nodes_are_well_formed(self):
        for p in content.PROJECTS:
            arch = p.get("engineering", {}).get("architecture")
            if not arch:
                continue
            for node in arch.get("nodes", []):
                with self.subTest(project=p["slug"], node=node.get("id")):
                    self.assertTrue(node.get("id"))
                    self.assertTrue(node.get("label"))
                    self.assertIn(node.get("kind"), NODE_KINDS)

    def test_architecture_node_ids_are_unique_within_a_project(self):
        for p in content.PROJECTS:
            arch = p.get("engineering", {}).get("architecture")
            if not arch:
                continue
            ids = [n["id"] for n in arch.get("nodes", [])]
            with self.subTest(project=p["slug"]):
                self.assertEqual(len(ids), len(set(ids)))

    def test_architecture_edges_reference_declared_nodes(self):
        """A dangling edge is what would make a generic renderer throw."""
        for p in content.PROJECTS:
            arch = p.get("engineering", {}).get("architecture")
            if not arch:
                continue
            ids = {n["id"] for n in arch.get("nodes", [])}
            for edge in arch.get("edges", []):
                with self.subTest(project=p["slug"], edge=edge):
                    self.assertIn(edge.get("from"), ids)
                    self.assertIn(edge.get("to"), ids)

    def test_decisions_state_both_the_choice_and_the_reason(self):
        for p in content.PROJECTS:
            for decision in p.get("engineering", {}).get("decisions", []):
                with self.subTest(project=p["slug"]):
                    self.assertTrue(decision.get("choice"))
                    self.assertTrue(decision.get("rationale"))


class RenderMixin:
    """Resolve a path and call its view, bypassing the instrumented Client.

    Http404 is turned into a real 404 response the same way Django's exception
    handler does, so a missing project can be asserted on as a status code
    rather than as an exception type.
    """

    def get(self, path="/"):
        request = RequestFactory().get(path)
        try:
            match = resolve(path.split("?")[0])
        except Resolver404 as exc:
            return page_not_found(request, Http404(exc))
        try:
            return match.func(request, *match.args, **match.kwargs)
        except Http404 as exc:
            return page_not_found(request, exc)

    def html(self, path="/"):
        return self.get(path).content.decode()

    def html_legacy(self, path="/"):
        """The legacy landing, which is opt-in now that Build Space leads."""
        with LEGACY:
            return self.html(path)


class HomePageTests(RenderMixin, SimpleTestCase):
    def test_page_renders(self):
        self.assertEqual(self.get("/").status_code, 200)

    def test_every_project_reaches_the_page(self):
        html = self.html_legacy()
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                self.assertIn(f'id="project-{p["slug"]}"', html)
                self.assertIn(p["name"], html)

    def test_deck_count_matches_the_data(self):
        html = self.html_legacy()
        self.assertEqual(html.count("data-deck-panel"), len(content.PROJECTS))

    def test_legacy_paths_still_redirect(self):
        for path, target in (
            ("/about/", "/#about"),
            ("/projects/", "/#work"),
            ("/contact/", "/#contact"),
        ):
            with self.subTest(path=path):
                response = self.get(path)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], target)

    def test_work_index_redirects_to_the_deck(self):
        """There is no work index of its own; /work/ should not dead-end."""
        response = self.get("/work/")
        self.assertIn(response.status_code, (301, 302))
        self.assertEqual(response["Location"], "/#work")

    def test_every_panel_links_to_its_case_study(self):
        html = self.html()
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                self.assertIn(
                    f'href="{reverse("project_detail", args=[p["slug"]])}"', html
                )

    def test_deck_hooks_survive_the_shared_media_partial(self):
        """The panel media moved into a partial; the deck's hooks must remain."""
        html = self.html_legacy()
        videos = sum(1 for p in content.PROJECTS if p.get("video"))
        self.assertEqual(html.count("data-deck-video"), videos)
        self.assertEqual(html.count("data-deck-play"), videos)
        # The deck's clips are driven by deck.js, so they carry no native
        # controls; that is the difference from the same partial on a case page.
        # Checked on the video tags themselves: "controls" as a bare substring
        # also matches aria-controls elsewhere on the page.
        for tag in re.findall(r"<video[^>]*>", html):
            with self.subTest(tag=tag[:60]):
                self.assertNotIn(" controls", tag)


class ProjectDetailTests(RenderMixin, SimpleTestCase):
    def test_every_slug_returns_200(self):
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                url = reverse("project_detail", args=[p["slug"]])
                self.assertEqual(self.get(url).status_code, 200)

    def test_unknown_slug_returns_404(self):
        response = self.get("/work/not-a-project/")
        self.assertEqual(response.status_code, 404)

    def test_page_shows_its_own_project_and_not_another(self):
        first, second = content.PROJECTS[0], content.PROJECTS[1]
        html = self.html(reverse("project_detail", args=[first["slug"]]))
        self.assertIn(first["name"], html)
        self.assertIn(first["kind"], html)
        self.assertIn(first["experience"]["summary"][:60], html)
        self.assertNotIn(second["experience"]["summary"][:60], html)

    def test_project_without_engineering_still_renders(self):
        with with_unverified():
            html = self.html(reverse("project_detail", args=[UNVERIFIED["slug"]]))
        self.assertIn(UNVERIFIED["name"], html)
        # The lens exists so the switch stays consistent across pages, but
        # nothing is invented to fill it.
        self.assertNotIn("data-engineering=", html)
        self.assertIn("has not been published", html)

    def test_engineering_lens_appears_only_where_there_is_data(self):
        for p in content.PROJECTS:
            html = self.html(reverse("project_detail", args=[p["slug"]]))
            with self.subTest(project=p["slug"]):
                # The experience lens is always the page's spine.
                self.assertIn('data-lens="experience"', html)
                if p.get("engineering"):
                    self.assertIn('data-lens="engineering"', html)

    def test_recorded_engineering_blocks_are_reachable_in_the_markup(self):
        """Each block carries its key, so a later renderer can target one."""
        for p in content.PROJECTS:
            engineering = p.get("engineering") or {}
            if not engineering:
                continue
            html = self.html(reverse("project_detail", args=[p["slug"]]))
            for key in ("stack", "architecture", "decisions"):
                if engineering.get(key):
                    with self.subTest(project=p["slug"], block=key):
                        self.assertIn(f'data-engineering="{key}"', html)

    def test_media_references_resolve(self):
        """Same manifest hazard as the deck, on a second surface."""
        for p in content.PROJECTS:
            html = self.html(reverse("project_detail", args=[p["slug"]]))
            with self.subTest(project=p["slug"]):
                if p.get("video"):
                    self.assertIn(staticfiles_storage.url(p["video"] + ".mp4"), html)
                elif p.get("image"):
                    self.assertIn(staticfiles_storage.url(p["image"] + ".jpg"), html)
                else:
                    self.assertIn("panel__plate", html)

    def test_clips_carry_native_controls_off_the_deck(self):
        """No deck means no deck.js, so the clip must be playable on its own."""
        withvideo = next(p for p in content.PROJECTS if p.get("video"))
        html = self.html(reverse("project_detail", args=[withvideo["slug"]]))
        self.assertIn("controls", html)
        self.assertNotIn("data-deck-video", html)

    def test_page_offers_a_way_back_to_the_work_section(self):
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                html = self.html(reverse("project_detail", args=[p["slug"]]))
                self.assertIn('href="/#work"', html)

    def test_meta_is_per_project(self):
        for p in content.PROJECTS:
            html = self.html(reverse("project_detail", args=[p["slug"]]))
            with self.subTest(project=p["slug"]):
                self.assertIn(f"<title>{p['name']}, {p['kind']}", html)
                self.assertIn(
                    f'<link rel="canonical" href="http://testserver/work/{p["slug"]}/">',
                    html,
                )
                # og:image has to be absolute to be usable by a crawler.
                self.assertIn('property="og:image" content="http://testserver/static/', html)

    def test_home_and_detail_do_not_share_a_title(self):
        home = self.html("/")
        detail = self.html(reverse("project_detail", args=[content.PROJECTS[0]["slug"]]))
        self.assertIn("<title>Joseph Edward,", home)
        self.assertNotIn("<title>Joseph Edward,", detail)


class PartialProjectTests(RenderMixin, SimpleTestCase):
    """The point of optional fields: a thin project renders, it doesn't fail."""

    MINIMAL = {
        "slug": "minimal",
        "name": "Minimal",
        "kind": "Nothing but identity",
        "year": "2026",
        "role": "Full-stack",
        "status": "in development",
    }

    def _render_with(self, projects):
        # Deck panels, so the legacy landing.
        with LEGACY, patch.object(content, "PROJECTS", projects):
            return self.get("/")

    @staticmethod
    def _panel(html, slug):
        return html.split(f'id="project-{slug}"')[1].split("</article>")[0]

    def test_project_with_no_media_links_or_engineering_renders(self):
        response = self._render_with([self.MINIMAL, content.PROJECTS[0]])
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('id="project-minimal"', html)
        # Falls back to the typographic plate rather than emitting a static tag.
        self.assertIn("panel__plate", html)

    def test_absent_optional_blocks_emit_nothing_rather_than_empty_shells(self):
        html = self._render_with([self.MINIMAL, content.PROJECTS[0]]).content.decode()
        panel = self._panel(html, "minimal")
        for absent in ("panel__features", "panel__tech", "panel__links"):
            with self.subTest(block=absent):
                self.assertNotIn(absent, panel)
        # The one thing a project with nothing recorded does say is that
        # nothing is recorded, and only inside the engineering lens.
        self.assertIn("panel__none", panel)
        self.assertIn("has not been published", panel)

    def test_engineering_without_a_stack_still_renders(self):
        thin = dict(self.MINIMAL, engineering={"overview": "Recorded, but no stack yet."})
        response = self._render_with([thin, content.PROJECTS[0]])
        self.assertEqual(response.status_code, 200)
        # An engineering block on its own renders nothing in the panel: the
        # chips come from the shared product-facing tech list, not from
        # engineering.stack. Scoped to this panel because the control project
        # beside it does have chips.
        panel = self._panel(response.content.decode(), "minimal")
        self.assertNotIn("panel__tech", panel)


class ModeResolutionTests(RenderMixin, SimpleTestCase):
    """The server half of mode resolution: URL parameter, else the default."""

    def mode_of(self, html):
        found = re.search(r'<html lang="en" data-mode="([^"]*)"', html)
        return found.group(1) if found else None

    def test_experience_is_the_default(self):
        for path in ("/", "/work/quanta/"):
            with self.subTest(path=path):
                self.assertEqual(self.mode_of(self.html(path)), "experience")

    def test_valid_url_mode_is_honoured(self):
        for path in ("/?mode=engineering", "/work/quanta/?mode=engineering"):
            with self.subTest(path=path):
                self.assertEqual(self.mode_of(self.html(path)), "engineering")

    def test_invalid_mode_falls_back_rather_than_becoming_a_third_state(self):
        for bad in ("bogus", "", "ENGINEERING", "engineering%20x", "1"):
            with self.subTest(value=bad):
                self.assertEqual(self.mode_of(self.html("/?mode=" + bad)), "experience")

    def test_mode_and_theme_stay_independent(self):
        """Mode must never emit a theme, or the two would fight on the root."""
        html = self.html("/?mode=engineering")
        self.assertIn('data-mode="engineering"', html)
        self.assertNotIn("data-theme=", html)

    def test_precedence_is_encoded_in_the_pre_paint_script(self):
        """The stored preference is only consulted when the URL is silent."""
        script = self.html("/").split("<script>")[1].split("</script>")[0]
        self.assertIn("localStorage.getItem('mode')", script)
        self.assertLess(
            script.index("window.location.search"),
            script.index("localStorage.getItem('mode')"),
        )

    def test_mode_is_resolved_before_the_body(self):
        """A deferred resolution would flash one lens and then replace it."""
        html = self.html("/")
        self.assertLess(html.index("data-mode="), html.index("<body"))


class ModeSwitchTests(RenderMixin, SimpleTestCase):
    def test_switch_offers_both_states_once(self):
        html = self.html("/")
        self.assertEqual(html.count('data-mode-set="experience"'), 1)
        self.assertEqual(html.count('data-mode-set="engineering"'), 1)
        self.assertIn('role="group"', html)
        self.assertIn('aria-label="View mode"', html)

    def test_selected_state_is_marked_on_exactly_one_option(self):
        for path, selected in (("/", "experience"), ("/?mode=engineering", "engineering")):
            html = self.html(path)
            with self.subTest(path=path):
                self.assertEqual(html.count('aria-current="true"'), 1)
                marked = re.search(r'data-mode-set="([^"]+)"\s+aria-current="true"', html)
                self.assertIsNotNone(marked, "no option carries the selected state")
                self.assertEqual(marked.group(1), selected)

    def test_switch_targets_are_real_links_so_it_works_without_javascript(self):
        html = self.html("/work/quanta/")
        self.assertIn('href="/work/quanta/?mode=engineering"', html)
        self.assertIn('href="/work/quanta/"', html)

    def test_switch_urls_keep_unrelated_query_parameters(self):
        html = self.html("/work/quanta/?ref=newsletter")
        self.assertIn("ref=newsletter", html)
        self.assertIn("mode=engineering", html)

    def test_default_mode_needs_no_parameter(self):
        """Ordinary URLs stay clean; only the non-default carries a parameter."""
        html = self.html("/?mode=engineering")
        self.assertIn('href="/"', html)


class ModeContentTests(RenderMixin, SimpleTestCase):
    def test_both_lenses_ship_in_the_html(self):
        """The switch is instant because nothing has to be fetched."""
        html = self.html("/work/quanta/")
        self.assertIn('data-lens="experience"', html)
        self.assertIn('data-lens="engineering"', html)

    def test_every_project_is_reachable_in_both_modes(self):
        for p in content.PROJECTS:
            for query in ("", "?mode=engineering"):
                path = reverse("project_detail", args=[p["slug"]]) + query
                with self.subTest(path=path):
                    self.assertEqual(self.get(path).status_code, 200)

    def test_engineering_lens_carries_verified_content(self):
        html = self.html("/work/rbad/?mode=engineering")
        rbad = next(p for p in content.PROJECTS if p["slug"] == "rbad")
        self.assertIn(rbad["engineering"]["overview"][:50], html)
        self.assertIn('data-engineering="architecture"', html)

    def test_project_without_engineering_stays_valid_in_engineering_mode(self):
        path = reverse("project_detail", args=[UNVERIFIED["slug"]]) + "?mode=engineering"
        with with_unverified():
            html = self.html(path)
        self.assertIn(UNVERIFIED["name"], html)
        # Absence is stated, never filled in with an invented block.
        self.assertNotIn("data-engineering=", html)
        self.assertIn("has not been published", html)

    def test_shared_content_is_rendered_once_not_per_lens(self):
        """Media and links belong to the project, not to a lens."""
        html = self.html("/work/rbad/")
        self.assertEqual(html.count('class="panel__shot"'), 1)
        self.assertEqual(html.count("panel__link--repo"), 1)

    def test_deck_panels_carry_both_lenses(self):
        html = self.html_legacy("/")
        self.assertEqual(html.count('data-lens="experience"'), len(content.PROJECTS))
        self.assertEqual(html.count('data-lens="engineering"'), len(content.PROJECTS))

    def test_deck_mechanics_are_untouched_by_mode(self):
        """Panel count drives the deck's height maths; mode must not alter it."""
        videos = sum(1 for p in content.PROJECTS if p.get("video"))
        for query in ("", "?mode=engineering"):
            html = self.html_legacy("/" + query)
            with self.subTest(query=query):
                self.assertEqual(html.count("data-deck-panel"), len(content.PROJECTS))
                self.assertEqual(html.count("data-deck-video"), videos)


class ModeNavigationTests(RenderMixin, SimpleTestCase):
    def test_internal_links_carry_an_explicit_mode(self):
        html = self.html("/?mode=engineering")
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                self.assertIn("/work/%s/?mode=engineering" % p["slug"], html)

    def test_case_study_back_links_preserve_the_mode(self):
        html = self.html("/work/quanta/?mode=engineering")
        self.assertIn('href="/?mode=engineering#work"', html)
        self.assertIn('href="/?mode=engineering#contact"', html)

    def test_external_links_never_get_a_mode(self):
        html = self.html("/?mode=engineering")
        for external in re.findall(r'href="(https?://[^"]*)"', html):
            with self.subTest(url=external):
                self.assertNotIn("mode=", external)

    def test_legacy_redirects_are_unaffected_by_mode(self):
        response = self.get("/projects/?mode=engineering")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/#work")


class ModeThemeIndependenceTests(SimpleTestCase):
    """Mode and theme are separate root-level concerns and must stay that way.

    These read the stylesheet rather than a rendered page, because what is
    being asserted is a property of the rules themselves: if every colour in
    the switch comes from a token, the control cannot be legible in one theme
    and invisible in the other.
    """

    @staticmethod
    def _rule(css, selector):
        start = css.index(selector)
        return css[start:css.index("}", start) + 1]

    def setUp(self):
        with open(BASE_CSS, encoding="utf-8") as handle:
            self.css = handle.read()

    def test_switch_takes_every_colour_from_a_token(self):
        for selector in (".modes {", ".modes__opt {", '.modes__opt[aria-current="true"] {'):
            with self.subTest(selector=selector):
                rule = self._rule(self.css, selector)
                self.assertNotRegex(
                    rule,
                    r"#[0-9a-fA-F]{3,8}|\brgb\(|\bhsl\(",
                    "a literal colour here would pin the switch to one theme",
                )

    def test_selected_state_inverts_ink_and_paper(self):
        """Whatever the theme, the selected option is the page's inverse."""
        rule = self._rule(self.css, '.modes__opt[aria-current="true"] {')
        self.assertIn("background: var(--ink)", rule)
        self.assertIn("color: var(--paper)", rule)

    def test_selected_state_hangs_off_the_accessible_state(self):
        """One source of truth: what is announced is what is styled."""
        self.assertIn('.modes__opt[aria-current="true"]', self.css)
        self.assertNotIn(".modes__opt.is-active", self.css)

    def test_inactive_lens_is_removed_not_just_hidden(self):
        """display:none also takes it out of the tab order and the a11y tree."""
        rule = self._rule(self.css, '[data-mode="experience"] [data-lens="engineering"]')
        self.assertIn("display: none", rule)
        self.assertNotIn("opacity", rule)
        self.assertNotIn("visibility", rule)

    def test_mode_rules_never_mention_theme(self):
        """A rule needing both would couple two independent concerns."""
        for line in self.css.splitlines():
            if "data-mode=" in line and "data-theme=" in line:
                self.fail("mode and theme are entangled in: " + line.strip())


class ContactMixin:
    """POST to the contact endpoint without middleware or real mail.

    RequestFactory skips the middleware, so the message framework has nothing
    to write into. Attaching storage by hand is the smallest way to exercise
    the real view rather than a stand-in for it.
    """

    VALID = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "subject": "Prediction engine",
        "message": "Two lines.\nSecond one.",
    }

    def post(self, data=None):
        request = RequestFactory().post("/", data if data is not None else self.VALID)
        request.session = {}
        request._messages = FallbackStorage(request)
        return views.home(request)


class ContactSubmissionTests(ContactMixin, SimpleTestCase):
    """The path a real enquiry takes. Nothing here may send real mail."""

    def test_get_never_sends_mail(self):
        with patch("pages.views.send_contact_message") as send:
            request = RequestFactory().get("/")
            response = views.home(request)
        self.assertEqual(response.status_code, 200)
        send.assert_not_called()

    def test_valid_submission_sends_once_and_redirects_to_the_form(self):
        with patch("pages.views.send_contact_message") as send:
            response = self.post()
        self.assertEqual(send.call_count, 1)
        # POST-redirect-GET, so a refresh cannot resubmit.
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/#contact")

    def test_submitted_values_reach_the_mail_layer_intact(self):
        with patch("pages.views.send_contact_message") as send:
            self.post()
        args, kwargs = send.call_args
        name, email, subject, message = args
        self.assertEqual(name, self.VALID["name"])
        self.assertEqual(email, self.VALID["email"])
        self.assertEqual(subject, self.VALID["subject"])
        self.assertEqual(message, self.VALID["message"])

    def test_values_are_stripped_before_sending(self):
        with patch("pages.views.send_contact_message") as send:
            self.post(dict(self.VALID, name="  Ada  ", email=" ada@example.com "))
        name, email, _, _ = send.call_args[0]
        self.assertEqual(name, "Ada")
        self.assertEqual(email, "ada@example.com")

    def test_subject_is_optional(self):
        with patch("pages.views.send_contact_message") as send:
            response = self.post(dict(self.VALID, subject=""))
        self.assertEqual(send.call_count, 1)
        self.assertEqual(response.status_code, 302)

    def test_success_message_is_shown_and_names_the_sender(self):
        request = RequestFactory().post("/", self.VALID)
        request.session = {}
        request._messages = FallbackStorage(request)
        with patch("pages.views.send_contact_message"):
            views.home(request)
        texts = [str(m) for m in request._messages]
        self.assertTrue(any("Ada Lovelace" in t for t in texts), texts)
        self.assertTrue(any("24 hours" in t for t in texts), texts)


class ContactValidationTests(ContactMixin, SimpleTestCase):
    def test_required_fields_are_required(self):
        for missing in ("name", "email", "message"):
            with self.subTest(missing=missing):
                with patch("pages.views.send_contact_message") as send:
                    response = self.post(dict(self.VALID, **{missing: ""}))
                send.assert_not_called()
                # Re-rendered in place, not redirected, so nothing is lost.
                self.assertEqual(response.status_code, 200)

    def test_whitespace_only_counts_as_missing(self):
        with patch("pages.views.send_contact_message") as send:
            response = self.post(dict(self.VALID, message="   \n  "))
        send.assert_not_called()
        self.assertEqual(response.status_code, 200)

    def test_validation_failure_explains_itself(self):
        request = RequestFactory().post("/", dict(self.VALID, name=""))
        request.session = {}
        request._messages = FallbackStorage(request)
        with patch("pages.views.send_contact_message"):
            views.home(request)
        texts = [str(m) for m in request._messages]
        self.assertTrue(any("name" in t.lower() for t in texts), texts)

    def test_a_rejected_submission_hands_the_words_back(self):
        """Losing a typed enquiry to a validation error costs it twice."""
        response = self.post(dict(self.VALID, email=""))
        html = response.content.decode()
        self.assertIn('value="Ada Lovelace"', html)
        self.assertIn("Two lines.", html)

    def test_clearly_invalid_addresses_never_reach_the_mail_layer(self):
        """A bad address either bounces or arrives with a dead reply-to."""
        for bad in ("not-an-email", "ada@", "@example.com", "ada example.com",
                    "ada@@example.com", "ada@example", "ada@.com"):
            with self.subTest(email=bad):
                with patch("pages.views.send_contact_message") as send:
                    response = self.post(dict(self.VALID, email=bad))
                send.assert_not_called()
                self.assertEqual(response.status_code, 200)

    def test_an_invalid_address_says_so(self):
        request = RequestFactory().post("/", dict(self.VALID, email="not-an-email"))
        request.session = {}
        request._messages = FallbackStorage(request)
        with patch("pages.views.send_contact_message"):
            views.home(request)
        texts = [str(m) for m in request._messages]
        self.assertTrue(any("email address" in t.lower() for t in texts), texts)

    def test_an_invalid_address_keeps_every_other_field(self):
        response = self.post(dict(self.VALID, email="not-an-email"))
        html = response.content.decode()
        self.assertIn('value="Ada Lovelace"', html)
        self.assertIn("Two lines.", html)
        self.assertIn('value="not-an-email"', html)

    def test_ordinary_addresses_still_get_through(self):
        for good in ("ada@example.com", "ada.lovelace+tag@sub.example.co.uk",
                     "a@b.io", "JOSEPH@EXAMPLE.COM"):
            with self.subTest(email=good):
                with patch("pages.views.send_contact_message") as send:
                    response = self.post(dict(self.VALID, email=good))
                self.assertEqual(send.call_count, 1, f"{good} was rejected")
                self.assertEqual(response.status_code, 302)

    def test_an_empty_post_does_not_explode(self):
        with patch("pages.views.send_contact_message") as send:
            response = self.post({})
        send.assert_not_called()
        self.assertEqual(response.status_code, 200)


class ContactFailureTests(ContactMixin, SimpleTestCase):
    """What the visitor gets when Resend is down, misconfigured or absent."""

    def test_mail_failure_keeps_the_page_up(self):
        # assertLogs both captures the traceback, keeping the suite output
        # readable, and asserts the failure is actually recorded rather than
        # swallowed.
        with patch("pages.views.send_contact_message", side_effect=RuntimeError("boom")):
            with self.assertLogs("pages.views", level="ERROR") as logged:
                response = self.post()
        # Not a 500, and not a redirect that would imply success.
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any("Resend" in line for line in logged.output))

    def test_mail_failure_tells_the_visitor_where_else_to_go(self):
        request = RequestFactory().post("/", self.VALID)
        request.session = {}
        request._messages = FallbackStorage(request)
        with patch("pages.views.send_contact_message", side_effect=RuntimeError("boom")):
            with self.assertLogs("pages.views", level="ERROR"):
                views.home(request)
        texts = [str(m) for m in request._messages]
        self.assertTrue(any(settings.CONTACT_EMAIL in t for t in texts), texts)

    def test_a_failed_send_hands_the_words_back(self):
        """The failure the visitor did not cause must not also erase their work."""
        with patch("pages.views.send_contact_message", side_effect=RuntimeError("boom")):
            with self.assertLogs("pages.views", level="ERROR"):
                response = self.post()
        html = response.content.decode()
        self.assertIn('value="Ada Lovelace"', html)
        self.assertIn('value="ada@example.com"', html)
        self.assertIn("Two lines.", html)

    def test_a_missing_resend_dependency_is_survivable(self):
        """The import is inside the function precisely for this case."""
        with patch("pages.views.send_contact_message", side_effect=ImportError("no resend")):
            with self.assertLogs("pages.views", level="ERROR"):
                response = self.post()
        self.assertEqual(response.status_code, 200)


class MailPayloadTests(SimpleTestCase):
    """The boundary itself: what Resend is actually handed."""

    def send(self, **overrides):
        fake = MagicMock()
        payload = dict(
            name="Ada Lovelace", email="ada@example.com",
            subject="Prediction engine", message="Hello",
        )
        payload.update(overrides)
        with patch.dict(sys.modules, {"resend": fake}):
            mail.send_contact_message(**payload)
        return fake.Emails.send.call_args[0][0]

    def test_payload_addresses_are_correct(self):
        sent = self.send()
        self.assertEqual(sent["from"], mail.FROM_ADDRESS)
        self.assertEqual(sent["to"], [settings.CONTACT_EMAIL])
        # A reply must reach the sender, not the portfolio inbox.
        self.assertEqual(sent["reply_to"], "ada@example.com")

    def test_subject_uses_the_visitors_subject_when_given(self):
        self.assertIn("Prediction engine", self.send()["subject"])

    def test_subject_falls_back_to_the_sender_name(self):
        self.assertIn("Ada Lovelace", self.send(subject="")["subject"])

    def test_body_carries_the_message(self):
        self.assertIn("Hello", self.send()["html"])

    def test_html_injection_from_the_form_is_escaped(self):
        """These strings go straight into an HTML document in someone's inbox."""
        sent = self.send(
            name="<script>alert(1)</script>",
            message="<img src=x onerror=alert(1)>",
            subject="<b>bold</b>",
        )
        # The test is whether a tag can form, not whether the characters
        # appear: escape() leaves "onerror=" alone, and that is fine, because
        # with the angle brackets escaped it is text rather than an attribute.
        self.assertNotIn("<script>", sent["html"])
        self.assertNotIn("<img", sent["html"])
        self.assertNotIn("<b>bold</b>", sent["html"])
        self.assertIn("&lt;script&gt;", sent["html"])
        self.assertIn("&lt;img", sent["html"])

    def test_newlines_survive_as_line_breaks(self):
        self.assertIn("<br>", self.send(message="one\ntwo")["html"])

    def test_api_key_comes_from_settings(self):
        fake = MagicMock()
        with patch.dict(sys.modules, {"resend": fake}):
            mail.send_contact_message("A", "a@example.com", "", "hi")
        self.assertEqual(fake.api_key, settings.RESEND_API_KEY)


class ContactFormMarkupTests(RenderMixin, SimpleTestCase):
    """The contract the redesigned contact UI has to keep honouring."""

    def form(self):
        html = self.html("/")
        return html[html.index('<form class="form"'):html.index("</form>")]

    def test_a_fresh_form_is_empty(self):
        """Repopulation must not leak into an untouched page."""
        form = self.form()
        self.assertIn('name="name"', form)
        self.assertNotIn("value=\"Ada", form)

    def test_form_is_on_the_home_page(self):
        self.assertIn('id="contact-form"', self.html("/"))

    def test_form_posts_to_the_home_view_at_the_contact_anchor(self):
        form = self.form()
        self.assertIn('method="post"', form)
        self.assertIn('action="/#contact"', form)

    def test_field_names_are_the_ones_the_view_reads(self):
        form = self.form()
        for field in ("name", "email", "subject", "message"):
            with self.subTest(field=field):
                self.assertIn(f'name="{field}"', form)

    def test_csrf_token_is_present(self):
        self.assertIn("csrfmiddlewaretoken", self.form())

    def test_required_fields_are_marked_required(self):
        form = self.form()
        self.assertEqual(form.count("required"), 3)


class ContactCsrfTests(SimpleTestCase):
    """CSRF is enforced by middleware, so this one goes through the real stack.

    Uses django.test.Client rather than RequestFactory precisely because the
    middleware is the thing under test. It needs the supported interpreter.
    """

    def test_post_without_a_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        with patch("pages.views.send_contact_message") as send:
            response = client.post("/", {
                "name": "Ada", "email": "ada@example.com", "message": "hi",
            })
        self.assertEqual(response.status_code, 403)
        send.assert_not_called()

    def test_post_with_a_token_is_accepted(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/")                      # sets the CSRF cookie
        token = client.cookies["csrftoken"].value
        with patch("pages.views.send_contact_message") as send:
            response = client.post("/", {
                "name": "Ada", "email": "ada@example.com", "message": "hi",
                "csrfmiddlewaretoken": token,
            })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(send.call_count, 1)


class PartialContractTests(SimpleTestCase):
    """What each reusable partial promises, given only its documented inputs.

    Worth asserting directly because Django's include swallows exceptions
    outside debug mode: a partial that raises renders as an empty string, so a
    broken one looks like a styling problem rather than an error. Rendering the
    template on its own turns that silence back into a failure.
    """

    MEDIA = "pages/partials/project/media.html"
    LINKS = "pages/partials/project/links.html"
    ENGINEERING = "pages/partials/project/engineering.html"

    @staticmethod
    def render(template, context):
        return get_template(template).render(context)

    def project(self, slug):
        return next(p for p in content.PROJECTS if p["slug"] == slug)

    def test_media_renders_a_video_project_in_a_phone_frame(self):
        out = self.render(self.MEDIA, {"project": self.project("quanta"), "deck": True})
        self.assertIn("panel__phone", out)
        self.assertIn("data-deck-video", out)

    def test_media_renders_an_image_project_as_a_figure(self):
        out = self.render(self.MEDIA, {"project": self.project("rbad"), "deck": True})
        self.assertIn("panel__shot", out)
        self.assertIn("<img", out)

    def test_media_falls_back_to_a_plate_with_no_media(self):
        bare = {"slug": "x", "name": "X", "kind": "Nothing"}
        out = self.render(self.MEDIA, {"project": bare, "deck": True})
        self.assertIn("panel__plate", out)
        # No static tag may be emitted for media that does not exist.
        self.assertNotIn("<img", out)
        self.assertNotIn("<video", out)

    def test_media_off_the_deck_swaps_hooks_for_native_controls(self):
        out = self.render(self.MEDIA, {"project": self.project("quanta"), "deck": False})
        self.assertIn("controls", out)
        self.assertNotIn("data-deck-video", out)
        self.assertNotIn("data-deck-play", out)

    def test_links_renders_both_rows_when_present(self):
        out = self.render(self.LINKS, {"project": self.project("crownie")})
        self.assertIn("panel__links", out)
        self.assertIn("panel__link--repo", out)

    def test_links_renders_nothing_at_all_when_there_are_none(self):
        out = self.render(self.LINKS, {"project": {"slug": "x", "links": [], "repos": []}})
        self.assertNotIn("panel__links", out)

    def test_engineering_renders_only_the_blocks_that_exist(self):
        out = self.render(self.ENGINEERING, {"engineering": {"stack": [
            {"name": "Django", "layer": "backend"}]}})
        self.assertIn('data-engineering="stack"', out)
        for absent in ("architecture", "api", "auth", "decisions"):
            with self.subTest(block=absent):
                self.assertNotIn(f'data-engineering="{absent}"', out)

    def test_engineering_renders_nothing_for_an_empty_record(self):
        self.assertEqual(self.render(self.ENGINEERING, {"engineering": {}}).strip(), "")

    def test_partials_are_not_silently_empty_on_the_real_pages(self):
        """The failure mode this whole class exists for, checked end to end."""
        request = RequestFactory().get("/")
        html = views.home(request).content.decode()
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                if p.get("video"):
                    self.assertIn(staticfiles_storage.url(p["video"] + ".mp4"), html)
                elif p.get("image"):
                    self.assertIn(staticfiles_storage.url(p["image"] + ".jpg"), html)


class LandingSeamTests(RenderMixin, SimpleTestCase):
    """A deploy-time seam, so a new landing never means a second home page."""

    def test_the_current_landing_is_the_default(self):
        self.assertEqual(views._landing(), views.LANDINGS["build"])

    def test_legacy_landing_renders_the_hero_and_owns_the_intro(self):
        html = self.html_legacy("/")
        self.assertIn('class="hero"', html)
        self.assertIn('id="preloader"', html)

    def test_an_unknown_landing_falls_back_instead_of_blanking_the_page(self):
        """And falls back to the default, not to whatever used to be default:
        a typo in JOE_LANDING should serve the page an unset one does."""
        with override_settings(LANDING="landing-that-does-not-exist"):
            html = self.html("/")
        self.assertIn("data-build", html)
        self.assertNotIn('class="hero"', html)

    def test_the_seam_carries_the_intro_flag_with_the_landing(self):
        """A landing without a hero must not leave the preloader up."""
        registry = dict(views.LANDINGS, headless={
            "template": "pages/partials/about.html", "intro": False})
        with patch.object(views, "LANDINGS", registry), override_settings(LANDING="headless"):
            html = self.html("/")
        self.assertNotIn('id="preloader"', html)
        self.assertNotIn('class="hero"', html)

    def test_the_seam_is_not_reachable_from_a_url(self):
        """Configuration, not a user-facing toggle."""
        html = self.html("/?landing=legacy")
        self.assertIn("data-build", html)
        self.assertNotIn('class="hero"', html)


class MotionSchedulerTests(SimpleTestCase):
    """The shared scheduler is a contract between files, so assert the wiring."""

    @staticmethod
    def js(name):
        with open(JS_DIR / name, encoding="utf-8") as handle:
            return handle.read()

    def test_only_the_scheduler_listens_for_scroll(self):
        for name in ("nav.js", "deck.js"):
            with self.subTest(script=name):
                self.assertNotIn("addEventListener('scroll'", self.js(name))
        self.assertIn("addEventListener('scroll'", self.js("motion.js"))

    def test_consumers_subscribe_rather_than_scheduling_their_own_frames(self):
        for name in ("nav.js", "deck.js"):
            with self.subTest(script=name):
                script = self.js(name)
                self.assertIn("motion.onScroll(", script)
                self.assertNotIn("requestAnimationFrame", script)

    def test_the_scheduler_clears_its_guard_in_a_finally(self):
        """A throw that skipped the reset used to freeze every later frame."""
        script = self.js("motion.js")
        self.assertIn("finally", script)
        self.assertIn("scrolling = false", script)

    def test_a_throwing_subscriber_is_contained(self):
        self.assertIn("catch", self.js("motion.js"))

    def test_intro_keeps_its_own_loop_and_its_hard_stop(self):
        """It animates progress on a lifecycle of its own; it is not scroll work."""
        script = self.js("intro.js")
        self.assertIn("requestAnimationFrame", script)
        self.assertIn("setTimeout", script)

    def test_the_scheduler_loads_before_its_consumers(self):
        with open(TEMPLATES_DIR / "base.html", encoding="utf-8") as handle:
            base = handle.read()
        self.assertLess(base.index("js/motion.js"), base.index("js/nav.js"))
        self.assertLess(base.index("js/motion.js"), base.index("js/deck.js"))


class StylesheetSplitTests(SimpleTestCase):
    """The split has to keep the cascade, or the appearance changes silently."""

    ORDER = ["foundation.css", "chrome.css", "intro.css", "about.css",
             "work.css", "case.css", "contact.css"]

    def base(self):
        with open(TEMPLATES_DIR / "base.html", encoding="utf-8") as handle:
            return handle.read()

    def test_every_part_is_linked(self):
        base = self.base()
        for name in self.ORDER:
            with self.subTest(sheet=name):
                self.assertIn(f"css/{name}", base)

    def test_parts_are_linked_in_cascade_order(self):
        base = self.base()
        positions = [base.index(f"css/{name}") for name in self.ORDER]
        self.assertEqual(positions, sorted(positions))

    def test_tokens_live_only_in_the_foundation(self):
        """A part redefining a token would fork the theme."""
        for name in self.ORDER[1:]:
            with self.subTest(sheet=name):
                with open(CSS_DIR / name, encoding="utf-8") as handle:
                    self.assertNotIn("--ink:", handle.read())

    def test_the_monolith_is_gone(self):
        self.assertFalse((CSS_DIR / "main.css").exists())


class PaletteCommandTests(SimpleTestCase):
    """The command set is derived, so adding a project must add a command."""

    def commands(self):
        return views._palette_commands()

    def by_id(self):
        return {c["id"]: c for c in self.commands()}

    def test_every_project_has_a_command(self):
        ids = self.by_id()
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                self.assertIn(f"project:{p['slug']}", ids)

    def test_there_are_no_commands_for_projects_that_do_not_exist(self):
        """A stale entry would navigate to a 404."""
        slugs = {p["slug"] for p in content.PROJECTS}
        for command in self.commands():
            if command["id"].startswith("project:"):
                with self.subTest(command=command["id"]):
                    self.assertIn(command["id"].split(":", 1)[1], slugs)

    def test_project_commands_point_at_the_real_routes(self):
        ids = self.by_id()
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                expected = reverse("project_detail", args=[p["slug"]])
                self.assertEqual(ids[f"project:{p['slug']}"]["path"], expected)

    def test_project_commands_carry_no_mode_of_their_own(self):
        """Mode is appended by JE.mode at activation, not baked in here."""
        for command in self.commands():
            with self.subTest(command=command["id"]):
                self.assertNotIn("mode=", command.get("path", ""))

    def test_search_terms_cover_name_kind_and_tech(self):
        ids = self.by_id()
        quanta = ids["project:quanta"]["terms"]
        self.assertIn("quanta", quanta)
        self.assertIn("adaptive learning workspace", quanta)
        self.assertIn("django", quanta)

    def test_typing_a_technology_reaches_the_projects_that_use_it(self):
        """The example from the brief: django should surface Django projects."""
        matched = [c["label"] for c in self.commands() if "django" in c.get("terms", "")]
        for expected in ("Quanta", "SpendWise", "RBAD"):
            with self.subTest(project=expected):
                self.assertIn(expected, matched)

    def test_searching_mobile_finds_the_mobile_apps_and_only_those(self):
        """No project spells out "mobile"; the word is derived from Expo."""
        matched = {c["label"] for c in self.commands() if "mobile" in c.get("terms", "")}
        self.assertEqual(matched, {"Quanta", "SpendWise", "Sync"})

    def test_searching_web_finds_the_web_builds_and_not_the_apps(self):
        matched = {c["label"] for c in self.commands() if "web " in c.get("terms", "") + " "}
        self.assertEqual(matched, {"Vaultor", "RBAD", "Crownie"})

    def test_derived_keywords_come_from_technologies_a_project_lists(self):
        """Derivation, not hand-tagging: a project with no Expo is not mobile."""
        ids = self.by_id()
        self.assertIn("mobile", ids["project:quanta"]["terms"])
        self.assertNotIn("mobile", ids["project:marketbrainers"]["terms"])

    def test_engineering_stack_is_searchable_where_it_exists(self):
        """Verified stack names, not just the product-facing chips."""
        ids = self.by_id()
        self.assertIn("simple jwt", ids["project:rbad"]["terms"])
        self.assertIn("celery", ids["project:sync"]["terms"])

    def test_a_project_without_engineering_still_gets_a_command(self):
        with with_unverified():
            ids = {c["id"] for c in views._palette_commands()}
        self.assertIn(f"project:{UNVERIFIED['slug']}", ids)

    def test_both_modes_are_offered_as_commands(self):
        ids = self.by_id()
        for mode in views.MODES:
            with self.subTest(mode=mode):
                command = ids[f"mode:{mode}"]
                self.assertEqual(command["action"], "mode")
                self.assertEqual(command["value"], mode)

    def test_sections_and_links_are_present(self):
        ids = self.by_id()
        for slug in ("about", "work", "contact"):
            with self.subTest(section=slug):
                self.assertIn(f"section:{slug}", ids)
        self.assertIn("social:github", ids)
        self.assertIn("social:linkedin", ids)
        self.assertIn("contact:email", ids)

    def test_external_commands_are_flagged_and_absolute(self):
        for command in self.commands():
            if command.get("external"):
                with self.subTest(command=command["id"]):
                    self.assertTrue(
                        command["url"].startswith(("http", "mailto:")), command["url"]
                    )

    def test_internal_commands_are_never_flagged_external(self):
        for command in self.commands():
            if command.get("path"):
                with self.subTest(command=command["id"]):
                    self.assertFalse(command.get("external"))

    def test_the_payload_stays_small(self):
        """It ships on every page, so it has a budget."""
        size = len(json.dumps(self.commands()))
        self.assertLess(size, 12 * 1024, f"palette payload is {size} bytes")


class PaletteMarkupTests(RenderMixin, SimpleTestCase):
    def test_palette_is_on_every_page(self):
        for path in ("/", "/work/quanta/", "/work/marketbrainers/?mode=engineering"):
            with self.subTest(path=path):
                html = self.html(path)
                self.assertIn('id="palette"', html)
                self.assertIn('id="palette-data"', html)

    def test_there_is_a_visible_trigger_not_only_a_shortcut(self):
        html = self.html("/")
        self.assertIn("data-palette-open", html)
        self.assertIn('aria-label="Open command palette"', html)

    def test_dialog_semantics(self):
        html = self.html("/")
        self.assertIn("<dialog", html)
        self.assertIn('aria-label="Command palette"', html)

    def test_combobox_and_listbox_semantics(self):
        html = self.html("/")
        self.assertIn('role="combobox"', html)
        self.assertIn('role="listbox"', html)
        self.assertIn('aria-controls="palette-list"', html)
        self.assertIn('aria-activedescendant=""', html)

    def test_command_data_is_serialised_safely(self):
        """json_script escapes, so a label could never close the tag."""
        html = self.html("/")
        self.assertIn('<script id="palette-data" type="application/json">', html)

    def test_embedded_commands_match_the_server_side_set(self):
        html = self.html("/")
        raw = re.search(
            r'<script id="palette-data" type="application/json">(.*?)</script>',
            html, re.S,
        ).group(1)
        self.assertEqual(len(json.loads(raw)), len(views._palette_commands()))

    def test_palette_script_loads_after_mode(self):
        """It switches modes through JE.mode, so mode.js has to be defined."""
        with open(TEMPLATES_DIR / "base.html", encoding="utf-8") as handle:
            base = handle.read()
        self.assertLess(base.index("js/mode.js"), base.index("js/palette.js"))

    def test_palette_has_its_own_stylesheet(self):
        with open(TEMPLATES_DIR / "base.html", encoding="utf-8") as handle:
            self.assertIn("css/palette.css", handle.read())


class PaletteBehaviourContractTests(SimpleTestCase):
    """Contracts between palette.js and the rest, asserted at the source."""

    @staticmethod
    def js(name):
        with open(JS_DIR / name, encoding="utf-8") as handle:
            return handle.read()

    def test_mode_is_not_reimplemented(self):
        script = self.js("palette.js")
        self.assertIn("JE", script)
        self.assertIn("api.set(", script)
        # No second copy of the storage or parameter rules.
        self.assertNotIn("localStorage", script)
        self.assertNotIn("pushState", script)

    def test_mode_api_is_exported_unconditionally(self):
        """The palette needs it even on a page without the switch markup."""
        script = self.js("mode.js")
        self.assertIn("JE.mode", script)
        self.assertNotIn("if (!opts.length) return;", script)

    def test_slash_is_ignored_while_typing(self):
        script = self.js("palette.js")
        self.assertIn("isTyping", script)
        for tag in ("INPUT", "TEXTAREA", "SELECT"):
            with self.subTest(tag=tag):
                self.assertIn(tag, script)
        self.assertIn("isContentEditable", script)

    def test_it_uses_the_native_dialog_rather_than_a_hand_rolled_trap(self):
        script = self.js("palette.js")
        self.assertIn("showModal()", script)
        self.assertIn("dialog.close()", script)

    def test_focus_is_restored_on_close(self):
        script = self.js("palette.js")
        self.assertIn("opener", script)
        self.assertIn("opener.focus()", script)

    def test_no_client_router_is_introduced(self):
        script = self.js("palette.js")
        self.assertIn("window.location.assign", script)
        self.assertNotIn("history.pushState", script)

    def test_reduced_motion_is_respected_in_the_stylesheet(self):
        with open(CSS_DIR / "palette.css", encoding="utf-8") as handle:
            css = handle.read()
        # Animation is opt-in for people who have not asked for less motion.
        self.assertIn("prefers-reduced-motion: no-preference", css)

    def test_palette_colours_come_from_tokens(self):
        with open(CSS_DIR / "palette.css", encoding="utf-8") as handle:
            css = handle.read()
        literals = re.findall(r"#[0-9a-fA-F]{3,8}", css)
        self.assertEqual(literals, [], f"hard-coded colours: {literals}")


BUILD = override_settings(LANDING="build")


class BuildSpaceLandingTests(RenderMixin, SimpleTestCase):
    """The seam, and the guarantee that legacy is still there behind it."""

    def test_build_space_is_the_default(self):
        self.assertEqual(views._landing(), views.LANDINGS["build"])
        html = self.html("/")
        self.assertIn("data-build", html)
        self.assertEqual(html.count("data-node-link"), len(content.PROJECTS))

    def test_legacy_is_still_reachable_through_the_seam(self):
        """Signed off, but not deleted: JOE_LANDING=legacy brings it back."""
        html = self.html_legacy("/")
        self.assertIn('class="hero"', html)
        self.assertNotIn("data-node-link", html)

    def test_build_space_is_selectable_through_the_seam(self):
        with BUILD:
            html = self.html("/")
        self.assertIn("data-build", html)
        self.assertEqual(html.count("data-node-link"), len(content.PROJECTS))

    def test_build_space_replaces_the_hero_rather_than_joining_it(self):
        with BUILD:
            html = self.html("/")
        self.assertNotIn('class="hero"', html)
        self.assertNotIn('id="code-card"', html)

    def test_build_space_gets_the_preloader_too(self):
        """The loading layer belongs to the page, not to the hero."""
        with BUILD:
            html = self.html("/")
        self.assertIn('id="preloader"', html)
        self.assertIn("wantsIntro = true", html)

    def test_the_build_space_has_nothing_for_the_intro_to_hand_off_to(self):
        """Which is why intro.js must dismiss the preloader on its own rather
        than waiting on a hero to reveal."""
        with BUILD:
            html = self.html("/")
        self.assertNotIn('id="code-card"', html)
        self.assertNotIn('id="code-out"', html)

    def test_legacy_landing_pays_nothing_for_the_build_space(self):
        html = self.html_legacy("/")
        self.assertNotIn("css/build.", html)
        self.assertNotIn("js/build.", html)

    def test_build_assets_load_only_where_they_are_used(self):
        with BUILD:
            html = self.html("/")
        self.assertIn("css/build.", html)
        self.assertIn("js/build.", html)

    def test_the_seam_is_not_reachable_from_a_url(self):
        """Deploy configuration, not a public toggle."""
        html = self.html_legacy("/?landing=build")
        self.assertIn('class="hero"', html)
        self.assertNotIn("data-node-link", html)


class BuildSpaceNodeTests(SimpleTestCase):
    """Nodes are PROJECTS joined to layout, and nothing else."""

    def nodes(self):
        return views._build_space_nodes()

    def test_every_project_becomes_a_node(self):
        slugs = [n["slug"] for n in self.nodes()]
        self.assertEqual(slugs, [p["slug"] for p in content.PROJECTS])

    def test_there_are_no_nodes_for_projects_that_do_not_exist(self):
        known = {p["slug"] for p in content.PROJECTS}
        for node in self.nodes():
            with self.subTest(node=node["slug"]):
                self.assertIn(node["slug"], known)

    def test_node_links_resolve_to_real_routes(self):
        for node in self.nodes():
            with self.subTest(node=node["slug"]):
                self.assertEqual(
                    node["url"], reverse("project_detail", args=[node["slug"]])
                )

    def test_facts_come_from_projects_not_from_layout(self):
        by_slug = {p["slug"]: p for p in content.PROJECTS}
        for node in self.nodes():
            with self.subTest(node=node["slug"]):
                project = by_slug[node["slug"]]
                self.assertEqual(node["name"], project["name"])
                self.assertEqual(node["kind"], project["kind"])
                self.assertEqual(node["status"], project["status"])

    def test_every_node_is_placed_and_tiered(self):
        for node in self.nodes():
            with self.subTest(node=node["slug"]):
                self.assertIsInstance(node["x"], (int, float))
                self.assertIsInstance(node["y"], (int, float))
                self.assertIn(node["tier"], ("primary", "secondary"))

    def test_the_current_work_carries_the_most_weight(self):
        """Composition decision, asserted so a later edit cannot quietly undo it."""
        primary = {n["slug"] for n in self.nodes() if n["tier"] == "primary"}
        self.assertEqual(primary, {"quanta", "spendwise", "sync"})

    def test_coordinates_stay_inside_the_stage(self):
        for node in self.nodes():
            with self.subTest(node=node["slug"]):
                self.assertTrue(0 <= node["x"] <= 100, node["x"])
                self.assertTrue(0 <= node["y"] <= 100, node["y"])

    def test_no_node_sits_under_the_identity(self):
        """The name is the anchor; a node printed over it would fight it."""
        for node in self.nodes():
            if 30 <= node["x"] <= 70:
                with self.subTest(node=node["slug"]):
                    self.assertFalse(
                        38 <= node["y"] <= 62,
                        f"{node['slug']} sits inside the identity block",
                    )

    def test_a_project_with_no_coordinate_is_still_placed(self):
        """An unplaced project is a layout oversight, not a reason to vanish."""
        extra = dict(content.PROJECTS[0], slug="unplaced", name="Unplaced")
        with patch.object(content, "PROJECTS", list(content.PROJECTS) + [extra]):
            nodes = views._build_space_nodes()
        placed = next(n for n in nodes if n["slug"] == "unplaced")
        self.assertIsNotNone(placed["x"])
        self.assertIsNotNone(placed["y"])

    def test_engineering_detail_only_where_it_was_verified(self):
        """A project with no record must not be given one."""
        with with_unverified():
            thin = next(n for n in views._build_space_nodes()
                        if n["slug"] == UNVERIFIED["slug"])
        self.assertFalse(thin["has_engineering"])
        self.assertEqual(thin["stack"], [])
        self.assertEqual(thin["stack_groups"], [])
        self.assertEqual(thin["satellites"], [])

    def test_every_real_project_now_has_a_verified_record(self):
        """The notice is a branch, not a description of the content."""
        missing = [p["slug"] for p in content.PROJECTS if not p.get("engineering")]
        self.assertEqual(missing, [])

    def test_satellites_come_from_a_projects_own_architecture(self):
        rbad = next(n for n in self.nodes() if n["slug"] == "rbad")
        by_slug = {p["slug"]: p for p in content.PROJECTS}
        real = {
            n["label"]
            for n in by_slug["rbad"]["engineering"]["architecture"]["nodes"]
        }
        for satellite in rbad["satellites"]:
            with self.subTest(satellite=satellite["label"]):
                self.assertIn(satellite["label"], real)

    def test_payload_per_node_stays_lean(self):
        """Eight of these ship in the HTML on every visit."""
        for node in self.nodes():
            with self.subTest(node=node["slug"]):
                self.assertLessEqual(len(node["tech"]), 4)
                self.assertLessEqual(len(node["stack"]), 5)
                self.assertLessEqual(len(node["satellites"]), 4)


class BuildSpaceLinkTests(SimpleTestCase):
    def test_links_resolve_to_drawable_coordinates(self):
        nodes = views._build_space_nodes()
        links = views._build_space_links(nodes)
        self.assertEqual(len(links), len(layout.CONNECTIONS))
        for link in links:
            with self.subTest(link=(link["source"], link["target"])):
                for key in ("x1", "y1", "x2", "y2"):
                    self.assertIsInstance(link[key], (int, float))

    def test_links_only_reference_the_core_or_a_real_project(self):
        known = {p["slug"] for p in content.PROJECTS} | {"core"}
        for source, target in layout.CONNECTIONS:
            with self.subTest(link=(source, target)):
                self.assertIn(source, known)
                self.assertIn(target, known)

    def test_a_link_to_a_missing_project_is_dropped_not_drawn_wrong(self):
        nodes = [n for n in views._build_space_nodes() if n["slug"] != "quanta"]
        links = views._build_space_links(nodes)
        for link in links:
            with self.subTest(link=(link["source"], link["target"])):
                self.assertNotIn("quanta", (link["source"], link["target"]))


class BuildSpaceMarkupTests(RenderMixin, SimpleTestCase):
    def html_build(self, path="/"):
        with BUILD:
            return self.html(path)

    def stage(self, path="/"):
        """Just the Build Space section.

        The legacy deck still renders below it with its own lens blocks and
        its own videos, so a page-wide count would be measuring both and
        passing or failing for the wrong reason.
        """
        html = self.html_build(path)
        start = html.index('<section class="build"')
        return html[start:html.index("</section>", start)]

    def test_the_name_is_the_page_heading_not_a_node(self):
        html = self.html_build()
        self.assertIn('class="build__name"', html)
        self.assertIn("<h1", html)
        # The identity is outside the node list entirely.
        nodes = html.split('class="build__nodes"')[1]
        self.assertNotIn("build__name", nodes)

    def test_every_node_is_a_real_link_not_a_click_handler(self):
        html = self.html_build()
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                self.assertIn(f'href="{reverse("project_detail", args=[p["slug"]])}"', html)

    def test_nodes_are_a_list_with_an_accessible_name(self):
        html = self.html_build()
        self.assertIn('<ul class="build__nodes"', html)
        self.assertIn("aria-label=\"Projects.", html)

    def test_each_node_describes_itself_for_assistive_tech(self):
        html = self.html_build()
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                self.assertIn(f'aria-describedby="node-detail-{p["slug"]}"', html)
                self.assertIn(f'id="node-detail-{p["slug"]}"', html)

    def test_project_names_and_purposes_are_in_the_markup(self):
        """Understandable with no motion, no JavaScript and no pointer."""
        html = self.html_build()
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                self.assertIn(p["name"], html)
                self.assertIn(p["kind"], html)

    def test_both_lenses_are_present_per_node(self):
        """Every node carries both lenses, in the node itself and in its panel.

        Counts rather than an exact number per node: Phase 6B added at-rest
        lens content (a product thumbnail, the stack, the satellites) so a
        node now holds several blocks per lens, and the point of the assertion
        is that neither lens is ever missing.
        """
        stage = self.stage()
        for lens in ("experience", "engineering"):
            with self.subTest(lens=lens):
                self.assertGreaterEqual(
                    stage.count(f'data-lens="{lens}"'), len(content.PROJECTS)
                )

    def test_engineering_reads_at_rest_not_only_on_hover(self):
        """The audit scored the old lens 2/10 because the only at-rest change
        was the wire dash. The stack now renders in the node itself."""
        stage = self.stage()
        # Every node gets the block; what goes in it depends on the record.
        self.assertEqual(stage.count('class="build__stack mono"'), len(content.PROJECTS))
        # And it is the real stack, not a placeholder.
        verified = [p for p in content.PROJECTS
                    if (p.get("engineering") or {}).get("stack")]
        self.assertGreaterEqual(len(verified), 1)
        first = verified[0]["engineering"]["stack"][0]["name"]
        self.assertIn(f"<i>{first}</i>", stage)

    def test_a_project_without_an_engineering_record_says_so(self):
        stage = self.stage()
        missing = [p for p in content.PROJECTS if not p.get("engineering")]
        self.assertEqual(stage.count("build__unknown"), len(missing))

    def test_only_the_lead_work_carries_a_thumbnail(self):
        stage = self.stage()
        primary = [s for s, p in layout.POSITIONS.items() if p["tier"] == "primary"]
        self.assertEqual(stage.count("build__thumb"), len(primary))

    def test_engineering_mode_renders_valid_markup(self):
        html = self.html_build("/?mode=engineering")
        self.assertIn('data-mode="engineering"', html)
        self.assertEqual(html.count("data-node-link"), len(content.PROJECTS))

    def test_experience_mode_renders_valid_markup(self):
        html = self.html_build("/")
        self.assertIn('data-mode="experience"', html)
        self.assertEqual(html.count("data-node-link"), len(content.PROJECTS))

    def node_markup(self, stage, slug):
        """One node's markup, from its detail panel to the next node.

        Not split on </li>: the chip lists inside a panel close their own list
        items, so that would cut the panel off at the first chip.
        """
        start = stage.index(f'id="node-detail-{slug}"')
        nxt = stage.find('<li class="build__node', start)
        return stage[start:nxt if nxt != -1 else len(stage)]

    def test_a_project_without_engineering_says_so_rather_than_inventing(self):
        with with_unverified():
            panel = self.node_markup(self.stage(), UNVERIFIED["slug"])
        self.assertIn("No engineering record published", panel)
        self.assertNotIn("build__satellites", panel)

    def test_a_project_with_engineering_shows_it_instead_of_the_notice(self):
        panel = self.node_markup(self.stage(), "rbad")
        self.assertIn("build__satellites", panel)
        self.assertNotIn("No engineering record published", panel)

    def test_media_references_resolve_under_manifest_storage(self):
        """The same 500-not-a-broken-image hazard as every other surface."""
        html = self.html_build()
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                if p.get("video"):
                    self.assertIn(staticfiles_storage.url(p["video"] + ".mp4"), html)
                elif p.get("image"):
                    self.assertIn(staticfiles_storage.url(p["image"] + ".jpg"), html)

    def test_videos_do_not_preload_or_autoplay_together(self):
        """Eight previews arriving at once is the payload risk here.

        Scoped to the stage: the deck below uses preload="metadata", which is
        right for it and wrong here, where nothing should be fetched until a
        project is actually opened.
        """
        for tag in re.findall(r"<video[^>]*>", self.stage()):
            with self.subTest(tag=tag[:60]):
                self.assertIn('preload="none"', tag)
                self.assertNotIn("autoplay", tag)
                self.assertIn("muted", tag)
                self.assertIn("playsinline", tag)

    def test_node_links_carry_the_mode(self):
        html = self.html_build("/?mode=engineering")
        for p in content.PROJECTS:
            with self.subTest(project=p["slug"]):
                self.assertIn(f'/work/{p["slug"]}/?mode=engineering', html)


class BuildSpaceCoexistenceTests(RenderMixin, SimpleTestCase):
    """Everything that existed before must survive the new landing."""

    def html_build(self, path="/"):
        with BUILD:
            return self.html(path)

    def test_contact_form_is_untouched(self):
        html = self.html_build()
        self.assertIn('id="contact-form"', html)
        for field in ("name", "email", "subject", "message"):
            with self.subTest(field=field):
                self.assertIn(f'name="{field}"', html)
        self.assertIn("csrfmiddlewaretoken", html)

    def test_command_palette_is_still_there(self):
        html = self.html_build()
        self.assertIn('id="palette"', html)
        self.assertIn("data-palette-open", html)

    def test_mode_switch_is_still_there(self):
        html = self.html_build()
        self.assertEqual(html.count("data-mode-set"), 2)

    def test_the_pinned_deck_is_not_rendered_under_the_constellation(self):
        """The Build Space has a work section, but not the deck.

        The deck spends 5.9 viewport-heights showing eight panels one at a
        time, which is the wrong shape under a landing that has already shown
        all eight at once. The index below it shows the same projects to read.
        """
        html = self.html_build()
        self.assertNotIn("data-deck-panel", html)
        self.assertIn('id="work"', html)
        self.assertIn('class="index"', html)

    def test_each_project_appears_once_in_the_index(self):
        """Once in the index. It also appears once as a node above, which is
        the point of the pair: the same project discovered on the map and
        then read in the list, both from one PROJECTS entry."""
        html = self.html_build()
        start = html.index('<ol class="index__list')
        index = html[start:html.index("</ol>", start)]
        for project in content.PROJECTS:
            with self.subTest(project=project["slug"]):
                url = reverse("project_detail", args=[project["slug"]])
                self.assertEqual(index.count(f'href="{url}"'), 1)

    def test_every_project_reaches_the_index(self):
        html = self.html_build()
        self.assertEqual(html.count("index__item"), len(content.PROJECTS))

    def test_the_deck_partial_is_kept_and_still_works_on_legacy(self):
        """Switched off, not deleted: the legacy landing is unchanged."""
        html = self.html_legacy("/")
        self.assertEqual(html.count("data-deck-panel"), len(content.PROJECTS))
        self.assertIn('id="work"', html)
        self.assertNotIn('class="index"', html)

    def test_navigation_rail_is_still_there(self):
        html = self.html_build()
        self.assertIn('class="rail"', html)
        # Work exists again, so the rail offers all three sections.
        for slug in ("about", "work", "contact"):
            with self.subTest(section=slug):
                self.assertIn(f'href="/#{slug}"', html)

    def test_the_index_does_not_invent_scroll_distance(self):
        """No second pinned surface: the section is as tall as its content."""
        with open(CSS_DIR / "work.css", encoding="utf-8") as handle:
            css = re.sub(r"/\*.*?\*/", "", handle.read(), flags=re.S)
        index = css[css.index(".index {"):]
        self.assertNotIn("position: sticky", index)
        self.assertNotRegex(index, r"height:\s*\d{3,}vh")

    def test_project_routes_are_unaffected_by_the_landing(self):
        with BUILD:
            for p in content.PROJECTS:
                with self.subTest(project=p["slug"]):
                    url = reverse("project_detail", args=[p["slug"]])
                    self.assertEqual(self.get(url).status_code, 200)

    def test_legacy_redirects_are_unaffected(self):
        with BUILD:
            response = self.get("/projects/")
        self.assertEqual(response.status_code, 301)


class BuildSpaceSourceContractTests(SimpleTestCase):
    """Contracts the browser cannot be asked about in a server test."""

    @staticmethod
    def js():
        with open(JS_DIR / "build.js", encoding="utf-8") as handle:
            return handle.read()

    @staticmethod
    def css():
        with open(CSS_DIR / "build.css", encoding="utf-8") as handle:
            return handle.read()

    def test_no_client_router(self):
        script = self.js()
        self.assertNotIn("pushState", script)
        self.assertNotIn("preventDefault()", script.replace("e.preventDefault();", ""))

    def test_mode_and_motion_are_consumed_not_reimplemented(self):
        script = self.js()
        self.assertIn("JE", script)
        self.assertNotIn("localStorage", script)
        self.assertNotIn("data-mode-set", script)

    def test_reduced_motion_is_honoured(self):
        script = self.js()
        self.assertIn("reduced()", script)
        css = self.css()
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn("prefers-reduced-motion: no-preference", css)

    @staticmethod
    def _declarations(css):
        """CSS with comments stripped.

        The sheet explains in prose why backdrop-filter is not used here, and
        a naive substring search reads that explanation as a use of it.
        """
        return re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    def test_no_webgl_canvas_or_backdrop_filter(self):
        """Renderer-freeze history: none of these belong on this surface."""
        declarations = self._declarations(self.css())
        script = self.js()
        for banned in ("backdrop-filter", "will-change"):
            with self.subTest(property=banned):
                self.assertNotIn(banned, declarations)
        for banned in ("getContext", "WebGL", "THREE"):
            with self.subTest(api=banned):
                self.assertNotIn(banned, script)

    def test_scroll_anchoring_is_disabled_on_the_stage(self):
        """Content changing above the fold has caused jumps here before."""
        self.assertIn("overflow-anchor: none", self.css())

    def test_the_stage_does_not_invent_scroll_distance(self):
        """No second 590vh deck: the page continues normally underneath."""
        heights = [int(v) for v in re.findall(r"height:\s*(\d+)vh",
                                              self._declarations(self.css()))]
        self.assertTrue(heights, "expected the stage to declare a height")
        self.assertLessEqual(max(heights), 100, f"viewport heights found: {heights}")

    def test_mobile_gets_a_different_layout_not_a_smaller_one(self):
        css = self.css()
        self.assertIn("max-width: 60rem", css)
        # The constellation's absolute positioning is undone, not shrunk.
        mobile = css.split("max-width: 60rem")[1]
        self.assertIn("position: static", mobile)

    def test_colours_come_from_tokens(self):
        css = self.css()
        # The phone frame's body is the one deliberate literal, as elsewhere.
        literals = [c for c in re.findall(r"#[0-9a-fA-F]{3,8}", css)
                    if c.lower() not in ("#17161a", "#000", "#2f9e5f")]
        self.assertEqual(literals, [], f"unexpected literal colours: {literals}")

    def test_build_styles_stay_in_the_build_sheet(self):
        """Nothing Build Space-specific leaks into the other stylesheets."""
        for sheet in ("foundation.css", "chrome.css", "work.css", "contact.css"):
            with self.subTest(sheet=sheet):
                with open(CSS_DIR / sheet, encoding="utf-8") as handle:
                    self.assertNotIn(".build__", handle.read())


class BarPointerContractTests(SimpleTestCase):
    """The rules that make the top bar's controls clickable with a mouse.

    Background: `.bar` is deliberately transparent to the pointer so the fixed
    header never blocks the page scrolling underneath it. For several phases
    only `.bar__mark` and `.bar__meta` opted back in by name, so the mode
    switch and the palette trigger — both added to the bar later — inherited
    `pointer-events: none` and could not be clicked at all. Every server test
    passed throughout, because `pointer-events` blocks hit-testing only:
    focus, keyboard activation and `element.click()` all still worked.

    These assert the shape of the fix rather than the symptom. A hit test is
    the real check and lives in tools/hittest.js, which needs a browser; this
    is what can be enforced without one.
    """

    @staticmethod
    def css():
        with open(CSS_DIR / "chrome.css", encoding="utf-8") as handle:
            return re.sub(r"/\*.*?\*/", "", handle.read(), flags=re.S)

    def test_the_bar_is_still_click_through(self):
        """The behaviour being worked around is intentional and still wanted."""
        self.assertRegex(self.css(), r"\.bar\s*\{[^}]*pointer-events:\s*none")

    def test_bar_children_opt_back_in_as_a_group(self):
        """Not an allow-list: the previous one silently dropped two controls."""
        self.assertRegex(
            self.css(),
            r"\.bar__inner\s*>\s*\*\s*\{[^}]*pointer-events:\s*auto",
        )

    def test_no_control_relies_on_being_named_individually(self):
        """A named exemption is the pattern that failed; keep it out."""
        css = self.css()
        for control in (".modes", ".palette-trigger", ".bar__mark"):
            with self.subTest(control=control):
                self.assertNotRegex(
                    css,
                    re.escape(control) + r"[^{]*\{[^}]*pointer-events:\s*auto",
                )

    def test_every_bar_control_is_a_direct_child_of_bar_inner(self):
        """The group selector only covers direct children, so this is the
        condition that makes it sufficient."""
        template = get_template("pages/partials/nav.html").template.source
        header = template.split("</header>")[0]
        inner = header.split('class="shell bar__inner"')[1]
        # Each control opens at the top level of .bar__inner rather than being
        # wrapped in an extra div that would break the > * selector.
        for control in ("palette-trigger", 'class="modes"', "bar__mark"):
            with self.subTest(control=control):
                self.assertIn(control, inner)


class BuildSpacePanelPlacementTests(SimpleTestCase):
    """Corner placement of the hover preview.

    build.js writes a space-separated edge value, so a node in the bottom
    right carries `data-edge="right bottom"`. Exact-match selectors never fire
    for that value, which left the one case needing both flips getting neither
    and clipped the panel off the viewport.
    """

    @staticmethod
    def css():
        with open(CSS_DIR / "build.css", encoding="utf-8") as handle:
            return handle.read()

    @staticmethod
    def js():
        with open(JS_DIR / "build.js", encoding="utf-8") as handle:
            return handle.read()

    def test_edge_flags_are_matched_as_a_token_list(self):
        css = self.css()
        for edge in ("right", "bottom"):
            with self.subTest(edge=edge):
                self.assertIn(f'[data-edge~="{edge}"]', css)
                self.assertNotIn(f'[data-edge="{edge}"]', css)

    def test_placement_clamps_as_well_as_flips(self):
        """A flip is a guess that there is room; the clamp is the guarantee."""
        script = self.js()
        self.assertIn("--shift-x", script)
        self.assertIn("--shift-y", script)
        self.assertIn("Math.min(Math.max(", script)

    def test_the_clamp_survives_reduced_motion(self):
        """Dropping the entrance offset must not drop the correction with it."""
        css = self.css()
        # The exact string, so this anchors on the desktop block rather than
        # the mobile one, whose condition reads "... and (prefers-...)".
        reduced = css.split("@media (prefers-reduced-motion: reduce)")[1]
        rule = reduced[reduced.index(".build__detail"):]
        rule = rule[:rule.index("}")]
        self.assertIn("--shift-x", rule)
        self.assertIn("--shift-y", rule)

    def test_measurements_avoid_in_flight_transforms(self):
        """offsetWidth/offsetHeight are transform-free; a rect is not, and a
        correction still animating would otherwise feed the next one."""
        script = self.js()
        self.assertIn("panel.offsetWidth", script)
        self.assertIn("panel.offsetHeight", script)


class BuildSpaceModeLinkTests(RenderMixin, SimpleTestCase):
    """Node links keep the current lens even when it came from storage.

    The server stamps `?mode=` onto these hrefs only when it saw the parameter
    in the URL. When the lens was restored from localStorage instead, the
    server rendered plain paths, so following a node dropped the reader back
    into Experience.
    """

    def html_build(self, path="/"):
        with BUILD:
            return self.html(path)

    def test_node_links_expose_their_bare_route(self):
        html = self.html_build("/?mode=engineering")
        for slug in ("quanta", "sync"):
            with self.subTest(slug=slug):
                self.assertIn(f'data-path="/work/{slug}/"', html)

    def test_href_still_carries_the_mode_without_javascript(self):
        html = self.html_build("/?mode=engineering")
        self.assertIn('href="/work/quanta/?mode=engineering"', html)

    def test_default_mode_leaves_urls_clean(self):
        html = self.html_build("/")
        self.assertIn('data-path="/work/quanta/"', html)

    def test_the_client_restamps_through_the_shared_mode_api(self):
        """Not by appending a parameter itself: there is one implementation
        of what a URL looks like in a given mode."""
        with open(JS_DIR / "build.js", encoding="utf-8") as handle:
            script = handle.read()
        self.assertIn("mode.urlFor", script)
        self.assertIn("dataset.path", script)


class BuildSpaceCompositionTests(SimpleTestCase):
    """Phase 6B composition contracts.

    The visual result is checked in a browser; these pin the decisions that a
    later edit could silently undo, and the reasoning behind each one.
    """

    @staticmethod
    def css():
        with open(CSS_DIR / "build.css", encoding="utf-8") as handle:
            return handle.read()

    def test_the_name_is_never_capped_below_the_old_hero(self):
        """The 5rem short-viewport cap rendered 80px on a 1366x768 laptop,
        smaller than the hero it replaced. Height belongs in the clamp."""
        css = self.css()
        self.assertIn("min(10.5vw, 17vh)", css)
        self.assertNotIn("clamp(2.5rem, 6vw, 5rem)", css)

    def test_short_viewports_give_up_copy_before_scale(self):
        css = self.css()
        short = css.split("max-height: 60rem")[1]
        self.assertIn(".build__lede { display: none; }", short)
        # And no font-size override of the name anywhere in a height query.
        for block in css.split("max-height:")[1:]:
            with self.subTest(block=block[:12]):
                head = block[: block.index("\n}")] if "\n}" in block else block
                self.assertNotIn(".build__name { font-size", head)

    def test_the_coordinate_space_excludes_the_chrome(self):
        """Percentages in layout.py mean the usable field, not the section."""
        css = self.css()
        self.assertIn("top: calc(var(--bar-h) - 0.5rem)", css)

    def test_tiers_separate_on_more_than_size(self):
        css = self.css()
        # Secondary labels are set in a lighter ink than primary ones.
        self.assertIn(".build__project {", css)
        block = css.split(".build__project {")[1].split("}")[0]
        self.assertIn("color: var(--ink-soft)", block)
        primary = css.split(".build__node--primary .build__project {")[1].split("}")[0]
        self.assertIn("color: var(--ink)", primary)

    def test_engineering_changes_the_environment_not_just_the_wires(self):
        """The audit scored the lens 2/10 when the dash was the only change."""
        css = self.css()
        for selector in (
            '[data-mode="engineering"] .build__grid',
            '[data-mode="engineering"] .build__wire[data-tier="primary"]',
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, css)

    def test_the_field_has_a_ground(self):
        css = self.css()
        self.assertIn(".build__grid", css)
        self.assertIn("mask-image", css)


class BuildSpaceCoreClearanceTests(SimpleTestCase):
    """Connections stop at the identity instead of meeting inside it."""

    def links(self):
        return views._build_space_links(views._build_space_nodes())

    def test_core_endpoints_are_pulled_back_to_the_boundary(self):
        core = layout.CORE
        for link in self.links():
            if link["source"] != "core":
                continue
            with self.subTest(target=link["target"]):
                self.assertNotEqual((link["x1"], link["y1"]), (core["x"], core["y"]))

    def test_every_core_endpoint_lands_on_the_same_ellipse(self):
        core, clear = layout.CORE, layout.CORE_CLEARANCE
        for link in self.links():
            if link["source"] != "core":
                continue
            with self.subTest(target=link["target"]):
                dx = (link["x1"] - core["x"]) / clear["x"]
                dy = (link["y1"] - core["y"]) / clear["y"]
                self.assertAlmostEqual((dx * dx + dy * dy) ** 0.5, 1.0, places=2)

    def test_node_endpoints_are_untouched(self):
        nodes = {n["slug"]: n for n in views._build_space_nodes()}
        for link in self.links():
            if link["source"] == "core":
                continue
            with self.subTest(source=link["source"]):
                self.assertEqual(link["x1"], nodes[link["source"]]["x"])

    def test_a_node_on_the_core_does_not_divide_by_zero(self):
        core = {"x": 50, "y": 50}
        self.assertEqual(views._clear_core(core, dict(core)), core)

    def test_connections_carry_the_weight_of_the_heavier_end(self):
        tiers = {link["tier"] for link in self.links()}
        self.assertEqual(tiers, {"primary", "secondary"})
        for link in self.links():
            if link["source"] == "core":
                with self.subTest(target=link["target"]):
                    self.assertEqual(link["tier"], "primary")


class LandingIsolationTests(RenderMixin, SimpleTestCase):
    """Switching the landing must not reach the legacy page."""

    def test_legacy_still_has_hero_deck_and_full_nav(self):
        html = self.html_legacy("/")
        self.assertIn('class="hero"', html)
        self.assertIn('id="work"', html)
        self.assertIn('href="/#work"', html)
        self.assertEqual(html.count("data-deck-panel"), len(content.PROJECTS))

    def test_legacy_never_renders_build_space_markup(self):
        html = self.html_legacy("/")
        for marker in ("data-build", "build__node", "build__grid"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, html)

    def test_the_build_landing_only_changes_shared_nav_on_project_pages(self):
        """A project page's own content is landing-independent.

        The rail and the palette are shared furniture and do follow the
        landing — offering a "Work" jump to a section the home page no longer
        has would be a link to nowhere — but nothing inside the case study
        itself may move.
        """
        def case(html):
            start = html.index('<article class="case')
            body = html[start:html.index("</article>", start)]
            # The one legitimate difference: "all work" points at whichever
            # section holds the work on that landing.
            return body.replace('href="/#top"', 'href="/#work"')

        plain = self.html("/work/sync/")
        with BUILD:
            switched = self.html("/work/sync/")

        self.assertEqual(case(plain), case(switched))

    def test_case_studies_link_back_to_the_work_on_both_landings(self):
        """Both landings have a #work section, so the anchor is the same."""
        plain = self.html("/work/sync/")
        self.assertIn('href="/#work"', plain)

        with BUILD:
            switched = self.html("/work/sync/")
        self.assertIn('href="/#work"', switched)


class BuildSpaceStackingTests(SimpleTestCase):
    """The active-state stacking model.

    Previews used to render behind the identity. .build__nodes is a stacking
    context, so a z-index on a preview inside it could never lift the preview
    past the name however large it was — the layer has to move, not the panel.
    """

    @staticmethod
    def css():
        with open(CSS_DIR / "build.css", encoding="utf-8") as handle:
            return handle.read()

    def test_the_node_layer_rises_above_the_identity_when_active(self):
        css = self.css()
        self.assertIn("[data-build].has-active .build__nodes { z-index: 4; }", css)
        identity = css.split(".build__identity {")[1].split("}")[0]
        self.assertIn("z-index: 3", identity)

    def test_the_open_node_sits_above_its_neighbours(self):
        self.assertIn(".build__node.is-active { z-index: 1; }", self.css())

    def test_the_identity_recedes_but_does_not_vanish(self):
        css = self.css()
        block = css.split("[data-build].has-active .build__identity {")[1].split("}")[0]
        opacity = float(re.search(r"opacity:\s*([\d.]+)", block).group(1))
        self.assertGreater(opacity, 0, "the name must stay visible")
        self.assertLess(opacity, 0.6, "and must clearly step back")

    def test_motion_is_expressed_in_shared_tokens(self):
        """One vocabulary, not a duration per rule."""
        css = self.css()
        for token in ("--b-ease", "--b-quick", "--b-base", "--b-slow", "--b-hold"):
            with self.subTest(token=token):
                self.assertIn(token, css)
        # No stray hardcoded transition durations left behind.
        declarations = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        strays = re.findall(r"transition:[^;]*?\b0\.\d+s", declarations)
        self.assertEqual(strays, [], f"un-tokenised transitions: {strays}")

    def test_reduced_motion_keeps_the_centring_transform(self):
        """A node's transform is its centring; only `translate` is its drift.
        Clearing the transform moved every node by half its own box."""
        css = self.css()
        # The exact string, so this anchors on the desktop block rather than
        # the mobile one, whose condition reads "... and (prefers-...)".
        reduced = css.split("@media (prefers-reduced-motion: reduce)")[1]
        rule = reduced.split(".build__node {")[1].split("}")[0]
        self.assertIn("translate: none", rule)
        self.assertNotIn("transform: none", rule)


class WorkIndexTests(RenderMixin, SimpleTestCase):
    """The calm half of the pair, under the Build Space."""

    def html_build(self, path="/"):
        with BUILD:
            return self.html(path)

    def test_every_project_is_present_with_a_case_study_link(self):
        html = self.html_build()
        for project in content.PROJECTS:
            with self.subTest(project=project["slug"]):
                url = reverse("project_detail", args=[project["slug"]])
                self.assertIn(f'href="{url}"', html)

    def test_both_lenses_are_served(self):
        html = self.html_build()
        index = html[html.index('<section class="index"'):]
        self.assertIn('data-lens="experience"', index)
        self.assertIn('data-lens="engineering"', index)

    def test_engineering_shows_the_verified_stack_with_layers(self):
        html = self.html_build()
        self.assertIn('data-layer="backend"', html)

    def test_a_project_without_a_record_says_so_rather_than_inventing_one(self):
        html = self.html_build()
        missing = [p for p in content.PROJECTS if not p.get("engineering")]
        self.assertEqual(html.count("entry__none"), len(missing))

    def test_media_comes_from_the_shared_partial(self):
        """Not a second copy of the media branch."""
        with open(_ROOT / "pages" / "templates" / "pages" / "partials"
                  / "work_index.html", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("pages/partials/project/media.html", source)
        self.assertNotIn("<video", source)

    def test_index_media_is_lazy_and_keeps_its_controls(self):
        html = self.html_build()
        index = html[html.index('<section class="index"'):]
        self.assertIn('loading="lazy"', index)
        # Standalone media keeps native controls; only the deck suppresses them.
        self.assertIn("controls", index)

    def test_the_reveal_never_hides_content_it_cannot_show(self):
        with open(JS_DIR / "site.js", encoding="utf-8") as handle:
            script = handle.read()
        # The hidden state is opted into by the script, not by markup.
        self.assertIn("is-revealing", script)
        # And there is a net if the observer never reports.
        self.assertIn("setTimeout", script)


class BuildSpaceCueTests(RenderMixin, SimpleTestCase):
    """The scroll cue names its destination instead of describing the page."""

    def html_build(self):
        with BUILD:
            return self.html("/")

    def test_the_cue_points_at_the_work(self):
        html = self.html_build()
        self.assertIn('class="build__cue mono" href="#work"', html)

    def test_the_placeholder_copy_is_gone(self):
        self.assertNotIn("More below", self.html_build())

    def test_the_cue_carries_the_project_count(self):
        html = self.html_build()
        self.assertIn(
            f'<b class="build__cue-count">{len(content.PROJECTS)}</b>', html
        )


class WorkIndexVideoTests(SimpleTestCase):
    """Selected Work clips play as they scroll past.

    The Build Space hero and the legacy deck drive their own clips; this must
    not reach either of them.
    """

    @staticmethod
    def js():
        with open(JS_DIR / "site.js", encoding="utf-8") as handle:
            return handle.read()

    def test_playback_is_scoped_to_the_index(self):
        script = self.js()
        self.assertIn(".index__item video", script)
        # Not the hero's clips, and not the deck's.
        self.assertNotIn("data-build-video", script)
        self.assertNotIn("data-deck-video", script)

    def test_it_uses_an_observer_not_a_scroll_handler(self):
        script = self.js()
        block = script.split("function indexVideo()")[1]
        self.assertIn("IntersectionObserver", block)
        self.assertNotIn("addEventListener('scroll'", block)

    def test_a_meaningful_share_must_be_visible(self):
        """A strip at the edge of the viewport must not start a clip."""
        script = self.js()
        threshold = float(re.search(r"var PLAY_AT = ([\d.]+);", script).group(1))
        self.assertGreaterEqual(threshold, 0.5)
        self.assertLess(threshold, 1.0)

    def test_autoplay_conditions_are_asserted(self):
        script = self.js()
        block = script.split("function indexVideo()")[1]
        self.assertIn("el.muted = true", block)
        self.assertIn("el.playsInline = true", block)

    def test_a_rejected_play_does_not_throw(self):
        block = self.js().split("function indexVideo()")[1]
        self.assertIn("started.catch", block)

    def test_reduced_motion_leaves_the_clips_alone(self):
        block = self.js().split("function indexVideo()")[1]
        self.assertIn("if (reduced ||", block)

    def test_rewinding_is_separate_from_pausing(self):
        """Pausing happens at the edge; rewinding only well out of view."""
        block = self.js().split("function indexVideo()")[1]
        self.assertIn("rootMargin: '150% 0px 150% 0px'", block)
        self.assertIn("currentTime = 0", block)

    def test_only_one_clip_can_run(self):
        block = self.js().split("function indexVideo()")[1]
        # Enforced for automatic playback...
        self.assertIn("if (s.ratio >= PLAY_AT && (!best || s.ratio > best.ratio))", block)
        # ...and for a clip started by hand from the native controls.
        self.assertIn("addEventListener('play'", block)


class WorkIndexMediaContractTests(RenderMixin, SimpleTestCase):
    """What the markup has to provide for the above to work at all."""

    def html_build(self):
        with BUILD:
            return self.html("/")

    def index(self):
        html = self.html_build()
        start = html.index('<ol class="index__list')
        return html[start:html.index("</ol>", start)]

    def test_clips_are_autoplay_eligible_and_keep_their_controls(self):
        index = self.index()
        for video in re.findall(r"<video[^>]*>", index):
            with self.subTest(video=video[:60]):
                self.assertIn("muted", video)
                self.assertIn("playsinline", video)
                self.assertIn("controls", video)

    def test_clips_are_not_preloaded_aggressively(self):
        index = self.index()
        for video in re.findall(r"<video[^>]*>", index):
            with self.subTest(video=video[:60]):
                self.assertIn('preload="metadata"', video)
                self.assertNotIn('preload="auto"', video)

    def test_the_hero_still_loads_nothing_until_opened(self):
        """The Build Space is unchanged by this."""
        html = self.html_build()
        stage = html[html.index('<section class="build"'):html.index('<ol class="index__list')]
        for video in re.findall(r"<video[^>]*>", stage):
            with self.subTest(video=video[:60]):
                self.assertIn('preload="none"', video)
                self.assertNotIn("controls", video)


class BuildSpaceTrackTests(SimpleTestCase):
    """The phone layout is a swipeable track, not a shrunken constellation."""

    @staticmethod
    def css():
        with open(CSS_DIR / "build.css", encoding="utf-8") as handle:
            return handle.read()

    @staticmethod
    def js():
        with open(JS_DIR / "build.js", encoding="utf-8") as handle:
            return handle.read()

    def mobile_block(self):
        css = self.css()
        start = css.index("@media (max-width: 60rem)")
        return css[start:css.index("\n}", css.index(".build__cue-rule", start))]

    def test_the_track_snaps_natively(self):
        """The gesture belongs to the browser; the script only reads it."""
        block = self.mobile_block()
        self.assertIn("scroll-snap-type: x mandatory", block)
        # Start, not centre: a card rests against the gutter with the next one
        # showing past it, so the strip's position reads at a glance.
        self.assertIn("scroll-snap-align: start", block)
        self.assertIn("scroll-padding-inline: var(--gutter)", block)
        self.assertIn("overflow-x: auto", block)

    def test_a_swipe_off_the_end_cannot_become_a_page_gesture(self):
        self.assertIn("overscroll-behavior-x: contain", self.mobile_block())

    def test_the_peek_is_derived_so_it_is_identical_on_every_card(self):
        block = self.mobile_block()
        self.assertIn("--card: calc(100vw - var(--gutter) - var(--gap) - var(--peek))", block)
        # Trailing padding is exactly gap + peek, which is what lets the last
        # card rest against the same gutter as the first.
        self.assertIn("padding-inline: var(--gutter) calc(var(--gap) + var(--peek))", block)
        self.assertIn("opacity: 0.55", block)

    def test_every_card_is_the_same_width(self):
        """A strip whose cards differ in width slides against itself and reads
        as scattered rather than as one moving piece."""
        self.assertIn(".build__node--secondary { flex-basis: var(--card); }",
                      self.mobile_block())

    def test_no_per_card_scaling(self):
        """Focus changes weight, not geometry, so the track moves as one."""
        block = self.mobile_block()
        self.assertNotIn("transform: scale", block)

    def test_the_card_orders_media_name_facts(self):
        block = self.mobile_block()
        # display:contents lets the wrapper's children order themselves.
        self.assertIn("display: contents", block)
        for part, order in (("media", "1"), ("hit", "2"), ("facts", "3")):
            with self.subTest(part=part):
                self.assertRegex(block, rf"\.build__{part}\s*{{ order: {order}; }}")

    def test_engineering_changes_the_card_not_only_its_text(self):
        block = self.mobile_block()
        eng = block[block.index('[data-mode="engineering"]'):]
        self.assertIn("background: var(--paper-sunk)", eng)
        self.assertIn("border-bottom-style: dashed", eng)

    def test_the_breakpoint_is_defined_once(self):
        """The script reads the layout the stylesheet produced rather than
        repeating its breakpoint, so the two cannot drift apart."""
        script = self.js()
        self.assertIn("getComputedStyle(nodeLayer).overflowX === 'auto'", script)
        self.assertNotIn("60rem", script)

    def test_the_track_has_a_position_indicator(self):
        self.assertIn(".build__tick.is-on", self.mobile_block())
        self.assertIn("markTick", self.js())

    def test_a_neighbour_tap_focuses_and_the_focused_tap_navigates(self):
        script = self.js()
        block = script[script.index("if (onTrack() && active !== node)"):]
        self.assertIn("preventDefault", block[:400])
        self.assertIn("inline: 'center'", block[:400])

    def test_a_clip_interrupted_by_a_swipe_is_not_marked_blocked(self):
        """Moving on pauses the clip, which rejects its own play promise."""
        script = self.js()
        self.assertIn("if (active === node) node.setAttribute('data-clip', 'blocked')", script)

    def test_reduced_motion_keeps_the_track_usable(self):
        css = self.css()
        block = css[css.index("@media (max-width: 60rem) and (prefers-reduced-motion: reduce)"):]
        self.assertIn("transform: none", block)


class BuildSpaceTrackMarkupTests(RenderMixin, SimpleTestCase):
    def stage(self):
        with BUILD:
            html = self.html("/")
        start = html.index('<section class="build"')
        return html[start:html.index("</section>", start)]

    def test_one_tick_per_project(self):
        stage = self.stage()
        self.assertEqual(stage.count("data-tick="), len(content.PROJECTS))

    def test_the_indicator_is_decorative_not_a_second_list(self):
        """The track is the list a screen reader walks."""
        stage = self.stage()
        ticks = stage[stage.index('class="build__ticks"'):]
        ticks = ticks[:ticks.index("</div>")]
        self.assertIn('aria-hidden="true"', stage[stage.index("build__ticks") - 120:])
        self.assertNotIn("<a", ticks)

    def test_the_cards_are_still_the_same_real_links(self):
        stage = self.stage()
        self.assertEqual(stage.count("data-node-link"), len(content.PROJECTS))


class BuildSpaceTrackOffsetTests(SimpleTestCase):
    """The strip must not inherit the constellation's coordinates.

    Nodes carry left/top from --nx/--ny for the plotted layout. `static`
    ignores them; `relative` turns them into offsets from the flow position,
    which displaced every card by its desktop x-coordinate and made the track
    look scattered rather than stepped.
    """

    def test_the_card_clears_the_plotted_coordinates(self):
        with open(CSS_DIR / "build.css", encoding="utf-8") as handle:
            css = handle.read()
        block = css[css.index("@media (max-width: 60rem)"):]
        card = block[block.index(".build__node {"):]
        card = card[:card.index("\n  }")]
        self.assertIn("position: relative", card)
        # left/top become relative offsets...
        self.assertIn("inset: auto", card)
        # ...and the centring transform lifts the card above the section,
        # where overflow:hidden clips it out of reach.
        self.assertIn("transform: none", card)

    def mobile_build_rule(self, declarations_only=False):
        with open(CSS_DIR / "build.css", encoding="utf-8") as handle:
            css = handle.read()
        rule = css_rule(css[css.index("@media (max-width: 60rem)"):], ".build")
        # The prose explains why 100vh is not used, which a naive substring
        # search reads as a use of it.
        return re.sub(r"/\*.*?\*/", "", rule, flags=re.S) if declarations_only else rule

    def test_the_hero_uses_safe_area_insets(self):
        build = self.mobile_build_rule()
        self.assertIn("env(safe-area-inset-top, 0px)", build)
        self.assertIn("env(safe-area-inset-bottom, 0px)", build)

    def test_the_hero_grows_rather_than_clipping(self):
        """No viewport unit: 100vh on iOS reserves space the URL bar is using,
        and the hero is as tall as its content anyway."""
        build = self.mobile_build_rule(declarations_only=True)
        self.assertIn("min-height: 0", build)
        self.assertNotIn("100vh", build)


class PreloaderIndependenceTests(SimpleTestCase):
    """The preloader must not depend on the hero to dismiss itself.

    It used to bail out entirely without one, which is why the Build Space
    shipped without a loading layer: turning it on would have left a
    full-viewport overlay with nothing to take it away.
    """

    @staticmethod
    def js():
        with open(JS_DIR / "intro.js", encoding="utf-8") as handle:
            return handle.read()

    def test_only_the_loading_layer_is_required(self):
        script = self.js()
        self.assertIn("if (!pre) return;", script)
        self.assertNotIn("if (!hero || !out) return;", script)

    def test_the_typing_half_is_gated_on_having_a_hero(self):
        script = self.js()
        self.assertIn("var hasIntro = !!(hero && out);", script)
        self.assertIn("if (finished || !hasIntro) return;", script)

    def test_reveal_survives_a_landing_with_no_hero(self):
        """It still clears intro-pending, which is what shows the page."""
        script = self.js()
        reveal = script[script.index("function reveal()"):]
        reveal = reveal[:reveal.index("\n  }")]
        self.assertIn("root.classList.remove('intro-pending')", reveal)
        self.assertIn("if (!hero) return;", reveal)
        # The class must come off before the guard, or a heroless landing
        # would stay hidden behind the preloader's own styling.
        self.assertLess(reveal.index("intro-pending"), reveal.index("if (!hero)"))

    def test_nothing_on_a_heroless_page_is_hidden_while_pending(self):
        """Every intro-pending rule that hides something is scoped to .hero."""
        with open(CSS_DIR / "intro.css", encoding="utf-8") as handle:
            css = re.sub(r"/\*.*?\*/", "", handle.read(), flags=re.S)
        for line in css.splitlines():
            if "intro-pending" not in line:
                continue
            with self.subTest(rule=line.strip()[:60]):
                self.assertTrue(
                    ".hero" in line or ".pre" in line,
                    "an unscoped intro-pending rule would hide a heroless landing",
                )
