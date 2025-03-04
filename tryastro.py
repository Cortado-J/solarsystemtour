from astroquery.jplhorizons import Horizons
from astropy.coordinates import solar_system_ephemeris, get_body_barycentric
from astropy.time import Time
import astropy.units as u
import numpy as np

# Function to get the positions of moons relative to the barycenter
def get_moon_positions(start_time, end_time):
    with solar_system_ephemeris.set('builtin'):
        # Get barycentric coordinates of Jupiter
        jupiter = get_body_barycentric('599', start_time)

        # Get the positions of the moons
        moon_positions = {}
        for moon_number in range(1, 80):  # Assume a maximum of 80 moons
            try:
                moon = Horizons(id=f'{moon_number}',
                                epochs={'start': start_time.jd, 'stop': end_time.jd, 'step': '1d'},
                                location='@599')  # Specify Jupiter as the observer
                eph = moon.ephemerides(eph_type='vector', refplane='ecliptic', coord_format='rectangular')
                moon_positions[f'Moon {moon_number}'] = eph[['x', 'y', 'z']].values + jupiter.cartesian.xyz.value
            except Exception as e:
                if "ephemeris." in str(e):
                    break  # No more moons found
                else:
                    continue  # Try the next moon

        return moon_positions

# Specify the parameters
start_time = Time('2023-01-01')
end_time = Time('2023-01-02')

# Get moon positions relative to the barycenter
moon_positions = get_moon_positions(start_time, end_time)

# Print the results
for moon, position in moon_positions.items():
    print(f'{moon} Position (relative to the barycenter): {position}')
