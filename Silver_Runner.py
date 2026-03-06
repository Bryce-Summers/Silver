"""
Compile + Run Programs.

 - Transforms an Ag File into a Python File.

History:
 - Jan.16.2026: Adapted by Bryce Summers from another of his
                compiler for Transcript reports.
 - Mar.5.2026:  Renamed this project to align with Agnostic
                programming brand name.
"""

import Silver_Parser
import sys, subprocess
import traceback

# Default location for source code file.
ag_code_file = "./Test/Program_01.ag" # User written Ag program.
exe_file     = "./Test/Program.py"    # Executable generated form compiler.
input_file   = "./Test/Input.txt"     # Stream of input for tests.

# Returns True if no errors.
def compile(ag_file, dst_file):

    global parser

    print(f"src: {ag_file} -> dest: {dst_file}")
    
    with open(ag_file, 'r', encoding="utf-8", errors="ignore") as f_src:
        with open(dst_file, 'w', encoding="utf-8", errors="ignore") as f_out:
            parser = Silver_Parser.Silver_Parser(f_src, f_out)
            return parser.parseFile() # That's it!

# https://docs.python.org/3/library/subprocess.html
# https://discuss.python.org/t/how-to-run-a-py-file-from-another-py-file/59895
def run(python_file):
    #subprocess.run(["python", python_file])

    global parser

    try:
        with open(input_file, 'r') as f_in:

            # Run the subprocess, passing the file object to stdin
            # Use text=True for string input/output (Python 3.7+)
            result = subprocess.run(
                ["python", python_file],
                stdin=f_in,
                capture_output=True,
                text=True,
                check=True
            )
        print("Program output:")
        print("-------------- ")
        print(result.stdout)

    except FileNotFoundError:
        print("Error: {input_file} not found.")

    except subprocess.CalledProcessError as e:

        def errorToLineNumber(e):
            msg = f"{e.stderr}"
            
            msg = "".join([c for c in msg if '0' <= c <= '9' or c == ','])
            msg = msg.split(",")[-2]

            return int(msg)

        error_line_number = parser.pythonToAgLineNumber(errorToLineNumber(e))
        print("Runtime Error: The input stream has no more data. Check your problem requirements and use less input() statements.")
        print(f"The Error occured on line {error_line_number} or your .Ag file.")

if len(sys.argv) >= 2:
    print(sys.argv)
    ag_code_file = sys.argv[1]

# Try to compile, then run the exe if compilation was sucessful.
if warnings := compile(ag_code_file, exe_file) == 0:
    print("Compilation was successful! I'm running your program now:\n")
    run(exe_file)
else:
    msg =f"Your program won't be run until you heed the compiler's {warnings} warnings and spruce up your program."\
         f"\nI reccomend that you start by fixing error number #1, as it might be the source of the other errors."
    #print(f'{"-"*len(msg)}\n{msg}\n{"-"*len(msg)}')
    print(f"\n{msg}\n")