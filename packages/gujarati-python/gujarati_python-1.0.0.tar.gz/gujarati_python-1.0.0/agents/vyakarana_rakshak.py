import re
from typing import List, Dict, Tuple

class VyakaranRakshak:
    """
    વ્યાકરણ રક્ષક - Grammar Guardian
    Checks for correct spelling of Gujarati keywords and basic linguistic correctness.
    """
    
    def __init__(self):
        # Official Gujarati Python Keywords
        self.keywords = {
            'ઈમ્પોર્ટ', 'ડેફ', 'ક્લાસ', 'ફોર', 'વ્હાઈલ', 'જો', 'નહીં તો', 'અથવા જો',
            'પરત આપો', 'છાપો', 'સાચું', 'ખોટું', 'કંઈ નહીં', 'અને', 'અથવા', 'નહીં',
            'ઇન', 'છે', 'સાથે', 'આસ', 'માંથી', 'પ્રયત્ન કરો', 'સિવાય', 'અંતે',
            'ઊઠાવો', 'લેમ્બડા', 'વૈશ્વિક', 'બિન સ્થાનિક', 'ખાતરી કરો', 'બ્રેક',
            'ચાલુ રાખો', 'પાસ', 'ડિલીટ કરો', 'પ્રદાન કરો', 'અસિન્ક', 'રાહ જુઓ'
        }
        
        # Common typos map (Typo -> Correct)
        self.common_typos = {
            'પ્રિન્ટ': 'છાપો',
            'રીટર્ન': 'પરત આપો',
            'યીલ્ડ': 'પ્રદાન કરો',
            'ડેફ્': 'ડેફ',
            'ઈમ્પોટ': 'ઈમ્પોર્ટ',
            'વાઈલ': 'વ્હાઈલ',
            'નહીંતો': 'નહીં તો',  # Missing space
            'ફોર લુપ': 'ફોર',
        }

    def check_file(self, content: str) -> List[Dict]:
        """
        Checks a file content for grammar issues.
        Returns a list of issues found.
        """
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Skip comments for keyword checking (but could check comments for grammar later)
            if line.strip().startswith('#'):
                continue
                
            # Check for typos
            for typo, correct in self.common_typos.items():
                if typo in line:
                    issues.append({
                        'line': line_num,
                        'type': 'typo',
                        'message': f"શબ્દ '{typo}' ને બદલે '{correct}' વાપરો.",
                        'severity': 'warning'
                    })
            
            # Simple keyword validation (heuristic)
            # Find words that look like they might be intended as keywords but are slightly off
            # This is hard to do perfectly without a full parser, but we can catch obvious things
            pass 

        return issues

    def check_docstring(self, docstring: str) -> List[Dict]:
        """
        Placeholder for checking grammar inside docstrings.
        """
        issues = []
        # Future: Integrate with an LLM or dictionary-based checker for Gujarati text
        return issues
