__author__ = 'Wang Shudao'

from resources import Layout
from resources import Drawable
from resources import String
from resources import Animation
from resources import Style
import os
import re
import sys
import scan_utils

used_layouts = set()
used_drawables = set()
used_strings = set()
used_styles = set()
used_animations = set()

used_ids = set()
all_ids = set()

used_class = set()  # for custom views
view_dict = {}  # for custom views

used_tables = set()
all_tables = set()
cm_reports = set()
exclusions = set()

drawable_dict = {}
layout_dict = {}
style_dict = {}
string_dict = {}
animation_dict = {}

output_folder = 'outputs'
kfmt_table_pre = ('cm_', 'cmlite_')
builtin_styles = ('Theme', 'Dialog')


def _get_table_in_line(line):
    tables = []
    for pre in kfmt_table_pre:
        if pre in line:
            re_str = r'"(' + pre + r'[\w\d_]*)"'
            p = re.compile(re_str)
            m = p.findall(line)
            if m:
                for item in m:
                    tables.append(item)
                    # if 'cmlite' in item: print '>>>', line, item
    return tables


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


# read exclusions
def get_exclusion_set(path):
    e = set()
    for line in open(path):
        line = line.strip()
        e.add(line)
    return e


# read java files in src
def read_all_java(src_path):
    for f in os.listdir(src_path):
        if os.path.isdir(os.path.join(src_path, f)):
            read_all_java(os.path.join(src_path, f))
        else:
            filename = f.split('.')
            if len(filename) > 1:
                name = filename[0]
                ext = filename[1]
                if ext.lower() == 'java':
                    read_class(os.path.join(src_path, f))
                else:
                    pass
            else:
                pass


