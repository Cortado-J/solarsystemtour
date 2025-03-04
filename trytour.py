import os
import itertools
from skyfield.api import load
from datetime import timedelta
import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------
# 1) LOAD EPHEMERIS FILES
# ------------------------------------------------------------------------------
planets = load('de438.bsp')

ephemerides_folder = 'ephemerides'
bsp_kernels = []
for fname in os.listdir(ephemerides_folder):
    if fname.endswith('.bsp'):
        full_path = os.path.join(ephemerides_folder, fname)
        print(f"Loading kernel: {full_path}")
        kernel = load(full_path)
        bsp_kernels.append(kernel)

all_kernels = [planets] + bsp_kernels

# ------------------------------------------------------------------------------
# 2) GLOBAL CONSTANTS
# ------------------------------------------------------------------------------
ACCELERATION = 1.0  # m/s² constant
CONVERGENCE_THRESHOLD = 60  # seconds
MAX_WAIT_DAYS = 180
WAIT_INTERVAL_DAYS = 10

# ------------------------------------------------------------------------------
# 3) SYSTEM ORDER (PLANET FIRST, THEN MOONS)
# ------------------------------------------------------------------------------
system_order = [
    ('Mercury System', ['Mercury']),
    ('Venus System', ['Venus']),
    ('Earth System', ['Earth', 'Moon']),
    ('Mars System', ['Mars', 'Phobos', 'Deimos']),
    # ('Ceres System', ['Ceres']), # Ceres is a dwarf planet
    ('Jupiter System', ['Jupiter', 'Io', 'Europa', 'Ganymede', 'Callisto']),
    ('Saturn System', ['Saturn', 'Mimas', 'Enceladus', 'Tethys', 'Dione', 'Rhea', 'Titan']),
    # ('Saturn System', ['Saturn', 'Mimas', 'Enceladus', 'Tethys', 'Dione', 'Rhea', 'Titan', 'Hyperion', 'Iapetus']),
    ('Uranus System', ['Uranus', 'Ariel', 'Umbriel', 'Titania', 'Oberon', 'Miranda']),
    ('Neptune System', ['Neptune', 'Triton', 'Nereid', 'Proteus']),
    # ('Pluto System', ['Pluto', 'Charon']), # Pluto is a dwarf planet
    # ('Haumea System', ['Haumea', 'Hiʻiaka']), # Haumea is a dwarf planet
    # ('Makemake System', ['Makemake']), # Makemake is a dwarf planet
    # ('Eris System', ['Eris', 'Dysnomia']), # Eris is a dwarf planet
]

system_order = [
    ('Mercury System', ['Mercury']),
    ('Venus System', ['Venus']),
    ('Earth System', ['Earth', 'Moon']),
    ('Mars System', ['Mars', 'Phobos', 'Deimos']),
    ('Jupiter System', ['Jupiter', 'Io', 'Europa', 'Ganymede', 'Callisto']),
    ('Saturn System', ['Saturn', 'Mimas', 'Enceladus', 'Dione', 'Rhea', 'Titan']),
    ('Uranus System', ['Uranus', 'Ariel', 'Umbriel', 'Titania', 'Oberon', 'Miranda']),
    ('Neptune System', ['Neptune', 'Triton', 'Nereid', 'Proteus']),
]

# ------------------------------------------------------------------------------
# 4) HELPER: load_body
# ------------------------------------------------------------------------------
def load_body(name):
    name_lower = name.lower()
    has_barycenter = name_lower in [
        'mercury', 'venus', 'earth', 'mars', 'jupiter', 
        'saturn', 'uranus', 'neptune', 'pluto'
    ]
    possible_labels = []
    if has_barycenter:
        possible_labels.append(name_lower + ' barycenter')
    possible_labels.append(name_lower)
    possible_labels.append(name_lower.capitalize())
    possible_labels.append(name.capitalize())
    possible_labels.append(name.upper())

    for kernel in all_kernels:
        for label in possible_labels:
            try:
                return kernel[label]
            except KeyError:
                pass
    return None

# ------------------------------------------------------------------------------
# 5) BUILD BODIES DICTIONARY
# ------------------------------------------------------------------------------
bodies = {}
for system_name, names in system_order:
    for nm in names:
        if nm not in bodies:
            obj = load_body(nm)
            if obj is None:
                print(f"Warning: {nm} not found in any loaded ephemeris file.")
            else:
                bodies[nm] = obj

# Ensure Earth is present (needed for initial/final journeys)
if 'Earth' not in bodies:
    earth_obj = load_body('Earth')
    if earth_obj:
        bodies['Earth'] = earth_obj

