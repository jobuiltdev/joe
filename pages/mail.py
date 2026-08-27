"""The contact form's mail boundary.

This exists for one reason: the Resend call used to sit inline in the view, so
there was no way to exercise the contact path without either sending real mail
or monkeypatching a module imported halfway down a function body. Everything
here was lifted out of ``views.home`` unchanged; the payload Resend receives is
byte-for-byte what it received before.

It is a boundary, not a service layer. Two functions, no classes, no config.
"""

import logging

from django.conf import settings
from django.utils.html import escape

logger = logging.getLogger(__name__)

FROM_ADDRESS = "Portfolio Contact <onboarding@resend.dev>"


def build_notification_html(name, email, subject, message):
    """Build the email that lands in the inbox.

    Every interpolated value is escaped, since these are raw strings from a
    public form going straight into an HTML document.
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
                      text-transform:uppercase;color:#8a8578">Portfolio: new message</div>
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


def send_contact_message(name, email, subject, message):
    """Hand the message to Resend. Raises on any failure; the view decides.

    The import stays inside the function, as it was in the view: a missing or
    broken mail dependency should cost the contact form, not the whole site.
    """
    import resend

    resend.api_key = settings.RESEND_API_KEY
    return resend.Emails.send(
        {
            "from": FROM_ADDRESS,
            "to": [settings.CONTACT_EMAIL],
            "subject": (
                f"Portfolio: {subject}" if subject else f"Portfolio: new message from {name}"
            ),
            "html": build_notification_html(name, email, subject, message),
            # So a reply goes to the sender rather than to the portfolio.
            "reply_to": email,
        }
    )
