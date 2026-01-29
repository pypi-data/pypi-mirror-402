
import sys
import os
import shutil
import numpy as np

# Dynamically add ../src to path relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "../src")
if src_path not in sys.path:
    sys.path.append(src_path)

from sage_lib.partition.Partition import Partition

def test_apm_aliases():
    print("--- Testing AtomPositionManager Aliases ---")
    
    # Setup dummy data in the test folder or temp folder
    test_dir = os.path.join(current_dir, "test_data_alias")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # Standard XYZ (no explicit properties)
    xyz_content = """2
Test Frame
H 0.0 0.0 0.0
H 1.0 0.0 0.0
"""
    xyz_path = os.path.join(test_dir, "test.xyz")
    with open(xyz_path, "w") as f:
        f.write(xyz_content)

    success = False
    try:
        p = Partition()
        # verbose=True helps debug if something goes wrong
        p.read_files(xyz_path, verbose=True) 
        
        if len(p.containers) == 0:
            print("FAIL: No containers loaded")
            return

        sr = p.containers[0]
        # Access APM via alias 'atoms' or 'atom'
        apm = sr.atom 
        print(f"APM accessed via sr.atom: {apm}")

        # TEST READ ALIASES
        print("1. Testing Read Aliases:")
        print(f"  Accessing .pos (expecting atomPositions):")
        pos = apm.pos
        if pos is not None and len(pos) == 2:
            print(f"    PASS: .pos returned {pos.shape} array.")
        else:
            print(f"    FAIL: .pos returned {pos}")

        print(f"  Accessing .species (expecting atomLabelsList):")
        species = apm.species
        if species is not None and len(species) == 2:
             print(f"    PASS: .species returned {species}")
        else:
             print(f"    FAIL: .species returned {species}")
             
        print(f"  Accessing .natoms (expecting atomCount):")
        natoms = apm.natoms
        if natoms == 2:
             print(f"    PASS: .natoms = {natoms}")
        else:
             print(f"    FAIL: .natoms = {natoms}")

        # TEST WRITE ALIASES
        print("2. Testing Write Aliases:")
        print(f"  Setting .pos = new_positions")
        new_pos = np.array([[5.0, 5.0, 5.0], [6.0, 6.0, 6.0]])
        apm.pos = new_pos
        
        # Verify via original attribute
        curr_pos = apm.atomPositions
        if np.allclose(curr_pos, new_pos):
            print("    PASS: .atomPositions detected the change made via .pos")
        else:
            print(f"    FAIL: .atomPositions {curr_pos} != {new_pos}")

        # Test introspection
        print("3. Introspection .aliases:")
        if "pos" in apm.aliases:
            print(f"    PASS: 'pos' found in aliases pointing to {apm.aliases['pos']}")
        else:
            print("    FAIL: 'pos' not found in aliases")

        success = True

    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    test_apm_aliases()
