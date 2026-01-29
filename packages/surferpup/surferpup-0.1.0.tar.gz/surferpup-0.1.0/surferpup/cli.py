import argparse
import asyncio
from .validate import is_allowed_target
from .runner import run
from colorama import Fore, Style, init
init(autoreset=True)

banner = f"""{Fore.LIGHTBLUE_EX}
 ░▒▓███████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓████████▓▒░▒▓████████▓▒░▒▓███████▓▒░       ░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░  
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓██████▓▒░ ░▒▓██████▓▒░ ░▒▓███████▓▒░       ░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░  
       ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
       ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░       ░▒▓██████▓▒░░▒▓█▓▒░        
                                                                                                                              
                            Application Stress-Testing Tool - Authorised use only


--------------------
HOW TO USE SURFERPUP
--------------------
    Arguments:
        -w (How many workers, default 20)
        -r (Requests, default 200)
        -t (Timeout, default 1)

    Usage:
        - Only localhost or private ranges/networks allowed.
    
    Examples:
        Default
            surferpup <local or private url>:<port>

        Manual
            surferpup -w <workers> -r <requests> -t <timeout> <local or private url>:<port>

"""

def main():
    print(banner)

    p = argparse.ArgumentParser(
        description="Local application stress tester",
        add_help=False,
        usage=argparse.SUPPRESS,
        formatter_class=argparse.RawTextHelpFormatter
    )

    p.add_argument("url", help="Target URL (localhost/private only)")
    p.add_argument("-w", "--workers", type=int, default=20, help="Number of workers")
    p.add_argument("-r", "--requests", type=int, default=200, help="Total requests")
    p.add_argument("-t", "--timeout", type=int, default=1, help="Timeout per request")

    args = p.parse_args()

    if not is_allowed_target(args.url):
        raise SystemExit("Target not allowed. Only localhost or private networks.")

    # Run stress test
    report = asyncio.run(
        run(args.url, args.workers, args.requests, args.timeout)
    )

    print("\nResults")
    for k, v in report.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
