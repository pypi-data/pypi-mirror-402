#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ઉદાહરણ ટેસ્ટ - ગુજરાતી પાઈથન

આ ફાઈલ બધા ઉદાહરણોનું ટેસ્ટિંગ કરે છે અને તેમની કાર્યક્ષમતા ચકાસે છે.
"""

import os
import sys
import unittest
import tempfile
import subprocess
from pathlib import Path

# પ્રોજેક્ટ પાથ ઉમેરો
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ગુજરાતી_પાઈથન import કોડ_અનુવાદ_કરો, ગુજરાતી_કોડ_ચલાવો


class ઉદાહરણ_ટેસ્ટ(unittest.TestCase):
    """બધા ઉદાહરણ ફાઈલોના ટેસ્ટ"""

    def setUp(self):
        """ટેસ્ટ માટે સેટઅપ"""
        self.પ્રોજેક્ટ_પાથ = Path(__file__).parent.parent
        self.ઉદાહરણ_પાથ = self.પ્રોજેક્ટ_પાથ / "ઉદાહરણો"
        self.મુખ્ય_ફાઈલ = self.પ્રોજેક્ટ_પાથ / "મુખ્ય.py"
        
        # ખાતરી કરો કે ફાઈલો અસ્તિત્વમાં છે
        self.assertTrue(self.ઉદાહરણ_પાથ.exists(), f"ઉદાહરણ ડિરેક્ટરી મળી નથી: {self.ઉદાહરણ_પાથ}")
        self.assertTrue(self.મુખ્ય_ફાઈલ.exists(), f"મુખ્ય ફાઈલ મળી નથી: {self.મુખ્ય_ફાઈલ}")

    def _ફાઈલ_ચલાવો(self, ઉદાહરણ_નામ):
        """
        ઉદાહરણ ફાઈલ ચલાવે છે અને તેનું પરિણામ પરત કરે છે
        
        પેરામીટર:
            ઉદાહરણ_નામ (str): ઉદાહરણ ફાઈલનું નામ
            
        પરત:
            dict: {'returncode': int, 'stdout': str, 'stderr': str}
        """
        ફાઈલ_પાથ = self.ઉદાહરણ_પાથ / ઉદાહરણ_નામ
        self.assertTrue(ફાઈલ_પાથ.exists(), f"ઉદાહરણ ફાઈલ મળી નથી: {ફાઈલ_પાથ}")
        
        # Windows encoding issues માટે environment વેરિએબલ સેટ કરો
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'  # Python 3.7+ માટે UTF-8 mode
        
        # Python subprocess ઉપયોગ કરીને ફાઈલ ચલાવો
        પરિણામ = subprocess.run(
            [sys.executable, str(self.મુખ્ય_ફાઈલ), str(ફાઈલ_પાથ)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Unicode encode/decode errors ને handle કરો
            cwd=str(self.પ્રોજેક્ટ_પાથ),
            env=env
        )
        
        return {
            'returncode': પરિણામ.returncode,
            'stdout': પરિણામ.stdout,
            'stderr': પરિણામ.stderr
        }

    def test_સરળ_ડેમો(self):
        """સરળ ડેમો ફાઈલનું ટેસ્ટ"""
        પરિણામ = self._ફાઈલ_ચલાવો("સરળ_ડેમો.py")
        
        self.assertEqual(પરિણામ['returncode'], 0, 
                        f"સરળ ડેમો fail થયો. Error: {પરિણામ['stderr']}")
        
        આઉટપુટ = પરિણામ['stdout']
        
        # મુખ્ય આઉટપુટ ચકાસો
        self.assertIn("નમસ્તે! આ ગુજરાતી પાઈથન છે!", આઉટપુટ)
        self.assertIn("મારું નામ રામ છે", આઉટપુટ)
        self.assertIn("10 + 20 = 30", આઉટપુટ)
        self.assertIn("તમે પુખ્ત છો", આઉટપુટ)
        self.assertIn("ગુજરાતી પાઈથન ડેમો પૂર્ણ!", આઉટપુટ)

    def test_મૂળભૂત_ઉદાહરણ(self):
        """મૂળભૂત ઉદાહરણ ફાઈલનું ટેસ્ટ"""
        પરિણામ = self._ફાઈલ_ચલાવો("મૂળભૂત_ઉદાહરણ.py")
        
        self.assertEqual(પરિણામ['returncode'], 0, 
                        f"મૂળભૂત ઉદાહરણ fail થયો. Error: {પરિણામ['stderr']}")
        
        આઉટપુટ = પરિણામ['stdout']
        
        # મુખ્ય આઉટપુટ ચકાસો
        self.assertIn("સ્વાગત છે ગુજરાતી પાઈથન", આઉટપુટ)
        self.assertIn("ગણિતના ઓપરેશન", આઉટપુટ)
        self.assertIn("શરત પરીક્ષણ", આઉટપુટ)
        self.assertIn("લૂપ્સ", આઉટપુટ)
        self.assertIn("ડેટા સ્ટ્રક્ચર", આઉટપુટ)
        self.assertIn("એરર હેન્ડલિંગ", આઉટપુટ)
        self.assertIn("ગુજરાતી પાઈથનનો ડેમો પૂર્ણ!", આઉટપુટ)

    def test_ક્લાસ_ઉદાહરણ(self):
        """ક્લાસ ઉદાહરણ ફાઈલનું ટેસ્ટ"""
        પરિણામ = self._ફાઈલ_ચલાવો("ક્લાસ_ઉદાહરણ.py")
        
        self.assertEqual(પરિણામ['returncode'], 0, 
                        f"ક્લાસ ઉદાહરણ fail થયો. Error: {પરિણામ['stderr']}")
        
        આઉટપુટ = પરિણામ['stdout']
        
        # મુખ્ય આઉટપુટ ચકાસો
        self.assertIn("ગુજરાતી પાઈથન - ક્લાસ ડેમો", આઉટપુટ)
        self.assertIn("કુલ વ્યક્તિઓ", આઉટપુટ)
        self.assertIn("હું રાજેશ છું", આઉટપુટ)
        self.assertIn("હું પ્રિયા છું", આઉટપુટ)
        self.assertIn("હવે મિત્રો છે", આઉટપુટ)
        self.assertIn("રીપોર્ટ કાર્ડ", આઉટપુટ)
        self.assertIn("ક્લાસ ડેમો પૂર્ણ!", આઉટપુટ)

    def test_બધા_ઉદાહરણો_યાદી(self):
        """ખાતરી કરો કે બધા અપેક્ષિત ઉદાહરણ ફાઈલો અસ્તિત્વમાં છે"""
        અપેક્ષિત_ફાઈલો = [
            "સરળ_ડેમો.py",
            "મૂળભૂત_ઉદાહરણ.py", 
            "ક્લાસ_ઉદાહરણ.py",
            "અડવાન્સ_ઉદાહરણ.py",
            "સંપૂર્ણ_ઉદાહરણ.py"
        ]
        
        for ફાઈલ_નામ in અપેક્ષિત_ફાઈલો:
            ફાઈલ_પાથ = self.ઉદાહરણ_પાથ / ફાઈલ_નામ
            self.assertTrue(ફાઈલ_પાથ.exists(), 
                           f"ઉદાહરણ ફાઈલ મળી નથી: {ફાઈલ_નામ}")

    def test_ઉદાહરણ_ફાઈલ_વાચન(self):
        """ખાતરી કરો કે ઉદાહરણ ફાઈલો UTF-8 માં વાંચી શકાય છે"""
        કામ_કરતા_ઉદાહરણો = [
            "સરળ_ડેમો.py",
            "મૂળભૂત_ઉદાહરણ.py", 
            "ક્લાસ_ઉદાહરણ.py"
        ]
        
        for ફાઈલ_નામ in કામ_કરતા_ઉદાહરણો:
            with self.subTest(ફાઈલ=ફાઈલ_નામ):
                ફાઈલ_પાથ = self.ઉદાહરણ_પાથ / ફાઈલ_નામ
                
                # ફાઈલ વાંચો
                સામગ્રી = ફાઈલ_પાથ.read_text(encoding='utf-8')
                self.assertIsNotNone(સામગ્રી, f"ફાઈલ સામગ્રી null છે: {ફાઈલ_નામ}")
                self.assertGreater(len(સામગ્રી), 0, f"ફાઈલ ખાલી છે: {ફાઈલ_નામ}")
                
                # ગુજરાતી યુનિકોડ અક્ષરો છે કે નહીં
                self.assertTrue(any(ord(char) > 127 for char in સામગ્રી), 
                               f"ગુજરાતી અક્ષરો મળ્યા નથી: {ફાઈલ_નામ}")

    def test_અનુવાદ_ક્ષમતા(self):
        """ખાતરી કરો કે કામ કરતા ઉદાહરણો સફળતાપૂર્વક અનુવાદ થાય છે"""
        કામ_કરતા_ઉદાહરણો = [
            "સરળ_ડેમો.py",
            "મૂળભૂત_ઉદાહરણ.py", 
            "ક્લાસ_ઉદાહરણ.py"
        ]
        
        for ફાઈલ_નામ in કામ_કરતા_ઉદાહરણો:
            with self.subTest(ફાઈલ=ફાઈલ_નામ):
                ફાઈલ_પાથ = self.ઉદાહરણ_પાથ / ફાઈલ_નામ
                
                # ફાઈલ વાંચો
                ગુજરાતી_કોડ = ફાઈલ_પાથ.read_text(encoding='utf-8')
                
                # અનુવાદ કરો
                અંગ્રેજી_કોડ = કોડ_અનુવાદ_કરો(ગુજરાતી_કોડ)
                
                # ખાતરી કરો કે અનુવાદ થયો છે
                self.assertIsNotNone(અંગ્રેજી_કોડ, f"અનુવાદ નહીં થયો: {ફાઈલ_નામ}")
                self.assertGreater(len(અંગ્રેજી_કોડ), 0, f"અનુવાદ ખાલી છે: {ફાઈલ_નામ}")
                
                # મૂળભૂત કીવર્ડ અનુવાદ ચકાસો
                if "છાપો(" in ગુજરાતી_કોડ:
                    self.assertIn("print(", અંગ્રેજી_કોડ, f"છાપોનો અનુવાદ નહીં થયો: {ફાઈલ_નામ}")


class પ્રદર્શન_ટેસ્ટ(unittest.TestCase):
    """ઉદાહરણો માટે પ્રદર્શન ટેસ્ટ"""

    def setUp(self):
        """ટેસ્ટ માટે સેટઅપ"""
        self.પ્રોજેક્ટ_પાથ = Path(__file__).parent.parent
        self.ઉદાહરણ_પાથ = self.પ્રોજેક્ટ_પાથ / "ઉદાહરણો"
        self.મુખ્ય_ફાઈલ = self.પ્રોજેક્ટ_પાથ / "મુખ્ય.py"

    def test_ઉદાહરણ_એક્ઝિક્યુશન_સમય(self):
        """ખાતરી કરો કે ઉદાહરણો વ્યાજબી સમયમાં ચાલે છે"""
        import time
        
        કામ_કરતા_ઉદાહરણો = [
            ("સરળ_ડેમો.py", 5.0),  # મહત્તમ 5 સેકન્ડ
            ("મૂળભૂત_ઉદાહરણ.py", 10.0),  # મહત્તમ 10 સેકન્ડ
            ("ક્લાસ_ઉદાહરણ.py", 15.0)  # મહત્તમ 15 સેકન્ડ
        ]
        
        for ફાઈલ_નામ, મહત્તમ_સમય in કામ_કરતા_ઉદાહરણો:
            with self.subTest(ફાઈલ=ફાઈલ_નામ):
                ફાઈલ_પાથ = self.ઉદાહરણ_પાથ / ફાઈલ_નામ
                
                શરુઆત_સમય = time.time()
                
                # Windows encoding issues માટે environment વેરિએબલ સેટ કરો
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUTF8'] = '1'  # Python 3.7+ માટે UTF-8 mode
                
                પરિણામ = subprocess.run(
                    [sys.executable, str(self.મુખ્ય_ફાઈલ), str(ફાઈલ_પાથ)],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',  # Unicode encode/decode errors ને handle કરો
                    cwd=str(self.પ્રોજેક્ટ_પાથ),
                    env=env,
                    timeout=મહત્તમ_સમય  # Timeout protection
                )
                
                અંત_સમય = time.time()
                કુલ_સમય = અંત_સમય - શરુઆત_સમય
                
                self.assertEqual(પરિણામ.returncode, 0, 
                               f"{ફાઈલ_નામ} execute નહીં થયો")
                self.assertLess(કુલ_સમય, મહત્તમ_સમય, 
                               f"{ફાઈલ_નામ} વધુ પડતો સમય લીધો: {કુલ_સમય:.2f}s")


if __name__ == "__main__":
    print("=" * 60)
    print("ગુજરાતી પાઈથન - ઉદાહરણ ટેસ્ટ")  
    print("=" * 60)
    print()
    
    # UTF-8 આઉટપુટ માટે encoding set કરો
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    
    unittest.main(verbosity=2, buffer=True)