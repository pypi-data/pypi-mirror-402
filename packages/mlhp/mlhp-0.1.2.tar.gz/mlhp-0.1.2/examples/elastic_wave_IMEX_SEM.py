import mlhp
import time
import scipy.sparse
import scipy.sparse.linalg
import numpy as np

# This example demonstrates how to use nodal lumping (naturally 
# leading to a diagonal mass matrix) for explicit time integration of
# uncut elements and an implicit Newmark scheme for cut elements.
# 
# The setup is an immersed beam that is clamped on one side. The 
# initial condition is obtained from a linear elastic computation
# where force is applied to the free end of the beam. When removing
# this force in the subsequent dynamic simulation, the beam starts 
# oscillating back and forth.

# Largest eigenvalue scales quadratically for high p, but to get a better 
# estimate we interpolate lambda_max with a fourth order polynomial
def critical_time_step(h, p, wave_speed):
    if p == 1:
        return h / wave_speed
    else:
        fitND = [0.405270, 0.812248, 1.006601, 1.700265, -8.513121]
        lambda_p = np.polyval(fitND, p) if (D != 2 or p != 2) else 14.4
        return h / wave_speed * 2 / float(np.sqrt(D * lambda_p))
        
# Number of space dimensions (2 or 3)
D = 2

print("1. Preprocessing", flush=True)

# Background finite element mesh and finite cell parameters
nelements = [100] * D
lengths = [0.1] * D
origin = [-l/2 for l in lengths]
p = 1
filter = True
alpha = 1e-6
depth = p + 2

# Material parameters and initial condition
rho = 8000
c = 1000
E = rho * c**2
nu = 0.25
dirichletPenalty = 1e3 * E

u0 = mlhp.vectorField(D, f"[0.001 * x, 0]")

# Spatial and temporal component of body force
ft = lambda t : 0.0
fx = mlhp.vectorField(D, [0.0] * D)

# Time stepping with Newmark parameters
duration = 100 * max(lengths) / c
hmin = min(l / n for l, n in zip(lengths, nelements))
dt = 0.8 * critical_time_step(hmin, p, c)
time_steps = int(np.ceil(duration / dt))

beta = 1 / 4
gamma = 1 / 2

# Define physical domain as rotated rectangle in 2D or cylinder in 3D
base = mlhp.implicitSphere([0.0] * (D - 1), max(lengths[:-1]) / 32)
domainHeights = [0.8 * origin[-1], 0.8 * (origin[-1] + lengths[-1])]
cylinder = mlhp.extrude(base, axis=D - 1, minValue=domainHeights[0], maxValue=domainHeights[1])
phi = 50 * np.pi / 180
rotation = mlhp.rotation(phi) if D == 2 else mlhp.rotation([1] + [0] * (D - 1), phi)
domain = mlhp.implicitTransformation(cylinder, rotation)

print(f"T = {duration*1e6:.6g} us")
print(f"dt = {dt*1e9:.6g} ns")
print(f"{time_steps} time steps")

