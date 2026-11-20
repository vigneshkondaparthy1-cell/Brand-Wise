import json
import os
import unittest
from unittest.mock import patch

import audit_chat


class AuditChatTests(unittest.TestCase):
    def test_chat_requires_an_ai_provider(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': '', 'OPENAI_API_KEY': ''}):
            with self.assertRaisesRegex(RuntimeError, 'Configure GEMINI_API_KEY'):
                audit_chat.answer({'findings': []}, 'What should I change?', [])

    def test_gemini_receives_saved_audit_and_follow_up_context(self):
        audit = {'title': 'Home page', 'content': 'Guaranteed results', 'findings': [
            {'id': 'F1', 'title': 'Unsupported promise', 'severity': 'High', 'why': 'No evidence supplied'}]}
        response = type('Response', (), {
            '__enter__': lambda self: self,
            '__exit__': lambda self, *args: None,
            'read': lambda self: json.dumps({'candidates': [{'content': {'parts': [{'text': 'Revise the promise in F1.'}]}}]}).encode(),
        })()
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key', 'OPENAI_API_KEY': ''}):
            with patch('audit_chat.urllib.request.urlopen', return_value=response) as send:
                result = audit_chat.answer(audit, 'How should I fix it?', [{'role': 'user', 'content': 'What went wrong?'}])
        self.assertEqual(result, 'Revise the promise in F1.')
        request = send.call_args.args[0]
        payload = json.loads(request.data)
        sent = payload['contents'][0]['parts'][0]['text']
        self.assertIn('Unsupported promise', sent)
        self.assertIn('What went wrong?', sent)
        self.assertIn('How should I fix it?', sent)
        self.assertEqual(request.headers['X-goog-api-key'], 'test-key')


if __name__ == '__main__':
    unittest.main()
