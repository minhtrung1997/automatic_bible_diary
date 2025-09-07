#!/usr/bin/env python3
"""Email sender for the diary (Gospel) workflow."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from datetime import datetime
from string import Template

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, config):
        self.config = config
        self.provider = config.email_provider.lower()

    def send_daily_diary(self, bible_content: Dict[str, str], diary_entry: str, date: datetime) -> bool:
        try:
            subject = f"Daily Bible Diary - {date.strftime('%B %d, %Y')}"
            body = self._create_email_body(bible_content, diary_entry, date)
            if self.provider == 'gmail':
                return self._send_via_gmail(subject, body)
            if self.provider == 'sendgrid':
                return self._send_via_sendgrid(subject, body)
            if self.provider == 'ses':
                return self._send_via_ses(subject, body)
            logger.error(f"Unsupported email provider: {self.provider}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def _create_email_body(self, bible_content: Dict[str, str], diary_entry: str, date: datetime) -> str:
        gospel_citation = bible_content.get('gospel_citation')
        gospel_link = bible_content.get('gospel_link')
        gospel_body = bible_content.get('gospel_body') or bible_content.get('Gospel', '')
        if not gospel_citation and '\n\n' in gospel_body:
            first_part, _, rest = gospel_body.partition('\n\n')
            if len(first_part) < 120:
                gospel_citation = first_part
                gospel_body = rest
        gospel_body_html = ''.join(
            f'<p>{p.strip()}</p>' for p in gospel_body.split('\n\n') if p.strip()
        ) or f'<p>{gospel_body.strip()}</p>'
        citation_html = ''
        if gospel_citation:
            if gospel_link:
                citation_html = f'<h4>{gospel_citation} <a href="{gospel_link}" target="_blank">🔗</a></h4>'
            else:
                citation_html = f'<h4>{gospel_citation}</h4>'
        template = Template("""<html>
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
</style>
</head>
<body>
<div class="header">
    <h1>🙏 Daily Bible Diary</h1>
    <h2>$DATE</h2>
</div>
<div class="content">
    <div class="gospel">
        <h3>📖 Gospel of the Day</h3>
        $CITATION_HTML
        $GOSPEL_BODY_HTML
        <p style="margin-top:10px; font-size:12px;">Source:
            <a href="$SOURCE_URL" target="_blank">USCCB Daily Readings</a>
        </p>
    </div>
    <div class="diary-entry">
        <h3>✍️ Personal Reflection</h3>
        <p>$DIARY_ENTRY_HTML</p>
    </div>
</div>
<div class="footer">Daily Bible Diary - Generated with AI assistance</div>
</body>
</html>
""")
        diary_entry_html = "<br/>".join(line for line in diary_entry.strip().splitlines())
        html_body = template.substitute(
            DATE=date.strftime('%A, %B %d, %Y'),
            CITATION_HTML=citation_html,
            GOSPEL_BODY_HTML=gospel_body_html,
            SOURCE_URL=bible_content.get('url', '#'),
            DIARY_ENTRY_HTML=diary_entry_html,
        )
        return html_body

    def _send_via_gmail(self, subject: str, body: str) -> bool:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.email_from
            msg['To'] = self.config.email_to
            msg.attach(MIMEText(body, 'html'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.config.email_from, self.config.email_password)
            server.send_message(msg)
            server.quit()
            logger.info("Email sent successfully via Gmail")
            return True
        except Exception as e:
            logger.error(f"Gmail SMTP error: {str(e)}")
            return False

    def _send_via_sendgrid(self, subject: str, body: str) -> bool:
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            sg = sendgrid.SendGridAPIClient(api_key=self.config.email_password)
            response = sg.send(Mail(
                from_email=self.config.email_from,
                to_emails=self.config.email_to,
                subject=subject,
                html_content=body,
            ))
            if response.status_code in [200, 201, 202]:
                logger.info("Email sent successfully via SendGrid")
                return True
            logger.error(f"SendGrid error: {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return False

    def _send_via_ses(self, subject: str, body: str) -> bool:
        try:
            import boto3
            ses_client = boto3.client(
                'ses',
                region_name=self.config.aws_region,
                aws_access_key_id=self.config.aws_access_key,
                aws_secret_access_key=self.config.aws_secret_key,
            )
            ses_client.send_email(
                Source=self.config.email_from,
                Destination={'ToAddresses': [self.config.email_to]},
                Message={'Subject': {'Data': subject, 'Charset': 'UTF-8'}, 'Body': {'Html': {'Data': body, 'Charset': 'UTF-8'}}},
            )
            logger.info("Email sent successfully via Amazon SES")
            return True
        except Exception as e:
            logger.error(f"Amazon SES error: {str(e)}")
            return False
