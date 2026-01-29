import subprocess
import sys
import os

python = sys.executable

py_path = "./bin/"
cpp_path = "./bin/"
#cpp_path = "./bin/RelWithDebInfo/"

python_examples = [
    "elastic_fcm.py",
    "elastic_fcm_csg.py",
    "elastic_fcm_stl.py",
    "elastic_gmsh.py ../mesh.msh",
    "elastic_gyroid.py",
    "elastic_wave_IMEX_SEM.py",
    "interactive_eigenmodes.py",
    "planestress_fcm_lshaped_adaptive.py",
    "planestress_fcm_plate_with_hole.py",
    "poisson_compiled.py",
    "scalar_wave_SEM.py"
]

cpp_examples = [
    "fichera_corner",
#    "j2_pressurized_sphere_fcm",
    "linear_elastic_fcm_stl ../stl.stl",
    "travelling_heat_source",
    "waveequation_matrix_free",
    "wing_elastic_fcm"
]

# Do some initial checks first
try:
    import numba
    import gmshparser
    import numpy
    import scipy

except ImportError as e:
    print("Error: Missing packages.")
    raise e

if len(cpp_examples):
    testpath = cpp_path + cpp_examples[0]
    if not os.path.exists(testpath) and not os.path.exists(testpath + ".exe"):
        raise ValueError(f"Unable open {cpp_path + cpp_examples[0]}.")

# Run examples
py_count = 0
py_total = len(python_examples)

cpp_count = 0
cpp_total = len(cpp_examples)

separator = "----------------------------"
print(f"Running {py_total} python and {cpp_total} C++ examples.")

for example in python_examples:
    print(f"{separator}\nRunning: {example}\n")

    if example == "interactive_eigenmodes.py":
        try:
            import matplotlib.pyplot
            print("Reminder: Use right click to close interactive_eigenmodes.")
            
        except ImportError:
            print("Skipping interactive_eigenmodes since matplotlib is not available.")
            py_total -= 1
            continue

    args = example.split(' ')
    result = subprocess.call([python, py_path + args[0]] + args[1:])
    py_count += result == 0    

    print("\n" + "Ok." if result == 0 else "Fail.")

print(f"\n{separator}\n\nPython: {py_count} successful with {py_total - py_count} errors.\n")

for example in cpp_examples:
    print(f"{separator}\nRunning: {example}\n")
    args = example.split(' ')
    result = subprocess.call([cpp_path + args[0]] + args[1:])
    cpp_count += result == 0

    print("\n" + "Ok." if result == 0 else "Fail.")

py_errors = py_total - py_count
cpp_errors = cpp_total - cpp_count

print(f"\n{separator}\n")
print(f"Python: {py_count} successful with {py_errors} errors.")
print(f"C++: {cpp_count} successful with {cpp_errors} errors.")
print("\n" + "Ok." if (py_errors + cpp_errors == 0) else "Fail.")
