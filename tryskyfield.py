from skyfield.api import Loader

# Load the ephemeris data
load = Loader('~/skyfield-data')
ephemeris = load('de421.bsp')

# Define the target body ID for Jupiter
target_body = 5

# Define the start and end dates for the ephemeris calculation
start_date = '2022-01-01'
end_date = '2022-01-31'

# Create a timescale
timescale = load.timescale()

# Define the time range
start_time = timescale.utc(int(start_date[:4]), int(start_date[5:7]), int(start_date[8:10]))
end_time = timescale.utc(int(end_date[:4]), int(end_date[5:7]), int(end_date[8:10]))

# Get the positions of the moons as vectors from the center of the solar system
# ts = load.timescale()
# t = ts.utc(start_time, end_time)
t = [start_time, end_time]
planets = load('de421.bsp')
jupiter = planets[target_body]
earth = planets['earth']

for time_index in [0,1]:
    # Print the positions of the moons
    for i in range(len(t)):
        astrometric = earth.at(t[i]).observe(jupiter)
        position = astrometric.position.au
        print(f"Time: {t[i].utc_datetime()}")
        print(f"  Io:   Position = {position[0]} au, {position[1]} au, {position[2]} au")
        print(f"  Europa:   Position = {position[0]} au, {position[1]} au, {position[2]} au")
        print(f"  Ganymede:   Position = {position[0]} au, {position[1]} au, {position[2]} au")
        print(f"  Callisto:   Position = {position[0]} au, {position[1]} au, {position[2]} au")
        print()

