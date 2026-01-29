import dolfinx as dfx
import matplotlib.pyplot as plt
from basix.ufl import element
from data import detection_levelset
from meshtagsplot import plot_mesh_tags
from mpi4py import MPI

from src.phifem.mesh_scripts import compute_tags_measures

# N = 100
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
# with XDMFFile(comm, "mesh.xdmf", "r") as fi:
#     mesh = fi.read_mesh()

bbox = [[-4.5, -4.5], [4.5, 4.5]]
mesh = dfx.mesh.create_rectangle(
    comm, bbox, [4, 4], ghost_mode=dfx.cpp.mesh.GhostMode.shared_facet
)

cell_name = mesh.topology.cell_name()
cg1_element = element("Lagrange", cell_name, 1)

cg1_space = dfx.fem.functionspace(mesh, cg1_element)

detection_levelset_h = dfx.fem.Function(cg1_space)
detection_levelset_h.interpolate(detection_levelset)

cells_tags, facets_tags, _, _, _, _ = compute_tags_measures(
    mesh, detection_levelset_h, 1, box_mode=True
)

fig = plt.figure()
ax = fig.subplots()
plot_mesh_tags(mesh, cells_tags, ax, expression_levelset=detection_levelset)
plt.savefig(
    f"cells_tags_rank_{str(comm.rank).zfill(2)}.png", dpi=300, bbox_inches="tight"
)
fig = plt.figure()
ax = fig.subplots()
plot_mesh_tags(
    mesh, facets_tags, ax, expression_levelset=detection_levelset, linewidth=3.0
)
ax.set_frame_on(False)
ax.set_xticklabels([])
ax.set_xticks([])
ax.set_yticklabels([])
ax.set_yticks([])
plt.savefig(
    f"facets_tags_rank_{str(comm.rank).zfill(2)}.png", dpi=300, bbox_inches="tight"
)
# mesh = dfx.mesh.create_unit_square(
#     comm, N, N, ghost_mode=dfx.cpp.mesh.GhostMode.shared_facet
# )

"""
start = MPI.Wtime()

print(
    f"Local num dofs (rank {comm.rank}):",
    len(
        dfx.fem.locate_dofs_geometrical(cg1_space, lambda x: np.full(x.shape[1], True))
    ),
)
end = MPI.Wtime()
local_time = end - start
global_time = comm.reduce(local_time, op=MPI.MAX, root=0)
if comm.rank == 0:
    times["Space creation"][0] = global_time

fh = dfx.fem.Constant(mesh, dfx.default_scalar_type(1.0))

u = ufl.TrialFunction(cg1_space)
v = ufl.TestFunction(cg1_space)

a = ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx
L = ufl.inner(fh, v) * ufl.dx

u_dbc = dfx.fem.Function(cg1_space)
tdim = mesh.topology.dim
facets = dfx.mesh.locate_entities_boundary(
    mesh, tdim - 1, lambda x: np.full(x.shape[1], True)
)
dofs = dfx.fem.locate_dofs_topological(cg1_space, tdim - 1, facets)
bcs = [dfx.fem.dirichletbc(u_dbc, dofs)]

bilinear_form = dfx.fem.form(a)

start = MPI.Wtime()
A = assemble_matrix(bilinear_form, bcs=bcs)
A.assemble()
end = MPI.Wtime()
local_time = end - start
global_time = comm.reduce(local_time, op=MPI.MAX, root=0)
if comm.rank == 0:
    times["Matrix assembly"][0] = global_time
linear_form = dfx.fem.form(L)

start = MPI.Wtime()
b = dfx.fem.Function(cg1_space)
b = assemble_vector(linear_form)
end = MPI.Wtime()
local_time = end - start
global_time = comm.reduce(local_time, op=MPI.MAX, root=0)
if comm.rank == 0:
    times["Vector assembly"][0] = global_time
dfx.fem.apply_lifting(b, [bilinear_form], [bcs])
start = MPI.Wtime()
b.ghostUpdate(addv=PETSc.InsertMode.ADD_VALUES, mode=PETSc.ScatterMode.REVERSE)
end = MPI.Wtime()
local_time = end - start
global_time = comm.reduce(local_time, op=MPI.MAX, root=0)
if comm.rank == 0:
    times["Vector ghost update"][0] = global_time
dfx.fem.set_bc(b, bcs)

ksp = PETSc.KSP().create(mesh.comm)
ksp.setOperators(A)
ksp.setType("cg")

pc = ksp.getPC()
pc.setType("hypre")
pc.setFactorSolverType("mumps")

uh = dfx.fem.Function(cg1_space)
start = MPI.Wtime()
ksp.solve(b, uh.x.petsc_vec)
end = MPI.Wtime()
local_time = end - start
global_time = comm.reduce(local_time, op=MPI.MAX, root=0)
if comm.rank == 0:
    times["Solve"][0] = global_time

start = MPI.Wtime()
uh.x.scatter_forward()
end = MPI.Wtime()
local_time = end - start
global_time = comm.reduce(local_time, op=MPI.MAX, root=0)
if comm.rank == 0:
    times["Solution scatter forward"][0] = global_time

start = MPI.Wtime()
with XDMFFile(mesh.comm, os.path.join("solution.xdmf"), "w") as of:
    of.write_mesh(mesh)
    of.write_function(uh)
end = MPI.Wtime()
local_time = end - start
global_time = comm.reduce(local_time, op=MPI.MAX, root=0)
if comm.rank == 0:
    times["XDMF save"][0] = global_time

    times["Total"][0] = sum([it[0] for it in times.values()])
    for key in times.keys():
        times[key][1] = 100 * times[key][0] / times["Total"][0]
    df = pl.DataFrame(times)
    with pl.Config(fmt_str_lengths=1000, tbl_width_chars=1000, tbl_cols=-1):
        print(df)
"""
