#!/usr/bin/env python3
"""
Simple Calendar Update Script
Reads config, converts CSV to ICS, and copies to web directory
"""

import configparser
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys


def log_message(message, log_file=None, timezone='America/New_York'):
    """Print and optionally log a message"""
    tz = ZoneInfo(timezone)
    timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(full_message + '\n')


def main():
    # Get script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_file = project_root / 'config' / 'config.ini'
    
    # Read config
    if not config_file.exists():
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # Get settings (paths relative to project root)
    input_file = project_root / config['Paths']['input_file']
    output_file = project_root / config['Paths']['output_file']
    web_destination = Path(config['Paths']['web_destination'])
    timezone = config['Calendar']['timezone']
    create_backup = config['Options']['create_backup'].lower() == 'yes'
    log_file = project_root / config['Options']['log_file']
    
    log_message("=" * 60, log_file, timezone)
    log_message(f"Starting calendar update (timezone: {timezone})", log_file, timezone)
    
    # Step 1: Check if input file exists
    if not input_file.exists():
        log_message(f"Error: Input file not found: {input_file}", log_file, timezone)
        sys.exit(1)
    
    log_message(f"Found input file: {input_file}", log_file, timezone)
    
    # Step 2: Run convert_calendar.py
    log_message("Running conversion...", log_file, timezone)
    
    # Use the same Python interpreter that's running this script
    python_exe = sys.executable
    
    try:
        result = subprocess.run(
            [python_exe, str(script_dir / 'convert_calendar.py'), str(input_file), str(output_file)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            log_message(f"Error running converter: {result.stderr}", log_file, timezone)
            sys.exit(1)
        
        log_message("Conversion completed successfully", log_file, timezone)
        
    except Exception as e:
        log_message(f"Error running converter: {e}", log_file, timezone)
        sys.exit(1)
    
    # Step 3: Check if output file was created
    if not output_file.exists():
        log_message(f"Error: Output file not created: {output_file}", log_file, timezone)
        sys.exit(1)
    
    # Step 4: Create backup if requested
    if create_backup and web_destination.exists():
        backup_file = web_destination.parent / f"{web_destination.stem}_backup{web_destination.suffix}"
        shutil.copy2(web_destination, backup_file)
        log_message(f"Created backup: {backup_file}", log_file, timezone)
    
    # Step 5: Copy to web destination
    try:
        # Ensure destination directory exists
        web_destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(output_file, web_destination)
        log_message(f"Copied to: {web_destination}", log_file, timezone)
        
    except Exception as e:
        log_message(f"Error copying to web destination: {e}", log_file, timezone)
        sys.exit(1)
    
    # Done
    log_message("✓ Calendar update completed successfully", log_file, timezone)
    log_message("=" * 60, log_file, timezone)


if __name__ == "__main__":
    main()
