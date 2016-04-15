import glob
import inspect
import os
import unittest

import sys
import xmlrunner


def get_module_path():
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    file_name = info.filename
    return os.path.dirname(os.path.abspath(file_name))


def __get_suites():
    path = get_module_path()
    test_path = os.path.abspath(os.path.join(path, 'wshubsapi', 'test'))
    test_files = glob.glob(os.path.join(test_path, 'test*.py'))
    relative_test_files = [test_file.split(os.sep)[-3:] for test_file in test_files]
    module_strings = [".".join(test_file)[:-3] for test_file in relative_test_files]
    print "this is a test", path, test_path, test_files
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
    suite = unittest.TestSuite(__get_suites())
    __run_test(suite)


if __name__ == '__main__':
    run_unit_test()
