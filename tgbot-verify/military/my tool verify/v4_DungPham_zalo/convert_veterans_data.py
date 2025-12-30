"""
Convert veterans data from 10-field format to 6-field format for extension

Input format (all_veterans.txt - 10 fields):
FIRST|LAST|BRANCH|BIRTH_MONTH|BIRTH_DAY|BIRTH_YEAR|DISCHARGE_MONTH|DISCHARGE_DAY|DISCHARGE_YEAR|EMAIL

Output format (for extension - 6 fields):
FIRST|LAST|BRANCH|MONTH|DAY|YEAR

Where MONTH is converted from text (January, February...) to number (01, 02...)
"""

import os

# Month name to number mapping
MONTH_MAP = {
    'january': '01', 'february': '02', 'march': '03', 'april': '04',
    'may': '05', 'june': '06', 'july': '07', 'august': '08',
    'september': '09', 'october': '10', 'november': '11', 'december': '12'
}


def convert_month(month_text):
    """Convert month text to number string (01-12)"""
    month_lower = month_text.strip().lower()
    return MONTH_MAP.get(month_lower, '01')  # Default to 01 if not found


def convert_line(line):
    """Convert a single line from 10-field to 6-field format"""
    parts = line.strip().split('|')
    
    if len(parts) != 10:
        print(f"⚠️ Skipping invalid line (not 10 fields): {line[:50]}...")
        return None
    
    first = parts[0].strip()
    last = parts[1].strip()
    branch = parts[2].strip()
    birth_month = parts[3].strip()  # Keep as text! Extension expects "August" not "08"
    birth_day = parts[4].strip()
    birth_year = parts[5].strip()
    
    # Output format: FIRST|LAST|BRANCH|MONTH|DAY|YEAR
    # Month stays as text (January, February, etc.)
    return f"{first}|{last}|{branch}|{birth_month}|{birth_day}|{birth_year}"


def convert_file(input_path, output_path=None):
    """Convert entire file from 10-field to 6-field format"""
    
    if output_path is None:
        # Create output filename with _converted suffix
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_converted{ext}"
    
    print(f"📂 Input file: {input_path}")
    print(f"📂 Output file: {output_path}")
    
    converted_count = 0
    skipped_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as infile:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for line_num, line in enumerate(infile, 1):
                line = line.strip()
                if not line:
                    continue
                
                converted = convert_line(line)
                if converted:
                    outfile.write(converted + '\n')
                    converted_count += 1
                else:
                    skipped_count += 1
                
                # Progress update every 1000 lines
                if line_num % 1000 == 0:
                    print(f"  📊 Processed {line_num} lines...")
    
    print(f"\n✅ Conversion complete!")
    print(f"   📊 Converted: {converted_count} lines")
    print(f"   ⚠️ Skipped: {skipped_count} lines")
    print(f"   📂 Output saved to: {output_path}")
    
    return output_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # Default: convert all_veterans.txt in same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_file = os.path.join(script_dir, "extension_auto_verify_final", "all_veterans.txt")
        
        if not os.path.exists(input_file):
            print("❌ all_veterans.txt not found!")
            print("Usage: python convert_veterans_data.py <input_file> [output_file]")
            sys.exit(1)
    else:
        input_file = sys.argv[1]
    
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_file(input_file, output_file)
