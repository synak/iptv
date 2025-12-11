#!/usr/bin/env python3
"""
EPG Channel Filter Script - Version 8
With M3U filtering, exclusion, date range, description stripping, and basic mode
"""

import xml.etree.ElementTree as ET
import argparse
import sys
import os
import re
from datetime import datetime, timedelta

def read_channel_ids(channel_file):
    if not channel_file:
        return None
    
    channel_ids = set()
    try:
        with open(channel_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    channel_ids.add(line)
        print(f"Read {len(channel_ids)} channel IDs from channel file")
        return channel_ids
    except FileNotFoundError:
        print(f"Error: Channel file '{channel_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading channel file: {e}")
        sys.exit(1)

def read_m3u_channels(m3u_file):
    """
    Read channel IDs from M3U file by extracting tvg-id values
    """
    if not m3u_file:
        return None
    
    channel_ids = set()
    try:
        with open(m3u_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Look for EXTINF lines that contain tvg-id
                if line.startswith('#EXTINF:'):
                    # Extract tvg-id using regex
                    tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
                    if tvg_id_match:
                        tvg_id = tvg_id_match.group(1)
                        if tvg_id:  # Only add non-empty IDs
                            channel_ids.add(tvg_id)
        
        print(f"Found {len(channel_ids)} channel IDs in M3U file")
        return channel_ids
        
    except FileNotFoundError:
        print(f"Error: M3U file '{m3u_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading M3U file: {e}")
        sys.exit(1)

def read_exclusion_file(exclude_file):
    """
    Read exclusion ranges from a file, ignoring comments and empty lines
    """
    if not exclude_file:
        return set()
    
    exclusion_ranges = set()
    try:
        with open(exclude_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse the line which may contain one or more ranges
                exclusion_ranges.update(parse_range(line))
                
        print(f"Read {len(exclusion_ranges)} exclusion patterns from file")
        return exclusion_ranges
        
    except FileNotFoundError:
        print(f"Error: Exclusion file '{exclude_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading exclusion file: {e}")
        sys.exit(1)

def parse_range(range_str):
    """
    Parse numeric range strings like:
    - "100" (single number)
    - "100-200" (range)
    - "100,200,300" (comma-separated)
    - "100-200,300,400-500" (mixed)
    Returns a set of channel IDs to exclude
    """
    excluded = set()
    
    # Split by commas first
    parts = [part.strip() for part in range_str.split(',')]
    
    for part in parts:
        if '-' in part:
            # Handle range like "100-200"
            try:
                start, end = part.split('-')
                start = start.strip()
                end = end.strip()
                
                # Extract numeric parts from channel IDs if they contain numbers
                start_num = int(''.join(filter(str.isdigit, start)) or 0)
                end_num = int(''.join(filter(str.isdigit, end)) or 0)
                
                # Generate all numbers in the range
                for num in range(start_num, end_num + 1):
                    excluded.add(str(num))
                    # Also add common channel ID patterns
                    excluded.add(f"channel{num}")
                    excluded.add(f"ch{num}")
                    excluded.add(f"id{num}")
                    
            except ValueError as e:
                print(f"Warning: Invalid range format '{part}': {e}")
        else:
            # Handle single number or exact string
            excluded.add(part.strip())
            # Also try to extract numeric part for matching
            numeric_part = ''.join(filter(str.isdigit, part))
            if numeric_part:
                excluded.add(numeric_part)
    
    return excluded

def parse_exclusion_ranges(exclude_args, exclude_file_args):
    """
    Parse multiple exclusion ranges from command line arguments and files
    """
    excluded = set()
    
    # Parse command line exclusion arguments
    if exclude_args:
        for arg in exclude_args:
            excluded.update(parse_range(arg))
    
    # Parse exclusion files
    if exclude_file_args:
        for exclude_file in exclude_file_args:
            excluded.update(read_exclusion_file(exclude_file))
    
    if excluded:
        print(f"Total exclusion patterns: {len(excluded)}")
    
    return excluded

def should_exclude_channel(channel_id, exclude_patterns):
    """
    Check if a channel ID should be excluded based on patterns
    """
    if not exclude_patterns:
        return False
    
    # Check exact match
    if channel_id in exclude_patterns:
        return True
    
    # Check if any numeric pattern matches
    channel_numeric = ''.join(filter(str.isdigit, channel_id))
    if channel_numeric and channel_numeric in exclude_patterns:
        return True
    
    # Check common patterns
    for pattern in exclude_patterns:
        if pattern.isdigit():
            # If pattern is a number, check if it appears in channel ID
            if pattern in channel_id:
                return True
    
    return False

def parse_xmltv_timestamp(timestamp):
    """
    Parse XMLTV timestamp format (YYYYMMDDHHMMSS +0000)
    Returns datetime object
    """
    try:
        dt_str = timestamp[:14]
        return datetime.strptime(dt_str, '%Y%m%d%H%M%S')
    except ValueError as e:
        print(f"Warning: Could not parse timestamp '{timestamp}': {e}")
        return None

def parse_date_string(date_str):
    """
    Parse date string in YYYY-MM-DD format
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

def safe_remove_descriptions(element):
    """
    Safely remove all <desc> tags from the element and its children.
    Uses multiple approaches to handle different XML structures.
    """
    if element is None:
        return
    
    # Approach 1: Direct removal using findall (most common case)
    try:
        # Find all desc elements at any depth
        for desc in element.findall('.//desc'):
            try:
                parent = desc.getparent()
                if parent is not None:
                    parent.remove(desc)
            except (AttributeError, TypeError) as e:
                print(f"Warning: Could not remove desc element: {e}")
                continue
    except Exception as e:
        print(f"Warning: Error in findall approach: {e}")
        # Fall back to recursive approach
        recursive_remove_descriptions(element)

def recursive_remove_descriptions(element):
    """
    Recursively remove desc elements using a safer iterative approach
    """
    if element is None:
        return
    
    # Process children safely
    children = list(element)  # Create a copy to avoid modification during iteration
    for child in children:
        if child.tag == 'desc':
            try:
                element.remove(child)
            except (AttributeError, ValueError) as e:
                print(f"Warning: Could not remove desc tag: {e}")
                continue
        else:
            # Recursively process non-desc elements
            recursive_remove_descriptions(child)

def safe_strip_descriptions(root_element):
    """
    Main function to safely strip descriptions from the entire XML tree
    """
    if root_element is None:
        return
    
    try:
        # Use the safer recursive approach as primary method
        recursive_remove_descriptions(root_element)
    except Exception as e:
        print(f"Warning: Error during description stripping: {e}")
        print("Continuing without description removal...")

def strip_to_basic(element):
    """
    Strip programme elements down to only programme attributes and title elements
    Keeps only the essential programme information
    """
    if element is None or element.tag != 'programme':
        return
    
    # Create a list of children to remove
    children_to_remove = []
    
    for child in element:
        if child.tag != 'title':
            children_to_remove.append(child)
    
    # Remove all non-title children
    for child in children_to_remove:
        element.remove(child)

def safe_strip_to_basic(programme_element):
    """
    Safely strip programme elements to basic format
    """
    if programme_element is None:
        return
    
    try:
        strip_to_basic(programme_element)
    except Exception as e:
        print(f"Warning: Error during basic stripping: {e}")
        print("Continuing without basic mode processing...")

def parse_epg_data(xml_file, channel_ids, exclude_patterns, days_future=None, days_past=None, start_date=None, strip_descriptions=False, basic_mode=False):
    try:
        # Parse the XML file with error recovery
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            print("Attempting to parse with error recovery...")
            # Try parsing with error recovery
            parser = ET.XMLParser(recover=True)
            tree = ET.parse(xml_file, parser=parser)
        
        root = tree.getroot()
        
        channels = []
        programmes = []
        found_channel_ids = set()
        
        # Calculate time range based on new parameters
        now = datetime.now()
        range_start = None
        range_end = None
        
        if days_past is not None:
            range_start = now - timedelta(days=days_past)
        elif start_date is not None:
            range_start = start_date
        
        if days_future is not None:
            range_end = now + timedelta(days=days_future)
        
        # If only one bound is specified, set the other to a reasonable default
        if range_start and not range_end:
            range_end = range_start + timedelta(days=365)  # 1 year default
        elif range_end and not range_start:
            range_start = now - timedelta(days=365)  # 1 year default
        
        if range_start and range_end:
            print(f"Date range: {range_start.strftime('%Y-%m-%d')} to {range_end.strftime('%Y-%m-%d')}")
        
        # First pass: collect channels and programmes with filtering
        for elem in root:
            if elem.tag == 'channel':
                channel_id = elem.get('id')
                if channel_id is None:
                    continue
                    
                # Check if channel should be included based on inclusion list
                include_channel = (channel_ids is None or channel_id in channel_ids)
                
                # Check if channel should be excluded
                exclude_channel = should_exclude_channel(channel_id, exclude_patterns)
                
                if include_channel and not exclude_channel:
                    channels.append(elem)
                    found_channel_ids.add(channel_id)
                    
            elif elem.tag == 'programme':
                channel_ref = elem.get('channel')
                if channel_ref is None:
                    continue
                    
                # Check if programme should be included based on channel inclusion list
                include_programme = (channel_ids is None or channel_ref in channel_ids)
                
                # Check if programme should be excluded based on channel exclusion
                exclude_programme = should_exclude_channel(channel_ref, exclude_patterns)
                
                if include_programme and not exclude_programme:
                    # Check date range if specified
                    if range_start and range_end:
                        start_time = parse_xmltv_timestamp(elem.get('start'))
                        if not start_time or not (range_start <= start_time <= range_end):
                            continue
                    
                    programmes.append(elem)
        
        # Apply processing based on options
        if strip_descriptions:
            print("Stripping descriptions...")
            for channel in channels:
                safe_strip_descriptions(channel)
            for programme in programmes:
                safe_strip_descriptions(programme)
        
        if basic_mode:
            print("Applying basic mode (keeping only programme attributes and title)...")
            for programme in programmes:
                safe_strip_to_basic(programme)
        
        print(f"Results: {len(channels)} channels, {len(programmes)} programmes")
        return channels, programmes, found_channel_ids
        
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        print("This might be due to malformed XML. Try checking your input file.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading XML file: {e}")
        print(f"Error type: {type(e).__name__}")
        sys.exit(1)

def indent(elem, level=0):
    """
    Recursively add indentation and line breaks to XML elements
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def create_filtered_xml(channels, programmes, output_file):
    root = ET.Element('tv')
    
    for channel in channels:
        root.append(channel)
    
    for programme in programmes:
        root.append(programme)
    
    try:
        # Add pretty printing with line breaks between elements
        indent(root)
        
        tree = ET.ElementTree(root)
        
        # Write with custom formatting to ensure each element is on its own line
        with open(output_file, 'wb') as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            
            # Convert to string and manually format
            xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
            
            # Ensure proper line breaks between major elements
            lines = xml_str.split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if line:
                    formatted_lines.append(line)
            
            # Write formatted output
            f.write('\n'.join(formatted_lines).encode('utf-8'))
        
        print(f"Output written to: {output_file}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

def validate_xml_file(file_path):
    """
    Basic validation that the file exists and appears to be XML
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file '{file_path}' not found.")
    
    # Check if file has XML content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line.startswith('<?xml') or first_line.startswith('<tv'):
                return True
            else:
                print(f"Warning: File '{file_path}' doesn't start with XML declaration or <tv> tag")
                return True  # Still try to parse it
    except UnicodeDecodeError:
        print(f"Warning: File '{file_path}' may not be UTF-8 encoded")
        return True  # Still try to parse it

def report_missing_channels(m3u_channel_ids, found_channel_ids):
    """
    Report which channels from the M3U file were not found in the XMLTV file
    """
    if m3u_channel_ids is None:
        return
    
    missing_channels = m3u_channel_ids - found_channel_ids
    if missing_channels:
        # Format missing channels as a compact list
        missing_list = sorted(missing_channels)
        if len(missing_list) <= 10:
            missing_str = ", ".join(missing_list)
            print(f"Missing channels ({len(missing_list)}): {missing_str}")
        else:
            # Show first 5 and last 5 with ellipsis
            first_five = ", ".join(missing_list[:5])
            last_five = ", ".join(missing_list[-5:])
            print(f"Missing channels ({len(missing_list)}): {first_five}, ..., {last_five}")
    else:
        print("All M3U channels found in XMLTV file")

def main():
    parser = argparse.ArgumentParser(
        description='Filter EPG XMLTV data with M3U filtering, exclusion, date range, description stripping, and basic mode',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Extract all programmes for all channels
  python epg_filter.py -i epg.xml -o filtered_epg.xml

  # Filter using M3U file with basic mode (minimal programme data)
  python epg_filter.py -i epg.xml -m playlist.m3u -o filtered_epg.xml --basic

  # Basic mode with date range and description stripping
  python epg_filter.py -i epg.xml -o filtered_epg.xml --basic -df 7 --nodesc

  # Filter using M3U and exclude specific ranges with basic mode
  python epg_filter.py -i epg.xml -m playlist.m3u -o filtered_epg.xml -x 100-200 --basic

  # Combine M3U filtering with exclusion file and basic mode
  python epg_filter.py -i epg.xml -m playlist.m3u -o filtered_epg.xml -xf exclude.txt --basic

Channel selection (use one of):
  -c CHANNELS    Text file with channel IDs (one per line)
  -m M3U_FILE    M3U playlist file (uses tvg-id attributes)

Processing options:
  --nodesc       Remove description tags only
  --basic        Strip programmes to minimal format (attributes + title only)

Exclusion format:
  -x RANGE       Exclude channels (100, 100-200, 100,200,300)
  -xf FILE       File with exclusion ranges

        '''
    )
    
    parser.add_argument('-i', '--input', required=True, help='Input XMLTV file')
    
    # Channel selection options (mutually exclusive)
    channel_group = parser.add_mutually_exclusive_group()
    channel_group.add_argument('-c', '--channels', help='File containing channel IDs to extract')
    channel_group.add_argument('-m', '--m3u', help='M3U playlist file for filtering by tvg-id')
    
    parser.add_argument('-o', '--output', required=True, help='Output XML file')
    
    # Date range options
    date_group = parser.add_argument_group('Date range options')
    date_group.add_argument('-df', '--days-future', type=int, help='Number of days in the future to include')
    date_group.add_argument('-dp', '--days-past', type=int, help='Number of days in the past to include')
    date_group.add_argument('--start', type=parse_date_string, help='Start date (YYYY-MM-DD)')
    
    # Exclusion options
    exclusion_group = parser.add_argument_group('Exclusion options')
    exclusion_group.add_argument('-x', '--exclude', action='append', help='Exclude channel IDs')
    exclusion_group.add_argument('-xf', '--exclude-file', action='append', help='File containing channel IDs to exclude')
    
    # Processing options
    processing_group = parser.add_argument_group('Processing options')
    processing_group.add_argument('--nodesc', action='store_true', help='Remove all <desc> tags from the output')
    processing_group.add_argument('--basic', action='store_true', help='Strip programmes to minimal format (attributes + title only)')
    
    args = parser.parse_args()
    
    # Validate input file
    try:
        validate_xml_file(args.input)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Validate date arguments
    if args.days_future and args.days_future <= 0:
        print("Error: Days future must be a positive number")
        sys.exit(1)
    
    if args.days_past and args.days_past <= 0:
        print("Error: Days past must be a positive number")
        sys.exit(1)
    
    if args.start and not args.days_future:
        print("Warning: Start date specified without days-future")
    
    # Determine channel IDs based on input method
    channel_ids = None
    m3u_channel_ids = None
    
    if args.channels:
        channel_ids = read_channel_ids(args.channels)
        if not channel_ids:
            print("Error: No channel IDs found in the channel file.")
            sys.exit(1)
    elif args.m3u:
        m3u_channel_ids = read_m3u_channels(args.m3u)
        if not m3u_channel_ids:
            print("Error: No tvg-id attributes found in M3U file.")
            sys.exit(1)
        channel_ids = m3u_channel_ids
    else:
        print("No channel filter specified - keeping all channels")
    
    # Parse exclusion patterns from both command line and files
    exclude_patterns = parse_exclusion_ranges(args.exclude, args.exclude_file)
    
    if args.nodesc:
        print("Description stripping enabled")
    
    #if args.basic:
    #    print("Basic mode enabled - keeping only programme attributes and title")
    
    # Show date range info
    date_info = []
    if args.days_past:
        date_info.append(f"past {args.days_past} days")
    if args.days_future:
        date_info.append(f"next {args.days_future} days")
    if args.start:
        date_info.append(f"from {args.start.strftime('%Y-%m-%d')}")
    
    if date_info:
        print(f"Date filter: {', '.join(date_info)}")
    
    try:
        channels, programmes, found_channel_ids = parse_epg_data(
            args.input, 
            channel_ids, 
            exclude_patterns,
            args.days_future, 
            args.days_past, 
            args.start, 
            args.nodesc,
            args.basic
        )
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    
    if not channels:
        print("Warning: No channels found matching the criteria")
    
    create_filtered_xml(channels, programmes, args.output)
    
    # Report missing channels if using M3U filtering
    if args.m3u and m3u_channel_ids:
        report_missing_channels(m3u_channel_ids, found_channel_ids)

if __name__ == '__main__':
    main()

