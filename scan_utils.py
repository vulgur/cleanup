import os

output_folder = 'outputs'
PROJECT_PATH_PROP_FILE = 'project_props.txt'
PROJECT_TRUNK = 'trunk'
PROJECT_BOOSTER = 'booster'


# write the scan result
def write_output(filename, set_name):
    if os.path.isdir(output_folder):
        pass
    else:
        os.mkdir(output_folder)
    filename = output_folder + os.sep + filename
    result = list(set_name)
    result.sort()
    output = open(filename, 'w')
    for x in result:
        output.write(x + '\n')
    output.close()


# read project path
def get_project_path(path):
    for line in open(path):
        line = line.strip()
        return line


# read project prop file
def get_project_props():
    props = {}
    with open(PROJECT_PATH_PROP_FILE) as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                parts = line.split('=')
                if len(parts) > 1:
                    props[parts[0]] = parts[1]
    return props


def make_temp_file(file_path):
    f = open(file_path, 'rb')
    tmp = open('tmp_file', 'wb')
    while True:
        b = f.read(1)
        if not b:
            break
        if b == '\r':
            b = '\r\n'
        tmp.write(b)
    tmp.close()
    return tmp


def get_file_lines(file_path):
    f = open(file_path)
    lines = f.readlines()
    f.close()
    if len(lines) == 1:
        return lines[0].split('\r')
    else:
        return lines
