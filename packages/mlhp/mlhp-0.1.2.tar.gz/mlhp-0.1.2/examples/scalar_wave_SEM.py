import mlhp
import time
import numpy as np

# Largest eigenvalue scales quadratically for high p, but to get a better 
# estimate we interpolate lambda_max with a fourth order polynomial
def critical_time_step(h, p):
    if p == 1:
        return h / c
    else:
        fit1D = [0.405285, 0.810616, 1.067388, 0.777045, 5.818442]
        fitND = [0.405270, 0.812248, 1.006601, 1.700265, -8.513121]
        fit = { 1: fit1D, 2: fitND, 3: fitND }
        lambda_p = np.polyval(fit[D], p) if (D != 2 or p != 2) else 14.4
        return h / c * 2 / float(np.sqrt(D * lambda_p))
        
D = 2

print("1. Preprocessing", flush=True)

nelements = [20] * D
lengths = [0.1] * D
p = 5
rho = 8000
c = 6000
duration = 2 * max(lengths) / c
u0 = mlhp.scalarField(D, 0.0)

# Time step
hmin = min(l / n for l, n in zip(lengths, nelements))
dt = 0.7 * critical_time_step(hmin, p)
time_steps = int(np.ceil(duration / dt))
resultInterval = max(time_steps // 90, 1)

print(f"T = {duration*1e6:.6g} us")
print(f"dt = {dt*1e9:.6g} ns")
print(f"{time_steps} time steps")

# Source function (Ricklers wavelet)
frequency = 0.5 * 1e6
t0 = 1 / frequency
sigmaT = 1 / (2 * np.pi * frequency)
sigmaS = 1 * hmin

r2 = " + ".join(f"xyz[{i}]" for i in range(D))
ft = lambda t : -(t - t0) / (np.sqrt(2 * np.pi) * sigmaT**3) * np.exp(-(t - t0)**2 / (2 * sigmaT**2))
fx = mlhp.scalarField(D, f"{10} * exp( -({r2}) / (2 * {sigmaS}**2))")

# Create Cartesian grid with Lagrange shape functions interpolating Gauss Lobatto points
mesh = mlhp.makeRefinedGrid(nelements, lengths=lengths)
basis = mlhp.makeHpTensorSpace(mesh, degree=p)
basis.setPolynomialBases([mlhp.gaussLobattoLagrangePolynomials(degree=p)] * D)

print(basis)

print("2. Assembly", flush=True)

M = mlhp.allocateSparseMatrix(basis)
K = M.copy()
F = mlhp.allocateRhsVector(M)

quadrature1 = mlhp.standardQuadrature(D, rule=mlhp.gaussLobattoRule())

integrand1 = mlhp.l2DomainIntegrand(mass=mlhp.scalarField(D, rho), rhs=None)
integrand2 = mlhp.poissonIntegrand(mlhp.scalarField(D, rho * c**2), fx)

mlhp.integrateOnDomain(basis, integrand1, [M], quadrature=quadrature1)
mlhp.integrateOnDomain(basis, integrand2, [K, F])

# Since mass matrix is diagonal, we can extract its diagonal and invert it
invM = dt**2 / np.array([M(i, i) for i in range(M.shape[0])])

# Project initial condition and set initial velocity to zero by setting u1 = u0
dofs0 = mlhp.projectOnto(basis, u0)
dofs1 = dofs0.copy()

print("3. Time integration", flush=True)
checkpoint1 = time.time()

results = [dofs1.copy()]

# Temporary storage
dofs2, finternal = tuple(mlhp.DoubleVector(dofs0.size) for _ in range(2))

# Time integration (progress printing may reduce throughput)
for i in range(time_steps):
    print(f"\rTime step {i + 1} / {time_steps}", flush=True, end='')
    
    K.multiply(dofs1, out=finternal)
    
    dofs2.array[:] = 2 * dofs1.array - dofs0.array + invM * (F.array * ft(i * dt) - finternal.array)
    
    results += [] if i % resultInterval else [dofs2.copy()]
    dofs0, dofs1, dofs2 = dofs1, dofs2, dofs0

print(f" (took {time.time() - checkpoint1:.2f}s)")
print(f"Throughput: {dofs0.size * time_steps / (time.time() - checkpoint1):.2e} dofs/s", flush=True)

print("4. Postprocessing", flush=True)

# Postprocess
if D < 3:
    try:
        mplAvailable = True
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation
    except ImportError:
        mplAvailable = False
        print("Matplotlib not available.")

    umin, umax = min(np.min(dofs.array) for dofs in results), max(np.max(dofs.array) for dofs in results)
    
    def mesh_ticks(axis):
        return np.linspace(0, lengths[axis], nelements[axis] * p + 1)

if D == 1 and mplAvailable:
    def animate(i):
        ax.clear()
        x = mesh_ticks(0)
        u = mlhp.scalarEvaluator(basis, results[i])(x)
        ax.plot(x, u)
        ax.plot(x[::p], u[::p], 'x')
        ax.set_ylim([umin - 0.05 * (umax - umin), umax + 0.05 * (umax - umin)])
    
    fig, ax = plt.subplots()
    anim = animation.FuncAnimation(fig, animate, len(results), interval=20)
    plt.show()

if D == 2 and mplAvailable:
    def animate(i):
        ax.clear()
        Z = np.reshape(mlhp.scalarEvaluator(basis, results[i])(X.ravel(), Y.ravel()), X.shape)
        ax.contourf(X, Y, Z, levels=np.linspace(-limit, limit, 32), cmap='seismic', extend='both')
        ax.add_collection(lines)
            
    fig, ax = plt.subplots()
    X, Y = np.meshgrid(mesh_ticks(0), mesh_ticks(1), indexing='ij')
    limit = 0.2 * max(abs(umin), abs(umax))
    lines = mesh.skeletonMesh().lineCollection()
    ax.set_aspect('equal', adjustable='box')
    anim = animation.FuncAnimation(fig, animate, len(results), interval=0)
    plt.show()

if D == 3:
    for i, u in enumerate(results):
        processors = [mlhp.solutionProcessor(D, u, "Solution")]
        gridmesh = mlhp.gridCellMesh([p + 1 if p > 1 else 1] * D)
        gridoutput = mlhp.PVtuOutput(filename=f"outputs/scalar_wave_{i}")
        mlhp.basisOutput(basis, gridmesh, gridoutput, processors)

# Check consistency with previous result
assert(abs(mlhp.norm(dofs1) - 5.6633689e-08) < 1e-14)
