import sys
from pathlib import Path
import numpy as np
import random

from actualcauses import suzzy_example_scm, SCM

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from examples.custom_scm import ForestFireExampleSystemModel
from examples.vectorized_system_model import LampModel
from examples.stochastic_system_model import RockThrowingModel, AvgRockThrowingModel, LUCBRockThrowingModel
from examples.custom_heuristic import SuzzyCustomPsi
# import pytest


def test_example_1():
    dis_ff_example = SCM(
        V=("MD", "L", "FF"),
        U=("md", "l"),
        D=(0,1),
        u=(1,1),
        model=ForestFireExampleSystemModel(disjuctive=True),
        dag={"MD":[], "L":[], "FF":["MD", "L"]}
    )
    
    conj_ff_example = SCM(
        V=("MD", "L", "FF"),
        U=("md", "l"),
        D=(0,1),
        u=(1,1),
        model=ForestFireExampleSystemModel(disjuctive=False),
        dag={"MD":[], "L":[], "FF":["MD", "L"]}
    )
    dis_exp_causes = [{'MD', 'L'}]
    dis_ff_example.find_causes()
    dis_causes = dis_ff_example.causes
    assert set(map(frozenset, dis_exp_causes)) == set(map(frozenset, dis_causes))
    
    conj_exp_causes = [{'L'}, {'MD'}]
    conj_ff_example.find_causes()
    conj_causes = conj_ff_example.causes
    assert set(map(frozenset, conj_exp_causes)) == set(map(frozenset, conj_causes))

def test_example_2():
    scm_lamp = SCM(V=["A","B", "C", "L"], U=["a","b", "c"], D=[(-1,0,1)]*3+[(0,1)], 
                model=LampModel(V=["A","B", "C", "L"], dtype=int), 
                u=(1,-1,-1), 
                dag={"A":[], "B": [], "C":[], "L":["A", "B", "C"]})
    lamp_exp_causes = [{'B'}, {'C'}]
    scm_lamp.find_causes()
    lamp_causes = scm_lamp.causes
    assert set(map(frozenset, lamp_exp_causes)) == set(map(frozenset, lamp_causes))

def test_example_3():
    suzzy_vars = ("ST", "BT", "SH", "BH", "BS")

    t = .05 
    N = 25
    eps = .25 
    beam_size = 10
    lucb_params = {"a": eps, 
                   "cause_eps": .1, 
                   "non_cause_eps": .1, 
                   "beam_eps": .1, 
                   "max_iter": N, 
                   "verbose": 0, 
                   "init_batch_size": 15,
                   "batch_size": 2,
                   "delta": .05,
                   "beam_size": beam_size,
                   "seed": 0
                   }
    
    noisy_suzzy_avg = SCM(
        V=suzzy_vars,
        U=("st", "bt"),
        D=(0,1),
        u=(1,1),
        dag=None,
        model=AvgRockThrowingModel(suzzy_vars, t, N, seed=0, rng=np.random.default_rng(seed=42))
        )
    
    noisy_suzzy_lucb = SCM(
        V=suzzy_vars,
        U=("st", "bt"),
        D=(0,1),
        u=(1,1),
        dag=None,
        model=LUCBRockThrowingModel(suzzy_vars, t, lucb_params, rng=np.random.default_rng(seed=42))
        )
    noisy_suzzy_avg.find_causes(epsilon=eps, beam_size=beam_size)
    noisy_suzzy_lucb.find_causes(epsilon=eps, beam_size=beam_size)

    exp_causes = [{'ST'}, {'SH'}]
    assert set(map(frozenset, exp_causes)) == set(map(frozenset, noisy_suzzy_avg.causes))
    assert set(map(frozenset, exp_causes)) == set(map(frozenset, noisy_suzzy_lucb.causes))

def test_example_4():
    v = suzzy_example_scm.v

    heuristics = {
        "sum of negative variables": lambda s: sum(s),
        "sum of positive variables": lambda s: len(s) - sum(s),
        "sum of counteractual variables": lambda s: sum([s_val != v_val for s_val, v_val in zip(s, v)]),
        "sum of actual variables": lambda s: sum([s_val == v_val for s_val, v_val in zip(s, v)]),
    }
    exp_causes = [{'ST'}, {'SH'}]
    for desc, psi in heuristics.items():
        system_model = SuzzyCustomPsi(psi)
        scm = SCM(
            V=("ST", "BT", "SH", "BH", "BS"),
            U=("st", "bs"),
            D=(0,1),
            u=(1,1),
            model=system_model,
            dag={"ST":[], "BT":[], "SH":["ST"], "BH":["BT","SH"], "BS":["BH","SH"]}
        )
        scm.find_causes()
        assert set(map(frozenset, exp_causes)) == set(map(frozenset, scm.causes))