import datetime
import numpy as np
import pandas as pd
from .analytics import calculate_ace, calculate_track_distance, calculate_duration_days
from .plot import plot_storm_tracks, plot_intensity_chart 

# -----------------------------------------------------------------------------
# 1. The Atomic Unit: Hurdat2Entry
# -----------------------------------------------------------------------------

class Hurdat2Entry:
    """
    Represents a single data entry (row) for a storm at a specific timestamp.
    """
    def __init__(self, entry_list):
        # Timestamps are constructed from date + time strings
        self.entrytime = datetime.datetime.strptime(entry_list[0] + entry_list[1], '%Y%m%d%H%M')
        
        # 'L' indicates landfall, otherwise NaN
        self.landfall = entry_list[2].strip() if entry_list[2].strip() == 'L' else np.nan
        
        self.status = entry_list[3].strip()

        # Parse Lat/Lon with N/S/E/W handling
        self.latitude = float(entry_list[4][:-1]) if entry_list[4][-1] == 'N' else -float(entry_list[4][:-1])
        self.longitude = float(entry_list[5][:-1]) if entry_list[5][-1] == 'E' else -float(entry_list[5][:-1])
        
        self.wind = int(entry_list[6].strip())
        
        # Handle pressure (often -999 for missing data)
        try:
            pressure_str = entry_list[7].strip()
            self.pressure = int(pressure_str) if pressure_str and pressure_str != '-999' else None
        except (ValueError, IndexError):
            self.pressure = None
    
    def is_TC(self):
        """Returns True if the status is a tropical cyclone type."""
        return self.status in ['TD', 'TS', 'HU', 'SS', 'SD']

    def __repr__(self):
        return f"<Hurdat2Entry: {self.entrytime} ({self.status} {self.wind}kts)>"


# -----------------------------------------------------------------------------
# 2. The Individual Storm: TropicalCyclone
# -----------------------------------------------------------------------------

class TropicalCyclone:
    """
    Represents a single tropical cyclone with its data and analysis methods.
    """
    def __init__(self, storm_atcfid, storm_name, entries):
        self.atcfid = storm_atcfid
        self.name = storm_name
        self.entries = entries
        
        # Safely parse year and cyclone number from ATCFID (e.g., AL012005)
        self.year = int(self.atcfid[-4:])
        try:
            self.cyclone_number = int(self.atcfid[2:4])
        except (ValueError, IndexError):
            self.cyclone_number = None
    
    # ==========================================
    # Properties: The Raw Data (Grouped Naming)
    # ==========================================

    @property
    def lats(self):
        """Returns a list of all latitudes for the storm."""
        return [entry.latitude for entry in self.entries]

    @property
    def lons(self):
        """Returns a list of all longitudes for the storm."""
        return [entry.longitude for entry in self.entries]
    
    @property
    def ace(self):
        return calculate_ace(self.entries)
        
    @property
    def peak_wind(self):
        if not self.entries: return 0
        return max(e.wind for e in self.entries)

    @property
    def peak_status(self):
        """
        Returns the highest tropical classification the storm achieved.
        Hierarchy: MH > HU > TS > SS > TD > SD.
        
        Note: 'MH' is derived. It requires the storm to have status='HU' 
        AND wind >= 96 kts simultaneously to avoid counting Extratropical winds.
        """
        # 1. Check for Major Hurricane (HU status + Wind >= 96)
        hu_entries = [e for e in self.entries if e.status == 'HU']
        if hu_entries:
            if max(e.wind for e in hu_entries) >= 96:
                return "MH"
            return "HU"
            
        # 2. Check for Tropical Storm
        statuses = set(e.status for e in self.entries)
        if 'TS' in statuses: 
            return "TS"
            
        # 3. Check for Subtropical Storm (SS)
        if 'SS' in statuses:
            return "SS"
            
        # 4. Check for Tropical Depression
        if 'TD' in statuses:
            return "TD"
            
        # 5. Check for Subtropical Depression
        if 'SD' in statuses:
            return "SD"
        
        # 6. Fallback (e.g., if it was ONLY ever EX, DB, LO, WV)
        # Returns the status associated with the highest wind speed.
        peak_entry = max(self.entries, key=lambda e: e.wind)
        return peak_entry.status
    
    @property
    def min_pressure(self):
        valid_pressures = [e.pressure for e in self.entries if e.pressure is not None]
        return min(valid_pressures) if valid_pressures else None

    @property
    def landfalls(self):
        return sum(1 for entry in self.entries if entry.landfall == 'L')

    # --- DURATION (Days) ---
    @property
    def duration_total(self):
        """Total time between first and last entry."""
        if len(self.entries) < 2: return 0.0
        diff = self.entries[-1].entrytime - self.entries[0].entrytime
        return diff.total_seconds() / (24 * 3600)

    @property
    def duration_tc(self):
        """Days spent as a Tropical Cyclone (TD or stronger)."""
        return calculate_duration_days(self.entries, min_wind=0)

    @property
    def duration_ts(self):
        """Days spent as a Tropical Storm (>= 34 kts)."""
        return calculate_duration_days(self.entries, min_wind=34)

    @property
    def duration_hurricane(self):
        """Days spent as a Hurricane (>= 64 kts)."""
        return calculate_duration_days(self.entries, min_wind=64)

    @property
    def duration_major(self):
        """Days spent as a Major Hurricane (>= 96 kts)."""
        return calculate_duration_days(self.entries, min_wind=96)

    # --- DISTANCE (Nautical Miles) ---
    @property
    def distance_total(self):
        """Total track length regardless of status."""
        return calculate_track_distance(self.entries, min_wind=0)

    @property
    def distance_tc(self):
        """Distance traveled while at least Tropical Depression strength."""
        return calculate_track_distance(self.entries, min_wind=0)

    @property
    def distance_ts(self):
        """Distance traveled while at least Tropical Storm strength."""
        return calculate_track_distance(self.entries, min_wind=34)

    @property
    def distance_hurricane(self):
        """Distance traveled while at least Hurricane strength."""
        return calculate_track_distance(self.entries, min_wind=64)

    @property
    def distance_major(self):
        """Distance traveled while at least Major Hurricane strength."""
        return calculate_track_distance(self.entries, min_wind=96)

    # ==========================================
    # Methods: Display & Export
    # ==========================================

    def stats(self):
        """
        Prints detailed statistics. 
        All values shown here are accessible as properties.
        """
        if not self.entries:
            print(f"Error: No data entries found for storm {self.atcfid}.")
            return

        print(f"--- Statistics for {self.name} ({self.atcfid}) ---")
        print(f"Range: {self.entries[0].entrytime} to {self.entries[-1].entrytime}")
        
        print(f"Duration (Days):")
        print(f"  Total: {self.duration_total:.2f}")
        print(f"  TC:    {self.duration_tc:.2f}") 
        print(f"  TS:    {self.duration_ts:.2f}")
        print(f"  HU:    {self.duration_hurricane:.2f}")
        print(f"  MH:    {self.duration_major:.2f}")
        
        print(f"Distance (nmi):")
        print(f"  Total: {self.distance_total:.0f}")
        print(f"  TC:    {self.distance_tc:.0f}")
        print(f"  TS:    {self.distance_ts:.0f}")
        print(f"  HU:    {self.distance_hurricane:.0f}")
        print(f"  MH:    {self.distance_major:.0f}")
        
        print(f"Peak Status:  {self.peak_status} ({self.peak_wind} kts)")
        print(f"Min Pressure: {self.min_pressure} hPa")
        print(f"Landfalls:    {self.landfalls}")
        print(f"ACE:          {self.ace:.2f}")

    def info(self):
        """Prints basic storm info."""
        print(f"--- {self.name} ({self.year}) ---")
        print(f"ID: {self.atcfid}")
        print(f"Status: {self.peak_status} ({self.peak_wind} kts)")
        print(f"ACE: {self.ace:.2f}")
        print(f"Entries: {len(self.entries)}")

    def to_dataframe(self):
        """Returns a pandas DataFrame of the storm's track data."""
        data_list = []
        for entry in self.entries:
            data_list.append({
                'atcfid': self.atcfid,
                'name': self.name,
                'time': entry.entrytime,
                'status': entry.status,
                'lat': entry.latitude,
                'lon': entry.longitude,
                'wind': entry.wind,
                'pressure': entry.pressure,
                'landfall': entry.landfall == 'L'
            })
        return pd.DataFrame(data_list)

    def plot(self):
        """Plots the track of this storm."""
        plot_storm_tracks(self)

    def plot_intensity(self, zoom=False, landfalls=False):
        """Plots the intensity (wind speed) over time."""
        plot_intensity_chart(self, zoom=zoom, landfalls=landfalls)

    def __repr__(self):
        return f"<TropicalCyclone: {self.name} ({self.year})>"


