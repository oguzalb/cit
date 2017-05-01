import os
import sys
import hashlib
from StringIO import StringIO
from struct import unpack, pack
from collections import namedtuple
from string import hexdigits


MYGIT_ROOTDIR = '.cit'
OBJECTS_DIR = os.path.join(MYGIT_ROOTDIR, 'objects')
REFS_DIR = os.path.join(MYGIT_ROOTDIR, 'refs')
HEADS_DIR = os.path.join(REFS_DIR, 'heads')
HEAD_DIR = os.path.join(MYGIT_ROOTDIR, 'heads')


def calc_sha1_file(content):
    return hashlib.sha1('blob %s\x00' % len(content) + content).hexdigest()


def hexify_byte(byte):
    return str(hexdigits[ord(byte) / 16]) + str(hexdigits[ord(byte) % 16])


#def bytify_hex(hexbytes):
#    hexbytes = hexbytes.lower()
#    result = []
#    for i in xrange(0, len(hexbytes), 2):
#        result.append(chr(hexdigits.index(hexbytes[i])*16 + hexdigits.index(hexbytes[i+1])))
#    return "".join(result)


def take_name(arr, i):
    name = ''
    while arr[i] != '\0':
        name += arr[i]
        i += 1
    # the zero paddings complete it to the next 8
    while i < len(arr) and arr[i] == '\0':
        i += 1
    return name, i


def blob_save_path(first_byte):
    return os.path.join(OBJECTS_DIR, hexify_byte(first_byte))


class FileTypes:
    BLOB = 1
    TREE = 2
    COMMIT = 3


class Blob(dict):
    @classmethod
    def from_file(self, filename):
        if '/' in filename:
            print >>sys.stderr, 'fullpath not permitted (yet)!'
            sys.exit(1)
        with open(filename) as f:
            content = f.read()
        blob = Blob()
        blob.content = 'blob %s\x00' % len(content) + content
        blob.sha1 = calc_sha1_file(blob.content)
        blob.content_size = len(content)
        return blob

    @classmethod
    def from_saved_blob(self, sha1text):
        blob = Blob()
        # hexify first byte
        first_byte = chr(int(sha1text[:2], 16))
        dirpath = blob_save_path(first_byte)
        filepath = os.path.join(dirpath, sha1text[2:])
        with open(filepath, 'r') as f:
            blob.content = f.read()
        blob.sha1 = sha1text
        blob.content_size = blob.content[blob.content.index('\x00') + 1:]
        return blob

    @property
    def original_content(self):
        return self.content[self.content.index('\x00') + 1:]

    def save(self):
        # hexify first byte
        first_byte = chr(int(self.sha1[:2], 16))
        dirpath = blob_save_path(first_byte)
        filepath = os.path.join(dirpath, self.sha1[2:])
        with open(filepath, 'w') as f:
            f.write(self.content)


def read_32bit(arr, i):
    # unsigned 4 byte int
    return unpack(">I", arr[i:i+4])[0], i+4


def read_16bit(arr, i):
    # unsigned 2 byte int
    return unpack(">H", arr[i:i+2])[0], i+2


IndexEntry = namedtuple('IndexEntry', (
    'ctimesec', 'ctimenano',
    'mtimesec', 'mtimenano', 'dev', 'ino',
    'perms', 'otype', 'uid', 'gid', 'content_size',
    'sha1', 'flags', 'name'
))


