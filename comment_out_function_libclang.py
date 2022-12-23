import sys

import clang.cindex

def comment_out_function(input_filename, output_filename, function_name):
    # Create an Index object
    index = clang.cindex.Index.create()

    # Parse the input file and generate an AST
    tu = index.parse(input_filename)

    # Initialize a list to store the output lines
    output_lines = []

    # Define a helper function to recursively visit the AST nodes
    def visit(node):
        # Check if the node represents a function declaration
        if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            # Check if the function name matches the target function
            if node.spelling == function_name:
                # Comment out the function body
                output_lines.append('// {')
                for i in range(node.extent.start.line + 1, node.extent.end.line):
                    output_lines.append('// ' + tu.get_extent(tu.get_location(input_filename, i, 0)).spelling)
                output_lines.append('// }')
            else:
                # Add the function declaration to the output
                output_lines.append(tu.get_extent(node.extent.start.start, node.extent.end.end).spelling)
        # Recursively visit the children of this node
        for child in node.get_children():
            visit(child)

#     def visit(node):
#         # Check if the node represents a function declaration
#         if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
#             # Check if the function name matches the target function
#             if node.spelling == function_name:
#                 # Comment out the function body
#                 output_lines.append('// {')
#                 for i in range(node.extent.start.line + 1, node.extent.end.line):
#                     output_lines.append('// ' + tu.get_extent(tu.get_location(input_filename, i, 0)).spelling)
#                 output_lines.append('// }')
#             else:
#                 # Add the function declaration to the output
#                 output_lines.append(tu.get_extent(node.extent.start, node.extent.end).spelling)
#         # Recursively visit the children of this node
#         for child in node.get_children():
#             visit(child)

    # Visit the root node of the AST
    visit(tu.cursor)

    # Write the output file
    with open(output_filename, 'w') as output_file:
        for line in output_lines:
            output_file.write(line)

# Read the input and output filenames and the function name from the command line
input_filename = sys.argv[1]
output_filename = sys.argv[2]
function_name = sys.argv[3]

# Call the comment_out_function function
comment_out_function(input_filename, output_filename, function_name)
