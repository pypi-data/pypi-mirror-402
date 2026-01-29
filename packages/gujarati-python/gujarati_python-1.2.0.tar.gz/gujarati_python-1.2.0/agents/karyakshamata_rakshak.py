import re
from typing import List, Dict

class KaryakshamataRakshak:
    """
    કાર્યક્ષમતા રક્ષક - Performance Guardian
    Identifies potential performance issues and optimizations.
    """

    def check_file(self, content: str) -> List[Dict]:
        issues = []
        lines = content.split('\n')
        
        in_function = False
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            
            if not stripped or stripped.startswith('#'):
                continue
                
            if stripped.startswith('ડેફ ') or stripped.startswith('def '):
                in_function = True
            
            # Check for imports inside functions (heuristic)
            if in_function and indentation_level(line) > 0:
                if stripped.startswith('ઈમ્પોર્ટ ') or stripped.startswith('import '):
                     issues.append({
                        'line': line_num,
                        'type': 'perf_import',
                        'message': "ફંક્શનની અંદર ઈમ્પોર્ટ કરવાથી પર્ફોર્મન્સ ઘટી શકે છે. ટોપ-લેવલ ઈમ્પોર્ટ વાપરો.",
                        'severity': 'info'
                    })
            
            # Reset function flag if we hit top level (heuristic - not perfect without robust parser)
            if indentation_level(line) == 0 and not (stripped.startswith('ડેફ ') or stripped.startswith('def ')):
                 in_function = False
            
            # Check for usage of 'global'
            if 'વૈશ્વિક ' in stripped or 'global ' in stripped:
                issues.append({
                    'line': line_num,
                    'type': 'perf_global',
                    'message': "'global' (વૈશ્વિક) વેરિએબલનો ઉપયોગ ટાળો.",
                    'severity': 'info'
                })

        return issues

def indentation_level(line):
    return len(line) - len(line.lstrip(' '))
