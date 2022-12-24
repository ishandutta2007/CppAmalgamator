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


gcov_filename = statically_commented_filename.replace(
    "expanded_commented.cpp", "expanded_commented.cpp.gcov"
)
with open(gcov_filename) as f:
    gcov_lines = f.readlines()


index = clang.cindex.Index.create()
tu = index.parse(statically_commented_filename)

cnt = 0

functions = []


def is_totally_dead(node):
    for line_no in range(node.extent.start.line - 1, node.extent.end.line):
        match = re.match(pattern_comment1, gcov_lines[line_no].strip())
        if not match:
            return False
    return True


def comment_it(node):
    for line_no in range(node.extent.start.line - 1, node.extent.end.line):
        if statcom_lines[line_no].strip()[:2] != "//":
            statcom_lines[line_no] = "// " + statcom_lines[line_no]


def visit(node):
    # global cnt
    try:
        kindly = str(node.kind).replace("CursorKind.", "")
        # print(str(node.kind))
    except Exception as e:
        kindly = "0"
    if (
        (node.extent.start.line < node.extent.end.line)
        and ("CXX_METHOD" in kindly)
        and int(node.extent.start.line) > 18000
    ):
        # or "METHOD" in kindly #CXX_METHOD # FUNCTION_TEMPLATE FUNCTION_DECL
        # ):
        # print(node.extent.start.line, node.extent.end.line, node.spelling, kindly)
        # functions.append([node.extent.start.line, node.extent.end.line, node.spelling, kindly])
        # cnt += 1
        if is_totally_dead(node):
            comment_it(node)
            print(
                "Commented",
                node.extent.start.line,
                node.extent.end.line,
                node.spelling,
                kindly,
            )
            return
    for child in node.get_children():
        visit(child)


visit(tu.cursor)


def write_to_output_file():
    output_filename = statically_commented_filename.replace(
        "_commented.cpp", "_commented_coveraged.cpp"
    )
    print("Saving the prceedings so far to file: {}".format(output_filename))
    with open(output_filename, "w") as output_file:
        output_file.write("".join(statcom_lines))


write_to_output_file()


# pp.pprint(functions)
# print(cnt)

# functions.reverse()
# functions = functions[1:]
# for idx, fn in (functions):
#     is_commented(fn)
