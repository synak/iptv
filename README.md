## parse_epg.py

Filter EPG XMLTV data with M3U filtering, exclusion, date range, description stripping, etc.

Command line options:
```
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input XMLTV file
  -c CHANNELS, --channels CHANNELS
                        File containing channel IDs to extract
  -m M3U, --m3u M3U     M3U playlist file for filtering by tvg-id
  -o OUTPUT, --output OUTPUT
                        Output XML file
```
Date range options:
```
  -df DAYS_FUTURE, --days-future DAYS_FUTURE
                        Number of days in the future to include
  -dp DAYS_PAST, --days-past DAYS_PAST
                        Number of days in the past to include
  --start START         Start date (YYYY-MM-DD)
```
Exclusion options:
```
  -x EXCLUDE, --exclude EXCLUDE
                        Exclude channel IDs
  -xf EXCLUDE_FILE, --exclude-file EXCLUDE_FILE
                        File containing channel IDs to exclude
```
Processing options:
```
  --nodesc              Remove all <desc> tags from the output
  --basic               Strip programmes to minimal format (attributes + title only)
```
Example:

Filter an EPG file using a M3U while setting date ranges (yesterday to +7 days), writing only the essential EPG output (excludes description, rating, etc. tags). Useful for when you have a pre-filtered m3u using a tool such as m3u-editor and not the entire feed from the provider.
  
```python parse_epg.py -i epg.xml -o filtered_epg.xml -m playlist.m3u -dp 1 -df 7 --basic```

------------
------------

## parse_m3u.py

Process M3U file and filter out unwanted entries

positional arguments:
```
  input_file            Path to the input M3U file
  output_file           Path to the output M3U file
```
options:
```
  -h, --help            show this help message and exit
  --exclude EXCLUDE [EXCLUDE ...], -e EXCLUDE [EXCLUDE ...]
                        Strings to exclude (entries containing any of these strings will be removed)
  --include INCLUDE [INCLUDE ...], -i INCLUDE [INCLUDE ...]
                        Strings to include in tvg-name (entries must contain at least one of these strings)
  --min-length MIN_LENGTH, -m MIN_LENGTH
                        Minimum length for tvg-name (entries shorter than this will be removed)
  --include-groups INCLUDE_GROUPS [INCLUDE_GROUPS ...], -g INCLUDE_GROUPS [INCLUDE_GROUPS ...]
                        Only include entries with these group titles (supports multiple groups)
  --logo LOGO, -l LOGO  URL to use for tvg-logo attribute (will be added to all included entries)
  --channel-start CHANNEL_START, -c CHANNEL_START
                        Starting channel number for channel fields (will increment for each entry)
  --channel-fields {tvg-id,tvg-chno,both}, -f {tvg-id,tvg-chno,both}
                        Which channel field(s) to update with incrementing numbers (default: tvg-id)
  --replace OLD NEW, -r OLD NEW
                        Replace text (all instances of OLD with NEW). Can be used multiple times.
```
example - process PPV channels, only outputting those which have upcoming content
```
python3 parse_m3u.py playlist.m3u output.m3u \
   --include-groups "PPV EVENTS" \
   --exclude "NO EVENT" "No events sched" \
   --logo "https://raw.githubusercontent.com/synak/synak.github.io/refs/heads/main/logos/misc/ppv.jpg" \
   --min-length 16 \
   --channel-start 7200 \
   --channel-fields both
```
