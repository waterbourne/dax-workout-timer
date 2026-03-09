#!/usr/bin/env python3
import urllib.request
import re
from datetime import datetime, timedelta, timezone

# Fetch the iCal feed
url = "https://calendar.google.com/calendar/ical/on9f1k6ou2052pvqhlahg0ogus%40group.calendar.google.com/private-07bf7877165feaafb70535ddc92886c6/basic.ics"

with urllib.request.urlopen(url) as response:
    ical_data = response.read().decode('utf-8')

# Get current time in Pacific timezone
PDT_OFFSET = timedelta(hours=-7)
pacific = timezone(PDT_OFFSET)
now = datetime.now(pacific)
window_end = now + timedelta(hours=4)
today_weekday = now.weekday()
weekday_names = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
today_code = weekday_names[today_weekday]

print(f"Current time: {now}")
print(f"Today: {now.strftime('%A, %B %d, %Y')}")
print(f"Looking ahead to: {window_end.strftime('%I:%M %p')}")
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
        rrule = rrule_match.group(1).strip()
        event['rrule'] = rrule
        
        # Parse UNTIL date from RRULE
        until_match = re.search(r'UNTIL=(\d{8})', rrule)
        if until_match:
            until_str = until_match.group(1)
            try:
                event['until'] = datetime.strptime(until_str, '%Y%m%d').replace(tzinfo=pacific)
            except:
                pass
    
    # Check for EXDATE (exclusions)
    exdate_match = re.search(r'EXDATE(?:;[^:]*)?:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
    if exdate_match:
        event['exdate'] = exdate_match.group(1).strip()
    
    # Get DTSTART
    dtstart_match = re.search(r'DTSTART(?:;[^:]*)?:(.*?)(?:\r?\n[\w-]+:|\r?\nEND:)', vevent, re.DOTALL)
    if dtstart_match:
        dtstart_str = dtstart_match.group(1).strip()
        event['dtstart'] = dtstart_str
        
        # Parse the start time
        try:
            if 'T' in dtstart_str and len(dtstart_str) >= 15:
                if dtstart_str.endswith('Z'):
                    dt = datetime.strptime(dtstart_str, '%Y%m%dT%H%M%SZ')
                    dt = dt.replace(tzinfo=timezone.utc).astimezone(pacific)
                else:
                    dt = datetime.strptime(dtstart_str[:15], '%Y%m%dT%H%M%S')
                    dt = dt.replace(tzinfo=pacific)
                event['start_datetime'] = dt
            else:
                dt = datetime.strptime(dtstart_str, '%Y%m%d')
                event['start_datetime'] = dt.replace(tzinfo=pacific)
        except Exception as e:
            event['parse_error'] = str(e)
    
    events.append(event)

# Find events happening TODAY that require leaving soon
alerts_needed = []

for e in events:
    if not e.get('location') or not e.get('start_datetime'):
        continue
    
    # Skip cancelled/no class events
    summary = e.get('summary', '').upper()
    if 'NO CLASS' in summary or 'CANCELLED' in summary or 'CANCELED' in summary:
        continue
    
    start_dt = e['start_datetime']
    event_time = start_dt.time()
    
    # Check if this is a recurring event
    if e.get('rrule'):
        rrule = e['rrule']
        
        # Check UNTIL - skip if recurrence has ended
        if e.get('until') and e['until'].date() < now.date():
            continue  # Recurrence ended before today
        
        # Parse BYDAY from RRULE
        byday_match = re.search(r'BYDAY=([^;]+)', rrule)
        if byday_match:
            byday_str = byday_match.group(1)
            valid_days = []
            for day_code in weekday_names:
                if day_code in byday_str:
                    valid_days.append(day_code)
            
            # Only include if today matches one of the valid days
            if today_code not in valid_days:
                continue
        else:
            # No BYDAY specified - use the day of week from DTSTART
            dtstart_weekday = start_dt.weekday()
            dtstart_day_code = weekday_names[dtstart_weekday]
            
            # Only include if today matches DTSTART's day of week
            if today_code != dtstart_day_code:
                continue
        
        # Check EXDATE - is today excluded?
        if e.get('exdate'):
            today_str = now.strftime('%Y%m%d')
            if today_str in e['exdate']:
                continue
        
        # Create today's instance with the event's time
        today_event = datetime.combine(now.date(), event_time).replace(tzinfo=pacific)
        
        # Check if DTSTART is in the future (recurrence hasn't started yet)
        if start_dt.date() > now.date():
            continue  # Recurrence starts in the future
    else:
        # Non-recurring event - use actual date
        if start_dt.date() != now.date():
            continue  # Not today
        today_event = start_dt
    
    # Check if event is within our window (next 4 hours)
    if now <= today_event <= window_end:
        alerts_needed.append({
            'summary': e.get('summary', 'Unknown'),
            'location': e.get('location', ''),
            'start': today_event
        })

# Print results
if alerts_needed:
    print(f"\nFound {len(alerts_needed)} event(s) requiring departure:")
    for evt in alerts_needed:
        print(f"\n• {evt['summary']}")
        print(f"  Start: {evt['start'].strftime('%I:%M %p')}")
        print(f"  Location: {evt['location'][:60]}...")
        
        # Calculate leave time (15 min drive + 15 min buffer)
        drive_time_minutes = 15
        leave_by = evt['start'] - timedelta(minutes=drive_time_minutes + 15)
        minutes_until_leave = (leave_by - now).total_seconds() / 60
        
        print(f"  Leave by: {leave_by.strftime('%I:%M %p')} ({minutes_until_leave:.0f} min from now)")
        
        if 0 <= minutes_until_leave <= 60:
            print(f"  ⚠️  ALERT: Leave within {minutes_until_leave:.0f} minutes!")
        elif minutes_until_leave < 0:
            print(f"  🚨 OVERDUE: Should have left {abs(minutes_until_leave):.0f} minutes ago!")
else:
    print("\nNo events requiring departure in the next 4 hours.")

print("\n" + "="*60)

# Summary for alerting system
if alerts_needed:
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
else:
    print("NO_REPLY")