class Index(object):
    def init_file(self, filename):
        print "Initializing init"
        with open(filename, 'w') as f:
            f.write('DIRC')
            # version, entry count
            f.write(pack('>II', 2, 0))
        
    def load(self, filename):
        print "loading from %s" % filename
        with open(filename, 'r') as f:
            content = f.read()
        if content[:4] != 'DIRC':
            print >>sys.stderr, 'Wrong signature for index file'
            sys.exit(1)
        i = 4
        self.version, i = read_32bit(content, i)
        self.entry_count, i = read_32bit(content, i)
        print "entry count: %s" % self.entry_count
        index_entries = []
        for entry_index in xrange(0, self.entry_count):
            index_entry, i = self.read_index_entry(self.version, content, i)
            index_entries.append(index_entry)
        self.index_entries = index_entries
        print "index_entries: %s" % index_entries

    def write_tree(self):
        # think about length stuff later
        stream = StringIO()
        stream.write('tree 0\x00')
        for entry in self.index_entries:
            self.write_index_entry(stream, entry)
        sha1 = calc_sha1_file(stream.getvalue())
        # hexify first byte
        first_byte = chr(int(sha1[:2], 16))
        dirpath = blob_save_path(first_byte)
        filepath = os.path.join(dirpath, sha1[2:])
        with open(filepath, 'w') as f:
            f.write(stream.getvalue())
        print "Written the tree, %s %s" % (filepath, sha1)
        return sha1

    @classmethod
    def from_tree(cls, version, sha1):
        # hexify first byte
        first_byte = chr(int(sha1[:2], 16))
        dirpath = blob_save_path(first_byte)
        filepath = os.path.join(dirpath, sha1[2:])
        with open(filepath, 'r') as f:
            content = f.read()
        if not content.startswith('tree 0\x00'):
            print >>sys.stderr, "%s is not a tree" % sha1
            sys.exit(1)
        index = Index()
        i = 7
        index_entries = []
        index.version = 2
        while i < len(content):
            index_entry, i = cls.read_index_entry(version, content, i)
            index_entries.append(index_entry)
        index.index_entries = index_entries
        index.entry_count = len(index_entries)
        return index

    def new_files(self, other_index):
        files = {e.name for e in self.index_entries}
        other_files = {e.name for e in other_index.index_entries}
        return other_files - files

    def changed_files(self, other_index):
        removed = []
        changed = []
        # not yet
        added = []
        for index_entry in self.index_entries:
            if not os.path.isfile(index_entry.name):
                removed.append(index_entry.name)
                continue
            with open(index_entry.name, 'r') as f:
                content = f.read()
            blob = Blob.from_saved_blob(index_entry.sha1)
            if content != blob.original_content:
                changed.append(index_entry.name)
        return removed, changed

    def list_nonoverwritable_files_by_index(self, other_index):
        # TODO additional files
        files = []
        for index_entry in self.index_entries:
            filename = index_entry.name
            other_index_entry = next(
                (i for i in other_index.index_entries if i.name == index_entry.name), None)
            # Find the files that are different in the staging (self) and the checkout revision
            # if there are no differences then doing nothing is fine
            # if there are differences then we check the file content to see if it is different than the staging
            # if not, that's also fine
            # if the file content is changed and it doesn't fit the other branch then we complain
            if other_index_entry is not None and os.path.isfile(filename):
                other_index_entry_blob = Blob.from_saved_blob(other_index_entry.sha1)
                index_entry_blob = Blob.from_saved_blob(index_entry.sha1)
                if index_entry_blob.original_content != other_index_entry_blob.original_content:
                    print "|%s|%s|1" % (
                        index_entry_blob.original_content, other_index_entry_blob.original_content)
                    with open(filename, "r") as f:
                        content = f.read()
                    if index_entry_blob.original_content != content:
                        files.append(filename)
                        print "|%s|%s|2" % (content, index_entry_blob.original_content)
        # check if there will be new files that will be added by the new tree
        # which might override an untracked file
        for other_index_entry in other_index.index_entries:
            if next((i for i in self.index_entries if i.name == other_index_entry.name), None):
                continue
            if os.path.isfile(other_index_entry.name):
                files.append(other_index_entry.name)
        return files

    def overwrite_repo(self, commit_index, target_commit_index):
        # If the target commit file content is the same content with current commit file content
        #   don't touch the file
        # else:
        #   if the file content is different from current_commit fail
        for target_commit_index_entry in target_commit_index.index_entries:
            filename = target_commit_index_entry.name
            target_commit_blob = Blob.from_saved_blob(target_commit_index_entry.sha1)
            index_entry = next(
                (i for i in commit_index.index_entries if i.name == target_commit_index_entry.name), None)
            if index_entry is None:
                print "writing to %s |%s|", (filename, target_commit_blob.original_content)
                with open(filename, "w") as f:
                    f.write(target_commit_blob.original_content)
                continue

            cur_index_blob = Blob.from_saved_blob(index_entry.sha1)
            if cur_index_blob.original_content != target_commit_blob.original_content or not os.path.exists(filename):
                print "writing to %s |%s|", (filename, target_commit_blob.original_content)
                with open(filename, "w") as f:
                    f.write(target_commit_blob.original_content)

        for index_entry in commit_index.index_entries:
            if next((i for i in target_commit_index.index_entries if
                     i.name == index_entry.name), None):
                continue
            if os.path.isfile(index_entry.name):
                os.remove(index_entry.name)

    @staticmethod
    def read_index_entry(version, content, i):
        e_ctimesec, i = read_32bit(content, i)
        e_ctimenano, i = read_32bit(content, i)
        e_mtimesec, i = read_32bit(content, i)
        e_mtimenano, i = read_32bit(content, i)
        e_dev, i = read_32bit(content, i)
        e_ino, i = read_32bit(content, i)
        mode, i = read_32bit(content, i)
        # reads wrong, should be revisited
        e_perms = mode & (0x0fff)
        e_otype = (mode & (0xf000)) >> 12
        e_uid, i = read_32bit(content, i)
        e_gid, i = read_32bit(content, i)
        e_content_size, i = read_32bit(content, i)
        e_sha1 = content[i:i+40]
        i += 40
        e_flags, i = read_16bit(content, i)
        # version 3
        if version > 3:
            e_extended_flag, i = read_16bit(content, i)
        e_name, i = take_name(content, i)
        index_entry = IndexEntry(
            ctimesec=e_ctimesec, ctimenano=e_ctimenano, mtimesec=e_mtimesec,
            mtimenano=e_mtimenano, dev=e_dev, ino=e_ino, perms=e_perms,
            otype=e_otype, uid=e_uid, gid=e_gid, content_size=e_content_size,
            sha1=e_sha1, flags=e_flags, name=e_name)
        return index_entry, i

    def write_index_entry(self, f, e):
        # fix later
        mode = 0
        f.write(pack(
            '>IIIIIIIIII', e.ctimesec, e.ctimenano, e.mtimesec, e.mtimenano,
            e.dev, e.ino, mode, e.uid, e.gid, e.content_size))
        f.write(e.sha1)
        f.write(pack('>H', e.flags))
        if self.version > 3:
            f.write(pack('>H', e.extended_flags))
        f.write(e.name + '\0' * (8-len(e.name)%8))

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write('DIRC')
            f.write(pack('>II', self.version, self.entry_count))
            print "saving %s to %s" % (self.index_entries, filename)
            for e in self.index_entries:
                self.write_index_entry(f, e)

    def add_file(self, filename):
        blob = Blob.from_file(filename)
        blob.save()
        s = os.stat(filename)
        entry = IndexEntry(
            ctimesec=int(s.st_ctime), ctimenano=0, mtimesec=int(s.st_mtime),
            mtimenano=0, dev=s.st_rdev, ino=s.st_ino, perms=0, otype=0,
            uid=s.st_uid, gid=s.st_gid, content_size=blob.content_size,
            sha1=blob.sha1, flags=0, name=filename)
        index = next(
            (i for i, e in enumerate(self.index_entries)
             if e.name==entry.name), None)
        if index is not None:
            self.index_entries[index] = entry
        else:
            self.entry_count += 1
            self.index_entries.append(entry)
        self.index_entries.sort(key=lambda x: x.name)

    def remove_file(self, filename):
        index = next((i for i, _ in enumerate(self.index_entries)), None)
        if index is None:
            print >>sys.stderr, "%s is not found" % filename
            sys.exit(1)
        self.index_entries.pop(index)
        self.index_entries.sort(key=lambda x:x.name)
        self.entry_count -= 1