# read one java file
def read_class(f):
    global used_layouts
    global used_drawables
    global used_strings
    global used_styles
    global used_animations
    global cm_reports
    global all_ids
    global used_class
    global used_ids

    p_java = re.compile('.*class\s+.*\s+extends\s+.*')
    p_layout = re.compile('R\.layout\.(\w*)')
    p_drawable = re.compile('R\.drawable\.(\w*)')
    p_string = re.compile('R\.string\.(\w*)')
    p_string_android = re.compile('android\.R\.string\.(\w*)')
    p_style = re.compile('R\.style\.(\w*)')
    p_style_android = re.compile('android\.R\.style\.(\w*)')
    p_anim = re.compile('R\.anim\.(\w*)')
    p_id = re.compile('R\.id\.(\w*)')

    p_report = re.compile('KInfocClientAssist\.getInstance\(\)\.reportData')
    p_force_report = re.compile('KInfocClientAssist\.getInstance\(\)\.forceReportData')
    p_report_param = re.compile('KInfocClientAssist\.getInstance\(\)\.reportData\(\"(\w*)\".*')
    p_force_report_param = re.compile('KInfocClientAssist\.getInstance\(\)\.forceReportData\(\"(\w*)\".*')
    p_table = re.compile('\"(\w*)\"')


    # p_br_1 = re.compile('R\.?$')
    # p_br_2 = re.compile('R\.(\w+)\.?$')
    p_br = re.compile('R\.?(\w+)?\.?$')
    p_br_tail = re.compile('^\.?(\w*)?\.?(\w*)?')
    p_res = re.compile('R\.(\w+)\.(\w+)')


    is_macro = False
    is_comment = False
    is_break_line = False
    filename = os.path.basename(f)
    class_name = None

    break_res = None

    for line in open(f):
        line = line.strip()
        # macro
        if line.find('BUILD_CTRL:IF') > -1:
            is_macro = True
        if line.find('BUILD_CTRL:ENDIF') > -1:
            is_macro = False
        # one line comment
        if line.startswith("//"):
            continue
        # multi-line comment
        if line.startswith("/**") > 0 or line.startswith("/*") > 0:
            is_comment = True
        if line.find("*/") >= 0:
            is_comment = False
            continue
        if is_comment:
            if is_macro:
                pass
            else:
                continue

        if is_break_line:
            m_br_tail = p_br_tail.search(line)
            if m_br_tail:
                break_res += m_br_tail.group()
                m_res = p_res.match(break_res)
                if m_res:
                    res_type = m_res.group(1)
                    res_name = m_res.group(2)
                    if res_type == 'string':
                        used_strings.add(res_name)
                    elif res_type == 'layout':
                        used_layouts.add(res_name)
                    elif res_type == 'style':
                        used_styles.add(res_name)
                    elif res_type == 'drawable':
                        used_drawables.add(res_name)
                    elif res_type == 'anim':
                        used_drawables.add(res_name)
                    elif res_type == 'id':
                        used_ids.add(res_name)
                    # print '>>>>>>>>>>', break_res, m_res.group(1), m_res.group(2)
                    is_break_line = False

        # check break line
        m_br = p_br.search(line)
        if m_br:
            # print '***', m_br.group()
            is_break_line = True
            break_res = m_br.group()

        # check infoc table name
        tables = _get_table_in_line(line)
        for item in tables:
            used_tables.add(item)

        m_java = p_java.match(line)
        if m_java:
            keywords = line.split()
            for i in range(len(keywords)):
                if keywords[i].lower() == 'extends':
                    break
            class_name = keywords[i - 1]
            base = keywords[i + 1]
            view_dict[class_name] = set()
        # match the id
        ids = p_id.findall(line)
        if ids:
            for item in ids:
                if class_name:
                    view_dict[class_name].add(item)
                used_ids.add(item)

        # match the db table name
        m_table = p_table.search(line)
        if m_table:
            table = m_table.group(1)
            if table.startswith('cm_'):
                used_tables.add(table)

        # match the layout
        m_layout = p_layout.findall(line)
        if m_layout:
            for layout in m_layout:
                used_layouts.add(layout)

        # match the string
        m_android_string = p_string_android.findall(line)
        if m_android_string:
            pass
        else:
            m_string = p_string.findall(line)
            if m_string:
                for string in m_string:
                    used_strings.add(string)

        # match the drawable
        m_drawable = p_drawable.findall(line)
        if m_drawable:
            for drawable in m_drawable:
                used_drawables.add(drawable)

        # match the styles
        m_android_style = p_style_android.findall(line)
        if m_android_style:
            pass
        else:
            m_style = p_style.findall(line)
            if m_style:
                for style in m_style:
                    used_styles.add(style)

        # match the animations
        m_anim = p_anim.findall(line)
        if m_anim:
            for anim in m_anim:
                used_animations.add(anim)


def read_all_animation_file(res_path):
    global animation_dict
    for folder in os.listdir(res_path):
        if os.path.isdir(os.path.join(res_path, folder)) and folder.startswith('anim'):
            path = os.path.join(res_path, folder)
            for f in os.listdir(path):
                if os.path.isdir(os.path.join(path, f)):
                    pass
                else:
                    filename = f.split('.')
                    pre = filename[0]
                    animation_dict[pre] = Animation(pre, os.path.join(path, f))


def read_all_drawable_file(res_path):
    global drawable_dict
    for folder in os.listdir(res_path):
        if os.path.isdir(os.path.join(res_path, folder)) and folder.startswith('drawable'):
            path = os.path.join(res_path, folder)
            for f in os.listdir(path):
                if os.path.isdir(os.path.join(path, f)):
                    pass
                else:
                    filename = f.split('.')
                    pre = filename[0]
                    drawable_dict[pre] = Drawable(pre, os.path.join(path, f))


