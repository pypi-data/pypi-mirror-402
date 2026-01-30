import pytest
from actualcauses import suzzy_example_scm

def test_toy_scm_MBS():
    suzzy_example_scm.find_causes(ISI=False)
    mbs_causes = suzzy_example_scm.causes
    expected_causes = [{'SH'}, {'ST'}]
    assert set(map(frozenset, mbs_causes)) == set(map(frozenset, expected_causes))

def test_toy_scm_MBS():
    suzzy_example_scm.find_causes(ISI=True)
    mbs_causes = suzzy_example_scm.causes
    expected_causes = [{'SH'}, {'ST'}]
    assert set(map(frozenset, mbs_causes)) == set(map(frozenset, expected_causes))
