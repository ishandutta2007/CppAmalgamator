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


def visit(node, search_fn_name):
    has_commented = False
    # print(node.spelling, node.kind)
    for child in node.get_children():
        has_commented |= visit(child, search_fn_name)

    if (
        node.kind == clang.cindex.CursorKind.FUNCTION_DECL
        or node.kind == clang.cindex.CursorKind.CXX_METHOD
    ) and is_starting_line_of_function(node, search_fn_name):
        for line_no in range(node.extent.start.line - 1, node.extent.end.line):
            lines[line_no] = "// " + lines[line_no]
        has_commented |= True
    return has_commented


cppcheck_filename = input_filename.replace(".cpp", "_cppcheck.txt")
with open(cppcheck_filename) as f:
    errors = f.readlines()

unused_functions = [
    re.findall("'([^']*)'", "".join(err.split(" ")))[0]
    for err in errors
    if "unusedFunction" in err
]

print(unused_functions)

index = clang.cindex.Index.create()
tu = index.parse(input_filename)

for unused_function in unused_functions:
    if visit(node=tu.cursor, search_fn_name=unused_function):
        # print("".join(lines))
        print("commented:", unused_function)
    else:
        print("couldn't find:", unused_function)

output_filename = input_filename.replace(".cpp", "_commented.cpp")
with open(output_filename, "w") as output_file:
    output_file.write("".join(lines))
