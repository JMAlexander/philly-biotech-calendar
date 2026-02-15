# Philadelphia Life Sciences 2026 Event Calendar

A simple system to convert CSV event data to ICS calendar format and host it on a webpage with automatic updates.

## Features

- ✅ **CSV to ICS conversion** - Generates standard iCalendar format
- ✅ **Automatic past event filtering** - Only shows current/future events
- ✅ **Timezone-aware** - Properly handles America/New_York timezone
- ✅ **Web interface** - Beautiful calendar display with search/filter
- ✅ **Calendar subscriptions** - One-click subscribe for Apple, Google, Outlook
- ✅ **Automatic updates** - Script to regenerate and deploy calendar
- ✅ **Backup system** - Creates backups before overwriting

## Project Structure

```
philly_biotech_cal/
├── config/
│   └── config.ini              # Configuration settings
├── scripts/
│   ├── convert_calendar.py     # CSV to ICS converter
│   └── update_calendar.py      # Update and deploy script
├── data/
│   └── 2026_philly_lifescience_calendar.csv
├── output/
│   └── philly_biotech_calendar.ics
├── logs/
│   └── update.log              # Update activity log
├── index.html                  # Calendar webpage
├── README.md                   # This file
└── SETUP_CRON.md              # Cron setup instructions
```

## Quick Start

### 1. Configure

Edit `config/config.ini` to set your paths and timezone:

```ini
[Paths]
csv_file = data/2026_philly_lifescience_calendar.csv
output_file = output/philly_biotech_calendar.ics
web_destination = /path/to/your/website/philly_biotech_calendar.ics

[Calendar]
timezone = America/New_York

[Options]
create_backup = yes
```

### 2. Generate Calendar

Run the conversion script:

```bash
python3 scripts/convert_calendar.py
```

This will:
- Read the CSV file
- Filter out past events (timezone-aware)
- Generate ICS file in `output/`
- Show how many events were processed

### 3. Deploy to Website

Run the update script:

```bash
python3 scripts/update_calendar.py
```

This will:
- Run the converter
- Create a backup of the existing calendar
- Copy the new calendar to your web directory
- Log all activity to `logs/update.log`

## How It Works

### CSV to ICS Conversion

The `convert_calendar.py` script:

1. **Reads CSV** - Parses event data from CSV file
2. **Filters events** - Removes events that have already passed (compares full datetime with timezone)
3. **Parses dates/times** - Handles various formats:
   - All-day events: "All Day", "TBD", "To be released"
   - Timed events: "8:30 to 10am", "5 to 7:30pm"
   - Time inheritance: "5 to 7pm" means "5pm to 7pm" (not 5am)
4. **Generates ICS** - Creates standard iCalendar format file
5. **Sorts chronologically** - Events ordered by date and time

### Update and Deploy

The `update_calendar.py` script:

1. **Runs converter** - Generates fresh ICS file
2. **Creates backup** - Saves previous version (if exists)
3. **Copies to web** - Deploys to configured web directory
4. **Logs activity** - Records all actions with timestamps

### Web Interface

The `index.html` page provides:

- **Event display** - Clean card layout with date badges
- **Search & filter** - Search by keyword, filter by month
- **Statistics** - Total events, upcoming events, organizers
- **Subscribe buttons** - One-click for Apple, Google, Outlook
- **Responsive design** - Works on desktop and mobile

## Configuration

### config/config.ini

```ini
[Paths]
# Input CSV file (relative to project root)
csv_file = data/2026_philly_lifescience_calendar.csv

# Output ICS file (relative to project root)
output_file = output/philly_biotech_calendar.ics

# Where to copy for web hosting (absolute path)
web_destination = /var/www/your-site/path/to/calendar.ics

[Calendar]
# Calendar name in ICS file
name = Philadelphia Life Sciences 2026

# Calendar description
description = Life sciences events in Philadelphia

# Timezone for dates and filtering
timezone = America/New_York

[Options]
# Create backup before overwriting (yes/no)
create_backup = yes

# Log file location (relative to project root)
log_file = logs/update.log
```

## Automated Updates

### Option 1: Cron (Recommended)

Run the update script automatically on a schedule:

