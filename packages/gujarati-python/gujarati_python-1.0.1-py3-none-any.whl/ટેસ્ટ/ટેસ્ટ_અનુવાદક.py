#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ગુજરાતી અનુવાદક માટે ટેસ્ટ

આ ફાઈલ અનુવાદક મોડ્યુલનું ટેસ્ટિંગ કરે છે.
"""

import sys
import os
import unittest

# પ્રોજેક્ટ પાથ ઉમેરો
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ગુજરાતી_પાઈથન.અનુવાદક import કીવર્ડ_અનુવાદક, કોડ_અનુવાદ_કરો, વેલિડેશન_કરો


class ટેસ્ટ_કીવર્ડ_અનુવાદક(unittest.TestCase):
    """
    કીવર્ડ અનુવાદકના ટેસ્ટ
    """
    
    def setUp(self):
        """
        ટેસ્ટ માટે સેટઅપ
        """
        self.અનુવાદક = કીવર્ડ_અનુવાદક()
    
    def test_basic_keywords(self):
        """
        મૂળભૂત કીવર્ડ્સનું ટેસ્ટ
        """
        # ગુજરાતી કોડ
        ગુજરાતી_કોડ = """
ડેફ નમસ્કાર():
    છાપો("નમસ્તે!")
    
નમસ્કાર()
        """.strip()
        
        # અપેક્ષિત અંગ્રેજી કોડ
        અપેક્ષિત = """
def નમસ્કાર():
    print("નમસ્તે!")
    
નમસ્કાર()
        """.strip()
        
        પરિણામ = self.અનુવાદક.ગુજરાતીથી_અંગ્રેજી(ગુજરાતી_કોડ)
        self.assertEqual(પરિણામ.strip(), અપેક્ષિત.strip())
    
    def test_control_structures(self):
        """
        કન્ટ્રોલ સ્ટ્રક્ચર્સનું ટેસ્ટ
        """
        ગુજરાતી_કોડ = """
જો સાચું:
    છાપો("હા")
નહીં તો:
    છાપો("ના")
        """.strip()
        
        અપેક્ષિત = """
if True:
    print("હા")
else:
    print("ના")
        """.strip()
        
        પરિણામ = self.અનુવાદક.ગુજરાતીથી_અંગ્રેજી(ગુજરાતી_કોડ)
        self.assertEqual(પરિણામ.strip(), અપેક્ષિત.strip())
    
    def test_loops(self):
        """
        લૂપ્સનું ટેસ્ટ
        """
        ગુજરાતી_કોડ = """
ફોર i ઇન રેંજ(3):
    છાપો(i)
    
સંખ્યા = 0
વ્હાઈલ સંખ્યા < 3:
    છાપો(સંખ્યા)
    સંખ્યા += 1
        """.strip()
        
        અપેક્ષિત = """
for i in range(3):
    print(i)
    
સંખ્યા = 0
while સંખ્યા < 3:
    print(સંખ્યા)
    સંખ્યા += 1
        """.strip()
        
        પરિણામ = self.અનુવાદક.ગુજરાતીથી_અંગ્રેજી(ગુજરાતી_કોડ)
        self.assertEqual(પરિણામ.strip(), અપેક્ષિત.strip())
    
    def test_class_definition(self):
        """
        ક્લાસ ડેફિનેશનનું ટેસ્ટ
        """
        ગુજરાતી_કોડ = """
ક્લાસ ટેસ્ટ:
    ડેફ __init__(સ્વ):
        સ્વ.નામ = "ટેસ્ટ"
    
    ડેફ પરિચય(સ્વ):
        પરત આપો સ્વ.નામ
        """.strip()
        
        અપેક્ષિત = """
