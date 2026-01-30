import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms
import matplotlib.dates as mdates
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------

WIND_COLORS = {
    'Cat 5': '#8b0088',
    'Cat 4': '#ff00fc',
    'Cat 3': '#dd0000',
    'Cat 2': '#ff9e00',
    'Cat 1': '#ffff00',
    'TS': '#3185d3',
    'TD': '#8fc2f2',
}

STATUS_MARKERS = {
    'Tropical': 'o',
    'Subtropical': 's',
    'Non-Tropical': '^',
}

# (min_wind, max_wind, label, color, title_label)
CATEGORIES_INTENSITY = [
    (0, 34, 'TD', '#ffffff', 'Tropical Depression'),
    (34, 64, 'TS', '#f1fafc', 'Tropical Storm'),
    (64, 83, 'Cat 1', '#fffde2', 'Hurricane'),
    (83, 96, 'Cat 2', '#fff2d0', 'Hurricane'),
    (96, 113, 'Cat 3', '#ffdfbe', 'Major Hurricane'),
    (113, 137, 'Cat 4', '#ffc9b3', 'Major Hurricane'),
    (137, 200, 'Cat 5', '#f6b3a7', 'Major Hurricane')
]
    
DEFAULT_ATLANTIC_EXTENT = [-105, -5, 0, 65]


# -----------------------------------------------------------------------------
# Main Plotting Functions
# -----------------------------------------------------------------------------

def plot_storm_tracks(storm_or_storms, title_info=None, labels=False):
    """
    Plots a map of the storm track(s).
    Accepts a single object (TropicalCyclone) or a list of objects (Season).
    """
    is_single_storm = not isinstance(storm_or_storms, list)
    storms_to_plot = [storm_or_storms] if is_single_storm else storm_or_storms

    if not storms_to_plot:
        print("No storms to plot.")
        return

    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    
    _add_default_map_features(ax)
    
    all_latitudes = []
    all_longitudes = []

    # Plot each storm
    for storm in storms_to_plot:
        latitudes = [entry.latitude for entry in storm.entries]
        longitudes = [entry.longitude for entry in storm.entries]
        all_latitudes.extend(latitudes)
        all_longitudes.extend(longitudes)

        if is_single_storm:
            # Single storm plot: black line with colored markers
            ax.plot(longitudes, latitudes, color='black', linewidth=1, transform=ccrs.PlateCarree(), zorder=1)
            _plot_default_data_points(ax, storm.entries)
        else:
            # Multi-storm plot: line segments colored by intensity
            for i in range(len(storm.entries) - 1):
                entry1 = storm.entries[i]
                entry2 = storm.entries[i+1]
                
                # Determine color and style based on the starting point of the segment
                color, linestyle = _get_line_color_and_style(entry1)
                
                ax.plot([entry1.longitude, entry2.longitude], [entry1.latitude, entry2.latitude],
                        color=color, linestyle=linestyle, linewidth=1, transform=ccrs.PlateCarree(), zorder=1)
    
    # Set map extent based on plot type
    if is_single_storm:
        _set_default_map_extent(ax, all_longitudes, all_latitudes)
    else:
        ax.set_extent(DEFAULT_ATLANTIC_EXTENT, crs=ccrs.PlateCarree())
        ax.set_aspect('equal')
    
    _add_default_legend(ax, is_single_storm)
    _add_default_titles(ax, storms_to_plot, is_single_storm, title_info)
    
    if labels and not is_single_storm:
        _add_default_labels(ax, storms_to_plot)
    
    plt.show()


