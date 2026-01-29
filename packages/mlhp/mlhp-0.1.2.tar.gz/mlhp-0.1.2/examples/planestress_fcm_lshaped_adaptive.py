import mlhp
import math
import numpy as np
import scipy.sparse
import scipy.sparse.linalg
    
D = 2

print("1. Preprocessing", flush=True)

elementsize = 0.25
degree = 2
alpha = 1e-10
treedepth = degree + 7
nseedpoints = degree + 5
penalty = 1e16
rotate = 30 * math.pi / 180
maxiter = 12 # 100
plotIterations = True
plotConvergence = True

# Check if matplotlib is available 
if plotIterations or plotConvergence:
    try:
        import matplotlib.pyplot as plt
        from mpl_toolkits.axes_grid1 import make_axes_locatable
    except ImportError:
        print("Matplotlib import failed.")
        plotIterations, plotConvergence = False, False
        
# Prepare implicit function
rectangle1 = mlhp.implicitCube((0.0, 0.0), (0.5, 1.0))
rectangle2 = mlhp.implicitCube((0.0, 0.0), (1.0, 0.5))
Lshape = mlhp.implicitUnion([rectangle1, rectangle2])
rotation = mlhp.rotation(rotate)
domain = mlhp.implicitTransformation(Lshape, rotation)

# Boundary segments and domain bounding box
top = mlhp.lineSegments(rotation([(0.0, 1.0), (0.5, 1.0)]), [(0, 1)])
right = mlhp.lineSegments(rotation([(1.0, 0.0), (1.0, 0.5)]), [(0, 1)])

bounds0 = [min(v + (0.0, )) for v in zip(top.boundingBox()[0], right.boundingBox()[0])]
bounds1 = [max(v + (0.0, )) for v in zip(top.boundingBox()[1], right.boundingBox()[1])]

lengths = tuple(x1 - x0 for x0, x1 in zip(bounds0, bounds1))
nelements = tuple(max(int(round(dx / elementsize)), 1) for dx in lengths)

# Create base grid and filter based on sum of quadrature point weights (integrate 1)
baseGrid = mlhp.makeGrid(ncells=nelements, lengths=lengths, origin=bounds0)

quadrature0 = mlhp.momentFittingQuadrature(domain, depth=treedepth, epsilon=0.0, nseedpoints=nseedpoints) 

partitions = lambda icell: quadrature0.evaluate(baseGrid, icell, [degree + 1]*D)
mask = [sum([sum(p.weights) for p in partitions(icell)]) != 0 for icell in range(baseGrid.ncells())]
baseGrid = mlhp.makeFilteredGrid(baseGrid, mask=mask)

# Initialize stuff for refinement
refine = [0 for _ in range(baseGrid.ncells())]
mesh = mlhp.makeRefinedGrid(baseGrid)
iter, ndofs, energies, errors = 0, [], [], []

