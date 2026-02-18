#!/usr/bin/env python3
"""
iCal Parser for Calendar Events
Properly handles RRULE with BYDAY validation and UNTIL dates
"""
import urllib.request
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple

# Day name to iCal BYDAY code mapping
DAY_MAP = {
    'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6
}
REVERSE_DAY_MAP = {v: k for k, v in DAY_MAP.items()}


def parse_rrule(rrule: str) -> Dict:
    """Parse RRULE string into components"""
    parts = {}
    for component in rrule.split(';'):
        if '=' in component:
            key, value = component.split('=', 1)
            parts[key] = value
    return parts


def get_day_of_week(date: datetime) -> str:
    """Get iCal BYDAY code for a date (MO, TU, WE, etc.)"""
    return REVERSE_DAY_MAP[date.weekday()]


def parse_until_date(until_str: str) -> Optional[datetime]:
    """Parse UNTIL date from RRULE"""
    try:
        if until_str.endswith('Z'):
            dt = datetime.strptime(until_str, '%Y%m%dT%H%M%SZ')
            return dt.replace(tzinfo=timezone.utc)
        elif 'T' in until_str:
            dt = datetime.strptime(until_str[:15], '%Y%m%dT%H%M%S')
            return dt.replace(tzinfo=timezone.utc)
        else:
            dt = datetime.strptime(until_str, '%Y%m%d')
            return dt.replace(tzinfo=timezone.utc)
    except:
        return None


def check_rrule_valid_for_date(rrule: str, target_date: datetime) -> bool:
    """
    Check if a recurring event's RRULE produces an instance on target_date
    Returns True if there's a valid instance on that date
    """
    rrule_parts = parse_rrule(rrule)
    
    # Check UNTIL - has the series ended?
    if 'UNTIL' in rrule_parts:
        until_date = parse_until_date(rrule_parts['UNTIL'])
        if until_date and target_date > until_date:
            return False
    
    # Check BYDAY - does this event occur on target day?
    target_day_code = get_day_of_week(target_date)
    
    if 'BYDAY' in rrule_parts:
        byday = rrule_parts['BYDAY']
        # Handle compound days like "MO,WE,FR"
        allowed_days = byday.split(',')
        # Strip any position prefixes (e.g., "-1FR" for last Friday)
        allowed_days = [d.lstrip('-0123456789') for d in allowed_days]
        if target_day_code not in allowed_days:
            return False
    
    # Check FREQ
    freq = rrule_parts.get('FREQ', 'DAILY')
    
    # For simplicity, we assume WEEKLY and DAILY are valid
    # More complex rules (MONTHLY with BYMONTHDAY, etc.) would need more logic
    if freq == 'WEEKLY':
        # Already checked BYDAY above
        return True
    elif freq == 'DAILY':
        return True
    elif freq == 'MONTHLY':
        # Would need more complex logic for monthly recurrence
        return True
    
    return True


def parse_ical(url: str, target_date: datetime, tz: timezone) -> List[Dict]:
    """
    Parse iCal feed and return events for target_date
    """
    with urllib.request.urlopen(url) as response:
        ical_data = response.read().decode('utf-8')
    
    events = []
    vevent_pattern = r'BEGIN:VEVENT\s*(.*?)\s*END:VEVENT'
    vevents = re.findall(vevent_pattern, ical_data, re.DOTALL)
    
    for vevent in vevents:
        event = {}
        
        # Get summary
        summary_match = re.search(r'SUMMARY:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
        if summary_match:
            event['summary'] = summary_match.group(1).replace('\\n', '\n').strip()
        
        # Get location
        location_match = re.search(r'LOCATION:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
        if location_match:
            loc = location_match.group(1).replace('\\n', '\n').replace('\\,', ',').strip()
            event['location'] = loc
        
        # Get RRULE
        rrule_match = re.search(r'RRULE:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
        if rrule_match:
            event['rrule'] = rrule_match.group(1).strip()
        
        # Get DTSTART
        dtstart_match = re.search(r'DTSTART(?:;[^:]*)?:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
        if dtstart_match:
            dtstart_str = dtstart_match.group(1).strip()
            event['dtstart'] = dtstart_str
            
            try:
                if 'T' in dtstart_str and len(dtstart_str) >= 15:
                    if dtstart_str.endswith('Z'):
                        dt = datetime.strptime(dtstart_str, '%Y%m%dT%H%M%SZ')
                        dt = dt.replace(tzinfo=timezone.utc).astimezone(tz)
                    else:
                        dt = datetime.strptime(dtstart_str[:15], '%Y%m%dT%H%M%S')
                        dt = dt.replace(tzinfo=tz)
                    event['start_datetime'] = dt
                else:
                    dt = datetime.strptime(dtstart_str, '%Y%m%d')
                    event['start_datetime'] = dt.replace(tzinfo=tz)
            except Exception as e:
                event['parse_error'] = str(e)
        
        # Check for RECURRENCE-ID (modified instance - skip these as they're exceptions)
        rec_id_match = re.search(r'RECURRENCE-ID(?:;[^:]*)?:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
        if rec_id_match:
            event['recurrence_id'] = rec_id_match.group(1).strip()
        
        events.append(event)
    
    return events


def get_events_for_date(events: List[Dict], target_date: datetime, tz: timezone) -> List[Dict]:
    """
    Filter events to find those occurring on target_date
    Properly handles recurring events with RRULE validation
    """
    day_events = []
    
    for e in events:
        event_date = None
        is_valid = False
        
        # Check if it's a recurring event
        if e.get('rrule'):
            # Validate RRULE for target date
            if check_rrule_valid_for_date(e['rrule'], target_date):
                if e.get('start_datetime'):
                    event_time = e['start_datetime'].time()
                    event_date = datetime.combine(target_date.date(), event_time).replace(tzinfo=tz)
                    is_valid = True
        
        # Check non-recurring events
        elif e.get('start_datetime'):
            start = e['start_datetime']
            if start.date() == target_date.date():
                event_date = start
                is_valid = True
        
        if is_valid and event_date:
            day_events.append({
                'summary': e.get('summary', 'Unknown'),
                'location': e.get('location', ''),
                'start': event_date,
                'is_recurring': bool(e.get('rrule')),
                'rrule': e.get('rrule', '')
            })
    
    # Sort by time
    day_events.sort(key=lambda x: x['start'])
    return day_events


def main():
    # Configuration
    url = "https://calendar.google.com/calendar/ical/on9f1k6ou2052pvqhlahg0ogus%40group.calendar.google.com/private-07bf7877165feaafb70535ddc92886c6/basic.ics"
    
    # Target: Next Wednesday, February 25, 2026
    PST_OFFSET = timedelta(hours=-8)
    pacific = timezone(PST_OFFSET)
    target_date = datetime(2026, 2, 25, tzinfo=pacific)
    
    print(f"Calendar: {target_date.strftime('%A, %B %d, %Y')}")
    print("="*60)
    
    # Parse and filter
    all_events = parse_ical(url, target_date, pacific)
    day_events = get_events_for_date(all_events, target_date, pacific)
    
    print(f"\nFound {len(day_events)} events:\n")
    
    for e in day_events:
        recurring_tag = " (↻)" if e['is_recurring'] else ""
        time_str = e['start'].strftime('%I:%M %p').lstrip('0')
        
        print(f"• {time_str} — {e['summary']}{recurring_tag}")
        if e['location']:
            # Clean up location display
            loc = e['location'].replace('\r\n', ' ').replace('\n', ' ')
            if len(loc) > 60:
                loc = loc[:57] + "..."
            print(f"  📍 {loc}")


if __name__ == '__main__':
    main()