def plot_intensity_chart(storm, zoom=False, landfalls=False):
    """
    Generates and shows a plot of the storm's intensity over time.
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Extract data using the object's to_dataframe method
    df = storm.to_dataframe()
    t = df['time']
    w = df['wind'] # Note: 'wind' matches the column name in objects.py

    _plot_intensity_bands(ax, t, CATEGORIES_INTENSITY)
    _plot_intensity_lines_and_labels(ax, t, w, CATEGORIES_INTENSITY, zoom)
    ax.plot(t, w, color='black', linewidth=3)
    
    if landfalls:
        landfall_df = df[df['landfall'] == True]
        if not landfall_df.empty:
            landfall_t = landfall_df['time']
            landfall_w = landfall_df['wind']
            ax.scatter(landfall_t, landfall_w, color='red', marker="$L$", s=115, zorder=10)

    _set_intensity_axes(ax, t, w, zoom)
    _set_intensity_title(ax, storm, w, CATEGORIES_INTENSITY)
    
    plt.show()


# -----------------------------------------------------------------------------
# Internal Helper Functions
# -----------------------------------------------------------------------------

def _add_default_labels(ax, storms_to_plot):
    """Adds labels to the start and end of tracks if visible."""
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    for storm in storms_to_plot:
        start_entry = storm.entries[0]
        end_entry = storm.entries[-1]
        
        if x_min <= start_entry.longitude <= x_max and y_min <= start_entry.latitude <= y_max:
            ax.text(start_entry.longitude + 0.5, start_entry.latitude + 0.5, storm.name,
                    transform=ccrs.PlateCarree(), fontsize=8, color='black')
                
        if x_min <= end_entry.longitude <= x_max and y_min <= end_entry.latitude <= y_max:
            ax.text(end_entry.longitude + 0.5, end_entry.latitude + 0.5, storm.name,
                    transform=ccrs.PlateCarree(), fontsize=8, color='black')

def _get_line_color_and_style(entry):
    """Returns the color and linestyle for a track segment."""
    wind = entry.wind
    status = entry.status
    
    if status in ['EX', 'LO', 'WV', 'DB']:
        linestyle = ':' 
        color = 'black'
    else:
        linestyle = '-' 
        if wind >= 137:   color = WIND_COLORS['Cat 5']
        elif wind >= 113: color = WIND_COLORS['Cat 4']
        elif wind >= 96:  color = WIND_COLORS['Cat 3']
        elif wind >= 83:  color = WIND_COLORS['Cat 2']
        elif wind >= 64:  color = WIND_COLORS['Cat 1']
        elif wind >= 34:  color = WIND_COLORS['TS']
        else:             color = WIND_COLORS['TD']
        
    return color, linestyle

def _add_default_map_features(ax):
    scale = '50m'
    states = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale=scale,
        facecolor='none')

    ax.add_feature(cfeature.LAND.with_scale(scale), facecolor='#fbf5ea')
    ax.add_feature(cfeature.OCEAN.with_scale(scale), facecolor='#edfbff')
    ax.add_feature(cfeature.LAKES.with_scale(scale), facecolor='#edfbff')
    ax.add_feature(cfeature.COASTLINE.with_scale(scale), alpha=1, edgecolor='black', linewidth=0.5)
    ax.add_feature(cfeature.BORDERS.with_scale(scale), alpha=1, edgecolor='black', linewidth=0.5)
    ax.add_feature(states, alpha=1, edgecolor='black', linewidth=0.5)
    
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'fontsize': 7.5}
    gl.ylabel_style = {'fontsize': 7.5}

def _plot_default_data_points(ax, entries):
    for entry in entries:
        wind = entry.wind
        status = entry.status
        
        if wind >= 137:   color = WIND_COLORS['Cat 5']
        elif wind >= 113: color = WIND_COLORS['Cat 4']
        elif wind >= 96:  color = WIND_COLORS['Cat 3']
        elif wind >= 83:  color = WIND_COLORS['Cat 2']
        elif wind >= 64:  color = WIND_COLORS['Cat 1']
        elif wind >= 34:  color = WIND_COLORS['TS']
        else:             color = WIND_COLORS['TD']
        
        if status in ['SS', 'SD']:
            marker = STATUS_MARKERS['Subtropical']
        elif status in ['EX', 'LO', 'WV', 'DB']:
            marker = STATUS_MARKERS['Non-Tropical']
        else:
            marker = STATUS_MARKERS['Tropical']
        
        ax.scatter(entry.longitude, entry.latitude, color=color, marker=marker, s=30, edgecolor='black', linewidth=0.35, transform=ccrs.PlateCarree(),zorder=2)

def _set_default_map_extent(ax, longitudes, latitudes, buffer=7):
    if not longitudes or not latitudes:
        ax.set_global()
        return
        
    min_lon, max_lon = min(longitudes), max(longitudes)
    min_lat, max_lat = min(latitudes), max(latitudes)
    
    lon_range = max_lon - min_lon
    lat_range = max_lat - min_lat

    center_lon = (min_lon + max_lon) / 2
    center_lat = (min_lat + max_lat) / 2
    
    figure_aspect = 9.0 / 6.0
    
    if lat_range == 0:
        map_aspect = figure_aspect
    else:
        map_aspect = lon_range / lat_range

    lon_buffer = buffer
    lat_buffer = buffer
    
    if map_aspect > figure_aspect:
        half_lon_side = lon_range / 2 + lon_buffer
        half_lat_side = half_lon_side / figure_aspect
    else:
        half_lat_side = lat_range / 2 + lat_buffer
        half_lon_side = half_lat_side * figure_aspect

    ax.set_extent([center_lon - half_lon_side, center_lon + half_lon_side,
                   center_lat - half_lat_side, center_lat + half_lat_side],
                   crs=ccrs.PlateCarree())
    ax.set_aspect('equal')

def _add_default_legend(ax, is_single_storm):
    if not is_single_storm:
        legend_elements = [
            plt.Line2D([0], [0], color='black', linestyle=':', linewidth=2, label='Non-Tropical'),
            plt.Line2D([0], [0], color=WIND_COLORS['TD'], linewidth=2, label='Sub/Tropical Depression'),
            plt.Line2D([0], [0], color=WIND_COLORS['TS'], linewidth=2, label='Sub/Tropical Storm'),
            plt.Line2D([0], [0], color=WIND_COLORS['Cat 1'], linewidth=2, label='Category 1'),
            plt.Line2D([0], [0], color=WIND_COLORS['Cat 2'], linewidth=2, label='Category 2'),
            plt.Line2D([0], [0], color=WIND_COLORS['Cat 3'], linewidth=2, label='Category 3'),
            plt.Line2D([0], [0], color=WIND_COLORS['Cat 4'], linewidth=2, label='Category 4'),
            plt.Line2D([0], [0], color=WIND_COLORS['Cat 5'], linewidth=2, label='Category 5'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.9).set_zorder(10)
        return

    legend_elements = [
        plt.Line2D([0], [0], marker=STATUS_MARKERS['Non-Tropical'], color='w', markerfacecolor='w', markeredgecolor='black', markersize=7, label='Non-Tropical'),
        plt.Line2D([0], [0], marker=STATUS_MARKERS['Subtropical'], color='w', markerfacecolor='w', markeredgecolor='black', markersize=7, label='Subtropical'),
        plt.Line2D([0], [0], marker=STATUS_MARKERS['Tropical'], color='w', markerfacecolor=WIND_COLORS['TD'], markeredgecolor='black', markersize=6, label='Tropical Depression'),
        plt.Line2D([0], [0], marker=STATUS_MARKERS['Tropical'], color='w', markerfacecolor=WIND_COLORS['TS'], markeredgecolor='black', markersize=6, label='Tropical Storm'),
        plt.Line2D([0], [0], marker=STATUS_MARKERS['Tropical'], color='w', markerfacecolor=WIND_COLORS['Cat 1'], markeredgecolor='black', markersize=6, label='Category 1'),
        plt.Line2D([0], [0], marker=STATUS_MARKERS['Tropical'], color='w', markerfacecolor=WIND_COLORS['Cat 2'], markeredgecolor='black', markersize=6, label='Category 2'),
        plt.Line2D([0], [0], marker=STATUS_MARKERS['Tropical'], color='w', markerfacecolor=WIND_COLORS['Cat 3'], markeredgecolor='black', markersize=6, label='Category 3'),
        plt.Line2D([0], [0], marker=STATUS_MARKERS['Tropical'], color='w', markerfacecolor=WIND_COLORS['Cat 4'], markeredgecolor='black', markersize=6, label='Category 4'),
        plt.Line2D([0], [0], marker=STATUS_MARKERS['Tropical'], color='w', markerfacecolor=WIND_COLORS['Cat 5'], markeredgecolor='black', markersize=6, label='Category 5'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.9).set_zorder(10)

def _add_default_titles(ax, storms_to_plot, is_single_storm, title_info=None):
    if is_single_storm:
        storm = storms_to_plot[0]
        # Use peak_status from object, or calculate simply if needed
        # We rely on Duck Typing here. We assume storm has .name, .year, .peak_status
        # If peak_status is property we access it directly.
        
        status_str = getattr(storm, 'peak_status', 'Storm')
        peak_w = getattr(storm, 'peak_wind', 0)
        
        # Expand abbreviations for title
        if status_str == 'MH': title_status = "Major Hurricane"
        elif status_str == 'HU': title_status = "Hurricane"
        elif status_str == 'TS': title_status = "Tropical Storm"
        elif status_str == 'TD': title_status = "Tropical Depression"
        elif status_str == 'SS': title_status = "Subtropical Storm"
        elif status_str == 'SD': title_status = "Subtropical Depression"
        else: title_status = status_str
            
        ax.set_title(f"{title_status} {storm.name}", fontsize=15, fontweight="bold", loc="left")
        
        start_date = storm.entries[0].entrytime.strftime('%d %b %Y')
        end_date = storm.entries[-1].entrytime.strftime('%d %b %Y')
        ax.set_title(f"{start_date} - {end_date}", fontsize=10, loc="right", fontweight="normal")
        
    else:
        if title_info and title_info.get('type') == 'season':
            ax.set_title(f"{title_info['year']} Atlantic Hurricane Season", fontsize=15, fontweight="bold", loc="left")
            subtitle = f"{title_info['ts_count']} named {chr(183)} {title_info['hu_count']} hurricanes {chr(183)} {title_info['mh_count']} major"
            ax.set_title(subtitle, fontsize=10, loc="right", fontweight="normal")
        else:
            ax.set_title(f"{len(storms_to_plot)} Filtered Storms", fontsize=11, fontweight="bold", loc="left")
    
    plt.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.89)

def _plot_intensity_bands(ax, t, categories):
    for w_min, w_max, _, color, _ in categories:
        rect = mpatches.Rectangle(
            (mdates.date2num(t.iloc[0]), w_min),
            mdates.date2num(t.iloc[-1]) - mdates.date2num(t.iloc[0]),
            w_max - w_min, facecolor=color, alpha=1, zorder=-1)
        ax.add_patch(rect)

def _plot_intensity_lines_and_labels(ax, t, w, categories, zoom):
    trans = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)

    if zoom:
        max_w = max(w)
        for w_min, w_max, label, _, _ in categories:
            if w_max <= max_w + 5 and w_max < 200:
                ax.axhline(w_max, linewidth=0.5, linestyle='dashed', color='black', alpha=0.5)
            if w_min > 0 and max_w >= w_min - 2:
                ax.text(0.015, w_min + 1.5, label, fontsize=9, fontweight="light", alpha=0.6, transform=trans)
    else:
        for w_min, w_max, label, _, _ in categories:
            if w_max < 200:
                ax.axhline(w_max, linewidth=0.5, linestyle='dashed', color='black', alpha=0.5)
            if w_min > 0:
                ax.text(0.015, w_min + 1.5, label, fontsize=9, fontweight="light", alpha=0.6, transform=trans)

def _set_intensity_axes(ax, t, w, zoom):
    if zoom:
        y_lim_bottom = max(0, min(w) - 5)
        y_lim_top = max(w) + 5
        ax.set_ylim(bottom=y_lim_bottom, top=y_lim_top)
        y_ticks = range(int(y_lim_bottom), int(y_lim_top), 10)
        ax.set_yticks(y_ticks)
    else:
        ax.set_ylim(bottom=20, top=165)
        y_ticks = range(20, 170, 10)
        ax.set_yticks(y_ticks)
    
    ax.set_ylabel('maximum sustained wind speed (kt)', fontsize=10)

    tick_indices = np.linspace(0, len(t) - 1, 5).astype(int)
    tick_locations = [t.iloc[i] for i in tick_indices]
    tick_labels = [t.iloc[i].strftime('%m/%d\n%H UTC') for i in tick_indices]
    ax.set_xticks(tick_locations)
    ax.set_xticklabels(tick_labels, ha='center')
    ax.set_xlim(t.iloc[0], t.iloc[-1])

def _set_intensity_title(ax, storm, w, categories):
    max_w = max(w)
    cat_label = "Tropical Depression"
    for w_min, _, _, _, title_label in categories:
        if max_w >= w_min:
            cat_label = title_label
    ax.set_title(f'{cat_label} {storm.name} ({storm.year})', fontsize=20, fontweight="medium")