"""
Custom Presidio recognizers for improved entity detection.

This module provides enhanced recognizers that supplement or replace
Presidio's default implementations:
- PhonePatternRecognizer: Catches phone patterns missed by phonenumbers lib
- ModernUrlRecognizer: Supports modern protocols (git, ssh, ipfs, onion addresses)
"""

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class PhonePatternRecognizer(PatternRecognizer):
    """
    Regex-based phone number recognizer to supplement Presidio's phonenumbers-based recognizer.
    
    This recognizer catches phone-like patterns that the phonenumbers library might miss,
    such as local numbers (e.g., "747-1234") or numbers in non-standard formats.
    
    Uses a lower confidence score (0.3) to work alongside PhoneRecognizer,
    allowing validation-based detection to take precedence.
    
    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """
    
    PATTERNS = [
        Pattern(
            "Phone Pattern",
            r"(?!\d{1,3}\.\d{1,3}\b)(?:(?:\+(?:\d{1,3}[ .-]?)?(?:\(\d{1,3}\)[ .-]?)?)(?:\d{2,5}[- ]?){2,}|\d{3,5}[- ]\d{3,5}(?:[- ]\d{2,5}){0,2})\b",
            0.5,  # Lower score to allow phonenumbers-based recognizer to take precedence
        ),
    ]
    
    CONTEXT = ["phone", "number", "telephone", "cell", "cellphone", "mobile", "call", "contact"]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "PHONE_NUMBER",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )


class ModernUrlRecognizer(PatternRecognizer):
    """
    Enhanced URL recognizer supporting modern protocols and future-proof TLD matching.
    
    Advantages over Presidio's default UrlRecognizer:
    - Supports modern protocols: git://, ssh://, ipfs://, ipns://, onion://
    - Native .onion address support (Tor hidden services)
    - Generic TLD pattern instead of hardcoded list (future-proof)
    - More compact and maintainable
    
    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """
    
    PATTERNS = [
        Pattern(
            "Modern URL",
            r"\b(?:(?:https?|ftp|sftp|ftps|ssh|file|mailto|git|onion|ipfs|ipns):\/\/|www\.)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}(?::\d+)?(?:\/(?:[-a-z0-9\/_.,~%+:@]|(?:%[0-9a-f]{2}))*)?(?:\?(?:[-a-z0-9\/_.,~%+:@=&]|(?:%[0-9a-f]{2}))*)?(?:#(?:[-a-z0-9\/_.,~%+:@=&]|(?:%[0-9a-f]{2}))*)?|(?:https?:\/\/)?[a-z2-7]{16,56}\.onion(?:\/(?:[-a-z0-9\/_.,~%+:@]|(?:%[0-9a-f]{2}))*)?(?:\?(?:[-a-z0-9\/_.,~%+:@=&]|(?:%[0-9a-f]{2}))*)?(?:#(?:[-a-z0-9\/_.,~%+:@=&]|(?:%[0-9a-f]{2}))*)\b",
            0.8,
        ),
    ]
    
    CONTEXT = ["url", "file","website", "link", "http", "https", "git", "repository", "onion"]
    
    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        supported_entity: str = "URL",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

