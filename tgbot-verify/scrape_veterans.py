#!/usr/bin/env python3
"""
Veteran Data Scraper CLI Tool

Công cụ dòng lệnh để thu thập thông tin cựu chiến binh từ VLM (vlm.cem.va.gov)
dùng cho xác thực Military SheerID.

Sử dụng:
    python scrape_veterans.py                    # Scrape mặc định
    python scrape_veterans.py -n b -y 2025 -c 50  # Tùy chỉnh tham số
    python scrape_veterans.py --bulk              # Scrape hàng loạt
    python scrape_veterans.py --output data.json  # Xuất ra file JSON
"""

import argparse
import asyncio
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from military.vlm_scraper import VLMScraper, scrape_veterans_sync, scrape_veterans_bulk_sync


def print_banner():
    """Print ASCII banner"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║        🎖️  VETERAN DATA SCRAPER for Military Verify        ║
║           Scrapes veteran info from VLM.cem.va.gov         ║
╚═══════════════════════════════════════════════════════════╝
    """)


def format_veteran_line(vet: dict) -> str:
    """Format veteran data to pipe-delimited line"""
    return "|".join([
        vet.get('firstName', ''),
        vet.get('lastName', ''),
        vet.get('branch', 'Navy'),
        vet.get('birthMonth', 'January'),
        vet.get('birthDay', '1'),
        vet.get('birthYear', '1950'),
        vet.get('dischargeMonth', 'January'),
        vet.get('dischargeDay', '1'),
        vet.get('dischargeYear', '2025'),
        vet.get('email', '')
    ])


def main():
    parser = argparse.ArgumentParser(
        description='Scrape veteran data from VLM for military verification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrape_veterans.py                        # Default: lastName=b, year=2025, count=20
  python scrape_veterans.py -n smith -y 2025 -c 50 # Search Smith, 2025, max 50 results
  python scrape_veterans.py --bulk -c 100          # Bulk search, 100 results
  python scrape_veterans.py -o veterans.json       # Export to JSON file
  python scrape_veterans.py -o veterans.txt --txt  # Export to text file
        """
    )
    
    parser.add_argument('-n', '--name', default='b',
                        help='Last name prefix to search (default: b)')
    parser.add_argument('-y', '--year', type=int, default=2025,
                        help='Death year to filter (default: 2025)')
    parser.add_argument('-c', '--count', type=int, default=20,
                        help='Maximum number of results (default: 20)')
    parser.add_argument('-b', '--branch', default='',
                        help='Military branch filter (Army, Navy, Air Force, etc.)')
    parser.add_argument('--bulk', action='store_true',
                        help='Perform bulk scraping with multiple searches')
    parser.add_argument('-o', '--output', default='',
                        help='Output file path (JSON or TXT)')
    parser.add_argument('--txt', action='store_true',
                        help='Output as pipe-delimited text instead of JSON')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet mode - only output data')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_banner()
        print(f"🔍 Search Parameters:")
        print(f"   • Last Name: {args.name}")
        print(f"   • Death Year: {args.year}")
        print(f"   • Max Count: {args.count}")
        if args.branch:
            print(f"   • Branch: {args.branch}")
        if args.bulk:
            print(f"   • Mode: BULK (multiple searches)")
        print()
        print("⏳ Scraping VLM... Please wait...")
        print()
    
    try:
        if args.bulk:
            # Bulk scraping
            last_names = ['a', 'b', 'c', 'd', 'e', 's', 'm', 'j', 'w', 'h', 'k', 'l', 'p', 'r', 't']
            branches = ['Navy', 'Army', 'Air Force', 'Marine Corps', 'Coast Guard'] if not args.branch else [args.branch]
            
            veterans = scrape_veterans_bulk_sync(
                last_names=last_names,
                branches=branches,
                death_year=args.year,
                max_total=args.count
            )
        else:
            # Single search
            veterans = scrape_veterans_sync(
                last_name=args.name,
                branch=args.branch,
                death_year=args.year,
                max_results=args.count
            )
        
        if not veterans:
            if not args.quiet:
                print("❌ No veterans found. Try different search parameters.")
            sys.exit(1)
        
        if not args.quiet:
            print(f"✅ Found {len(veterans)} veterans!\n")
            print("=" * 60)
            print("VETERAN LIST:")
            print("=" * 60)
            for i, vet in enumerate(veterans[:30], 1):
                print(f"{i:3}. {vet.get('firstName', ''):<15} {vet.get('lastName', ''):<20} "
                      f"{vet.get('branch', 'N/A'):<12} {vet.get('birthYear', 'N/A')}")
            if len(veterans) > 30:
                print(f"... and {len(veterans) - 30} more")
            print("=" * 60)
            print()
        
        # Output to file or stdout
        if args.output:
            if args.txt or args.output.endswith('.txt'):
                # Text format
                text_data = '\n'.join([format_veteran_line(v) for v in veterans])
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(text_data)
                if not args.quiet:
                    print(f"📁 Saved to {args.output} (TXT format)")
            else:
                # JSON format
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(veterans, f, indent=2, ensure_ascii=False)
                if not args.quiet:
                    print(f"📁 Saved to {args.output} (JSON format)")
        else:
            # Print to stdout in pipe format
            if not args.quiet:
                print("📋 PIPE-DELIMITED DATA (copy this):")
                print("-" * 60)
            for vet in veterans:
                print(format_veteran_line(vet))
            if not args.quiet:
                print("-" * 60)
        
        if not args.quiet:
            print()
            print("💡 Usage:")
            print("   1. Copy the pipe-delimited data above")
            print("   2. Use with /verify6 command in Telegram bot")
            print("   3. Or paste into military-verify-extension")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
