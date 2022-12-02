import sys
import os
import re
from checker import Checker


def main():
    path = sys.argv[1]
    if path.endswith(".py"):
        Checker.test(path)
    else:
        # returns a list containing the names of the files
        # and subdirectories in the directory given by the path argument
        tests_list = os.listdir(path)
        for file in sorted(tests_list):
            if re.match("test_[0-9]*.py", file):
                Checker.test(os.path.join(path, file))


if __name__ == "__main__":
    main()
