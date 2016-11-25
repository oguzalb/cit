import sys
import os
from citlib.objects import Index, MYGIT_ROOTDIR, initialized


def help():
    print """
    usage: status
    """


def command(argv):
    initialized()
    if len(argv) > 1:
        help()
        sys.exit(1)

    filename = os.path.join(MYGIT_ROOTDIR, 'index')
    index = Index()
    index.load(filename)
    sha1 = index.write_tree()
    print sha1