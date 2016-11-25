import sys
from citlib.objects import Blob, Index, Commit, initialized


def help():
    print """
    usage: cat-file [blob|tree|commit] hash
    """

def command(argv):
    initialized()
    if len(argv) < 3:
        help()
        sys.exit(1)

    object_type = argv[1]
    sha1text = argv[2]
    if object_type == "blob":
        blob = Blob.from_saved_blob(sha1text)
        print blob.original_content
    elif object_type == "tree":
        # version should be read from the file?
        tree = Index.from_tree(2, sha1text)
        for index_entry in tree.index_entries:
            print "%s %s" % (index_entry.sha1, index_entry)
    elif object_type == "commit":
        commit = Commit.from_file(sha1text)
        print "commit: %s\ntree: %s\nauthor: %s\nmessage: %s\nparent: %s" % (sha1text, commit.treesha1, commit.author, commit.message, commit.parent)
    else:
        print >>sys.stderr, "%s is not an object type" % object_type

