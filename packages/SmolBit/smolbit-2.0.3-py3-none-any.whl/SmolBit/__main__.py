from .smolbitCore import *
from .Converter import *
from .SyntaxChecker import *
import sys
if __name__ == "__main__":
    helpmsg="""
Commands 
run [smbt file] | runs the compiled smbt file
compile [smolbit file] [smbt path] | compiles the smolbit script to an ambt file
"""
    if(len(sys.argv)<2):
        print(helpmsg)
        exit()
    if sys.argv[1] == "run":
        bitcode = sys.argv[2]
        vm = VM(bitcode)
        vm.run()
    elif sys.argv[1] == "compile":
        path = sys.argv[2]
        save = sys.argv[3]
        with open(path, "r") as file:
            bits = file.read()
        checker(bits).check()
        convert(bits, save)
    elif sys.argv[1] == "help":
        print(helpmsg)