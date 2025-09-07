#!/usr/bin/env python3
"""
Test Vietnamese content generation for Magisterium client
Tests the generate_psalm_reflection function's ability to produce Vietnamese content.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from magisterium.magisterium_client import MagisteriumClient


class TestMagisteriumVietnamese(unittest.TestCase):
    """Test Vietnamese content generation in MagisteriumClient"""

    def setUp(self):
        """Set up test environment"""
        self.sample_psalm_content = {
            'psalm_citation': 'Psalm 95:1-2, 6-7, 8-9',
            'psalm_body': '''O come, let us sing to the Lord;
    let us make a joyful noise to the rock of our salvation!
Let us come into his presence with thanksgiving;
    let us make a joyful noise to him with songs of praise!

O come, let us worship and bow down,
    let us kneel before the Lord, our Maker!
For he is our God,
    and we are the people of his pasture,
    and the sheep of his hand.

O that today you would listen to his voice!
    Do not harden your hearts, as at Meribah,
    as on the day at Massah in the wilderness,
when your ancestors tested me,
    and put me to the proof, though they had seen my work.''',
            'psalm_link': 'https://bible.usccb.org/bible/readings/092925.cfm',
            'url': 'https://bible.usccb.org/bible/readings/092925.cfm',
            'date': '2025-09-29'
        }

        # Mock Vietnamese response that includes both sections
        self.mock_vietnamese_response = """Suy niệm:
Thánh vịnh 95 mời gọi chúng ta hãy ca ngợi Chúa với lòng biết ơn và niềm vui. Đây không chỉ là một lời mời gọi đơn thuần mà là một lời kêu gọi sâu sắc để chúng ta nhận ra Thiên Chúa là Đấng Tạo Hóa và là Mục Tử của chúng ta. Khi chúng ta "đến trước mặt Người với lòng biết ơn", chúng ta thừa nhận rằng mọi ơn phước trong cuộc sống đều đến từ Thiên Chúa.

Hình ảnh "đàn chiên trong tay Người" thể hiện mối quan hệ thân mật giữa Thiên Chúa và con người. Chúng ta không phải là những người xa lạ mà là con em được Người yêu thương và chăm sóc. Thánh vịnh cũng nhắc nhở: "Ước gì hôm nay các bạn nghe tiếng Người!" - đây là lời mời gọi chúng ta hãy mở lòng để lắng nghe và đáp ứng tiếng gọi của Thiên Chúa trong cuộc sống hàng ngày.

