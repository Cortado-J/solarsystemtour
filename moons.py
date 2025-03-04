from astroquery.jplhorizons import Horizons

def get_jupiter_moons_list():
    # Initialize the Horizons object for Jupiter
    jupiter = Horizons(id='5', id_type=None)  # '5' is the ID for Jupiter
    
    # Query for Jupiter's moons
    eph = jupiter.elements(refsystem='B1950')
    jupiter_moons = eph['targetname']
    
    # jupiter_moons = eph['targetname'][eph['targetname'].str.contains('Jupiter', case=False)]
    
    return jupiter_moons.tolist()

# Example usage:
if __name__ == "__main__":
    jupiter_moons_list = get_jupiter_moons_list()
    print("List of moons of Jupiter:")
    for idx, moon in enumerate(jupiter_moons_list, start=1):
        print(f"{idx}. {moon}")
