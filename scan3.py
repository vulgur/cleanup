__author__ = 'Wang Shudao'

from resources import Layout
from resources import Drawable
from resources import String
from resources import Animation
from resources import Style
from scan_utils import write_output
from xml_utils import separate_nodes_and_comments, get_xml_root
import os
import re


# global containers
used_layouts = set()
used_drawables = set()
used_strings = set()
used_styles = set()
used_animations = set()
used_ids = set()

used_tables = set()
all_tables = set()
cm_reports = set()
exclusions = set()

used_class = set()  # for custom views
view_dict = {}  # for custom views

drawable_dict = {}
layout_dict = {}
style_dict = {}
string_dict = {}
animation_dict = {}

kfmt_table_pre = ('cm_', 'cmlite_')
res_types = ('drawable', 'style', 'layout', 'anim', 'string')




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
            all_tables.add(table_name)


# read exclusions
def _get_exclusion_set(path):
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
    p_layout = re.compile('R[\.\r\n ]+layout[\.\r\n ]+(\w+)', re.S | re.M)
    p_drawable = re.compile('R[\.\r\n ]+drawable[\.\r\n ]+(\w+)', re.S | re.M)
    p_string = re.compile('R\s*\.\s*string\s*.\s*(\w+)', re.S | re.M)
    # p_string_android = re.compile('android\.R\.string\.(\w*)', re.S, re.M)
    p_style = re.compile('R[\.\r\n ]+style[\.\r\n ]+(\w+)', re.S | re.M)
    # p_style_android = re.compile('android\.R\.style\.(\w*)', re.S, re.M)
    p_anim = re.compile('R[\.\r\n ]+anim[\.\r\n ]+(\w+)', re.S | re.M)
    p_id = re.compile('R[\.\r\n ]+id[\.\r\n ]+(\w+)', re.S | re.M)
    p_table = re.compile('\"(\w+)\"')

    with open(f) as reader:
        lines = reader.read()
    m = re.findall(p_string, lines)
    # --- strings
    for item in m:
        used_strings.add(item)
    m = re.findall(p_layout, lines)
    # --- layouts
    for item in m:
        used_layouts.add(item)
    m = re.findall(p_drawable, lines)
    # --- drawables
    for item in m:
        used_drawables.add(item)
    m = re.findall(p_style, lines)
    # --- styles
    for item in m:
        used_styles.add(item)
        # print item
    m = re.findall(p_id, lines)
    # --- ids
    for item in m:
        used_ids.add(item)
    m = re.findall(p_anim, lines)
    # --- anim
    for item in m:
        used_animations.add(item)
    # --- infoc tables
    m = re.findall(p_table, lines)
    for item in m:
        for pre in kfmt_table_pre:
            if item.startswith(pre):
                used_tables.add(item)


def _read_all_animation_file(res_path):
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


def _read_all_drawable_file(res_path):
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


def _scan_style_node_res(nodes, value_set, value_dict):
    for node in nodes:
        if node.tag == 'style':
            _scan_style_node_res(list(node), value_set, value_dict)
        elif node.tag == 'item':

            for attr, val in node.attrib.iteritems():
                if attr == 'name' and 'android' in val and node.text:
                    for v in value_set:
                        if node.text.startswith(v):
                            res_type, res_value = _get_res_value_tuple(node.text)
                            # print '>>> ', res_type, res_value
                            if res_type in value_dict:
                                value_dict[res_type].add(res_value)
                            else:
                                value_dict[res_type] = set(res_value)


def _scan_xml_node_res(nodes, value_set, value_dict):
    for node in nodes:
        # scan child nodes
        _scan_xml_node_res(list(node), value_set, value_dict)
        for attr, val in node.attrib.iteritems():
            if 'android' in attr:
                for v in value_set:
                    if val.startswith(v):
                        res_type, res_value = _get_res_value_tuple(val)
                        # print '>', res_type, res_value
                        if res_type in value_dict:
                            value_dict[res_type].add(res_value)
                        else:
                            value_dict[res_type] = set(res_value)


def _scan_all_comment_res(comments, value_set, value_dict):
    for item in comments:
        text = item.text
        for pre in value_set:
            pattern = re.compile(pre+'\w+')
            match_items = re.findall(pattern, text)
            for m in match_items:
                res_type, res_value = _get_res_value_tuple(m)
                print '*** in comments:', res_type, res_value
                if res_type in value_dict:
                    value_dict[res_type].add(res_value)
                else:
                    value_dict[res_type] = set(res_value)


