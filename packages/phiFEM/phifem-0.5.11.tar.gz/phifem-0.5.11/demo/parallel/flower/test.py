import os
import time

import dolfinx as dfx
import numpy as np
import petsc4py.PETSc as PETSc
import polars as pl
import ufl
from basix.ufl import element
from dolfinx.fem.petsc import assemble_matrix, assemble_vector
from dolfinx.io import XDMFFile
from mpi4py import MPI

N = 2500
comm = MPI.COMM_WORLD
mesh = dfx.mesh.create_unit_square(comm, N, N, ghost_mode=dfx.cpp.mesh.GhostMode.none)
cell_name = mesh.topology.cell_name()
cg1_element = element("Lagrange", cell_name, 1)

cg1_space = dfx.fem.functionspace(mesh, cg1_element)

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

A = assemble_matrix(bilinear_form, bcs=bcs)
A.assemble()
linear_form = dfx.fem.form(L)

b = dfx.fem.Function(cg1_space)
b = assemble_vector(linear_form)
dfx.fem.apply_lifting(b, [bilinear_form], [bcs])
b.ghostUpdate(addv=PETSc.InsertMode.ADD_VALUES, mode=PETSc.ScatterMode.REVERSE)
dfx.fem.set_bc(b, bcs)

ksp = PETSc.KSP().create(mesh.comm)
ksp.setOperators(A)
ksp.setType("preonly")

pc = ksp.getPC()
pc.setType("lu")
pc.setFactorSolverType("mumps")

uh = dfx.fem.Function(cg1_space)
ksp.solve(b, uh.x.petsc_vec)
ksp.destroy()

uh.x.scatter_forward()

with XDMFFile(mesh.comm, os.path.join("solution.xdmf"), "w") as of:
    of.write_mesh(mesh)
