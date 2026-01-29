#!/usr/bin/env python3
"""
NetworkDoctor - Main Entry Point
"""
import sys
from networkdoctor.cli.parser import parse_args
from networkdoctor.core.doctor import NetworkDoctor


def main():
    """Main entry point"""
    try:
        args = parse_args()
        doctor = NetworkDoctor(use_cache=not args.no_cache)
        return doctor.run(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())







