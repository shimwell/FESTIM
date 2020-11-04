# Unit tests formulation
import FESTIM
from FESTIM.formulations import formulation, formulation_extrinsic_traps
import fenics
import pytest
import sympy as sp
from ufl.core.multiindex import Index

k_B = FESTIM.k_B


def test_formulation_no_trap_1_material():
    '''
    Test function formulation() with 0 intrinsic trap
    and 1 material
    '''
    Index._globalcount = 8
    dt = 1
    parameters = {
        "materials": [{
            "alpha": 1,
            "beta": 2,
            "borders": [0, 1],
            "E_D": 4,
            "D_0": 5,
            "id": 1
            }],
        "traps": [],
        "source_term": {"value": "1"},
    }
    extrinsic_traps = []
    mesh = fenics.UnitIntervalMesh(10)
    V = fenics.VectorFunctionSpace(mesh, 'P', 1, 1)
    u = fenics.Function(V)
    u_n = fenics.Function(V)
    v = fenics.TestFunction(V)

    mf = fenics.MeshFunction('size_t', mesh, 1, 1)
    dx = fenics.dx(subdomain_data=mf)
    temp = fenics.Expression("300", degree=0)

    F, expressions = formulation(
        parameters, extrinsic_traps, u, v,
        u_n, dt, dx, temp, transient=True)

    solutions = list(fenics.split(u))
    previous_solutions = list(fenics.split(u_n))
    testfunctions = list(fenics.split(v))
    Index._globalcount = 8
    flux_ = expressions[0]
    expected_form = ((solutions[0] - previous_solutions[0]) / dt) * \
        testfunctions[0]*dx(1)
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(solutions[0]),
        fenics.grad(testfunctions[0]))*dx(1)
    expected_form += -flux_*testfunctions[0]*dx

    assert expected_form.equals(F) is True


def test_formulation_1_trap_1_material():
    '''
    Test function formulation() with 1 intrinsic trap
    and 1 material
    '''
    Index._globalcount = 8
    dt = 1
    parameters = {
        "traps": [{
            "k_0": 1,
            "E_k": 2,
            "p_0": 3,
            "E_p": 4,
            "density": 2,
            "materials": [1]
            }],
        "materials": [{
            "borders": [0, 1],
            "E_D": 4,
            "D_0": 5,
            "id": 1
            }],
        "source_term": {"value": 1},
    }
    extrinsic_traps = []
    mesh = fenics.UnitIntervalMesh(10)
    V = fenics.VectorFunctionSpace(mesh, 'P', 1, 2)
    u = fenics.Function(V)
    u_n = fenics.Function(V)
    v = fenics.TestFunction(V)

    solutions = list(fenics.split(u))
    previous_solutions = list(fenics.split(u_n))
    testfunctions = list(fenics.split(v))

    mf = fenics.MeshFunction('size_t', mesh, 1, 1)
    dx = fenics.dx(subdomain_data=mf)
    temp = fenics.Expression("300", degree=0)
    F, expressions = formulation(
        parameters, extrinsic_traps, u,
        v, u_n, dt, dx, temp, transient=True)
    flux_ = expressions[0]
    Index._globalcount = 8
    # take density Expression() from formulation()
    density = expressions[2]
    expected_form = ((solutions[0] - previous_solutions[0]) / dt) * \
        testfunctions[0]*dx(1)
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(solutions[0]),
        fenics.grad(testfunctions[0]))*dx(1)
    expected_form += -flux_*testfunctions[0]*dx + \
        ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[1]*dx
    expected_form += - 1 * fenics.exp(-2/k_B/temp) * \
        solutions[0] * (density - solutions[1]) * \
        testfunctions[1]*dx(1)
    expected_form += 3*fenics.exp(-4/k_B/temp)*solutions[1] * \
        testfunctions[1]*dx(1)
    expected_form += ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[0]*dx
    assert expected_form.equals(F) is True


