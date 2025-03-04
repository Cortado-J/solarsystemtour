import os
from skyfield.api import load

def inspect_bsp_folder(folder='ephemerides'):
    # Find all BSP files
    bsp_files = [f for f in os.listdir(folder) if f.endswith('.bsp')]
    if not bsp_files:
        print("No BSP files found in folder:", folder)
        return

    for fname in bsp_files:
        full_path = os.path.join(folder, fname)
        print(f"\n=== Inspecting BSP: {fname} ===")

        # Load kernel with Skyfield
        kernel = load(full_path)

        # Check each segment
        for seg_index, seg in enumerate(kernel.segments):
            # Attempt to read coverage if possible
            if hasattr(seg, 'start_time') and hasattr(seg, 'end_time'):
                start_utc = seg.start_time.utc_strftime('%Y-%m-%d %H:%M:%S')
                end_utc = seg.end_time.utc_strftime('%Y-%m-%d %H:%M:%S')
                coverage_days = (seg.end_time - seg.start_time).days
                print(f"  Segment {seg_index}:")
                print(f"    Center : {seg.center_name} (ID={seg.center})")
                print(f"    Target : {seg.target_name} (ID={seg.target})")
                print(f"    Start  : {start_utc}")
                print(f"    End    : {end_utc}")
                print(f"    Coverage Duration: ~{coverage_days:.3f} days")
            else:
                # Fallback if no .start_time / .end_time
                print(f"  Segment {seg_index} has no explicit coverage times.")
                print(f"    Center : {seg.center_name} (ID={seg.center})")
                print(f"    Target : {seg.target_name} (ID={seg.target})")
                # Optionally do something else: skip, or sample times, etc.

if __name__ == "__main__":
    inspect_bsp_folder('ephemerides')
