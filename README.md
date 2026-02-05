💼 Joseph Edward - Full-Stack Developer Portfolio
A modern, responsive portfolio website showcasing my projects, skills, and experience as a Full-Stack Developer. Built with Django and styled with Tailwind CSS, featuring a sleek dark mode, smooth animations, and professional design.

Live demo: https://joewebs.vercel.app

🌟 Features

Modern UI/UX: Clean, professional design with smooth animations and transitions
Dark Mode: Toggle between light and dark themes with persistent preferences
Responsive Design: Fully optimized for desktop, tablet, and mobile devices
Project Showcase: Detailed project cards with live links and technology stacks
Contact Form: Integrated email functionality using Resend API
Professional Animations: Smooth page transitions and interactive elements
SEO Optimized: Structured for search engine visibility

🛠️ Tech Stack
Backend

Django 5.x - Python web framework
Python 3.10+ - Programming language
Resend API - Email service for contact form

Frontend

Tailwind CSS - Utility-first CSS framework
JavaScript (Vanilla) - Interactive elements
HTML5 - Semantic markup
Google Fonts - Space Grotesk & JetBrains Mono

Tools & Libraries

python-dotenv - Environment variable management
Django Messages - User feedback system

⚙️ Installation & Setup
Prerequisites

Python 3.10 or higher
pip (Python package manager)
Git

🎨 Featured Projects

SZN Brand E-Commerce - Fashion e-commerce platform

Django, PostgreSQL, Payment Gateway Integration
🔗 Live Site


Party Ticketing Platform - Event management system

Django, Paystack API, QR Code Generation
🔗 Live Site


Crownie Coin Launch - Cryptocurrency platform (2 versions)

Django Version & Next.js Version
Discord API Integration, Referral System
🔗 Live Site


MarketBrainers Agency - Marketing agency website

Django, CMS, SEO Optimization
🔗 Live Site



📱 Responsive Design
The portfolio is fully responsive with breakpoints optimized for:

📱 Mobile devices (320px - 767px)
📱 Tablets (768px - 1023px)
💻 Desktops (1024px+)
🖥️ Large screens (1440px+)

🎯 Key Features Implementation
Dark Mode

Persistent theme preference using localStorage
Smooth transitions between themes
Custom scrollbar styling for both modes

Navigation

Sticky navbar with blur effect
Smooth hamburger animation
Mobile menu with staggered item animations
Active page highlighting

Contact Form

Client-side validation
Server-side processing with Django
Email delivery via Resend API
Success/error feedback messages
Loading states during submission

Animations

Smooth page transitions
Hover effects on cards and buttons
Gradient text animations
Floating elements
Staggered item reveals

🔒 Security Notes

Never commit .env file to version control
Use environment variables for sensitive data
Keep DEBUG=False in production
Set ALLOWED_HOSTS in production settings
Use strong SECRET_KEY
Verify domain in Resend for production emails

📝 Customization
Update Personal Information
Edit these files:

templates/about.html - Your bio, skills, experience
templates/contact.html - Contact details
settings.py - Email address for contact form

Add New Projects
Edit templates/projects.html and templates/home.html to add/update project cards.
Change Color Scheme
Update Tailwind config in base.html:
javascriptcolors: {
    primary: '#667eea',    // Purple
    secondary: '#764ba2',  // Dark purple
}
Update Technology Icons
Add/replace images in static/tech/ folder and update references in templates.
🐛 Known Issues

Emails from onboarding@resend.dev may go to spam (solution: verify custom domain)
Dark mode flash on page load (solution: add inline script in head)

🤝 Contributing
While this is a personal portfolio, suggestions and feedback are welcome!

Fork the repository
Create a feature branch (git checkout -b feature/improvement)
Commit your changes (git commit -m 'Add some improvement')
Push to the branch (git push origin feature/improvement)
Open a Pull Request

📄 License
This project is open source and available under the MIT License.
📬 Contact
Joseph Edward

📧 Email: josephedward201@gmail.com
💼 Portfolio: joewebs.vercel.app
🔗 LinkedIn: www.linkedin.com/in/joseph-edward-94b7a3322
💻 GitHub: @zazajo

🙏 Acknowledgments

Design inspiration from modern portfolio trends
Icons from Heroicons
Fonts from Google Fonts
Email service by Resend


⭐ If you found this portfolio helpful or interesting, please consider giving it a star!
Built with ❤️ by Joseph Edward