def test_formulation_2_traps_1_material():
    '''
    Test function formulation() with 2 intrinsic traps
    and 1 material
    '''
    Index._globalcount = 8
    # Set parameters
    dt = 1
    extrinsic_traps = []
    parameters = {
        "traps": [{
            "k_0": 1,
            "E_k": 2,
            "p_0": 3,
            "E_p": 4,
            "density": 2 + FESTIM.x,
            "materials": [1]
            },
            {
            "k_0": 1,
            "E_k": 2,
            "p_0": 3,
            "E_p": 4,
            "density": 3,
            "materials": [1]
            }],
        "materials": [{
            "borders": [0, 1],
            "E_D": 4,
            "D_0": 5,
            "id": 1
            }],
        "source_term": {"value": 1},
    }
    # Prepare
    mesh = fenics.UnitIntervalMesh(10)
    V = fenics.VectorFunctionSpace(mesh, 'P', 1, len(parameters["traps"])+1)
    u = fenics.Function(V)
    u_n = fenics.Function(V)
    v = fenics.TestFunction(V)

    solutions = list(fenics.split(u))
    previous_solutions = list(fenics.split(u_n))
    testfunctions = list(fenics.split(v))

    mf = fenics.MeshFunction('size_t', mesh, 1, 1)
    dx = fenics.dx(subdomain_data=mf)
    temp = fenics.Expression("300", degree=0)

    F, expressions = formulation(
        parameters, extrinsic_traps, u, v,
        u_n, dt, dx, temp, transient=True)
    flux_ = expressions[0]

    Index._globalcount = 8
    # Densities from formulation()
    density1 = expressions[2]
    density2 = expressions[3]
    # Transient sol
    expected_form = ((solutions[0] - previous_solutions[0]) / dt) * \
        testfunctions[0]*dx(1)
    # Diffusion sol
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(solutions[0]),
        fenics.grad(testfunctions[0]))*dx(1)
    # Source sol
    expected_form += -flux_*testfunctions[0]*dx
    # Transient trap 1
    expected_form += ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[1]*dx
    # Trapping trap 1
    expected_form += - 1 * fenics.exp(-2/k_B/temp) * \
        solutions[0] * (density1 - solutions[1]) * \
        testfunctions[1]*dx(1)
    # Detrapping trap 1
    expected_form += 3*fenics.exp(-4/k_B/temp)*solutions[1] * \
        testfunctions[1]*dx(1)
    # Source detrapping sol
    expected_form += ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[0]*dx

    # Transient trap 2
    expected_form += ((solutions[2] - previous_solutions[2]) / dt) * \
        testfunctions[2]*dx
    # Trapping trap 2
    expected_form += - 1 * fenics.exp(-2/k_B/temp) * \
        solutions[0] * (density2 - solutions[2]) * \
        testfunctions[2]*dx(1)
    # Detrapping trap 2
    expected_form += 3*fenics.exp(-4/k_B/temp)*solutions[2] * \
        testfunctions[2]*dx(1)
    # Source detrapping 2 sol
    expected_form += ((solutions[2] - previous_solutions[2]) / dt) * \
        testfunctions[0]*dx

    assert expected_form.equals(F) is True


def test_formulation_1_trap_2_materials():
    '''
    Test function formulation() with 1 intrinsic trap
    and 2 materials
    '''
    Index._globalcount = 8

    def create_subdomains(x1, x2):
        class domain(fenics.SubDomain):
            def inside(self, x, on_boundary):
                return x[0] >= x1 and x[0] <= x2
        domain = domain()
        return domain
    dt = 1
    parameters = {
        "traps": [
            {
                "k_0": 1,
                "E_k": 2,
                "p_0": 3,
                "E_p": 4,
                "density": 2 + FESTIM.x**2,
                "materials": [1, 2]
            }],
        "materials": [{

                "borders": [0, 0.5],
                "E_D": 4,
                "D_0": 5,
                "id": 1
                },
                {

                "borders": [0.5, 1],
                "E_D": 5,
                "D_0": 6,
                "id": 2
                }],
        "source_term": {"value": 1},
    }
    extrinsic_traps = []
    mesh = fenics.UnitIntervalMesh(10)
    mf = fenics.MeshFunction("size_t", mesh, 1, 1)
    mat1 = create_subdomains(0, 0.5)
    mat2 = create_subdomains(0.5, 1)
    mat1.mark(mf, 1)
    mat2.mark(mf, 2)
    V = fenics.VectorFunctionSpace(mesh, 'P', 1, 2)
    u = fenics.Function(V)
    u_n = fenics.Function(V)
    v = fenics.TestFunction(V)

    solutions = list(fenics.split(u))
    previous_solutions = list(fenics.split(u_n))
    testfunctions = list(fenics.split(v))

    mf = fenics.MeshFunction('size_t', mesh, 1, 1)
    dx = fenics.dx(subdomain_data=mf)
    temp = fenics.Expression("300", degree=0)

    F, expressions = formulation(
        parameters, extrinsic_traps, u, v,
        u_n, dt, dx, temp, transient=True)
    flux_ = expressions[0]
    Index._globalcount = 8
    # Density from formulation()
    density = expressions[2]
    # Transient sol
    expected_form = ((solutions[0] - previous_solutions[0]) / dt) * \
        testfunctions[0]*dx(1)
    expected_form += ((solutions[0] - previous_solutions[0]) / dt) * \
        testfunctions[0]*dx(2)
    # Diffusion sol mat 1
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp)*fenics.grad(solutions[0]),
        fenics.grad(testfunctions[0]))*dx(1)
    # Diffusion sol mat 2
    expected_form += fenics.dot(
            6 * fenics.exp(-5/k_B/temp) * fenics.grad(solutions[0]),
            fenics.grad(testfunctions[0]))*dx(2)
    # Source sol
    expected_form += -flux_*testfunctions[0]*dx
    # Transient trap 1
    expected_form += ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[1]*dx
    # Trapping trap 1 mat 1
    expected_form += - 1 * fenics.exp(-2/k_B/temp) * \
        solutions[0] * (density - solutions[1]) * \
        testfunctions[1]*dx(1)
    # Trapping trap 1 mat 2
    expected_form += - 1 * fenics.exp(-2/k_B/temp) * \
        solutions[0] * (density - solutions[1]) * \
        testfunctions[1]*dx(2)
    # Detrapping trap 1 mat 1
    expected_form += 3*fenics.exp(-4/k_B/temp)*solutions[1] * \
        testfunctions[1]*dx(1)
    # Detrapping trap 1 mat 2
    expected_form += 3*fenics.exp(-4/k_B/temp)*solutions[1] * \
        testfunctions[1]*dx(2)
    # Source detrapping sol
    expected_form += ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[0]*dx
    assert expected_form.equals(F) is True


