#!/usr/bin/env python3
"""
M3U File Processor
Filters M3U files based on inclusion/exclusion strings, minimum name length, and group titles.
Adds tvg-logo attributes to entries and renumbers channels.
"""

import argparse
import re
import sys
from pathlib import Path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Process M3U file and filter out unwanted entries'
    )
    parser.add_argument(
        'input_file',
        help='Path to the input M3U file'
    )
    parser.add_argument(
        'output_file',
        help='Path to the output M3U file'
    )
    parser.add_argument(
        '--exclude',
        '-e',
        nargs='+',
        help='Strings to exclude (entries containing any of these strings will be removed)'
    )
    parser.add_argument(
        '--include',
        '-i',
        nargs='+',
        help='Strings to include in tvg-name (entries must contain at least one of these strings)'
    )
    parser.add_argument(
        '--min-length',
        '-m',
        type=int,
        help='Minimum length for tvg-name (entries shorter than this will be removed)'
    )
    parser.add_argument(
        '--include-groups',
        '-g',
        nargs='+',
        help='Only include entries with these group titles (supports multiple groups)'
    )
    parser.add_argument(
        '--logo',
        '-l',
        help='URL to use for tvg-logo attribute (will be added to all included entries)'
    )
    parser.add_argument(
        '--channel-start',
        '-c',
        type=int,
        help='Starting channel number for channel fields (will increment for each entry)'
    )
    parser.add_argument(
        '--channel-fields',
        '-f',
        choices=['tvg-id', 'tvg-chno', 'both'],
        default='tvg-id',
        help='Which channel field(s) to update with incrementing numbers (default: tvg-id)'
    )
    parser.add_argument(
        '--replace',
        '-r',
        nargs=2,
        action='append',
        metavar=('OLD', 'NEW'),
        help='Replace text (all instances of OLD with NEW). Can be used multiple times.'
    )
    
    return parser.parse_args()

def extract_tvg_name(extinf_line):
    """Extract tvg-name value from EXTINF line."""
    match = re.search(r'tvg-name="([^"]*)"', extinf_line)
    if match:
        return match.group(1)
    return None

def extract_group_title(extinf_line):
    """Extract group-title value from EXTINF line."""
    match = re.search(r'group-title="([^"]*)"', extinf_line)
    if match:
        return match.group(1)
    return None

def add_tvg_logo(extinf_line, logo_url):
    """Add or replace tvg-logo attribute in EXTINF line, placing it before group-title."""
    if not logo_url:
        return extinf_line
    
    # Check if tvg-logo already exists
    logo_pattern = r'tvg-logo="[^"]*"'
    if re.search(logo_pattern, extinf_line):
        # Replace existing tvg-logo
        return re.sub(logo_pattern, f'tvg-logo="{logo_url}"', extinf_line)
    else:
        # Insert new tvg-logo before group-title if it exists
        group_pattern = r'(group-title="[^"]*")'
        if re.search(group_pattern, extinf_line):
            return re.sub(group_pattern, f'tvg-logo="{logo_url}" \\1', extinf_line)
        else:
            # If no group-title, add tvg-logo before the final comma
            parts = extinf_line.rsplit(',', 1)
            if len(parts) == 2:
                return f'{parts[0]} tvg-logo="{logo_url}",{parts[1]}'
            else:
                # Fallback: just append it
                return f'{extinf_line} tvg-logo="{logo_url}"'
    
    return extinf_line

def update_channel_fields(extinf_line, channel_number, channel_fields):
    """Update or add channel fields with the specified channel number."""
    updated_line = extinf_line
    
    if channel_fields in ['tvg-id', 'both']:
        # Update tvg-id
        tvg_id_pattern = r'tvg-id="[^"]*"'
        if re.search(tvg_id_pattern, updated_line):
            # Replace existing tvg-id
            updated_line = re.sub(tvg_id_pattern, f'tvg-id="{channel_number}"', updated_line)
        else:
            # Insert new tvg-id after #EXTINF: but before other attributes
            extinf_parts = updated_line.split(' ', 1)
            if len(extinf_parts) == 2:
                updated_line = f'{extinf_parts[0]} tvg-id="{channel_number}" {extinf_parts[1]}'
            else:
                # Fallback: just append it
                updated_line = f'{updated_line} tvg-id="{channel_number}"'
    
    if channel_fields in ['tvg-chno', 'both']:
        # Update tvg-chno
        tvg_chno_pattern = r'tvg-chno="[^"]*"'
        if re.search(tvg_chno_pattern, updated_line):
            # Replace existing tvg-chno
            updated_line = re.sub(tvg_chno_pattern, f'tvg-chno="{channel_number}"', updated_line)
        else:
            # Insert new tvg-chno after #EXTINF: but before other attributes
            extinf_parts = updated_line.split(' ', 1)
            if len(extinf_parts) == 2:
                updated_line = f'{extinf_parts[0]} tvg-chno="{channel_number}" {extinf_parts[1]}'
            else:
                # Fallback: just append it
                updated_line = f'{updated_line} tvg-chno="{channel_number}"'
    
    return updated_line

def apply_replacements(line, replacements):
    """Apply all text replacements to a line."""
    if not replacements:
        return line
    
    updated_line = line
    for old_text, new_text in replacements:
        updated_line = updated_line.replace(old_text, new_text)
    
    return updated_line