class ટેસ્ટ:
    def __init__(સ્વ):
        સ્વ.નામ = "ટેસ્ટ"
    
    def પરિચય(સ્વ):
        return સ્વ.નામ
        """.strip()
        
        પરિણામ = self.અનુવાદક.ગુજરાતીથી_અંગ્રેજી(ગુજરાતી_કોડ)
        self.assertEqual(પરિણામ.strip(), અપેક્ષિત.strip())
    
    def test_import_statements(self):
        """
        ઇમ્પોર્ટ સ્ટેટમેન્ટ્સનું ટેસ્ટ
        """
        ગુજરાતી_કોડ = """
ઈમ્પોર્ટ ગણિત
માંથી os ઈમ્પોર્ટ path
ઈમ્પોર્ટ numpy આસ np
        """.strip()
        
        અપેક્ષિત = """
import math
from os import path
import numpy as np
        """.strip()
        
        પરિણામ = self.અનુવાદક.ગુજરાતીથી_અંગ્રેજી(ગુજરાતી_કોડ)
        self.assertEqual(પરિણામ.strip(), અપેક્ષિત.strip())
    
    def test_exception_handling(self):
        """
        એક્સેપ્શન હેન્ડલિંગનું ટેસ્ટ
        """
        ગુજરાતી_કોડ = """
પ્રયત્ન કરો:
    પરિણામ = 10 / 0
સિવાય ZeroDivisionError:
    છાપો("એરર!")
અંતે:
    છાપો("પૂર્ણ")
        """.strip()
        
        અપેક્ષિત = """
try:
    પરિણામ = 10 / 0
except ZeroDivisionError:
    print("એરર!")
finally:
    print("પૂર્ણ")
        """.strip()
        
        પરિણામ = self.અનુવાદક.ગુજરાતીથી_અંગ્રેજી(ગુજરાતી_કોડ)
        self.assertEqual(પરિણામ.strip(), અપેક્ષિત.strip())
    
    def test_reverse_translation(self):
        """
        રિવર્સ ટ્રાન્સલેશનનું ટેસ્ટ
        """
        અંગ્રેજી_કોડ = """
def test():
    print("Hello")
    return True
        """.strip()
        
        અપેક્ષિત = """
ડેફ test():
    છાપો("Hello")
    પરત આપો સાચું
        """.strip()
        
        પરિણામ = self.અનુવાદક.અંગ્રેજીથી_ગુજરાતી(અંગ્રેજી_કોડ)
        self.assertEqual(પરિણામ.strip(), અપેક્ષિત.strip())
    
    def test_validation(self):
        """
        વેલિડેશનનું ટેસ્ટ
        """
        # સાચો કોડ
        સાચો_કોડ = "ડેફ ટેસ્ટ(): છાપો('હેલો')"
        errors = વેલિડેશન_કરો(સાચો_કોડ)
        self.assertEqual(len(errors), 0)


class ટેસ્ટ_ગ્લોબલ_ફંક્શન્સ(unittest.TestCase):
    """
    ગ્લોબલ ફંક્શન્સના ટેસ્ટ
    """
    
    def test_કોડ_અનુવાદ_કરો(self):
        """
        કોડ અનુવાદ ફંક્શનનું ટેસ્ટ
        """
        ગુજરાતી_કોડ = "છાપો('નમસ્તે')"
        અપેક્ષિત = "print('નમસ્તે')"
        
        પરિણામ = કોડ_અનુવાદ_કરો(ગુજરાતી_કોડ)
        self.assertEqual(પરિણામ.strip(), અપેક્ષિત.strip())


if __name__ == '__main__':
    # ગુજરાતી આઉટપુટ માટે UTF-8 એન્કોડિંગ
    import io
    import locale
    
    # સિસ્ટમ એન્કોડિંગ સેટ કરો
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    
    print("ગુજરાતી અનુવાદક ટેસ્ટ શરૂ કરી રહ્યા છીએ...")
    print("=" * 50)
    
    # ટેસ્ટ ચલાવો
    unittest.main(verbosity=2, buffer=True)