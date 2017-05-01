import os
import shutil
import unittest

from citlib.commands.init import command as init_command
from citlib.commands.add import command as add_command
from citlib.commands.checkout import command as checkout_command
from citlib.commands.branch import command as branch_command
from citlib.commands.commit import command as commit_command
from citlib.commands.rm import command as rm_command
from citlib.commands.status import command as status_command
from citlib.objects import Index, MYGIT_ROOTDIR, Branch, Commit


class TestIndex(unittest.TestCase):
    def setUp(self):
        self.repodir = '/tmp/repo/'
        os.mkdir(self.repodir)
        os.chdir('/tmp/repo/')
        init_command([])
        self.file_count = 0
        self.modification_count = 0

    def create_file(self, file_name=None):
        if file_name is None:
            self.file_count += 1
            file_name = 'filename%s.txt' % self.file_count

        file_content = 'first_line%s' % self.file_count
        with open(os.path.join(self.repodir, file_name), 'w') as f:
            f.write(file_content)
        return file_name, file_content

    def modify_file(self, file_name):
        self.modification_count += 1
        modification = "file modification %s" % self.modification_count
        with open(os.path.join(self.repodir, file_name), 'a') as f:
            f.write(modification)

    def assertIndexEquals(self, file_names):
        index = Index()
        index.load(os.path.join(MYGIT_ROOTDIR, 'index'))
        self.assertEquals(len(index.index_entries), len(file_names))
        saved_file_names = [ie.name for ie in index.index_entries]
        for file_name in file_names:
            self.assertIn(file_name, saved_file_names)

    def assertBranchHEADEquals(self, branch_name, file_names):
        master = Branch.from_file(branch_name)
        commit = Commit.from_file(master.sha1text)
        tree = Index.from_tree(2, commit.treesha1)
        saved_file_names = [ie.name for ie in tree.index_entries]
        for file_name in file_names:
            self.assertIn(file_name, saved_file_names)

    def assertFilesEqual(self, file_names):
        files = [f for f in os.listdir(self.repodir) if f != '.cit']
        self.assertEquals(set(files), set(file_names))

    def test_add_remove(self):
        file1_name, _ = self.create_file()
        add_command([file1_name])
        self.assertIndexEquals([file1_name])

        file2_name, _ = self.create_file()
        add_command([file2_name])
        self.assertIndexEquals([file1_name, file2_name])

        rm_command([file1_name])
        self.assertIndexEquals([file2_name])

    def test_checkout(self):
        '''
        Commits, then checks out HEAD~1
        '''
        file1_name, _ = self.create_file()
        add_command([file1_name])
        self.assertIndexEquals([file1_name])
        commit_command(['-m', 'first commit'])

        file2_name, _ = self.create_file()
        add_command([file2_name])
        self.assertIndexEquals([file1_name, file2_name])
        commit_command(['-m', 'second commit'])
        self.assertBranchHEADEquals('master', [file1_name, file2_name])

        checkout_command(['HEAD~1'])
        self.assertIndexEquals([file1_name])

    def test_checkout_last_commit(self):
        '''
        Checks out HEAD~1, then checks out master again
        '''
        file1_name, _ = self.create_file()
        add_command([file1_name])
        self.assertIndexEquals([file1_name])
        commit_command(['-m', 'first commit'])

        file2_name, _ = self.create_file()
        add_command([file2_name])
        self.assertIndexEquals([file1_name, file2_name])
        commit_command(['-m', 'second commit'])
        self.assertBranchHEADEquals('master', [file1_name, file2_name])

        checkout_command(['master'])
        self.assertIndexEquals([file1_name, file2_name])
        self.assertBranchHEADEquals('master', [file1_name, file2_name])

    def test_checkout_branch(self):
        '''
        creates a new branch, adds a commit
        checks out back and forth
        additional file should appear,
          missing file should disappear since there are no changes on it
        '''
        file1_name, _ = self.create_file()
        add_command([file1_name])
        self.assertIndexEquals([file1_name])
        commit_command(['-m', 'first commit'])

        branch_command(['branch1'])
        self.assertBranchHEADEquals('branch1', [file1_name])
        checkout_command(['branch1'])

        file2_name, _ = self.create_file()
        add_command([file2_name])
        self.assertIndexEquals([file1_name, file2_name])
        commit_command(['-m', 'second commit'])
        self.assertBranchHEADEquals('branch1', [file1_name, file2_name])

        checkout_command(['master'])
        self.assertIndexEquals([file1_name])
        self.assertFilesEqual([file1_name])

        checkout_command(['branch1'])
        self.assertIndexEquals([file1_name, file2_name])
        self.assertFilesEqual([file1_name, file2_name])

    def test_status(self):
        removed_file_name, _ = self.create_file('removed_file.txt')
        add_command([removed_file_name])
        self.assertIndexEquals([removed_file_name])
        commit_command(['-m', 'first commit'])

        modified_fs_removed_file_name, _ = self.create_file('modified_fs_removed_file.txt')
        add_command([modified_fs_removed_file_name])
        self.assertIndexEquals([removed_file_name, modified_fs_removed_file_name])
        commit_command(['-m', 'second commit'])
        self.assertBranchHEADEquals('master', [removed_file_name, modified_fs_removed_file_name])

        # staging differences
        # added file
        added_fs_modified_file_name, _ = self.create_file('added_fs_modified_file.txt')
        add_command([added_fs_modified_file_name])

        # removed file
        rm_command([removed_file_name])

        # modify file
        self.modify_file(modified_fs_removed_file_name)
        add_command([modified_fs_removed_file_name])

        # file system differences

        # fs added file
        fs_added_file_name, _ = self.create_file('fs_added_file.txt')

        # fs removed file
        os.remove(modified_fs_removed_file_name)

        # fs modified_file
        self.modify_file(added_fs_modified_file_name)

        (
            (removed_files, changed_files, new_files),
            (fs_removed_files, fs_changed_files, fs_new_files)
        ) = status_command([])

        self.assertEquals(removed_files, [removed_file_name])
        self.assertEquals(changed_files, [modified_fs_removed_file_name])
        self.assertEquals(new_files, [added_fs_modified_file_name])

        self.assertEquals(fs_removed_files, [modified_fs_removed_file_name])
        self.assertEquals(fs_changed_files, [added_fs_modified_file_name])
        self.assertEquals(fs_new_files, [fs_added_file_name])

    def tearDown(self):
        shutil.rmtree(self.repodir)