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

# Media on a panel is optional and comes in three shapes, checked in this
# order by the template: "video" (a portrait screen recording, for the mobile
# apps), then "image", then neither, which renders a typographic plate. Paths
# are extension-less: the template appends .mp4/.jpg for video and .webp/.jpg
# for images.
#
# "repos" is a list of {label, url}. Crownie has one per build, so a list
# rather than a single URL, and an empty list renders no source link at all.
# That matters for the private repos: a link a visitor can only 404 on is
# worse than no link.
#
# "status" is free text. Anything other than "live" is styled as in-progress
# rather than green.
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
        "media_alt": "The Vaultor prediction market platform",
        # The apex redirects to www, so link www directly and skip the hop.
        "links": [{"label": "Visit site", "url": "https://www.vaultor.org"}],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/vaultor"}],
        "status": "live",
    },
    {
        "slug": "quanta",
        "name": "Quanta",
        "kind": "Adaptive learning workspace",
        "year": "2026",
        "role": "Full-stack",
        "summary": (
            "An AI-assisted study app built as a Django REST API with an Expo "
            "client. It turns uploaded material into guided paths, schedules "
            "review from how well you actually recall a topic, and maps what "
            "you have learned as a memory constellation."
        ),
        "features": [
            "Guided study paths generated from uploaded documents",
            "Spaced repetition scheduled from recall performance",
            "AI tutor and generated quizzes per topic",
            "Versioned REST API with pagination and an error envelope",
        ],
        "tech": ["Django", "DRF", "PostgreSQL", "Expo", "React Native", "TypeScript"],
        "video": "video/quanta-demo",
        "media_alt": "Screen recording of the Quanta learning app",
        "links": [],
        # Private repository, so no source link.
        "repos": [],
        "status": "in development",
    },
    {
        "slug": "spendwise",
        "name": "SpendWise",
        "kind": "Personal finance app",
        "year": "2026",
        "role": "Full-stack",
        "summary": (
            "Expense tracking and budgeting as a Django REST API with an Expo "
            "client. It handles recurring transactions, splits group expenses "
            "between people, and settles up the balances that fall out of it."
        ),
        "features": [
            "JWT auth with rotating, blacklisted refresh tokens",
            "Budgets, recurring transactions and spending analysis",
            "Group expenses with flexible splitting and settlements",
            "Financial reports and data export",
        ],
        "tech": ["Django", "DRF", "PostgreSQL", "Expo", "React Native", "TypeScript"],
        "video": "video/spendwise-demo",
        "media_alt": "Screen recording of the SpendWise finance app",
        "links": [],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/spendwise"}],
        "status": "in development",
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
        "media_alt": "The MarketBrainers marketing agency website",
        "links": [{"label": "Visit site", "url": "https://www.marketbrainer.org"}],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/marketbrainers"}],
        "status": "live",
    },
    {
        "slug": "rbad",
        "name": "RBAD",
        "kind": "Role-based admin dashboard",
        "year": "2026",
        "role": "Full-stack",
        "summary": (
            "An administrative dashboard for teams that need to see who did "
            "what. Three roles with granular permissions, bulk data ingestion "
            "from spreadsheets, and an audit trail behind every change."
        ),
        "features": [
            "Role-based access control across admin, manager and viewer",
            "CSV and Excel upload with row-by-row validation",
            "Audit trail recording before and after values",
            "User management with bulk actions and filtered search",
        ],
        "tech": ["Django", "DRF", "PostgreSQL", "Next.js", "TypeScript", "pandas"],
        # Awaiting a screenshot, so the panel renders its typographic plate.
        "image": "",
        "media_alt": "The RBAD admin dashboard",
        # The repo's own homepage field points at a deployment that 404s; this
        # is the one that answers.
        "links": [
            {"label": "Visit site", "url": "https://admin-dashboard-main-nu.vercel.app"}
        ],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/admin-dashboard"}],
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
        "media_alt": "The Crownie coin launch platform",
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
    {
        "slug": "spooky",
        "name": "Spooky’s Y2K Rave",
        "kind": "Event ticketing platform",
        "year": "2025",
        "role": "Full-stack",
        "summary": (
            "Ticketing for a live rave, built to take real money on the night. "
            "Paystack handles checkout, and a successful payment issues a "
            "QR-coded ticket the door can scan."
        ),
        "features": [
            "Secure ticket purchase through Paystack",
            "QR-coded tickets generated as PDFs after payment",
            "Account handling and registration with allauth",
            "Responsive event pages for desktop and mobile",
        ],
        "tech": ["Django", "Python", "Paystack", "PostgreSQL", "qrcode", "ReportLab"],
        "image": "images/party-ticketing",
        "media_alt": "The Spooky’s Y2K Rave ticketing site",
        "links": [{"label": "Visit site", "url": "https://pancakejo.pythonanywhere.com"}],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/spooky"}],
        "status": "live",
    },
]
