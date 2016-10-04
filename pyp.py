"""

pyp, a python preprocessor:
    Copyright (C) 2011 Stephen L Bade
    This software is provided "as is", without any express or implied warranty.
    Permission is granted to anyone to use this software for any purpose,
    including commercial applications, and to alter it and redistribute it
    freely, provided origin of this software is not misrepresented.  
    Modified versions must be marked as such.  
    Acknowledgement of use in a program is not required.    
    Written for Python grammar version 3    
    The concepts here are similar to 'pp', 
    a perl preprocessor written by Richard Rudell, 
    but the idea predates 'pp'  
"""

import optparse
import sys
import re

# picks out expressions from text, using `name`
argFinder = re.compile("`(.+?)[:.*]?`") # ? for non-greedy

_numErrors = 0;
def _error(msg):
    global _numErrors;
    _numErrors += 1;
    print(msg);

def _ParseOptions(args):
    ""
    usage = "usage: %prog [options] files"
    parser = optparse.OptionParser(usage=usage, version="%prog 1.0")
    parser.add_option("--verbose", dest="verbose", action="store_true", help="Verbose messages")
    parser.add_option("--save-python", dest="save_python", action="store_true", help="Save generated python code")
    parser.add_option("--print-vars", dest="print_vars", action="store_true", help="Print variables set on the command line")
    parser.add_option("--code-char", metavar="char", dest="code_char", action="store", 
                      help="Use this as the first char of a line of python code", default='!')
    parser.add_option("--handler", metavar="Function to call for text lines", dest="handler", action="store", 
                      help="Optional function to call on text lines. Default is print", default='print')
    parser.add_option("--header-code", metavar="Python to run at the start. Use \\n for newline", dest="header_code", action="store", 
                      help="Optional code at the start", default='')
    parser.add_option("--footer-code", metavar="Python to run at the end", dest="footer_code", action="store", 
                      help="Optional code at the end", default='')
    parser.add_option("-s", "--set", dest="vars", action="append", default=[], help="Set a variable with format: name=value")
    (opt, args) = parser.parse_args(args)    
    if opt.verbose:
        print(opt.vars)
    # Block start and end chars. Use {} rather than : so we don't need to indent the input text.
    opt.blockStartChar = '{'
    opt.blockEndChar = '}'
    if opt.header_code:
        opt.header_code = opt.header_code.replace("\\n", "\n")
    if opt.footer_code:
        opt.footer_code = opt.footer_code.replace("\\n", "\n")
    return (opt, args)
    
class Pyp(object):
    def __init__(self, opt):
        self.opt = opt
        self.code = []
        self.indent = 0
    
    def AddCodeLine(self, codeLine):
        "Add a line of python code"
        line = codeLine.strip() # use { and } for indent, not :
        
        if line.startswith(self.opt.blockEndChar):
            line = line[ len(self.opt.blockEndChar):].strip()
            if self.indent:
                self.indent -= 1
            else:
                _error("Error: unmatched block ending: {}".format(codeLine))

        if line.endswith(':') :
            _error("Error: use {} and {} instead of : ".format(self.opt.blockStartChar, self.opt.blockEndChar))

        nextIndent = self.indent
        if line.endswith(self.opt.blockStartChar):
            endlen = len(self.opt.blockStartChar)
            line = line[0 : -endlen] + ":" # start of block
            nextIndent += 1
            
        self.AppendAndIndent(line)
        self.indent = nextIndent
        
    def AddTextLine(self, textLine):
        "Add a line of plain text"
        t = argFinder.sub("{}", textLine) # todo: keep format specifiers
        args = []
        for m in argFinder.finditer(textLine):
            args.append( m.group(1))
        q1 = 'r"""'  # quotes to use
        q2 = '"""'
        if -1 == textLine.find('\\') and -1 == textLine.find('"'):
            q1 = '"'
            q2 = '"'
        elif -1 == textLine.find('\\') and -1 == textLine.find("'"):
            q1 = "'"
            q2 = "'"
        else:
            if textLine.startswith('"'): q1 = 'r""" '
            if textLine.endswith('"'): q2 = ' """'
        if textLine.endswith('\\'):
            q2 = '\\ ' + q2; # escape last slash
        if not args:
            self.AppendAndIndent('{}({}{}{})'.format(self.opt.handler, q1, textLine, q2))
        else:
            self.AppendAndIndent('{}({}{}{}.format({}))'.format(self.opt.handler, q1, t, q2, ",".join(args)))

    def AppendAndIndent(self, code):
        self.code.append("{}{}".format(' ' * (4*self.indent), code))

def _IsCode(opt, line):
    "Check to see if a line is code."
    return line.startswith(opt.code_char)
    
def _ReadFile(opt, fh, pyp):
    if opt.header_code:
        pyp.AddCodeLine(opt.header_code) 
    for line in fh.readlines():
        line = line.rstrip('\n')
        if len(line) and _IsCode(opt, line):
            pyp.AddCodeLine(line[ len(opt.code_char) : ])
        else:
            pyp.AddTextLine(line)
    if opt.footer_code:
        pyp.AddCodeLine(opt.footer_code) 

def _ExecuteFile(opt, file):
    if opt.verbose:
        print ("Executing: {}".format(file))
    pyp = Pyp(opt)
    fh = open(file)
    _ReadFile(opt, fh, pyp)
    fh.close()
    code_str = "\n".join(pyp.code)
    if opt.save_python:
        gen_fname = file + ".py"
        if opt.verbose:
            print("Writing {}".format(gen_fname))
        try:
            gen = open(gen_fname, "w")
            gen.write(code_str)
            gen.close()
        except BaseException as e:
            print("Error saving generated python: " + str(e))
    _ExecCodeString(code_str)
    
def _ExecCodeString(code_str):
    global_dict = globals(); 
    try:
        exec(code_str, global_dict)
    except NameError as e:
        _error(str(e))
    except SyntaxError as e:
        _error("Unknown '!' command, or invalid script syntax.")
    except BaseException as e:
        _error("Script error: {}".format(str(e)))


def ExecuteFile(file):
    (opt, unused_files) = _ParseOptions([]) # Use Defaults
    _ExecuteFile(opt, file)


def ExecuteString(lines):
    (opt, unused_files) = _ParseOptions([]) # Use Defaults
    pyp = Pyp(opt)
    if opt.header_code:
        pyp.AddCodeLine(opt.header_code) 
    for line in lines.split("\n"):
        line = line.rstrip('\n')
        if len(line) and _IsCode(opt, line):
            pyp.AddCodeLine(line[ len(opt.code_char) : ])
        else:
            pyp.AddTextLine(line)
    if opt.footer_code:
        pyp.AddCodeLine(opt.footer_code) 
    code_str = "\n".join(pyp.code)
    _ExecCodeString(code_str)
       

def main():
    (opt, files) = _ParseOptions(sys.argv[1:])
    for name_val in opt.vars:
        try:
            (n,v) = name_val.split('=',1)
            globals()[n] = v
            if opt.print_vars:
                print("{}={}".format(n,v))
        except BaseException as e:
            _error("Error: expected name=value for argument -s, --set.  Got {}. Error: {}".format(name_val, str(e)))
            return
    
    if 0 == len(files):
        _error("Error: no files")
    else:
        for file in files:
            _ExecuteFile(opt, file)


if __name__ == "__main__":
    main()
    if _numErrors:
        sys.exit(_numErrors)

def coolFn():
    return 42