```bash
# Edit crontab
crontab -e

# Update every hour
0 * * * * cd /path/to/philly_biotech_cal && /usr/bin/python3 scripts/update_calendar.py

# Or update twice daily (6am and 6pm)
0 6,18 * * * cd /path/to/philly_biotech_cal && /usr/bin/python3 scripts/update_calendar.py
```

### Option 2: Manual Update

Run whenever you update the CSV:

```bash
cd /path/to/philly_biotech_cal
python3 scripts/update_calendar.py
```

### Viewing Logs

Check what happened during updates:

```bash
# View all logs
cat logs/update.log

# View recent logs
tail -20 logs/update.log

# Watch logs in real-time
tail -f logs/update.log
```

## CSV Format

The CSV should have these columns:

| Column | Example | Notes |
|--------|---------|-------|
| Start Date | "Wed, Jan 7, 2026" | Required |
| End Date | "Wed, Jan 7, 2026" | Can be same as start |
| Time | "8:30 to 10am" or "All Day" | See time formats below |
| Event Title | "January Open House" | Required |
| Organizer(s) | "Pennovation" | Optional |
| Location | "Philadelphia, PA" | Optional |
| Link | "https://..." | Optional |

### Time Format Rules

1. **All-day events**: Use "All Day", "TBD", or "To be released"
2. **Timed events**: Use format like "8:30 to 10am" or "5 to 7:30pm"
3. **Time inheritance**: If start time has no am/pm, it inherits from end
   - "5 to 7:30pm" = "5pm to 7:30pm" (not 5am)
   - "8 to 10am" = "8am to 10am"

## Calendar Subscriptions

The webpage provides buttons to subscribe in:

- **Apple Calendar** - Uses `webcal://` protocol
- **Google Calendar** - Opens Google's subscription page
- **Outlook** - Opens Outlook's subscription page
- **Download** - Direct ICS file download

Users who subscribe will automatically see updates when you regenerate the calendar.

## Troubleshooting

### Calendar not updating on website

1. Check that `web_destination` path is correct in `config/config.ini`
2. Verify you have write permissions to the web directory
3. Check `logs/update.log` for errors

### Events not being filtered correctly

1. Verify `timezone` is set correctly in `config/config.ini`
2. Check that dates in CSV are in format "Day, Mon DD, YYYY"
3. Run `python3 scripts/convert_calendar.py` to see filtering output

### Time parsing issues

1. Verify time format follows examples: "8:30 to 10am", "5 to 7pm"
2. Remember: "5 to 7pm" means "5pm to 7pm" (inherits period)
3. For all-day events, use "All Day", "TBD", or "To be released"

### Permission errors

If you get permission denied when copying to web directory:

```bash
# Option 1: Change ownership
sudo chown $USER:$USER /path/to/web/directory

# Option 2: Run with sudo (not recommended for cron)
sudo python3 scripts/update_calendar.py
```

## Development

### Testing Changes

1. Modify the CSV file
2. Run converter: `python3 scripts/convert_calendar.py`
3. Check output: `cat output/philly_biotech_calendar.ics`
4. Deploy: `python3 scripts/update_calendar.py`

### Customizing the Calendar

- **Change timezone**: Edit `timezone` in `config/config.ini`
- **Change calendar name**: Edit `name` in `config/config.ini`
- **Modify web design**: Edit `index.html` (uses PhillyGenome theme)
- **Adjust filtering**: Edit `convert_calendar.py` around line 120

## Maintenance

### Backup and Recovery

Backups are automatically created in the web directory as `*_backup.ics`.

To restore from backup:

```bash
cp /path/to/web/directory/philly_biotech_calendar_backup.ics \
   /path/to/web/directory/philly_biotech_calendar.ics
```

### Log Rotation

The log file will grow over time. Rotate it periodically:

```bash
# Archive old logs
mv logs/update.log logs/update.log.$(date +%Y%m%d)

# Or clear logs
> logs/update.log
```

## License

Open source - use and modify as needed.

## Support

For issues or questions, check:
1. `logs/update.log` for error messages
2. `SETUP_CRON.md` for detailed cron setup
3. Configuration in `config/config.ini`
