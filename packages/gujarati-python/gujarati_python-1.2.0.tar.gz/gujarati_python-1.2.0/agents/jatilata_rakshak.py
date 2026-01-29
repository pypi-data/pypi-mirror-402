from typing import List, Dict

class JatilataRakshak:
    """
    જટિલતા રક્ષક - Complexity Guardian
    Measures code complexity to ensure maintainability.
    """

    def check_file(self, content: str) -> List[Dict]:
        issues = []
        lines = content.split('\n')
        
        current_function = None
        current_function_lines = 0
        current_function_start = 0
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            
            # Check nesting depth
            indent = len(line) - len(line.lstrip(' '))
            # Assuming 4 spaces per indent, > 4 levels (16 spaces) is deep
            if indent > 16:
                 issues.append({
                    'line': line_num,
                    'type': 'complexity_nesting',
                    'message': "બહુ ઊંડું નેસ્ટિંગ (Nesting) છે. કોડને સરળ બનાવો.",
                    'severity': 'info'
                })

            # Check function length
            if stripped.startswith('ડેફ ') or stripped.startswith('def '):
                # If we were in a function, check its length ? 
                # (Simple parser limitation: we only check previous func if we hit a new one or file ends)
                if current_function:
                    self._check_func_len(issues, current_function, current_function_lines, current_function_start)
                
                current_function = stripped.split('(')[0] # inaccurate name parsing but fine for ID
                current_function_start = line_num
                current_function_lines = 0
            
            if current_function:
                current_function_lines += 1
                
                # Check for end of logical block (dedent to 0) - rough heuristic
                if indent == 0 and not (stripped.startswith('ડેફ ') or stripped.startswith('def ')) and stripped and not stripped.startswith('#') and not stripped.startswith('"""'):
                     self._check_func_len(issues, current_function, current_function_lines, current_function_start)
                     current_function = None

        # Check last function
        if current_function:
            self._check_func_len(issues, current_function, current_function_lines, current_function_start)

        return issues

    def _check_func_len(self, issues, func_name, lines, start_line):
        if lines > 50:
            issues.append({
                'line': start_line,
                'type': 'complexity_length',
                'message': f"ફંક્શન બહુ લાંબુ છે ({lines} લાઈનો). તેને નાના ભાગોમાં વહેંચો.",
                'severity': 'warning'
            })
