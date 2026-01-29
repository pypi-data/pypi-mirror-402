import dolfinx as dfx
import mpi4py.MPI as MPI
from dolfinx.io import XDMFFile

N = 100
comm = MPI.COMM_WORLD

mesh = dfx.mesh.create_unit_square(
    comm, N, N, ghost_mode=dfx.cpp.mesh.GhostMode.shared_facet
)

with XDMFFile(mesh.comm, "small_mesh.xdmf", "w") as of:
    of.write_mesh(mesh)
