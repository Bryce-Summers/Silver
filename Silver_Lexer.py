"""
Silver_Lexer

 - Converts a stream of characters from a file into a stream of tokens.

History:
 - Jan.16.2026: Adapted by Bryce Summers from another his
                compiler for Transcript reports.
"""

class Silver_Lexer:

    from enum import Enum

    # Start of File, End of File.
    Token = Enum('Token', [('Start', 1), ('End', 2)])

    def __init__(self, open_src_file):
        
        charStream = Silver_Lexer.charStream(open_src_file)
        self.char_list = [char for char in charStream]
        self.next_char_index = -1
        self.end_of_stream_index = len(self.char_list)

        self.match_index = 0
        self.matchFound = True
        self.token_type = None

        self.src_line_number           = 1
        self.src_index_of_last_newline = 0

    def charStream(src_file):

        # blank line is '\n', EOF is ""
        while (line := src_file.readline()) != "":
            for char in line:
                yield char

    def Accept(self, predicate):

        if not self.matchFound: 
            return False

        elif predicate(self.char_list[min(self.match_index, self.end_of_stream_index)]):
            self.match_index += 1
            return True

        else:
            return False

    def Expect(self, predicate):
        as_expected = self.Accept(predicate)
        if not as_expected:
            self.matchFound = False # Short-circuit remainder of calling function.
            return False
        return True

    def ExpectChar(self, char):
        return self.Expect(lambda c:c == char)

    def ExpectString(self, word):
        out = True
        for char in word:
            out = self.ExpectChar(char)
            if not out: return False # Short circuit.
        return out

    def startMatch(self):
        self.match_index = self.next_char_index
        self.matchFound  = True
        self.next_token  = None
        self.token_type = None

    def matchText(self):
        return "".join(self.char_list[self.next_char_index: self.match_index])


    def lookAhead(self, k = 1):
        return self.char_list[self.match_index + k - 1]

    # -----------------------------------------------------------------
    # The parser calls this function to lazily lex a stream of tokens.|
    # -----------------------------------------------------------------
    def nextToken(self):

        def current_char_number():
            return self.next_char_index - self.src_index_of_last_newline + 1

        char_number = current_char_number()

        newlineTokensInARow = 0

        self._calculateNextToken()

        # Don't distribute whitespace tokens to the parser.
        while self.token_type in ['ws', 'newline']:
            
            # Keep track of line numbers and column numbers for debugging.
            if self.token_type == 'newline':
                self.src_line_number += 1
                self.src_index_of_last_newline = self.next_char_index
                newlineTokensInARow += 1

            # Dispatch a token for multiple newlines in a row.
            if newlineTokensInARow == 2:
                self.token_type = "Multi_Newline"
                self.value = '\n\n'
                break

            char_number = current_char_number() # Calculated at a time before the token has been read.
            self._calculateNextToken()

        token = {'type':self.token_type, 'value':self.next_token,
                 'line_number': self.src_line_number, 'char_number': char_number}
        
        print(token)
        return token

    def _calculateNextToken (self):
        
        if self.next_char_index < 0:
            self.token_type = Silver_Lexer.Token.Start
            self.next_token = Silver_Lexer.Token.Start
            self.next_char_index += 1

            return

        if self.next_char_index >= self.end_of_stream_index:
            self.token_type = Silver_Lexer.Token.End
            self.next_token = Silver_Lexer.Token.End
            self.next_char_index += 1

            return  # End of file.

        if self.next_char_index > self.end_of_stream_index:
            raise Exception("LexerError: Reached end of file too soon.")

        self.next_token = None    
        self.anytoken() # Matches any valid token.

    # ================================================================
    # Matching - Defines all of the possible tokens that can be lexed.
    # ================================================================


    # Describes the order in which all possible tokens are tested.
    def anytoken(self):
        if self.newline() or\
           self.ws() or\
           self.syntaxSymbol() or\
           self.keyword() or\
           self.typename() or\
           self.variable_name() or\
           self.literal():
           self.next_char_index = self.match_index
           return # A token was lexed properly.

        raise Exception(f"LexerError: No prefix was matched for input:"
                       f"{"".join(self.char_list[self.next_char_index:])}"  )

    def newline(self):

        self.startMatch()

        self.Expect(lambda c: c == "\n")

        if self.matchFound:
            self.next_token = self.matchText()
            self.token_type = "newline"

        return self.matchFound 

    def ws(self):
        self.startMatch()

        whitespace = lambda c: c in list(" \t")
        self.Expect(whitespace)
        while self.Accept(whitespace): pass

        if self.matchFound:
            self.next_token = self.matchText()
            self.token_type = "ws"

        return self.matchFound

    def syntaxSymbol(self):
        self.startMatch()

        value = self.char_list[self.match_index]
        self.Expect(lambda c:c in list("()="))

        if self.matchFound:
            self.next_token = self.matchText()
            self.token_type = "Syntax Symbol"

            if value == ']': self.ignoreNumbers = True

        return self.matchFound

    def keyword(self):
    
        # Iteratively tests keyword matches,
        # Could possibly be sped up if it checked prefixes.
        # Or used a state machine.

        for word in ["print", "input", "declare"]:
            self.startMatch()
            self.ExpectString(word)

            # Typenames cannot contain letters or numbers after the keyword.
            if self.matchFound and not self.lookAhead(1).isalnum():
            
                self.next_token = self.matchText()
                self.token_type = "Keyword"

                return True

        return False

    def typename(self):

        # Iteratively tests keyword matches,
        # Could possibly be sped up if it checked prefixes.
        # Or used a state machine.

        for word in ["boolean", "char", "int", "float", "String"]:
            self.startMatch()
            self.ExpectString(word)

            # Typenames cannot contain letters or numbers after the keyword.
            if self.matchFound and not self.lookAhead(1).isalnum():

                self.next_token = self.matchText()
                self.token_type = "Type_Name"

                return True

        return False

    # variable_name = [a-zA-z][a-zA-z0-9]*
    def variable_name(self):
        self.startMatch()
        
        # First char must be a letter.
        self.Expect(lambda c: c.isalpha())

        if not self.matchFound:
            return False
        
        # Then fill in the rest with alpha or numeric.
        while self.lookAhead(1).isalnum():
            self.Expect(lambda c:True)

        self.next_token = self.matchText()
        self.token_type = "Variable_Name"
        return True

    # Returns true if it has matched any kind of literal.
    def literal(self):
        return self.string()  or self.char() or \
               self.boolean() or self.number()

    def string(self):
        
        self.startMatch()

        self.ExpectChar(quote := '"')
        while self.Accept(lambda c:c != quote): pass
        self.ExpectChar(quote)

        if not self.matchFound: return False
           
        token_text = self.matchText()

        self.next_token = str(token_text)
        self.token_type = "String" # String.

        return True

    def char(self):
        self.startMatch()

        self.ExpectChar(quote := "'")
        self.Expect(lambda c:c != quote)
        self.ExpectChar(quote)

        if not self.matchFound: return False

        token_text = self.matchText()

        self.next_token = str(token_text)
        self.token_type = "Char" # Char.

        return True

    def boolean(self):
        
        self.startMatch()
        if self.ExpectString('True') :
            self.next_token = self.matchText() # "True"
            self.token_type = "Boolean"
            return True

        self.startMatch()
        if self.ExpectString('False'):
            self.next_token = self.matchText() # "False"
            self.token_type = "Boolean"
            return True

        return False

    def number(self):
        self.startMatch()

        # number = "'.' [0-9]+"
        if self.lookAhead(1) == '.':
            
            self.Expect(lambda c:c=='.')
            self.Expect(lambda c:c in "0123456789")
            while self.Accept(lambda c:c in "0123456789"): pass

        # number = "[0-9]+ ('.' [0-9]*)?""
        else:

            self.Expect(lambda c:c in "0123456789")
            while self.Accept(lambda c:c in "0123456789"): pass

            if self.lookAhead(1) == '.':
                self.Expect(lambda c:c=='.')
                while self.Accept(lambda c:c in "0123456789"): pass

        if self.matchFound:
            token_text = self.matchText()

            if '.' in token_text:
                self.next_token = float(token_text)
                self.token_type = "Int" # Int.
            else:
                #print(f"Token text: {token_text}")
                self.next_token = int(token_text)
                self.token_type = "Float" # Float.

        return self.matchFound