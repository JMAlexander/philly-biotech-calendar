#!/usr/bin/env python3
"""
Calendar Converter - CSV/Excel to ICS
Converts Philadelphia Life Sciences events from CSV or Excel to iCalendar format
Supports:
- CSV files with standard format
- Excel files with multiple month sheets
"""

import csv
import sys
from datetime import datetime
from pathlib import Path
import hashlib
import re
from zoneinfo import ZoneInfo

# Import Excel parser (will use only if Excel file is provided)
try:
    from excel_parser import ExcelParser
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False


def parse_date(date_str):
    """
    Parse date string to datetime
    Example: 'Wed, Jan 7, 2026' -> datetime object
    """
    try:
        return datetime.strptime(date_str, "%a, %b %d, %Y")
    except:
        return None


def is_all_day_event(time_str):
    """
    Check if event is all-day
    Returns True if: empty, 'All Day', 'TBD', or 'To be released'
    """
    if not time_str:
        return True
    
    time_upper = time_str.upper().strip()
    return time_upper in ['ALL DAY', 'TBD', 'TO BE RELEASED']


def parse_time(time_str):
    """
    Parse time string to get start and end times
    Examples: 
      '8:30 to 10am' -> ('8:30am', '10:00am')
      '5 to 7:30pm' -> ('5:00pm', '7:30pm')
      '8am to 10am' -> ('8:00am', '10:00am')
    
    Rule: If start time has no am/pm, it inherits from end time
    (e.g., "5 to 7:30pm" means both are PM, not 5am to 7:30pm)
    
    Returns (None, None) for all-day events
    """
    if is_all_day_event(time_str):
        return None, None
    
    # Match patterns like "8:30 to 10am", "5pm to 7pm", "8 to 10am", "5 to 7:30pm"
    match = re.search(r'(\d{1,2}(?::\d{2})?)\s*(?:am|pm)?\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?)\s*(am|pm)', time_str, re.IGNORECASE)
    
    if not match:
        return None, None
    
    start = match.group(1)
    end = match.group(2)
    end_period = match.group(3).lower()
    
    # Add :00 if no minutes specified
    if ':' not in start:
        start = f"{start}:00"
    if ':' not in end:
        end = f"{end}:00"
    
    # If start time doesn't specify am/pm, it inherits from end time
    # Example: "5 to 7:30pm" means "5pm to 7:30pm"
    start_period = end_period
    
    return f"{start}{start_period}", f"{end}{end_period}"


def combine_datetime(date, time_str):
    """
    Combine date and time into datetime object
    Example: date(2026,1,7) + '8:30am' -> datetime(2026,1,7,8,30)
    """
    if not date or not time_str:
        return None
    
    # Parse time like "8:30am" or "5:00pm"
    match = re.match(r'(\d{1,2}):(\d{2})(am|pm)', time_str.lower())
    if not match:
        return None
    
    hour = int(match.group(1))
    minute = int(match.group(2))
    period = match.group(3)
    
    # Convert to 24-hour format
    if period == 'pm' and hour != 12:
        hour += 12
    elif period == 'am' and hour == 12:
        hour = 0
    
    return date.replace(hour=hour, minute=minute, second=0)


def escape_ics(text):
    """Escape special characters for ICS format"""
    if not text:
        return ""
    return text.replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')


def generate_uid(event):
    """Generate unique ID for event"""
    content = f"{event['start_date']}{event['title']}{event.get('organizer', '')}"
    return hashlib.md5(content.encode()).hexdigest() + "@phillybiotech.cal"


def parse_input_file(input_file: Path) -> list:
    """
    Parse input file (CSV or Excel) and return list of events
    
    Args:
        input_file: Path to input file (CSV or Excel)
        
    Returns:
        List of event dictionaries
    """
    file_ext = input_file.suffix.lower()
    
    if file_ext == '.csv':
        return parse_csv(input_file)
    elif file_ext in ['.xlsx', '.xls']:
        if not EXCEL_SUPPORT:
            print("Error: Excel support not available. Install openpyxl:")
            print("  pip install openpyxl")
            sys.exit(1)
        return parse_excel(input_file)
    else:
        print(f"Error: Unsupported file type: {file_ext}")
        print("Supported types: .csv, .xlsx, .xls")
        sys.exit(1)