def _get_res_value_tuple(val):
    pattern_val = re.compile(r'@(\w+)/(\w+)')
    m = pattern_val.search(val)
    if m:
        res_type = m.group(1)
        res_value = m.group(2)
        # print '>>>', m.group(1), m.group(2)
        return res_type, res_value
    else:
        print '!!! ERROR'


# read all nested drawable in xml except layouts and styles
def _read_nested_drawables(res_folder_path):
    global used_drawables
    global drawable_dict
    global animation_dict
    pattern = re.compile('@drawable/(\w*)')
    for folder in os.listdir(res_folder_path):
        if folder.startswith('layout') or folder.startswith('values'):
            continue
        sub_folder = os.path.join(res_folder_path, folder)
        if not os.path.isdir(sub_folder):
            continue

        print 'sub folder:', sub_folder
        for f in os.listdir(os.path.join(res_folder_path, folder)):
            file_path = os.path.join(res_folder_path, folder, f)
            print 'path', file_path
            if os.path.isdir(file_path):
                continue
            else:
                filename = f.split('.')
                if len(filename) == 2:
                    pre = filename[0]
                    ext = filename[1]
                    if ext.lower() == 'xml':
                        f_path = os.path.join(res_folder_path, folder, f)
                        doc_root = get_xml_root(f_path)
                        nodes, comments = separate_nodes_and_comments(doc_root)
                        value_dict = {}
                        value_set = ('@drawable/',)

                        _scan_xml_node_res(nodes, value_set, value_dict)
                        _scan_all_comment_res(comments, value_set, value_dict)
                        for k, v in value_dict.iteritems():
                            if k == 'drawable':
                                if drawable_dict.get(pre):
                                    outer = drawable_dict[pre]
                                    if v in outer.drawables:
                                        pass
                                    else:
                                        outer.drawables.add(v)
                                        if drawable_dict.get(v):
                                            drawable_dict[v].add_ref()
                                elif animation_dict.get(pre):
                                    anim = animation_dict[pre]
                                    anim.drawables.add(v)
                                    if drawable_dict.get(v):
                                        drawable_dict[v].add_ref()


def _read_all_strings(res_path):
    global string_dict
    pattern = re.compile('<string\s*name=\s*"(\w*)"')
    for folder in os.listdir(res_path):
        if folder.startswith('values'):
            for f in os.listdir(os.path.join(res_path, folder)):
                filename = f.split('.')
                if len(filename) == 2:
                    pre = filename[0]
                    ext = filename[1]
                    if pre.find('strings') > -1:
                        f_path = os.path.join(res_path, folder, f)
                        doc_root = get_xml_root(f_path)
                        nodes, comments = separate_nodes_and_comments(doc_root)
                        # normal nodes
                        for child in nodes:
                            for attr, val in child.attrib.iteritems():
                                string_dict[val] = String(val)
                        # comments
                        for item in comments:
                            m = re.findall(pattern, item.text)
                            for name in m:
                                string_dict[name] = String(name)


def _add_style_parent_ref(style_obj):
    if style_obj.parent:
        parent_obj = style_dict[style_obj.parent]
        if parent_obj:
            parent_obj.add_ref()
            _add_style_parent_ref(parent_obj)


def _read_all_styles(res_path):
    global style_dict
    global drawable_dict
    global animation_dict
    global string_dict
    global layout_dict

    # read all styles in styles.xml into dict
    for folder in os.listdir(res_path):
        if folder.startswith('values'):
            for f in os.listdir(os.path.join(res_path, folder)):
                filename = f.split('.')
                if len(filename) == 2:
                    pre = filename[0]
                    ext = filename[1]
                    if 'style' in pre or 'theme' in pre:
                        f_path = os.path.join(res_path, folder, f)
                        doc_root = get_xml_root(f_path)
                        for child in list(doc_root):
                            if child.tag == 'style':
                                name = child.attrib['name']
                                style_obj = Style(name)
                                style_dict[name] = style_obj

    # add sub res to each style
    for folder in os.listdir(res_path):
        if folder.startswith('values'):
            for f in os.listdir(os.path.join(res_path, folder)):
                filename = f.split('.')
                if len(filename) == 2:
                    pre = filename[0]
                    ext = filename[1]
                    if 'style' in pre or 'theme' in pre:
                        f_path = os.path.join(res_path, folder, f)
                        doc_root = get_xml_root(f_path)
                        for child in list(doc_root):
                            name = child.attrib['name']
                            # deal with parent style
                            if child.attrib['parent']:
                                parent_name = child.attrib['parent']
                                style_obj.parent = parent_name
                            if '.' in name:
                                parts = name.split('.')
                                parent_parts = parts[0:-1]
                                parent_name = '.'.join(parent_parts)
                                style_obj.parent = parent_name
                            if style_obj.parent:
                                _add_style_parent_ref(style_obj)

                            # <item>
                            for item in list(child):
                                res_type, res_value = _get_res_value_tuple(item.text)
                                if res_type == 'drawable':
                                    if res_value in style_obj.drawables:
                                        pass
                                    else:
                                        style_obj.drawables.add(res_value)
                                        if res_value in drawable_dict:
                                            drawable_dict[res_value].add_ref()

                                elif res_type == 'style':
                                    if res_value in style_obj.styles:
                                        pass
                                    else:
                                        style_obj.styles.add(res_value)
                                        if res_value in style_dict:
                                            style_dict[res_value].add_ref()

                                elif res_type == 'anim':
                                    if res_value in style_obj.animations:
                                        pass
                                    else:
                                        style_obj.animations.add(res_value)
                                        if res_value in animation_dict:
                                            animation_dict[res_value].add_ref()

                                elif res_type == 'string':
                                    if res_value in style_obj.strings:
                                        pass
                                    else:
                                        style_obj.strings.add(res_value)
                                        if res_value in string_dict:
                                            string_dict[res_value].add_ref()

                                elif res_type == 'layout':
                                    if res_value in style_obj.layouts:
                                        pass
                                    else:
                                        style_obj.layouts.add(res_value)
                                        if res_value in layout_dict:
                                            layout_dict[res_value].add_ref()


