import os
import sys
import time

import cleaner.del_drawables as del_drawables
import cleaner.del_layouts as del_layouts
import cleaner.del_styles as del_styles
import cleaner.del_strings as del_strings
import cleaner.del_dat as del_dat
import cleaner.del_animations as del_animations


# read project path
import scan_utils


def get_project_path(path):
    for line in open(path):
        line = line.strip()
        return line


def add_to_list(s, l):
    sorted_list = list(s)
    sorted_list.sort()
    for e in sorted_list:
        l.append(e)


def write_to_log(filename, logs):
    if os.path.isdir(output_folder):
        pass
    else:
        os.mkdir(output_folder)
    filename = output_folder + os.sep + filename
    output = open(filename, 'w')
    for x in logs:
        output.write(x + '\n')
    output.close()


if __name__ == '__main__':

    size = 0
    total_size = 0
    deleted = set()
    total_deleted = []

    if len(sys.argv) > 1:
        project_name = sys.argv[1]
        project_dict = scan_utils.get_project_props()
        if project_name in project_dict:
            project_path = project_dict[project_name]
        else:
            project_path = get_project_path("project_path.txt")
    else:
        project_path = get_project_path("project_path.txt")

    print "Project path :", project_path
    res_folder = os.path.join(project_path, "res")
    output_folder = "outputs"

    args = sys.argv

    layout_out_path = os.path.join("outputs", "result_layouts.txt")
    del_layouts.read_unused_layouts(layout_out_path)
    (size, deleted) = del_layouts.delete_layouts()
    total_size += size
    total_deleted.append('--------------- layouts ' + str(size / 1024) + "K")
    add_to_list(deleted, total_deleted)

    style_out_path = os.path.join("outputs", "result_styles.txt")
    del_styles.read_unused_styles(style_out_path)
    (size, deleted) = del_styles.delete_xml_styles(res_folder)
    total_size += size
    total_deleted.append('--------------- styles ' + str(size / 1024) + "K")
    add_to_list(deleted, total_deleted)

    animation_out_path = os.path.join("outputs", "result_animations.txt")
    del_animations.read_unused_animations(animation_out_path)
    (size, deleted) = del_animations.delete_animations()
    total_size += size
    total_deleted.append('--------------- animations ' + str(size / 1024) + "K")
    add_to_list(deleted, total_deleted)

    drawable_out_path = os.path.join("outputs", "result_drawables.txt")
    del_drawables.read_unused_styles(drawable_out_path)
    (size, deleted) = del_drawables.delete_pics()
    total_size += size
    total_deleted.append('--------------- drawables ' + str(size / 1024) + "K")
    add_to_list(deleted, total_deleted)

    string_out_path = os.path.join("outputs", "result_strings.txt")
    del_strings.read_unused_strings(string_out_path)
    (size, deleted) = del_strings.delete_xml_strings(res_folder)
    total_size += size
    total_deleted.append('--------------- strings ' + str(size / 1024) + "K")
    add_to_list(deleted, total_deleted)

    dat_file = os.path.join(project_path, "assets", "kfmt.dat")
    dat_out_path = os.path.join("outputs", "result_tables.txt")
    del_dat.read_unused_tables(dat_out_path)
    (size, deleted) = del_dat.delete_tables(dat_file)
    total_size += size
    total_deleted.append('--------------- tables ' + str(size / 1024) + "K")
    add_to_list(deleted, total_deleted)

    print "total cleanup size=" + str(total_size / 1024) + "K"
    total_deleted.append('---------------')
    total_deleted.append("total cleanup size=" + str(total_size / 1024) + "K")

    cleanup_filename = "cleanup" + time.strftime("%Y-%m-%d-%H%M%S", time.localtime()) + '.log'
    write_to_log(cleanup_filename, total_deleted)