cit, a reimplementation of git with python
==========================================

```
pip install .
```
to try

Still under development and not refactored yet

This is a script i use to see if the implemented parts are working, these parts are currently working
(remove not implemented fully, does not support directory structure yet)

```
set -e
set -x

rm -f hede*.txt

cit init
echo "test1" >> hede.txt
cit add hede.txt
cit commit . -m "first commit - master branch"

echo "test2" >> hede.txt
touch hede2.txt
cit update-index --add hede2.txt
cit add hede.txt
cit commit . -m "second commit - master branch"

cit branch feature1
cit checkout feature1
echo "test3" >> hede3.txt
rm hede2.txt
echo "test4" >> hede.txt
cit update-index --add hede3.txt
cit update-index --add hede.txt
cit status
cit commit . -m "third commit - feature1 branch"

cit checkout master
cit checkout feature1

cit checkout master~1
cit checkout feature1
cit checkout HEAD~1
cit log
cit branch

cit checkout feature1
HASH=`cit write-tree| tail -n 1`
cit cat-file tree $HASH| awk '{print $1}'| xargs cit cat-file blob
cit cat-file commit `cat .cit/refs/heads/master`
```
