#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ગુજરાતી પાઈથન મુખ્ય ફાઈલ - કમાંડ લાઈન ઈન્ટરફેસ

આ ફાઈલ ગુજરાતી પાઈથન કોડ ચલાવવા માટે વાપરી શકાય છે.
"""

import sys
import os
import argparse
from pathlib import Path

try:
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
except ImportError:
    print("Rich library not installed. Install with: pip install rich")
    console = None

# પ્રોજેક્ટ પાથ ઉમેરો
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ગુજરાતી_પાઈથન import કોડ_અનુવાદ_કરો, ગુજરાતી_કોડ_ચલાવો, ગુજરાતી_હેલ્પ
from ગુજરાતી_પાઈથન.સહાયકો import કીવર્ડ_લિસ્ટ, કીવર્ડ_સર્ચ
from ગુજરાતી_પાઈથન.ભૂલ_અનુવાદક import કસ્ટમ_એક્સેપ્શન_હુક

# કસ્ટમ એરર હેન્ડલર સેટ કરો
sys.excepthook = કસ્ટમ_એક્સેપ્શન_હુક


def _ensure_utf8_output():
    """
    Windows પર UTF-8 આઉટપુટ ની ખાતરી કરે છે
    """
    if sys.platform == 'win32':
        # stdout અને stderr ને UTF-8 માટે reconfigure કરો
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        
        # વૈકલ્પિક રીતે environment variables સેટ કરો
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'


# આયાત કરતી વખતે UTF-8 setup કરો
_ensure_utf8_output()


def ફાઈલ_ચલાવો(ફાઈલ_પાથ):
    """
    ગુજરાતી પાઈથન ફાઈલ ચલાવે છે
    
    પેરામીટર:
        ફાઈલ_પાથ (str): ફાઈલનો પાથ
    """
    try:
        with open(ફાઈલ_પાથ, 'r', encoding='utf-8') as f:
            કોડ = f.read()
        
        પરિણામ = ગુજરાતી_કોડ_ચલાવો(કોડ)
        
        if પરિણામ['આઉટપુટ']:
            if console:
                console.print(Panel(પરિણામ['આઉટપુટ'], title="આઉટપુટ", border_style="green"))
            else:
                print(પરિણામ['આઉટપુટ'], end='')
        
        if not પરિણામ['સફળતા']:
            if console:
                console.print(f"[bold red]એરર: {પરિણામ['એરર']}[/]")
            else:
                print(f"એરર: {પરિણામ['એરર']}", file=sys.stderr)
            sys.exit(1)
            
    except FileNotFoundError:
        print(f"એરર: ફાઈલ '{ફાઈલ_પાથ}' મળી નથી.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"એરર: {e}", file=sys.stderr)
        sys.exit(1)


def ઈન્ટરએક્ટિવ_મોડ():
    """
    ઈન્ટરએક્ટિવ REPL મોડ
    """
    print("ગુજરાતી પાઈથન ઈન્ટરએક્ટિવ મોડ")
    print("બહાર નીકળવા માટે 'બહાર નીકળો' અથવા Ctrl+C દબાવો")
    print("મદદ માટે 'મદદ()' ટાઈપ કરો")
    print("-" * 50)
    
    while True:
        try:
            કોડ = input("ગુજરાતી>>> ")
            
            if કોડ.strip() == "બહાર નીકળો" or કોડ.strip() == "exit":
                break
            elif કોડ.strip() == "મદદ()" or કોડ.strip() == "help()":
                print(ગુજરાતી_હેલ્પ())
                continue
            elif કોડ.strip().startswith("મદદ("):
                વિષય = કોડ.strip()[4:-1].strip('"\'')
                print(ગુજરાતી_હેલ્પ(વિષય))
                continue
            elif not કોડ.strip():
                continue
            
            પરિણામ = ગુજરાતી_કોડ_ચલાવો(કોડ)
            
            if પરિણામ['આઉટપુટ']:
                if console:
                    console.print(પરિણામ['આઉટપુટ'], style="bold green")
                else:
                    print(પરિણામ['આઉટપુટ'], end='')
            
            if not પરિણામ['સફળતા']:
                if console:
                    console.print(f"[bold red]એરર: {પરિણામ['એરર']}[/]")
                else:
                    print(f"એરર: {પરિણામ['એરર']}")
                
        except KeyboardInterrupt:
            print("\n\nબાય! આવજો ફરી...")
            break
        except EOFError:
            print("\n\nબાય! આવજો ફરી...")
            break


def કીવર્ડ_યાદી_બતાવો():
    """
    બધા કીવર્ડ્સની યાદી બતાવે છે
    """
    કીવર્ડ્સ = કીવર્ડ_લિસ્ટ()
    if console:
        table = Table(title="ગુજરાતી પાઈથન કીવર્ડ્સ")
        table.add_column("ગુજરાતી", style="cyan")
        table.add_column("અંગ્રેજી", style="magenta")
        
        for ગુજરાતી, અંગ્રેજી in કીવર્ડ્સ.items():
            table.add_row(ગુજરાતી, અંગ્રેજી)
            
        console.print(table)
    else:
        print("ગુજરાતી પાઈથન કીવર્ડ્સ:")
        print("=" * 50)
        
        for ગુજરાતી, અંગ્રેજી in કીવર્ડ્સ.items():
            print(f"{ગુજરાતી:15} → {અંગ્રેજી}")


def કીવર્ડ_શોધાવો(શોધ_ટર્મ):
    """
    કીવર્ડ શોધે છે
    
    પેરામીટર:
        શોધ_ટર્મ (str): શોધવાનો ટર્મ
    """
    પરિણામો = કીવર્ડ_સર્ચ(શોધ_ટર્મ)
    
    if પરિણામો:
        print(f"'{શોધ_ટર્મ}' માટે મળતા કીવર્ડ્સ:")
        print("-" * 30)
        for પરિણામ in પરિણામો:
            print(f"{પરિણામ['ગુજરાતી']:15} → {પરિણામ['અંગ્રેજી']}")
    else:
        print(f"'{શોધ_ટર્મ}' માટે કોઈ કીવર્ડ મળ્યો નથી.")


def અનુવાદ_કરો(ફાઈલ_પાથ, આઉટપુટ_ફાઈલ=None):
    """
    ગુજરાતી કોડને અંગ્રેજી પાઈથન કોડમાં અનુવાદ કરે છે
    
    પેરામીટર:
        ફાઈલ_પાથ (str): ઇનપુટ ફાઈલ
        આઉટપુટ_ફાઈલ (str): આઉટપુટ ફાઈલ (વૈકલ્પિક)
    """
    try:
        with open(ફાઈલ_પાથ, 'r', encoding='utf-8') as f:
            ગુજરાતી_કોડ = f.read()
        
        અંગ્રેજી_કોડ = કોડ_અનુવાદ_કરો(ગુજરાતી_કોડ)
        
        if આઉટપુટ_ફાઈલ:
            with open(આઉટપુટ_ફાઈલ, 'w', encoding='utf-8') as f:
                f.write(અંગ્રેજી_કોડ)
            if console:
                console.print(f"[bold green]અનુવાદ પૂર્ણ: {આઉટપુટ_ફાઈલ}[/]")
            else:
                print(f"અનુવાદ પૂર્ણ: {આઉટપુટ_ફાઈલ}")
        else:
            if console:
                syntax = Syntax(અંગ્રેજી_કોડ, "python", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="અનુવાદિત કોડ", border_style="blue"))
            else:
                print("અનુવાદિત કોડ:")
                print("-" * 30)
                print(અંગ્રેજી_કોડ)
            
    except FileNotFoundError:
        print(f"એરર: ફાઈલ '{ફાઈલ_પાથ}' મળી નથી.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"એરર: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """
    મુખ્ય ફંક્શન - કમાંડ લાઈન આર્ગ્યુમેન્ટ્સ હેન્ડલ કરે છે
    """
    parser = argparse.ArgumentParser(
        description='ગુજરાતી પાઈથન - ગુજરાતી ભાષામાં પાઈથન પ્રોગ્રામિંગ',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ઉદાહરણો:
  python મુખ્ય.py                          # ઈન્ટરએક્ટિવ મોડ
  python મુખ્ય.py ફાઈલ.py                   # ફાઈલ ચલાવો  
  python મુખ્ય.py --keywords               # કીવર્ડ્સની યાદી
  python મુખ્ય.py --search "પ્રિન્ટ"        # કીવર્ડ શોધો
  python મુખ્ય.py --translate ફાઈલ.py      # અનુવાદ કરો
  python મુખ્ય.py --help                   # મદદ
        """
    )
    
    parser.add_argument('file', nargs='?', help='ચલાવવાની ગુજરાતી પાઈથન ફાઈલ')
    parser.add_argument('-i', '--interactive', action='store_true', help='ઈન્ટરએક્ટિવ મોડ')
    parser.add_argument('-k', '--keywords', action='store_true', help='કીવર્ડ્સની યાદી બતાવો')
    parser.add_argument('-s', '--search', metavar='TERM', help='કીવર્ડ શોધો')
    parser.add_argument('-t', '--translate', metavar='FILE', help='ગુજરાતી કોડને અંગ્રેજીમાં અનુવાદ કરો')
    parser.add_argument('-o', '--output', metavar='FILE', help='અનુવાદ માટે આઉટપુટ ફાઈલ')
    
    args = parser.parse_args()
    
    # કીવર્ડ્સ બતાવો
    if args.keywords:
        કીવર્ડ_યાદી_બતાવો()
        return
    
    # કીવર્ડ શોધો
    if args.search:
        કીવર્ડ_શોધાવો(args.search)
        return
    
    # અનુવાદ કરો
    if args.translate:
        અનુવાદ_કરો(args.translate, args.output)
        return
    
    # ફાઈલ ચલાવો
    if args.file:
        ફાઈલ_ચલાવો(args.file)
        return
    
    # ઈન્ટરએક્ટિવ મોડ (ડિફોલ્ટ)
    ઈન્ટરએક્ટિવ_મોડ()


if __name__ == "__main__":
    main()