def test_formulation_1_extrap_1_material():
    '''
    Test function formulation() with 1 extrinsic trap
    and 1 material
    '''
    Index._globalcount = 8
    dt = 1
    parameters = {
        "traps": [{
            "k_0": 1,
            "E_k": 2,
            "p_0": 3,
            "E_p": 4,
            "materials": [1],
            "type": "extrinsic"
            }],
        "materials": [{
                "borders": [0, 1],
                "E_D": 4,
                "D_0": 5,
                "id": 1
                }],
        "source_term": {"value": 10000},
    }

    mesh = fenics.UnitIntervalMesh(10)
    V = fenics.VectorFunctionSpace(mesh, 'P', 1, 2)
    W = fenics.FunctionSpace(mesh, 'P', 1)
    u = fenics.Function(V)
    u_n = fenics.Function(V)
    v = fenics.TestFunction(V)
    n = fenics.interpolate(fenics.Expression('1', degree=0), W)
    solutions = list(fenics.split(u))
    previous_solutions = list(fenics.split(u_n))
    testfunctions = list(fenics.split(v))
    extrinsic_traps = [n]
    mf = fenics.MeshFunction('size_t', mesh, 1, 1)
    dx = fenics.dx(subdomain_data=mf)
    temp = fenics.Expression("300", degree=0)

    F, expressions = formulation(
        parameters, extrinsic_traps, u, v,
        u_n, dt, dx, temp, transient=True)
    flux_ = expressions[0]
    Index._globalcount = 8
    expected_form = ((solutions[0] - previous_solutions[0]) / dt) * \
        testfunctions[0]*dx(1)
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(solutions[0]),
        fenics.grad(testfunctions[0]))*dx(1)
    expected_form += -flux_*testfunctions[0]*dx + \
        ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[1]*dx
    expected_form += - 1 * fenics.exp(-2/k_B/temp) * \
        solutions[0] * (extrinsic_traps[0] - solutions[1]) * \
        testfunctions[1]*dx(1)
    expected_form += 3*fenics.exp(-4/k_B/temp)*solutions[1] * \
        testfunctions[1]*dx(1)
    expected_form += ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[0]*dx

    assert expected_form.equals(F) is True


