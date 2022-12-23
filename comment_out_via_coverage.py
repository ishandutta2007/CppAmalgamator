import sys
import clang.cindex
import pprint as pp
import colorama
import re


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

# pp.pprint(statcom_lines[-200:])
del gcov_lines[:4]
# pp.pprint(gcov_lines[-200:])

# print(len(statcom_lines), len(gcov_lines))
index = clang.cindex.Index.create()
tu = index.parse(statically_commented_filename)


def get_innermost_node_containing_line_no(node, line_number):
    ret = None
    if node.extent.start.line <= line_number and line_number <= node.extent.end.line:
        for child in node.get_children():
            ret = get_innermost_node_containing_line_no(child, line_number)
            if ret:
                return ret
        ret = node

    return ret


def get_starting_line_no_of_node_containing_line_no(line_number):
    node_inner = get_innermost_node_containing_line_no(tu.cursor, line_number)
    if node_inner:
        return node_inner.extent.start.line


def get_ending_line_no_of_node_containing_line_no(line_number):
    node_inner = get_innermost_node_containing_line_no(tu.cursor, line_number)
    if node_inner:
        return node_inner.extent.end.line


def uncomment_parent_node(line_number):
    node_inner = get_innermost_node_containing_line_no(tu.cursor, line_number)
    if node_inner:
        parent_node = node_inner.lexical_parent
        print(
            node_inner.extent.start.line,
            node_inner.extent.end.line,
            parent_node.extent.start.line,
            parent_node.extent.end.line,
        )
        if parent_node:
            parent_start = parent_node.extent.start.line
            while statcom_lines[int(parent_start) - 1][:2] == "//":
                statcom_lines[int(parent_start) - 1] = statcom_lines[
                    int(parent_start) - 1
                ][2:].lstrip()
            parent_end = parent_node.extent.end.line
            while statcom_lines[int(parent_end) - 1][:2] == "//":
                statcom_lines[int(parent_end) - 1] = statcom_lines[int(parent_end) - 1][
                    2:
                ].lstrip()


for line in gcov_lines:  # [-200:]:
    match = re.match(pattern, line.strip())
    if match:
        execution_count = match.group(1)
        line_number = int(match.group(3))
        code = match.group(4)
        # print("Excuted", execution_count, "times, on line_no", line_number, "=>", code)
        uncomment_parent_node(line_number)
    elif re.match(pattern_comment1, line.strip()):
        match2 = re.match(pattern_comment1, line.strip())
        if match2:
            line_number = int(match2.group(2))
            code = match2.group(3)
            if code.strip() not in ["}", "} // namespace"]:
                statcom_lines[int(line_number) - 1] = (
                    "// " + statcom_lines[int(line_number) - 1]
                )
            else:
                # ie code is in ["}"]
                st_line_number = get_starting_line_no_of_node_containing_line_no(
                    line_number
                )
                try:
                    if st_line_number and statcom_lines[st_line_number - 1][:2] == "//":
                        statcom_lines[int(line_number) - 1] = (
                            "// " + statcom_lines[int(line_number) - 1]
                        )
                except Exception as e:
                    print(st_line_number, line_number)
                    raise e
            # print("NOT Excuted, on line_no", line_number, "=>", code)
    elif re.match(pattern_comment2, line.strip()):
        # unreacheble code case
        match3 = re.match(pattern_comment2, line.strip())
        if match3:
            line_number = int(match3.group(2))
            code = match3.group(3)
            # print("pattern_#####, on line_no", line_number, "=>", code)
            if "return" not in code:
                statcom_lines[int(line_number) - 1] = (
                    "// " + statcom_lines[int(line_number) - 1]
                )
            else:
                st_line_number = get_starting_line_no_of_node_containing_line_no(
                    line_number
                )
                try:
                    if st_line_number and statcom_lines[st_line_number - 1][:2] == "//":
                        statcom_lines[int(line_number) - 1] = (
                            "// " + statcom_lines[int(line_number) - 1]
                        )
                except Exception as e:
                    print(st_line_number, line_number)
                    raise e
    elif re.match(pattern_pass, line.strip()):
        match4 = re.match(pattern_pass, line.strip())
        if match4:
            line_number = match4.group(1)
            # print("pass", line_number, "=>", line)
    else:
        print("Didnt match =>", line)
        pass

gcov_lines.reverse()
for line in gcov_lines:  # [-200:]:
    if re.match(pattern_comment1, line.strip()):
        match2 = re.match(pattern_comment1, line.strip())
        if match2:
            line_number = int(match2.group(2))
            code = match2.group(3)
            if code.strip() in ["try {", "namespace "]:
                # ie code is in ["try {"]
                ed_line_number = get_ending_line_no_of_node_containing_line_no(
                    line_number
                )
                print(line_number, ed_line_number)
                try:
                    if ed_line_number and statcom_lines[ed_line_number - 1][:2] == "//":
                        statcom_lines[int(line_number) - 1] = (
                            "// " + statcom_lines[int(line_number) - 1]
                        )
                except Exception as e:
                    print(ed_line_number, line_number)
                    raise e

# pp.pprint(statcom_lines[-200:])


def write_to_output_file():
    output_filename = statically_commented_filename.replace(
        "_commented.cpp", "_commented_coveraged.cpp"
    )
    print("Saving the prceedings so far to file: {}".format(output_filename))
    with open(output_filename, "w") as output_file:
        output_file.write("".join(statcom_lines))


write_to_output_file()

# dynamically_commented_filename= statically_commented_filename.replace("_commented.cpp", "_commented_coveraged.cpp")
# python ../../CppAmalgamator/comment_out_via_coverage.py crt_expanded_commented.cpp
