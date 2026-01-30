import os
import re
import datetime
import urllib.request
import collections
from .objects import TropicalCyclone, Hurdat2Entry, Season
from .errors import StormNotFoundError, DataDownloadError, DataParseError

class Hurdat2:
    """
    Parses HURDAT2 data. If a file_path is provided, it reads the local file.
    Otherwise, it attempts to download the latest data from the NHC website.
    Access storms by ATCFID (e.g., hurdat_data.al031991) or seasons by year
    (e.g., hurdat_data[1991]).
    """
    def __init__(self, file_path=None):
        self._storms = {}
        data_content = False

        if file_path:
            if os.path.exists(file_path):
                print(f"Read data from local file: {file_path}")
                with open(file_path, 'r') as file:
                    data_content = file.read()
            else:
                print(f"Local file not found: {file_path}. Attempting to download from online...")
        else:
            print("Local file not specified. Attempting to download from online...")

        if not data_content:
            data_content = self._get_data_from_url()

        if data_content:
            self._read_data(data_content)
            self._create_storm_attributes()
        else:
            raise DataDownloadError("No data available to parse. The download failed. Please check the URL or your internet connection.")

    def __getitem__(self, key):
        """
        Allows access to a storm object by ATCFID or a (name, year) tuple,
        or a Season object by year.
        """
        if isinstance(key, int):
            storms_in_year = [storm for storm in self._storms.values() if storm.year == key]
            
            if not storms_in_year:
                raise StormNotFoundError(f"No storms found for the year {key}.")
                
            return Season(storms_in_year)
            
        if isinstance(key, str):
            storm_obj = self._storms.get(key.lower())
            if storm_obj is None:
                raise StormNotFoundError(f"'{key}' is not a valid ATCFID or storm name.")
            return storm_obj

        elif isinstance(key, tuple) and len(key) == 2:
            name_to_find = key[0].upper()
            try:
                year_to_find = int(key[1])
            except (ValueError, IndexError) as e:
                raise TypeError("The second element of the tuple must be a valid year.") from e
            
            for storm in self._storms.values():
                if storm.name.upper() == name_to_find and storm.year == year_to_find:
                    return storm
            
            raise StormNotFoundError(f"Storm '{key[0]}' from {key[1]} was not found.")

        else:
            raise TypeError("Invalid key format. Please use an integer year, an ATCFID string, or a (name, year) tuple.")
            
    def _get_data_from_url(self):
        """Finds and downloads the latest HURDAT2 file from the NHC website with caching."""
        cache_dir = os.path.join(os.path.expanduser('~'), '.hurdat2py_cache')
        cache_path = os.path.join(cache_dir, 'hurdat2_latest.txt')

        if os.path.exists(cache_path) and (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(cache_path))).days < 30:
            print("Using cached data from local file.")
            with open(cache_path, 'r') as file:
                return file.read()

        try:
            print("Cached data not found or outdated. Attempting to download from online...")
            url = "https://www.nhc.noaa.gov/data/hurdat/"
            with urllib.request.urlopen(url, timeout=5) as u:
                page_data = u.read().decode()

            all_hurdat_urls = re.findall(r"(hurdat2-[^\s]+\.txt)", page_data)
            
            URLTime = collections.namedtuple("URLTime", ["url", "date"])
            hurdat_urls_with_dates = []

            for filename in all_hurdat_urls:
                if "format" in filename or "readme" in filename:
                    continue

                timestr = None
                parsed_date = None
                match = re.search(r"(\d{4}-\d{2}-\d{2})\.txt", filename)
                if match:
                    timestr = match.group(1)
                    parsed_date = datetime.datetime.strptime(timestr, '%Y-%m-%d').date()
                else:
                    match = re.search(r"(\d{6})\.txt", filename)
                    if match:
                        timestr = match.group(1)
                        year = int(timestr[-2:])
                        if year > 50:
                            parsed_date = datetime.date(1900 + year, int(timestr[:2]), int(timestr[2:4]))
                        else:
                            parsed_date = datetime.date(2000 + year, int(timestr[:2]), int(timestr[2:4]))
                    else:
                        match = re.search(r"(\d{4}-\d{2})\.txt", filename)
                        if match:
                            timestr = match.group(1)
                            parsed_date = datetime.datetime.strptime(timestr, '%Y-%m').date()
                        else:
                            continue
                
                hurdat_urls_with_dates.append(URLTime(filename, parsed_date))
                
            if not hurdat_urls_with_dates:
                raise DataParseError("No HURDAT2 URLs found with a parseable date.")

            hurdat_urls_with_dates.sort(key=lambda u: u.date, reverse=True)

            latest_url = hurdat_urls_with_dates[0].url
            full_url = url + latest_url
            
            with urllib.request.urlopen(full_url, timeout=10) as u:
                file_content = u.read().decode()
                
                os.makedirs(cache_dir, exist_ok=True)
                with open(cache_path, 'w') as f:
                    f.write(file_content)
                
                print(f"Downloaded and read '{latest_url}' successfully.")
                print("A local copy has been saved.")
                return file_content
                
        except Exception as e:
            print(f"Error downloading HURDAT2 data from URL: {e}")
            raise DataDownloadError(f"Failed to download data: {e}") from e

    def _read_data(self, file_content):
        """Parses HURDAT2 data from a string."""
        lines = file_content.splitlines()
        
        current_storm = None
        for line in lines:
            if line.startswith('AL'):
                parts = line.split(',')
                storm_atcfid = parts[0].strip().lower()
                storm_name = parts[1].strip()
                current_storm = TropicalCyclone(storm_atcfid, storm_name, [])
                self._storms[storm_atcfid] = current_storm
            elif current_storm:
                parts = re.split(r',\s*', line.strip())
                try:
                    entry = Hurdat2Entry(parts[:8])
                    current_storm.entries.append(entry)
                except (ValueError, IndexError) as e:
                    print(f"Warning: Skipping malformed data line '{line.strip()}' due to error: {e}")

    def _create_storm_attributes(self):
        """Dynamically creates an attribute for each storm ATCFID."""
        for storm_atcfid, storm_obj in self._storms.items():
            setattr(self, storm_atcfid, storm_obj)
            
    def rank_seasons_by_ace(self, descending=True):
        """
        Calculates and returns a ranked list of all seasons by their ACE.
        """
        season_ace_data = []
        
        all_years = sorted(list(set(storm.year for storm in self._storms.values())))
        
        for year in all_years:
            try:
                season = self[year]
                ace_value = season.ace
                season_ace_data.append({'year': year, 'ace': ace_value})
            except StormNotFoundError:
                continue

        sorted_seasons = sorted(season_ace_data, key=lambda x: x['ace'], reverse=descending)

        return sorted_seasons
        
    def to_dataframe(self):
        """
        Returns a single pandas DataFrame containing all storm data in the database.
        """
        import pandas as pd
        all_data = []
        for storm in self._storms.values():
            all_data.append(storm.to_dataframe())
        
        return pd.concat(all_data, ignore_index=True)

    def __iter__(self):
        return iter(self._storms.values())

    def __len__(self):
        return len(self._storms)