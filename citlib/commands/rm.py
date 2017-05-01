import sys
import os
from citlib.objects import Index, MYGIT_ROOTDIR, initialized


def help():
    print """
    usage: rm filename
    """


def command(argv):
    initialized()
    if len(argv) < 1:
        help()
        sys.exit(1)

    filename = argv[0]
    index = Index()
    index.load(os.path.join(MYGIT_ROOTDIR, 'index'))
    index.remove_file(filename)
    os.remove(filename)
    index.save(os.path.join(MYGIT_ROOTDIR, 'index'))