# read all nested drawable in xml except layouts and styles
def read_nested_drawables(res_folder_path):
    global used_drawables
    global drawable_dict
    global animation_dict
    pattern = re.compile('@drawable/(\w*)')
    for folder in os.listdir(res_folder_path):
        if folder.startswith('layout') or folder.startswith('values'):
            continue
        for f in os.listdir(os.path.join(res_folder_path, folder)):
            if os.path.isdir(os.path.join(res_folder_path, folder, f)):
                continue
            else:
                filename = f.split('.')
                if len(filename) == 2:
                    pre = filename[0]
                    ext = filename[1]
                    if ext.lower() == 'xml':
                        is_comment = False
                        is_macro = False
                        for line in open(os.path.join(res_folder_path, folder, f), 'U'):
                            line = line.strip()
                             # meet the macro
                            if line.find('BUILD_CTRL:IF') > -1:
                                is_macro = True
                            if line.find('BUILD_CTRL:ENDIF') > -1:
                                is_macro = False
                            if line.startswith('<!--'):
                                is_comment = True
                            # comment inside the line
                            elif line.find('<!--') > 0:
                                if line.endswith('-->'):
                                    is_comment = False
                            if is_comment and line.endswith('-->'):
                                is_comment = False
                                continue
                            if is_comment:
                                if is_macro:
                                    pass
                                else:
                                    continue
                            m_drawables = pattern.search(line)
                            if m_drawables:
                                d = m_drawables.group(1)
                                if drawable_dict.get(pre):
                                    outer = drawable_dict[pre]
                                    if d in outer.drawables:
                                        pass
                                    else:
                                        outer.drawables.add(d)
                                        if drawable_dict.get(d):
                                            drawable_dict[d].add_ref()
                                elif animation_dict.get(pre):
                                    anim = animation_dict[pre]
                                    anim.drawables.add(d)
                                    if drawable_dict.get(d):
                                        drawable_dict[d].add_ref()


def read_all_strings(res_path):
    global string_dict
    pattern = re.compile('<string name="(\w*)"')
    for folder in os.listdir(res_path):
        if folder.startswith('values'):
            for f in os.listdir(os.path.join(res_path, folder)):
                filename = f.split('.')
                if len(filename) == 2:
                    pre = filename[0]
                    ext = filename[1]
                    if pre.find('strings') > -1:
                        for line in open(os.path.join(res_path, folder, f), 'U'):
                            m = pattern.search(line)
                            if m:
                                name = m.group(1)
                                string_dict[name] = String(name)


def _add_style_parent_ref(style_obj):
    if style_obj.parent and style_obj.parent in style_dict:
        parent_obj = style_dict[style_obj.parent]
        if parent_obj:
            parent_obj.add_ref()
            _add_style_parent_ref(parent_obj)


