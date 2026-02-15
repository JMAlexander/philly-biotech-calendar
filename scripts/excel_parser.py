"""
Excel Parser Module
Handles parsing of Excel event files with multiple sheets
"""

import openpyxl
from datetime import datetime
from typing import List, Dict
from pathlib import Path


class ExcelParser:
    """Parse Excel event files and extract structured event data"""
    
    def __init__(self, excel_path: Path):
        """
        Initialize the Excel parser
        
        Args:
            excel_path: Path to the Excel file
        """
        self.excel_path = excel_path
        
    def parse(self) -> List[Dict[str, str]]:
        """
        Parse the Excel file and return a list of event dictionaries
        
        Returns:
            List of event dictionaries with keys: start_date, end_date, time,
            title, organizer, location, link
        """
        events = []
        
        wb = openpyxl.load_workbook(self.excel_path)
        
        # Get all month sheets (e.g., Jan.26, Feb.26, etc.)
        month_sheets = [name for name in wb.sheetnames if name.endswith('.26')]
        
        print(f"Found {len(month_sheets)} month sheets: {', '.join(month_sheets)}")
        
        for sheet_name in month_sheets:
            ws = wb[sheet_name]
            sheet_events = self._parse_sheet(ws, sheet_name)
            events.extend(sheet_events)
            print(f"  - {sheet_name}: {len(sheet_events)} events")
        
        return events
    
    def _parse_sheet(self, ws, sheet_name: str) -> List[Dict[str, str]]:
        """
        Parse a single worksheet
        
        Args:
            ws: openpyxl worksheet object
            sheet_name: Name of the sheet (for logging)
            
        Returns:
            List of event dictionaries from this sheet
        """
        events = []
        
        # Row 1 is merged header (skip)
        # Row 2 is column headers
        # Row 3+ are data
        
        rows = list(ws.rows)
        if len(rows) < 3:
            return events
        
        # Get header row (row 2, index 1)
        headers = [cell.value for cell in rows[1]]
        
        # Find column indices (column B=1, C=2, etc.)
        # Columns: B=Start Date, C=End Date, D=Time, E=Event Title, 
        #          F=Organizer(s), G=Location, H=Link
        start_date_col = 1  # B
        end_date_col = 2    # C
        time_col = 3        # D
        title_col = 4       # E
        organizer_col = 5   # F
        location_col = 6    # G
        link_col = 7        # H
        
        # Parse data rows (starting from row 3, index 2)
        for row in rows[2:]:
            # Get values (skip column A)
            start_date = row[start_date_col].value
            end_date = row[end_date_col].value
            time = row[time_col].value
            title = row[title_col].value
            organizer = row[organizer_col].value
            location = row[location_col].value
            
            # Extract hyperlink URL if present, otherwise use cell value
            link_cell = row[link_col]
            if link_cell.hyperlink and link_cell.hyperlink.target:
                link = link_cell.hyperlink.target
            else:
                link = link_cell.value
            
            # Skip empty rows
            if not title or title is None:
                continue
            
            # Convert datetime objects to string format
            if isinstance(start_date, datetime):
                start_date = start_date.strftime("%a, %b %d, %Y")
            if isinstance(end_date, datetime):
                end_date = end_date.strftime("%a, %b %d, %Y")
            
            # Clean string fields
            event = {
                'start_date': self._clean_field(start_date),
                'end_date': self._clean_field(end_date),
                'time': self._clean_field(time),
                'title': self._clean_field(title),
                'organizer': self._clean_field(organizer),
                'location': self._clean_field(location),
                'link': self._clean_field(link)
            }
            
            # Only add if we have required fields
            if event['start_date'] and event['title']:
                events.append(event)
        
        return events
    
    @staticmethod
    def _clean_field(field) -> str:
        """
        Clean a field by removing extra whitespace
        
        Args:
            field: Raw field value
            
        Returns:
            Cleaned field string
        """
        if field is None:
            return ""
        
        # Convert to string if not already
        field = str(field)
        
        # Remove newlines and extra whitespace
        field = ' '.join(field.split())
        
        return field.strip()
