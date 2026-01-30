import math
import datetime

# -----------------------------------------------------------------------------
# ACE Calculation
# -----------------------------------------------------------------------------

def calculate_ace(entries):
    """
    Calculates Accumulated Cyclone Energy (ACE).
    Formula: Sum of (Wind_Speed / 10000)^2 for every 6 hours (00, 06, 12, 18Z)
    where storm status is Tropical/Subtropical and wind >= 34kts.
    """
    ace_sum = 0
    for entry in entries:
        # Check for 6-hour synoptic times
        if entry.entrytime.hour in [0, 6, 12, 18]:
            # Check for Tropical/Subtropical status
            if entry.status in ['SS', 'TS', 'HU', 'SD']:
                # Check for TS intensity
                if entry.wind >= 34:
                    ace_sum += (entry.wind ** 2)
    
    return ace_sum / 10000


# -----------------------------------------------------------------------------
# Duration Calculation
# -----------------------------------------------------------------------------

def calculate_duration_days(entries, min_wind=0):
    """
    Calculates the duration (in days) where the storm maintained 
    winds >= min_wind.
    """
    duration = datetime.timedelta(0)
    
    # Iterate through segments
    for i in range(1, len(entries)):
        prev_entry = entries[i - 1]
        curr_entry = entries[i]
        
        # We attribute the duration of the segment to the status of the START point
        # We check is_TC() to ensure we aren't counting Extratropical duration
        if prev_entry.is_TC() and prev_entry.wind >= min_wind:
            duration += curr_entry.entrytime - prev_entry.entrytime
            
    return duration.total_seconds() / (24 * 3600)


# -----------------------------------------------------------------------------
# Distance Calculation (Haversine)
# -----------------------------------------------------------------------------

def calculate_track_distance(entries, min_wind=0):
    """
    Calculates the track distance (in nautical miles) where the storm
    maintained winds >= min_wind.
    """
    total_distance = 0
    if len(entries) < 2:
        return 0
        
    for i in range(1, len(entries)):
        prev_entry = entries[i - 1]
        curr_entry = entries[i]
        
        include_segment = False
        
        # Logic: If looking for specific intensity, check the previous entry
        if min_wind > 0:
            if prev_entry.is_TC() and prev_entry.wind >= min_wind:
                include_segment = True
        else:
            # If no min_wind (total distance), include everything
            include_segment = True
            
        if include_segment:
            dist = haversine(prev_entry.latitude, prev_entry.longitude, 
                             curr_entry.latitude, curr_entry.longitude)
            total_distance += dist
            
    return total_distance


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two geographical points (nautical miles).
    """
    R = 3440.1 # Radius of Earth in Nautical Miles
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c