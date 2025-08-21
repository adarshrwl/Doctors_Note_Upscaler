"""
Application Launcher for Doctors Note Upscaler
This script allows users to choose between GUI and console modes.
"""

import sys
import argparse

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(description='Doctors Note Upscaler Launcher')
    parser.add_argument('--mode', choices=['gui', 'console'], default='gui',
                       help='Run mode: gui (default) or console')
    parser.add_argument('--console', action='store_true',
                       help='Run in console mode (shortcut for --mode=console)')
    
    args = parser.parse_args()
    
    # Determine run mode
    if args.console:
        run_mode = 'console'
    else:
        run_mode = args.mode
    
    print(f"🏥 Starting Doctors Note Upscaler in {run_mode} mode...")
    
    if run_mode == 'gui':
        try:
            from gui_main import main as gui_main
            gui_main()
        except ImportError as e:
            print("❌ GUI dependencies not found!")
            print("💡 Install GUI requirements with: pip install -r requirements_gui.txt")
            print("   Or run in console mode with: python launcher.py --console")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error starting GUI: {e}")
            print("💡 Try running in console mode: python launcher.py --console")
            sys.exit(1)
    
    elif run_mode == 'console':
        try:
            from main import main as console_main
            console_main()
        except Exception as e:
            print(f"❌ Error starting console application: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()