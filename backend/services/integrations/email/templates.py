# ruff: noqa: E501

from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _templates_dir() -> Path:
    return Path(__file__).resolve().parent / "html"


def render_template(template_name: str, context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(_templates_dir()),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)
    return template.render(**context)


def render_inline(
    subject: str,
    body_lines: list[str],
    *,
    button_text: str | None = None,
    button_url: str | None = None,
) -> str:
    heading = escape(subject)
    paragraphs = "".join(f"<p style='margin:0 0 16px;'>{escape(line)}</p>" for line in body_lines)
    button_html = ""
    if button_text and button_url:
        button_html = (
            f"<div style='margin:24px 0;'>"
            f"<a href='{escape(button_url)}' "
            f"style='display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;"
            f"padding:12px 20px;border-radius:8px;font-weight:600;'>"
            f"{escape(button_text)}</a></div>"
        )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{heading}</title>
  </head>
  <body style="margin:0;padding:0;background:#f3f4f6;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f4f6;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;">
            <tr>
              <td style="padding:24px 24px 8px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                <div style="font-size:14px;color:#6b7280;margin-bottom:16px;">[Logo]</div>
                <h1 style="margin:0 0 16px;font-size:24px;line-height:1.3;color:#111827;">{heading}</h1>
                <div style="font-size:16px;line-height:1.6;color:#374151;">
                  {paragraphs}
                </div>
                {button_html}
              </td>
            </tr>
            <tr>
              <td style="padding:16px 24px 24px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-size:12px;line-height:1.5;color:#9ca3af;border-top:1px solid #e5e7eb;">
                You are receiving this email because you have an account with us.
                <br />
                <a href="{{{{ unsubscribe_url }}}}" style="color:#6b7280;">Unsubscribe</a>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""
