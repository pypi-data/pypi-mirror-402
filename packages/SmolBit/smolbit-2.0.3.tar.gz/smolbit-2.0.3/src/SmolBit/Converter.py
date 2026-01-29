codes_3 = {
    # ----- NOP -----
    'NOP': "000",

    # ----- Manipulation (001 mnip) -----
    'INC': "001000",   # increment
    'DEC': "001001",   # decrement
    'CLZ': "001010",   # clear to 0
    'CLI': "001011",   # clear to init
    'PUS': "001100",  # PUSH
    'POP': "001101",  # POP

    # ----- Page Select (010 int2) -----
    'PG1': "010000",   # page 0
    'PG2': "010001",   # page 1
    'PG3': "010010",   # page 2
    'PG4': "010011",   # page 3
    'PG5': "010100",
    'PG6': "010101",
    'PG7': "010110",
    'PG8': "010111",

    # ----- Arithmetic (011 armd) -----
    'ADD': "011000",  # add
    'SUB': "011001",  # sub
    'MUL': "011010",  # mul
    'DIV': "011011",  # div
    'SET': "011100",  # set A = B
    'LDI': "011101",  # set A = byte (no B)
    'POW': "011110",  # exponent
    'ROT': "011111",  # root

    # ----- Display (100 addr dpmd) -----
    'DPU': "10000",  # display utf8
    'DPD': "10001",  # display decimal
    'DPH': "10010",  # display hex
    'DPI': "10011",  # display utf8 (immediate)

    # ----- Block instructions (101 blok) -----
    'IF': "101000",  # IF
    'REP': "101001",  # REPEAT
    'DEF': "101010",  # FUNCTION DEF
    'UDF': "101011",  # UNDEF
    'CLL': "101100",  # CALL
    'FOR': "1011010",  # FOR
    'VFR': "1011011",
    'WHL': "101110",  # WHILE
    '   ': "101111",

    # ----- Block end -----
    ']': "110",

    # ----- IO (111 iocd) -----
    'EXO': "11100",   # exit ok
    'EXE': "11101",   # exit error
    'INH': "11110",   # await hex → next nibble = addr
    'IND': "11111",   # await decimal → next nibble = addr

    # ----- Nibbles (operands) -----
    '0': "0000",
    '1': "0001",
    '2': "0010",
    '3': "0011",
    '4': "0100",
    '5': "0101",
    '6': "0110",
    '7': "0111",
    '8': "1000",
    '9': "1001",
    'a': "1010",
    'b': "1011",
    'c': "1100",
    'd': "1101",
    'e': "1110",
    'f': "1111",

    # ----- 2-bit numbers -----
    '=':'00',
    '<':'01',
    '>':'10',
    '!':'11'
}

def binaryToBytes(binary:str):
    if("0b" in binary):
        binary = binary[2:]
    binary = "".join([b for b in binary if not b.isspace()])
    while len(binary) % 8 > 0:
        binary+="0"
    byte = int(binary, 2)
    byte = byte.to_bytes((len(binary) // 8), byteorder="big")
    return byte

def splitCode(bitcode:str):
    split = []
    bitcode = bitcode.replace("[", "").replace("(", "").replace(")", "")
    singles = "0123456789abcdef]=<>!"
    doubles = ["IF"]
    quotes = ['"', "'"]
    activeQuote = None
    skip=False
    quoteChars = ""
    skipL = 0
    for i, ch in enumerate(bitcode):
        if(ch == ";"):
            skip = not skip
            continue
        if(ch == activeQuote):
            activeQuote = None
            for char in quoteChars:
                split.append("DPI")
                split.extend(list(char.encode().hex()))
            continue
        if(activeQuote != None):
            quoteChars += ch
            continue
        if(skip):
            continue
        if(skipL):
            skipL-=1
            continue
        if ch.isspace():
            continue
        if ch in singles:
            split.append(ch)
        elif ch in quotes:
            if split[-1] != "DPI":
                raise ValueError("Unexpected quote")
            activeQuote = ch
            split.pop()
        elif bitcode[i:i+2] in doubles:
            split.append(bitcode[i:i+2])
            skipL = 1
        else:
            split.append(bitcode[i:i+3])
            skipL = 2
    if(skip):
        print("Unclosed comment: please ensure all comments are closed correctly and try again")
        return None
    return split

def convert(bitcode:str, file:str=False):
    bitcode = splitCode(bitcode.replace("[", "").replace("(", "").replace(")", ""))
    
    bits = ""
    for i, ch in enumerate(bitcode):

        if ch in codes_3:
            bits += codes_3[ch]
        else:
            print(f"COMPILATION ERROR: Illegal character '{ch}' found at position {i}")
            print(f"Context: ...{bitcode[max(0, i-5):i+5]}...")
            return None
    if(file):
        file = open(file, "wb")
        file.write(binaryToBytes(bits))
        file.close()
    return bits