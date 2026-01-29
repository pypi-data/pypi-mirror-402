"""
Formatting Utilities

Common formatting utilities for FireFeed microservices.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any, List
import re

logger = logging.getLogger(__name__)


def format_datetime(dt: Union[datetime, str], 
                   format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format datetime object or string.
    
    Args:
        dt: Datetime object or ISO string
        format_str: Output format string
        
    Returns:
        Formatted datetime string
    """
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        elif isinstance(dt, datetime):
            pass
        else:
            raise ValueError("Input must be datetime object or ISO string")
        
        return dt.strftime(format_str)
        
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return str(dt)


def format_file_size(size_bytes: Union[int, float]) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable file size string
    """
    try:
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.2f} {size_names[i]}"
        
    except Exception as e:
        logger.error(f"Error formatting file size: {e}")
        return str(size_bytes)


def format_number(number: Union[int, float], 
                 decimal_places: int = 2,
                 thousands_separator: str = ',') -> str:
    """
    Format number with decimal places and thousands separator.
    
    Args:
        number: Number to format
        decimal_places: Number of decimal places
        thousands_separator: Thousands separator character
        
    Returns:
        Formatted number string
    """
    try:
        if isinstance(number, int):
            return f"{number:,}".replace(",", thousands_separator)
        else:
            format_str = f"{{:,.{decimal_places}f}}"
            formatted = format_str.format(number)
            return formatted.replace(",", thousands_separator)
            
    except Exception as e:
        logger.error(f"Error formatting number: {e}")
        return str(number)


def format_currency(amount: Union[int, float], 
                   currency: str = 'USD',
                   symbol: Optional[str] = None) -> str:
    """
    Format currency amount.
    
    Args:
        amount: Amount to format
        currency: Currency code
        symbol: Currency symbol (if None, uses default for currency)
        
    Returns:
        Formatted currency string
    """
    try:
        # Default currency symbols
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'RUB': '₽',
            'JPY': '¥',
            'CNY': '¥'
        }
        
        if symbol is None:
            symbol = currency_symbols.get(currency.upper(), currency)
        
        formatted_amount = format_number(amount, 2)
        return f"{symbol}{formatted_amount}"
        
    except Exception as e:
        logger.error(f"Error formatting currency: {e}")
        return f"{currency} {amount}"


def slugify(text: str, max_length: int = 100, separator: str = '-') -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to slugify
        max_length: Maximum slug length
        separator: Word separator
        
    Returns:
        Slugified string
    """
    try:
        # Convert to lowercase
        text = text.lower()
        
        # Replace special characters with separator
        text = re.sub(r'[^a-z0-9]+', separator, text)
        
        # Remove leading/trailing separators
        text = text.strip(separator)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length].rstrip(separator)
        
        return text
        
    except Exception as e:
        logger.error(f"Error slugifying text: {e}")
        return ""


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human-readable duration string
    """
    try:
        if seconds < 0:
            return "0 seconds"
        
        # Calculate time components
        td = timedelta(seconds=seconds)
        
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Build components
        components = []
        
        if days > 0:
            components.append(f"{days} day{'s' if days != 1 else ''}")
        
        if hours > 0:
            components.append(f"{hours} hour{'s' if hours != 1 else ''}")
        
        if minutes > 0:
            components.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        
        if seconds > 0 or not components:
            components.append(f"{int(seconds)} second{'s' if seconds != 1 else ''}")
        
        return ", ".join(components)
        
    except Exception as e:
        logger.error(f"Error formatting duration: {e}")
        return str(seconds)


def format_percentage(value: Union[int, float], 
                     decimal_places: int = 2) -> str:
    """
    Format percentage value.
    
    Args:
        value: Percentage value (0-100)
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    try:
        format_str = f"{{:.{decimal_places}f}}%"
        return format_str.format(value)
        
    except Exception as e:
        logger.error(f"Error formatting percentage: {e}")
        return f"{value}%"


def format_bytes(bytes_value: Union[int, float]) -> str:
    """
    Format bytes in human-readable format.
    
    Args:
        bytes_value: Bytes value
        
    Returns:
        Human-readable bytes string
    """
    return format_file_size(bytes_value)


def format_memory_size(size_bytes: Union[int, float]) -> str:
    """
    Format memory size in human-readable format.
    
    Args:
        size_bytes: Memory size in bytes
        
    Returns:
        Human-readable memory size string
    """
    return format_file_size(size_bytes)


def format_table(data: List[Dict[str, Any]], 
                columns: Optional[List[str]] = None,
                headers: Optional[List[str]] = None) -> str:
    """
    Format data as ASCII table.
    
    Args:
        data: List of dictionaries
        columns: List of column keys to include
        headers: List of column headers
        
    Returns:
        ASCII table string
    """
    try:
        if not data:
            return "No data to display"
        
        # Determine columns
        if columns is None:
            columns = list(data[0].keys())
        
        # Determine headers
        if headers is None:
            headers = [col.title() for col in columns]
        
        # Calculate column widths
        widths = []
        for col in columns:
            max_width = len(str(headers[columns.index(col)]))
            for row in data:
                max_width = max(max_width, len(str(row.get(col, ''))))
            widths.append(max_width)
        
        # Build table
        separator = "+" + "+".join(["-" * (w + 2) for w in widths]) + "+"
        
        # Header row
        header_row = "| " + " | ".join([str(h).ljust(w) for h, w in zip(headers, widths)]) + " |"
        
        # Data rows
        data_rows = []
        for row in data:
            row_str = "| " + " | ".join([str(row.get(col, '')).ljust(w) for col, w in zip(columns, widths)]) + " |"
            data_rows.append(row_str)
        
        # Combine all parts
        table_parts = [separator, header_row, separator] + data_rows + [separator]
        
        return "\n".join(table_parts)
        
    except Exception as e:
        logger.error(f"Error formatting table: {e}")
        return str(data)


def format_json(data: Any, indent: int = 2) -> str:
    """
    Format data as JSON string.
    
    Args:
        data: Data to format
        indent: JSON indentation
        
    Returns:
        Formatted JSON string
    """
    try:
        import json
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error formatting JSON: {e}")
        return str(data)


def format_yaml(data: Any) -> str:
    """
    Format data as YAML string.
    
    Args:
        data: Data to format
        
    Returns:
        Formatted YAML string
    """
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        
    except Exception as e:
        logger.error(f"Error formatting YAML: {e}")
        return str(data)


def format_list(items: List[Any], 
               separator: str = ', ',
               quote_char: str = '"') -> str:
    """
    Format list as string.
    
    Args:
        items: List of items
        separator: Item separator
        quote_char: Quote character for strings
        
    Returns:
        Formatted list string
    """
    try:
        formatted_items = []
        for item in items:
            if isinstance(item, str):
                formatted_items.append(f"{quote_char}{item}{quote_char}")
            else:
                formatted_items.append(str(item))
        
        return separator.join(formatted_items)
        
    except Exception as e:
        logger.error(f"Error formatting list: {e}")
        return str(items)


def format_code_block(code: str, language: str = '') -> str:
    """
    Format code as markdown code block.
    
    Args:
        code: Code string
        language: Programming language
        
    Returns:
        Markdown code block string
    """
    try:
        return f"```{language}\n{code}\n```"
        
    except Exception as e:
        logger.error(f"Error formatting code block: {e}")
        return code