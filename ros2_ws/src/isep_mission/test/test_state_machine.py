from isep_mission.state_machine import Inputs, MissionStateMachine, State


def kinds(actions):
    return [a[0] for a in actions]


def run_to_mission(sm):
    sm.step(Inputs(now=0, connected=True, start_requested=True))
    sm.step(Inputs(now=1, connected=True, mission_upload_ok=True))
    sm.step(Inputs(now=2, connected=True, mode="QLOITER"))
    sm.step(Inputs(now=3, connected=True, armed=True, mode="AUTO"))
    assert sm.state == State.MISSION


def test_nominal_flight():
    sm = MissionStateMachine()
    a = sm.step(Inputs(now=0, connected=True, start_requested=True))
    assert sm.state == State.UPLOAD_MISSION and ("upload_mission",) in a
    sm.step(Inputs(now=1, connected=True, mission_upload_ok=True))
    assert sm.state == State.ARMING
    a = sm.step(Inputs(now=2, connected=True, mode="QLOITER"))
    assert ("set_mode", "AUTO") in a and ("arm", True) in a
    sm.step(Inputs(now=3, connected=True, armed=True, mode="AUTO"))
    assert sm.state == State.MISSION
    sm.step(Inputs(now=10, connected=True, armed=True, mode="AUTO", landed=False))
    sm.step(Inputs(now=300, connected=True, armed=False, mode="AUTO", landed=True))
    assert sm.state == State.DONE


def test_landed_before_takeoff_is_not_done():
    sm = MissionStateMachine()
    run_to_mission(sm)
    sm.step(Inputs(now=4, connected=True, armed=False, mode="AUTO", landed=True))
    assert sm.state == State.MISSION


def test_start_refused_when_disconnected():
    sm = MissionStateMachine()
    a = sm.step(Inputs(now=0, connected=False, start_requested=True))
    assert sm.state == State.IDLE and kinds(a) == ["log"]


def test_upload_refused_aborts():
    sm = MissionStateMachine()
    sm.step(Inputs(now=0, connected=True, start_requested=True))
    sm.step(Inputs(now=1, connected=True, mission_upload_ok=False))
    assert sm.state == State.ABORTED


def test_upload_timeout_aborts():
    sm = MissionStateMachine()
    sm.step(Inputs(now=0, connected=True, start_requested=True))
    sm.step(Inputs(now=20, connected=True))
    assert sm.state == State.ABORTED


def test_arming_retries_then_aborts():
    sm = MissionStateMachine()
    sm.step(Inputs(now=0, connected=True, start_requested=True))
    sm.step(Inputs(now=1, connected=True, mission_upload_ok=True))
    t, arms = 2.0, 0
    while sm.state == State.ARMING and t < 100:
        arms += kinds(sm.step(Inputs(now=t, connected=True, mode="AUTO"))).count("arm")
        t += 0.2
    assert sm.state == State.ABORTED
    assert arms == sm.config.arming_max_attempts


def test_failsafe_mode_takes_over():
    sm = MissionStateMachine()
    run_to_mission(sm)
    sm.step(Inputs(now=5, connected=True, armed=True, mode="QRTL", landed=False))
    assert sm.state == State.FAILSAFE
    assert sm.step(Inputs(now=6, connected=True, armed=True, mode="QRTL", landed=False)) == []
    sm.step(Inputs(now=60, connected=True, armed=False, mode="QRTL", landed=True))
    assert sm.state == State.DONE


def test_target_triggers_single_drop():
    sm = MissionStateMachine()
    run_to_mission(sm)
    a = sm.step(Inputs(now=5, connected=True, armed=True, mode="AUTO", landed=False,
                       target_detected=True, target_confidence=0.9))
    assert sm.state == State.TARGET_FOUND and ("drop",) in a
    sm.step(Inputs(now=6, connected=True, armed=True, mode="AUTO", landed=False))
    assert sm.state == State.MISSION
    a = sm.step(Inputs(now=7, connected=True, armed=True, mode="AUTO", landed=False,
                       target_detected=True, target_confidence=0.9))
    assert ("drop",) not in a


def test_low_confidence_target_ignored():
    sm = MissionStateMachine()
    run_to_mission(sm)
    sm.step(Inputs(now=5, connected=True, armed=True, mode="AUTO", landed=False,
                   target_detected=True, target_confidence=0.3))
    assert sm.state == State.MISSION


def test_link_lost_before_takeoff_aborts():
    sm = MissionStateMachine()
    sm.step(Inputs(now=0, connected=True, start_requested=True))
    sm.step(Inputs(now=1, connected=False))
    assert sm.state == State.ABORTED
