"""
Newsletter Generator & Sender
Sends a daily HTML digest of published, unsent articles to active subscribers
via SendGrid. Marks articles as sent only if >=1 delivery succeeded.
"""

import argparse
import html
import logging
import os
import sys
import textwrap
from datetime import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo

from sheets_client import SheetsClient

# Configure logging — match main.py style
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

FROM_NAME = "AI News"
FROM_EMAIL = "contactus@ivolution-ai.com"
WEBSITE_URL = "https://ivolution-ai.com"
AI_NEWS_PAGE_URL = "https://ivolution-ai.com/pages/ai-news.html"
UNSUBSCRIBE_URL_TEMPLATE = "https://ivolution-ai.com/pages/unsubscribe.html?token={token}"

CATEGORY_ORDER = [
    "model_releases",
    "agentic_ai",
    "developer_tools",
    "enterprise_strategy",
    "healthcare_ai",
    "robotics",
    "creative_tools",
    "infrastructure",
]

CATEGORY_DISPLAY = {
    "model_releases": "Model Releases",
    "agentic_ai": "Agentic AI",
    "developer_tools": "Developer Tools",
    "enterprise_strategy": "Enterprise Strategy",
    "healthcare_ai": "Healthcare AI",
    "robotics": "Robotics",
    "creative_tools": "Creative Tools",
    "infrastructure": "Infrastructure",
}

OTHER_DISPLAY = "Other"

# Brand tokens (inline in email HTML)
COLOR_PRIMARY_BLUE = "#2563eb"
COLOR_ORANGE = "#FFB020"
COLOR_DARK_TEXT = "#1e293b"
COLOR_GRAY_TEXT = "#64748b"
COLOR_BORDER = "#e2e8f0"
COLOR_PAGE_BG = "#f8fafc"

FONT_STACK = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

PROCESSED_TAB = "Processed Articles"
PROCESSED_RANGE = f"{PROCESSED_TAB}!A2:L"
SUBSCRIBERS_RANGE = "Newsletter Subscribers!A2:E"


# ── Data loaders ─────────────────────────────────────────────────────────────

def load_unsent_published_articles(sheets_client: SheetsClient) -> List[Dict]:
    """Read Processed Articles!A2:L. Keep rows where K='yes' and L is empty."""
    result = sheets_client.service.spreadsheets().values().get(
        spreadsheetId=sheets_client.sheet_id,
        range=PROCESSED_RANGE
    ).execute()
    rows = result.get("values", [])

    articles: List[Dict] = []
    for i, row in enumerate(rows):
        # Pad to 12 columns
        padded = list(row) + [""] * (12 - len(row))

        published = padded[10].strip().lower()
        sent = padded[11].strip()

        if published != "yes":
            continue
        if sent:
            continue

        articles.append({
            "row_index":       i + 2,  # A2 = row 2
            "date":            padded[0],
            "source":          padded[1],
            "category":        padded[2],
            "title":           padded[3],
            "summary":         padded[4],
            "sources":         padded[5],
            "source_count":    padded[6],
            "confidence":      padded[7],
            "processed_at":    padded[8],
            "duplicate_count": padded[9],
            "published":       padded[10],
        })

    logger.info(f"Loaded {len(articles)} unsent published articles")
    return articles


def load_active_subscribers(sheets_client: SheetsClient) -> List[Dict]:
    """Read Newsletter Subscribers!A2:E. Keep rows where B='active' and A non-empty."""
    result = sheets_client.service.spreadsheets().values().get(
        spreadsheetId=sheets_client.sheet_id,
        range=SUBSCRIBERS_RANGE
    ).execute()
    rows = result.get("values", [])

    subscribers: List[Dict] = []
    for row in rows:
        padded = list(row) + [""] * (5 - len(row))
        email = padded[0].strip()
        status = padded[1].strip().lower()
        token = padded[4].strip()

        if not email:
            continue
        if status != "active":
            continue

        subscribers.append({"email": email, "token": token})

    logger.info(f"Loaded {len(subscribers)} active subscribers")
    return subscribers


