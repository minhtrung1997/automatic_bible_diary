#!/usr/bin/env python3
"""
Email Sender Module
Supports multiple email providers for sending daily Bible diary
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, config):
        """
        Initialize email sender with configuration
        
        Args:
            config: Configuration object containing email settings
        """
        self.config = config
        self.provider = config.email_provider.lower()
        
    def send_daily_diary(self, bible_content: Dict[str, str], 
                        diary_entry: str, date: datetime) -> bool:
        """
        Send daily Bible diary via email
        
        Args:
            bible_content: Dictionary containing Bible readings
            diary_entry: Generated diary entry
            date: Date for the diary entry
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            subject = f"Daily Bible Diary - {date.strftime('%B %d, %Y')}"
            body = self._create_email_body(bible_content, diary_entry, date)
            
            if self.provider == 'gmail':
                return self._send_via_gmail(subject, body)
            elif self.provider == 'sendgrid':
                return self._send_via_sendgrid(subject, body)
            elif self.provider == 'ses':
                return self._send_via_ses(subject, body)
            else:
                logger.error(f"Unsupported email provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def _create_email_body(self, bible_content: Dict[str, str], 
                          diary_entry: str, date: datetime) -> str:
        """Create formatted email body"""
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f4f4f4; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .bible-reading {{ background-color: #f9f9f9; padding: 15px; margin: 15px 0; border-left: 4px solid #4CAF50; }}
                .diary-entry {{ background-color: #fff3cd; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; padding: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🙏 Daily Bible Diary</h1>
                <h2>{date.strftime('%A, %B %d, %Y')}</h2>
            </div>
            
            <div class="content">
                <div class="bible-reading">
                    <h3>📖 Today's Bible Readings</h3>
        """
        
        # Add Bible readings
        reading_order = ['First Reading', 'Responsorial Psalm', 'Second Reading', 'Alleluia', 'Gospel']
        for reading_type in reading_order:
            if reading_type in bible_content:
                html_body += f"<h4>{reading_type}</h4><p>{bible_content[reading_type][:500]}...</p>"
        
        if 'content' in bible_content:
            html_body += f"<p>{bible_content['content'][:800]}...</p>"
        
        # Add diary entry
        html_body += f"""
                </div>
                
                <div class="diary-entry">
                    <h3>✍️ Personal Reflection</h3>
                    <p>{diary_entry}</p>
                </div>
                
                <p>Source: <a href="{bible_content.get('url', '#')}">USCCB Daily Readings</a></p>
            </div>
            
            <div class="footer">
                <p>Daily Bible Diary - Generated with ❤️ and AI assistance</p>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def _send_via_gmail(self, subject: str, body: str) -> bool:
        """Send email via Gmail SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.email_from
            msg['To'] = self.config.email_to
            
            # Add HTML body
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Connect to Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.config.email_from, self.config.email_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info("Email sent successfully via Gmail")
            return True
            
        except Exception as e:
            logger.error(f"Gmail SMTP error: {str(e)}")
            return False
    
    def _send_via_sendgrid(self, subject: str, body: str) -> bool:
        """Send email via SendGrid API"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.config.email_password)
            
            message = Mail(
                from_email=self.config.email_from,
                to_emails=self.config.email_to,
                subject=subject,
                html_content=body
            )
            
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info("Email sent successfully via SendGrid")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return False
    
    def _send_via_ses(self, subject: str, body: str) -> bool:
        """Send email via Amazon SES"""
        try:
            import boto3
            
            ses_client = boto3.client(
                'ses',
                region_name=self.config.aws_region,
                aws_access_key_id=self.config.aws_access_key,
                aws_secret_access_key=self.config.aws_secret_key
            )
            
            response = ses_client.send_email(
                Source=self.config.email_from,
                Destination={'ToAddresses': [self.config.email_to]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {'Html': {'Data': body, 'Charset': 'UTF-8'}}
                }
            )
            
            logger.info("Email sent successfully via Amazon SES")
            return True
            
        except Exception as e:
            logger.error(f"Amazon SES error: {str(e)}")
            return False