def test_formulation_steady_state():
    '''
    Test function formulation() with 1 intrinsic trap
    and 1 material in steady state
    '''
    Index._globalcount = 8
    parameters = {
        "traps": [
            {
                "k_0": 1,
                "E_k": 2,
                "p_0": 3,
                "E_p": 4,
                "density": 2,
                "materials": [1]
            }
            ],
        "materials": [{
            "borders": [0, 1],
            "E_D": 4,
            "D_0": 5,
            "id": 1
            }],
        "source_term": {"value": 1},
    }
    extrinsic_traps = []
    mesh = fenics.UnitIntervalMesh(10)
    V = fenics.VectorFunctionSpace(mesh, 'P', 1, 2)
    u = fenics.Function(V)
    u_n = fenics.Function(V)
    v = fenics.TestFunction(V)

    solutions = list(fenics.split(u))
    previous_solutions = list(fenics.split(u_n))
    testfunctions = list(fenics.split(v))

    mf = fenics.MeshFunction('size_t', mesh, 1, 1)
    dx = fenics.dx(subdomain_data=mf)
    temp = fenics.Expression("300", degree=0)
    F, expressions = formulation(
        parameters, extrinsic_traps, u,
        v, u_n, 0, dx, temp, transient=False)
    Index._globalcount = 8
    print(F)
    flux_ = expressions[0]
    density = expressions[2]
    expected_form = -flux_*testfunctions[0]*dx
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(solutions[0]),
        fenics.grad(testfunctions[0]))*dx(1)
    expected_form += - 1 * fenics.exp(-2/k_B/temp) * \
        solutions[0] * (density - solutions[1]) * \
        testfunctions[1]*dx(1)
    expected_form += 3*fenics.exp(-4/k_B/temp)*solutions[1] * \
        testfunctions[1]*dx(1)
    print(expected_form)
    assert expected_form.equals(F) is True


def test_formulation_heat_transfer():
    '''
    Test function define_variational_problem_heat_transfers
    '''

    def thermal_cond(a):
        return a**2

    Index._globalcount = 8
    u = 1 + 2*FESTIM.x**2
    parameters = {
        "materials": [{
            "borders": [0, 1],
            "thermal_cond": thermal_cond,
            "rho": 5,
            "heat_capacity": 4,
            "id": 1
            }],
        "temperature": {
            "type": "solve_transient",
            "boundary_conditions": [
                {
                    "type": "dirichlet",
                    "value": u,
                    "surfaces": [1]
                },
                {
                    "type": "flux",
                    "value": 2,
                    "surfaces": [2]
                },
                ],
            "source_term": [
                {
                    "value": -4,
                    "volume": 1
                }
            ],
        },
    }
    dt = 2
    mesh = fenics.UnitIntervalMesh(10)
    V = fenics.FunctionSpace(mesh, 'P', 1)

    T = fenics.Function(V)
    T_n = fenics.Function(V)
    v = fenics.TestFunction(V)
    functions = [T, v, T_n]

    # create mesh functions
    surface_markers = fenics.MeshFunction(
        "size_t", mesh, mesh.topology().dim()-1, 0)
    surface_markers.set_all(0)
    for f in fenics.facets(mesh):
        x0 = f.midpoint()
        if fenics.near(x0.x(), 0):
            surface_markers[f] = 1
        if fenics.near(x0.x(), 1):
            surface_markers[f] = 2
    volume_markers = fenics.MeshFunction('size_t', mesh, 1, 1)
    ds = fenics.Measure('ds', domain=mesh, subdomain_data=surface_markers)
    dx = fenics.Measure('dx', domain=mesh, subdomain_data=volume_markers)
    # Run function
    F, expressions = \
        FESTIM.formulations.define_variational_problem_heat_transfers(
            parameters, functions, [dx, ds], dt=dt)
    Index._globalcount = 8
    source = expressions[0]
    expected_form = 5*4*(T - T_n)/dt * v * dx(1) + \
        fenics.dot(thermal_cond(T)*fenics.grad(T), fenics.grad(v))*dx(1)
    expected_form += - source*v*dx(1)

    neumann_flux = expressions[1]
    expected_form += -neumann_flux * v * ds(2)

    assert expected_form.equals(F)


