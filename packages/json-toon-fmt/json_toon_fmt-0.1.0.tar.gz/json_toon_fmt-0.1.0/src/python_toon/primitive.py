"""
Primitive data types and related utilities.
"""

from .types import jsonPrimitive

class PrimitiveUtils:
    def __init__ (self):
        self.escape_sequences = {'\\', '"', '\n', '\r', '\t', '\b', '\f'}

    def encode_primitive(self, value: jsonPrimitive, delimiter: str) -> str:
        if value is None:
            return 'null'
        
        if isinstance(value, bool):
            return 'true' if value else 'false'
        
        if isinstance(value, (int, float)):
            return str(value)

        return self._encode_string(value, delimiter)

    def _encode_string(self, value: str, delimiter: str) -> str:
        if self._need_quotes(value, delimiter):
          escaped=self._escape_string(value)
          return f'"{escaped}"'

        return value
 
    def _escape_string(self, value: str) -> str:
        """Escape special characters in string."""
        result = []
        for char in value:
            if char == '\\':
                result.append('\\\\')
            elif char == '"':
                result.append('\\"')
            elif char == '\n':
                result.append('\\n')
            elif char == '\r':
                result.append('\\r')
            elif char == '\t':
                result.append('\\t')
            elif char == '\b':
                result.append('\\b')
            elif char == '\f':
                result.append('\\f')
            else:
                result.append(char)
            
        return ''.join(result)


    def _need_quotes(self, value: str, delimiter: str) -> bool:
        if not value:
            return True
        
        special_chars = {delimiter, ':', '"', '\\', '\n', '\r', '\t'}
        if any(char in special_chars for char in value):
            return True
        
        if value!= value.strip():
            return True
        
        if value.lower() in {'true', 'false', 'null'}:
            return True

        if self._looks_like_number(value):
            return True
        
        if value.startswith('- '):
            return True
        
        if self._looks_like_structured_token(value):
            return True
        
        return False
    
    def _looks_like_number(self, value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _looks_like_structured_token(self, value: str) -> bool:
        import re
        
        if re.match(r'^\[\d+\]$', value):
            return True
        
        if re.match(r'^\{[^}]+\}$', value):
            return True

        if re.match(r'^\[\d+\]: .+$', value):
            return True

        return False
    
    