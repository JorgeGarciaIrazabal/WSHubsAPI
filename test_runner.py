import glob
import inspect
import os
import threading
import unittest

import sys

import time
import xmlrunner


def get_module_path():
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    file_name = info.filename
    return os.path.dirname(os.path.abspath(file_name))


def __get_suites(tests_path):
    path = get_module_path()
    tests_path = os.path.abspath(os.path.join(path, tests_path))
    test_files = glob.glob(tests_path)
    relative_test_files = [test_file.split(os.sep)[-4:] for test_file in test_files]
    module_strings = [".".join(test_file)[:-3] for test_file in relative_test_files]
    print "this is a test", path, tests_path, test_files
    print module_strings
    for t in module_strings:
        try:
            unittest.defaultTestLoader.loadTestsFromName(t)
            print t, 'good'
        except Exception as e:
            print t, str(e)
    return [unittest.defaultTestLoader.loadTestsFromName(test_file) for test_file in module_strings]


def __run_test(suite):
    runner = xmlrunner.XMLTestRunner(output='test-reports')
    runner.run(suite)


def run_unit_test():
    suite = unittest.TestSuite(__get_suites('wshubsapi/test/unit/test*.py'))
    __run_test(suite)


def run_integration_test():
    def exec_server():
        execfile("wshubsapi/test/integration/resources/tornado_ws_server.py")

    t = threading.Thread(target=exec_server)
    t.setDaemon(True)
    t.start()
    time.sleep(1)  # wait sever to start
    suite = unittest.TestSuite(__get_suites('wshubsapi/test/integration/test*.py'))
    __run_test(suite)


if __name__ == '__main__':
    try:
        if len(sys.argv) <= 1:
            run_unit_test()
        else:
            if sys.argv[1] in ("unit", "all"):
                run_unit_test()
            if sys.argv[1] in ("integration", "all"):
                run_integration_test()
    finally:
        pass
        # os._exit(0)