# -----------------------------------------------------------------------------
# 3. The Collection: Season
# -----------------------------------------------------------------------------

class Season:
    """
    Represents a single hurricane season (a collection of TropicalCyclones).
    """
    def __init__(self, storms):
        if not storms:
            raise ValueError("Cannot create a Season object with an empty storm list.")
        self.storms = storms
        self.year = storms[0].year
    
    # --- Properties ---

    @property
    def ace(self):
        return sum(storm.ace for storm in self.storms)

    @property
    def total_storms(self):
        return len(self.storms)
        
    @property
    def tropical_storms(self):
        return sum(1 for storm in self.storms if storm.peak_wind >= 34)

    @property
    def hurricanes(self):
        return sum(1 for storm in self.storms if storm.peak_wind >= 64)

    @property
    def major_hurricanes(self):
        return sum(1 for storm in self.storms if storm.peak_wind >= 96)

    # --- Methods ---

    def stats(self):
        """Prints a summary of the season's activity."""
        # Calculate TD count (Total - Named Storms)
        td_count = self.total_storms - self.tropical_storms
        
        print(f"--- Season Statistics for {self.year} ---")
        print(f"Total Storms: {self.total_storms} (TDs: {td_count})") 
        print(f"Tropical Storms: {self.tropical_storms}")
        print(f"Hurricanes: {self.hurricanes}")
        print(f"Major Hurricanes: {self.major_hurricanes}")
        print(f"Accumulated Cyclone Energy (ACE): {self.ace:.2f}")

    def to_dataframe(self):
        """Returns a single DataFrame containing data for ALL storms in the season."""
        if not self.storms:
            return pd.DataFrame()
        return pd.concat([storm.to_dataframe() for storm in self.storms], ignore_index=True)

    def plot(self, labels=True):
        """Plots tracks for the entire season."""
        title_info = {
            'type': 'season', 
            'year': self.year, 
            'ts_count': self.tropical_storms,
            'hu_count': self.hurricanes, 
            'mh_count': self.major_hurricanes
        }
        plot_storm_tracks(self.storms, title_info=title_info, labels=labels)
    
    def __getitem__(self, key):
        return self.storms[key]

    def __iter__(self):
        return iter(self.storms)

    def __len__(self):
        return len(self.storms)

    def __repr__(self):
        return f"<Season: {self.year} ({len(self.storms)} storms)>"