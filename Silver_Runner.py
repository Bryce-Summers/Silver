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

# Default location for source code file.
ag_code_file = "./Test/Program.txt"
exe_file     = "./Test/Program.py" # Executable.

# Returns True if no errors.
def compile(ag_file, dst_file):
    print(f"src: {ag_file} -> dest: {dst_file}")
    
    with open(ag_file, 'r', encoding="utf-8", errors="ignore") as f_src:
        with open(dst_file, 'w', encoding="utf-8", errors="ignore") as f_out:
            parser = Silver_Parser.Silver_Parser(f_src, f_out)
            return parser.parseFile() # That's it!

# https://docs.python.org/3/library/subprocess.html
# https://discuss.python.org/t/how-to-run-a-py-file-from-another-py-file/59895
def run(python_file):
    subprocess.run(["python", python_file])




if len(sys.argv) >= 2:
    print(sys.argv)
    ag_code_file = sys.argv[1]

# Try to compile, then run the exe if compilation was sucessful.
if compile(ag_code_file, exe_file):
    run(exe_file)