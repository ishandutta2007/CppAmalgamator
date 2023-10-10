import sys
import clang.cindex
import pprint as pp
import colorama
import re
import copy

pattern = r"^(\d+):( *)(\d+):(.*)$"
pattern_comment1 = r"^(\-):( *)(\d+):(.*)$"
pattern_comment2 = r"^#####:( *)(\d+):(.*)$"
pattern_pass = r"^(.*):( *)(\d+)-block(.*)$"
pattern_somebigkey = r"^[a-zA-Z0-9_]*:$"

statically_commented_filename = sys.argv[1]

with open(statically_commented_filename) as f:
    statcom_lines = f.readlines()


gcov_filename = statically_commented_filename.replace(
    "expanded_commented.cpp", "expanded_commented.cpp.gcov"
)
with open(gcov_filename) as f:
    gcov_lines = f.readlines()
del gcov_lines[:4]

gcov_lines = [i for i in gcov_lines if not re.compile(pattern_pass).match(i)]
# gcov_lines = [i for i in gcov_lines if i !='------------------\n']
# gcov_lines = [i for i in gcov_lines if not (re.compile(pattern_somebigkey).match(i) and len(i)>100)]

gcov_lines_cleaned = []
skip_mode_ebabled = False
for i, gcov_line in enumerate(gcov_lines):
    if (
        skip_mode_ebabled == False
        and gcov_line == "------------------\n"
        and re.compile(pattern_somebigkey).match(gcov_lines[i + 1])
        and len(gcov_lines[i + 1]) > 32
    ):
        skip_mode_ebabled = True
    if (
        skip_mode_ebabled == True
        and gcov_lines[i - 1] == "------------------\n"
        and not (
            re.compile(pattern_somebigkey).match(gcov_line) and len(gcov_line) > 32
        )
    ):
        skip_mode_ebabled = False
    if skip_mode_ebabled == False:
        gcov_lines_cleaned.append(gcov_line)

gcov_lines = gcov_lines_cleaned
assert len(statcom_lines), len(gcov_lines)

index = clang.cindex.Index.create()
tu = index.parse(statically_commented_filename)

FUNDEF_CUR_KINDS = [
    "CXX_METHOD",
    "FUNCTION_TEMPLATE",
    "FUNCTION_DECL",
    "CONSTRUCTOR",
    "DESTRUCTOR",
]

FUNDEC_CUR_KINDS = [
    "FUNCTION_DECL",
]


OTHER_KINDS = [
    "USING_DECLARATION",
]

def is_totally_dead(node):
    for line_no in range(node.extent.start.line - 1, node.extent.end.line):
        match = re.match(pattern_comment1, gcov_lines[line_no].strip())
        # print(statcom_lines[line_no], match)
        if not match:
            # print(node.extent.start.line,"is not dead")
            return False
    # print(node.extent.start.line,"is_totally_dead")
    return True


def comment_it(node):
    for line_no in range(node.extent.start.line - 1, node.extent.end.line):
        if statcom_lines[line_no].strip()[:2] != "//":
            statcom_lines[line_no] = "// " + statcom_lines[line_no]


def is_function_definition(node):
    # TODO:node.extent.start.line < node.extent.end.line is my hack to separate defination and declaration
    ret = False
    if node.extent.start.line == node.extent.end.line:
        if (
            statcom_lines[node.extent.end.line - 1].strip()[-2:] == "{}"
            or statcom_lines[node.extent.end.line - 1].strip()[-3:] == "{};"
        ):
            ret = True
    if node.extent.start.line + 1 == node.extent.end.line:
        if (
            statcom_lines[node.extent.end.line - 1].strip()[-2:] == "{}"
            or statcom_lines[node.extent.end.line - 1].strip()[-3:] == "{};"
        ):
            ret = True
        if (
            statcom_lines[node.extent.start.line - 1].strip()[-1:] == "{"
            or statcom_lines[node.extent.end.line - 1].strip()[-1] == "}"
        ):
            ret = True
        if (
            statcom_lines[node.extent.start.line - 1].strip()[-1:] == "{"
            or statcom_lines[node.extent.end.line - 1].strip()[-2:] == "};"
        ):
            ret = True
    else:
        if (
            statcom_lines[node.extent.start.line - 1].strip()[-1:] == "{"
            or statcom_lines[node.extent.end.line - 1].strip()[-1] == "}"
        ):
            ret = True
        if (
            statcom_lines[node.extent.start.line - 1].strip()[-1:] == "{"
            or statcom_lines[node.extent.end.line - 1].strip()[-2:] == "};"
        ):
            ret = True
    if node.extent.start.line == 1073:
        print(node.spelling, node.kind, "is_function_definition=", ret)
    return ret

def is_function_declaration(node):
    ret = False
    if node.extent.start.line == node.extent.end.line:
        if (
            statcom_lines[node.extent.end.line - 1].strip()[-1] == ";"
            and statcom_lines[node.extent.end.line - 1].strip()[-2] != "}"
        ):
            ret = True
    if node.extent.start.line == 1073:
        print(node.spelling, node.kind, "is_function_declaration=", ret)
    return ret

def visit(node):
    try:
        kindly = str(node.kind).replace("CursorKind.", "")
        # print(str(node.kind))
    except Exception as e:
        kindly = "0"
    if int(node.extent.start.line) > 0:  # 19666:  # 22766:#22806:
        # if int(node.extent.start.line) == 20605:  # 19666:  # 22766:#22806:
        # TODO:Why does ut label both function defination and declaration as FUNCTION_DECL?
        if node.extent.start.line == 1073:
            print(node.spelling, node.kind)
        if kindly in FUNDEF_CUR_KINDS and is_function_definition(node):
            if is_totally_dead(node):
                comment_it(node)
                # print(
                #     "Commented",
                #     node.extent.start.line,
                #     node.extent.end.line,
                #     node.spelling,
                #     kindly,
                # )
                return
        elif kindly in FUNDEC_CUR_KINDS and is_function_declaration(node):
            if is_totally_dead(node):
                comment_it(node)
                # print(
                #     "Commented",
                #     node.extent.start.line,
                #     node.extent.end.line,
                #     node.spelling,
                #     kindly,
                # )
                return
        elif kindly in OTHER_KINDS:
            if is_totally_dead(node):
                comment_it(node)
                # print(
                #     "Commented",
                #     node.extent.start.line,
                #     node.extent.end.line,
                #     node.spelling,
                #     kindly,
                # )
                return
        else:
            # print(
            #     "Skipped",
            #     node.extent.start.line,
            #     node.extent.end.line,
            #     node.spelling,
            #     kindly,
            # )
            pass
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