def read_all_styles(res_path):
    global style_dict
    global drawable_dict
    global animation_dict
    global string_dict
    global layout_dict

    global used_layouts
    global used_styles
    global used_animations
    global used_drawables
    global used_strings

    pattern = re.compile('<style name="([\w|\.]+)"')
    p_item = re.compile('<item.*@style/([\w|\.]+)')
    p_parent = re.compile('<style name="([\w|\.]+)"\s+parent="(.+?)"')
    p_drawable = re.compile('@drawable/(\w+)')
    p_end = re.compile('</style>')
    p_anim = re.compile('@anim/(\w+)')
    p_string = re.compile('@string/(\w*)')
    p_layout = re.compile('@layout/(\w*)')
    p_id = re.compile('@id/(\w*)')

    # read all styles in styles.xml into dict
    for folder in os.listdir(res_path):
        if folder.startswith('values'):
            for f in os.listdir(os.path.join(res_path, folder)):
                filename = f.split('.')
                if len(filename) == 2:
                    pre = filename[0]
                    ext = filename[1]
                    if 'style' in pre or 'theme' in pre:
                        for line in open(os.path.join(res_path, folder, f)):
                            m_style = pattern.search(line)
                            if m_style:
                                name = m_style.group(1)
                                style_dict[name] = Style(name)

    # read all nested or included styles in xml
    for folder in os.listdir(res_path):
        if folder.startswith('values'):
            for f in os.listdir(os.path.join(res_path, folder)):
                filename = f.split('.')
                if len(filename) == 2:
                    pre = filename[0]
                    ext = filename[1]
                    if 'style' in pre or 'theme' in pre:
                        style_obj = None
                        for line in open(os.path.join(res_path, folder, f), 'U'):
                            line = line.strip()
                            # match the sub style
                            m_style = pattern.search(line)
                            if m_style:
                                name = m_style.group(1)
                                if style_dict.get(name):
                                    style_obj = style_dict[name]
                                    # if name.find(".") > -1:
                                    #     fullname = name.split(".")
                                    #     parent = fullname[0]
                                    #     if style_dict.get(parent):
                                    #         style_dict[parent].add_ref()
                                    #     else:
                                    #         style_obj.parent = parent
                                    #         style_dict[parent] = Style(parent)
                                    #         style_dict[parent].add_ref()
                                    if '.' in name:
                                        parts = name.split('.')
                                        parent_parts = parts[0:-1]
                                        parent_name = '.'.join(parent_parts)
                                        # if parent_name in style_dict or parent_name in builtin_styles:
                                        #     pass
                                        # else:
                                        #     style_dict[parent_name] = Style(parent_name)
                                        style_obj.parent = parent_name


                            # match the parent style
                            m_parent = p_parent.search(line)
                            if m_parent:
                                child = m_parent.group(1)
                                parent = m_parent.group(2)
                                if '/' in parent:
                                    parent_name = parent.split("/")[1]
                                else:
                                    parent_name = parent
                                if not parent_name in style_dict:  # this parent is a built-in style
                                    pass
                                    # style_dict[parent_name] = Style(parent_name)


                                if style_obj:
                                    style_obj.parent = parent_name
                                else:
                                    style_obj = Style(child)
                                    style_obj.parent = parent_name
                                    style_dict[child] = style_obj

                                if style_obj.parent:
                                    _add_style_parent_ref(style_obj)

                            # match the style item
                            m_style_item = p_item.search(line)
                            if m_style_item:
                                item = m_style_item.group(1)
                                if style_obj:
                                    if style_dict.get(item):
                                        item_obj = style_dict[item]
                                        item_obj.add_ref()
                                        style_obj.styles.add(item)
                                else:
                                    if style_dict.get(item):
                                        style_dict[item].add_ref()

                            # match the drawable item
                            m_drawable_item = p_drawable.search(line)
                            if m_drawable_item:
                                drawable = m_drawable_item.group(1)
                                if style_obj:
                                    if drawable in style_obj.drawables:
                                        # if the drawable is already in the style, then pass
                                        pass
                                    else:
                                        style_obj.drawables.add(drawable)
                                        if drawable_dict.get(drawable):
                                            drawable_dict[drawable].add_ref()

                            # match the anim item
                            m_anim = p_anim.search(line)
                            if m_anim:
                                anim = m_anim.group(1)
                                if style_obj:
                                    if anim in style_obj.animations:
                                        # if the animation is already in the style, then pass
                                        pass
                                    else:
                                        style_obj.animations.add(anim)
                                        if animation_dict.get(anim):
                                            animation_dict[anim].add_ref()

                            # match the string item
                            m_str = p_string.search(line)
                            if m_str:
                                string = m_str.group(1)
                                if style_obj:
                                    if string in style_obj.strings:
                                        # if the string is already in the style, then pass
                                        pass
                                    else:
                                        style_obj.strings.add(string)
                                        if string_dict.get(string):
                                            string_dict[string].add_ref()

                            # match the layout item
                            m_layout = p_layout.search(line)
                            if m_layout:
                                layout = m_layout.group(1)
                                if style_obj:
                                    if layout in style_obj.layouts:
                                        pass
                                    else:
                                        style_obj.layouts.add(layout)
                                        if layout_dict.get(layout):
                                            layout_dict[layout].add_ref()

                            m_end = p_end.search(line)
                            if m_end:
                                style_obj = None


