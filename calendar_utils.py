import caldav
import datetime
import logging
from dateutil import tz

def get_todays_events(email, password, timezone="Europe/Berlin"):
    """
    Fetches events for the current day from Apple Calendar (iCloud).
    """
    try:
        # iCloud CalDAV URL
        caldav_url = "https://caldav.icloud.com"
        
        client = caldav.DAVClient(
            url=caldav_url,
            username=email,
            password=password
        )
        
        principal = client.principal()
        calendars = principal.calendars()
        
        if not calendars:
            return "Keine Kalender gefunden."

        # Define the time range for today
        tz_info = tz.gettz(timezone)
        now = datetime.datetime.now(tz_info)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        events_found = []

        for calendar in calendars:
            try:
                # search for events in the time range
                events = calendar.date_search(start=start_of_day, end=end_of_day)
                
                for event in events:
                    # Load the event details
                    ical_data = event.data
                    vobject = event.vobject_instance
                    vevent = vobject.vevent
                    
                    summary = vevent.summary.value
                    
                    # Handle start time
                    dtstart = vevent.dtstart.value
                    
                    # If it's a datetime object (normal event)
                    if isinstance(dtstart, datetime.datetime):
                         # Convert to local time if it has timezone info
                         if dtstart.tzinfo:
                             local_dtRequest = dtstart.astimezone(tz_info)
                             time_str = local_dtRequest.strftime("%H:%M")
                         else:
                             # Naive usually implies floating or UTC, assume local for now or leave as is
                             time_str = dtstart.strftime("%H:%M")
                    # If it's a date object (all-day event)
                    elif isinstance(dtstart, datetime.date):
                        time_str = "Ganztägig"
                    else:
                        time_str = "?"

                    events_found.append(f"• {time_str}: {summary}")
            except Exception as e:
                logging.error(f"Error reading calendar {calendar}: {e}")
                continue

        if not events_found:
            return "Heute stehen keine Termine im Kalender."
            
        return "📅 **Deine Termine heute:**\n" + "\n".join(events_found)

    except Exception as e:
        logging.error(f"CalDAV error: {e}")
        return f"Fehler beim Abrufen des Kalenders: {str(e)}"
