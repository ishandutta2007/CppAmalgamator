import sys
import clang.cindex
import pprint as pp
import colorama
import re
import copy

pattern = r"^(\d+):( *)(\d+):(.*)$"
pattern_comment1 = r"^-:( *)(\d+):(.*)$"
pattern_comment2 = r"^#####:( *)(\d+):(.*)$"
pattern_pass = r"^(.*):( *)(\d+)-block(.*)$"

statically_commented_filename = sys.argv[1]
with open(statically_commented_filename) as f:
    statcom_lines = f.readlines()

index = clang.cindex.Index.create()
tu = index.parse(statically_commented_filename)


def print_node_heirarchy_by_node(node, line_number, print_list=[]):
    if node.extent.start.line <= line_number and line_number <= node.extent.end.line:
        print_list_forwarded = copy.deepcopy(print_list)
        try:
            kindly = str(node.kind).replace("CursorKind.", "")
            # print(str(node.kind))
        except Exception as e:
            kindly = "0"
        print_list_forwarded.append(
            [node.spelling, kindly, node.extent.start.line, node.extent.end.line,]
        )
        for child in node.get_children():
            print_node_heirarchy_by_node(child, line_number, print_list_forwarded)
    if len(print_list) > 1:
        print(print_list)


def print_node_heirarchy(line_number):
    print_node_heirarchy_by_node(node=tu.cursor, line_number=line_number)


def get_lowest_greater_parent_by_node(node, line_number):
    if node.extent.start.line <= line_number and line_number <= node.extent.end.line:
        if node.extent.start.line == node.extent.end.line:  # Too low
            return None
        for child in node.get_children():
            c = get_lowest_greater_parent_by_node(child, line_number)
            if c is not None:
                return c
        return node
    return None


def get_lowest_greater_parent(line_number):  # greater means containing more lines
    return get_lowest_greater_parent_by_node(node=tu.cursor, line_number=line_number)


print_node_heirarchy(4706)
lgp = get_lowest_greater_parent(4706)


print(lgp.spelling, lgp.kind, lgp.extent.start.line, lgp.extent.end.line)
