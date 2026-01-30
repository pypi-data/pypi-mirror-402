import unittest
import os
import json
import pickle
import threading
import time
import shutil
import logging
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY, call
from types import MappingProxyType
from queue import Empty

# Ensure we can import vxsched
sys.path.append(os.getcwd())
import vxsched
from vxsched import (
    _freeze, _release, Config, Params,
    _CronField, _Cron, Trigger, OnceTrigger, IntervalTrigger, CronTrigger,
    once, daily, weekly, every, crontab,
    Event, _EventQueue, Scheduler,
    init_command, run_command, main,
    INIT_EVENT, SHUTDOWN_EVENT
)

# Setup logging to avoid cluttering output
logging.basicConfig(level=logging.CRITICAL)

class TestHelpers(unittest.TestCase):
    def test_freeze(self):
        d = {"a": 1, "b": [2, 3]}
        frozen = _freeze(d)
        self.assertIsInstance(frozen, MappingProxyType)
        self.assertIsInstance(frozen["b"], tuple)
        
        l = [1, 2]
        self.assertIsInstance(_freeze(l), tuple)
        
        s = {1, 2}
        self.assertIsInstance(_freeze(s), frozenset)
        
        x = 10
        self.assertEqual(_freeze(x), 10)

    def test_release(self):
        d = MappingProxyType({"a": 1, "b": (2, 3)})
        released = _release(d)
        self.assertIsInstance(released, dict)
        self.assertIsInstance(released["b"], list)
        
        t = (1, 2)
        self.assertIsInstance(_release(t), list)
        
        s = frozenset({1, 2})
        self.assertIsInstance(_release(s), set)
        
        x = 10
        self.assertEqual(_release(x), 10)

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_config_dir")
        self.test_dir.mkdir(exist_ok=True)
        self.config_file = self.test_dir / "vxsched.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init_and_access(self):
        # Env mocking needs to be done carefully if Config reads os.environ directly in init
        with patch.dict(os.environ, {}, clear=True):
             cfg = Config(a=1, b={"c": 2}, env={"TEST_ENV_VAR": "123"})
             self.assertEqual(cfg.a, 1)
             self.assertEqual(cfg["b"]["c"], 2)
             self.assertEqual(os.environ.get("TEST_ENV_VAR"), "123")
        
        cfg = Config(a=1)
        # Test readonly
        with self.assertRaises(RuntimeError):
            cfg.a = 2
        with self.assertRaises(RuntimeError):
            cfg["a"] = 2
        
        # Test internal attr
        cfg._internal = 99
        self.assertEqual(cfg._internal, 99)

    def test_iter_len_contains(self):
        cfg = Config(a=1, b=2)
        self.assertEqual(len(cfg), 2)
        self.assertIn("a", cfg)
        self.assertIn("b", cfg)
        self.assertEqual(set(iter(cfg)), {"a", "b"})
        self.assertTrue(str(cfg).startswith("{"))
        self.assertTrue(repr(cfg).startswith("{"))

    def test_get(self):
        cfg = Config(a=1)
        self.assertEqual(cfg.get("a"), 1)
        self.assertEqual(cfg.get("b", 2), 2)

    def test_load_save(self):
        # Save
        cfg = Config(a=1, b=[1, 2])
        cfg.save(str(self.config_file))
        self.assertTrue(self.config_file.exists())
        
        # Load
        loaded_cfg = Config.load(str(self.config_file))
        self.assertEqual(loaded_cfg.a, 1)
        self.assertEqual(loaded_cfg.b, (1, 2)) # loaded as tuple due to freeze

        # Load non-existent
        empty_cfg = Config.load("non_existent_file.json")
        self.assertEqual(len(empty_cfg), 0)