def parse_csv(csv_file: Path) -> list:
    """Parse CSV file and return list of events"""
    events = []
    
    print(f"Reading CSV file: {csv_file}")
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty rows
            if not row.get('Event Title') and not row.get('event title'):
                continue
            
            # Handle both with and without spaces in column names
            events.append({
                'start_date': row.get('Start Date', row.get('start date', '')).strip().strip('"'),
                'end_date': row.get('End Date', row.get('end date', '')).strip().strip('"'),
                'time': row.get('Time', row.get('time', '')).strip(),
                'title': row.get('Event Title', row.get('event title', '')).strip(),
                'organizer': row.get('Organizer(s)', row.get('organizer(s)', '')).strip(),
                'location': row.get('Location', row.get('location', '')).strip().strip('"'),
                'link': row.get('Link', row.get('link', '')).strip()
            })
    
    return events


def parse_excel(excel_file: Path) -> list:
    """Parse Excel file and return list of events"""
    print(f"Reading Excel file: {excel_file}")
    parser = ExcelParser(excel_file)
    return parser.parse()


def export_to_csv(events: list, csv_file: Path) -> None:
    """
    Export events to CSV file
    
    Args:
        events: List of event dictionaries
        csv_file: Path to output CSV file
    """
    if not events:
        return
    
    # Ensure output directory exists
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['Start Date', 'End Date', 'Time', 'Event Title', 'Organizer(s)', 'Location', 'Link']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for event in events:
            writer.writerow({
                'Start Date': event['start_date'],
                'End Date': event['end_date'],
                'Time': event['time'],
                'Event Title': event['title'],
                'Organizer(s)': event['organizer'],
                'Location': event['location'],
                'Link': event['link']
            })
    
    print(f"Exported CSV: {csv_file}")


