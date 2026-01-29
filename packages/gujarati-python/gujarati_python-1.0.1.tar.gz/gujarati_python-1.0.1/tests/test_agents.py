import unittest
from agents.vyakarana_rakshak import VyakaranRakshak
from agents.bandharan_rakshak import BandharanRakshak
from agents.shaili_rakshak import ShailiRakshak

class TestAgents(unittest.TestCase):
    
    def test_vyakaran_rakshak_typos(self):
        agent = VyakaranRakshak()
        # Code with a typo 'પ્રિન્ટ' instead of 'છાપો'
        bad_code = """
        ડેફ my_func():
            પ્રિન્ટ("Hello")
        """
        issues = agent.check_file(bad_code)
        self.assertTrue(any(i['type'] == 'typo' and 'છાપો' in i['message'] for i in issues))

    def test_bandharan_rakshak_mixed_language(self):
        agent = BandharanRakshak()
        # Code with mixed language: 'if' instead of 'જો'
        bad_code = """
        if True:
            pass
        """
        issues = agent.check_file(bad_code)
        self.assertTrue(any(i['type'] == 'mixed_language' for i in issues))

    def test_bandharan_rakshak_indentation(self):
        agent = BandharanRakshak()
        # Code with 3 spaces indentation (invalid per our rule)
        bad_code = """
        ડેફ test():
           પાસ
        """
        issues = agent.check_file(bad_code)
        self.assertTrue(any(i['type'] == 'indentation' for i in issues))

    def test_shaili_rakshak_docstring(self):
        agent = ShailiRakshak()
        # Function without docstring
        bad_code = """
        ડેફ no_doc():
            પાસ
        """
        issues = agent.check_file(bad_code)
        self.assertTrue(any(i['type'] == 'missing_docstring' for i in issues))

    def test_shaili_rakshak_line_length(self):
        agent = ShailiRakshak()
        # Very long line
        bad_code = "a" * 105
        issues = agent.check_file(bad_code)
        self.assertTrue(any(i['type'] == 'line_length' for i in issues))

if __name__ == '__main__':
    unittest.main()

from agents.suraksha_rakshak import SurakshaRakshak
from agents.karyakshamata_rakshak import KaryakshamataRakshak
from agents.jatilata_rakshak import JatilataRakshak

class TestAdvancedAgents(unittest.TestCase):
    
    def test_suraksha_eval(self):
        agent = SurakshaRakshak()
        bad_code = "eval('rm -rf')"
        issues = agent.check_file(bad_code)
        self.assertTrue(any(i['type'] == 'security_danger' for i in issues))

    def test_suraksha_secret(self):
        agent = SurakshaRakshak()
        bad_code = "password = '123'"
        issues = agent.check_file(bad_code)
        self.assertTrue(any(i['type'] == 'security_secret' for i in issues))

    def test_karyakshamata_import(self):
        agent = KaryakshamataRakshak()
        bad_code = """
        def func():
            import os
        """
        issues = agent.check_file(bad_code)
        self.assertTrue(any(i['type'] == 'perf_import' for i in issues))

    def test_jatilata_length(self):
        agent = JatilataRakshak()
        # Function with 60 lines
        bad_code = "def long_func():\n" + "\n".join(["    pass"] * 60)
        issues = agent.check_file(bad_code)
        self.assertTrue(any(i['type'] == 'complexity_length' for i in issues))
