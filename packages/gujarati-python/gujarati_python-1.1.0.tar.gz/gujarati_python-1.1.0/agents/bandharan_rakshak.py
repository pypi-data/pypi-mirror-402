import re
from typing import List, Dict

class BandharanRakshak:
    """
    બંધારણ રક્ષક - Structure/Syntax Guardian
    Ensures the integrity of the Gujarati-Python code structure.
    """

    def check_file(self, content: str) -> List[Dict]:
        """
        Checks a file for structural issues.
        """
        issues = []
        lines = content.split('\n')
        
        # English keywords to check for mixed usage
        english_keywords = {
            'def', 'class', 'return', 'print', 'if', 'else', 'elif', 
            'while', 'for', 'import', 'from', 'try', 'except'
        }
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped_line = line.strip()
            
            if not stripped_line or stripped_line.startswith('#'):
                continue
            
            # 1. Check for mixed English/Gujarati keywords
            # This is a simple check; it might flag strings, but good for a warning
            words = set(re.findall(r'\b[a-z]+\b', stripped_line))
            common = words.intersection(english_keywords)
            if common:
                issues.append({
                    'line': line_num,
                    'type': 'mixed_language',
                    'message': f"ચેતવણી: લાઈનમાં અંગ્રેજી કીવર્ડ્સ વપરાયા છે: {', '.join(common)}. કૃપા કરીને ગુજરાતી કીવર્ડ્સ વાપરો.",
                    'severity': 'warning'
                })

            # 2. Indentation Check (Basic)
            # Python relies on consistent indentation. 
            # We can check if indentation is a multiple of 4 spaces (standard)
            indentation = len(line) - len(line.lstrip(' '))
            if indentation > 0 and indentation % 4 != 0:
                issues.append({
                    'line': line_num,
                    'type': 'indentation',
                    'message': f"ઈન્ડેન્ટેશન 4 સ્પેસના ગુણાંકમાં હોવું જોઈએ (વર્તમાન: {indentation}).",
                    'severity': 'info' # Just info because 2 spaces is valid Python, though not PEP8
                })

        return issues
