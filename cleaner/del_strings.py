import os
import re

project_path = ""
unused_strings = set()


def read_unused_strings(path):
    global unused_strings
    for line in open(path):
        line = line.strip()
        if not line == '':
            unused_strings.add(line)


def delete_xml_strings(res_folder_path):
    global unused_strings
    size = 0
    if len(unused_strings) == 0:
        print 'no strings to be deleted'
    else:

        pattern = re.compile('<string name="(\w*)"')

        for folder in os.listdir(res_folder_path):
            if folder.startswith('values'):
                for f in os.listdir(os.path.join(res_folder_path, folder)):
                    if 'strings' in f:
                        # infile = res_folder_path + os.sep + folder + os.sep + f
                        infile = os.path.join(res_folder_path, folder, f)
                        # outfile = res_folder_path + os.sep + folder + os.sep + "temp"
                        outfile = os.path.join(res_folder_path, folder, "temp")
                        infp = open(infile, 'rb')
                        outfp = open(outfile, 'wb')
                        before = os.path.getsize(infile)
                        is_multilines = False
                        for line in infp:
                            if is_multilines and line.strip().endswith('</string>'):
                                is_multilines = False
                                continue
                            elif is_multilines:
                                continue
                            else:
                                m = pattern.search(line)
                                if m:
                                    name = m.group(1)
                                    if name in unused_strings:
                                        if not line.strip().endswith('</string>'):
                                            is_multilines = True
                                        else:
                                            is_multilines = False
                                    else:
                                        outfp.write(line)
                                else:
                                    outfp.write(line)
                        infp.close()
                        outfp.close()
                        after = os.path.getsize(outfile)
                        size = size + (before - after)
                        os.remove(infile)
                        os.rename(outfile, infile)
        print "delete strings size=" + str(size / 1024) + "K"
    return size, unused_strings

