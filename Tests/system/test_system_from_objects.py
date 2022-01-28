import FESTIM
import fenics
import pytest
import sympy as sp
import numpy as np
from pathlib import Path
import timeit


# System tests

def test_run_temperature_stationary(tmpdir):
    '''
    Check that the temperature module works well in 1D stationary
    '''
    d = tmpdir.mkdir("Solution_Test")
    u = 1 + 2*FESTIM.x**2
    size = 1

    my_materials = [
        FESTIM.Material(id=1, D_0=4.1e-7, E_D=0.39, thermal_cond=1)
    ]

    my_mesh = FESTIM.MeshFromRefinements(200, size=size)
    my_boundary_conditions = [
        FESTIM.DirichletBC("dc", value=1, component=0, surfaces=[1]),
        FESTIM.DirichletBC("dc", value=u, component="T", surfaces=[1, 2])
    ]

    my_sources = [FESTIM.Source(-4, 1, "T")]
    my_temperature = FESTIM.Temperature("solve_stationary")
    my_settings = FESTIM.Settings(
        absolute_tolerance=1e10, relative_tolerance=1e-9,
        maximum_iterations=50,
        final_time=30
    )
    my_stepsize = FESTIM.Stepsize(initial_value=0.5, stepsize_change_ratio=1, dt_min=1e-5)

    my_derived_quantities = FESTIM.DerivedQuantities(file="derived_quantities.csv", folder=str(Path(d)))
    my_derived_quantities.derived_quantities = [FESTIM.TotalVolume("solute", 1)]

    my_exports = [
            FESTIM.XDMFExports(fields=['T', 'solute'], labels=["temperature", "solute"], folder=str(Path(d))),
            my_derived_quantities,
            FESTIM.Error("T", exact_solution=u)
    ]

    my_sim = FESTIM.Simulation(
        mesh=my_mesh, materials=my_materials,
        boundary_conditions=my_boundary_conditions,
        sources=my_sources,
        dt=my_stepsize, settings=my_settings,
        temperature=my_temperature, exports=my_exports)
    my_sim.initialise()
    output = my_sim.run()
    assert output["error"][0] < 1e-9


def test_run_temperature_transient(tmpdir):
    '''
    Check that the temperature module works well in 1D transient
    '''
    d = tmpdir.mkdir("Solution_Test")
    u = 1 + 2*FESTIM.x**2+FESTIM.t
    size = 1

    my_materials = FESTIM.Materials(
        [FESTIM.Material(
            id=1,
            D_0=4.1e-7, E_D=0.39,
            thermal_cond=1, rho=1, heat_capacity=1,
            borders=[0, size])
        ]
    )
    my_mesh = FESTIM.MeshFromRefinements(200, size)

    my_bcs = [
        FESTIM.DirichletBC(type="dc", surfaces=[1], value=1, component=0),
        FESTIM.DirichletBC(type="dc", surfaces=[1, 2], value=u, component="T")
    ]

    my_temp = FESTIM.Temperature("solve_transient", initial_value=u)

    my_sources = [
        FESTIM.Source(value=sp.diff(u, FESTIM.t) - sp.diff(u, FESTIM.x, 2), volume=1, field="T")
    ]

    my_settings = FESTIM.Settings(
        absolute_tolerance=1e10,
        relative_tolerance=1e-9,
        maximum_iterations=50,
        transient=True, final_time=30
    )

    my_dt = FESTIM.Stepsize(
        initial_value=0.5, stepsize_change_ratio=1,
        t_stop=40, stepsize_stop_max=0.5, dt_min=1e-5)

    my_exports = FESTIM.Exports(
        [
            FESTIM.XDMFExport("T", "temperature", str(Path(d))),
            FESTIM.Error("T", u)
        ]
    )

    my_sim = FESTIM.Simulation(
        mesh=my_mesh, materials=my_materials, sources=my_sources,
        boundary_conditions=my_bcs, dt=my_dt,
        settings=my_settings, temperature=my_temp,
        exports=my_exports
    )
    my_sim.initialise()
    output = my_sim.run()

    assert output["error"][0] < 1e-9


def test_run_MMS(tmpdir):
    '''
    Test function run() for several refinements
    '''
    d = tmpdir.mkdir("Solution_Test")
    u = 1 + sp.sin(2*fenics.pi*FESTIM.x)*FESTIM.t
    v = 1 + sp.cos(2*fenics.pi*FESTIM.x)*FESTIM.t
    size = 1
    k_0 = 2
    E_k = 1.5
    p_0 = 3
    E_p = 0.2
    T = 700 + 30*FESTIM.x
    n_trap = 1
    E_D = 0.1
    D_0 = 2
    k_B = FESTIM.k_B
    D = D_0 * sp.exp(-E_D/k_B/T)
    p = p_0 * sp.exp(-E_p/k_B/T)
    k = k_0 * sp.exp(-E_k/k_B/T)

    f = sp.diff(u, FESTIM.t) + sp.diff(v, FESTIM.t) - \
        D * sp.diff(u, FESTIM.x, 2) - \
        sp.diff(D, FESTIM.x)*sp.diff(u, FESTIM.x)
    g = sp.diff(v, FESTIM.t) + p*v - k * u * (n_trap-v)

    def run(h):
        my_materials = FESTIM.Materials(
            [
                FESTIM.Material(id=1, D_0=D_0, E_D=E_D)
            ]
        )
        my_traps = FESTIM.Traps(
            [
                FESTIM.Trap(k_0, E_k, p_0, E_p, 1, n_trap)
            ]
        )

        my_initial_conditions = [
            FESTIM.InitialCondition(field=0, value=u),
            FESTIM.InitialCondition(field=1, value=v),
        ]

        my_mesh = FESTIM.MeshFromRefinements(round(size/h), size)

        my_bcs = [
            FESTIM.DirichletBC(type="dc", surfaces=[1, 2], value=u, component=0),
            FESTIM.DirichletBC(type="dc", surfaces=[1, 2], value=v, component=1),
        ]

        my_temp = FESTIM.Temperature("expression", T)

        my_sources = [
            FESTIM.Source(f, 1, "0"),
            FESTIM.Source(g, 1, "1")
        ]

        my_settings = FESTIM.Settings(
            absolute_tolerance=1e-10,
            relative_tolerance=1e-9,
            maximum_iterations=50,
            transient=True, final_time=0.1
        )

        my_dt = FESTIM.Stepsize(0.1/50)
        my_exports = FESTIM.Exports([
                FESTIM.XDMFExport("retention", "retention", str(Path(d))),
                FESTIM.Error(0, u),
                FESTIM.Error(1, v),
            ]
        )

        my_sim = FESTIM.Simulation(
            mesh=my_mesh, materials=my_materials, traps=my_traps,
            initial_conditions=my_initial_conditions, boundary_conditions=my_bcs,
            temperature=my_temp, sources=my_sources, settings=my_settings,
            dt=my_dt, exports=my_exports)

        my_sim.initialise()
        return my_sim.run()

    tol_u = 1e-7
    tol_v = 1e-6
    sizes = [1/1600, 1/1700]
    dt = 0.1/50
    final_time = 0.1
    for h in sizes:
        output = run(h)
        error_max_u = output["error"][0]
        error_max_v = output["error"][1]
        msg = 'Maximum error on u is:' + str(error_max_u) + '\n \
            Maximum error on v is:' + str(error_max_v) + '\n \
            with h = ' + str(h) + '\n \
            with dt = ' + str(dt)
        print(msg)
        assert error_max_u < tol_u and error_max_v < tol_v