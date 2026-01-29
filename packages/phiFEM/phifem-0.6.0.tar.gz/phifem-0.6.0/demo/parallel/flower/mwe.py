import os

import dolfinx as dfx
import numpy as np
import petsc4py.PETSc as PETSc
import polars as pl
import ufl
from basix.ufl import element
from dolfinx.fem.petsc import assemble_matrix, assemble_vector
from dolfinx.io import XDMFFile
from mpi4py import MPI

N = 100
comm = MPI.COMM_WORLD

if comm.rank == 0:
    times = {
        "Space creation": [0, 0],
        "Matrix assembly": [0, 0],
        "Vector assembly": [0, 0],
        "Vector ghost update": [0, 0],
        "Solve": [0, 0],
        "Solution scatter forward": [0, 0],
        "XDMF save": [0, 0],
        "Total": [0, 0],
    }

mesh = dfx.mesh.create_unit_square(
    comm, N, N, ghost_mode=dfx.cpp.mesh.GhostMode.shared_facet
)
cell_name = mesh.topology.cell_name()
cg1_element = element("Lagrange", cell_name, 1)

start = MPI.Wtime()
cg1_space = dfx.fem.functionspace(mesh, cg1_element)
print(
    f"Local num dofs (rank {comm.rank}):",
    len(
        dfx.fem.locate_dofs_geometrical(cg1_space, lambda x: np.full(x.shape[1], True))
    ),
)
end = MPI.Wtime()
local_time = end - start
if comm.rank == 0:
    times["Space creation"][0] = (
        local_time  # comm.reduce(local_time, op=MPI.MAX, root=0)
    )
