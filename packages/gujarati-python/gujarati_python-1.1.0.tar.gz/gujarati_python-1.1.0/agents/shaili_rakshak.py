from typing import List, Dict

class ShailiRakshak:
    """
    શૈલી રક્ષક - Style Guardian
    Enforces coding standards and best practices.
    """

    def check_file(self, content: str) -> List[Dict]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # 1. Check Line Length
            if len(line) > 100:
                issues.append({
                    'line': line_num,
                    'type': 'line_length',
                    'message': f"લાઈન ૩૦૦0 અક્ષરો કરતા લાંબી છે ({len(line)} અક્ષરો).",
                    'severity': 'info'
                })

        # 2. Check for Docstrings in Functions
        # This is a rudimentary check. A full AST parser would be better.
        # We look for 'ડેફ' followed by a line that doesn't have """
        
        in_function_def = False
        function_start_line = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith('ડેફ '):
                in_function_def = True
                function_start_line = i + 1
                continue
            
            if in_function_def:
                # If next non-empty line is not a docstring
                if not stripped:
                    continue
                    
                if not stripped.startswith('"""') and not stripped.startswith("'''"):
                     issues.append({
                        'line': function_start_line,
                        'type': 'missing_docstring',
                        'message': "ફંક્શન માટે ડોક્યુમેન્ટેશન (docstring) ખૂટે છે.",
                        'severity': 'warning'
                    })
                
                in_function_def = False

        return issues
