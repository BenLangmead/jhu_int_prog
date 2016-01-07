#!/usr/bin/env python

"""
Script that takes a cppmd file (Markdown with inline C/C++), runs the
appropriate commands to compile and run the C/C++, does ppropriate
substitutions so commands and output appear, outputs markdown, then
runs pandoc to convert final markdown into slides.

Brief specification for cppmd files
===================================

File blocks
-----------

Blocks set off with <!---cppmd-file ... --> contain the contents of a text
file, usually source code.  Example:

<!---cppmd-cppfile unit7_headers1.cpp
#include <iostream>

int main(void) {
	std::cout << "Hello world" << std::endl;
	return 0;
}
-->

The name of the file is specified on the same line as the
"<!---cppmd-cppfile", separated by a space.

The "<!---cppmd-shell" has to be the first token on the line.

The contents of the file are also echoed into the final Markdown as C++
source, i.e. between "```cpp" and "```" lines.

Shell blocks
------------

Blocks set off with <!---cppmd-shell ... --> contain shell code to run.
Example:

<!---cppmd-shell
g++ -std=c++11 -pedantic -Wall -Wextra -o unit7_headers1 unit7_headers1.cpp
./unit7_headers1
-->

The "<!---cppmd-shell" has to be the first token on the line.

The commands themselves are printed into the final Markdown, with "$ "
prepended.  Standard out and standard error are also printed (with nothing
prepended).

"""

from __future__ import print_function

import os
import sys
import subprocess
import argparse

__author__ = "Ben Langmead"
__email__ = "ben.langmead@gmail.com"


def handle_shell_commands(fh, ofh, prefix='$ '):
    """
    Handle a block of shell commands.  First echo the command with "$ "
    prepended.  Then run the command and paste its output.  If there is stderr
    output, or if the input file is not formatted as expected, raise
    RuntimeError.

    :param prefix: prepend this when printing a command
    :param ofh: Output md file
    :param fh: Input cppmd file
    """
    ofh.write("```\n")
    while True:
        ln = fh.readline()
        if len(ln) == 0:
            raise RuntimeError('Ended in the middle of a shell block')
        if ln.startswith('-->'):
            break
        ln = ln.rstrip()
        print('Running command "%s"' % ln, file=sys.stderr)
        ofh.write(prefix + ln + '\n')
        p = subprocess.Popen(ln, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        ofh.write(out)
        ofh.write(err)
    ofh.write("```\n")


def handle_source_file(fh, ofh, fn, force=False):
    """
    Handle a file block.  Write the contents to a file with the specified name
    and echo to the markdown inside a ```cpp ... ``` block.

    :param fh: Input cppmd file
    :param ofh: Output md file
    :param fn: Name of output file
    :param force: If false, raise error when file with that name exists
    """
    if os.path.exists(fn) and not force:
        raise RuntimeError('Refusing to overwrite "%s"' % fn)
    ofh.write("```cpp\n")
    with open(fn, 'w') as cpp_ofh:
        while True:
            ln = fh.readline()
            if len(ln) == 0:
                raise RuntimeError('Ended in the middle of a C++ source block')
            if ln.startswith('-->'):
                break
            ofh.write(ln)
            cpp_ofh.write(ln)
    ofh.write("```\n")


def go(fh, prefix, force, no_pandoc, pandoc_style):
    """
    Main driver.

    :param fh: Input file
    :param prefix: String to prepend to output files
    :param force: If false, raise error when about to overwtite a file
    :param no_pandoc: If true, skip running pandoc
    :param pandoc_style: Specifies style to pass to pandoc -t
    :return:
    """
    with open(prefix + '.md', 'w') as md_ofh:
        while True:
            ln = fh.readline()
            if len(ln) == 0:
                break
            if ln.strip().startswith('<!---cppmd-file'):
                handle_source_file(fh, md_ofh, ln.rstrip().split()[-1], force=force)
            elif ln.strip().startswith('<!---cppmd-shell'):
                handle_shell_commands(fh, md_ofh)
            else:
                md_ofh.write(ln)
    if not no_pandoc:
        cmd = 'pandoc -t %s %s -o %s' % (pandoc_style, prefix + '.md', prefix + '.pdf')
        print('Running pandoc command: "%s"' % cmd, file=sys.stderr)
        os.system(cmd)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run a C/C++ markdown file, creating source files, '
                    'running shell commands and pasting their output '
                    'appropriately formatted blocks.  pandoc must be '
                    'installed')
    parser.add_argument(
        '--prefix', metavar='path', type=str, required=True,
        help='Write output to <prefix>.md and <prefix>.pdf')
    parser.add_argument(
        '--pandoc-style', metavar='path', type=str, default='beamer',
        help='pandoc -t <style>')
    parser.add_argument(
        '--force', action='store_const', const=True, default=False,
        help='Overwrite .c/.cpp files that already exist')
    parser.add_argument(
        '--skip-pandoc', action='store_const', const=True, default=False,
        help='Don\'t run pandoc; just write the <prefix>.md file')
    args = parser.parse_args()
    go(sys.stdin, args.prefix,
       force=args.force,
       no_pandoc=args.skip_pandoc,
       pandoc_style=args.pandoc_style)
