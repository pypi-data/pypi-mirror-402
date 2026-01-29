"""
Privacy-Preserving Data Redaction
==================================

Redacts sensitive information before sending to verification LLM.
"""

import re
from typing import Dict, Pattern


class SentinelRedactor:
    """
    Redacts sensitive data to protect privacy during verification.
    
    Supports:
    - Email addresses
    - API keys and tokens
    - Financial amounts
    - Phone numbers
    - Credit card numbers
    - Custom patterns
    """
    
    DEFAULT_PATTERNS: Dict[str, str] = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'currency': r'\$\d+(?:,\d{3})*(?:\.\d+)?',
        'api_key': r'\b[A-Za-z0-9]{32,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b'
    }
    
    def __init__(self, custom_patterns: Dict[str, str] = None):
        """
        Initialize redactor with optional custom patterns.
        
        Args:
            custom_patterns: Dictionary of {name: regex_pattern} to add/override
        """
        self.patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)
    
    def redact(self, text: str) -> str:
        """
        Redact sensitive information from text.
        
        Args:
            text: Input text potentially containing sensitive data
            
        Returns:
            Redacted text with sensitive data replaced
        """
        if not text:
            return text
            
        redacted = text
        
        # Apply all patterns
        for name, pattern in self.patterns.items():
            replacement = f'[{name.upper()}_REDACTED]'
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
        
        return redacted
    
    def add_pattern(self, name: str, pattern: str):
        """
        Add a custom redaction pattern.
        
        Args:
            name: Name for the pattern (e.g., 'ip_address')
            pattern: Regex pattern to match
        """
        self.patterns[name] = pattern
    
    def remove_pattern(self, name: str):
        """
        Remove a redaction pattern.
        
        Args:
            name: Name of the pattern to remove
        """
        self.patterns.pop(name, None)