class Commit(object):
    def __init__(self, treesha1, author, message, parent):
        self.treesha1 = treesha1
        self.author = author
        self.message = message
        self.parent = parent
        self.sha1 = calc_sha1_file(
            "commit 0\x00%s\n%s\n%s\n%s\n" % (
                self.treesha1, self.author, self.message, self.parent))

    def save(self):
        content = "commit 0\x00%s\n%s\n%s\n%s\n" % (
            self.treesha1, self.author, self.message, self.parent)
        sha1 = calc_sha1_file(content)
        # hexify first byte
        first_byte = chr(int(sha1[:2], 16))
        dirpath = blob_save_path(first_byte)
        filepath = os.path.join(dirpath, sha1[2:])
        with open(filepath, 'w') as f:
            f.write(content)
        return sha1

    @classmethod
    def from_file(self, sha1text):
         # hexify first byte
        first_byte = chr(int(sha1text[:2], 16))
        dirpath = blob_save_path(first_byte)
        filepath = os.path.join(dirpath, sha1text[2:])
        with open(filepath, 'r') as f:
            raw_content = f.read()
            content = [f for f in raw_content.split('\n')]
        if not content[0].startswith("commit 0\x00"):
            print >>sys.stderr, "This is not a commit object"
        content[0] = content[0][9:]
        treesha1 = content[0]
        author = content[1]
        message = content[2]
        parent = content[3] if content[3] != "None" else None
        commit = Commit(treesha1, author, message, parent)
        return commit


