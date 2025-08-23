#!/usr/bin/env python3
"""
Gemini API Client Module
Integrates with Google Gemini AI for generating Bible diary entries
"""

import google.generativeai as genai
import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: str):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """Load prompt template from file"""
        try:
            template_path = os.path.join(os.path.dirname(__file__), 'template_prompt.txt')
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # Default template
                return self._get_default_template()
        except Exception as e:
            logger.warning(f"Could not load template file: {str(e)}, using default")
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Default prompt template"""
        return """
Please create a thoughtful and personal Bible diary entry based on today's readings.

Today's Bible Readings:
{bible_content}

Please write a diary entry that:
1. Reflects on the key themes and messages from today's readings
2. Connects the biblical teachings to modern daily life
3. Includes personal insights and practical applications
4. Maintains a warm, contemplative, and inspiring tone
5. Is approximately 300-500 words long

The diary entry should help the reader:
- Understand the deeper meaning of the scriptures
- Find practical ways to apply these teachings
- Feel encouraged and spiritually uplifted
- Connect with God through reflection

Please write this as a personal diary entry, using a warm and reflective tone.
"""
    
    def generate_diary_entry(self, bible_content: Dict[str, str]) -> Optional[str]:
        """
        Generate a diary entry based on Bible readings
        
        Args:
            bible_content: Dictionary containing Bible readings
            
        Returns:
            Generated diary entry or None if failed
        """
        try:
            # Format bible content for prompt
            formatted_content = self._format_bible_content(bible_content)
            
            # Create prompt
            prompt = self.prompt_template.format(bible_content=formatted_content)
            
            logger.info("Generating diary entry with Gemini AI...")
            
            # Generate content
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                )
            )
            
            if response and response.text:
                logger.info("Successfully generated diary entry")
                return response.text.strip()
            else:
                logger.error("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Error generating diary entry: {str(e)}")
            return None
    
    def _format_bible_content(self, bible_content: Dict[str, str]) -> str:
        """Format Bible content for the AI prompt"""
        formatted_parts = []
        
        # Add date
        if 'date' in bible_content:
            formatted_parts.append(f"Date: {bible_content['date']}")
        
        # Add readings in order
        reading_order = [
            'First Reading',
            'Responsorial Psalm',
            'Second Reading', 
            'Alleluia',
            'Gospel'
        ]
        
        for reading_type in reading_order:
            if reading_type in bible_content:
                formatted_parts.append(f"\n{reading_type}:\n{bible_content[reading_type]}")
        
        # Add any other content
        if 'content' in bible_content:
            formatted_parts.append(f"\nAdditional Content:\n{bible_content['content']}")
        
        return "\n".join(formatted_parts)