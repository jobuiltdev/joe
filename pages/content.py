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

# Projects carry shared facts once, then two lenses over them.
#
#   shared      slug, name, kind, year, role, status, media, links, repos, tech.
#               True regardless of which lens is showing.
#   experience  what it is and what it does, in product language.
#   engineering how it is built. Structured, not one prose block, so a
#               renderer can draw it rather than print it.
#
# "tech" is the product-facing headline stack and is what the work panel's
# chips render. "engineering.stack" is the verified implementation, read from
# each project's own dependency manifest. They are allowed to disagree: the
# chips are copy, the engineering block is a claim about the code. Where they
# differ today it is recorded in the Phase 1 report, not reconciled by
# quietly editing one to match the other.
#
# Everything inside "engineering" is optional, including "engineering" itself.
# A consumer must branch on each key it wants, the same way the media block in
# work.html branches: under manifest static storage a missing file raises
# rather than degrading, and the same intolerance applies to half-filled data.
# An absent key means "not recorded", never "none" or "zero".
#
# "architecture" is a graph, deliberately, so a future renderer can lay out any
# project without knowing which project it is:
#     nodes  {"id", "label", "kind", "tech"?, "note"?}
#     edges  {"from", "to", "label"?}   ids must match nodes
# node kind is one of: client | service | datastore | external
#
# "stack" entries are {"name", "layer"} where layer is one of:
#     client | backend | data | infra | integration
#
# Every engineering value below is read from that project's own repository:
# dependency manifests, application layout, deployment descriptors, or the
# running deployment. Nothing is inferred from intent, and nothing is carried
# over from a project README where the README disagrees with the manifest. A
# key that is absent is absent because it was not verified.
PROJECTS = [
    {
        "slug": "quanta",
        "name": "Quanta",
        "kind": "Adaptive learning workspace",
        "year": "2026",
        "role": "Full-stack",
        "status": "in development",
        "tech": ["Django", "DRF", "PostgreSQL", "Expo", "React Native", "TypeScript"],
        "video": "video/quanta-demo",
        "media_alt": "Screen recording of the Quanta learning app",
        "links": [],
        # Private repository, so no source link.
        "repos": [],
        "experience": {
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
        },
        "engineering": {
            "overview": (
                "A monorepo split into a Django REST backend and an Expo client. "
                "The backend is divided into thirteen domain apps rather than one "
                "large application, behind a single versioned API root."
            ),
            "stack": [
                {"name": "Django 6.0", "layer": "backend"},
                {"name": "DRF 3.17", "layer": "backend"},
                {"name": "Simple JWT", "layer": "backend"},
                {"name": "drf-spectacular", "layer": "backend"},
                {"name": "PostgreSQL (psycopg 3)", "layer": "data"},
                {"name": "Gunicorn", "layer": "infra"},
                {"name": "Expo", "layer": "client"},
                {"name": "React Native", "layer": "client"},
                {"name": "NativeWind", "layer": "client"},
                {"name": "Zustand", "layer": "client"},
                {"name": "React Query", "layer": "client"},
                {"name": "Zod", "layer": "client"},
            ],
            "architecture": {
                "summary": (
                    "One client, one versioned API surface, and domain apps that "
                    "own their own slice of the schema."
                ),
                "nodes": [
                    {"id": "app", "label": "Expo client", "kind": "client",
                     "tech": ["Expo Router", "React Query", "Zustand", "NativeWind"]},
                    {"id": "api", "label": "Versioned REST API", "kind": "service",
                     "tech": ["DRF", "drf-spectacular"]},
                    {"id": "accounts", "label": "Accounts", "kind": "service"},
                    {"id": "profiles", "label": "Profiles", "kind": "service"},
                    {"id": "learning", "label": "Learning", "kind": "service"},
                    {"id": "documents", "label": "Documents", "kind": "service",
                     "tech": ["pypdf", "python-docx"],
                     "note": "Extracts content from uploaded PDF and Word files"},
                    {"id": "knowledge", "label": "Knowledge", "kind": "service"},
                    {"id": "quizzes", "label": "Quizzes", "kind": "service"},
                    {"id": "tutor", "label": "Tutor", "kind": "service"},
                    {"id": "intelligence", "label": "Intelligence", "kind": "service"},
                    {"id": "progress", "label": "Progress", "kind": "service"},
                    {"id": "replay", "label": "Replay", "kind": "service"},
                    {"id": "twin", "label": "Twin", "kind": "service"},
                    {"id": "subscriptions", "label": "Subscriptions", "kind": "service"},
                    {"id": "dashboard", "label": "Dashboard", "kind": "service"},
                    {"id": "db", "label": "PostgreSQL", "kind": "datastore"},
                    {"id": "llm", "label": "Anthropic and OpenAI", "kind": "external"},
                ],
                "edges": [
                    {"from": "app", "to": "api", "label": "HTTPS"},
                    {"from": "api", "to": "accounts"},
                    {"from": "api", "to": "profiles"},
                    {"from": "api", "to": "learning"},
                    {"from": "api", "to": "documents"},
                    {"from": "api", "to": "knowledge"},
                    {"from": "api", "to": "quizzes"},
                    {"from": "api", "to": "tutor"},
                    {"from": "api", "to": "intelligence"},
                    {"from": "api", "to": "progress"},
                    {"from": "api", "to": "replay"},
                    {"from": "api", "to": "twin"},
                    {"from": "api", "to": "subscriptions"},
                    {"from": "api", "to": "dashboard"},
                    {"from": "tutor", "to": "llm"},
                    {"from": "intelligence", "to": "llm"},
                    {"from": "api", "to": "db"},
                ],
            },
            "api": {
                "style": "REST",
                "notes": [
                    "Versioned URL root with shared pagination and error envelope",
                    "Schema and documentation generated by drf-spectacular",
                ],
                "endpoints": [
                    {"method": "GET", "path": "/api/v1/health/", "note": "Health check"},
                    {"method": "GET", "path": "/api/docs/", "note": "Generated API documentation"},
                ],
            },
            "data": {
                "engine": "PostgreSQL",
                "notes": ["Accessed through psycopg 3"],
            },
            "auth": {
                "method": "JSON Web Tokens",
                "notes": ["Simple JWT, with identity owned by the accounts app"],
            },
            "integrations": [
                {"name": "Anthropic API", "purpose": "Model access for the tutor and generated study material"},
                {"name": "OpenAI API", "purpose": "Model access for the tutor and generated study material"},
            ],
            "testing": {
                "notes": [
                    "Dedicated backend test package",
                    "Separate development requirements file",
                ],
            },
            "infra": {
                "notes": ["Served by Gunicorn"],
            },
            "decisions": [
                {
                    "choice": "Split settings into base, development and production",
                    "rationale": "Keeps deploy-specific configuration out of the shared base",
                },
                {
                    "choice": "One versioned API root rather than per-app URL trees",
                    "rationale": "Pagination and the error envelope are defined once for every endpoint",
                },
                {
                    "choice": "Two model providers rather than one",
                    "rationale": "Neither vendor is a single point of failure for the tutor",
                },
            ],
        },
    },
    {
        "slug": "spendwise",
        "name": "SpendWise",
        "kind": "Personal finance app",
        "year": "2026",
        "role": "Full-stack",
        "status": "in development",
        "tech": ["Django", "DRF", "PostgreSQL", "Expo", "React Native", "TypeScript"],
        "video": "video/spendwise-demo",
        "media_alt": "Screen recording of the SpendWise finance app",
        "links": [],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/spendwise"}],
        "experience": {
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
        },
        "engineering": {
            "overview": (
                "A Django REST backend paired with an Expo client, with the auth "
                "flow designed so the app can reach its home screen without a "
                "second round trip after registering or signing in."
            ),
            "stack": [
                {"name": "Django 4.2", "layer": "backend"},
                {"name": "DRF 3.16", "layer": "backend"},
                {"name": "Simple JWT", "layer": "backend"},
                {"name": "django-filter", "layer": "backend"},
                {"name": "django-environ", "layer": "backend"},
                {"name": "Expo 54", "layer": "client"},
                {"name": "React Native 0.81", "layer": "client"},
                {"name": "React Query", "layer": "client"},
                {"name": "React Hook Form", "layer": "client"},
                {"name": "Zod", "layer": "client"},
            ],
            "architecture": {
                "nodes": [
                    {"id": "app", "label": "Expo client", "kind": "client",
                     "tech": ["Expo Router", "React Query", "React Hook Form", "Zod"]},
                    {"id": "api", "label": "Django REST API", "kind": "service",
                     "tech": ["DRF", "Simple JWT", "django-filter"]},
                ],
                "edges": [
                    {"from": "app", "to": "api", "label": "HTTPS, bearer token"},
                ],
            },
            "api": {
                "style": "REST",
                "notes": [
                    "Register and login both return the token pair plus the user, "
                    "so the client can skip a follow-up profile request",
                ],
                "endpoints": [
                    {"method": "POST", "path": "/api/register/", "note": "Returns user plus token pair"},
                    {"method": "POST", "path": "/api/token/", "note": "Login, returns token pair plus full profile"},
                    {"method": "POST", "path": "/api/token/refresh/", "note": "Rotates the refresh token"},
                    {"method": "POST", "path": "/api/token/logout/", "note": "Blacklists the refresh token"},
                    {"method": "GET", "path": "/api/users/me/", "note": "Current user profile"},
                ],
            },
            "auth": {
                "method": "JSON Web Tokens",
                "notes": [
                    "Bearer tokens via Simple JWT rather than DRF's plain token auth",
                    "Refresh tokens rotate on every use and the spent one is blacklisted",
                    "A stolen refresh token is good for a single refresh before it is dead",
                ],
            },
            "decisions": [
                {
                    "choice": "Rotate and blacklist refresh tokens on every use",
                    "rationale": "Caps the damage from a stolen refresh token at one refresh",
                },
                {
                    "choice": "Return the user object alongside the token pair",
                    "rationale": "Removes a round trip on app startup and after registration",
                },
            ],
        },
    },
    {
        "slug": "sync",
        "name": "Sync",
        "kind": "On-demand services marketplace",
        "year": "2026",
        "role": "Full-stack",
        "status": "in development",
        "tech": ["Django", "DRF", "PostgreSQL", "Expo", "React Native", "OTP auth"],
        "video": "video/sync-demo",
        "media_alt": "Screen recording of the Sync services marketplace app",
        "links": [],
        # Private repository, so no source link.
        "repos": [],
        "experience": {
            "summary": (
                "A marketplace connecting customers with local providers for "
                "dispatch, cleaning, errands, home services, beauty and laundry. "
                "Two sides of the same app: customers book, providers onboard, "
                "set their areas and get paid."
            ),
            "features": [
                "Customer and provider roles in one Expo app",
                "Provider onboarding, verification and service areas",
                "Bookings with saved addresses and job tracking",
                "OTP authentication and payouts to bank accounts",
            ],
        },
        "engineering": {
            "overview": (
                "A two-sided marketplace where both roles share one Expo client "
                "against a Django REST backend split into seven apps. The only "
                "project here with a full test, typing and lint toolchain pinned "
                "alongside the runtime dependencies."
            ),
            "stack": [
                {"name": "Django 5.2", "layer": "backend"},
                {"name": "DRF 3.18", "layer": "backend"},
                {"name": "Simple JWT", "layer": "backend"},
                {"name": "drf-spectacular", "layer": "backend"},
                {"name": "Argon2", "layer": "backend"},
                {"name": "PostgreSQL (psycopg 3)", "layer": "data"},
                {"name": "Redis", "layer": "data"},
                {"name": "Celery", "layer": "backend"},
                {"name": "Gunicorn", "layer": "infra"},
                {"name": "Docker", "layer": "infra"},
                {"name": "Expo", "layer": "client"},
                {"name": "React Native", "layer": "client"},
                {"name": "React Native Maps", "layer": "client"},
                {"name": "Zustand", "layer": "client"},
                {"name": "React Query", "layer": "client"},
            ],
            "architecture": {
                "summary": (
                    "One client serving two roles, against a backend split by "
                    "marketplace concern, with background work on a queue."
                ),
                "nodes": [
                    {"id": "app", "label": "Expo client", "kind": "client",
                     "tech": ["Expo Router", "React Query", "Zustand", "React Native Maps"],
                     "note": "Customer and provider experiences in one binary"},
                    {"id": "api", "label": "Django REST API", "kind": "service",
                     "tech": ["DRF", "drf-spectacular"]},
                    {"id": "accounts", "label": "Accounts", "kind": "service",
                     "tech": ["Simple JWT", "Argon2", "phonenumbers"]},
                    {"id": "providers", "label": "Providers", "kind": "service"},
                    {"id": "catalog", "label": "Catalogue", "kind": "service"},
                    {"id": "bookings", "label": "Bookings", "kind": "service"},
                    {"id": "payments", "label": "Payments", "kind": "service"},
                    {"id": "notifications", "label": "Notifications", "kind": "service"},
                    {"id": "worker", "label": "Celery workers", "kind": "service"},
                    {"id": "redis", "label": "Redis", "kind": "datastore",
                     "note": "Broker for the task queue"},
                    {"id": "db", "label": "PostgreSQL", "kind": "datastore"},
                ],
                "edges": [
                    {"from": "app", "to": "api", "label": "HTTPS"},
                    {"from": "api", "to": "accounts"},
                    {"from": "api", "to": "providers"},
                    {"from": "api", "to": "catalog"},
                    {"from": "api", "to": "bookings"},
                    {"from": "api", "to": "payments"},
                    {"from": "api", "to": "notifications"},
                    {"from": "api", "to": "redis", "label": "Enqueue"},
                    {"from": "redis", "to": "worker"},
                    {"from": "worker", "to": "db"},
                    {"from": "api", "to": "db"},
                ],
            },
            "data": {
                "engine": "PostgreSQL",
                "notes": ["Accessed through psycopg 3", "Redis alongside it as the Celery broker"],
            },
            "auth": {
                "method": "JSON Web Tokens",
                "notes": [
                    "Simple JWT for session tokens",
                    "Argon2 password hashing rather than Django's default",
                    "Phone numbers parsed and validated with phonenumbers",
                ],
            },
            "testing": {
                "notes": [
                    "pytest with pytest-django and factory-boy",
                    "Coverage measured as part of the dev extra",
                    "Ruff for linting, mypy with django-stubs and DRF stubs for typing",
                ],
            },
            "infra": {
                "notes": [
                    "Dockerfile and a Docker Compose definition for local services",
                    "GitHub Actions workflows in the repository",
                    "Dependencies pinned exactly and verified together against one interpreter",
                    "Served by Gunicorn",
                ],
            },
            "decisions": [
                {
                    "choice": "Pin every dependency exactly and verify them as a set",
                    "rationale": "A marketplace taking payments cannot afford a surprise transitive upgrade",
                },
                {
                    "choice": "Argon2 instead of Django's default password hasher",
                    "rationale": "Memory-hard hashing is the current recommendation for stored credentials",
                },
                {
                    "choice": "Celery on Redis for work that must not block a request",
                    "rationale": "Notifications and payout processing are slow and retryable, so they leave the request cycle",
                },
            ],
        },
    },
    {
        "slug": "vaultor",
        "name": "Vaultor",
        "kind": "Solana presale platform",
        "year": "2025",
        "role": "Full-stack",
        "status": "live",
        "tech": ["Django", "DRF", "PostgreSQL", "Next.js", "TypeScript", "Solana"],
        "image": "images/vaultor",
        "media_alt": "The Vaultor prediction market platform",
        # The apex redirects to www, so link www directly and skip the hop.
        "links": [{"label": "Visit site", "url": "https://www.vaultor.org"}],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/vaultor"}],
        "experience": {
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
        },
        "engineering": {
            "overview": (
                "A Next.js front end against a Django REST backend, where the "
                "authentication boundary is a wallet signature the server verifies "
                "itself with Ed25519, not a password."
            ),
            "stack": [
                {"name": "Django 5.1", "layer": "backend"},
                {"name": "DRF", "layer": "backend"},
                {"name": "drf-spectacular", "layer": "backend"},
                {"name": "PyNaCl", "layer": "backend"},
                {"name": "base58", "layer": "backend"},
                {"name": "PostgreSQL (psycopg2)", "layer": "data"},
                {"name": "Gunicorn", "layer": "infra"},
                {"name": "WhiteNoise", "layer": "infra"},
                {"name": "Next.js", "layer": "client"},
                {"name": "Solana Wallet Adapter", "layer": "integration"},
                {"name": "solana/web3.js", "layer": "integration"},
            ],
            "architecture": {
                "nodes": [
                    {"id": "web", "label": "Next.js front end", "kind": "client",
                     "tech": ["Solana Wallet Adapter", "solana/web3.js", "Framer Motion", "Lenis"]},
                    {"id": "api", "label": "Django REST API", "kind": "service",
                     "tech": ["DRF", "drf-spectacular"]},
                    {"id": "accounts", "label": "Accounts", "kind": "service",
                     "tech": ["PyNaCl", "base58"],
                     "note": "Verifies the wallet signature server-side"},
                    {"id": "presale", "label": "Presale", "kind": "service"},
                    {"id": "documents", "label": "Documents", "kind": "service"},
                    {"id": "roadmap", "label": "Roadmap", "kind": "service"},
                    {"id": "updates", "label": "Updates", "kind": "service"},
                    {"id": "faq", "label": "FAQ", "kind": "service"},
                    {"id": "db", "label": "PostgreSQL", "kind": "datastore"},
                    {"id": "wallet", "label": "Solana wallet", "kind": "external"},
                ],
                "edges": [
                    {"from": "web", "to": "wallet", "label": "Sign"},
                    {"from": "web", "to": "api", "label": "HTTPS"},
                    {"from": "api", "to": "accounts"},
                    {"from": "api", "to": "presale"},
                    {"from": "api", "to": "documents"},
                    {"from": "api", "to": "roadmap"},
                    {"from": "api", "to": "updates"},
                    {"from": "api", "to": "faq"},
                    {"from": "api", "to": "db"},
                ],
            },
            "api": {
                "style": "REST",
                "notes": ["Schema and documentation generated by drf-spectacular"],
            },
            "data": {
                "engine": "PostgreSQL",
                "notes": ["Accessed through psycopg2, with the URL supplied by dj-database-url"],
            },
            "auth": {
                "method": "Solana wallet signature",
                "notes": [
                    "Ed25519 signatures verified on the server with PyNaCl",
                    "Wallet addresses decoded with base58",
                ],
            },
            "capabilities": [
                "Presale flow with referral attribution",
                "Roadmap, updates, FAQ and document management",
            ],
            "infra": {
                "notes": [
                    "Procfile process types, with migrate and collectstatic in the release phase",
                    "Gunicorn with three workers",
                    "Pinned to Python 3.12",
                ],
            },
            "decisions": [
                {
                    "choice": "Verify wallet signatures on the backend with PyNaCl",
                    "rationale": "A client-side check proves nothing to the server",
                },
                {
                    "choice": "Run migrations and collectstatic in the release phase",
                    "rationale": "A deploy that cannot migrate fails before it serves traffic",
                },
            ],
        },
    },
    {
        "slug": "marketbrainers",
        "name": "MarketBrainers",
        "kind": "Marketing agency platform",
        "year": "2024 to present",
        "role": "Lead developer",
        "status": "live",
        "tech": ["Django", "Python", "Django Templates", "Vanilla JavaScript", "SQLite"],
        "image": "images/marketbrainers",
        "media_alt": "The MarketBrainers marketing agency website",
        "links": [{"label": "Visit site", "url": "https://www.marketbrainer.org"}],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/marketbrainers"}],
        "experience": {
            "summary": (
                "The public face of a marketing agency: services, packages, "
                "platform coverage and client case studies, laid out across a "
                "responsive Django site. Enquiries reach the team directly "
                "from the contact page."
            ),
            "features": [
                "Service, package and platform pages built on one shared layout",
                "Ten client case studies presented as a portfolio",
                "Transparency, privacy and data-handling pages for compliance",
                "Direct contact page with a one-tap email CTA",
            ],
        },
        # Verified against github.com/zazajo/marketbrainers. Everything below is
        # read from requirements.txt, mb_site/settings.py, vercel.json, the core
        # app and the templates; nothing is taken from the repository README,
        # which claims PostgreSQL the settings do not use.
        "engineering": {
            "overview": (
                "A marketing site built as plain server-rendered Django. One "
                "app, core, serves fifteen routes through function views that "
                "render a template and pass a page title. There are no models "
                "and no migrations, so every page is authored markup rather "
                "than content read from a database."
            ),
            "stack": [
                {"name": "Django 4.2", "layer": "backend"},
                {"name": "Python 3.11", "layer": "backend"},
                {"name": "Django Templates", "layer": "client"},
                {"name": "Vanilla JavaScript", "layer": "client"},
                {"name": "Font Awesome 6.4", "layer": "client"},
                {"name": "SQLite", "layer": "data"},
                {"name": "WhiteNoise 6.11", "layer": "infra"},
                {"name": "Vercel (@vercel/python)", "layer": "infra"},
                # Last deliberately: the work index shows the first eight, so
                # the one that drops off should be the least load-bearing.
                # The Build Space panel groups by layer and still shows it.
                {"name": "Google Fonts", "layer": "client"},
            ],
            "architecture": {
                "summary": "One app, one base layout, no database reads.",
                "nodes": [
                    {"id": "core", "label": "core app", "kind": "service",
                     "tech": ["Django 4.2", "Function views"],
                     "note": "Fifteen routes, each rendering a template"},
                    {"id": "pages", "label": "Template pages", "kind": "client",
                     "tech": ["Django Templates", "Vanilla JavaScript"],
                     "note": "One base layout with title, extra-CSS and extra-JS blocks"},
                    {"id": "static", "label": "WhiteNoise", "kind": "service",
                     "note": "Serves the collected CSS, JavaScript and imagery"},
                    {"id": "sqlite", "label": "SQLite", "kind": "datastore",
                     "note": "Django's default connection; the app defines no models"},
                    {"id": "cdn", "label": "Font Awesome, Google Fonts", "kind": "external",
                     "note": "Icons and typefaces loaded per page"},
                ],
                "edges": [
                    {"from": "core", "to": "pages", "label": "Renders"},
                    {"from": "pages", "to": "static", "label": "CSS, JS, images"},
                    {"from": "pages", "to": "cdn", "label": "Icons and fonts"},
                    {"from": "core", "to": "sqlite", "label": "Configured, unused"},
                ],
            },
            "capabilities": [
                "Fifteen server-rendered routes from a single app",
                "One base layout with per-page title, extra-CSS and extra-JS blocks",
                "Service, package, platform and case-study pages authored as templates",
                "Six legal pages and an HTML sitemap page",
                "Hand-written CSS and vanilla JavaScript, no build step and no framework",
                "Contact page hands off to a mailto address: no form post, no form "
                "handling and no email backend",
            ],
            "data": (
                "SQLite is configured as Django's default connection, but core "
                "defines no models and ships no migrations, so nothing is read "
                "from it or written to it. MEDIA_URL and MEDIA_ROOT are set and "
                "unused; all imagery is static and committed."
            ),
            "infra": (
                "Deployed on Vercel through @vercel/python on the Python 3.11.3 "
                "runtime, serving mb_site/wsgi.py. Static files are collected "
                "into staticfiles/ and served by WhiteNoise middleware."
            ),
        },
    },
    {
        "slug": "rbad",
        "name": "RBAD",
        "kind": "Role-based admin dashboard",
        "year": "2026",
        "role": "Full-stack",
        "status": "live",
        "tech": ["Django", "DRF", "PostgreSQL", "Next.js", "TypeScript", "pandas"],
        # The permission matrix, since role-based access is the headline here
        # and this is the one view that shows it as working UI rather than a
        # claim. The audit timeline is the other candidate, currently too thin
        # to be worth the panel.
        "image": "images/rbad",
        "media_alt": "The RBAD dashboard showing a manager's permission matrix",
        # The repo's own homepage field points at a deployment that 404s; this
        # is the one that answers.
        "links": [
            {"label": "Visit site", "url": "https://admin-dashboard-main-nu.vercel.app"}
        ],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/admin-dashboard"}],
        "experience": {
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
        },
        "engineering": {
            "overview": (
                "A Next.js dashboard against a Django REST backend split into "
                "three apps: accounts, uploads and audit. Permissions are checked "
                "on the server and every mutation is written to the audit app."
            ),
            "stack": [
                {"name": "Django 4.2", "layer": "backend"},
                {"name": "DRF 3.14", "layer": "backend"},
                {"name": "Simple JWT", "layer": "backend"},
                {"name": "drf-yasg", "layer": "backend"},
                {"name": "pandas", "layer": "backend"},
                {"name": "OpenPyXL", "layer": "backend"},
                {"name": "PostgreSQL (psycopg2)", "layer": "data"},
                {"name": "Gunicorn", "layer": "infra"},
                {"name": "WhiteNoise", "layer": "infra"},
                {"name": "Next.js", "layer": "client"},
                {"name": "Axios", "layer": "client"},
            ],
            "architecture": {
                "summary": (
                    "A conventional client and API split, with ingestion and "
                    "auditing as their own apps rather than helpers."
                ),
                "nodes": [
                    {"id": "web", "label": "Next.js dashboard", "kind": "client",
                     "tech": ["Axios", "date-fns", "js-cookie", "Lucide"]},
                    {"id": "api", "label": "Django REST API", "kind": "service",
                     "tech": ["DRF", "Simple JWT", "drf-yasg"]},
                    {"id": "accounts", "label": "Accounts", "kind": "service",
                     "note": "Roles and per-capability permissions"},
                    {"id": "uploads", "label": "Uploads", "kind": "service",
                     "tech": ["pandas", "OpenPyXL", "NumPy"],
                     "note": "Row-by-row validation with per-row error reporting"},
                    {"id": "audit", "label": "Audit", "kind": "service",
                     "note": "Before and after values, attributed to a user"},
                    {"id": "db", "label": "PostgreSQL", "kind": "datastore"},
                ],
                "edges": [
                    {"from": "web", "to": "api", "label": "HTTPS, bearer token"},
                    {"from": "api", "to": "accounts"},
                    {"from": "api", "to": "uploads", "label": "CSV / Excel"},
                    {"from": "api", "to": "audit", "label": "Every mutation"},
                    {"from": "accounts", "to": "db"},
                    {"from": "uploads", "to": "db"},
                    {"from": "audit", "to": "db"},
                ],
            },
            "api": {
                "style": "REST",
                "notes": [
                    "Interactive schema documentation generated by drf-yasg",
                    "Cross-origin access handled by django-cors-headers",
                ],
            },
            "data": {
                "engine": "PostgreSQL",
                "notes": ["Accessed through psycopg2, with the URL supplied by dj-database-url"],
            },
            "auth": {
                "method": "JSON Web Tokens with role-based access control",
                "roles": ["Admin", "Manager", "Viewer"],
                "notes": [
                    "Simple JWT, with automatic refresh on the client",
                    "Granular per-capability permissions rather than role checks at the view",
                    "The public demo account is a Manager: upload, edit, export and "
                    "audit are allowed; managing users and deleting data are denied",
                ],
            },
            "integrations": [
                {"name": "pandas", "purpose": "Parsing and validating uploaded spreadsheets"},
                {"name": "OpenPyXL", "purpose": "Reading Excel workbooks"},
            ],
            "capabilities": [
                "CSV and Excel upload with drag and drop",
                "Row-by-row validation with detailed error reporting",
                "Upload history with a success rate per run",
                "Complete audit timeline with change attribution",
                "Bulk user activation and deactivation",
            ],
            "infra": {
                "hosting": ["Vercel (dashboard)"],
                "notes": [
                    "Procfile process types, with migrate and collectstatic in the release phase",
                    "Backend pinned to Python 3.11.10",
                ],
            },
            "decisions": [
                {
                    "choice": "Permissions expressed per capability rather than per role",
                    "rationale": "A role becomes a set of capabilities, so a new role needs no new checks",
                },
                {
                    "choice": "Record both the before and after value on every change",
                    "rationale": "An audit trail without the prior value cannot answer what actually changed",
                },
                {
                    "choice": "Auditing as its own app rather than a mixin",
                    "rationale": "Keeps the trail independent of the models being written to",
                },
            ],
        },
    },
    {
        "slug": "crownie",
        "name": "Crownie",
        "kind": "Coin launch platform",
        "year": "2024",
        "role": "Full-stack",
        "status": "live",
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
        "experience": {
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
        },
        "engineering": {
            "overview": (
                "The same product delivered as two separate repositories with no "
                "shared code: one Django application and one Next.js application, "
                "each deployed on its own."
            ),
            "stack": [
                {"name": "Django 4.2", "layer": "backend"},
                {"name": "DRF", "layer": "backend"},
                {"name": "discord.py", "layer": "integration"},
                {"name": "Redis", "layer": "data"},
                {"name": "Next.js", "layer": "client"},
                {"name": "React", "layer": "client"},
                {"name": "Recharts", "layer": "client"},
                {"name": "Framer Motion", "layer": "client"},
            ],
            "architecture": {
                "summary": "Two independent deployments of one product, not a shared backend.",
                "nodes": [
                    {"id": "django", "label": "Django build", "kind": "service",
                     "tech": ["DRF", "django-redis", "PyJWT"],
                     "note": "Backend architecture and admin"},
                    {"id": "next", "label": "Next.js build", "kind": "client",
                     "tech": ["React", "Recharts", "Framer Motion"],
                     "note": "Frontend-led take on the same product"},
                    {"id": "redis", "label": "Redis", "kind": "datastore",
                     "note": "Cache backend for the Django build"},
                    {"id": "discord", "label": "Discord", "kind": "external"},
                ],
                "edges": [
                    {"from": "django", "to": "discord", "label": "discord.py"},
                    {"from": "django", "to": "redis", "label": "Cache"},
                ],
            },
            "integrations": [
                {"name": "Discord", "purpose": "Community membership and engagement, via discord.py"},
                {"name": "Redis", "purpose": "Cache backend for the Django build"},
            ],
            "capabilities": [
                "Referral system with tracked invites",
                "Analytics dashboard charted with Recharts",
            ],
            "decisions": [
                {
                    "choice": "Rebuild the same product on a second stack",
                    "rationale": "Separated the backend and admin concerns from the frontend experience",
                },
            ],
        },
    },
    {
        "slug": "spooky",
        "name": "Spooky’s Y2K Rave",
        "kind": "Event ticketing platform",
        "year": "2025",
        "role": "Full-stack",
        "status": "live",
        "tech": ["Django", "Python", "Paystack", "PostgreSQL", "qrcode", "ReportLab"],
        # The ticket grid rather than the hero. The hero is event artwork with
        # the title over it, which says nothing about what was built; this
        # shows the tiers, prices and remaining stock.
        "image": "images/spooky",
        "media_alt": "The Spooky’s Y2K Rave ticket tiers with prices and remaining stock",
        "links": [{"label": "Visit site", "url": "https://pancakejo.pythonanywhere.com"}],
        "repos": [{"label": "Source", "url": "https://github.com/zazajo/spooky"}],
        "experience": {
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
        },
        "engineering": {
            "overview": (
                "A server-rendered Django application in two apps, where the money "
                "path is the critical one: payment confirmation is what mints a "
                "ticket, and the ticket is generated as a scannable document "
                "rather than a row in a table."
            ),
            "stack": [
                {"name": "Django 5.1", "layer": "backend"},
                {"name": "DRF 3.16", "layer": "backend"},
                {"name": "django-allauth", "layer": "backend"},
                {"name": "django-crispy-forms", "layer": "backend"},
                {"name": "paystackapi", "layer": "integration"},
                {"name": "qrcode", "layer": "backend"},
                {"name": "ReportLab", "layer": "backend"},
                {"name": "django-user-agents", "layer": "backend"},
            ],
            "architecture": {
                "nodes": [
                    {"id": "pages", "label": "Pages", "kind": "service",
                     "note": "Server-rendered event pages, no separate client"},
                    {"id": "tickets", "label": "Party tickets", "kind": "service",
                     "tech": ["qrcode", "ReportLab"],
                     "note": "Tiers, stock, and QR-coded PDF issuing"},
                    {"id": "paystack", "label": "Paystack", "kind": "external"},
                    {"id": "db", "label": "Database", "kind": "datastore"},
                ],
                "edges": [
                    {"from": "pages", "to": "tickets"},
                    {"from": "tickets", "to": "paystack", "label": "Checkout"},
                    {"from": "paystack", "to": "tickets", "label": "Payment confirmed"},
                    {"from": "tickets", "to": "db"},
                ],
            },
            "auth": {
                "method": "django-allauth",
                "notes": ["Registration and account handling delegated rather than hand-rolled"],
            },
            "integrations": [
                {"name": "Paystack", "purpose": "Card and transfer payments in Nigerian naira"},
            ],
            "capabilities": [
                "Ticket tiers with per-tier pricing and remaining stock",
                "QR-coded tickets generated as PDFs after payment",
                "Device and browser detection on requests",
            ],
            "data": {
                "notes": [
                    "The repository ships a SQLite database file and carries no "
                    "PostgreSQL driver, so the deployed store is unconfirmed",
                ],
            },
            "infra": {
                "hosting": ["PythonAnywhere"],
            },
            "decisions": [
                {
                    "choice": "Issue the ticket from the payment confirmation, not the checkout request",
                    "rationale": "An unpaid or abandoned checkout can never produce a valid ticket",
                },
            ],
        },
    },
]
