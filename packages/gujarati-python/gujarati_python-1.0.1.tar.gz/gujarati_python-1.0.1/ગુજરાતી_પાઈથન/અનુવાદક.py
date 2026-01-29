"""
અનુવાદક મોડ્યુલ - પાઈથન કીવર્ડ્સને ગુજરાતીમાં અનુવાદ કરવા માટે

આ મોડ્યુલ ગુજરાતી કીવર્ડ્સને અંગ્રેજી કીવર્ડ્સમાં કન્વર્ટ કરે છે
જેથી સ્ટાન્ડર્ડ પાઈથન ઇન્ટરપ્રિટર ચલાવી શકાય.
"""

import re
from typing import List

class કીવર્ડ_અનુવાદક:
    """
    ગુજરાતી કીવર્ડ્સને અંગ્રેજીમાં અનુવાદ કરવા માટેનો ક્લાસ
    """
    
    def __init__(self):
        # ગુજરાતી કીવર્ડ્સથી અંગ્રેજી કીવર્ડ્સનું મેપિંગ
        self.કીવર્ડ_મેપ = {
            # મૂળભૂત કીવર્ડ્સ
            'ઈમ્પોર્ટ': 'import',
            'ડેફ': 'def',
            'ક્લાસ': 'class',
            'ફોર': 'for',
            'વ્હાઈલ': 'while',
            'જો': 'if',
            'નહીં તો': 'else',
            'અથવા જો': 'elif',
            'પરત આપો': 'return',
            'છાપો': 'print',
            'સાચું': 'True',
            'ખોટું': 'False',
            'કંઈ નહીં': 'None',
            'અને': 'and',
            'અથવા': 'or',
            'નહીં': 'not',
            'ઇન': 'in',
            'છે': 'is',
            'સાથે': 'with',
            'આસ': 'as',
            'માંથી': 'from',
            'પ્રયત્ન કરો': 'try',
            'સિવાય': 'except',
            'અંતે': 'finally',
            'ઊઠાવો': 'raise',
            'લેમ્બડા': 'lambda',
            'વૈશ્વિક': 'global',
            'બિન સ્થાનિક': 'nonlocal',
            'ખાતરી કરો': 'assert',
            'બ્રેક': 'break',
            'ચાલુ રાખો': 'continue',
            'પાસ': 'pass',
            'ડિલીટ કરો': 'del',
            'પ્રદાન કરો': 'yield',
            'અસિન્ક': 'async',
            'અસિન્ક': 'async',
            'રાહ જુઓ': 'await',
            'મેચ': 'match',
            'કેસ': 'case',
            
            # બિલ્ટ-ઇન ફંક્શન્સ
            'લેન': 'len',
            'રેંજ': 'range',
            'ટાઇપ': 'type',
            'સ્ટ્ર': 'str',
            'ઇન્ટ': 'int',
            'ફ્લોટ': 'float',
            'લિસ્ટ': 'list',
            'ડિક્ટ': 'dict',
            'સેટ': 'set',
            'ટ્યુપલ': 'tuple',
            'ઓપન': 'open',
            'મિન': 'min',
            'મેક્સ': 'max',
            'સમ': 'sum',
            'સોર્ટેડ': 'sorted',
            'રેવર્સેડ': 'reversed',
            'એની': 'any',
            'ઓલ': 'all',
            'મેપ': 'map',
            'ફિલ્ટર': 'filter',
            'ઝીપ': 'zip',
            'એન્યુમરેટ': 'enumerate',
            'ઈનપુટ': 'input',
            'ઈવલ': 'eval',
            'એક્ઝેક': 'exec',
            'કોમ્પાઇલ': 'compile',
            'હેશ': 'hash',
            'આઈડી': 'id',
            'વાર્સ': 'vars',
            'ડાઇર': 'dir',
            'હેલ્પ': 'help',
            'રાઉન્ડ': 'round',
            'એબ્સ': 'abs',
            'પાવર': 'pow',
            'ડિવમોડ': 'divmod',
            'બિન': 'bin',
            'ઓક્ટ': 'oct',
            'હેક્સ': 'hex',
            'ઓર્ડ': 'ord',
            'ક્રોમ': 'chr',
            'બૂલ': 'bool',
            'બાઇટ્સ': 'bytes',
            'બાઇટઆરે': 'bytearray',
            'કોમ્પ્લેક્સ': 'complex',
            'ફ્રોઝનસેટ': 'frozenset',
            'મેમરીવ્યુ': 'memoryview',
            'ઓબ્જેક્ટ': 'object',
            'પ્રોપર્ટી': 'property',
            'સ્લાઇસ': 'slice',
            'સુપર': 'super',
            'સ્ટેટિકમેથડ': 'staticmethod',
            'ક્લાસમેથડ': 'classmethod',
            
            # સામાન્ય મોડ્યુલ નામો - ફક્ત imports માં
            # આને અલગ category માં મૂકવા જોઈએ
        }
        
        # સામાન્ય મોડ્યુલ નામો - આ ફક્ત import statements માં જ translate થવા જોઈએ
        self.મોડ્યુલ_નામ_મેપ = {
            'ગણિત': 'math',
            'રેન્ડમ': 'random',
            'અવિકલ': 'time',
            'datetime': 'datetime',
            'json': 'json',
            'os': 'os',
            'sys': 'sys',
            'કલેક્શન્સ': 'collections',
            'ઇટરટૂલ્સ': 'itertools',
            'ફંકટૂલ્સ': 'functools',
            'રી': 're',
        }
        
        # રિવર્સ મેપિંગ (અંગ્રેજીથી ગુજરાતી)
        આલ_મેપ = {**self.કીવર્ડ_મેપ, **self.મોડ્યુલ_નામ_મેપ}
        self.રિવર્સ_મેપ = {v: k for k, v in આલ_મેપ.items()}
        
        # ઓપરેટર્સનું મેપિંગ
        self.ઓપરેટર_મેપ = {
            '==': '==',
            '!=': '!=',
            '<=': '<=',
            '>=': '>=',
            '<': '<',
            '>': '>',
            '+': '+',
            '-': '-',
            '*': '*',
            '/': '/',
            '//': '//',
            '%': '%',
            '**': '**',
        }
    
    def ગુજરાતીથી_અંગ્રેજી(self, કોડ: str) -> str:
        """
        ગુજરાતી કોડને અંગ્રેજી પાઈથન કોડમાં કન્વર્ટ કરે છે
        
        પેરામીટર:
            કોડ (str): ગુજરાતી પાઈથન કોડ
            
        પરત આપે:
            str: અંગ્રેજી પાઈથન કોડ
        """
        import re  
        
        અનુવાદિત_કોડ = કોડ
        
        # પહેલા import statements અને module usages ને handle કરો
        # 1. Import statements
        for લાઇન in અનુવાદિત_કોડ.split('\n'):
            if લાઇન.strip().startswith('import ') or 'ઈમ્પોર્ટ' in લાઇન:
                # import statement માં module names ટ્રાન્સલેટ કરો
                for ગુજ_મોડ, ઇંગ_મોડ in self.મોડ્યુલ_નામ_મેપ.items():
                    if ગુજ_મોડ in લાઇન:
                        નવી_લાઇન = લાઇન.replace(ગુજ_મોડ, ઇંગ_મોડ)
                        અનુવાદિત_કોડ = અનુવાદિત_કોડ.replace(લાઇન, નવી_લાઇન)
        
        # 2. Module usage (ગણિત.sqrt) ને translate કરો
        for ગુજ_મોડ, ઇંગ_મોડ in self.મોડ્યુલ_નામ_મેપ.items():
            પેટર્ન = r'\b' + re.escape(ગુજ_મોડ) + r'\.'
            અનુવાદિત_કોડ = re.sub(પેટર્ન, ઇંગ_મોડ + '.', અનુવાદિત_કોડ)
        
        # હવે સ્ટ્રિંગ લિટરલ્સને પ્રોટેક્ટ કરો (પરંતુ f-strings માં keywords translate કરવા દો)
        સ્ટ્રિંગ_પ્લેસહોલ્ડર્સ = {}
        પ્લેસહોલ્ડર_કાઉન્ટર = 0
        
        # Protect string literals (both regular strings and f-strings)
        સ્ટ્રિંગ_પેટર્ન્સ = [
            (r'"""([^"]|"[^"]|""[^"])*"""', 'triple_double'),      # Triple double quotes
            (r"'''([^']|'[^']|''[^'])*'''", 'triple_single'),      # Triple single quotes  
            (r'(?<!f)"([^"\n\\]*(\\.[^"\n\\]*)*)"', 'double'),    # Double quotes not preceded by f, no newlines
            (r"(?<!f)'([^'\n\\]*(\\.[^'\n\\]*)*)'", 'single'),    # Single quotes not preceded by f, no newlines
            (r'f"([^"\n\\]*(\\.[^"\n\\]*)*)"', 'f_double'),       # f-strings with double quotes  
            (r"f'([^'\n\\]*(\\.[^'\n\\]*)*)'", 'f_single'),       # f-strings with single quotes
        ]
        
        # પ્રોટેક્ટ string literals (પરંતુ f-strings નહીં)
        for પેટર્ન, quote_type in સ્ટ્રિંગ_પેટર્ન્સ:
            matches = list(re.finditer(પેટર્ન, અનુવાદિત_કોડ, re.DOTALL))
            # Reverse order માટે position corruption ટાળવું
            for match in reversed(matches):
                સ્ટ્રિંગ_કન્ટેન્ટ = match.group(0)
                પ્લેસહોલ્ડર = f"__STR_{quote_type}_{પ્લેસહોલ્ડર_કાઉન્ટર}__"
                સ્ટ્રિંગ_પ્લેસહોલ્ડર્સ[પ્લેસહોલ્ડર] = સ્ટ્રિંગ_કન્ટેન્ટ
                અનુવાદિત_કોડ = અનુવાદિત_કોડ[:match.start()] + પ્લેસહોલ્ડર + અનુવાદિત_કોડ[match.end():]
                પ્લેસહોલ્ડર_કાઉન્ટર += 1
        
        # હવે કીવર્ડ્સનો અનુવાદ કરો (લાંબાથી નાના ક્રમમાં) - SIMPLE APPROACH
        કીવર્ડ_લિસ્ટ = sorted(self.કીવર્ડ_મેપ.keys(), key=len, reverse=True)
        
        for ગુજરાતી_કીવર્ડ in કીવર્ડ_લિસ્ટ:
            અંગ્રેજી_કીવર્ડ = self.કીવર્ડ_મેપ[ગુજરાતી_કીવર્ડ]
            
            # Use very simple and reliable word boundary replacement
            # This works line by line to preserve indentation and structure
            lines = અનુવાદિત_કોડ.split('\n')
            new_lines = []
            
            for line in lines:
                if ગુજરાતી_કીવર્ડ in line:
                    # Simple word boundary replacement that preserves spacing and indentation
                    # Allow keywords to be preceded by whitespace, start of line, or operators
                    # Allow keywords to be followed by punctuation, whitespace, or end of line
                    પેટર્ન = r'(?<![a-zA-Z0-9_])' + re.escape(ગુજરાતી_કીવર્ડ) + r'(?=\s|[(){}[\]:,]|$)'
                    line = re.sub(પેટર્ન, અંગ્રેજી_કીવર્ડ, line)
                new_lines.append(line)
            
            અનુવાદિત_કોડ = '\n'.join(new_lines)
        
        # સ્ટ્રિંગ પ્લેસહોલ્ડર્સને વાપસ લાવો, પરંતુ f-strings ને અલગથી process કરો
        # First, make placeholders available to f-string processing
        self._current_string_placeholders = સ્ટ્રિંગ_પ્લેસહોલ્ડર્સ
        
        for પ્લેસહોલ્ડર, મૂળ_સ્ટ્રિંગ in સ્ટ્રિંગ_પ્લેસહોલ્ડર્સ.items():
            if 'f_double' in પ્લેસહોલ્ડર or 'f_single' in પ્લેસહોલ્ડર:
                # Process f-string separately
                processed_f_string = self._process_f_string(મૂળ_સ્ટ્રિંગ, કીવર્ડ_લિસ્ટ)
                અનુવાદિત_કોડ = અનુવાદિત_કોડ.replace(પ્લેસહોલ્ડર, processed_f_string)
            else:
                # Regular string - restore as-is  
                અનુવાદિત_કોડ = અનુવાદિત_કોડ.replace(પ્લેસહોલ્ડર, મૂળ_સ્ટ્રિંગ)
        
        # Clean up the temporary attribute
        if hasattr(self, '_current_string_placeholders'):
            delattr(self, '_current_string_placeholders')

        return અનુવાદિત_કોડ
    
    def _process_f_string(self, f_string_content: str, કીવર્ડ_લિસ્ટ: list) -> str:
        """
        Process f-string by translating keywords only in expressions (inside {})
        
        પેરામીટર:
            f_string_content (str): Complete f-string like f"hello {name}"
            કીવર્ડ_લિસ્ટ (list): List of Gujarati keywords to translate
            
        પરત આપે:
            str: Processed f-string with keywords translated in expressions only
        """
        import re
        
        # Extract the quote type and content
        if f_string_content.startswith('f"'):
            quote_char = '"'
            content = f_string_content[2:-1]  # Remove f" and "
        elif f_string_content.startswith("f'"):
            quote_char = "'"
            content = f_string_content[2:-1]  # Remove f' and '
        else:
            # Fallback - return as is
            return f_string_content
        
        # First restore any string placeholders that might be inside the f-string
        # This handles cases like f"  - {વ્યક્તિ[__STR_single_67__]}"
        if hasattr(self, '_current_string_placeholders'):
            for પ્લેસહોલ્ડર, મૂળ_સ્ટ્રિંગ in self._current_string_placeholders.items():
                content = content.replace(પ્લેસહોલ્ડર, મૂળ_સ્ટ્રિંગ)
            
        # F-string expressions ({...}) શોધો
        expr_pattern = r'\{([^}]+)\}'
        expressions = re.findall(expr_pattern, content)
        
        # દરેક expression માં keywords translate કરો
        processed_content = content
        for expr in expressions:
            # Expression માં keywords translate કરો
            translated_expr = expr
            
            for ગુજરાતી_કીવર્ડ in કીવર્ડ_લિસ્ટ:
                if ગુજરાતી_કીવર્ડ in translated_expr:
                    અંગ્રેજી_કીવર્ડ = self.કીવર્ડ_મેપ[ગુજરાતી_કીવર્ડ]
                    પેટર્ન = r'(?<![a-zA-Z0-9_])' + re.escape(ગુજરાતી_કીવર્ડ) + r'(?=\s|[(){}[\]:,]|$)'
                    translated_expr = re.sub(પેટર્ન, અંગ્રેજી_કીવર્ડ, translated_expr)
            
            # Original expression ને translated સાથે replace કરો
            processed_content = processed_content.replace('{' + expr + '}', '{' + translated_expr + '}')
        
        # Rebuild the f-string
        return f'f{quote_char}{processed_content}{quote_char}'
    
    def અંગ્રેજીથી_ગુજરાતી(self, કોડ: str) -> str:
        """
        અંગ્રેજી પાઈથન કોડને ગુજરાતી કોડમાં કન્વર્ટ કરે છે
        
        પેરામીટર:
            કોડ (str): અંગ્રેજી પાઈથન કોડ
            
        પરત આપે:
            str: ગુજરાતી પાઈથન કોડ
        """
        અનુવાદિત_કોડ = કોડ
        
        # અંગ્રેજી કીવર્ડ્સનો અનુવાદ કરો
        for અંગ્રેજી_કીવર્ડ, ગુજરાતી_કીવર્ડ in self.રિવર્સ_મેપ.items():
            પેટર્ન = r'\b' + re.escape(અંગ્રેજી_કીવર્ડ) + r'\b'
            અનુવાદિત_કોડ = re.sub(પેટર્ન, ગુજરાતી_કીવર્ડ, અનુવાદિત_કોડ)
        
        return અનુવાદિત_કોડ
    
    def કીવર્ડ_વેલિડેશન(self, કોડ: str) -> List[str]:
        """
        ગુજરાતી કોડમાં અજાણ્યા કીવર્ડ્સ શોધે છે
        
        પેરામીટર:
            કોડ (str): ગુજરાતી કોડ
            
        પરત આપે:
            List[str]: અજાણ્યા કીવર્ડ્સની યાદી
        """
        # વેલિડેશન બંધ કરો - વેરિએબલ નામો અને કમેન્ટ્સની સાથે બહુ મુશ્કેલી આવે છે
        # ફક્ત syntax errors માટે Python નો પોતાનો પેર્સર વાપરીશું
        return []


# ગ્લોબલ અનુવાદક ઇન્સ્ટન્સ
_અનુવાદક = કીવર્ડ_અનુવાદક()


def કોડ_અનુવાદ_કરો(ગુજરાતી_કોડ: str) -> str:
    """
    ગુજરાતી કોડને અંગ્રેજી પાઈથન કોડમાં અનુવાદ કરે છે
    
    પેરામીટર:
        ગુજરાતી_કોડ (str): ગુજરાતી પાઈથન કોડ
        
    પરત આપે:
        str: અંગ્રેજી પાઈથન કોડ
    """
    return _અનુવાદક.ગુજરાતીથી_અંગ્રેજી(ગુજરાતી_કોડ)


def વેલિડેશન_કરો(ગુજરાતી_કોડ: str) -> List[str]:
    """
    ગુજરાતી કોડમાં એરર્સ શોધે છે
    
    પેરામીટર:
        ગુજરાતી_કોડ (str): ગુજરાતી પાઈથન કોડ
        
    પરત આપે:
        List[str]: એરર મેસેજોની યાદી
    """
    return _અનુવાદક.કીવર્ડ_વેલિડેશન(ગુજરાતી_કોડ)