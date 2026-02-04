import caldav
import datetime
import os
import sys
from dotenv import load_dotenv
from dateutil import tz

# Force UTF-8 for stdout
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

def debug_calendar():
    email = os.getenv('ICLOUD_EMAIL')
    password = os.getenv('ICLOUD_PASSWORD')
    timezone = "Europe/Berlin"

    print(f"Connecting with {email}...")

    caldav_url = "https://caldav.icloud.com"
    client = caldav.DAVClient(
        url=caldav_url,
        username=email,
        password=password
    )
    
    principal = client.principal()
    calendars = principal.calendars()
    
    print(f"Found {len(calendars)} calendars:")
    for cal in calendars:
        try:
            print(f" - {cal.name} (URL: {cal.url})")
        except Exception as e:
            print(f" - [Error printing name]: {e}")

    tz_info = tz.gettz(timezone)
    now = datetime.datetime.now(tz_info)
    # Search whole days
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    print(f"\nSearching for events between {start_of_day} and {end_of_day}...")

    for calendar in calendars:
        print(f"\nChecking calendar: {calendar.name}")
        try:
            # Try date_search
            events = calendar.date_search(start=start_of_day, end=end_of_day)
            print(f"  Found {len(events)} events.")
            
            for event in events:
                # event.load() # sometimes needed, sometimes automatic
                if not hasattr(event, 'vobject_instance'):
                    event.load()
                
                vevent = event.vobject_instance.vevent
                summary = vevent.summary.value
                dtstart = vevent.dtstart.value
                print(f"  - Event: {summary}")
                print(f"    Start: {dtstart} (Type: {type(dtstart)})")
                
        except Exception as e:
            print(f"  Error searching calendar: {e}")

if __name__ == "__main__":
    debug_calendar()