class TestParams(unittest.TestCase):
    def test_params_ops(self):
        p = Params()
        p.set_params("a", 1, persist=True)
        p.set_params("b", 2, persist=False)
        
        self.assertEqual(p.a, 1)
        self.assertEqual(p.b, 2)
        self.assertEqual(p["a"], 1)
        
        with self.assertRaises(KeyError):
            _ = p["c"]

        # Test pickle
        state = p.__getstate__()
        self.assertEqual(state, {"a": 1}) # Only a is persisted
        
        p2 = Params()
        p2.__setstate__(state)
        self.assertEqual(p2.a, 1)
        self.assertFalse(hasattr(p2, "b"))

class TestCron(unittest.TestCase):
    def test_cron_field(self):
        # Exact
        cf = _CronField("5", 0, 59)
        self.assertEqual(cf.values, [5])
        
        # Range
        cf = _CronField("1-3", 0, 59)
        self.assertEqual(cf.values, [1, 2, 3])
        
        # Step
        cf = _CronField("*/15", 0, 59)
        self.assertEqual(cf.values, [0, 15, 30, 45])
        
        cf = _CronField("10/20", 0, 59)
        self.assertEqual(cf.values, [10, 30, 50])
        
        # List
        cf = _CronField("1,3,5", 0, 59)
        self.assertEqual(cf.values, [1, 3, 5])
        
        # Any
        cf = _CronField("*", 0, 2)
        self.assertEqual(cf.values, [0, 1, 2])
        
        # Contains
        self.assertIn(1, cf)
        self.assertNotIn(3, cf)
        
        # Iter
        self.assertEqual(list(iter(cf)), [0, 1, 2])
        
        # Reset
        cf.reset(1)
        self.assertEqual(list(iter(cf)), [1, 2])

    def test_cron_parser(self):
        start = datetime(2023, 1, 1, 0, 0, 0)
        end = datetime(2023, 1, 1, 0, 2, 0)
        
        # Run every minute
        c = _Cron("* * * * * *", start_dt=start, end_dt=end)
        dates = list(c(current_dt=start))
        self.assertTrue(len(dates) > 0)
        self.assertEqual(dates[0], start)
        
        # Invalid expression
        with self.assertRaises(ValueError):
            _Cron("invalid")

        # Complex case: 2023-01-01 00:00:05
        c = _Cron("5 0 0 1 1 *", start_dt=start, end_dt=end)
        dates = list(c(current_dt=start))
        self.assertEqual(dates[0], datetime(2023, 1, 1, 0, 0, 5))
        
        # Test wrapping year
        c = _Cron("* * * * 1 *", start_dt=datetime(2023, 2, 1), end_dt=datetime(2024, 2, 1))
        gen = c(datetime(2023, 2, 1))
        d = next(gen)
        self.assertEqual(d.year, 2024)
        self.assertEqual(d.month, 1)

