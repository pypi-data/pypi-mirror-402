import re
from typing import List, Dict

class SurakshaRakshak:
    """
    સુરક્ષા રક્ષક - Security Guardian
    Detects potential security vulnerabilities.
    """

    def check_file(self, content: str) -> List[Dict]:
        issues = []
        lines = content.split('\n')
        
        # 1. Dangerous Functions
        dangerous_functions = ['eval', 'exec', 'ઈવેલ', 'એક્ઝિક્યુટ']
        
        # 2. Hardcoded Secrets patterns
        secret_patterns = [
            r'password\s*=', r'key\s*=', r'token\s*=', r'secret\s*=',
            r'પાસવર્ડ\s*=', r'કી\s*='
        ]
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            
            if not stripped or stripped.startswith('#'):
                continue
                
            # Check dangerous functions
            for func in dangerous_functions:
                if f"{func}(" in stripped:
                    issues.append({
                        'line': line_num,
                        'type': 'security_danger',
                        'message': f"ચેતવણી: ભયજનક ફંક્શન '{func}()' નો ઉપયોગ ટાળો.",
                        'severity': 'warning'
                    })
            
            # Check secrets
            for pattern in secret_patterns:
                if re.search(pattern, stripped, re.IGNORECASE):
                    issues.append({
                        'line': line_num,
                        'type': 'security_secret',
                        'message': "સંભવિત હાર્ડકોડેડ સિક્રેટ (password/key) મળી આવ્યું છે.",
                        'severity': 'warning'
                    })

        return issues
