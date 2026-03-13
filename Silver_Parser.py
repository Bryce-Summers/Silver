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

        char_stream       =  Silver_Lexer.charStream(open_src_file)
        self.tokenStreams = [Silver_Lexer.Silver_Lexer(char_stream)]

        self.lookAheadBuffer = []
        self.symbol_table = [] # All declared symbols. Stack.
        self.macro_definitions = {}
        self.warnings = {'count':0}
        self.linemap  = {'python_line':1}
        self.commentQueue = []

    def write(self, str):
        self.dst_file.write(str)

    def _nextToken(self):
        
        # Stack of token streams.
        # Always stream from the one on top first.
        # Pop from stack of size >= 2 if top stream gets to its end token.
        
        while(True):

            # Look at the next token from the top stream in the stack.
            token = self.tokenStreams[-1].nextToken()
            value = token['value']

            # Case 1: The token is a macro.
            if token['type' ] == 'Variable_Name' and\
               value in self.macro_definitions:

               definition_token = self.macro_definitions[value]

               definition_text = definition_token['value']
               line_number     = definition_token['line_number']
               column_number   = definition_token['char_number'] + 1 # Account for opening '"' quote.

               subStream  = Silver_Lexer.Silver_Lexer(definition_text, line_number, column_number)
               
               # Skip the sub stream's 
               # Silver_Lexer.Silver_Lexer.Token.Start token.
               subStream.nextToken()

               self.tokenStreams.append(subStream)
               continue

            # Case 2: The token is the end of a sub stream.
            if len(self.tokenStreams) > 1 and\
               value == Silver_Lexer.Silver_Lexer.Token.End:
               self.tokenStreams.pop()
               continue

            # Case 3: Comment
            if(token['type'] == 'comment'):
                self.commentQueue.append(value)
                continue

            # Case ?: We've received a normal token that should be parsed.
            return token


    # k = 1: next token, k = 2: token after next token, etc.
    def lookAhead(self, k):

        while len(self.lookAheadBuffer) < k:
            self.lookAheadBuffer.append(self._nextToken())

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


    # Consumes the next symbol, throws an error if token is unexpected.
    # Returns token if it is as expected.
    def Expect(self, expectedTokenType, expectedTokenValue):
        
        next = self.consumeToken()

        if expectedTokenValue != None:
            fix_it = f"replace [{next['value']}] with [{expectedTokenValue}]."
        elif expectedTokenType != None:
            fix_it = f"replace [{next['value']}] with a [{expectedTokenType}]."
        else:
            raise Exception("This should be impossible.")


        if expectedTokenValue != None and expectedTokenValue != next['value']:
            self.Error('Syntax Error', f"I saw [{next['value']}] in your code", fix_it, next)
        elif expectedTokenType != None and expectedTokenType != next['type']:
            self.Error('Type Error', f"I saw [{next['value']}] in your code, which is a {next['type']}", fix_it, next)
        
        self.linemap[self.linemap['python_line']] = next['line_number']

        # The token is as expected.
        return next

    # Specifies to consume this token if it comes next,
    # and to not consume it if it is not coming next.
    def Accept(self, expectedTokenType, expectedTokenValue):
        if self.checkLookAhead(1, expectedTokenType, expectedTokenValue):
            return self.Expect(expectedTokenType, expectedTokenValue)
        return None

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

    # Definition should be a string.
    def defineSymbol(self, name, definition_string_token):

        self.macro_definitions[name] = definition_string_token

        print(definition_string_token)
        definition = definition_string_token['value'][1:-1]
        print(f"Definition: {name} -> [{definition}]")

    # ==============================================================
    # Methods for providing the user with feedback on their program.
    def Error(self, kind_of_problem, what_is_wrong, advice_on_how_to_fix_it, token):
        """
        output = []
        for x in range(7):
            output.append(str(self.lookAhead(1 + x)))
        raise Exception(message + "\n" + "\n".join(output))
        """
        self.warn(kind_of_problem, what_is_wrong, advice_on_how_to_fix_it, token)
        print("\nGiving up on compilation.")
        exit()

    # keep going, its a warning, because we think we can fix the problem during compilation.
    # Warn reports, but doesn't crash the compiler.
    def warn (self, kind_of_problem, what_is_wrong, advice_on_how_to_fix_it, token):
        self.warnings['count'] += 1
        self.write(f" # [<- {what_is_wrong}. Try to {advice_on_how_to_fix_it}] ")
        self.report(kind_of_problem, what_is_wrong, advice_on_how_to_fix_it, token)

    # Report a problem to the user.
    def report(self, kind_of_problem, what_is_wrong, advice_on_how_to_fix_it, token):
        id = self.warnings['count']

        here = f"line {token['line_number']}, column {token['char_number']}"

        if id == 1 :
            print(f"\nHey there! I'm the silver compiler and I'm here to help you!\n"\
                  f"Here's some constructive feedback on your program:")
        print(f"\n{id}. At {here}, a {kind_of_problem} has occured.")
        print(f"I don't understand your code, because {what_is_wrong}.")
        print(f"To help me out, {advice_on_how_to_fix_it}")
        #if terminate: exit()

    def pythonToAgLineNumber(self, pythonLineNumber):
        return self.linemap[pythonLineNumber]


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

        self.write(f"# --------------------------------------------------------------\n")
        self.write(f"# Python Code File, generated on {time} from Silver_Parser.py\n")
        self.write(f"# Silver compiles .Ag program files. Written by Bryce Summers.\n")
        self.write(f"# --------------------------------------------------------------\n\n")

        self.Bryce_Code_File()
        self.popScope()

        return self.warnings['count']

    def Bryce_Code_File(self):
        
        self.Expect(Silver_Lexer.Silver_Lexer.Token.Start,
                    Silver_Lexer.Silver_Lexer.Token.Start)
        self.Statements()


    def Statements(self):
        
        while self.lookAhead(1)['type'] != Silver_Lexer.Silver_Lexer.Token.End:
            self.Statement()
            self.Accept('Syntax Symbol', ',') # Just ignore.
            self.Accept('Keyword', 'then')    # Just ignore.

        self.Expect(Silver_Lexer.Silver_Lexer.Token.End,
                    Silver_Lexer.Silver_Lexer.Token.End)

    def Statement(self):

        # Add an extra space to visually separate
        # Blocks of text in the output.
        if self.checkLookAhead(1, 'Multi_Newline', None):
            self.Expect('Multi_Newline', None)

        # Print statements.
        elif self.checkLookAhead(1, 'Keyword', 'print'):
           self.Expect('Keyword', "print")
           self.write("print(") # Code.
           self.Expression()
           self.write(")")

        # Input statements.
        elif self.checkLookAhead(1, 'Keyword', 'input'):
            self.Input_Statement()

        # Declaration Statement
        elif self.checkLookAhead(1, 'Keyword', "declare") or\
             self.checkLookAhead(1, "Type_Name", None):
            self.Declaration_Statement()

        elif self.checkLookAhead(1, 'Variable_Name', None):

            # Definition Statement.
            if self.checkLookAhead(2, 'Keyword', 'means'):
                self.Definition_Statement()
                return # Definitions don't generate code, so they don't
                       # produce newline chars.

            # Assignment Statement.
            else:
                self.Assignment_Statement()

        else:
            token = self.lookAhead(1)
            value = token['value']
            type  = token['type' ]
            #self.Error("Parse Error: Not a statement.")
            self.Error("Parse Error", f"The {type} token [{value}] is not the start of an Agnostic programming language statement", "write a statement that I can understand, such as print(input()), char x, or x = input().", token)

        self.comments()
        self.write("\n")
        self.linemap['python_line'] += 1 # Keep track of python line number.

    def Expression(self):
        if self.checkLookAhead(1, 'Keyword', 'input'):
            self.Input_Statement()

        elif self.checkLookAhead(1, 'Syntax Symbol', '('):
            self.Expect('Syntax Symbol', '(')
            self.Expression()
            self.Expect('Syntax Symbol', ')')

        elif self.checkLookAhead(1, 'Variable_Name', None):
            
            token   = self.lookAhead(1)
            varname = self.Lvalue()

            if(not self.symbolDefined(varname)):
                self.warn("Compile Error", f"The variable {varname} doesn't exist yet", f"declare the variable before using it in this expression.", token)
        
        elif self.checkLookAhead(1, Silver_Lexer.Silver_Lexer.Token.End, None):
            token = self.lookAhead(1)
            self.Error("Parse Error", f"I've reached the end of the file without seeing the end of your expression", "Please finish writing the end of your program.", token)

        else:
            token = self.lookAhead(1)
            value = token['value']
            type  = token['type']
            
            self.Error("Parse Error", f"The {type} token [{value}] is not the start of an Agnostic programming language expression", "write an expression that I can understand, such as input(), '(' expression ')', or a variable name. ", token)

            #raise Exception("Parse Error: Not an expression.")

    def Input_Statement(self):
        self.Expect("Keyword", "input")
        if self.checkLookAhead(1, 'Syntax Symbol', '('):
            self.Expect("Syntax Symbol", '(')
            self.Expect("Syntax Symbol", ')')

        self.write("input()") # Code.

    def Declaration_Statement(self):

        self.Accept("Keyword", "declare")
        type_value = self.Expect("Type_Name", None)['value']
        varname    = self.Expect("Variable_Name", None)['value']

        self.declareSymbol(varname, type_value)

        type_constructor = {'char':'str', 'String':'str',\
            'int':'int', 'float':'float', 'boolean':'bool'}

        self.write(f"{varname} = {type_constructor[type_value]}(")

        if self.checkLookAhead(1, "Syntax Symbol", '='):

            self.Expect('Syntax Symbol', '=')
            self.Expression()

        self.write(')')
        self.write(f" # Declaration of {varname} as a variable of type {type_value}.")
        
        return

    def Assignment_Statement(self):

        token   = self.lookAhead(1)
        varname = self.Lvalue()

        if(not self.symbolDefined(varname)):
            self.warn("Compile Error", f"I can't assign a value to the variable {varname} that doesn't yet exist",
                     f"declare {varname} by writing a typename before the variable name. Ex: char x = ..., rather than x = ...", token)

        self.Expect('Syntax Symbol', '=')
        self.write(' = ')
        self.Expression()

        return

    def Lvalue(self):

        varname = self.Expect('Variable_Name', None)['value']
        self.write(varname)
        return varname

    def Definition_Statement(self):

        varname = self.Expect('Variable_Name', None)['value']

        self.Expect('Keyword', 'means')

        definition_token = self.Expect('String', None)

        # Associate this varname with definition string of code.
        self.defineSymbol(varname, definition_token)

        # No code is generated here, this merely affects how
        # instances of the varname are lexed later in this parse.

        return

    def number_literal(self):

        return self.Expect('Number', None)['value']

    def comments(self):
        if len(self.commentQueue) > 0:
            self.write(f'#{", ".join(self.commentQueue)}')
            self.commentQueue = []