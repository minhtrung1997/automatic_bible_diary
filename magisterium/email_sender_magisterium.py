#!/usr/bin/env python3
"""Email Sender for Magisterium Psalm Reflection."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime
from string import Template

logger = logging.getLogger(__name__)


class EmailSenderMagisterium:
    def __init__(self, config):
        self.config = config
        self.provider = config.email_provider.lower()

    def send_psalm_reflection(self, content: Dict[str, str], reflection: str, date: datetime,
                              subject: Optional[str] = None, section_title: str = 'Responsorial Psalm',
                              vietnamese_text: Optional[str] = None) -> bool:
        try:
            subject = subject or f"Daily Psalm Reflection - {date.strftime('%B %d, %Y')}"
            body = self._create_email_body(content, reflection, date, section_title, vietnamese_text)
            if self.provider == 'gmail':
                return self._send_via_gmail(subject, body)
            if self.provider == 'sendgrid':
                return self._send_via_sendgrid(subject, body)
            if self.provider == 'ses':
                return self._send_via_ses(subject, body)
            logger.error(f"Unsupported email provider: {self.provider}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def _create_email_body(self, content: Dict[str, str], reflection: str, date: datetime, 
                          section_title: str, vietnamese_text: Optional[str] = None) -> str:
        # Keep the source link and citation, but content follows mg_prompt structure
        citation = content.get('psalm_citation') or content.get('gospel_citation')
        link = content.get('psalm_link') or content.get('gospel_link')
        body_txt = content.get('psalm_body') or content.get('gospel_body') or ''
        if not citation and '\n\n' in body_txt:
            first, _, rest = body_txt.partition('\n\n')
            if len(first) < 120:
                citation = first
                body_txt = rest
        body_html = ''.join(
            f'<p>{p.strip()}</p>' for p in body_txt.split('\n\n') if p.strip()
        ) or (f'<p>{body_txt.strip()}</p>' if body_txt.strip() else '')
        citation_html = ''
        if citation:
            citation_html = (
                f'<h4>{citation} ' + (f'<a href="{link}" target="_blank">🔗</a>' if link else '') + '</h4>'
            )

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
    <h1>🙏 Daily Psalm Reflection</h1>
    <h2>$DATE</h2>
</div>
<div class="content">
    <div class="gospel">
        <h3>📖 $SECTION_TITLE</h3>
        $CITATION_HTML
                    <h4>Thánh vịnh hôm nay</h4>
                    $BODY_HTML
        <p style="margin-top:10px; font-size:12px;">Source:
            <a href="$SOURCE_URL" target="_blank">USCCB Daily Readings</a>
        </p>
        </div>
        <div class="diary-entry">
            <h3>📖 Kinh thánh:</h3>
            <p>$VIETNAMESE_HTML</p>
            <h3 style="margin-top:18px;">✍️ Suy niệm</h3>
            <p>$MEDITATION_HTML</p>
            <h3 style="margin-top:18px;">🙏 Cầu nguyện</h3>
            <p>$PRAYER_HTML</p>
        </div>
</div>
<div class="footer">Automated Psalm Reflection - Generated with AI assistance</div>
</body>
</html>
""")
        # Try to split the reflection into sections per mg_prompt structure
        text = reflection.strip()
        
        # Clean up footnote references like [^9], [^14], etc.
        import re
        text = re.sub(r'\[\^\d+\]', '', text)
        
        # Clean up markdown-style headers like #### or ###
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        
        med = text
        prayer = ''
        # Simple split on section headers
        if 'Cầu nguyện' in text:
            parts = text.split('Cầu nguyện', 1)
            med = parts[0].replace('Suy niệm', '').replace('Suy niệm:', '').strip()
            prayer = parts[1].replace(':', '', 1).strip()
        
        # Clean up any remaining colons at the start
        if med.startswith(':'):
            med = med[1:].strip()
        if prayer.startswith(':'):
            prayer = prayer[1:].strip()
            
        MEDITATION_HTML = "<br/>".join(med.splitlines())
        PRAYER_HTML = "<br/>".join(prayer.splitlines())
        
        # Format Vietnamese text for HTML
        if vietnamese_text:
            # Split by double newlines and create paragraphs for each verse section
            vietnamese_sections = vietnamese_text.strip().split('\n\n')
            VIETNAMESE_HTML = "<br/><br/>".join(
                "<br/>".join(section.strip().splitlines()) 
                for section in vietnamese_sections if section.strip()
            )
        else:
            VIETNAMESE_HTML = "<em>Không tìm thấy bản dịch LCCMN</em>"
        
        html_body = template.substitute(
            DATE=date.strftime('%A, %B %d, %Y'),
            SECTION_TITLE=section_title,
            CITATION_HTML=citation_html,
            BODY_HTML=body_html,
            SOURCE_URL=content.get('url', '#'),
            VIETNAMESE_HTML=VIETNAMESE_HTML,
            MEDITATION_HTML=MEDITATION_HTML,
            PRAYER_HTML=PRAYER_HTML,
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
            logger.error(f"Gmail SMTP error: {e}")
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
            logger.error(f"SendGrid error: {e}")
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
            logger.error(f"Amazon SES error: {e}")
            return False