# ── Grouping ─────────────────────────────────────────────────────────────────

def group_articles_by_category(articles: List[Dict]) -> Dict[str, List[Dict]]:
    """Group articles by category slug in CATEGORY_ORDER, unknowns in 'other'."""
    grouped: Dict[str, List[Dict]] = {cat: [] for cat in CATEGORY_ORDER}
    other: List[Dict] = []
    unknown_slugs = set()

    for article in articles:
        cat = (article.get("category") or "").strip()
        if cat in grouped:
            grouped[cat].append(article)
        else:
            if cat:
                unknown_slugs.add(cat)
            other.append(article)

    for slug in unknown_slugs:
        logger.warning(f"Unknown category slug bucketed as 'other': {slug}")

    # Sort each bucket by date descending (YYYY-MM-DD sorts lexically)
    for cat in grouped:
        grouped[cat].sort(key=lambda a: a.get("date", ""), reverse=True)
    other.sort(key=lambda a: a.get("date", ""), reverse=True)

    # Drop empty categories, keep insertion order, append 'other' at end
    ordered: Dict[str, List[Dict]] = {cat: arts for cat, arts in grouped.items() if arts}
    if other:
        ordered["other"] = other

    return ordered


def _display_name(slug: str) -> str:
    return CATEGORY_DISPLAY.get(slug, OTHER_DISPLAY)


def _iter_articles_in_display_order(grouped: Dict[str, List[Dict]]):
    for slug, articles in grouped.items():
        for article in articles:
            yield slug, article


# ── HTML rendering ───────────────────────────────────────────────────────────

def _summary_paragraphs(summary: str) -> List[str]:
    """Split a summary into paragraphs on blank lines; fall back to a single para."""
    if not summary:
        return [""]
    parts = [p.strip() for p in summary.split("\n\n") if p.strip()]
    return parts if parts else [summary.strip()]