def read_kfmt_file(path):
    global all_tables
    p_num = re.compile('.+\d+$')
    for line in open(path):
        table_name = line.split(':')[0]
        m = p_num.search(table_name)
        if m:
            # skip all table ends with numbers
            pass
        else:
            # skip 'cm_public'
            all_tables.add(table_name)


# recursively reduce layout ref
def reduce_resource_ref(res):
    global style_dict
    global drawable_dict
    global layout_dict
    global drawable_dict
    global animation_dict

    # reduce sub drawable refs
    if 'drawables' in res.__dict__:
        for d in res.drawables:
            if drawable_dict.get(d):
                drawable_dict[d].remove_ref()
                reduce_resource_ref(drawable_dict[d])

    # reduce sub animations refs
    if 'animations' in res.__dict__:
        for a in res.animations:
            if animation_dict.get(a):
                item = animation_dict[a]
                item.remove_ref()
                reduce_resource_ref(item)

    # reduce sub layout refs
    if 'layouts' in res.__dict__:
        for l in res.layouts:
            if layout_dict.get(l):
                item = layout_dict[l]
                item.remove_ref()
                reduce_resource_ref(item)
    # reduce sub style refs
    if 'styles' in res.__dict__:
        for s in res.styles:
            if style_dict.get(s):
                item = style_dict[s]
                item.remove_ref()
                reduce_resource_ref(item)

    # reduce sub string refs
    if 'strings' in res.__dict__:
        for t in res.strings:
            if string_dict.get(t):
                item = string_dict[t]
                item.remove_ref()


def set_res_used(obj):
    global used_layouts
    global used_styles
    global used_strings
    global used_animations
    global used_drawables

    global layout_dict
    global style_dict
    global drawable_dict
    global string_dict
    global drawable_dict

    if isinstance(obj, Layout):
        used_layouts.add(obj.name)
    elif isinstance(obj, Drawable):
        used_drawables.add(obj.name)
    elif isinstance(obj, Animation):
        used_animations.add(obj.name)
    elif isinstance(obj, String):
        used_strings.add(obj.name)
    elif isinstance(obj, Style):
        used_styles.add(obj.name)

    if 'parent' in obj.__dict__:
        parent = obj.parent
        if parent and parent in style_dict:
            parent_style = style_dict[parent]
            set_res_used(parent_style)

     # reduce sub drawable refs
    if 'drawables' in obj.__dict__:
        for element in obj.drawables:
            if drawable_dict.get(element):
                set_res_used(drawable_dict[element])

    # reduce sub animations refs
    if 'animations' in obj.__dict__:
        for element in obj.animations:
            if animation_dict.get(element):
                set_res_used(animation_dict[element])

    # reduce sub layout refs
    if 'layouts' in obj.__dict__:
        for element in obj.layouts:
            if layout_dict.get(element):
                set_res_used(layout_dict[element])
    # reduce sub style refs
    if 'styles' in obj.__dict__:
        for element in obj.styles:
            if style_dict.get(element):
                set_res_used(style_dict[element])

    # reduce sub string refs
    if 'strings' in obj.__dict__:
        for element in obj.strings:
            if string_dict.get(element):
                set_res_used(string_dict[element])


def get_underscore_name(name):
    if '.' in name:
        return name.replace('.', '_')
    else:
        return name


