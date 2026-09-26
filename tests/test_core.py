import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import core


class QueueTests(unittest.TestCase):
    @patch.object(core, "run")
    @patch.object(core, "queues", return_value=["Existing"])
    def test_existing_queue_is_never_overwritten(self, _queues, run):
        with self.assertRaisesRegex(ValueError, "already in use"):
            core.add_queue("Existing", "ipp://example/ipp/print", "everywhere")
        run.assert_not_called()

    @patch.object(core, "run")
    @patch.object(core, "queues", return_value=[])
    def test_everywhere_refuses_usb_device(self, _queues, run):
        with patch.object(core, "usb_devices", return_value=["usb://Brother/HL-2035"]):
            with self.assertRaisesRegex(ValueError, "IPP"):
                core.add_queue("Printer", "usb://Brother/HL-2035", "everywhere")
        run.assert_not_called()

    @patch.object(core, "run")
    @patch.object(core, "queues", return_value=["Existing"])
    def test_new_queue_does_not_delete_old_queue(self, _queues, run):
        core.add_queue("NewPrinter", "ipp://example/ipp/print", "everywhere")
        self.assertEqual(run.call_args_list[0].args[:4], ("lpadmin", "-p", "NewPrinter", "-E"))
        self.assertFalse(any("-x" in call.args for call in run.call_args_list))

    @patch.object(core, "queues", return_value=["Existing"])
    def test_mobile_pdf_must_be_pdf(self, _queues):
        with self.assertRaisesRegex(ValueError, "PDF"):
            core.print_pdf("Existing", b"not a pdf")

    @patch.object(core.subprocess, "run")
    def test_first_run_without_any_queues(self, run):
        run.return_value = CompletedProcess(["lpstat", "-p"], 1, "", "No destinations added")
        self.assertEqual(core.queues(), [])


if __name__ == "__main__":
    unittest.main()