def render_email_html(grouped: Dict[str, List[Dict]], subscriber_token: str, send_date_display: str) -> str:
    """Build the full HTML email as a single string. Table-based, inline styles."""
    unsubscribe_url = UNSUBSCRIBE_URL_TEMPLATE.format(token=subscriber_token)

    # (a) Top bar — 2-col table, 600px, on page background
    top_bar = f"""
    <table role="presentation" align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="width:600px;max-width:100%;margin:0 auto;font-family:{FONT_STACK};">
      <tr>
        <td align="left" style="padding:16px 8px;font-size:12px;color:{COLOR_GRAY_TEXT};">
          <a href="{AI_NEWS_PAGE_URL}" style="color:{COLOR_GRAY_TEXT};text-decoration:underline;">Read on the web</a>
        </td>
        <td align="right" style="padding:16px 8px;font-size:12px;color:{COLOR_GRAY_TEXT};">
          {html.escape(send_date_display)}
        </td>
      </tr>
    </table>
    """

    # (b) Header — inside white content box
    header = f"""
    <tr>
      <td align="center" style="padding:32px 24px 16px 24px;font-family:{FONT_STACK};">
        <div style="font-size:28px;font-weight:bold;color:{COLOR_PRIMARY_BLUE};line-height:1.2;">iVolution AI News</div>
        <div style="font-size:14px;color:{COLOR_GRAY_TEXT};margin-top:8px;">Daily enterprise AI intelligence</div>
      </td>
    </tr>
    """

    # (c) TL;DR box
    tldr_rows = []
    for slug, article in _iter_articles_in_display_order(grouped):
        title = html.escape(article.get("title") or "Untitled")
        cat_display = html.escape(_display_name(slug))
        tldr_rows.append(f"""
        <tr>
          <td style="padding:4px 0;vertical-align:top;font-family:{FONT_STACK};">
            <span style="color:{COLOR_ORANGE};font-size:14px;font-weight:bold;">&bull;</span>
            <span style="color:{COLOR_DARK_TEXT};font-size:14px;margin-left:6px;">{title}</span>
            <span style="color:{COLOR_GRAY_TEXT};font-size:12px;margin-left:8px;">({cat_display})</span>
          </td>
        </tr>
        """)

    tldr = f"""
    <tr>
      <td style="padding:0 24px 16px 24px;">
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid {COLOR_BORDER};border-left:6px solid {COLOR_ORANGE};font-family:{FONT_STACK};">
          <tr>
            <td style="padding:24px;">
              <div style="font-size:14px;font-weight:bold;color:{COLOR_ORANGE};text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">TL;DR</div>
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                {''.join(tldr_rows)}
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """

    # (d) Category sections
    category_blocks = []
    for slug, articles in grouped.items():
        if not articles:
            continue
        cat_display = html.escape(_display_name(slug))

        article_rows = []
        for idx, article in enumerate(articles):
            if idx > 0:
                article_rows.append(f"""
                <tr>
                  <td style="padding:0 24px;">
                    <div style="height:1px;line-height:1px;font-size:0;background-color:{COLOR_BORDER};">&nbsp;</div>
                  </td>
                </tr>
                """)

            title = html.escape(article.get("title") or "Untitled")
            paragraphs = _summary_paragraphs(article.get("summary") or "")
            last = len(paragraphs) - 1
            summary_html = "".join(
                f'<p style="margin:0 0 {0 if idx == last else 12}px 0;font-size:15px;line-height:1.6;color:{COLOR_DARK_TEXT};">{html.escape(p)}</p>'
                for idx, p in enumerate(paragraphs)
            )

            article_rows.append(f"""
            <tr>
              <td style="padding:24px;background-color:#ffffff;font-family:{FONT_STACK};">
                <div style="font-size:18px;font-weight:bold;color:{COLOR_DARK_TEXT};line-height:1.35;margin-bottom:12px;">{title}</div>
                {summary_html}
              </td>
            </tr>
            """)

        category_blocks.append(f"""
        <tr>
          <td style="padding:0;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;">
              <tr>
                <td style="padding:12px 24px;background-color:{COLOR_ORANGE};font-family:{FONT_STACK};">
                  <div style="font-size:14px;font-weight:bold;color:#ffffff;text-transform:uppercase;letter-spacing:1px;">{cat_display}</div>
                </td>
              </tr>
              {''.join(article_rows)}
            </table>
          </td>
        </tr>
        """)

    categories_html = "".join(category_blocks)

    # (e) CTA button — bulletproof table-based pattern
    cta = f"""
    <tr>
      <td align="center" style="padding:32px 24px;background-color:#ffffff;">
        <table border="0" cellspacing="0" cellpadding="0" align="center">
          <tr>
            <td align="center" bgcolor="{COLOR_ORANGE}" style="border-radius:6px;">
              <a href="{AI_NEWS_PAGE_URL}" target="_blank"
                 style="display:inline-block;padding:14px 32px;font-size:16px;font-weight:bold;color:{COLOR_DARK_TEXT};text-decoration:none;font-family:{FONT_STACK};">
                See all articles on iVolution &rarr;
              </a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """

    # Content box (sections b–e) — white, 600px, centered
    content_box = f"""
    <table role="presentation" align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="width:600px;max-width:100%;margin:0 auto;background-color:#ffffff;">
      {header}
      {tldr}
      {categories_html}
      {cta}
    </table>
    """

    # (f) Footer — on page background
    footer = f"""
    <table role="presentation" align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="width:600px;max-width:100%;margin:0 auto;font-family:{FONT_STACK};">
      <tr>
        <td align="center" style="padding:32px 24px;font-size:12px;color:{COLOR_GRAY_TEXT};line-height:1.6;">
          <div>iVolution &mdash; AI transformation advisory for MENA</div>
          <div style="height:8px;line-height:8px;font-size:0;">&nbsp;</div>
          <div>You're receiving this because you subscribed at ivolution-ai.com</div>
          <div style="height:8px;line-height:8px;font-size:0;">&nbsp;</div>
          <div><a href="{unsubscribe_url}" style="color:{COLOR_GRAY_TEXT};text-decoration:underline;">Unsubscribe</a></div>
        </td>
      </tr>
    </table>
    """

    # Full document
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>iVolution AI News &mdash; {html.escape(send_date_display)}</title>
</head>
<body style="margin:0;padding:0;background-color:{COLOR_PAGE_BG};">
  {top_bar}
  {content_box}
  {footer}
