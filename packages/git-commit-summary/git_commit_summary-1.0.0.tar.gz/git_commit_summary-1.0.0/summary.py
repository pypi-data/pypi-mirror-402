import sys
import re
import argparse
from collections import defaultdict

# Force UTF-8 output for Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    # Fallback class if colorama is not installed
    class Fore:
        GREEN = "\033[92m"
        RED = "\033[91m"
        CYAN = "\033[96m"
        YELLOW = "\033[93m"
        MAGENTA = "\033[95m"
        RESET = "\033[0m"
        BLUE = "\033[94m"
        WHITE = "\033[97m"
    class Style:
        BRIGHT = "\033[1m"
        RESET_ALL = "\033[0m"

AUTHOR_INFO = {
    "Name": "Sai Annam",
    "Handle": "mr_ask_chay / otaku0304",
    "StartMyDev": "https://start-my-dev-dashboard.vercel.app/",
    "PDF Password Remover": "https://pdf-fe-kappa.vercel.app/",
    "Angular i18n SPA": "Multilingual Single Page Application Demo"
}

def print_banner():
    """Prints the author and project banner."""
    print(f"\n{Style.BRIGHT}{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
    print(f"║ {Fore.MAGENTA}Git Commit Summary Tool{Fore.CYAN}                                  ║")
    print(f"║ {Fore.WHITE}Author: {AUTHOR_INFO['Name']} ({AUTHOR_INFO['Handle']}){Fore.CYAN}{' ' * (47 - len(AUTHOR_INFO['Name']) - len(AUTHOR_INFO['Handle']) - 3)}║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Fore.BLUE}Other Projects by Author:{Fore.RESET}")
    for proj, desc in list(AUTHOR_INFO.items())[2:]:
        print(f"  {Fore.YELLOW}• {proj}{Fore.RESET}: {desc}")
    print(f"{Fore.CYAN}──────────────────────────────────────────────────────────{Style.RESET_ALL}\n")

def get_input_stream():
    """Yields lines from stdin properly, handling encoding errors safely."""
    if sys.stdin.isatty():
        print(f"{Fore.RED}❌ Error: Please pipe a git diff or commit.{Fore.RESET}")
        print(f"{Fore.YELLOW}Usage: git show HEAD | python summary.py{Fore.RESET}")
        sys.exit(1)
    
    # Process line by line to prevent Memory DoS
    for line in sys.stdin:
        yield line

def detect_function(line):
    """Detects function definitions in various languages."""
    # Python, Ruby: def name
    if match := re.match(r"\+\s*def\s+([a-zA-Z_]\w*)", line):
        return match.group(1), "Python/Ruby"
    # JS, TS, Java, C#: function name or type name(
    if match := re.match(r"\+\s*(?:async\s+)?function\s+([a-zA-Z_]\w*)", line):
        return match.group(1), "JS/TS"
    # Safe regex for C-like languages avoiding excessive backtracking
    if match := re.match(r"\+\s*(?:public|private|protected|static|\w+)\s+[\w<>]+\s+([a-zA-Z_]\w*)\s*\(", line):
        return match.group(1), "C-Like"
    return None, None

def summarize(line_iterator):
    files = set()
    added = 0
    removed = 0
    functions_added = []
    file_types = defaultdict(int)

    for line in line_iterator:
        # Sanitize input: Strip potential control characters if needed, but git output is usually safe.
        line = line.rstrip() 
        
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 3:
                fpath = parts[2].replace("a/", "", 1)
                files.add(fpath)
                ext = fpath.split(".")[-1] if "." in fpath else "no-ext"
                file_types[ext] += 1
        
        # Count lines
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
            func_name, lang = detect_function(line)
            if func_name:
                functions_added.append(func_name)

        if line.startswith("-") and not line.startswith("---"):
            removed += 1

    return {
        "file_count": len(files),
        "files": files,
        "added": added,
        "removed": removed,
        "net": added - removed,
        "functions_added": functions_added,
        "file_types": file_types
    }

def main():
    parser = argparse.ArgumentParser(description="Summarize git diffs.")
    parser.add_argument("--no-banner", action="store_true", help="Hide author banner")
    args = parser.parse_args()

    if not args.no_banner:
        print_banner()

    try:
        # Use streaming input
        diff_stream = get_input_stream()
        result = summarize(diff_stream)

        print(f"{Style.BRIGHT}📊 Statistics:{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}Files Changed :{Fore.RESET} {result['file_count']}")
        print(f"  {Fore.GREEN}Lines Added   :{Fore.RESET} {result['added']}")
        print(f"  {Fore.RED}Lines Removed :{Fore.RESET} {result['removed']}")
        
        net_color = Fore.GREEN if result['net'] >= 0 else Fore.RED
        print(f"  {Fore.WHITE}Net Change    :{Fore.RESET} {net_color}{result['net']:+d}{Fore.RESET}")
        
        print(f"\n{Style.BRIGHT}📁 File Types:{Style.RESET_ALL}")
        for ext, count in result['file_types'].items():
            print(f"  {Fore.YELLOW}.{ext:<10}{Fore.RESET}: {count}")

        if result["functions_added"]:
            print(f"\n{Style.BRIGHT}✨ New Functions ({len(result['functions_added'])}):{Style.RESET_ALL}")
            # Limit output to prevent terminal flooding (Security/Usability)
            for fn in result["functions_added"][:15]: 
                print(f"  {Fore.CYAN}+ {fn}{Fore.RESET}")
            if len(result["functions_added"]) > 15:
                print(f"  {Fore.WHITE}... and {len(result['functions_added']) - 15} more{Fore.RESET}")
        else:
            print(f"\n{Style.BRIGHT}✨ New Functions:{Style.RESET_ALL} None detected")
            
        print("\n" + f"{Fore.WHITE}Status: {Fore.GREEN}Success{Fore.RESET}")

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}An unexpected error occurred: {e}{Fore.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
