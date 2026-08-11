"""Site content as plain data.

Everything on the page that isn't layout lives here, so the templates stay
markup and the same project can't drift between two places the way the old
home/projects pair did. No model, since nothing here needs admin editing.
"""

PROFILE = {
    "name": "Joseph Edward",
    "first": "Joseph",
    "last": "Edward",
    "role": "Full-stack web & mobile engineer",
    "location": "Lagos, Nigeria",
    "email": "josephedward201@gmail.com",
    "phone_display": "+234 902 596 7499",
    "phone_tel": "+2349025967499",
    "whatsapp": "https://wa.me/2349025967499",
    "available": "Available for contract work and remote opportunities",
}

NAV = [
    {"index": "01", "slug": "about", "label": "About"},
    {"index": "02", "slug": "work", "label": "Work"},
    {"index": "03", "slug": "contact", "label": "Contact"},
]

SOCIALS = [
    {"label": "GitHub", "short": "GH", "url": "https://github.com/zazajo"},
    {
        "label": "LinkedIn",
        "short": "LI",
        "url": "https://www.linkedin.com/in/joseph-edward-94b7a3322",
    },
    {"label": "X", "short": "X", "url": "https://x.com/wblja3y"},
]

# Read as a single paragraph flow in the about section.
ABOUT = [
    "I’m a full-stack web and mobile engineer focused on building secure, "
    "scalable products for startups and businesses.",
    "I work mainly with Python and Django on the backend, and Next.js, "
    "React Native and Expo for web and mobile experiences.",
    "I’ve built and shipped production systems including ticketing platforms "
    "with payment integrations, e-commerce platforms, referral-based "
    "applications, marketing websites, financial applications and AI-powered "
    "applications.",
]

ABOUT_CLOSE = (
    "What matters most to me is clean architecture, getting things done "
    "efficiently, and building products that solve real problems."
)

HELP_WITH = [
    "Django & Django REST Framework applications",
    "REST APIs and backend architecture",
    "Authentication & user management",
    "Payment integrations (Paystack, Flutterwave)",
    "Next.js web applications",
    "React Native & Expo mobile applications",
    "MVP development for startups",
    "Third-party API integrations",
]

STACK = [
    {"name": "Python", "note": "core"},
    {"name": "Django", "note": "DRF"},
    {"name": "PostgreSQL", "note": "data"},
    {"name": "Next.js", "note": "web"},
    {"name": "React Native", "note": "mobile"},
    {"name": "Expo", "note": "mobile"},
    {"name": "TypeScript", "note": "web"},
    {"name": "Tailwind", "note": "ui"},
]

# Each project may carry "repos": a list of {label, url}. Crownie has one per
# build, so this is a list rather than a single URL. An empty list renders no
# source link at all, so a half-filled entry never ships a dead link.
PROJECTS = [
    {
        "slug": "vaultor",
        "name": "Vaultor",
        "kind": "Solana presale platform",
        "year": "2025",
        "role": "Full-stack",
        "summary": (
            "The Genesis presale platform for a perception-first prediction "
            "product. Solana wallet authentication with signature verification "
            "on the backend, a Django REST API, and a Next.js front end."
        ),
        "features": [
            "Solana wallet auth with server-side signature checks",
            "Presale flow with referral tracking",
            "Django REST API with generated schema docs",
            "Roadmap, updates, FAQ and document management",
        ],
        "tech": ["Django", "DRF", "PostgreSQL", "Next.js", "TypeScript", "Solana"],
        "image": "images/vaultor",
        "image_alt": "The Vaultor prediction market platform",
        # The apex redirects to www, so link www directly and skip the hop.
        "links": [{"label": "Visit site", "url": "https://www.vaultor.org"}],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/vaultor"}],
        "status": "live",
    },
    {
        "slug": "marketbrainers",
        "name": "MarketBrainers",
        "kind": "Marketing agency platform",
        "year": "2024 to present",
        "role": "Lead developer",
        "summary": (
            "A marketing agency’s full digital presence. Service showcase, "
            "client portal, and a CMS the team runs themselves, with lead "
            "capture wired through the contact flow."
        ),
        "features": [
            "Full CMS for content and blog posts",
            "Client portal with project tracking",
            "SEO-oriented service pages and case studies",
            "Contact form integration with lead capture",
        ],
        "tech": ["Django", "Python", "PostgreSQL", "CMS", "SEO"],
        "image": "images/marketbrainers",
        "image_alt": "The MarketBrainers marketing agency website",
        "links": [{"label": "Visit site", "url": "https://www.marketbrainer.org"}],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/marketbrainers"}],
        "status": "live",
    },
    {
        "slug": "crownie",
        "name": "Crownie",
        "kind": "Coin launch platform",
        "year": "2024",
        "role": "Full-stack",
        "summary": (
            "A cryptocurrency launch platform built twice, on two stacks. "
            "Django for the backend architecture and admin, Next.js for the "
            "modern frontend take on the same product."
        ),
        "features": [
            "Authentication and user management",
            "Referral system with tracked invites",
            "Discord API integration",
            "Analytics dashboard",
        ],
        "tech": ["Django", "Next.js", "React", "TypeScript", "PostgreSQL", "Discord API"],
        "image": "images/crownie-nextjs",
        "image_alt": "The Crownie coin launch platform",
        "links": [
            # No www: the apex domain is the only one that resolves.
            {"label": "Django build", "url": "https://crownieverse.xyz"},
            {"label": "Next.js build", "url": "https://crownie-landing-gilt.vercel.app/"},
        ],
        "repos": [
            {"label": "Django source", "url": "https://github.com/zazajo/crw-landing"},
            {"label": "Next.js source", "url": "https://github.com/zazajo/crownie-landing"},
        ],
        "status": "live",
    },
]
