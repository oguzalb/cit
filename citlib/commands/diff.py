from difflib import unified_diff
import sys
import os
from citlib.objects import Index, MYGIT_ROOTDIR, Branch, HEAD, Commit, initialized, Blob


def help():
    print """
    usage: diff
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
    commit_index = index.from_tree(2, commit.treesha1)
    for new_file in commit_index.new_files(index):
        with open(new_file, "r") as f:
            for line in unified_diff([""], f.readlines(), fromfile=new_file, tofile=new_file):
                print line
    removed_files, changed_files = commit_index.changed_files()
    for changed_file in changed_files:
        index_entry = next(
            (i for i in commit_index.index_entries if i.name == changed_file), None)
        blob = Blob.from_saved_blob(index_entry.sha1)
        with open(changed_file, "r") as f:
            for line in unified_diff(blob.content.split(), f.readlines(), fromfile=changed_file, tofile=changed_file):
                print line
    for removed_file in removed_files:
        index_entry = next(
            (i for i in commit_index.index_entries if i.name == removed_file), None)
        blob = Blob.from_saved_blob(index_entry.sha1)
        for line in unified_diff(blob.content.split(), [""], fromfile=removed_file, tofile=removed_file):
            print line
