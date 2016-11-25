import sys
from citlib.objects import  HEAD, Branch, Commit, initialized


def help():
    print """
    usage: log [branch_name]
    """


def command(argv):
    initialized()
    if len(argv) > 2:
        help()
        sys.exit(1)

    if len(argv) == 2:
        branch_name = argv[1]
        branch = Branch.from_file(branch_name)
        if branch.sha1text is None:
            print >> sys.stderr, "Branch does not have the first commit"
            sys.exit(1)
        sha1text = branch.sha1text
    else:
        head = HEAD.from_file()
        sha1text = head.sha1

    commit = Commit.from_file(sha1text)

    while commit is not None:
        print "hash: %s\ntree: %s\nauthor: %s\nmessage: %s\n" % (
            commit.sha1, commit.treesha1, commit.author, commit.message)
        if commit.parent is not None:
            commit = Commit.from_file(commit.parent)
        else:
            commit = None
