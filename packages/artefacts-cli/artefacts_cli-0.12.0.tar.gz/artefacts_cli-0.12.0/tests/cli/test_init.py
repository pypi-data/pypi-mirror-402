from multiprocessing import Process
import signal
import sys
from time import sleep

import psutil

import artefacts
from artefacts.cli import proc_tree_tracker


#
# Sub-process with controlled behaviours
#
#   Using multiprocessing, we need module-global functions
#   or multiprocessing cannot pickle.
#
def _plain():
    sleep(0.1)


def _ignores_sigint_sigterm():
    signal.signal(signal.SIGINT, lambda sig, frame: ())
    signal.signal(signal.SIGTERM, lambda sig, frame: ())
    sleep(10)


#
# Test suite
#
def test_proc_tree_tracker_terminate_no_child(mocker):
    mocker.patch.object(psutil.Process, "children", return_value=[])
    assert proc_tree_tracker.terminate() == {
        "found": 0,
        "terminated": 0,
        "killed": 0,
        "errors": 0,
    }


def test_proc_tree_tracker_terminate_single_child_plain(mocker):
    child = Process(target=_plain)
    child.start()
    report = proc_tree_tracker.terminate(wait_time_s=0.2)
    expected = {
        "found": 1,
        "terminated": 1,
        "killed": 0,
        "errors": 0,
    }
    if sys.platform == "darwin":
        # Still unclear why an extra process appears on Darwin only
        expected["found"] += 1
        expected["killed"] += 1
    assert report == expected
    child.join()


def test_proc_tree_tracker_terminate_single_child_ignores_sigint_sigterm():
    child = Process(target=_ignores_sigint_sigterm)
    child.start()
    report = proc_tree_tracker.terminate(wait_time_s=0.2)
    expected = {
        "found": 1,
        "terminated": 0,
        "killed": 1,
        "errors": 0,
    }
    if sys.platform == "darwin":
        # Still unclear why an extra process appears on Darwin only
        expected["found"] += 1
        expected["terminated"] += 1
    assert report == expected
    child.join()


def test_proc_tree_tracker_terminate_multi_child_mixed():
    c1 = Process(target=_plain)
    c2 = Process(target=_ignores_sigint_sigterm)
    c1.start()
    c2.start()
    report = proc_tree_tracker.terminate(wait_time_s=0.2)
    expected = {
        "found": 2,
        "terminated": 1,
        "killed": 1,
        "errors": 0,
    }
    if sys.platform == "darwin":
        # Still unclear why an extra process appears on Darwin only
        expected["found"] += 1
        expected["terminated"] += 1
    assert report == expected
    c1.join()
    c2.join()


def test_proc_tree_tracker_terminate_single_child_ignores_sigint_sigterm_sigkill(
    mocker,
):
    unkillable = mocker.patch.object(
        artefacts.cli.utils.proc_tree_tracker.psutil.Process, "kill"
    )
    unkillable.side_effect = Exception("Test error")

    child = Process(target=_ignores_sigint_sigterm)
    child.start()

    report = proc_tree_tracker.terminate(wait_time_s=0.2)
    expected = {
        "found": 1,
        "terminated": 0,
        "killed": 0,
        "errors": 1,
    }
    if sys.platform == "darwin":
        # Still unclear why an extra process appears on Darwin only
        expected["found"] += 1
        expected["terminated"] += 1
    assert report == expected

    # Terminate here, so we do not make the test suite wait
    child.kill()
    child.join()