def get_unused_res(res_type, outputname):
    global used_layouts
    global used_drawables
    global used_styles
    global used_animations
    global used_strings

    global layout_dict
    global drawable_dict
    global style_dict
    global animation_dict
    global style_dict

    zero_refs = set()
    all_list = []
    sorted_list = None
    used_set = None
    res_dict = None
    if res_type == 'layout':
        res_dict = layout_dict
        used_set = used_layouts
        for key in res_dict:
            all_list.append(res_dict[key])
            sorted_list = sorted(all_list, key=lambda x: len(x.layouts), reverse=True)
    elif res_type == 'style':
        res_dict = style_dict
        used_set = used_styles
        for key in res_dict:
            all_list.append(res_dict[key])
            sorted_list = sorted(all_list, key=lambda x: len(x.styles), reverse=True)
    elif res_type == 'string':
        res_dict = string_dict
        used_set = used_strings
    elif res_type == 'drawable':
        res_dict = drawable_dict
        used_set = used_drawables
    elif res_type == 'animation':
        res_dict = animation_dict
        used_set = used_animations

    # add exclusions to used set
    for pre in exclusions:
        for key in res_dict:
            item = res_dict[key]
            name = item.name
            if pre in name:
                used_set.add(name)

    # calculate the refs
    if sorted_list:
        for res in sorted_list:
            if isinstance(res, Style):
                name = get_underscore_name(res.name)
            else:
                name = res.name

            if name in used_set:
                set_res_used(res)
            else:
                if res.ref <= 0:
                    reduce_resource_ref(res)
                else:
                    set_res_used(res)
    else:
        for item in res_dict:
            res = res_dict[item]
            if item in used_set:
                set_res_used(res)
            else:
                if res.ref <= 0:
                    reduce_resource_ref(res)
                else:
                    set_res_used(res)

    for key in res_dict:
        res = res_dict[key]
        name = res.name
        path = res.path

        if name in used_set:
            pass
        else:
            if res.ref <= 0:  # and is_deletable(res):
                if path:
                    zero_refs.add(path)
                else:
                    zero_refs.add(name)

    write_output(outputname, zero_refs)
    print "unused %s:" % res_type, len(zero_refs)


def read_android_manifest(xml):
    # print manifest
    global used_styles
    global used_strings
    global used_drawables
    p_style = re.compile('@style/([\w|\.]+)')
    p_drawable = re.compile('@drawable/(\w*)')
    p_string = re.compile('@string/(\w*)')
    is_comment = False
    is_macro = False
    for line in open(xml):
        line = line.strip()

        # meet the macro
        if line.find('BUILD_CTRL:IF') > -1:
            is_macro = True
        if line.find('BUILD_CTRL:ENDIF') > -1:
            is_macro = False
        if line.startswith('<!--'):
            is_comment = True
        if line.endswith('-->'):
            is_comment = False
            continue
        if is_comment:
            if is_macro:
                pass
            else:
                continue
        # match the style
        s = p_style.search(line)
        if s:
            style = s.group(1)
            used_styles.add(style)
        # match the drawable
        d = p_drawable.search(line)
        if d:
            drawable = d.group(1)
            used_drawables.add(drawable)
        # match the string
        st = p_string.search(line)
        if st:
            string = st.group(1)
            used_strings.add(string)


def _get_attr(line):
    if line and '=' in line:
        parts = line.split('=')
        if len(parts) > 1:
            return parts[0].strip()


