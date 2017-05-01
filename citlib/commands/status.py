import sys
import os
from citlib.objects import Index, MYGIT_ROOTDIR, Branch, HEAD, Commit, initialized


def help():
    print """
    usage: status
    """


def command(argv):
    initialized()
    if len(argv) > 0:
        help()
        sys.exit(1)

    filename = os.path.join(MYGIT_ROOTDIR, 'index')
    index = Index()
    index.load(filename)
    head = HEAD.from_file()
    if head.ref is None:
        commitsha1 = head.sha1
    else:
        branch = Branch.from_file(head.ref)
        commitsha1 = branch.sha1text

    commit = Commit.from_file(commitsha1)
    commitIndex = index.from_tree(2, commit.treesha1)

    removed, changed, added = index.differences(commitIndex)

    print "Added files:"
    print "\n".join(added) + "\n"
    print "Changed files:"
    print "\n".join(changed) + "\n"
    print "Removed files:"
    print "\n".join(removed) + "\n"

    fs_removed, fs_changed, fs_added = index.filesystem_differences()
    print "Changes not staged for commit"
    print "Added files:"
    print "\n".join(fs_added) + "\n"
    print "Changed files:"
    print "\n".join(fs_changed) + "\n"
    print "Removed files:"
    print "\n".join(fs_removed) + "\n"

    return ((removed, changed, added), (fs_removed, fs_changed, fs_added))