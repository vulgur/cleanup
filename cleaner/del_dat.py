import os

project_path = ""
unused_tables = set()


def read_unused_tables(path):
    global unused_tables
    for line in open(path):
        line = line.strip()
        if not line == '':
            unused_tables.add(line)


def delete_tables(filename):
    global unused_tables
    size = 0
    if len(unused_tables) == 0:
        print 'no tables to be deleted'
    else:
        infile = filename
        outfile = filename + ".tmp"
        infp = open(infile, 'rb')
        outfp = open(outfile, 'wb')
        before = os.path.getsize(infile)
        for line in infp:
            tablename = line.split(":")[0]
            if tablename in unused_tables:
                continue
            else:
                outfp.write(line)

        infp.close()
        # outfp.write(result)
        outfp.close()
        after = os.path.getsize(outfile)
        size = size + (before - after)
        os.remove(infile)
        os.rename(outfile, infile)
        print "deleted table dat size=" + str(size / 1024) + "K"
    return size, unused_tables


# read project path
def read_project_path(path):
    global project_path
    for line in open(path):
        line = line.strip()
        project_path = line