</body>
</html>"""


# ── Plain-text rendering ─────────────────────────────────────────────────────

def _wrap_paragraph(text: str, width: int = 80) -> str:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()] if text else []
    if not paragraphs:
        return ""
    return "\n\n".join(textwrap.fill(p, width=width) for p in paragraphs)


def render_email_plaintext(grouped: Dict[str, List[Dict]], subscriber_token: str, send_date_display: str) -> str:
    """Plain-text alternative to the HTML email."""
    unsubscribe_url = UNSUBSCRIBE_URL_TEMPLATE.format(token=subscriber_token)

    lines: List[str] = []
    lines.append(f"iVolution AI News — {send_date_display}")
    lines.append("")
    lines.append(f"View on the web: {AI_NEWS_PAGE_URL}")
    lines.append("")
    lines.append("TL;DR")
    lines.append("=====")
    lines.append("")

    for slug, article in _iter_articles_in_display_order(grouped):
        title = (article.get("title") or "Untitled").strip()
        cat = _display_name(slug)
        lines.append(f"- {title} ({cat})")
    lines.append("")

    for slug, articles in grouped.items():
        if not articles:
            continue
        heading = _display_name(slug).upper()
        lines.append(heading)
        lines.append("=" * len(heading))
        lines.append("")
        for article in articles:
            title = (article.get("title") or "Untitled").strip()
            summary = article.get("summary") or ""
            lines.append(title)
            lines.append("-" * len(title))
            wrapped = _wrap_paragraph(summary, width=80)
            lines.append(wrapped if wrapped else "")
            lines.append("")
        lines.append("")

    lines.append(f"See all articles: {AI_NEWS_PAGE_URL}")
    lines.append("")
    lines.append("---")
    lines.append("iVolution — AI transformation advisory for MENA")
    lines.append("You're receiving this because you subscribed at ivolution-ai.com")
    lines.append(f"Unsubscribe: {unsubscribe_url}")
    lines.append("")

    return "\n".join(lines)


# ── SendGrid delivery ────────────────────────────────────────────────────────

def send_email(sg_client, to_email: str, subject: str, html_body: str, plaintext: str) -> bool:
    """Send a single email via SendGrid. Returns True on 2xx, False on any error."""
    try:
        from sendgrid.helpers.mail import Mail, Email, To, Content

        mail = Mail(
            from_email=Email(FROM_EMAIL, FROM_NAME),
            to_emails=To(to_email),
            subject=subject,
            plain_text_content=Content("text/plain", plaintext),
            html_content=Content("text/html", html_body),
        )
        response = sg_client.send(mail)
        status = getattr(response, "status_code", None)
        if status is not None and 200 <= status < 300:
            logger.info(f"Sent to {to_email} (HTTP {status})")
            return True
        body = getattr(response, "body", b"")
        logger.error(f"Send failed for {to_email}: HTTP {status} body={body!r}")
        return False
    except Exception as e:
        logger.error(f"Send raised exception for {to_email}: {e}")
        return False


# ── Batch-mark articles as sent ──────────────────────────────────────────────

def mark_articles_as_sent(sheets_client: SheetsClient, articles: List[Dict], send_date: str) -> None:
    """Batch-update column L to send_date for each article's row_index.

    Raises on API error — consistency-critical operation.
    """
    if not articles:
        return

    data = [
        {
            "range": f"{PROCESSED_TAB}!L{article['row_index']}",
            "values": [[send_date]],
        }
        for article in articles
    ]
    body = {"valueInputOption": "RAW", "data": data}

    try:
        sheets_client.service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheets_client.sheet_id,
            body=body,
        ).execute()
        logger.info(f"Marked {len(articles)} articles as sent with date {send_date}")
    except Exception as e:
        logger.error(f"Failed to mark articles as sent: {e}")
        raise


# ── Arg parsing ──────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Send the daily iVolution AI News newsletter.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render HTML to preview.html, log counts, do not call SendGrid or update the sheet.",
    )
    parser.add_argument(
        "--test-email",
        metavar="EMAIL",
        default=None,
        help="Send exactly one real email to this address. Does NOT mark articles as sent.",
    )
    return parser.parse_args()


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    args = parse_args()

    if args.dry_run and args.test_email:
        logger.error("--dry-run and --test-email are mutually exclusive.")
        return 1

    # Sheets client — always required
    sheets_client = SheetsClient()

    # SendGrid client — fail loud if needed for actual sends; skip entirely in dry-run
    sg_client = None
    if not args.dry_run:
        api_key = os.environ.get("SENDGRID_API_KEY")
        if not api_key:
            logger.error("SENDGRID_API_KEY environment variable is not set.")
            return 1
        import sendgrid
        sg_client = sendgrid.SendGridAPIClient(api_key)

    # Load data
    articles = load_unsent_published_articles(sheets_client)
    if not articles:
        logger.info("No unsent published articles. Skipping newsletter.")
        return 0

    grouped = group_articles_by_category(articles)

    today_cairo = datetime.now(ZoneInfo("Africa/Cairo")).date()
    send_date_iso = today_cairo.strftime("%Y-%m-%d")
    send_date_display = today_cairo.strftime("%d-%m-%Y")
    subject = f"iVolution AI News — {send_date_display}"

    # ── Dry-run branch ───────────────────────────────────────────────────────
    if args.dry_run:
        html_body = render_email_html(grouped, "PREVIEW_TOKEN", send_date_display)
        plaintext = render_email_plaintext(grouped, "PREVIEW_TOKEN", send_date_display)
        with open("preview.html", "w", encoding="utf-8") as f:
            f.write(html_body)
        with open("preview.txt", "w", encoding="utf-8") as f:
            f.write(plaintext)
        try:
            subs = load_active_subscribers(sheets_client)
            logger.info(f"Dry run: would send to {len(subs)} subscribers")
        except Exception as e:
            logger.warning(f"Could not load subscribers in dry-run: {e}")
        logger.info(f"Dry run: rendered email for {len(articles)} articles")
        logger.info("Wrote preview.html and preview.txt")
        return 0

    # ── Test-email branch ────────────────────────────────────────────────────
    if args.test_email:
        html_body = render_email_html(grouped, "TEST_TOKEN", send_date_display)
        plaintext = render_email_plaintext(grouped, "TEST_TOKEN", send_date_display)
        ok = send_email(sg_client, args.test_email, subject, html_body, plaintext)
        if ok:
            logger.info(f"Test email sent to {args.test_email}")
            logger.info("Test mode: articles NOT marked as sent")
            return 0
        logger.error(f"Test email FAILED to {args.test_email}")
        return 1

    # ── Production branch ────────────────────────────────────────────────────
    subscribers = load_active_subscribers(sheets_client)
    if not subscribers:
        logger.info("No active subscribers. Skipping newsletter.")
        return 0

    success_count = 0
    fail_count = 0
    for sub in subscribers:
        html_body = render_email_html(grouped, sub["token"], send_date_display)
        plaintext = render_email_plaintext(grouped, sub["token"], send_date_display)
        ok = send_email(sg_client, sub["email"], subject, html_body, plaintext)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    logger.info(f"Send complete: {success_count} succeeded, {fail_count} failed")

    if success_count > 0:
        mark_articles_as_sent(sheets_client, articles, send_date_iso)
    else:
        logger.error("Zero successful sends. Articles NOT marked as sent.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
