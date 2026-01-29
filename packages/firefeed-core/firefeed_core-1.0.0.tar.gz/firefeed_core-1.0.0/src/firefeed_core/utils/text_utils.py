"""
Text Utilities

Common text processing utilities for FireFeed microservices.
"""

import re
import html
import logging
import unicodedata
from typing import List, Optional, Set, Dict, Any
from collections import Counter

logger = logging.getLogger(__name__)


def clean_text(text: str, remove_html: bool = True, normalize_unicode: bool = True,
               remove_extra_whitespace: bool = True, max_length: Optional[int] = None) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Input text
        remove_html: Remove HTML tags
        normalize_unicode: Normalize unicode characters
        remove_extra_whitespace: Remove extra whitespace
        max_length: Maximum text length
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    if remove_html:
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize unicode
    if normalize_unicode:
        text = unicodedata.normalize('NFKD', text)
    
    # Remove extra whitespace
    if remove_extra_whitespace:
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
    
    # Limit length
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip()
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Find last space before max_length to avoid cutting words
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Only break words if necessary
        truncated = truncated[:last_space]
    
    return truncated + suffix


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 10,
                    stop_words: Optional[Set[str]] = None) -> List[str]:
    """
    Extract keywords from text.
    
    Args:
        text: Input text
        min_length: Minimum word length
        max_keywords: Maximum number of keywords
        stop_words: Set of stop words to ignore
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Default stop words
    if stop_words is None:
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'can', 'may', 'might', 'must', 'shall', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
    
    # Clean and tokenize
    text = clean_text(text, remove_html=True, normalize_unicode=True)
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter words
    filtered_words = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Count and sort by frequency
    word_counts = Counter(filtered_words)
    keywords = [word for word, count in word_counts.most_common(max_keywords)]
    
    return keywords


def normalize_text(text: str, lowercase: bool = True, remove_punctuation: bool = False,
                  remove_numbers: bool = False) -> str:
    """
    Normalize text by applying various transformations.
    
    Args:
        text: Input text
        lowercase: Convert to lowercase
        remove_punctuation: Remove punctuation
        remove_numbers: Remove numbers
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    if lowercase:
        text = text.lower()
    
    if remove_punctuation:
        text = re.sub(r'[^\w\s]', '', text)
    
    if remove_numbers:
        text = re.sub(r'\d+', '', text)
    
    return text.strip()


def sanitize_html(text: str, allowed_tags: Optional[List[str]] = None) -> str:
    """
    Sanitize HTML content.
    
    Args:
        text: Input text with HTML
        allowed_tags: List of allowed HTML tags
        
    Returns:
        Sanitized HTML text
    """
    if not text:
        return ""
    
    if allowed_tags is None:
        allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'p', 'br', 'a']
    
    # Remove dangerous tags
    dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input']
    for tag in dangerous_tags:
        text = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(rf'<{tag}[^>]*/>', '', text, flags=re.IGNORECASE)
    
    # Allow only specified tags
    if allowed_tags:
        pattern = r'<(?!/?(' + '|'.join(allowed_tags) + r')\b)[^>]+>'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Input text
        
    Returns:
        List of URLs
    """
    if not text:
        return []
    
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+/?[\w\-.?=/&%+]*'
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Input text
        
    Returns:
        List of email addresses
    """
    if not text:
        return []
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_emails = []
    for email in emails:
        if email not in seen:
            seen.add(email)
            unique_emails.append(email)
    
    return unique_emails


def count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Input text
        
    Returns:
        Word count
    """
    if not text:
        return 0
    
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def count_characters(text: str, include_spaces: bool = True) -> int:
    """
    Count characters in text.
    
    Args:
        text: Input text
        include_spaces: Include spaces in count
        
    Returns:
        Character count
    """
    if not text:
        return 0
    
    if include_spaces:
        return len(text)
    else:
        return len(text.replace(' ', ''))


def detect_language(text: str) -> str:
    """
    Simple language detection based on character frequency.
    
    Args:
        text: Input text
        
    Returns:
        Detected language code
    """
    if not text:
        return "unknown"
    
    # Simple heuristic based on common characters
    text_lower = text.lower()
    
    # Russian detection
    russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    russian_count = sum(1 for char in text_lower if char in russian_chars)
    
    # German detection
    german_chars = set('äöüß')
    german_count = sum(1 for char in text_lower if char in german_chars)
    
    # French detection
    french_chars = set('àâäéèêëîïôöùûüÿç')
    french_count = sum(1 for char in text_lower if char in french_chars)
    
    # English is default if no other language detected
    if russian_count > len(text) * 0.1:
        return "ru"
    elif german_count > 0:
        return "de"
    elif french_count > 0:
        return "fr"
    else:
        return "en"


def format_text_for_display(text: str, max_line_length: int = 80) -> str:
    """
    Format text for display with proper line breaks.
    
    Args:
        text: Input text
        max_line_length: Maximum line length
        
    Returns:
        Formatted text
    """
    if not text:
        return ""
    
    # Split into words
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        # Check if adding this word would exceed line length
        word_length = len(word)
        if current_length + len(current_line) + word_length > max_line_length:
            # Start new line
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length
        else:
            # Add to current line
            current_line.append(word)
            current_length += word_length
    
    # Add final line
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)


def remove_duplicate_words(text: str) -> str:
    """
    Remove consecutive duplicate words.
    
    Args:
        text: Input text
        
    Returns:
        Text with duplicate words removed
    """
    if not text:
        return ""
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # Check if this word is the same as the previous one
        if i == 0 or word.lower() != words[i-1].lower():
            result.append(word)
    
    return ' '.join(result)


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Input text
        
    Returns:
        List of hashtags
    """
    if not text:
        return []
    
    hashtag_pattern = r'#([a-zA-Z0-9_]+)'
    hashtags = re.findall(hashtag_pattern, text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_hashtags = []
    for hashtag in hashtags:
        if hashtag not in seen:
            seen.add(hashtag)
            unique_hashtags.append(hashtag)
    
    return unique_hashtags


def extract_mentions(text: str) -> List[str]:
    """
    Extract mentions (@username) from text.
    
    Args:
        text: Input text
        
    Returns:
        List of mentions
    """
    if not text:
        return []
    
    mention_pattern = r'@([a-zA-Z0-9_]+)'
    mentions = re.findall(mention_pattern, text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_mentions = []
    for mention in mentions:
        if mention not in seen:
            seen.add(mention)
            unique_mentions.append(mention)
    
    return unique_mentions