class TestTriggers(unittest.TestCase):
    def test_trigger_validation(self):
        with self.assertRaises(ValueError):
            # start > end
            OnceTrigger(datetime.now(), skip_past=False).model_post_init(None)
            t = OnceTrigger(datetime.now())
            t.start_dt = datetime.now() + timedelta(hours=1)
            t.end_dt = datetime.now()
            t.model_post_init(None)

        with self.assertRaises(ValueError):
            # trigger not in range
            t = OnceTrigger(datetime.now())
            t.start_dt = datetime.now() - timedelta(hours=2)
            t.end_dt = datetime.now() - timedelta(hours=1)
            t.trigger_dt = datetime.now()
            t.model_post_init(None)

    def test_once_trigger(self):
        now = datetime.now()
        t = OnceTrigger(now + timedelta(hours=1))
        
        # First fire
        dt, status = t.get_first_fire_time()
        self.assertEqual(status, "Running")
        self.assertEqual(dt, t.trigger_dt)
        
        # Next fire (should be completed)
        dt, status = t.get_next_fire_time()
        self.assertEqual(status, "Completed")

        # Skip past
        t = OnceTrigger(now - timedelta(hours=1), skip_past=True)
        dt, status = t.get_first_fire_time()
        self.assertEqual(status, "Completed")

    def test_interval_trigger(self):
        now = datetime.now()
        t = IntervalTrigger(interval=10, start_dt=now, end_dt=now+timedelta(seconds=25))
        
        # First
        dt, status = t.get_first_fire_time()
        self.assertEqual(status, "Running")
        self.assertEqual(dt, now)
        
        # Next
        dt, status = t.get_next_fire_time()
        self.assertEqual(status, "Running")
        self.assertEqual(dt, now + timedelta(seconds=10))
        
        # Next
        dt, status = t.get_next_fire_time()
        self.assertEqual(status, "Running")
        self.assertEqual(dt, now + timedelta(seconds=20))
        
        # Next (exceeds end)
        dt, status = t.get_next_fire_time()
        self.assertEqual(status, "Completed")

        # Skip past logic
        past = now - timedelta(seconds=100)
        t = IntervalTrigger(interval=10, start_dt=past, end_dt=now+timedelta(seconds=50), skip_past=True)
        dt, status = t.get_first_fire_time()
        self.assertTrue(dt >= now)

    def test_cron_trigger(self):
        now = datetime.now()
        # Every second
        t = CronTrigger("* * * * * *", start_dt=now, end_dt=now+timedelta(seconds=2))
        
        dt, status = t.get_first_fire_time()
        self.assertEqual(status, "Running")
        
        dt, status = t.get_next_fire_time()
        self.assertEqual(status, "Running")
        
        # Exhausted
        # Manually force iteration end
        t._cron = iter([])
        dt, status = t.get_next_fire_time()
        self.assertEqual(status, "Completed")

    def test_decorators(self):
        t = once(datetime.now())
        self.assertIsInstance(t, OnceTrigger)
        
        t = daily("12:00:00")
        self.assertIsInstance(t, CronTrigger)
        
        t = weekly("12:00:00", 0)
        self.assertIsInstance(t, CronTrigger)
        
        t = every(10)
        self.assertIsInstance(t, IntervalTrigger)
        
        t = crontab("* * * * * *")
        self.assertIsInstance(t, CronTrigger)