class HEAD(object):
    def __init__(self):
        self.path = os.path.join(MYGIT_ROOTDIR, 'HEAD')
        self.ref = None

    def init_head(self):
        if not os.path.exists(MYGIT_ROOTDIR):
            os.makedirs(MYGIT_ROOTDIR)
        with open(self.path, 'w') as f:
            f.write('ref: refs/heads/master')

    @classmethod
    def from_file(self):
        head = HEAD()
        if not os.path.exists(head.path):
            print >>sys.stderr, 'HEAD does not exist'
            sys.exit(1)
        with open(head.path, 'r') as f:
            content = f.read()
        if not content.startswith("ref: "):
            head.sha1 = content
            head.ref = None
            return head
        head.ref = content[content.rfind('/') + 1:]
        cur_branch = Branch.from_file(head.ref)
        head.sha1 = cur_branch.sha1text
        return head

    def save(self):
        if self.ref is None:
            content = self.sha1
        else:
            content = 'ref: refs/heads/%s' % self.ref
        with open(self.path, 'w') as f:
            f.write(content)

       
class Branch(object):
    def __init__(self, name, sha1text=None):
        self.name = name
        self.sha1text = sha1text

    @classmethod
    def init_heads(self):
        if not os.path.exists(MYGIT_ROOTDIR):
            os.makedirs(MYGIT_ROOTDIR)
        if not os.path.exists(REFS_DIR):
            os.makedirs(REFS_DIR)
        if not os.path.exists(HEADS_DIR):
            os.makedirs(HEADS_DIR)
        with open(os.path.join(HEADS_DIR, 'master'), 'w') as f:
            f.write('None')

    @property
    def branch_path(self):
        branch_path = os.path.join(HEADS_DIR, self.name)
        return branch_path
 
    @classmethod
    def init_branch(cls, name, sha1text):
        branch = Branch(name)
        if os.path.exists(branch.branch_path):
            print >>sys.stderr, 'Branch already exists: %s' % name
            sys.exit(1)

        if os.path.exists(branch.branch_path):
            print >>sys.stderr, 'Branch already exists: %s' % name
            sys.exit(1)
        branch.sha1text = sha1text
        branch.save()
        return branch

    def save(self):
        with open(self.branch_path, 'w') as f:
            f.write(self.sha1text)

    @classmethod
    def list_branches(cls):
        return [
            f for f in os.listdir(HEADS_DIR)
            if os.path.isfile(os.path.join(HEADS_DIR, f))]

    @classmethod
    def from_file(cls, name):
        branch = Branch(name)
        if not os.path.exists(branch.branch_path):
            print >>sys.stderr, 'Branch does not exist: %s' % name
            sys.exit(1)
        with open(branch.branch_path, 'r') as f:
            branch.sha1text = f.read()
            if branch.sha1text == 'None':
                branch.sha1text = None
        return branch


def init_db():
    if not os.path.exists(MYGIT_ROOTDIR):
        os.makedirs(MYGIT_ROOTDIR)
    if not os.path.exists(OBJECTS_DIR):
        os.makedirs(OBJECTS_DIR)
    for i in xrange(0, 256):
        dirname = blob_save_path(chr(i))
        if not os.path.exists(dirname):
            os.makedirs(dirname)


def initialized():
    if not os.path.exists(MYGIT_ROOTDIR):
        print >>sys.stderr, "Not an initialized cit repo"
        sys.exit(1)
