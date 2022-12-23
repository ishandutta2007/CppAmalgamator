import sys
import clang.cindex
import pprint as pp
import re

input_filename = sys.argv[1]
with open(input_filename) as f:
    lines = f.readlines()


def is_starting_line_of_function(node, search_fn_name):
    if node.spelling == search_fn_name:
        print(
            "found {} starting at line no {}".format(
                node.spelling, node.extent.start.line
            )
        )
        # print(dir(node))
        return True
    return False


def visit(
    node, search_fn_name, search_node_kind=[clang.cindex.CursorKind.FUNCTION_DECL]
):
    commented_cnt = 0
    # if node.spelling=="__mbstate_t":
    # print(node.spelling, "=>", node.kind, node.extent.start.line)
    for child in node.get_children():
        commented_cnt += visit(child, search_fn_name)

    if (
        node.kind
        in search_node_kind  # clang.cindex.CursorKind.TYPEDEF_DECL#
        # or node.kind == clang.cindex.CursorKind.CXX_METHOD
    ) and is_starting_line_of_function(node, search_fn_name):
        for line_no in range(node.extent.start.line - 1, node.extent.end.line):
            lines[line_no] = "// " + lines[line_no]
        commented_cnt += True
    return commented_cnt


cppcheck_filename = input_filename.replace(".cpp", "_cppcheck.txt")
with open(cppcheck_filename) as f:
    errors = f.readlines()


def comment_functions(tu):
    unused_functions = [
        re.findall("'([^']*)'", "".join(err.split(" ")))[0]
        for err in errors
        if "unusedFunction" in err
    ]

    print(unused_functions)

    for unused_function in unused_functions:
        instances = visit(
            node=tu.cursor,
            search_fn_name=unused_function,
            search_node_kind=[clang.cindex.CursorKind.FUNCTION_DECL],
        )
        if instances > 0:
            # print("".join(lines))
            print("commented function {}: {} times".format(unused_function, instances))
        else:
            print("couldn't find function:", unused_function)


def comment_struct_members(tu):
    unused_struct_members = [
        re.findall("'([^']*)'", "".join(err.split(" ")))[0]
        for err in errors
        if "unusedStructMember" in err
    ]

    print(unused_struct_members)

    for unused_struct_member in unused_struct_members:
        instances = visit(
            node=tu.cursor,
            search_fn_name=unused_struct_member,
            search_node_kind=[clang.cindex.CursorKind.STRUCT_DECL],
        )
        if instances > 0:
            # print("".join(lines))
            print(
                "commented struct_member {}: {} times".format(
                    unused_function, instances
                )
            )
        else:
            print("couldn't find struct_member:", unused_struct_member)


index = clang.cindex.Index.create()
tu = index.parse(input_filename)
print("=======")
comment_functions(tu)
print("=======")
comment_structures(tu)
print("=======")

output_filename = input_filename.replace(".cpp", "_commented.cpp")
with open(output_filename, "w") as output_file:
    output_file.write("".join(lines))
