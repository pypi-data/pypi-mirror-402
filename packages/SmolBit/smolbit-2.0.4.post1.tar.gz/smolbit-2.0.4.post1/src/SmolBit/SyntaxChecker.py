import colorama

class checker():
    def __init__(self, bitcode:str):
        self.bitcode = bitcode#.replace("[", "").replace("(", "").replace(")", "")
        self.pos=0
        self.line=1
        self.posinline=1
        self.lastpos = (0,0)
        self.blockdepth = 0
        self.blockslist = []

        self.ignored = "()[]"
        self.numbers = "1234567890abcdef"
        self.boolops = "=<>!"
        self.booloptable = {
            "=":"==",
            "<":"<=",
            ">":">=",
            "!":"!="
        }
        self.quotes = ['"', "'"]
    
    def read(self, n, incpos=True):
        if self.pos + n > len(self.bitcode):
            raise RuntimeError("Unexpected end of bitstream")
        out = self.bitcode[self.pos:self.pos+n]
        if(incpos):
            self.lastpos = (self.line, self.posinline)
            self.pos += n
            self.posinline += n
            if('\n' in out):
                self.line+=1
                self.posinline=1
        return out

    def expect(self, mode:tuple|list, checkNext=True):
        if(mode[0]=="num"):
            num = ''
            for i in range(mode[1]):
                nextnum = self.read(1)
                if nextnum in self.numbers:
                    num += nextnum
                else:
                    if(not nextnum.isspace() and nextnum not in self.ignored):
                        raise SyntaxError(f"Character at {self.lastpos} was not a number")
                    else:
                        num+=self.expect(("num",1), False)
            if(self.read(1, False) in self.numbers and checkNext):
                raise SyntaxError(f"Unexpected number at ({self.line}, {self.posinline})")
            return num
        elif(mode[0]=="boolop"):
            op = self.read(1)
            if(op in self.boolops):
                return op
            else:
                if(not op.isspace() and op not in self.ignored):
                    raise SyntaxError(f"Character at {self.lastpos} was not a boolean operator (i, j, k, l)")
                else:
                    return self.expect(["boolop"])
        elif(mode[0]=="all"):
            num = ''
            if(not mode[2]):
                if isinstance(mode, tuple):
                    mode = list(mode)
                mode[1] = 1
            for i in range(mode[1]):
                nextnum = self.read(1)
                if(nextnum.isspace() or nextnum in self.ignored):
                    num+=self.expect(("all",1,mode[2]), False)
                else:
                    num+=nextnum
                    if(not mode[2]):
                        self.bitcode = nextnum + self.bitcode
            return num
    
    def check(self, printB = False):
        while not self.pos >= len(self.bitcode):
            char = self.read(1, False)
            if char.isspace() or char in self.ignored:
                if char == "]":
                    self.read(1, True)
                    self.blockdepth -= 1
                    if len(self.blockslist):
                        if printB:
                            print(f"END {self.blockslist.pop()}")
                    if self.blockdepth < 0 and not self.pos+1>len(self.bitcode):
                        if printB:
                            print(f"{colorama.Fore.YELLOW}SyntaxWarning{colorama.Fore.RESET} ']' at {self.lastpos} will end the script, possibly prematurely. if this is intentional, ignore this message.")
                    continue
                self.read(1, True)
                continue
            if self.pos + 3 > len(self.bitcode):
                break

            operation = self.read(2)

            if(operation == "IF"):
                self.blockdepth+=1
                self.blockslist.append("IF")
                n = self.expect(("num",1))
                o = self.expect(["boolop"])
                m = self.expect(("num",1))
                if printB:
                    print(f"IF reg{n} {self.booloptable[o]} reg{m}")
                continue
            
            operation += self.read(1)

            if(operation == "DPI"):
                c = self.expect(('all', 1, False))
                if(c in self.quotes):
                    usedQuote = c
                    chars = ""
                    while not char == usedQuote:
                        char = self.read(1, True)
                        chars += char
                    if printB:
                        print(f"Print immediate \"{chars}\"")
                else:
                    n=self.expect(("num", 2))
                    if printB:
                        print(f"Print immediate 0x{n} ({int(n, 16).to_bytes(1).decode()})")
            elif(operation == "DPU"):
                n=self.expect(("num",1))
                if printB:
                    print(f"Print register {n} (utf8)")
            elif(operation == "DPD"):
                n=self.expect(("num",1))
                if printB:
                    print(f"Print register {n} (dec)")
            elif(operation == "DPH"):
                n=self.expect(("num",1))
                if printB:
                    print(f"Print register {n} (hex)")
            elif(operation == "ADD"):
                n=self.expect(("num",2))
                m=n[1]
                n=n[0]
                if printB:
                    print(f"reg{n} = reg{n} + reg{m}")
            elif(operation == "SUB"):
                n=self.expect(("num",2))
                m=n[1]
                n=n[0]
                if printB:
                    print(f"reg{n} = reg{n} - reg{m}")
            elif(operation == "MUL"):
                n=self.expect(("num",2))
                m=n[1]
                n=n[0]
                if printB:
                    print(f"reg{n} = reg{n} * reg{m}")
            elif(operation == "DIV"):
                n=self.expect(("num",2))
                m=n[1]
                n=n[0]
                if printB:
                    print(f"reg{n} = reg{n} / reg{m}")
            elif(operation == "SET"):
                n=self.expect(("num",2))
                m=n[1]
                n=n[0]
                if printB:
                    print(f"reg{n} = reg{m}")
            elif(operation == "LDI"):
                n=self.expect(("num",1), False)
                m=self.expect(("num",2))
                if printB:
                    print(f"reg{n} = 0x{m}")
            elif(operation == "INC"):
                n=self.expect(("num",1))
                if printB:
                    print(f"INC reg{n}")
            elif(operation == "DEC"):
                n=self.expect(("num",1))
                if printB:
                    print(f"DEC reg{n}")
            elif(operation == "CLZ"):
                n=self.expect(("num", 1))
                if printB:
                    print(f"reg{n} = 0")
            elif(operation == "CLI"):
                n=self.expect(("num", 1))
                if printB:
                    print(f"reg{n} = {int(n, base=16)}")
            elif(operation == "POW"):
                n=self.expect(("num",2))
                m=n[1]
                n=n[0]
                if printB:
                    print(f"reg{n} = reg{n} ^ reg{m}")
            elif(operation == "ROT"):
                n=self.expect(("num",2))
                m=n[1]
                n=n[0]
                if printB:
                    print(f"reg{n} = (reg{m})root of reg{n}")
            elif(operation == "REP"):
                self.blockdepth+=1
                self.blockslist.append("REPEAT")
                n = self.expect(("num",1))
                if printB:
                    print(f"REPEAT reg{n}")
            elif(operation == "DEF"):
                self.blockdepth+=1
                self.blockslist.append("FUNCDEF")
                n = self.expect(("num",1))
                if printB:
                    print(f"FUNCDEF func{n}")
            elif(operation == "UDF"):
                n = self.expect(("num",1))
                if printB:
                    print(f"FUNCUNDEF func{n}")
            elif(operation == "CLL"):
                n = self.expect(("num",1))
                if printB:
                    print(f"FUNCCALL func{n}")
            elif(operation == "FOR"):
                self.blockdepth+=1
                self.blockslist.append("FOR")
                n = self.expect(("num",1), False)
                m = self.expect(("num",2))
                if printB:
                    print(f"FOR (reg{n}=1; reg{n}<={int(m, 16)}; reg{n}++)")
            elif(operation == "VFR"):
                self.blockdepth+=1
                self.blockslist.append("FOR")
                n = self.expect(("num",1), False)
                m = self.expect(("num",1))
                if printB:
                    print(f"FOR (reg{n}=1; reg{n}<=reg{m}; reg{n}++)")
            elif(operation == "WHL"):
                self.blockdepth+=1
                self.blockslist.append("WHILE")
                n = self.expect(("num",1))
                o = self.expect(["boolop"])
                m = self.expect(("num",1))
                if printB:
                    print(f"WHILE reg{n} {self.booloptable[o]} reg{m}")
            elif(operation == "PG1"):
                if printB:
                    print("PAGE 1")
            elif(operation == "PG2"):
                if printB:
                    print("PAGE 2")
            elif(operation == "PG3"):
                if printB:
                    print("PAGE 3")
            elif(operation == "PG4"):
                if printB:
                    print("PAGE 4")
            elif(operation == "PG5"):
                if printB:
                    print("PAGE 5")
            elif(operation == "PG6"):
                if printB:
                    print("PAGE 6")
            elif(operation == "PG7"):
                if printB:
                    print("PAGE 7")
            elif(operation == "PG8"):
                if printB:
                    print("PAGE 8")
            elif(operation == "PUS"):
                n = self.expect(("num", 1))
                if printB:
                    print(f"PUSH reg{n}")
            elif(operation == "POP"):
                n = self.expect(("num", 1))
                if printB:
                    print(f"POP to reg{n}")
            elif(operation == "IND"):
                n=self.expect(("num",1))
                if printB:
                    print(f"INPUT to reg{n} (dec)")
            elif(operation == "INH"):
                n=self.expect(("num",1))
                if printB:
                    print(f"INPUT to reg{n} (hex)")
            elif(operation == "EXE"):
                if printB:
                    print(f"EXIT (error)")
            elif(operation == "EXO"):
                if printB:
                    print(f"EXIT (no error)")
        if(self.blockdepth>0):
            if printB:
                    print(f"Unclosed block found, possibly a {self.blockslist.pop()}")