# ------------------------------------------------------------------------------
# 6) DISTANCE & TRAVEL
# ------------------------------------------------------------------------------
def distance(body1, body2, time):
    pos1 = body1.at(time).position.km
    pos2 = body2.at(time).position.km
    return np.linalg.norm(pos1 - pos2) * 1e3  # m

def travel_time(body1, body2, departure_time):
    d_initial = distance(body1, body2, departure_time)
    t_estimate = np.sqrt(2.0 * d_initial / ACCELERATION)
    for _ in range(20):
        arrival_time = departure_time + timedelta(seconds=t_estimate)
        d_new = distance(body1, body2, arrival_time)
        t_new = np.sqrt(2.0 * d_new / ACCELERATION)
        if abs(t_new - t_estimate) < CONVERGENCE_THRESHOLD:
            break
        t_estimate = t_new
    return t_new

def optimal_departure(body1, body2, current_time):
    best_total = float('inf')
    best_dep_time = current_time
    best_t_travel = 0.0
    for wait_days in range(0, MAX_WAIT_DAYS + 1, WAIT_INTERVAL_DAYS):
        dep_candidate = current_time + timedelta(days=wait_days)
        t_travel = travel_time(body1, body2, dep_candidate)
        total = wait_days*24*3600 + t_travel
        if total < best_total:
            best_total = total
            best_dep_time = dep_candidate
            best_t_travel = t_travel
    return best_dep_time, best_t_travel, best_total

# ------------------------------------------------------------------------------
# 7) ITINERARY TRACKING
# ------------------------------------------------------------------------------
itinerary = []

def record_leg(system_label, from_name, to_name, dep_time, travel_s):
    arrival_time = dep_time + timedelta(seconds=travel_s)
    # Simple max speed estimate = a*(travel_s/2)
    max_speed = ACCELERATION * (travel_s / 2.0)
    itinerary.append({
        'System': system_label,
        'From': from_name,
        'To': to_name,
        'Departure UTC': dep_time.utc_strftime('%Y-%m-%d %H:%M:%S'),
        'Travel Time (days)': travel_s/3600/24,
        'Max Speed (m/s)': max_speed,
        'Arrival UTC': arrival_time.utc_strftime('%Y-%m-%d %H:%M:%S')
    })
    return arrival_time

# ------------------------------------------------------------------------------
# 8) OPTIMIZE SYSTEM ROUTE (PLANET FIRST, THEN MOONS)
# ------------------------------------------------------------------------------
def optimize_system_route(system_bodies, arrival_time):
    """
    - system_bodies[0] is the planet
    - We fix that planet as the first visited body
    - We permute the remaining bodies (the moons)
    - Print candidate routes and pick the best
    """
    if len(system_bodies) == 1:
        # only the planet, no moons
        return system_bodies, arrival_time, 0.0

    planet = system_bodies[0]
    moons = system_bodies[1:]

    all_candidate_routes = []  # list of (full_route, total_internal_time)

    # Permute the moons only
    routes = list(itertools.permutations(moons))
    routecount = len(routes)
    routenum = 0
    for perm in routes:
        routenum += 1
        print(f"{planet}: Route {routenum} of {routecount}")
        route = [planet] + list(perm)
        total_time = 0.0
        valid = True
        # compute total time ignoring departure-time chaining
        current_t = arrival_time
        for i in range(len(route) - 1):
            fromB = route[i]
            toB = route[i+1]
            if fromB not in bodies or toB not in bodies:
                valid = False
                break
            _, _, leg_t = optimal_departure(bodies[fromB], bodies[toB], current_t)
            total_time += leg_t
            # We don't update current_t because we only need the sum

        if valid:
            all_candidate_routes.append((route, total_time))

    # Sort
    all_candidate_routes.sort(key=lambda x: x[1])

    print("Candidate routes for this system (planet-first) (sorted by total time):")
    for route, tval in all_candidate_routes:
        days = tval / (3600*24)
        print(f"   Route {route} -> internal travel time: {days:.2f} days")

    if not all_candidate_routes:
        print("   No valid permutations found.")
        return system_bodies, arrival_time, 0.0

    best_route, best_time = all_candidate_routes[0]
    print(f"   => Best route is {best_route}, total internal time = {best_time/(3600*24):.2f} days\n")

    # Now "fly" it to get final arrival_time
    current_t = arrival_time
    for i in range(len(best_route) - 1):
        fromB = best_route[i]
        toB = best_route[i+1]
        dep, t_travel, _ = optimal_departure(bodies[fromB], bodies[toB], current_t)
        current_t = record_leg("System: " + system_bodies[0], fromB, toB, dep, t_travel)

    return best_route, current_t, best_time