while (max(refine) > 0 and iter < maxiter) or iter == 0:
    iter, oldMesh = iter + 1, mesh
    mesh = mlhp.makeRefinedGrid(baseGrid)
    mesh.refine(mlhp.refineAdaptively(oldMesh, refine))
    basis = mlhp.makeHpTrunkSpace(mesh, degree=degree, nfields=D)

    print(basis)

    print("2. Assembly", flush=True)
    
    if rotate == 0:
        dirichletDofs = mlhp.integrateDirichletDofs(mlhp.vectorField(D, [0.0, 0.0]), basis, [3])
    else:
        dirichletDofs = [[], []]
        
    # Allocate linear system for internal dofs
    matrix = mlhp.allocateSparseMatrix(basis, dirichletDofs[0])
    vector = mlhp.allocateRhsVector(matrix)

    # Assemble domain contribution
    E = mlhp.scalarField(D, 206900 * 1e6)
    nu = mlhp.scalarField(D, 0.29)
    rhs = mlhp.vectorField(D, [0.0] * D)

    kinematics = mlhp.smallStrainKinematics(D) 
    constitutive = mlhp.planeStressMaterial(E, nu)
    domainIntegrand = mlhp.staticDomainIntegrand(kinematics, constitutive, rhs)

    #quadrature = mlhp.spaceTreeQuadrature(domain, depth=treedepth, epsilon=alpha)
    quadrature = mlhp.momentFittingQuadrature(domain, depth=treedepth, epsilon=alpha, nseedpoints=nseedpoints) 
    
    mlhp.integrateOnDomain(basis, domainIntegrand, [matrix, vector], quadrature=quadrature, dirichletDofs=dirichletDofs)

    # Assemble weak boundary and traction integral
    traction = rotation((0.0, 100 * 1e6))
    
    quadratureClamp = mlhp.simplexQuadrature(*mlhp.intersectWithMesh(top, mesh))
    quadratureForce = mlhp.simplexQuadrature(*mlhp.intersectWithMesh(right, mesh))
    
    clampIntegrand = mlhp.l2BoundaryIntegrand(mlhp.vectorField(D, [penalty] * D), mlhp.vectorField(D, [0.0] * D))
    forceIntegrand = mlhp.neumannIntegrand(mlhp.vectorField(D, traction))
    
    mlhp.integrateOnSurface(basis, forceIntegrand, [vector], quadratureForce, dirichletDofs=dirichletDofs)
    
    if rotate != 0:
        mlhp.integrateOnSurface(basis, clampIntegrand, [matrix, vector], quadratureClamp, dirichletDofs=dirichletDofs)

    print("3. Linear system solution", flush=True)
    internalDofs = mlhp.DoubleVector(scipy.sparse.linalg.spsolve(scipy.sparse.csr_matrix(*matrix.csr_arrays), vector.array))
    
    ##M = mlhp.additiveSchwarzPreconditioner(matrix, basis, dirichletDofs=dirichletDofs[0])
    #M = mlhp.diagonalPreconditioner(matrix)
    #internalDofs = mlhp.cg(matrix, vector, rtol=1e-12, maxiter=100000, M=M)
    allDofs = mlhp.inflateDofs(internalDofs, dirichletDofs)
    
    print("4. Error integration", flush=True)

    # Compute error indicator and relative refinement levels (-1 -> coarsen, 0 -> keep, 1 -> refine)
    error = mlhp.stressJumpIndicator(basis, allDofs, kinematics, constitutive, 
        scaling=domain.asfield(), order=mlhp.relativeQuadratureOrder(D, 4))
    minE, maxE = min(error), max(error)
    
    #refine = [(e > minE + 0.8 * (maxE - minE)) - (e < minE + 0.0 * (maxE - minE)) for e in error]
    refine = [e > 0.5 * maxE for e in error]
    
    internalEnergy = mlhp.ScalarDouble(0.0)
    energyIntegrand = mlhp.internalEnergyIntegrand(allDofs, kinematics, constitutive)
    mlhp.integrateOnDomain(basis, energyIntegrand, [internalEnergy], quadrature=quadrature0)

    print("5. File output", flush=True)

    processors = [mlhp.solutionProcessor(D, allDofs, "Displacement"),
                  mlhp.vonMisesProcessor(allDofs, kinematics, constitutive),
                  mlhp.cellIndexProcessor(D),
                  mlhp.functionProcessor(domain)]

    gridmesh = mlhp.domainCellMesh(domain, [degree + 4] * D)
    # gridoutput = mlhp.PVtuOutput(filename="outputs/planestress_fcm_plate")
    # mlhp.basisOutput(basis, gridmesh, gridoutput, processors)

    if plotIterations:
        print("6. Plotting", flush=True)
        
        result = mlhp.DataAccumulator()
        mlhp.basisOutput(basis, gridmesh, result, processors)
        
        height = 15 / (2 * lengths[0]) * lengths[1] + 1
        fig, ax = plt.subplots(1, 2, figsize=(15, height))
        
        im1 = ax[0].tricontourf(result.triangulation(), result.data()[1], vmax=1e9, vmin=0, 
            levels=np.linspace(0.0, 1e9, 20), cmap='turbo', extend='max')
            
        im2 = ax[1].tricontourf(result.triangulation(), [error[int(i)] for i in result.data()[2]])
        
        mesh.plot(show=False, axis=ax[0])
        mesh.plot(show=False, axis=ax[1])
        
        ax[0].set_axis_off()
        ax[1].set_axis_off()
    
        cax0 = make_axes_locatable(ax[0]).append_axes("bottom", size="5%", pad=0.3)
        cax1 = make_axes_locatable(ax[1]).append_axes("bottom", size="5%", pad=0.3)
    
        plt.colorbar(im1, cax=cax0, label="Von Mises Stress", orientation="horizontal")
        plt.colorbar(im2, cax=cax1, label="Error indicator", orientation="horizontal")
        
        plt.tight_layout()
        plt.show()
            
    overkillEnergy2 = 293047.2648067
    relativeError = math.sqrt(abs(internalEnergy.get() - overkillEnergy2) / overkillEnergy2)
    ndofs.append(len(allDofs))
    energies.append(internalEnergy.get())
    errors.append(relativeError)
    
    print(f"{ndofs = }")
    print(f"{energies = }")
    print(f"{errors = }")
    
if plotConvergence:
    plt.loglog(np.sqrt(ndofs), 100 * np.array(errors), "x-", label=f"p = {degree}")
    plt.legend()
    plt.show()
     
# Consistency check
assert(ndofs[3] == 328)
assert(abs(errors[3] - 0.159241866) < 1e-4)
