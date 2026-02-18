#!/usr/bin/env python3
import urllib.request
import re
from datetime import datetime, timedelta, timezone

# Fetch the iCal feed
url = "https://calendar.google.com/calendar/ical/on9f1k6ou2052pvqhlahg0ogus%40group.calendar.google.com/private-07bf7877165feaafb70535ddc92886c6/basic.ics"

with urllib.request.urlopen(url) as response:
    ical_data = response.read().decode('utf-8')

# Current time: Wednesday, February 18th, 2026 — 10:04 AM (America/Los_Angeles)
# Pacific timezone is UTC-8 in February (PST)
PST_OFFSET = timedelta(hours=-8)
pacific = timezone(PST_OFFSET)
now = datetime(2026, 2, 18, 10, 4, tzinfo=pacific)
window_end = now + timedelta(hours=4)

print(f"Current time: {now}")
print(f"Window end: {window_end}")
print("="*60)

# Parse VEVENT blocks
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
        event['location'] = location_match.group(1).replace('\\n', '\n').replace('\\,', ',').strip()
    
    # Check for RRULE (recurring)
    rrule_match = re.search(r'RRULE:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
    if rrule_match:
        event['rrule'] = rrule_match.group(1).strip()
    
    # Get DTSTART
    dtstart_match = re.search(r'DTSTART(?:;[^:]*)?:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
    if dtstart_match:
        dtstart_str = dtstart_match.group(1).strip()
        event['dtstart'] = dtstart_str
        
        # Parse the start time
        try:
            if 'T' in dtstart_str and len(dtstart_str) >= 15:
                # Has time component
                if dtstart_str.endswith('Z'):
                    # UTC time - convert to Pacific
                    dt = datetime.strptime(dtstart_str, '%Y%m%dT%H%M%SZ')
                    dt = dt.replace(tzinfo=timezone.utc).astimezone(pacific)
                else:
                    # Local time (assume Pacific)
                    dt = datetime.strptime(dtstart_str[:15], '%Y%m%dT%H%M%S')
                    dt = dt.replace(tzinfo=pacific)
                event['start_datetime'] = dt
            else:
                # All-day event (date only)
                dt = datetime.strptime(dtstart_str, '%Y%m%d')
                event['start_datetime'] = dt.replace(tzinfo=pacific)
        except Exception as e:
            event['parse_error'] = str(e)
    
    # Check for RECURRENCE-ID (modified instance)
    rec_id_match = re.search(r'RECURRENCE-ID(?:;[^:]*)?:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
    if rec_id_match:
        event['recurrence_id'] = rec_id_match.group(1).strip()
    
    events.append(event)

# Find events in the window
print("\nAll events with locations:")
for e in events:
    if e.get('location'):
        print(f"  - {e.get('summary', 'N/A')} at {e.get('start_datetime', 'N/A')}")
        print(f"    Location: {e.get('location', 'N/A')[:60]}...")
        if e.get('rrule'):
            print(f"    RRULE: {e.get('rrule')}")

print("\n" + "="*60)
print("Checking for recurring Wednesday events...")

# Look for Wednesday recurring events
wednesday_events = []
for e in events:
    if e.get('rrule') and 'BYDAY' in e.get('rrule', ''):
        rrule = e['rrule']
        # Check if it's a Wednesday event (WE)
        if 'WE' in rrule:
            if e.get('start_datetime'):
                # Calculate if there's an instance today
                start_dt = e['start_datetime']
                
                # Get the time of day from the original event
                event_time = start_dt.time()
                
                # Create datetime for today with that time
                today_event = datetime.combine(now.date(), event_time).replace(tzinfo=pacific)
                
                # Check if it's within our window
                if now <= today_event <= window_end:
                    wednesday_events.append({
                        'summary': e.get('summary', 'Unknown'),
                        'location': e.get('location', ''),
                        'start': today_event,
                        'original': e
                    })

print(f"\nFound {len(wednesday_events)} Wednesday events in window:")
for we in wednesday_events:
    print(f"  - {we['summary']} at {we['start']}")
    print(f"    Location: {we['location']}")
