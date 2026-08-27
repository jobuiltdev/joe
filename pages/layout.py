"""Spatial composition for the Build Space.

Presentation, not fact. Everything here is an art-direction decision about
where a node sits and how much weight it carries, and none of it belongs in
content.py: a coordinate is not a property of a project the way its stack is.
Keeping the two apart means the engineering record stays something that can be
verified against a repository, and this stays something that can be moved
around until it looks right.

Coordinates are percentages of the stage. The identity block occupies roughly
x 28-72, y 38-62, so nodes stay out of that band; the composition is built
around the name rather than the name being dropped into a field of nodes.

Tiers drive size, opacity and how close a node sits to the centre:

    primary    current work, nearest the name, largest
    secondary  earlier work, further out, quieter but plainly legible

Any project missing from POSITIONS still renders. It is placed on a ring by
the template rather than vanishing, because a project with no coordinate is a
layout oversight and hiding it would be the wrong failure.
"""

# Phase 6B moved four of these. The arrangement was composed around an 80px
# name; once the identity was restored to the size the brief actually calls
# for, measurement at 581/660/768/900px showed its glyphs overlapping
# SpendWise, Sync, Vaultor and RBAD at every one of those heights. The
# quadrants and the relationships are unchanged — each node moved outward
# along the axis it was already on, opening the centre band the name needs.
POSITIONS = {
    # Primary: the three current products, largest and nearest the name.
    "quanta":         {"x": 18, "y": 24, "tier": "primary"},
    "spendwise":      {"x": 88, "y": 22, "tier": "primary"},
    "sync":           {"x": 29, "y": 84, "tier": "primary"},

    # Secondary: earlier work, further out, still plainly reachable.
    "vaultor":        {"x": 64, "y": 83, "tier": "secondary"},
    "rbad":           {"x": 87, "y": 62, "tier": "secondary"},
    "crownie":        {"x": 12, "y": 48, "tier": "secondary"},
    "spooky":         {"x": 47, "y": 11, "tier": "secondary"},
    "marketbrainers": {"x": 70, "y": 10, "tier": "secondary"},
}

# Where a project with no entry above goes: spread around a wide ring so an
# unplaced node is visible and clickable rather than stacked at the origin.
FALLBACK_RING = {"radius": 44, "tier": "secondary"}

# Drawn connections. Each is a pair of slugs, or "core" for the identity at the
# centre. Chosen for composition rather than derived: these are the lines that
# make the arrangement read as one structure instead of scattered points.
#
# Engineering Mode strengthens these and adds satellites from each project's
# own verified architecture; it does not invent new relationships here.
CONNECTIONS = [
    ("core", "quanta"),
    ("core", "spendwise"),
    ("core", "sync"),
    ("quanta", "spooky"),
    ("quanta", "crownie"),
    ("spendwise", "marketbrainers"),
    ("spendwise", "rbad"),
    ("sync", "crownie"),
    ("sync", "vaultor"),
    ("vaultor", "rbad"),
]

# The identity sits at the centre of the stage and is not a node.
CORE = {"x": 50, "y": 50}

# How far short of the core a connection stops, as percentage radii of an
# ellipse around the identity block.
#
# Drawn all the way to CORE, every "core" line converged on a single point in
# the middle of a word and the wires appeared to emanate from inside the name.
# Stopping them at the identity's boundary makes the name read as the thing
# they connect to, which is what it is. Wider than it is tall because the name
# is a wide two-line block, and because x and y here are percentages of a
# stage that is not square.
CORE_CLEARANCE = {"x": 22, "y": 17}
