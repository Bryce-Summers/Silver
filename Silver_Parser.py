"""
Silver_Parser

 - Parses a stream of typed tokens and spits out Python Code.

History:
 - Jan.16.2026: Adapted by Bryce Summers from another his
                compiler for Transcript reports.
"""

import Silver_Lexer
from datetime import datetime

class Silver_Parser:

    """
    # GRAMMAR for Bryce Code.
    [EMPTY]
    """

    # Given open files that can be read or written to.
    # Creator of this Parser Object is responsible for closing those files.
    def __init__(self, open_src_file, open_dst_file):
        self.src_file = open_src_file
        self.dst_file = open_dst_file

        self.tokenStream = Silver_Lexer.Silver_Lexer(open_src_file)
        self.lookAheadBuffer = []
        self.symbol_table = [] # All declared symbols.   

    def write(self, str):
        self.dst_file.write(str)

    # k = 1: next token, k = 2: token after next token, etc.
    def lookAhead(self, k):

        while len(self.lookAheadBuffer) < k:
            self.lookAheadBuffer.append(self.tokenStream.nextToken())

        return self.lookAheadBuffer[k - 1]

    def checkLookAhead(self, k, expectedTokenType, expectedTokenValue):
        token = self.lookAhead(k)
        return (token['type' ] == expectedTokenType  or expectedTokenType  == None) and\
               (token['value'] == expectedTokenValue or expectedTokenValue == None)

    def consumeToken(self):
        
        # If lookAheadbufferIsEmpty
        if not self.lookAheadBuffer:
            self.lookAhead(1)

        # Linear Time Dequeue is ok when len(lookAheadBuffer) < small k.
        deqValue = self.lookAheadBuffer[0]
        # print("Consumed: ", deqValue)
        self.lookAheadBuffer.remove(deqValue)

        return deqValue


    # Consumes the next symbol, returns true if it is 
    def Expect(self, expectedTokenType, expectedTokenValue):
        
        next = self.consumeToken()

        if expectedTokenType != None and expectedTokenType != next['type']:
            self.Error(f'Type Error. Expected:[{expectedTokenType}],  Yours:[{next['type']}]')

        if expectedTokenValue != None and expectedTokenValue != next['value']:
            self.Error(f'Syntax Error. Expected:{expectedTokenValue},  Yours:[{next['value']}]')
        
        # Everything checked out.
        return True
        

    def Error(self, message):
        output = []
        for x in range(7):
            output.append(str(self.lookAhead(1 + x)))
        raise Exception(message + "\n" + "\n".join(output))

    def ExpectString(self, expectedString):

        for symbol in expectedString: self.Expect(symbol)

    def pushScope(self):
        self.symbol_table.append({})

    def popScope(self):
        self.symbol_table.pop()

    def symbolDefined(self, name):
        for table in self.symbol_table:
            if name in table:
                return True
        return False

    def declareSymbol(self, name, type):
        self.symbol_table[-1][name] = type

    # ======================================================
    # Everything before this are just helper functions.
    # Here is the parser, implemented via recursive descent.
    #
    # As of Jan.16.2026, No backtracking is used.
    # ======================================================

    # Side-Effect: conversion of src file is written to dst file.
    #              src file object is consumed and should be closed.
    # Returns True if and only if no errors were produced.
    def parseFile(self):
        
        self.pushScope()
        
        now  = datetime.now()
        time = f'{now.strftime("%B")[:3]}.{now.strftime("%d.%y")}'
        self.write(f"# Bryce Code File, generated on {time} from Silver_Parser.py\n")

        self.Bryce_Code_File()
        self.popScope()

    def Bryce_Code_File(self):
        
        self.Expect(Silver_Lexer.Silver_Lexer.Token.Start,
                    Silver_Lexer.Silver_Lexer.Token.Start)
        self.Statements()


    def Statements(self):
        
        while self.lookAhead(1)['type'] != Silver_Lexer.Silver_Lexer.Token.End:
            self.Statement()

        self.Expect(Silver_Lexer.Silver_Lexer.Token.End,
                    Silver_Lexer.Silver_Lexer.Token.End)

    def Statement(self):

        if self.checkLookAhead(1, 'Keyword', 'print'):
           self.Expect('Keyword', "print")
           self.write("print(") # Code.
           self.Expression()
           self.write(")")
        elif self.checkLookAhead(1, 'Keyword', 'input'):
            self.Input_Statement()

        # Declaration Statement.
        elif self.checkLookAhead(1, 'Type_Name', None) or\
             self.checkLookAhead(1, 'Keyword', "declare"):
            
            self.Declaration_Statement()

        # Assignment Statement.
        elif self.checkLookAhead(1, 'Variable_Name', None):
            value = self.lookAhead(1)['value']

            self.Expect('Variable_Name', value)
            self.write(value)
            self.Expect('Syntax Symbol', '=')
            self.write(' = ')
            self.Expression()

            if(not self.symbolDefined(value)):
                self.write(f" # Bryce Code Error: Variable {value} is undeclared.")
                #raise Exception(f"Variable {value} is undeclared.")
        else:
            self.Error("Parse Error: Not a statement.")

        self.write("\n")

    def Expression(self):
        if self.checkLookAhead(1, 'Keyword', 'input'):
            self.Input_Statement()

        elif self.checkLookAhead(1, 'Syntax Symbol', '('):
            self.Expect('Syntax Symbol', '(')
            self.Expression()
            self.Expect('Syntax Symbol', ')')

        elif self.checkLookAhead(1, 'Variable_Name', None):
            value = self.lookAhead(1)['value']
            self.Expect('Variable_Name', value)
            self.write(value)
            if(not self.symbolDefined(value)):
                self.write(f" #[Bryce Code Error: Variable {value} is undeclared]#")
        else:
            raise Exception("Parse Error: Not an expression.")

    def Input_Statement(self):
        self.Expect("Keyword", "input")
        if self.checkLookAhead(1, 'Syntax Symbol', '('):
            self.Expect("Syntax Symbol", '(')
            self.Expect("Syntax Symbol", ')')

        self.write("input()") # Code.

    
    def Declaration_Statement(self):

        if self.checkLookAhead(1, 'Keyword', "declare"):
            self.Expect("Keyword", "declare")

        type_value = self.lookAhead(1)['value']
        self.Expect("Type_Name", None)
        varname = self.lookAhead(1)['value']
        self.Expect("Variable_Name", None)
        self.declareSymbol(varname, type_value)

        type_constructor = {'char':'str', 'String':'str',\
            'int':'int', 'float':'float', 'boolean':'bool'}

        self.write(f"{varname} = {type_constructor[type_value]}() # Declaration of {varname} as a variable of type {type_value}.")
        return


    def number_literal(self):

        value = self.lookAhead(1)['value']
        self.Expect('Number', None)
        return value