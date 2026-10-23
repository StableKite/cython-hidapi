"""Run with LD_PRELOAD=fake_hidapi.so on a free-threaded CPython."""
import concurrent.futures
import ctypes
import os
import sys
import threading
import time
import unittest
import hid
import hidraw

backend=ctypes.CDLL(os.environ['LD_PRELOAD'])

class FreeThreadingTest(unittest.TestCase):
    def test_import_preserves_disabled_gil(self):
        self.assertFalse(sys._is_gil_enabled())

    def test_close_waits_for_native_io(self):
        for module in (hid,hidraw):
            for op in ('write','read','send_feature_report','get_feature_report','get_input_report'):
                with self.subTest(module=module.__name__,operation=op):
                    d=module.device();d.open_path(b'fixture')
                    args=([1,2],) if op in ('write','send_feature_report') else ((1,1) if op.startswith('get_') else (1,))
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                        io=pool.submit(getattr(d,op),*args)
                        deadline=time.monotonic()+3
                        while not backend.test_active():
                            self.assertLess(time.monotonic(),deadline);time.sleep(.001)
                        close=pool.submit(d.close)
                        io.result(timeout=3);close.result(timeout=3)
                    self.assertEqual(backend.test_violations(),0)
                    with self.assertRaises(ValueError):d.write(b'x')

    def test_open_is_serialized(self):
        for module in (hid,hidraw):
            d=module.device();start=threading.Barrier(2)
            before=backend.test_opens()
            def open_one():
                start.wait()
                try:d.open_path(b'fixture');return 'open'
                except RuntimeError:return 'already open'
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                result=list(pool.map(lambda _:open_one(),range(2)))
            self.assertCountEqual(result,['open','already open'])
            self.assertEqual(backend.test_opens()-before,1);d.close()

    def test_reentrant_bytes_conversion_can_close(self):
        for module in (hid,hidraw):
            for op in ('write','send_feature_report'):
                d=module.device();d.open_path(b'fixture')
                class CloseOnBytes:
                    def __bytes__(self):d.close();return b'x'
                with self.assertRaises(ValueError):getattr(d,op)(CloseOnBytes())
                self.assertEqual(backend.test_violations(),0)

    def test_empty_report_rejected_before_native_call(self):
        for module in (hid,hidraw):
            d=module.device();d.open_path(b'fixture')
            for op in ('get_feature_report','get_input_report'):
                with self.assertRaises(ValueError):getattr(d,op)(0,0)
            d.close()

if __name__=='__main__':unittest.main()
