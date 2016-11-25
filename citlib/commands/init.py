import sys
import os
from citlib.objects import init_db, MYGIT_ROOTDIR, Index, Branch, HEAD, initialized


def help():
    print """
    usage: init
    """


def command(argv):
    if len(argv) > 1:
        help()
        sys.exit(1)

    init_db()
    index = Index()
    index.init_file(os.path.join(MYGIT_ROOTDIR, 'index'))
    Branch.init_heads()
    head = HEAD()
    head.init_head()
