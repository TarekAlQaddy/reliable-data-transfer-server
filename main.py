import sys
import SelectiveRepeat
import StopAndWait
import GoBackN


def print_usage():
    print("""\nUsage: main.py option config-file-name\n
    option:\n-st:\tstop and wait\n-sr:\tselective repeat\n-go:\tgo back N\n""")


if len(sys.argv) < 3:
    print_usage()
elif len(sys.argv) == 3:
    method = sys.argv[1]
    file_name = sys.argv[2]
    if method == '-sr':
        SelectiveRepeat.start(file_name)
    elif method == '-st':
        StopAndWait.start(file_name)
    elif method == '-go':
        GoBackN.start(file_name)
else:
    print_usage()
