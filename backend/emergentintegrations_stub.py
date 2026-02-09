"""
Stub for emergentintegrations package (not available on PyPI)
This allows the app to run with graceful degradation when the package is unavailable
"""

class UserMessage:
    def __init__(self, content=None):
        self.content = content

class ImageContent:
    def __init__(self, data=None, media_type=None):
        self.data = data
        self.media_type = media_type

class FileContentWithMimeType:
    def __init__(self, data=None, mime_type=None):
        self.data = data
        self.mime_type = mime_type

class LlmChat:
    def __init__(self, **kwargs):
        self.model = kwargs.get('model')
    
    async def acompletion(self, **kwargs):
        return {"choices": [{"message": {"content": ""}}]}

# Create namespace for imports
class EmergentIntegrations:
    class llm:
        chat = type('chat', (), {
            'LlmChat': LlmChat,
            'UserMessage': UserMessage,
            'ImageContent': ImageContent,
            'FileContentWithMimeType': FileContentWithMimeType
        })()

import sys
emergentintegrations = EmergentIntegrations()
sys.modules['emergentintegrations'] = emergentintegrations
sys.modules['emergentintegrations.llm'] = emergentintegrations.llm
sys.modules['emergentintegrations.llm.chat'] = emergentintegrations.llm.chat