def test_formulation_soret():
    Index._globalcount = 8

    def create_subdomains(x1, x2):
        class domain(fenics.SubDomain):
            def inside(self, x, on_boundary):
                return x[0] >= x1 and x[0] <= x2
        domain = domain()
        return domain
    parameters = {
        "traps": [],
        "materials": [{
                "borders": [0, 0.5],
                "E_D": 4,
                "D_0": 5,
                "H":{
                    "free_enthalpy": 4,
                    "entropy": 3
                },
                "id": 1
                },
                {
                "borders": [0, 0.5],
                "E_D": 4,
                "D_0": 5,
                "H":{
                    "free_enthalpy": 4,
                    "entropy": 3
                },
                "id": 2
                }
                ],
        "source_term": {"value": 1},
        "temperature": {
            "soret": True
        }
    }
    extrinsic_traps = []
    mesh = fenics.UnitIntervalMesh(10)
    mf = fenics.MeshFunction("size_t", mesh, 1, 1)
    mat1 = create_subdomains(0, 0.5)
    mat2 = create_subdomains(0.5, 1)
    mat1.mark(mf, 1)
    mat2.mark(mf, 2)
    V = fenics.FunctionSpace(mesh, 'P', 1)
    u = fenics.Function(V)
    u_n = fenics.Function(V)
    v = fenics.TestFunction(V)

    solutions = list(fenics.split(u))
    previous_solutions = list(fenics.split(u_n))
    testfunctions = list(fenics.split(v))

    mf = fenics.MeshFunction('size_t', mesh, 1, 1)
    dx = fenics.dx(subdomain_data=mf)
    temp = fenics.Expression("300", degree=0)
    # temp must be a function and not an expression in that case
    temp = fenics.interpolate(temp, V)
    dt = 2
    F, expressions = formulation(
        parameters, extrinsic_traps, u, v,
        u_n, dt, dx, temp, transient=True)
    flux_ = expressions[0]
    Index._globalcount = 8

    # Transient sol
    expected_form = ((solutions[0] - previous_solutions[0]) / dt) * \
        testfunctions[0]*dx(1)
    expected_form += ((solutions[0] - previous_solutions[0]) / dt) * \
        testfunctions[0]*dx(2)
    # Diffusion sol mat 1
    H = 4*temp + 3
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(solutions[0]),
        fenics.grad(testfunctions[0]))*dx(1)
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * H * solutions[0] /
        (FESTIM.R*temp**2)*fenics.grad(temp),
        fenics.grad(testfunctions[0]))*dx(1)
    # Diffusion sol mat 2
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(solutions[0]),
        fenics.grad(testfunctions[0]))*dx(2)
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * H * solutions[0] /
        (FESTIM.R*temp**2)*fenics.grad(temp),
        fenics.grad(testfunctions[0]))*dx(2)
    # Source sol
    expected_form += -flux_*testfunctions[0]*dx

    assert expected_form.equals(F) is True


def test_formulation_no_trap_1_material_chemical_pot():
    '''
    Test function formulation() with 0 intrinsic trap
    and 1 material with chemical potential conservation
    '''
    Index._globalcount = 8
    dt = 1
    parameters = {
        "materials": [{
            "borders": [0, 1],
            "E_D": 4,
            "D_0": 5,
            "S_0": 2,
            "E_S": 2,
            "id": 1
            }],
        "traps": [],
        "source_term": [{"value": "1", "volumes": 1}],
    }
    extrinsic_traps = []
    mesh = fenics.UnitIntervalMesh(10)
    V = fenics.VectorFunctionSpace(mesh, 'P', 1, 1)
    u = fenics.Function(V)
    u_n = fenics.Function(V)
    v = fenics.TestFunction(V)

    solutions = list(fenics.split(u))
    previous_solutions = list(fenics.split(u_n))
    testfunctions = list(fenics.split(v))

    mf = fenics.MeshFunction('size_t', mesh, 1, 1)
    dx = fenics.dx(subdomain_data=mf)
    temp = fenics.Expression("300", degree=0)
    temp_n = fenics.Expression("200", degree=0)

    F, expressions = formulation(
        parameters, extrinsic_traps, u, v,
        u_n, dt, dx, temp, T_n=temp_n, transient=True)

    Index._globalcount = 8
    flux_ = expressions[0]
    theta = solutions[0]*2*fenics.exp(-2/k_B/temp)
    theta_n = previous_solutions[0]*2*fenics.exp(-2/k_B/temp_n)
    expected_form = ((theta - theta_n) / dt) * testfunctions[0]*dx(1)
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(theta),
        fenics.grad(testfunctions[0]))*dx(1)
    expected_form += -flux_*testfunctions[0]*dx(1)

    assert expected_form.equals(F) is True