# ------------------------------------------------------------------------------
# 9) MAIN TOUR SEQUENCE
# ------------------------------------------------------------------------------
ts = load.timescale()
start_time = ts.utc(2025, 1, 1)
current_time = start_time

overall_details = []

# (A) INITIAL JOURNEY: Earth -> Mercury
if 'Earth' in bodies and 'Mercury' in bodies:
    dep_time, t_travel, total_sec = optimal_departure(bodies['Earth'], bodies['Mercury'], current_time)
    next_time = record_leg("Initial Earth->Mercury", 'Earth', 'Mercury', dep_time, t_travel)
    overall_details.append({
        'System': "Initial Transit: Earth -> Mercury",
        'Route': 'Earth -> Mercury',
        'System Start': current_time.utc_strftime('%Y-%m-%d'),
        'System Finish': next_time.utc_strftime('%Y-%m-%d'),
        'Internal Time (days)': total_sec / (3600 * 24)
    })
    current_time = next_time
else:
    print("Cannot do initial Earth->Mercury transit; missing bodies.")

# (B) Go system by system
overall_route = []
for idx, (system_name, system_bodies) in enumerate(system_order):
    print(f"\n=== Optimizing {system_name} ===")
    missing = [b for b in system_bodies if b not in bodies]
    if missing:
        print(f"Warning: skipping {system_name}, missing: {missing}")
        continue

    best_route, final_time, internal_time = optimize_system_route(system_bodies, current_time)
    overall_route.append((system_name, best_route))
    overall_details.append({
        'System': system_name,
        'Route': best_route,
        'System Start': current_time.utc_strftime('%Y-%m-%d'),
        'System Finish': final_time.utc_strftime('%Y-%m-%d'),
        'Internal Time (days)': internal_time / (3600 * 24)
    })
    current_time = final_time

    # Transit to next system if not last
    if idx < len(system_order) - 1:
        next_sys, next_bodies = system_order[idx + 1]
        next_planet = next_bodies[0]  # always the planet, by design
        if best_route and best_route[-1] in bodies and next_planet in bodies:
            dep_time, t_travel, tot = optimal_departure(bodies[best_route[-1]], bodies[next_planet], current_time)
            next_time = record_leg(f"Transit: {system_name}->{next_sys}",
                                   best_route[-1], next_planet,
                                   dep_time, t_travel)
            overall_details.append({
                'System': f"Transit: {system_name} -> {next_sys}",
                'Route': f"{best_route[-1]} -> {next_planet}",
                'System Start': current_time.utc_strftime('%Y-%m-%d'),
                'System Finish': next_time.utc_strftime('%Y-%m-%d'),
                'Internal Time (days)': tot / (3600 * 24)
            })
            current_time = next_time
        else:
            print(f"Warning: cannot transit from {best_route[-1]} to {next_planet} (missing).")

# (C) FINAL JOURNEY: Pluto->Earth
print("\n=== Final Transit from Pluto System back to Earth ===")
if 'Earth' in bodies and overall_route:
    # The last system is Pluto
    final_sys_name, final_sys_route = overall_route[-1]
    if final_sys_route:
        last_body = final_sys_route[-1]
        if last_body in bodies:
            dep_time, t_travel, total_s = optimal_departure(bodies[last_body], bodies['Earth'], current_time)
            next_time = record_leg("Final Pluto->Earth", last_body, 'Earth', dep_time, t_travel)
            overall_details.append({
                'System': "Final Transit: Pluto -> Earth",
                'Route': f"{last_body} -> Earth",
                'System Start': current_time.utc_strftime('%Y-%m-%d'),
                'System Finish': next_time.utc_strftime('%Y-%m-%d'),
                'Internal Time (days)': total_s / (3600 * 24)
            })
            current_time = next_time
        else:
            print("Cannot do final Pluto->Earth; last body missing.")
    else:
        print("No final route in Pluto system.")
else:
    print("Cannot do final transit; Earth or route missing.")

# ------------------------------------------------------------------------------
# 10) PRINT SUMMARIES
# ------------------------------------------------------------------------------
df_systems = pd.DataFrame(overall_details)
print("\n=== SYSTEM-BY-SYSTEM SUMMARY ===")
print(df_systems)

df_legs = pd.DataFrame(itinerary)
print("\n=== FULL ITINERARY (LEG-BY-LEG) ===")
print(df_legs.to_string(index=False))

if itinerary:
    final_arrival = itinerary[-1]['Arrival UTC']
    print(f"\nFinal arrival time: {final_arrival}")
else:
    print("\nNo travel legs recorded!")
