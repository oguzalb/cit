import sys
import os
from citlib.objects import Index, MYGIT_ROOTDIR, Commit, Branch, HEAD, initialized


def help():
    print """
    usage: commit -m "message"
    """


def command(argv):
    initialized()
    if len(argv) < 2 or argv[0] != '-m':
        help()
        sys.exit(1)
    message = argv[1]
    filename = os.path.join(MYGIT_ROOTDIR, 'index')
    index = Index()
    index.load(filename)
    sha1 = index.write_tree()
    head = HEAD.from_file()
    if head.ref is None:
        print >>sys.stderr, "the head is detached!"
        sys.exit(1)

    branch = Branch.from_file(head.ref)
    # parent will be fixed when branch is implemented
    commit = Commit(sha1, "Oguz", message, branch.sha1text)
    commitsha1 = commit.save()
    branch.sha1text = commitsha1
    branch.save()
    index.save(filename)
    print commitsha1

