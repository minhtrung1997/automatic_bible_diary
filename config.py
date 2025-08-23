#!/usr/bin/env python3
"""
Configuration Management Module
"""

import os
from typing import Optional

class Config:
    def __init__(self):
        """Initialize configuration from environment variables"""
        
        # Gemini API
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Email Configuration
        self.email_provider = os.getenv('EMAIL_PROVIDER', 'gmail').lower()
        self.email_from = os.getenv('EMAIL_FROM')
        self.email_to = os.getenv('EMAIL_TO', self.email_from)  # Default to same as from
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        if not self.email_from or not self.email_password:
            raise ValueError("EMAIL_FROM and EMAIL_PASSWORD are required")
        
        # AWS SES Configuration (if using SES)
        if self.email_provider == 'ses':
            self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
            self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if not self.aws_access_key or not self.aws_secret_key:
                raise ValueError("AWS credentials are required for SES")
        
        # Debug mode
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'