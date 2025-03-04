from astroquery.jplhorizons import Horizons

# Query Ganymede (Jupiter's moon) using its ID (5)
obj = Horizons(id='503', location="@sun")

# Retrieve the data
eph = obj.ephemerides()

print(eph)

# # Extract the radius from the result
# radius_km = eph['R_mean'][0]