# Number of time steps after which the solution is stored for postprocessing
resultInterval = max(time_steps // 90, 1)

# Create Cartesian background and find out which cells are outside, cut, or inside
grid = mlhp.makeGrid(nelements, lengths=lengths, origin=origin)

quadrature = mlhp.spaceTreeQuadrature(domain, depth=depth, epsilon=0.0, rule=mlhp.gaussLobattoRule())
measures = [sum(sum(p.weights) for p in quadrature.evaluate(grid, i, [p + 1] * D)) for i in range(grid.ncells())]
full_cell = np.prod(np.divide(lengths, nelements))
cutstate = np.array([1 if abs(m - full_cell) < 1e-10 * full_cell else (-1 if m == 0.0 else 0) for m in measures])

# Recover domain bounary (triangulation + associated elements) and extract Dirichlet cells
def extractBoundaryFace(boundary, height):
    faceBounds0 = [-1e50] * (D - 1) + [height - 1e-4 * lengths[-1]]
    faceBounds1 = [+1e50] * (D - 1) + [height + 1e-4 * lengths[-1]]
    faceFilter = mlhp.implicitTransformation(mlhp.implicitCube(faceBounds0, faceBounds1), rotation)
    return boundary[0].filter(faceFilter, celldata=boundary[1])
    
boundary = mlhp.recoverDomainBoundary(grid, domain, [p + 2] * D)

face0 = extractBoundaryFace(boundary, domainHeights[0])

# Set cells to cut if they contain part of the Dirichlet boundary
cutstate[face0[1].meshSupport()] = 0

# Filter outside cells and create basis with Lagrange shape functions interpolating Gauss Lobatto points
if filter:
    grid = mlhp.makeFilteredGrid(grid, cutstate=cutstate)
    cutstate = cutstate[cutstate >= 0]

mesh = mlhp.makeRefinedGrid(grid)
basis = mlhp.makeHpTensorSpace(mesh, degree=p, nfields=D)
basis.setPolynomialBases([mlhp.gaussLobattoLagrangePolynomials(degree=p)] * D)

# Repeat boundary recovery on filtered mesh and extract two faces for Dirichlet and traction BCs
boundary = mlhp.recoverDomainBoundary(mesh, domain, [p + 2] * D)

face0 = extractBoundaryFace(boundary, domainHeights[0])
face1 = extractBoundaryFace(boundary, domainHeights[1])

print(basis, flush=True)

# Split dof indices in those belonging to shape functions supported on at least one 
# cut element and those that are only supported by uncut elements
cut = np.array(mlhp.findSupportedDofs(basis, np.where(cutstate == 0)[0]))
uncut = np.delete(np.arange(basis.ndof()), cut) if len(cut) else np.arange(basis.ndof())

print(f"{len(cut)} cut dofs")
print(f"{len(uncut)} uncut dofs")

print("2. Assembly", flush=True)

M = mlhp.allocateSparseMatrix(basis)
K = M.copy()
F = mlhp.allocateRhsVector(M)
B = mlhp.allocateRhsVector(M)

# Assemble domain integrals
quadrature1 = mlhp.spaceTreeQuadrature(domain, depth=depth, epsilon=alpha, rule=mlhp.gaussLobattoRule())
quadrature2 = mlhp.spaceTreeQuadrature(domain, depth=depth, epsilon=alpha, rule=mlhp.gaussLegendreRule())

makeMaterial = mlhp.planeStrainMaterial if D == 2 else mlhp.isotropicElasticMaterial

kinematics = mlhp.smallStrainKinematics(D)
material = makeMaterial(mlhp.scalarField(D, E), mlhp.scalarField(D, nu))

integrand1 = mlhp.l2DomainIntegrand(mass=mlhp.vectorField(D, [rho]*D), rhs=None)
integrand2 = mlhp.staticDomainIntegrand(kinematics, material, fx)

mlhp.integrateOnDomain(basis, integrand1, [M], quadrature=quadrature1)
mlhp.integrateOnDomain(basis, integrand2, [K, F], quadrature=quadrature2)

# Assemble boundary integrals
face0Quadrature = mlhp.simplexQuadrature(*face0)
face0PenaltyFunction = mlhp.vectorField(D, [dirichletPenalty] * D)
face0Integrand = mlhp.l2BoundaryIntegrand(face0PenaltyFunction, mlhp.vectorField(D, [0.0] * D))

mlhp.integrateOnSurface(basis, face0Integrand, [K, B], face0Quadrature)

# Since mass matrix is diagonal, we can extract its diagonal and invert it
M_uncut_inv = dt**2 / np.array([M(i, i) for i in uncut])

# Compute implicit Newmark matrix for cut block: S = M + dt**2 * beta * K
S_cut = M.extractBlock(cut, cut)
K_cut = K.extractBlock(cut, cut)
S_cut.data_array[:] += dt**2 * beta * K_cut.data_array[:]

K_uncut = K.extractBlock(uncut, range(basis.ndof()))
K_cut = K.extractBlock(cut, range(basis.ndof()))

# Assemble boundary integrals
B2 = B.copy()
face1Quadrature = mlhp.simplexQuadrature(*face1)
face1Integrand = mlhp.neumannIntegrand(mlhp.vectorField(D, rotation([1e6] + [0.0] * (D - 1))))

mlhp.integrateOnSurface(basis, face1Integrand, [B2], face1Quadrature)

print("3. Solve initial displacement", flush=True)

dofs0 = mlhp.cg(K, B2, M=mlhp.diagonalPreconditioner(K), maxiter=20000)
dofs1 = dofs0.copy()

del M, K

print("4. Time integration", flush=True)

# Compute sparse LU-decomposition of S
S_cut_inv = scipy.sparse.linalg.splu(scipy.sparse.csr_matrix(*S_cut.csr_arrays).tocsc())

#import mklwrapper as mkl
#S_cut_inv = mkl.pardisoFactorize(S_cut)
#S_cut_inv.solve = lambda rhs: np.array(S_cut_inv(mlhp.DoubleVector(rhs)))

checkpoint1 = time.time()
results = [dofs1.copy()]

# Temporary storage
dofs2 = mlhp.DoubleVector(dofs0.size)
f_cut = mlhp.DoubleVector(len(cut))
f_uncut = mlhp.DoubleVector(len(uncut))
u_c_dt = (dofs1.array[cut] - dofs0.array[cut]) / dt if len(cut) else dofs0.array[:]
u_c_ddt = np.zeros(len(cut))

# Time integration (progress printing may reduce throughput)
for i in range(time_steps):
    print(f"\rTime step {i + 1} / {time_steps}", flush=True, end='')
    
    # Explicit central difference step on uncut dofs
    K_uncut.multiply(dofs1, out=f_uncut)
    dofs2.array[uncut] = 2 * dofs1.array[uncut] - dofs0.array[uncut] + M_uncut_inv * (F.array[uncut] * ft(i * dt) - f_uncut.array)
    
    if(len(cut)):
        # Implicit Newmark predictor step on cut dofs
        dofs2.array[cut] = dofs1.array[cut] + dt * u_c_dt + (1/2 - beta) * dt**2 * u_c_ddt
        u_c_pred_dt = u_c_dt + (1 - gamma) * dt * u_c_ddt
        
        # Implicit Newmark acceleration on cut dofs
        K_cut.multiply(dofs2, out=f_cut)
        u_c_ddt = S_cut_inv.solve(F.array[cut] * ft(i * dt) - f_cut.array)
        
        # Implicit Newmark correction on cut dofs
        dofs2.array[cut] += beta * dt**2 * u_c_ddt
        u_c_dt = u_c_pred_dt + gamma * dt * u_c_ddt
        
    results += [] if i % resultInterval else [dofs2.copy()]
    dofs0, dofs1, dofs2 = dofs1, dofs2, dofs0

print(f" (took {time.time() - checkpoint1:.2f}s)")
print(f"Throughput: {dofs0.size * time_steps / (time.time() - checkpoint1):.2e} dofs/s", flush=True)

# ====================== Postprocessing ======================== 

def postprocess(dofs, output):
    processors = [mlhp.solutionProcessor(D, dofs, "Displacement"), 
                  mlhp.vonMisesProcessor(dofs, kinematics, material)]
    gridmesh = mlhp.domainCellMesh(domain, [p + (2 if p > 1 else 0)] * D)
    mlhp.basisOutput(basis, gridmesh, output, processors)
    return output
    
print("5. Postprocessing", flush=True)

# Animate using matplotlib
if D == 2:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation
        import matplotlib.collections as col

        warp_scaling = 0.3 * max(lengths) / max([max(np.abs(u.array)) for u in results])
        #lines0 = np.array(mesh.skeletonMesh().lineCollection(mpl=False))
        triangulations, lines, stresses, max_stress = [], [], [], 0.0
        
        for i, dofs in enumerate(results):
            print(f"\rEvaluating result {i + 1} / {len(results)}", flush=True, end='')
            output = postprocess(dofs, mlhp.DataAccumulator())
            triangulation, (u, vonmises) = output.triangulation(), output.data()
            triangulation.x += warp_scaling * np.reshape(u, (-1, D)).T[0]
            triangulation.y += warp_scaling * np.reshape(u, (-1, D)).T[1]
            
            triangulations.append(triangulation)
            stresses.append(np.array(vonmises))
            #linesN = mlhp.vectorEvaluator(basis, dofs)(lines0[..., 0].ravel(), lines0[..., 1].ravel())
            #lines.append(col.LineCollection(lines0 + warp_scaling * np.reshape(linesN, (-1, 2, 2)), colors="black"))
            max_stress = max(max_stress, max(stresses[-1]))
            
        print("")
        
        def animate(i):
            ax.clear()
            plt.tricontourf(triangulations[i], stresses[i], levels=np.linspace(0, 0.5*max_stress, 32), cmap='turbo', extend="both")
            #ax.add_collection(lines[i])
            ax.set_xlim([origin[0] - 0.05 * lengths[0], origin[0] + 1.05 * lengths[0]])
            ax.set_ylim([origin[1] - 0.05 * lengths[1], origin[1] + 1.05 * lengths[1]])
            
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_aspect('equal', adjustable='box')
        anim = animation.FuncAnimation(fig, animate, len(results), interval=0)
        plt.tight_layout()
        plt.show()
        
        #Writer = animation.writers['ffmpeg']
        #writer = Writer(fps=15, metadata=dict(artist='Me'), bitrate=1800)
        #anim.save('animation.mp4', writer=writer)

    except ImportError:
        print("Matplotlib not available.")

# Write vtu files for further postprocessing in Paraview
if D == 3:
    for i, u in enumerate(results):
        postprocess(u, mlhp.PVtuOutput(filename=f"outputs/elastic_wave_{i}"))

# Check consistency with previous result
#assert(abs(mlhp.norm(dofs1) - 5.6633689e-08) < 1e-14)
