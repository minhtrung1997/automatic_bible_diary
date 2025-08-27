#!/usr/bin/env python3
"""Email Sender Module

Supports multiple providers (gmail, sendgrid, ses) to send the daily diary.
Gospel-only + NKKT reflection formatting.
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from string import Template
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, config):
        self.config = config
        self.provider = config.email_provider.lower()
        self.from_addr = config.email_from
        self.to_addr = config.email_to or config.email_from
        self.password = config.email_password

    def send_daily_diary(self, bible_content: Dict[str, str], diary_entry: str, date: datetime) -> bool:
        if not bible_content:
            logger.error("Empty bible_content; aborting email send")
            return False
        if not diary_entry:
            logger.error("Empty diary_entry; aborting email send")
            return False
        subject = self._build_subject(bible_content, date)
        html_body = self._create_email_body(bible_content, diary_entry, date)
        plain_body = self._create_plain_text(bible_content, diary_entry, date)
        try:
            if self.provider == 'gmail':
                ok = self._send_via_gmail(subject, html_body, plain_body)
            elif self.provider == 'sendgrid':
                ok = self._send_via_sendgrid(subject, html_body, plain_body)
            elif self.provider == 'ses':
                ok = self._send_via_ses(subject, html_body, plain_body)
            else:
                logger.error(f"Unsupported email provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
        if ok:
            logger.info("Email sent successfully via %s", self.provider)
        else:
            logger.error("Email sending failed via %s", self.provider)
        return ok

    def _build_subject(self, bible_content: Dict[str, str], date: datetime) -> str:
        citation = bible_content.get('gospel_citation') or 'Daily Bible Diary'
        return f"NKKT {date.strftime('%Y-%m-%d')} - {citation}"[:150]

    def _create_email_body(self, bible_content: Dict[str, str], diary_entry: str, date: datetime) -> str:
        gospel_citation = bible_content.get('gospel_citation')
        gospel_link = bible_content.get('gospel_link')
        gospel_body = bible_content.get('gospel_body') or bible_content.get('Gospel', '')
        if not gospel_citation and '\n\n' in gospel_body:
            first_part, _, rest = gospel_body.partition('\n\n')
            if len(first_part) < 140:
                gospel_citation = first_part
                gospel_body = rest
        paragraphs = [p.strip() for p in gospel_body.split('\n\n') if p.strip()]
        gospel_body_html = ''.join(f'<p>{p}</p>' for p in paragraphs) or f'<p>{gospel_body.strip()}</p>'
        if gospel_citation:
            if gospel_link:
                citation_html = f'<h4>{gospel_citation} <a href="{gospel_link}" target="_blank">Link</a></h4>'
            else:
                citation_html = f'<h4>{gospel_citation}</h4>'
        else:
            citation_html = ''
        date_str = date.strftime('%A, %B %d, %Y')
        diary_entry_html = '<br/>'.join(line for line in diary_entry.strip().splitlines() if line.strip())
        tpl = Template("""
<html>
<head>
<meta charset="utf-8" />
<style>
body { font-family: Arial, sans-serif; line-height: 1.55; color: #222; }
.header { background:#f4f4f4; padding:20px; text-align:center; }
.content { padding:20px; }
.gospel { background:#f9f9f9; padding:18px 20px; border-left:4px solid #4CAF50; }
.gospel h3 { margin-top:0; }
.diary-entry { background:#fff8e1; padding:18px 20px; border-radius:6px; }
.footer { text-align:center; font-size:12px; color:#666; margin-top:30px; padding:12px; }
p { margin:0 0 12px; }
pre { white-space:pre-wrap; }
</style>
</head>
<body>
  <div class="header">
    <h1>Daily Bible Diary</h1>
    <h2>$DATE</h2>
  </div>
  <div class="content">
    <div class="gospel">
      <h3>Gospel of the Day</h3>
      $CITATION_HTML
      $GOSPEL_BODY_HTML
      <p style="margin-top:10px; font-size:12px;">Source: <a href="$SOURCE_URL" target="_blank">USCCB Daily Readings</a></p>
    </div>
    <div class="diary-entry">
      <h3>NKKT Reflection</h3>
      <pre>$DIARY_ENTRY_HTML</pre>
    </div>
  </div>
  <div class="footer">Generated automatically • Gospel only</div>
</body>
</html>
""")
        return tpl.substitute(
            DATE=date_str,
            CITATION_HTML=citation_html,
            GOSPEL_BODY_HTML=gospel_body_html,
            SOURCE_URL=bible_content.get('url', '#'),
            DIARY_ENTRY_HTML=diary_entry_html
        )

    def _create_plain_text(self, bible_content: Dict[str, str], diary_entry: str, date: datetime) -> str:
        citation = bible_content.get('gospel_citation')
        link = bible_content.get('gospel_link')
        body = bible_content.get('gospel_body') or bible_content.get('Gospel', '')
        date_str = date.strftime('%Y-%m-%d')
        lines = [f"Daily Bible Diary {date_str}"]
        if citation:
            if link:
                lines.append(f"Gospel: {citation} ({link})")
            else:
                lines.append(f"Gospel: {citation}")
        lines.append("")
        lines.append(body.strip())
        lines.append("")
        lines.append("NKKT Reflection:")
        lines.append(diary_entry.strip())
        return '\n'.join(lines)

    def _send_via_gmail(self, subject: str, html_body: str, plain_body: str) -> bool:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr
        msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=30) as server:
                server.login(self.from_addr, self.password)
                server.sendmail(self.from_addr, [self.to_addr], msg.as_string())
            return True
        except Exception as e:
            logger.error(f"Gmail send error: {e}")
            return False

    def _send_via_sendgrid(self, subject: str, html_body: str, plain_body: str) -> bool:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
        except ImportError:
            logger.error("sendgrid package not installed")
            return False
        try:
            message = Mail(
                from_email=self.from_addr,
                to_emails=self.to_addr,
                subject=subject,
                plain_text_content=plain_body,
                html_content=html_body
            )
            sg = SendGridAPIClient(self.password)
            resp = sg.send(message)
            if 200 <= resp.status_code < 300:
                return True
            logger.error(f"SendGrid failed status={resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"SendGrid send error: {e}")
            return False

    def _send_via_ses(self, subject: str, html_body: str, plain_body: str) -> bool:
        try:
            import boto3
        except ImportError:
            logger.error("boto3 not installed for SES")
            return False
        try:
            ses = boto3.client(
                'ses',
                region_name=getattr(self.config, 'aws_region', 'us-east-1'),
                aws_access_key_id=getattr(self.config, 'aws_access_key', None) or getattr(self.config, 'aws_access_key_id', None),
                aws_secret_access_key=getattr(self.config, 'aws_secret_key', None) or getattr(self.config, 'aws_secret_access_key', None),
            )
            resp = ses.send_email(
                Source=self.from_addr,
                Destination={'ToAddresses': [self.to_addr]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': plain_body, 'Charset': 'UTF-8'},
                        'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                    }
                }
            )
            status = resp.get('ResponseMetadata', {}).get('HTTPStatusCode')
            return status == 200
        except Exception as e:
            logger.error(f"SES send error: {e}")
            return False