def process_m3u_file(input_path, output_path, exclude_strings=None, include_strings=None, min_length=None, include_groups=None, logo_url=None, channel_start=None, channel_fields='tvg-id', replacements=None):
    """
    Process M3U file and write filtered version.
    
    Args:
        input_path: Path to input M3U file
        output_path: Path to output M3U file
        exclude_strings: List of strings to exclude (optional)
        include_strings: List of strings to include in tvg-name (optional)
        min_length: Minimum tvg-name length (optional)
        include_groups: List of group titles to include (optional)
        logo_url: URL to use for tvg-logo attribute (optional)
        channel_start: Starting channel number for channel fields (optional)
        channel_fields: Which channel field(s) to update (tvg-id, tvg-chno, or both)
        replacements: List of (old, new) text replacement tuples (optional)
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()
    except FileNotFoundError:
        print(f"Error: Input file '{input_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    processed_lines = []
    entries_processed = 0
    entries_excluded = 0
    current_channel = channel_start
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
            
        # Check if this is an EXTINF line
        if line.startswith('#EXTINF:'):
            # Check if there's a URL following this line
            if i + 1 < len(lines) and not lines[i + 1].startswith('#'):
                extinf_line = line
                url_line = lines[i + 1].strip()
                
                should_exclude = False
                
                # Check group title filter FIRST (takes precedence)
                if include_groups:
                    group_title = extract_group_title(extinf_line)
                    if group_title:
                        # Check if group_title matches any of the included groups (case-insensitive)
                        group_title_lower = group_title.lower()
                        group_matched = any(
                            included_group.lower() in group_title_lower 
                            for included_group in include_groups
                        )
                        if not group_matched:
                            should_exclude = True
                    else:
                        # No group title found, exclude if we're filtering by groups
                        should_exclude = True
                
                # Check include strings (tvg-name must contain at least one) - case-insensitive
                if not should_exclude and include_strings:
                    tvg_name = extract_tvg_name(extinf_line)
                    if tvg_name:
                        # Check if tvg_name contains any of the include strings (case-insensitive)
                        tvg_name_lower = tvg_name.lower()
                        name_matched = any(
                            include_string.lower() in tvg_name_lower 
                            for include_string in include_strings
                        )
                        if not name_matched:
                            should_exclude = True
                    else:
                        # No tvg-name found, exclude if we're filtering by include strings
                        should_exclude = True
                
                # Check exclusion strings - case-insensitive
                if not should_exclude and exclude_strings:
                    extinf_line_lower = extinf_line.lower()
                    for exclude_string in exclude_strings:
                        if exclude_string.lower() in extinf_line_lower:
                            should_exclude = True
                            break  # No need to check other exclusion strings
                
                # Check minimum length
                if not should_exclude and min_length is not None:
                    tvg_name = extract_tvg_name(extinf_line)
                    if tvg_name and len(tvg_name) < min_length:
                        should_exclude = True
                
                if should_exclude:
                    entries_excluded += 1
                    # Skip both EXTINF line and URL line
                    i += 2
                    continue
                else:
                    # Apply text replacements to both EXTINF and URL lines
                    if replacements:
                        extinf_line = apply_replacements(extinf_line, replacements)
                        url_line = apply_replacements(url_line, replacements)
                    
                    # Add tvg-logo if specified
                    if logo_url:
                        extinf_line = add_tvg_logo(extinf_line, logo_url)
                    
                    # Update channel fields if specified
                    if channel_start is not None:
                        extinf_line = update_channel_fields(extinf_line, current_channel, channel_fields)
                        current_channel += 1
                    
                    # Keep both lines
                    processed_lines.append(extinf_line)
                    processed_lines.append(url_line)
                    entries_processed += 1
                    i += 2
                    continue
            else:
                # No URL following, just keep the EXTINF line (with replacements if specified)
                if replacements:
                    line = apply_replacements(line, replacements)
                processed_lines.append(line)
                i += 1
        else:
            # Keep other metadata lines (like #EXTM3U) and comments (with replacements if specified)
            if replacements:
                line = apply_replacements(line, replacements)
            processed_lines.append(line)
            i += 1
    
    # Write output file
    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write('\n'.join(processed_lines))
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)
    
    print(f"Processing complete!")
    print(f"Entries processed: {entries_processed}")
    print(f"Entries excluded: {entries_excluded}")
    if logo_url:
        print(f"Added tvg-logo: {logo_url}")
    if include_strings:
        print(f"Included tvg-name strings: {', '.join(include_strings)}")
    if replacements:
        print(f"Text replacements applied: {len(replacements)}")
        for i, (old_text, new_text) in enumerate(replacements, 1):
            print(f"  {i}. '{old_text}' → '{new_text}'")
    if channel_start is not None:
        field_desc = channel_fields
        if channel_fields == 'both':
            field_desc = 'tvg-id and tvg-chno'
        print(f"Channel numbers ({field_desc}): {channel_start} to {current_channel - 1}")
    print(f"Output written to: {output_path}")

def main():
    """Main function."""
    args = parse_arguments()
    
    # Validate input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)
    
    # Process the M3U file
    process_m3u_file(
        input_path=args.input_file,
        output_path=args.output_file,
        exclude_strings=args.exclude,
        include_strings=args.include,
        min_length=args.min_length,
        include_groups=args.include_groups,
        logo_url=args.logo,
        channel_start=args.channel_start,
        channel_fields=args.channel_fields,
        replacements=args.replace
    )

if __name__ == "__main__":
    main()

