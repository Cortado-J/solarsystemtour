import re
from astroquery.jplhorizons import Horizons
# obj = Horizons(id='Ceres', location='568', epochs=2458133.33546)
# print(obj)


SOLAR_SYSTEM_BARYCENTRE = '0'
epochs=2458133.33546

def show(code):
    hor = Horizons(id=code, location=SOLAR_SYSTEM_BARYCENTRE, epochs=epochs)
    table = hor.elements()
    elements = table[0]
    # for col in elements.colnames:
    #     print(col)

    # diam = table['R_mean']
    name = elements['targetname']
    # for col in elements.colnames:
    #     print(col)
    # print(elements)
    # diameter = elements['diameter']
    betweenlastbrackets = re.search(r'\((.+)\)', name).group(0)[1:-1]
    if betweenlastbrackets == planet or betweenlastbrackets == code:
        print(planet, name)
    # , diameter)

for planet in range(1,9):
    print("---------------------------------------")
    show(str(planet))
    for moon in range(0,100):
        show(str(planet*100+moon))
