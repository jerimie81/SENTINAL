import argparse
from . import core

def main():
    parser = argparse.ArgumentParser(description="Sentinal: A system administration CLI.")
    parser.add_argument("--health-check", action="store_true", help="Perform a system health check.")
    
    args = parser.parse_args()

    if args.health_check:
        print("Performing health check...")
        core.health_check()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
