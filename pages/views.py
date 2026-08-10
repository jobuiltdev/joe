from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.html import escape

from . import content

CONTACT_ANCHOR = "/#contact"


def _page_context():
    return {
        "profile": content.PROFILE,
        "nav_items": content.NAV,
        "socials": content.SOCIALS,
        "about": content.ABOUT,
        "about_close": content.ABOUT_CLOSE,
        "help_with": content.HELP_WITH,
        "stack": content.STACK,
        "projects": content.PROJECTS,
    }


def _notification_html(name, email, subject, message):
    """Build the email that lands in the inbox.

    Every interpolated value is escaped — these are raw strings from a public
    form going straight into an HTML document.
    """
    name, email = escape(name), escape(email)
    subject = escape(subject)
    message = escape(message).replace("\n", "<br>")

    subject_row = (
        f'<tr><td style="padding:0 0 18px"><div style="font:600 11px/1.4 '
        f'ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;'
        f'color:#8a8578;padding-bottom:6px">Subject</div>'
        f'<div style="font:400 16px/1.5 Georgia,serif;color:#1a1a1a">{subject}</div></td></tr>'
        if subject
        else ""
    )

    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:32px 16px;background:#faf9f7;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"
           style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #e6e2d9">
      <tr>
        <td style="padding:28px 32px;border-bottom:1px solid #e6e2d9">
          <div style="font:500 11px/1.4 ui-monospace,monospace;letter-spacing:.12em;
                      text-transform:uppercase;color:#8a8578">Portfolio — new message</div>
        </td>
      </tr>
      <tr>
        <td style="padding:28px 32px">
          <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
            <tr>
              <td style="padding:0 0 18px">
                <div style="font:600 11px/1.4 ui-monospace,monospace;letter-spacing:.08em;
                            text-transform:uppercase;color:#8a8578;padding-bottom:6px">From</div>
                <div style="font:400 16px/1.5 Georgia,serif;color:#1a1a1a">{name}</div>
                <div style="font:400 14px/1.5 ui-monospace,monospace">
                  <a href="mailto:{email}" style="color:#1a1a1a">{email}</a>
                </div>
              </td>
            </tr>
            {subject_row}
            <tr>
              <td style="padding:0">
                <div style="font:600 11px/1.4 ui-monospace,monospace;letter-spacing:.08em;
                            text-transform:uppercase;color:#8a8578;padding-bottom:6px">Message</div>
                <div style="font:400 16px/1.7 Georgia,serif;color:#1a1a1a;
                            border-left:2px solid #e6e2d9;padding-left:16px">{message}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:20px 32px;border-top:1px solid #e6e2d9;
                   font:400 12px/1.6 ui-monospace,monospace;color:#8a8578">
          Reply directly to this email to reach {name}.
        </td>
      </tr>
    </table>
  </body>
</html>"""


def home(request):
    """The whole site. GET renders the page; POST is the contact form."""
    if request.method != "POST":
        return render(request, "pages/home.html", _page_context())

    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    subject = request.POST.get("subject", "").strip()
    message = request.POST.get("message", "").strip()

    if not name or not email or not message:
        messages.error(request, "Please fill in your name, email and message.")
        return render(request, "pages/home.html", _page_context())

    try:
        # Imported here, not at module scope: the whole page shouldn't fail to
        # load just because the mail dependency is missing or broken.
        import resend

        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send(
            {
                "from": "Portfolio Contact <onboarding@resend.dev>",
                "to": [settings.CONTACT_EMAIL],
                "subject": (
                    f"Portfolio: {subject}" if subject else f"Portfolio: new message from {name}"
                ),
                "html": _notification_html(name, email, subject, message),
                "reply_to": email,
            }
        )
    except Exception as exc:  # noqa: BLE001 — surface anything as a form error
        print(f"Contact form: failed to send via Resend — {exc}")
        messages.error(
            request,
            "Something went wrong sending that. Please email me directly at "
            f"{settings.CONTACT_EMAIL}.",
        )
        return render(request, "pages/home.html", _page_context())

    messages.success(
        request,
        f"Thanks {name} — message sent. I'll get back to you within 24 hours.",
    )
    # Redirect after POST so a refresh doesn't resubmit, and land on the form.
    return redirect(CONTACT_ANCHOR)