# recursively reduce layout ref
def _reduce_resource_ref(res):
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
                _reduce_resource_ref(drawable_dict[d])

    # reduce sub animations refs
    if 'animations' in res.__dict__:
        for a in res.animations:
            if animation_dict.get(a):
                item = animation_dict[a]
                item.remove_ref()
                _reduce_resource_ref(item)

    # reduce sub layout refs
    if 'layouts' in res.__dict__:
        for l in res.layouts:
            if layout_dict.get(l):
                item = layout_dict[l]
                item.remove_ref()
                _reduce_resource_ref(item)
    # reduce sub style refs
    if 'styles' in res.__dict__:
        for s in res.styles:
            if style_dict.get(s):
                item = style_dict[s]
                item.remove_ref()
                _reduce_resource_ref(item)

    # reduce sub string refs
    if 'strings' in res.__dict__:
        for t in res.strings:
            if string_dict.get(t):
                item = string_dict[t]
                item.remove_ref()


# set a resource and its sub resources as used
def _set_res_used(obj):
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
            _set_res_used(parent_style)

     # reduce sub drawable refs
    if 'drawables' in obj.__dict__:
        for element in obj.drawables:
            if drawable_dict.get(element):
                _set_res_used(drawable_dict[element])

    # reduce sub animations refs
    if 'animations' in obj.__dict__:
        for element in obj.animations:
            if animation_dict.get(element):
                _set_res_used(animation_dict[element])

    # reduce sub layout refs
    if 'layouts' in obj.__dict__:
        for element in obj.layouts:
            if layout_dict.get(element):
                _set_res_used(layout_dict[element])
    # reduce sub style refs
    if 'styles' in obj.__dict__:
        for element in obj.styles:
            if style_dict.get(element):
                _set_res_used(style_dict[element])

    # reduce sub string refs
    if 'strings' in obj.__dict__:
        for element in obj.strings:
            if string_dict.get(element):
                _set_res_used(string_dict[element])


# used for style name
def _get_underscore_name(name):
    if '.' in name:
        return name.replace('.', '_')
    else:
        return name


def _get_unused_res(res_type, outputname):
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
                name = _get_underscore_name(res.name)
            else:
                name = res.name
            if name in used_set:
                _set_res_used(res)
            else:
                if res.ref <= 0:
                    _reduce_resource_ref(res)
    else:
        for item in res_dict:
            res = res_dict[item]
            if item in used_set:
                _set_res_used(res)
            else:
                if res.ref <= 0:
                    _reduce_resource_ref(res)

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


def _read_android_manifest(xml_path):
    global used_styles
    global used_strings
    global used_drawables

    doc_root = get_xml_root(xml_path)
    nodes, comments = separate_nodes_and_comments(doc_root)
    print '*', len(nodes), len(comments)
    value_set = ('@style/', '@string/', '@drawable/')
    value_dict = {}
    _scan_xml_node_res(nodes, value_set, value_dict)
    _scan_all_comment_res(comments, value_set, value_dict)

    for k, v in value_dict.iteritems():
        if k == 'style':
            used_styles.add(v)
        elif k == 'string':
            used_strings.add(v)
        elif k == 'drawable':
            used_strings.add(v)


def _read_all_layouts(res_folder_path):
    # TODO finish

if __name__ == '__main__':
    _read_android_manifest('test_file/manifest.xml')
