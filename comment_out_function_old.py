import sys


def comment_out_function(input_filename, output_filename, function_name):
    # Read the input file
    with open(input_filename, "r") as input_file:
        input_lines = input_file.readlines()

    # Initialize variables to track the start and end of the function
    in_function = False
    function_start = 0
    function_end = 0

    # Iterate through the lines of the input file
    for i, line in enumerate(input_lines):
        # Check if the line contains the function name
        if function_name in line:
            # Check if the function is starting or ending
            if "{" in line:
                # Function is starting
                in_function = True
                function_start = i
            elif "}" in line:
                # Function is ending
                in_function = False
                function_end = i
                break

    # Comment out the function body
    for i in range(function_start + 1, function_end):
        input_lines[i] = "// " + input_lines[i]

    # Write the output file
    with open(output_filename, "w") as output_file:
        for line in input_lines:
            output_file.write(line)


# Read the input and output filenames and the function name from the command line
input_filename = sys.argv[1]
output_filename = sys.argv[2]
function_name = sys.argv[3]

# Call the comment_out_function function
comment_out_function(input_filename, output_filename, function_name)
