#!/usr/bin/env python3
import urllib.request
import re
from datetime import datetime, timedelta, timezone

# Fetch the iCal feed
url = "https://calendar.google.com/calendar/ical/on9f1k6ou2052pvqhlahg0ogus%40group.calendar.google.com/private-07bf7877165feaafb70535ddc92886c6/basic.ics"

with urllib.request.urlopen(url) as response:
    ical_data = response.read().decode('utf-8')

# Current time: Wednesday, February 18th, 2026 — 10:34 AM (America/Los_Angeles)
# Pacific timezone is UTC-8 in February (PST)
PST_OFFSET = timedelta(hours=-8)
pacific = timezone(PST_OFFSET)
now = datetime(2026, 2, 18, 10, 34, tzinfo=pacific)
window_end = now + timedelta(hours=4)

print(f"Current time: {now}")
print(f"Window end: {window_end}")
print(f"Today is: {now.strftime('%A, %B %d, %Y')}")
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
    
    events.append(event)

# Find events in the window
print("\nLooking for events between now and window end...")
print()

# Track events to alert on
alerts_needed = []

# Look for Wednesday recurring events (today is Wednesday)
for e in events:
    if not e.get('rrule'):
        continue
        
    rrule = e['rrule']
    
    # Check if it's a Wednesday event
    if 'BYDAY=WE' in rrule or 'BYDAY=1WE' in rrule or 'BYDAY=2WE' in rrule or 'BYDAY=3WE' in rrule:
        if e.get('start_datetime'):
            start_dt = e['start_datetime']
            
            # Get the time of day from the original event
            event_time = start_dt.time()
            
            # Create datetime for TODAY (Feb 18, 2026) with that time
            today_event = datetime.combine(now.date(), event_time).replace(tzinfo=pacific)
            
            # Check if it's within our window (next 4 hours)
            if now <= today_event <= window_end:
                # Check if there's a location
                if e.get('location') and e['location'].strip():
                    # Check for NO CLASS markers
                    summary = e.get('summary', '').upper()
                    if 'NO CLASS' not in summary and 'CANCELLED' not in summary and 'CANCELED' not in summary:
                        alerts_needed.append({
                            'summary': e.get('summary', 'Unknown'),
                            'location': e.get('location', ''),
                            'start': today_event
                        })

# Print results
if alerts_needed:
    print(f"Found {len(alerts_needed)} events with locations in the 4-hour window:")
    for evt in alerts_needed:
        print(f"\n• {evt['summary']}")
        print(f"  Start: {evt['start'].strftime('%I:%M %p')}")
        print(f"  Location: {evt['location'][:60]}...")
        
        # Calculate if alert should be sent
        # For local SF events, assume 15 min drive + 15 min buffer = need to leave 30 min before
        drive_time_minutes = 15  # Estimate for local SF
        leave_by = evt['start'] - timedelta(minutes=drive_time_minutes + 15)
        minutes_until_leave = (leave_by - now).total_seconds() / 60
        
        print(f"  Leave by: {leave_by.strftime('%I:%M %p')} ({minutes_until_leave:.0f} min from now)")
        
        if 0 <= minutes_until_leave <= 60:
            print(f"  ⚠️  ALERT NEEDED: Leave within {minutes_until_leave:.0f} minutes!")
        elif minutes_until_leave < 0:
            print(f"  🚨 OVERDUE: Should have left {abs(minutes_until_leave):.0f} minutes ago!")
else:
    print("No events with locations found in the 4-hour window.")

print("\n" + "="*60)
print("ALERT SUMMARY:")
for evt in alerts_needed:
    drive_time_minutes = 15
    leave_by = evt['start'] - timedelta(minutes=drive_time_minutes + 15)
    minutes_until_leave = (leave_by - now).total_seconds() / 60
    
    if minutes_until_leave <= 60:
        print(f"\n{evt['summary']}")
        print(f"  Start: {evt['start'].strftime('%I:%M %p')}")
        print(f"  Location: {evt['location']}")
        print(f"  Drive: ~{drive_time_minutes} min")
        print(f"  LEAVE BY: {leave_by.strftime('%I:%M %p')}")
