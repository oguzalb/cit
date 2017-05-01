import sys
import os
from citlib.objects import Index, MYGIT_ROOTDIR, initialized


def help():
    print """
    usage: add filename
    """


def command(argv):
    initialized()
    if len(argv) < 1:
        help()
        sys.exit(1)

    filename = argv[0]
    index = Index()
    index.load(os.path.join(MYGIT_ROOTDIR, 'index'))
    index.add_file(filename)
    index.save(os.path.join(MYGIT_ROOTDIR, 'index'))