class TestEventQueue(unittest.TestCase):
    def test_queue(self):
        q = _EventQueue()
        self.assertTrue(q.empty())
        self.assertEqual(q.qsize(), 0)
        
        evt = Event(type="test")
        q.put(evt)
        self.assertFalse(q.empty())
        self.assertEqual(q.qsize(), 1)
        self.assertEqual(len(q.queue), 1)
        
        got = q.get()
        self.assertEqual(got.type, "test")
        
        # Test get_nowait
        q.put(evt)
        got = q.get_nowait()
        self.assertEqual(got.type, "test")
        
        # Test clear
        q.put(evt)
        q.clear()
        self.assertTrue(q.empty())
        
        # Test timeout
        with self.assertRaises(Empty):
            q.get(timeout=0.01)

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.sched = Scheduler()
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        self.sched.stop()
        # Clean up any leftover files
        if Path(".vxsched").exists():
            shutil.rmtree(".vxsched")
        shutil.rmtree(self.test_dir)

    def test_register_dispatch(self):
        mock_handler = MagicMock()
        mock_handler.__name__ = "mock_handler"
        self.sched.register("test_event", mock_handler)
        
        # Dispatch wait=True
        e = Event(type="test_event")
        self.sched.dispatch(e, wait=True)
        mock_handler.assert_called_once()
        
        # Decorator
        @self.sched("deco_event")
        def deco_handler(app, evt):
            pass
        self.assertIn(deco_handler, self.sched._handlers["deco_event"])
        
        # Unregister
        self.sched.unregister("test_event", mock_handler)
        self.assertNotIn(mock_handler, self.sched._handlers["test_event"])
        
        # Unregister all
        self.sched.unregister("deco_event")
        self.assertEqual(len(self.sched._handlers["deco_event"]), 0)
        
        # Unregister unknown
        with self.assertLogs(level="ERROR"):
            self.sched.unregister("unknown", mock_handler)

    def test_include(self):
        other = Scheduler()
        handler = lambda x, y: None
        other.register("test", handler)
        
        self.sched.include(other)
        self.assertIn(handler, self.sched._handlers["test"])
        
        # Duplicate warning
        with self.assertLogs(level="WARNING"):
            self.sched.include(other)

    def test_run_cycle(self):
        # Test start
        self.assertTrue(self.sched.start())
        self.assertFalse(self.sched.start()) # Already started
        
        # Submit event
        e = Event(type="test")
        self.sched.submit(e)
        self.sched.submit("test_str")
        
        # Submit reserved
        with self.assertLogs(level="WARNING"):
            self.sched.submit(INIT_EVENT)
            
        # Wait briefly
        time.sleep(0.1)
        
        # Stop
        self.sched.stop()
        self.sched.stop() # Already stopped warning
        self.sched.wait()
        
        # Submit after stop
        with self.assertLogs(level="WARNING"):
            self.sched.submit("fail")

    def test_initialize_fail(self):
        # Mock handle to raise exception during INIT_EVENT
        with patch.object(self.sched, 'dispatch', side_effect=Exception("Init Fail")):
            with self.assertLogs(level="ERROR"):
                self.assertFalse(self.sched._initialize())

    def test_stop_exception(self):
        # Start first
        self.sched._stop_mutex.clear() 
        with patch.object(self.sched, 'dispatch', side_effect=Exception("Stop Fail")):
             with self.assertLogs(level="ERROR"):
                 self.sched.stop()

    def test_params_persistence(self):
        # Since code uses Path(".") / ".vxsched", we should change cwd
        cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            # Load empty
            self.sched.load_params()
            
            # Save on stop
            self.sched.params.set_params("foo", "bar", persist=True)
            self.sched._stop_mutex.clear() # pretend running
            self.sched.stop()
            
            # Load again
            sched2 = Scheduler()
            sched2.load_params()
            self.assertEqual(sched2.params.foo, "bar")
        finally:
            os.chdir(cwd)

    def test_load_modules(self):
        # Create a dummy module
        mod_dir = Path(self.test_dir) / "mods"
        mod_dir.mkdir()
        (mod_dir / "test_mod.py").write_text("x = 1")
        (mod_dir / "_ignore.py").write_text("y = 1")
        
        with self.assertLogs(level="INFO") as cm:
            vxsched.load_modules(str(mod_dir))
            # Check logs to verify loading
            self.assertTrue(any("Loading module test_mod.py" in o for o in cm.output))
        
    def test_load_config(self):
        cfg_file = Path(self.test_dir) / "config.json"
        with open(cfg_file, "w") as f:
            json.dump({"test": 1}, f)
            
        self.sched.load_config(cfg_file)
        self.assertEqual(self.sched.config.test, 1)

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_init_command(self):
        args = MagicMock()
        args.target = self.test_dir
        args.examples = True
        
        with patch("vxsched.loggerConfig"):
            init_command(args)
        
        self.assertTrue((Path(self.test_dir) / "config.json").exists())
        self.assertTrue((Path(self.test_dir) / "mods" / "handlers.py").exists())
        
    def test_run_command(self):
        args = MagicMock()
        args.log_level = "DEBUG"
        args.log_file = ""
        args.config = "config.json"
        args.load_params = False
        args.mods = "mods"
        
        # Mock load_modules and app methods
        app = MagicMock()
        with patch("vxsched.loggerConfig") as mock_log, \
             patch("vxsched.load_modules"), \
             patch("pathlib.Path.exists", return_value=True):
            run_command(args, app)
            mock_log.assert_called_with(level="DEBUG", filename="", force=True)
            app.load_config.assert_called()
            app.start.assert_called()
            app.wait.assert_called()
            app.stop.assert_called()

    def test_main(self):
        with patch("sys.argv", ["vxsched.py", "init", "-t", self.test_dir]), \
             patch("vxsched.loggerConfig"):
            main()
            self.assertTrue((Path(self.test_dir) / "config.json").exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