# read all layouts file in the folder 'layout'
def read_all_layouts(res_folder_path):
    global layout_dict
    global drawable_dict
    global animation_dict
    global style_dict
    global string_dict

    global used_layouts
    global used_styles
    global used_animations
    global used_drawables
    global used_strings
    global used_ids

    p = re.compile('@layout/(\w*)')
    p_string = re.compile('@string/(\w*)')
    p_style = re.compile('@style/([\w|\.]+)')
    p_drawable = re.compile(r'"@drawable/(\w*)"')
    p_anim = re.compile('@anim/(\w*)')
    p_id = re.compile('@\+?id/(\w*)')
    p_view = re.compile(r'<([a-z]+\x2e([a-z]+\x2e)*[a-zA-Z][a-zA-Z0-9]*)')
    is_comment = False
    is_macro = False

    # scan xml filename
    for folder in os.listdir(res_folder_path):
        if folder.startswith('layout'):
            for f in os.listdir(os.path.join(res_folder_path, folder)):
                if os.path.isdir(os.path.join(res_folder_path, folder, f)):
                    pass
                else:
                    filename = f.split('.')
                    pre = filename[0]
                    ext = filename[1]
                    if ext.lower() == 'xml':
                        layout_dict[pre] = Layout(pre, os.path.join(res_folder_path, folder, f))

    # scan xml contents
    for folder in os.listdir(res_folder_path):
        if folder.startswith('layout'):
            for f in os.listdir(os.path.join(res_folder_path, folder)):
                if os.path.isdir(os.path.join(res_folder_path, folder, f)):
                    pass
                else:
                    filename = f.split('.')
                    pre = filename[0]
                    ext = filename[1]
                    ids = None
                    if ext.lower() == 'xml':
                        # init a Layout Object
                        if layout_dict.get(pre):
                            layout_obj = layout_dict[pre]
                        else:
                            print "!!!ERORR: cannot find layout:", pre
                            continue  # impossible to go to here
                        layout_file_path = os.path.join(res_folder_path, folder, f)
                        file_lines = scan_utils.get_file_lines(layout_file_path)

                        for line in open(layout_file_path, 'U'):

                            line = line.strip()

                            # meet the macro
                            if line.find('BUILD_CTRL:IF') > -1:
                                is_macro = True
                            if line.find('BUILD_CTRL:ENDIF') > -1:
                                is_macro = False
                            # meet the comment
                            if line.startswith('<!--'):
                                is_comment = True
                            if line.endswith('-->'):
                                is_comment = False
                                continue
                            if is_comment:
                                if is_macro:
                                    pass
                                else:
                                    continue

                            # match the custom view name
                            m_view = p_view.search(line)
                            if m_view:
                                view = m_view.group(1)
                                class_name = view.split('.')[-1]
                                if class_name in view_dict:
                                    ids = view_dict[class_name]

                            # match the drawable
                            d = p_drawable.search(line)
                            if d:
                                drawable = d.group(1)
                                layout_obj.drawables.add(drawable)
                                # if 'boost_tag_shortcut_' in drawable or 'one_tap_icon' in drawable:
                                #     print '---------------', layout_obj.name, drawable
                                if drawable_dict.get(drawable):
                                    drawable_dict[drawable].add_ref()
                                else:
                                    drawable_dict[drawable] = Drawable(drawable)
                                    drawable_dict[drawable].add_ref()

                            # match the style
                            t = p_style.search(line)
                            if t:
                                style = t.group(1)
                                if style not in layout_obj.styles:
                                    layout_obj.styles.add(style)
                                else:
                                    if style_dict.get(style):
                                        style_dict[style].add_ref()
                                    else:
                                        style_dict[style] = Style(style)
                                        style_dict[style].add_ref()

                            # match the string
                            s = p_string.search(line)
                            if s:
                                string = s.group(1)
                                layout_obj.strings.add(string)

                                if string_dict.get(string):
                                    string_dict[string].add_ref()
                                else:
                                    string_dict[string] = String(string)
                                    string_dict[string].add_ref()

                            # match the anim
                            a = p_anim.search(line)
                            if a:
                                anim = a.group(1)
                                layout_obj.animations.add(anim)

                                if animation_dict.get(anim):
                                    animation_dict[anim].add_ref()
                                else:
                                    animation_dict[anim] = Animation(anim)
                                    animation_dict[anim].add_ref()

                            # match the layout
                            m = p.search(line)
                            if m:
                                layout = m.group(1)
                                attr = _get_attr(line)
                                # special handling
                                if 'android' in attr or 'layout' in attr:
                                    # add layout ref
                                    if layout in layout_obj.layouts:
                                        pass
                                    else:
                                        layout_obj.layouts.add(layout)

                                        if layout_dict.get(layout):
                                            layout_dict[layout].add_ref()
                                        else:
                                            layout_dict[layout] = Layout(layout)
                                            layout_dict[layout].add_ref()

                            # match the id
                            m_id = p_id.search(line)
                            if m_id:
                                item_id = m_id.group(1)
                                # TODO yyy
                                if item_id in used_ids:
                                    used_layouts.add(layout_obj.name)
                                # if ids and item_id in ids:
                                #     used_layouts.add(layout_obj.name)
                        # layout_file.close()


