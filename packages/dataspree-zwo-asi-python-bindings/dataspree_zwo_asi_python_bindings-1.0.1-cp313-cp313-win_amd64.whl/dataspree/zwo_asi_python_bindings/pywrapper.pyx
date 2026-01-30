"""
cimport dataspree.zwo_asi_python_bindings.cwrapper as cwrapper

# Define a Python-exposed wrapper for the C function
def py_add(int a, int b):
    ""Python wrapper for the C 'add' function""
    return cwrapper.add(a, b)

"""