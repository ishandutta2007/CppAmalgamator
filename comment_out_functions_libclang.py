import sys
import clang.cindex
import pprint as pp
import re
import colorama

COLOR_OKGREEN = "\033[92m"
COLOR_ENDC = "\033[0m"

input_filename = sys.argv[1]
with open(input_filename) as f:
    lines = f.readlines()


def is_searched_node(node, search_node_name):
    if node.spelling == search_node_name:
        print(
            "found {} starting at line no {}".format(
                node.spelling, node.extent.start.line
            )
        )
        # print(dir(node))
        return True
    return False


def visit(
    node, search_node_name, search_node_kind=[clang.cindex.CursorKind.FUNCTION_DECL]
):
    commented_cnt = 0
    # if node.spelling=="__mbstate_t":
    # print(node.spelling, "=>", node.kind, node.extent.start.line)
    for child in node.get_children():
        commented_cnt += visit(child, search_node_name)

    # clang.cindex.CursorKind.TYPEDEF_DECL# or node.kind == clang.cindex.CursorKind.CXX_METHOD
    if node.kind in search_node_kind and is_searched_node(node, search_node_name):
        for line_no in range(node.extent.start.line - 1, node.extent.end.line):
            lines[line_no] = "// " + lines[line_no]
        commented_cnt += True
    return commented_cnt


cppcheck_filename = input_filename.replace(".cpp", "_cppcheck.txt")
with open(cppcheck_filename) as f:
    errors = f.readlines()


def get_unused_members(serach_error):
    unused_members = [
        re.findall("'([^']*)'", "".join(err.split(" ")))[0]
        for err in errors
        if serach_error in err
    ]

    print(unused_members)
    return unused_members


def comment_functions(tu):
    unused_functions = get_unused_members("unusedFunction")
    for unused_function in unused_functions:
        instances = visit(
            node=tu.cursor,
            search_node_name=unused_function,
            search_node_kind=[clang.cindex.CursorKind.FUNCTION_DECL],
        )
        if instances > 0:
            # print("".join(lines))
            print(
                COLOR_OKGREEN
                + "commented function {}: {} times".format(unused_function, instances)
                + COLOR_ENDC
            )
        else:
            print(
                "couldn't find function: {} (within nodetypes: {})".format(
                    unused_function, [clang.cindex.CursorKind.FUNCTION_DECL]
                )
            )


def comment_struct_members(tu):
    unused_struct_members = get_unused_members("unusedStructMember")
    # unused_struct_members = [
    #     re.findall("'([^']*)'", "".join(err.split(" ")))[0]
    #     for err in errors
    #     if "unusedStructMember" in err
    # ]

    # print(unused_struct_members)

    for unused_struct_member in unused_struct_members:
        instances = visit(
            node=tu.cursor,
            search_node_name=unused_struct_member,
            search_node_kind=[clang.cindex.CursorKind.STRUCT_DECL],
        )
        if instances > 0:
            # print("".join(lines))
            print(
                COLOR_OKGREEN
                + "commented struct_member {}: {} times".format(
                    unused_function, instances
                )
                + COLOR_ENDC
            )
        else:
            print(
                "couldn't find struct_member: {} (within nodetypes: {})".format(
                    unused_struct_member, [clang.cindex.CursorKind.STRUCT_DECL]
                )
            )

def write_to_output_file():
    output_filename = input_filename.replace(".cpp", "_commented.cpp")
    print("Saving the prceedings so far to file: {}".format(output_filename))
    with open(output_filename, "w") as output_file:
        output_file.write("".join(lines))

index = clang.cindex.Index.create()
tu = index.parse(input_filename)
print("=======")
comment_functions(tu)
write_to_output_file()
print("=======")
comment_struct_members(tu)
write_to_output_file()
print("=======")

