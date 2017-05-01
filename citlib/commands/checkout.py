import sys
import os
import re
from citlib.objects import Index, MYGIT_ROOTDIR, Branch, Commit, HEAD, initialized


def help():
    print """
    usage: checkout [HEAD|branch_name][~1]
    """


def command(argv):
    initialized()
    if len(argv) < 1:
        help()
        sys.exit(1)

    ref = argv[0]
    match = re.match("(\w+)(~[1-9][0-9]*){0,1}", ref)
    if match is None:
        help()
        sys.exit(1)
    groups = match.groups()
    ref = groups[0]
    if ref == "HEAD":
        head = HEAD.from_file()
        ref = head.ref

    if groups[1] is None:
        prev_count = 0
    else:
        prev_count = int(groups[1][1:])

    head = HEAD.from_file()

    if head.sha1 is None:
        print >> sys.stderr, "Branch does not have the first commit"
        sys.exit(1)

    checkout_branch = Branch.from_file(ref)
    checkout_commit = Commit.from_file(checkout_branch.sha1text)
    for i in xrange(prev_count):
        if checkout_commit.parent is None:
            print >>sys.stderr, "Last commit doesn't have a parent"
            sys.exit()
        checkout_commit = Commit.from_file(checkout_commit.parent)
    staging = Index()
    staging.load(os.path.join(MYGIT_ROOTDIR, 'index'))
    target_commit_index = Index.from_tree(2, checkout_commit.treesha1)
    non_overwritable_files = staging.list_nonoverwritable_files_by_index(
        target_commit_index)
    if non_overwritable_files:
        print >> sys.stderr, "original file changed, you shouldn't write onto it %s" % non_overwritable_files
        sys.exit()
    current_head = HEAD.from_file()
    current_commit = Commit.from_file(current_head.sha1)
    current_index = Index.from_tree(2, current_commit.treesha1)
    staging.overwrite_repo(current_index, target_commit_index)
    target_commit_index.save(os.path.join(MYGIT_ROOTDIR, 'index'))
    new_head = HEAD()
    if not prev_count:
        new_head.ref = ref
        new_head.sha1 = checkout_commit.sha1
    else:
        new_head.sha1 = checkout_commit.sha1
    new_head.save()
