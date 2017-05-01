import sys
from citlib.objects import Branch, HEAD, initialized


def help():
    print """
    usage: branch [branch_name]
    """


def list_branches():
    branches = Branch.list_branches()
    head = HEAD.from_file()
    for b in branches:
        print b,
        print "*" if head.ref == b else ""


def create_branch(branch_name):
    head = HEAD.from_file()
    sha1text = head.sha1
    branch = Branch(branch_name, sha1text=sha1text)
    branch.save()


def command(argv):
    initialized()
    if len(argv) == 1:
        create_branch(argv[0])
        return

    if len(argv) == 0:
        list_branches()
        return

    help()
    sys.exit(1)

