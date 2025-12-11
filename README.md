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

Filter an EPG file using a M3U while setting date ranges (yesterday to +7 days), writing only the essential EPG output (excludes description, rating, etc. tags)
  
```python parse_epg.py -i epg.xml -o filtered_epg.xml -m playlist.m3u -dp 1 -df 7 --basic```
