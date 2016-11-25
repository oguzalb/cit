import sys
import os
from citlib.objects import Index, MYGIT_ROOTDIR, initialized


def help():
    print """
    usage: update-index --add filename
    """


def command(argv):
    initialized()
    if len(argv) < 2:
        help()
        sys.exit(1)

    if argv[1] != '--add':
        help()
        sys.exit(1)

    filename = argv[2]
    index = Index()
    index.load(os.path.join(MYGIT_ROOTDIR, 'index'))
    index.add_file(filename)
    index.save(os.path.join(MYGIT_ROOTDIR, 'index'))