def convert_to_ics(input_file, ics_file, timezone='America/New_York', export_csv=True):
    """
    Convert CSV or Excel file to ICS calendar format
    
    Args:
        input_file: Path to input file (CSV or Excel)
        ics_file: Path to output ICS file
        timezone: Timezone for calendar (default: America/New_York)
        export_csv: If True and input is Excel, also export CSV (default: True)
    """
    input_path = Path(input_file)
    
    # Parse input file (CSV or Excel)
    events = parse_input_file(input_path)
    
    # If input is Excel and export_csv is True, also export CSV
    if export_csv and input_path.suffix.lower() in ['.xlsx', '.xls']:
        csv_output = Path(ics_file).parent / 'philly_biotech_events.csv'
        export_to_csv(events, csv_output)
    
    total_events = len(events)
    print(f"Found {total_events} events")
    
    # Filter out past events (keep only current and future events)
    # Use timezone-aware datetime to match the calendar timezone
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    future_events = []
    
    for event in events:
        start_date = parse_date(event['start_date'])
        if not start_date:
            continue
        
        # Try to get the time component
        start_time, _ = parse_time(event['time'])
        
        if start_time:
            # Event has a specific time - compare full datetime
            start_datetime = combine_datetime(start_date, start_time)
            if start_datetime:
                # Make timezone-aware for comparison
                start_datetime = start_datetime.replace(tzinfo=tz)
                if start_datetime >= now:
                    future_events.append(event)
        else:
            # All-day event - compare just the date
            if start_date.date() >= now.date():
                future_events.append(event)
    
    events = future_events
    removed_count = total_events - len(events)
    print(f"Removed {removed_count} past events (before {now.strftime('%Y-%m-%d %H:%M:%S %Z')})")
    print(f"Keeping {len(events)} current/future events")
    
    # Sort events by date and time
    def sort_key(event):
        """Generate sort key for event (date + time)"""
        start_date = parse_date(event['start_date'])
        if not start_date:
            return datetime(1900, 1, 1)  # Put invalid dates at the beginning
        
        # Try to get time component
        start_time, _ = parse_time(event['time'])
        if start_time:
            full_datetime = combine_datetime(start_date, start_time)
            if full_datetime:
                return full_datetime
        
        # If no time, use start of day
        return start_date
    
    events.sort(key=sort_key)
    print(f"Sorted events chronologically")
    
    # Build ICS file
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Philly Biotech Calendar//EN",
        "X-WR-CALNAME:Philadelphia Life Sciences 2026",
        f"X-WR-TIMEZONE:{timezone}",
        "CALSCALE:GREGORIAN"
    ]
    
    # Add each event
    for event in events:
        # Parse dates (Start Date and End Date are always just dates)
        start_date = parse_date(event['start_date'])
        end_date = parse_date(event['end_date']) or start_date
        
        if not start_date:
            continue
        
        # Parse time (Time field has 3 cases: start/end times, "All Day", or "TBD")
        start_time, end_time = parse_time(event['time'])
        
        # Build VEVENT
        ics_lines.append("BEGIN:VEVENT")
        ics_lines.append(f"UID:{generate_uid(event)}")
        ics_lines.append(f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
        
        # Add date/time - two cases:
        if start_time and end_time:
            # Case 1: Event has specific start and end times
            dtstart = combine_datetime(start_date, start_time)
            dtend = combine_datetime(end_date, end_time)
            if dtstart and dtend:
                ics_lines.append(f"DTSTART;TZID={timezone}:{dtstart.strftime('%Y%m%dT%H%M%S')}")
                ics_lines.append(f"DTEND;TZID={timezone}:{dtend.strftime('%Y%m%dT%H%M%S')}")
        else:
            # Case 2: All-day event (includes "All Day", "TBD", "To be released")
            ics_lines.append(f"DTSTART;VALUE=DATE:{start_date.strftime('%Y%m%d')}")
            ics_lines.append(f"DTEND;VALUE=DATE:{end_date.strftime('%Y%m%d')}")
        
        ics_lines.append(f"SUMMARY:{escape_ics(event['title'])}")
        
        # Build description (notes/details) - only include organizer
        if event['organizer']:
            ics_lines.append(f"DESCRIPTION:Organizer: {escape_ics(event['organizer'])}")
        
        if event['location']:
            ics_lines.append(f"LOCATION:{escape_ics(event['location'])}")
        
        # Add URL field if we have a valid link
        if event['link'] and event['link'].lower() not in ['link', 'invite only', 'to be released', '']:
            link = event['link'].strip()
            # Only add if it's an actual URL (not just placeholder text)
            if link.startswith('http://') or link.startswith('https://'):
                ics_lines.append(f"URL:{link}")
        
        ics_lines.append("STATUS:CONFIRMED")
        ics_lines.append("END:VEVENT")
    
    ics_lines.append("END:VCALENDAR")
    
    # Write ICS file
    print(f"Writing {ics_file}...")
    
    # Create output directory if it doesn't exist
    Path(ics_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(ics_file, 'w', encoding='utf-8') as f:
        f.write('\r\n'.join(ics_lines) + '\r\n')
    
    print(f"✓ Done! Created calendar with {len(events)} events")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert CSV/Excel to ICS calendar format')
    parser.add_argument('input_file', nargs='?', 
                       default='data/2026_philly_lifescience_calendar.csv',
                       help='Input file (CSV or Excel)')
    parser.add_argument('output_file', nargs='?',
                       default='output/philly_biotech_calendar.ics',
                       help='Output ICS file')
    parser.add_argument('--timezone', default='America/New_York',
                       help='Timezone (default: America/New_York)')
    
    args = parser.parse_args()
    
    convert_to_ics(
        input_file=args.input_file,
        ics_file=args.output_file,
        timezone=args.timezone
    )
