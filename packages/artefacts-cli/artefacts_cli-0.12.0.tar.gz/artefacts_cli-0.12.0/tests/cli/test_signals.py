import signal
import sys

from artefacts.cli import job_sigint_handler


def test_sigint_handler_harmless(mocker):
    """
    Basic checks that calling the SIGINT handler with typical values
    is harmless (does nothing) by default.
    """
    mocker.patch("sys.exit", return_value=None)
    assert job_sigint_handler(None, None, None) is None
    assert job_sigint_handler(None, signal.SIG_IGN, None) is None
    assert job_sigint_handler(None, None, sys._getframe()) is None
    assert job_sigint_handler("not a WarpJob object", None, None) is None


def test_sigint_handler_fails_job(mocker, artefacts_job):
    """
    Check a job is marked as failed when SIGINT
    """
    mocker.patch("sys.exit", return_value=None)
    spy = mocker.spy(artefacts_job, "update")
    job_sigint_handler(artefacts_job, None, None)
    spy.assert_called_with(False, True)
    assert spy.call_count == 1


def test_sigint_handler_stops_run(mocker, artefacts_job, artefacts_run):
    """
    Check a run is stopped when SIGINT
    """
    mocker.patch("sys.exit", return_value=None)
    spy = mocker.spy(artefacts_run, "stop")
    job_sigint_handler(artefacts_job, None, None)
    assert spy.call_count == 1
