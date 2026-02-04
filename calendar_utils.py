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
        try:
            calendars = principal.calendars()
        except Exception as e:
            logging.error(f"Could not fetch calendars: {e}")
            return "⚠️ Fehler beim Abrufen der Kalenderliste."
        
        if not calendars:
            return "Keine Kalender gefunden."

        # Define the time range for "Today" in local time
        tz_info = tz.gettz(timezone)
        now = datetime.datetime.now(tz_info)
        today_date = now.date()
        
        # Search window: Today 00:00 to 23:59 Local Time
        search_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        search_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        events_found = []

        for calendar in calendars:
            try:
                # expand=True ensures recurring events (like birthdays) are expanded into instances
                events = calendar.date_search(start=search_start, end=search_end, expand=True)
                
                for event in events:
                    # Load the event details
                    try:
                        vobject = event.vobject_instance
                        vevent = vobject.vevent
                        summary = vevent.summary.value
                        dtstart = vevent.dtstart.value
                        
                        # Normalize start time
                        event_date = None
                        time_str = ""
                        is_all_day = False
                        
                        if isinstance(dtstart, datetime.datetime):
                            # It's a specific time
                            # Convert to local time
                            if dtstart.tzinfo:
                                local_dt = dtstart.astimezone(tz_info)
                            else:
                                # Assume local if no timezone
                                local_dt = dtstart.replace(tzinfo=tz_info)
                            
                            event_date = local_dt.date()
                            time_str = local_dt.strftime("%H:%M")
                            
                        elif isinstance(dtstart, datetime.date):
                            # It's an all-day event
                            event_date = dtstart
                            is_all_day = True
                            time_str = "Ganztägig"
                            
                        # FILTER: Check if the event happens TODAY
                        # We accept events that start today, OR all-day events that match today.
                        if event_date == today_date:
                            events_found.append(f"• {time_str}: {summary}")
                            
                    except Exception as ev_e:
                        logging.warning(f"Skipping event due to parse error: {ev_e}")
                        continue

            except Exception as e:
                logging.error(f"Error reading calendar {calendar.name if hasattr(calendar, 'name') else 'unknown'}: {e}")
                continue

        if not events_found:
            return "Heute stehen keine Termine im Kalender."
            
        # Deduplicate results
        unique_events = sorted(list(set(events_found)))
        
        return "📅 **Deine Termine heute:**\n" + "\n".join(unique_events)

    except Exception as e:
        logging.error(f"CalDAV error: {e}")
        return f"Fehler beim Abrufen des Kalenders: {str(e)}"
