import win32evtlog

def get_latest_logs(max_events=50):
    server = "localhost"
    logtype = "System"

    hand = win32evtlog.OpenEventLog(server, logtype)
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    events = []
    counts = {"INFO": 0, "WARNING": 0, "ERROR": 0}

    total = 0
    while total < max_events:
        records = win32evtlog.ReadEventLog(hand, flags, 0)
        if not records:
            break
        for ev_obj in records:
            level = "INFO"
            if ev_obj.EventType == 2:
                level = "ERROR"
            elif ev_obj.EventType == 3:
                level = "WARNING"

            counts[level] += 1
            events.append({
                "timestamp": ev_obj.TimeGenerated.Format(),
                "level": level,
                "message": str(ev_obj.StringInserts)
            })
            total += 1
            if total >= max_events:
                break

    return events, counts