def test_formulation_1_trap_1_material_chemical_pot():
    '''
    Test function formulation() with 1 intrinsic trap
    and 1 material with chemical potential conservation
    '''
    Index._globalcount = 8
    dt = 1
    parameters = {
        "traps": [
            {
                "k_0": 1,
                "E_k": 2,
                "p_0": 3,
                "E_p": 4,
                "density": 2,
                "materials": [1]
            }
        ],
        "materials": [{
            "borders": [0, 0.5],
            "E_D": 4,
            "D_0": 5,
            "S_0": 2,
            "E_S": 2,
            "id": 1
            },
            {
            "borders": [0.5, 1],
            "E_D": 4,
            "D_0": 5,
            "S_0": 3,
            "E_S": 3,
            "id": 2
            },
            ],
    }
    extrinsic_traps = []
    mesh = fenics.UnitIntervalMesh(10)
    V = fenics.VectorFunctionSpace(mesh, 'P', 1, 2)
    u = fenics.Function(V)
    u_n = fenics.Function(V)
    v = fenics.TestFunction(V)

    solutions = list(fenics.split(u))
    previous_solutions = list(fenics.split(u_n))
    testfunctions = list(fenics.split(v))

    mf = fenics.MeshFunction('size_t', mesh, 1, 1)
    dx = fenics.dx(subdomain_data=mf)
    temp = fenics.Expression("300", degree=0)
    temp_n = fenics.Expression("200", degree=0)
    F, expressions = formulation(
        parameters, extrinsic_traps, u,
        v, u_n,
        dt, dx, temp, temp_n, transient=True)
    Index._globalcount = 8
    # take density Expression() from formulation()
    print(expressions)
    density = expressions[1]

    theta1 = solutions[0]*2*fenics.exp(-2/k_B/temp)
    theta1_n = previous_solutions[0]*2*fenics.exp(-2/k_B/temp_n)
    theta2 = solutions[0]*3*fenics.exp(-3/k_B/temp)
    theta2_n = previous_solutions[0]*3*fenics.exp(-3/k_B/temp_n)

    expected_form = ((theta1 - theta1_n) / dt) * \
        testfunctions[0]*dx(1)
    expected_form += ((theta2 - theta2_n) / dt) * \
        testfunctions[0]*dx(2)

    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(theta1),
        fenics.grad(testfunctions[0]))*dx(1)
    expected_form += fenics.dot(
        5 * fenics.exp(-4/k_B/temp) * fenics.grad(theta2),
        fenics.grad(testfunctions[0]))*dx(2)

    expected_form += ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[1]*dx
    expected_form += - 1 * fenics.exp(-2/k_B/temp) * \
        theta1 * (density - solutions[1]) * \
        testfunctions[1]*dx(1)
    expected_form += 3*fenics.exp(-4/k_B/temp)*solutions[1] * \
        testfunctions[1]*dx(1)
    expected_form += ((solutions[1] - previous_solutions[1]) / dt) * \
        testfunctions[0]*dx
    assert expected_form.equals(F) is True


def test_formulation_extrinsic_traps():
    """Tests the function formulations.formulation_extrinsic_traps()
    """
    dt = 2
    n_amax = 1e-1*6.3e28
    n_bmax = 1e-2*6.3e28
    eta_a = 6e-4
    eta_b = 2e-4
    parameters = {
        "traps": [{
            "k_0": 1,
            "E_k": 2,
            "p_0": 3,
            "E_p": 4,
            "materials": [1],
            "type": "extrinsic",
            "form_parameters":{
                "phi_0": 2.5e19 * (FESTIM.t <= 400),
                "n_amax": n_amax,
                "f_a": (FESTIM.x < 1e-8) * (FESTIM.x > 0) * (1/1e-8),
                "eta_a": eta_a,
                "n_bmax": n_bmax,
                "f_b": (FESTIM.x < 1e-6) * (FESTIM.x > 0) * (1/1e-6),
                "eta_b": eta_b,
            }
            }],
    }

    mesh = fenics.UnitIntervalMesh(10)
    W = fenics.FunctionSpace(mesh, 'P', 1)
    extrinsic_traps = [fenics.Function(W)]
    extrinsic_traps_n = [fenics.Function(W)]
    test_functions = [fenics.TestFunction(W)]

    forms, expressions = formulation_extrinsic_traps(
        parameters["traps"], extrinsic_traps,
        test_functions, extrinsic_traps_n,  dt)

    phi_0, f_a, f_b = expressions
    expected_form = ((extrinsic_traps[0] - extrinsic_traps_n[0])/dt) * \
        test_functions[0]*fenics.dx
    expected_form += -phi_0*(
        (1 - extrinsic_traps[0]/n_amax)*eta_a*f_a +
        (1 - extrinsic_traps[0]/n_bmax)*eta_b*f_b) * \
        test_functions[0]*fenics.dx

    assert expected_form.equals(forms[0])