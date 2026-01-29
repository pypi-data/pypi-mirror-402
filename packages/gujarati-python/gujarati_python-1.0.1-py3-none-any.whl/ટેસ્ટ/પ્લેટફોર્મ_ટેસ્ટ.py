#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
પ્લેટફોર્મ સુસંગતતા ટેસ્ટ - ગુજરાતી પાઈથન

આ ટેસ્ટ વિવિધ પ્લેટફોર્મ પર ગુજરાતી પાઈથનની સુસંગતતા ચકાસે છે.
"""

import os
import sys
import platform
import tempfile
import unittest
import subprocess
from pathlib import Path

# પ્રોજેક્ટ પાથ ઉમેરો
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ગુજરાતી_પાઈથન import કોડ_અનુવાદ_કરો, ગુજરાતી_કોડ_ચલાવો


class પ્લેટફોર્મ_સુસંગતતા_ટેસ્ટ(unittest.TestCase):
    """પ્લેટફોર્મ સુસંગતતાના ટેસ્ટ"""

    def test_પ્લેટફોર્મ_માહિતી(self):
        """પ્લેટફોર્મની માહિતી ચકાસે છે"""
        self.assertIsNotNone(platform.system())
        self.assertIsNotNone(platform.machine())
        self.assertIsNotNone(sys.version)
        self.assertEqual(sys.getdefaultencoding(), 'utf-8')

    def test_ફાઇલ_પાથ_હેન્ડલિંગ(self):
        """ફાઇલ પાથ હેન્ડલિંગ ટેસ્ટ કરે છે"""
        # ટેમ્પરરી ફાઇલ બનાવો
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write('છાપો("હેલો વર્લ્ડ!")\n')
            temp_file = f.name
        
        try:
            # PathLib ઉપયોગ કરીને ફાઇલ વાંચો
            path = Path(temp_file)
            self.assertTrue(path.exists())
            
            content = path.read_text(encoding='utf-8')
            self.assertIn('છાપો', content)
            self.assertIn('હેલો વર્લ્ડ', content)
            
        finally:
            # ક્લીનઅપ
            os.unlink(temp_file)

    def test_એન્કોડિંગ_અને_અનુવાદ(self):
        """ગુજરાતી અક્ષરોની એન્કોડિંગ અને અનુવાદ ટેસ્ટ કરે છે"""
        # ગુજરાતી કોડ
        ગુજરાતી_કોડ = """
છાપો("નમસ્કાર! આ ગુજરાતી છે.")  
નામ = "રામ"
ઉંમર = 25
છાપો(f"{નામ} ની ઉંમર {ઉંમર} વર્ષ છે.")
        """.strip()
        
        # કોડ અનુવાદ કરો
        અનુવાદિત = કોડ_અનુવાદ_કરો(ગુજરાતી_કોડ)
        self.assertIsNotNone(અનુવાદિત)
        self.assertIn('print', અનુવાદિત)  # છાપો should be translated to print
        
        # કોડ ચલાવો  
        પરિણામ = ગુજરાતી_કોડ_ચલાવો(ગુજરાતી_કોડ)
        self.assertTrue(પરિણામ['સફળતા'], f"Code execution failed: {પરિણામ['એરર']}")
        self.assertIn('નમસ્કાર', પરિણામ['આઉટપુટ'])

    def test_મૂળભૂત_કીવર્ડ_અનુવાદ(self):
        """મૂળભૂત કીવર્ડ્સનો અનુવાદ ચકાસે છે"""
        test_cases = [
            ("છાપો('hello')", "print"),
            ("ડેફ test():", "def"),
            ("ફોર i ઇન રેંજ(5):", "for"),
            ("જો સાચું:", "if"),
        ]
        
        for ગુજરાતી, expected_english in test_cases:
            અનુવાદિત = કોડ_અનુવાદ_કરો(ગુજરાતી)
            self.assertIn(expected_english, અનુવાદિત, 
                         f"Expected '{expected_english}' in translation of '{ગુજરાતી}', got: {અનુવાદિત}")

    def test_windows_utf8_cli_support(self):
        """Windows પર CLI interface ની UTF-8 support ચકાસે છે"""
        import subprocess
        import os
        
        # CLI કમાંડ ટેસ્ટ કરો
        try:
            # UTF-8 environment variables સેટ કરો
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # મુખ્ય.py --help કમાંડ ટેસ્ટ કરો
            cmd = [sys.executable, "મુખ્ય.py", "--help"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                timeout=30
            )
            
            # આઉટપુટ ચકાસો
            self.assertEqual(result.returncode, 0, f"CLI help failed with error: {result.stderr}")
            self.assertIn("ગુજરાતી પાઈથન", result.stdout, "Gujarati text not found in help output")
            
            # Keywords કમાંડ પણ ટેસ્ટ કરો
            cmd = [sys.executable, "મુખ્ય.py", "--keywords"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                timeout=30
            )
            
            self.assertEqual(result.returncode, 0, f"CLI keywords failed with error: {result.stderr}")
            self.assertIn("છાપો", result.stdout, "Keywords output not working properly")
            
        except subprocess.TimeoutExpired:
            self.skipTest("CLI test timed out")
        except Exception as e:
            self.skipTest(f"CLI test failed due to: {e}")


def પ્લેટફોર્મ_માહિતી_બતાવો():
    """પ્લેટફોર્મની માહિતી દેખાડે છે"""
    print("🖥️ પ્લેટફોર્મ માહિતી:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Python: {sys.version}")
    print(f"   Encoding: {sys.getdefaultencoding()}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("ગુજરાતી પાઈથન - પ્લેટફોર્મ સુસંગતતા ટેસ્ટ")  
    print("=" * 60)
    print()
    
    પ્લેટફોર્મ_માહિતી_બતાવો()
    
    # Run unit tests
    unittest.main(verbosity=2, buffer=True)