Cầu nguyện:
Lạy Chúa, xin giúp con luôn ca ngợi và tôn vinh Chúa bằng cả cuộc đời mình. Xin cho con biết lắng nghe tiếng Chúa trong mỗi ngày và không cứng lòng trước tình yêu của Chúa. Xin Chúa làm cho con trở thành con chiên ngoan ngoãn, luôn tin tưởng và theo Chúa. Qua Chúa Kitô, Chúa chúng con. Amen."""

    def test_generate_psalm_reflection_with_mock_api(self):
        """Test generate_psalm_reflection with mocked API response"""
        with patch.dict(os.environ, {'MAGISTERIUM_API_KEY': 'test_key'}):
            client = MagisteriumClient()
            
            # Mock the HTTP request
            with patch('requests.post') as mock_post:
                # Setup mock response
                mock_response = MagicMock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = {
                    'choices': [{
                        'message': {
                            'content': self.mock_vietnamese_response
                        }
                    }]
                }
                mock_post.return_value = mock_response
                
                # Test the function
                result = client.generate_psalm_reflection(self.sample_psalm_content)
                
                # Verify the result
                self.assertIsNotNone(result)
                self.assertIsInstance(result, str)
                
                # Check that it contains Vietnamese content
                self.assertIn('Suy niệm:', result)
                self.assertIn('Cầu nguyện:', result)
                self.assertIn('Thánh vịnh', result)
                self.assertIn('Thiên Chúa', result)
                self.assertIn('Chúa', result)
                
                # Verify API was called correctly
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                
                # Check the payload structure
                payload = call_args[1]['json']
                self.assertEqual(payload['model'], 'magisterium-1')
                self.assertIn('messages', payload)
                
                # Check that messages include system prompts and user content
                messages = payload['messages']
                self.assertTrue(any(msg['role'] == 'system' for msg in messages))
                self.assertTrue(any(msg['role'] == 'user' for msg in messages))
                
                # Check user message contains Vietnamese structure
                user_message = next(msg for msg in messages if msg['role'] == 'user')
                self.assertIn('Thánh vịnh hôm nay:', user_message['content'])
                self.assertIn('Suy niệm:', user_message['content'])
                self.assertIn('Cầu nguyện:', user_message['content'])

    def test_generate_psalm_reflection_with_vietnamese_bible_text(self):
        """Test that Vietnamese Bible text is included when available"""
        with patch.dict(os.environ, {'MAGISTERIUM_API_KEY': 'test_key'}):
            client = MagisteriumClient()
            
            # Mock the Vietnamese text retrieval
            vietnamese_psalm_text = "Hãy đến ca ngợi Chúa, hãy reo mừng Đá Tảng cứu độ chúng ta!"
            
            with patch.object(client, 'get_vietnamese_psalm_text', return_value=vietnamese_psalm_text):
                with patch('requests.post') as mock_post:
                    # Setup mock response
                    mock_response = MagicMock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.json.return_value = {
                        'choices': [{
                            'message': {
                                'content': self.mock_vietnamese_response
                            }
                        }]
                    }
                    mock_post.return_value = mock_response
                    
                    # Test the function
                    result = client.generate_psalm_reflection(self.sample_psalm_content)
                    
                    # Verify Vietnamese Bible text was used
                    call_args = mock_post.call_args
                    payload = call_args[1]['json']
                    user_message = next(msg for msg in payload['messages'] if msg['role'] == 'user')
                    
                    # Check that the Vietnamese psalm text is included
                    self.assertIn(vietnamese_psalm_text, user_message['content'])

    def test_generate_psalm_reflection_without_vietnamese_bible_text(self):
        """Test fallback when Vietnamese Bible text is not available"""
        with patch.dict(os.environ, {'MAGISTERIUM_API_KEY': 'test_key'}):
            client = MagisteriumClient()
            
            # Mock no Vietnamese text available
            with patch.object(client, 'get_vietnamese_psalm_text', return_value=None):
                with patch('requests.post') as mock_post:
                    # Setup mock response
                    mock_response = MagicMock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.json.return_value = {
                        'choices': [{
                            'message': {
                                'content': self.mock_vietnamese_response
                            }
                        }]
                    }
                    mock_post.return_value = mock_response
                    
                    # Test the function
                    result = client.generate_psalm_reflection(self.sample_psalm_content)
                    
                    # Verify fallback to citation
                    call_args = mock_post.call_args
                    payload = call_args[1]['json']
                    user_message = next(msg for msg in payload['messages'] if msg['role'] == 'user')
                    
                    # Should fallback to the psalm citation
                    self.assertIn('Psalm 95:1-2, 6-7, 8-9', user_message['content'])

    def test_vietnamese_content_structure_validation(self):
        """Test that the returned content follows expected Vietnamese structure"""
        result = self.mock_vietnamese_response
        
        # Test structure validation
        self.assertIn('Suy niệm:', result)
        self.assertIn('Cầu nguyện:', result)
        
        # Split into sections
        parts = result.split('Cầu nguyện:')
        self.assertEqual(len(parts), 2, "Should have exactly one 'Cầu nguyện:' divider")
        
        meditation_part = parts[0].replace('Suy niệm:', '').strip()
        prayer_part = parts[1].strip()
        
        # Verify both sections have content
        self.assertTrue(len(meditation_part) > 50, "Meditation section should have substantial content")
        self.assertTrue(len(prayer_part) > 50, "Prayer section should have substantial content")
        
        # Check for Catholic/Vietnamese terms
        catholic_terms = ['Thiên Chúa', 'Chúa', 'Thánh vịnh', 'Kitô', 'Amen']
        combined_text = result.lower()
        found_terms = [term for term in catholic_terms if term.lower() in combined_text]
        self.assertTrue(len(found_terms) >= 3, f"Should contain Catholic Vietnamese terms. Found: {found_terms}")

    @patch.dict(os.environ, {'MAGISTERIUM_API_KEY': 'test_key'})
    def test_mg_prompt_integration(self):
        """Test that mg_prompt.txt is loaded and used as system prompt"""
        with patch('builtins.open', create=True) as mock_open:
            mock_mg_prompt = "Bạn là một linh hướng Công Giáo. Hãy viết bằng tiếng Việt theo cấu trúc: Suy niệm và Cầu nguyện."
            mock_open.return_value.__enter__.return_value.read.return_value = mock_mg_prompt
            
            client = MagisteriumClient()
            
            # Verify mg_prompt was loaded
            self.assertIsNotNone(client.extra_system_prompt)
            self.assertEqual(client.extra_system_prompt, mock_mg_prompt)

    def test_api_error_handling(self):
        """Test error handling for API failures"""
        with patch.dict(os.environ, {'MAGISTERIUM_API_KEY': 'test_key'}):
            client = MagisteriumClient()
            
            # Test HTTP error
            with patch('requests.post') as mock_post:
                mock_post.side_effect = Exception("Network error")
                
                result = client.generate_psalm_reflection(self.sample_psalm_content)
                self.assertIsNone(result)

    def test_empty_response_handling(self):
        """Test handling of empty or invalid API responses"""
        with patch.dict(os.environ, {'MAGISTERIUM_API_KEY': 'test_key'}):
            client = MagisteriumClient()
            
            with patch('requests.post') as mock_post:
                # Test empty choices
                mock_response = MagicMock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = {'choices': []}
                mock_post.return_value = mock_response
                
                result = client.generate_psalm_reflection(self.sample_psalm_content)
                self.assertIsNone(result)
                
                # Test missing content
                mock_response.json.return_value = {
                    'choices': [{'message': {}}]
                }
                
                result = client.generate_psalm_reflection(self.sample_psalm_content)
                self.assertIsNone(result)


def main():
    """Run the tests"""
    print("=== Testing Magisterium Vietnamese Content Generation ===")
    
    # Check for required environment (optional for mocked tests)
    if not os.getenv('MAGISTERIUM_API_KEY'):
        print("Note: MAGISTERIUM_API_KEY not set - running with mocked API calls only")
    
    # Run the tests
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()
