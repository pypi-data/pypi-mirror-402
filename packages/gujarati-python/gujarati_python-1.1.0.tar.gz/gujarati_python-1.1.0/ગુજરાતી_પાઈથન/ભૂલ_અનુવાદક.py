"""
ભૂલ અનુવાદક મોડ્યુલ - Python Exceptions ને ગુજરાતીમાં બતાવવા માટે

આ મોડ્યુલ Python ના સ્ટાન્ડર્ડ એરર મેસેજીસને ગુજરાતીમાં અનુવાદ કરે છે.
"""

import sys
import traceback

class ભૂલ_અનુવાદક:
    """
    Python એરર્સને ગુજરાતીમાં અનુવાદ કરવા માટેનો ક્લાસ
    """
    
    def __init__(self):
        # અંગ્રેજી Exception નામોનું ગુજરાતીમાં મેપિંગ
        self.એરર_મેપ = {
            'SyntaxError': 'વાક્યરચના ભૂલ',
            'IndentationError': 'ઈન્ડેન્ટેશન ભૂલ',
            'NameError': 'નામ ભૂલ',
            'TypeError': 'પ્રકાર ભૂલ',
            'ValueError': 'મૂલ્ય ભૂલ',
            'ZeroDivisionError': 'શૂન્ય વિભાજન ભૂલ',
            'IndexError': 'ઈન્ડેક્સ ભૂલ',
            'KeyError': 'કી ભૂલ',
            'AttributeError': 'એટ્રીબ્યુટ ભૂલ',
            'ImportError': 'ઈમ્પોર્ટ ભૂલ',
            'ModuleNotFoundError': 'મોડ્યુલ મળ્યું નથી',
            'FileNotFoundError': 'ફાઈલ મળી નથી',
            'FileExistsError': 'ફાઈલ પહેલેથી અસ્તિત્વમાં છે',
            'PermissionError': 'પરવાનગી ભૂલ',
            'KeyboardInterrupt': 'કીબોર્ડ ઇન્ટરપ્ટ',
            'RecursionError': 'પુનરાવર્તન ભૂલ',
            'MemoryError': 'મેમરી ભૂલ',
            'RuntimeError': 'રનટાઈમ ભૂલ',
            'NotImplementedError': 'અમલીકરણ બાકી ભૂલ',
            'AssertionError': 'દાવા ભૂલ (Assertion Error)',
        }
        
        # સામાન્ય એરર મેસેજીસનું મેપિંગ (Regex અથવા સીધું સ્ટ્રિંગ મેચ)
        self.મેસેજ_મેપ = {
            'division by zero': 'શૂન્ય વડે ભાગાકાર શક્ય નથી',
            'name \'{}\' is not defined': "નામ '{}' વ્યાખ્યાયિત નથી",
            'invalid syntax': 'અમાન્ય વાક્યરચના',
            'expected an indented block': 'ઈન્ડેન્ટેડ બ્લોક અપેક્ષિત છે',
            'unexpected indent': 'અણધાર્યો ઈન્ડેન્ટ',
            'list index out of range': 'લિસ્ટ ઈન્ડેક્સ range ની બહાર છે',
            'No module named \'{}\'': "'{}' નામનું કોઈ મોડ્યુલ નથી",
        }

    def ગુજરાતી_એરર_મેળવો(self, exc_type, exc_value, exc_traceback):
        """
        Exception ને ગુજરાતીમાં ફોર્મેટ કરે છે
        """
        exception_name = exc_type.__name__
        exception_msg = str(exc_value)
        
        # 1. એરરનું નામ ગુજરાતીમાં
        ગુજરાતી_નામ = self.એરર_મેપ.get(exception_name, exception_name)
        
        # 2. એરર મેસેજ ગુજરાતીમાં (જો શક્ય હોય તો)
        # સાદા રિપ્લેસમેન્ટ માટે પ્રયત્ન કરો
        ગુજરાતી_મેસેજ = exception_msg
        
        if exception_msg == 'division by zero':
             ગુજરાતી_મેસેજ = 'શૂન્ય વડે ભાગાકાર શક્ય નથી'
        
        # TODO: વધુ જટિલ મેસેજ ટ્રાન્સલેશન માટે અહીં logic ઉમેરી શકાય
        # ઉ.દા. regex વાપરીને dynamic values સાથે મેચ કરવું
        
        return f"{ગુજરાતી_નામ}: {ગુજરાતી_મેસેજ}"

def કસ્ટમ_એક્સેપ્શન_હુક(exc_type, exc_value, exc_traceback):
    """
    sys.excepthook માટે કસ્ટમ હુક
    """
    # જો કીબોર્ડ ઇન્ટરપ્ટ હોય તો ડિફોલ્ટ વર્તન રહેવા દો (શાંતિથી બહાર નીકળવા માટે)
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    અનુવાદક = ભૂલ_અનુવાદક()
    ગુજરાતી_એરર = અનુવાદક.ગુજરાતી_એરર_મેળવો(exc_type, exc_value, exc_traceback)
    
    # ટ્રેસબેક પણ બતાવવું જોઈએ, પણ અત્યારે આપણે ફક્ત છેલ્લી લાઇન બદલીએ છીએ
    # યુઝરને કન્ફ્યુઝ ન કરવા માટે ટ્રેસબેક ઓછું અથવા ગુજરાતીમાં બતાવી શકાય
    # અત્યારે આપણે સ્ટાન્ડર્ડ ટ્રેસબેક પ્રિન્ટ કરીએ છીએ અને અંતે ગુજરાતી મેસેજ
    
    # print("--- અંગ્રેજી ટ્રેસબેક ---")
    # traceback.print_tb(exc_traceback)
    # print("-" * 20)
    
    # ટ્રેસબેક માંથી ફાઈલ અને લાઈન નંબર કાઢો
    tb_list = traceback.extract_tb(exc_traceback)
    
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    
    એરર_વિગત = ""
    for frame in tb_list:
        # ફક્ત યુઝરની ફાઈલો બતાવો, લાઈબ્રેરી ફાઈલો નહીં (optional)
        filename = frame.filename
        line_no = frame.lineno
        func = frame.name
        code = frame.line
        
        એરર_વિગત += f"  ફાઈલ '{filename}', લાઈન {line_no}, '{func}' માં\n"
        if code:
             એરર_વિગત += f"    {code}\n"
    
    ફાઈનલ_મેસેજ = f"{એરર_વિગત}\n[bold red]{ગુજરાતી_એરર}[/]"
    
    console.print(Panel(ફાઈનલ_મેસેજ, title="ભૂલ (Error)", border_style="red"))

# આ ફંક્શનને મુખ્ય.py માં ઈમ્પોર્ટ કરીને સેટ કરવું