def is_deletable(res):
    if isinstance(res, String):
        return True

    if 'layouts' in res.__dict__:
        for item in res.layouts:
            item_obj = layout_dict[item]
            if item in used_layouts and item_obj.ref > 1:
                return False
            else:
                if not is_deletable(item_obj):
                    return False

    if 'styles' in res.__dict__:
        for item in res.styles:
            item_obj = style_dict[item]
            if item in used_styles and item_obj.ref > 1:
                return False
            else:
                if not is_deletable(item_obj):
                    return False

    if 'drawables' in res.__dict__:
        for item in res.drawables:
            item_obj = drawable_dict[item]
            if item in used_drawables and item_obj.ref > 1:
                return False
            else:
                if not is_deletable(item_obj):
                    return False

    if 'animations' in res.__dict__:
        for item in res.animations:
            item_obj = animation_dict[item]
            if item in used_animations and item_obj.ref > 1:
                return False
            else:
                if not is_deletable(item_obj):
                    return False

    if 'strings' in res.__dict__:
        for item in res.strings:
            item_obj = string_dict[item]
            if item in used_strings and item_obj.ref > 1:
                return False

    return True


def print_res_info(res, name, used_set):
    if res.name == name:
        print '>>>', name
        print '>>> type=', type(res)
        print '>>> ref=', res.ref
        print '>>> in use=', str(name in used_set)
        if 'styles' in res.__dict__:
            print res.styles


def free_containers():
    global used_layouts
    global used_drawables
    global used_strings
    global used_styles
    global used_animations
    global used_ids

    global layout_dict
    global style_dict
    global animation_dict
    global drawable_dict
    global string_dict
    global view_dict

    del used_layouts
    del used_animations
    del used_ids
    del used_drawables
    del used_strings
    del used_styles

    del layout_dict
    del style_dict
    del animation_dict
    del drawable_dict
    del string_dict
    del view_dict


def read_exclusive_tables(path):
    # global used_tables
    exclusions = []
    for line in open(path):
        line = line.strip()
        exclusions.append(line)
    return exclusions


def get_unused_tables(project_path):
    # unused kfmt table
    data = os.path.join(project_path, "assets", "kfmt.dat")
    db_tables = "db_tables.txt"
    read_kfmt_file(data)
    exclusion_tables = read_exclusive_tables(db_tables)
    unused_tables = all_tables - used_tables
    excluded_tables = set()
    for t in unused_tables:
        for pre in exclusion_tables:
            if pre in t:
                excluded_tables.add(t)
    result_tables = unused_tables - excluded_tables

    print "unused tables:", len(result_tables)
    write_output("result_tables.txt", result_tables)


def test():
    count = 0
    with open(r'test_file/layout/boost_tag_process_clean_activity.xml') as f:
        for line in f:
            print '...', line
            print count
            count += 1


def main():
    global exclusions
    # ------------- run the tool
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

    exclusions = get_exclusion_set("exclusions.txt")
    # ----- paths
    src_folder = os.path.join(project_path, "src")
    layout_folder = os.path.join(project_path, "res", "layout")
    res_folder = os.path.join(project_path, "res")
    manifest = os.path.join(project_path, "AndroidManifest.xml")

    # --- read all things
    read_android_manifest(manifest)
    read_all_java(src_folder)
    read_all_strings(res_folder)
    read_all_drawable_file(res_folder)
    read_all_animation_file(res_folder)
    read_nested_drawables(res_folder)
    read_all_styles(res_folder)
    read_all_layouts(res_folder)

    get_unused_tables(project_path)

    get_unused_res('layout', 'result_layouts.txt')
    get_unused_res('style', 'result_styles.txt')
    get_unused_res('animation', 'result_animations.txt')
    get_unused_res('drawable', 'result_drawables.txt')
    get_unused_res('string', 'result_strings.txt')

    free_containers()


if __name__ == '__main__':
    main()
    # test()

