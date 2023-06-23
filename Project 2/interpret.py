# Author: Baturov Illia (xbatur00)

import os
import re
import sys
import argparse
import xml.etree.ElementTree as xmltree

### CLASSES ###

class IPP_instruction:
    def __init__(self, order, opcode):
        self.order = order
        self.opcode = opcode
        self.arguments = []
    def new_argument(self, arg_type, arg_value):
        self.arguments.append( IPP_argument(arg_type, arg_value) )

class IPP_argument:
    def __init__(self, type, value):
        self.type = type
        self.value = value

### FRAMES ###

ipp_global_frame = {}
ipp_local_frames_stack = []
ipp_temporary_frame = {}
temporary_frame_is_defined = False

### REGEX ###

GF_var_regex = r'^GF@[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*$'
LF_var_regex = r'^LF@[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*$'
TF_var_regex = r'^TF@[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*$'
symbol_regex = r'^(var|int|bool|string|nil)$'
type_regex = r'^(int|string|bool)$'

### FUNCTIONS ###

# interpreter
def interpreter(instruction):

    # correct order
    global instruction_order
    if ( int(instruction.order) != instruction_order ):
        exit(32)

    # desired case
    case = instruction.opcode

    # all cases
    cases = {
        "MOVE": handle_case_move,
        "CREATEFRAME": handle_case_createframe,
        "PUSHFRAME": handle_case_pushframe,
        "POPFRAME": handle_case_popframe,
        "DEFVAR": handle_case_defvar,
        "CALL": handle_case_call,
        "RETURN": handle_case_return,
        "PUSHS": handle_case_pushs,
        "POPS": handle_case_pops,
        "ADD": handle_case_add,
        "SUB": handle_case_sub,
        "MUL": handle_case_mul,
        "IDIV": handle_case_idiv,
        "LT": handle_case_lt,
        "GT": handle_case_gt,
        "EQ": handle_case_eq,
        "AND": handle_case_and,
        "OR": handle_case_or,
        "NOT": handle_case_not,
        "INT2CHAR": handle_case_int2char,
        "STRI2INT": handle_case_stri2int,
        "READ": handle_case_read,
        "WRITE": handle_case_write,
        "CONCAT": handle_case_concat,
        "STRLEN": handle_case_strlen,
        "GETCHAR": handle_case_getchar,
        "SETCHAR": handle_case_setchar,
        "TYPE": handle_case_type,
        "LABEL": handle_case_label,
        "JUMP": handle_case_jump,
        "JUMPIFEQ": handle_case_jumpifeq,
        "JUMPIFNEQ": handle_case_jumpifneq,
        "EXIT": handle_case_exit,
        "DPRINT": handle_case_dprint,
        "BREAK": handle_case_break,
    }

    # check case
    if case in cases:
        cases[case](instruction)
    else:
        exit(53)

# return argument value - only for and symbols
def return_symbol_value(arg, arg_type):
    # symbol is var
    if arg_type == 'var':
        # global frame
        if ( bool( re.match(GF_var_regex, arg)) ):
            if arg in ipp_global_frame:
                return ipp_global_frame[arg]
            else:
                exit(54)
        # local frame
        elif ( bool( re.match(LF_var_regex, arg)) ):
            if len(ipp_local_frames_stack) == 0:
                exit(55)
            else:
                if arg in ipp_local_frames_stack[-1]:
                    return ipp_local_frames_stack[-1][arg]
                else:
                    exit(54)
        # temporary frame
        elif ( bool( re.match(TF_var_regex, arg)) ):
            if temporary_frame_is_defined:
                if arg in ipp_temporary_frame:
                    return ipp_temporary_frame[arg]
                else:
                    exit(54)
            else:
                exit(55)
        else:
            exit(53)
    # symbol is int, bool or string
    elif ( bool(re.match(r'^(int|bool)$', arg_type)) ):
        return arg
    elif arg_type == 'string':
        if arg is None:
        # Note: Empty string case
            return ""
        else:
            return arg
    # symbol is nil
    elif arg_type == 'nil':
        return ""
    # others
    else:
        exit(53)

def variable_value_assignment(variable, value):
    # global frame
    if ( bool(re.match(GF_var_regex, variable)) ):
        if variable in ipp_global_frame:
            ipp_global_frame[variable] = value
        else:
            exit(54)
    # local frame
    elif ( bool(re.match(LF_var_regex, variable)) ):
        if len(ipp_local_frames_stack) == 0:
            exit(55)
        else:
            if variable in ipp_local_frames_stack[-1]:
                ipp_local_frames_stack[-1][variable] = value
            else:
                exit(54)
    # temporary frame
    elif ( bool(re.match(TF_var_regex, variable)) ):
        if temporary_frame_is_defined:
            if variable in ipp_temporary_frame:
                ipp_temporary_frame[variable] = value
            else:
                exit(54)
        else:
            exit(55)
    # error
    else:
        exit(53)

def detect_type(value):
    if isinstance(value, int):
        return "int"
    elif value == "nil":
        return "nil"
    elif value in ["true", "false"]:
        return "bool"
    elif isinstance(value, str):
        return "string"

# case move (var) (symb)
def handle_case_move(instruction):
    # number of arguments is 2
    if len(instruction.arguments) != 2:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)

    # value assignment
    variable_value_assignment(var1, symb1)

# case createframe
def handle_case_createframe(instruction):
    # number of arguments is 0
    if len(instruction.arguments) != 0:
        exit(53)

    # create frame
    global temporary_frame_is_defined, ipp_temporary_frame
    if temporary_frame_is_defined == True:
        ipp_temporary_frame.clear()
    else:
        temporary_frame_is_defined = True

# case pushframe
def handle_case_pushframe(instruction):
    # number of arguments is 0
    if len(instruction.arguments) != 0:
        exit(53)

    # push frame
    global temporary_frame_is_defined, ipp_temporary_frame, ipp_local_frames_stack
    if temporary_frame_is_defined == False:
        exit(55)
    else:
        ipp_local_frames_stack.append(ipp_temporary_frame)
        ipp_temporary_frame.clear()
        temporary_frame_is_defined = False

# case popframe
def handle_case_popframe(instruction):
    # number of arguments is 0
    if len(instruction.arguments) != 0:
        exit(53)

    # pop frame
    global temporary_frame_is_defined, ipp_temporary_frame, ipp_local_frames_stack
    if len(ipp_local_frames_stack) == 0:
        exit(55)
    else:
        if temporary_frame_is_defined == True:
            ipp_temporary_frame.clear()
            ipp_temporary_frame = ipp_local_frames_stack.pop()
        else:
            temporary_frame_is_defined = True
            ipp_temporary_frame = ipp_local_frames_stack.pop()

# case defvar (var)
def handle_case_defvar(instruction):
    # number of arguments is 1
    if len(instruction.arguments) != 1:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value

    # frame definition
    # global frame
    if ( bool(re.match(GF_var_regex, var1)) ):
        if var1 in ipp_global_frame:
            exit(52)
        else:
            ipp_global_frame[var1] = ""
    # local frame
    elif ( bool(re.match(LF_var_regex, var1)) ):
        if len(ipp_local_frames_stack) == 0:
            exit(55)
        else:
            if var1 in ipp_local_frames_stack[-1]:
                exit(52)
            else:
                ipp_local_frames_stack[-1][var1] = ""
    # temporary frame
    elif ( bool(re.match(TF_var_regex, var1)) ):
        if temporary_frame_is_defined == False:
            exit(55)
        else:
            if var1 in ipp_temporary_frame:
                exit(52)
            else:
                ipp_temporary_frame[var1] = ""
    # error
    else:
        sys.exit(53)

# case call (label)
def handle_case_call(instruction):
    # number of arguments is 1
    if len(instruction.arguments) != 1:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'label':
        exit(53)

    # arguments
    label1 = instruction.arguments[0].value

    # instruction order
    global instruction_order

    # call stack
    ipp_calls.append(instruction_order+1)

    # jump on existing label in dictionary
    if label1 in ipp_labels:
        instruction_order = int(ipp_labels[label1])
    else:
        exit(52)

# case return
def handle_case_return(instruction):
    # number of arguments is 0
    if len(instruction.arguments) != 0:
        exit(53)

    # instruction order
    global instruction_order

    # jump on position
    if len(ipp_calls) == 0:
        exit(56)
    else:
        return_on = ipp_calls.pop()
        instruction_order = int(return_on)

# case pushs (symb)
def handle_case_pushs(instruction):
    # number of arguments is 1
    if len(instruction.arguments) != 1:
        exit(53)

    # correct type
    if not ( bool(re.match(symbol_regex, instruction.arguments[0].type)) ):
        exit(53)

    # arguments
    symb1 = return_symbol_value(instruction.arguments[0].value, instruction.arguments[0].type)

    # push on stack
    data_stack.append(symb1)

# case pops (var)
def handle_case_pops(instruction):
    # number of arguments is 1
    if len(instruction.arguments) != 1:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    if len(data_stack) == 0:
        exit(56)
    else:
        value = data_stack.pop()

    # value assignment
    variable_value_assignment(var1, value)

# case add (var1) (symb1) (symb2)
def handle_case_add(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # cast to integer
    try:
        symb1 = int(symb1)
        symb2 = int(symb2)
    except:
        exit(53)

    # add
    result = symb1 + symb2
    variable_value_assignment(var1, result)

# case sub (var1) (symb1) (symb2)
def handle_case_sub(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # cast to integer
    try:
        symb1 = int(symb1)
        symb2 = int(symb2)
    except:
        exit(53)

    # sub
    result = symb1 - symb2
    variable_value_assignment(var1, result)

# case mul (var1) (symb1) (symb2)
def handle_case_mul(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # cast to integer
    try:
        symb1 = int(symb1)
        symb2 = int(symb2)
    except:
        exit(53)

    # mul
    result = symb1 * symb2
    variable_value_assignment(var1, result)

# case idiv (var1) (symb1) (symb2)
def handle_case_idiv(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # cast to integer
    try:
        symb1 = int(symb1)
        symb2 = int(symb2)
    except:
        exit(53)

    # idiv
    try:
        result = symb1 / symb2
    except ZeroDivisionError:
        exit(57)
    variable_value_assignment(var1, result)

# case lt (var1) (symb1) (symb2)
def handle_case_lt(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # cast to integer
    try:
        symb1 = int(symb1)
        symb2 = int(symb2)
    except:
        exit(53)

    # symb1 is less than symb2
    if symb1 < symb2:
        result = "true"
    else:
        result = "false"
    variable_value_assignment(var1, result)

# case gt (var1) (symb1) (symb2)
def handle_case_gt(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # cast to integer
    try:
        symb1 = int(symb1)
        symb2 = int(symb2)
    except:
        exit(53)

    # symb1 is greater than symb2
    if symb1 > symb2:
        result = "true"
    else:
        result = "false"
    variable_value_assignment(var1, result)

# case eq (var1) (symb1) (symb2)
def handle_case_eq(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # cast to integer
    try:
        symb1 = int(symb1)
        symb2 = int(symb2)
    except:
        exit(53)

    # symb1 is greater than symb2
    if symb1 == symb2:
        result = "true"
    else:
        result = "false"
    variable_value_assignment(var1, result)

# case and (var1) (symb1) (symb2)
def handle_case_and(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    if detect_type(symb1) != "bool":
        exit(53)
    if detect_type(symb2) != "bool":
        exit(53)

    # symb1 and symb2
    if symb1 == "true" and symb2 == "false":
        result = "false"
    elif symb1 == "false" and symb2 == "true":
        result = "false"
    elif symb1 == "false" and symb2 == "false":
        result = "false"
    else:
        result = "true"
    variable_value_assignment(var1, result)

# case or (var1) (symb1) (symb2)
def handle_case_or(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    if detect_type(symb1) != "bool":
        exit(53)
    if detect_type(symb2) != "bool":
        exit(53)

    # symb1 or symb2
    if symb1 == "true" and symb2 == "false":
        result = "true"
    elif symb1 == "false" and symb2 == "true":
        result = "true"
    elif symb1 == "true" and symb2 == "true":
        result = "true"
    else:
        result = "false"
    variable_value_assignment(var1, result)

# case not (var1) (symb1)
def handle_case_not(instruction):
    # number of arguments is 2
    if len(instruction.arguments) != 2:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)

    if detect_type(symb1) != "bool":
        exit(53)

    # not symb1
    if symb1 == "true":
        result = "false"
    else:
        result = "true"
    variable_value_assignment(var1, result)

# case int2char (var1) (symb1)
def handle_case_int2char(instruction):
    # number of arguments is 2
    if len(instruction.arguments) != 2:
        exit(53)

    # correct typetry
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)

    # cast to int
    try:
        symb1 = int(symb1)
    except:
        exit(53)

    # cast to char
    try:
        result = chr(symb1)
    except:
        exit(53)
    variable_value_assignment(var1, result)

# case stri2int (var1) (symb1) (symb2)
def handle_case_stri2int(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # cast to str
    try:
        symb1 = str(symb1)
    except:
        exit(53)

    # cast to int
    try:
        symb2 = int(symb2)
    except:
        exit(53)
    if symb2 < 0 or symb2 >= len(symb1):
        exit(58)

    # stri2int
    char = symb1[symb2]
    result = ord(char)
    variable_value_assignment(var1, result)

# case read (var1) (type1)
def handle_case_read(instruction):
    # number of arguments is 2
    if len(instruction.arguments) != 2:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(type_regex, instruction.arguments[1].value)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    type1 = instruction.arguments[1].value

    # read stdin
    if program_args.input is None:
        data = input()
    else:
        with open(program_args.input, 'r') as input_file:
            sys.stdin = input_file
            while True:
                try:
                    data = input()
                except EOFError:
                    break
            sys.stdin = sys.__stdin__

    # cast
    try:
        if type1 == 'int':
            result = int(data)
        elif type1 == 'string':
            result = str(data)
        elif type1 == 'bool':
            result = bool(data)
        else:
            exit(57)
    except:
        exit(57)
    # result
    variable_value_assignment(var1, result)

# case write (symb)
def handle_case_write(instruction):
    # number of arguments is 1
    if len(instruction.arguments) != 1:
        exit(53)

    # correct type
    arg_type = instruction.arguments[0].type
    if not ( bool(re.match(symbol_regex, arg_type)) ):
        exit(53)

    # arguments
    symb1 = return_symbol_value(instruction.arguments[0].value, instruction.arguments[0].type)

    # print symbol
    replace_ascii_escape_and_print(symb1)

# escape sequences
def replace_ascii_escape_and_print(string):
    # cast to string
    try:
        string = str(string)
    except:
        exit(57)
    new_string = re.sub(r'\\[0-9]{3}', lambda match: chr(int(match.group(0)[1:])), string)
    print(new_string, end='')

# case concat (var) (symb) (symb)
def handle_case_concat(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # concat
    result = str(symb1) + str(symb2)
    variable_value_assignment(var1, result)

# case strlen (var1) (symb1)
def handle_case_strlen(instruction):
    # number of arguments is 2
    if len(instruction.arguments) != 2:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    
    if detect_type(symb1) != "string":
        exit(53)

    # cast to string
    try:
        symb1 = str(symb1)
    except:
        exit(57)

    # strlen
    result = len(symb1)
    variable_value_assignment(var1, result)

# case getchar (var) (symb) (symb)
def handle_case_getchar(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    # cast to str
    try:
        symb1 = str(symb1)
    except:
        exit(53)

    # cast to int
    try:
        symb2 = int(symb2)
    except:
        exit(53)
    if symb2 < 0 or symb2 >= len(symb1):
        exit(58)

    # getchar
    result = str(symb1[symb2])
    variable_value_assignment(var1, result)

# case setchar (var) (symb) (symb)
def handle_case_setchar(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    var1_value = return_symbol_value(instruction.arguments[0].value, instruction.arguments[0].type)
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    if detect_type(var1_value) != "string":
        exit(53)
    if detect_type(symb1) != "int":
        exit(53)
    if detect_type(symb2) != "string":
        exit(53)

    # cast to str
    try:
        string = str(var1_value)
        symb2 = str(symb2)
    except:
        exit(53)

    # cast to int
    try:
        symb1 = int(symb1)
    except:
        exit(53)
    if symb1 < 0 or symb1 >= len(string):
        exit(58)

    # setchar
    result = string[:symb1] + symb2[0] + string[symb1:]
    variable_value_assignment(var1, result)

# case type (var1) (symb1)
def handle_case_type(instruction):
    # number of arguments is 2
    if len(instruction.arguments) != 2:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'var':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)

    # arguments
    var1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)

    # type
    result = type(symb1)
    variable_value_assignment(var1, result)

# case label (label)
def handle_case_label(instruction):
    pass

# case jump (label)
def handle_case_jump(instruction):
    # number of arguments is 1
    if len(instruction.arguments) != 1:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'label':
        exit(53)

    # arguments
    label1 = instruction.arguments[0].value

    # instruction order
    global instruction_order

    # jump on existing label in dictionary
    if label1 in ipp_labels:
        instruction_order = int(ipp_labels[label1])
    else:
        exit(53)

# case jumpifeq (label) (symb) (symb)
def handle_case_jumpifeq(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'label':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)
    
    # arguments
    label1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    if detect_type(symb1) != detect_type(symb2):
        exit(53)

    # instruction order
    global instruction_order

    # jump on existing label in dictionary
    if label1 in ipp_labels:
        if symb1 == symb2:
            instruction_order = int(ipp_labels[label1])
    else:
        exit(52)

# case jumpifneq
def handle_case_jumpifneq(instruction):
    # number of arguments is 3
    if len(instruction.arguments) != 3:
        exit(53)

    # correct type
    if instruction.arguments[0].type != 'label':
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[1].type)) ):
        exit(53)
    if not ( bool(re.match(symbol_regex, instruction.arguments[2].type)) ):
        exit(53)
    
    # arguments
    label1 = instruction.arguments[0].value
    symb1 = return_symbol_value(instruction.arguments[1].value, instruction.arguments[1].type)
    symb2 = return_symbol_value(instruction.arguments[2].value, instruction.arguments[2].type)

    if detect_type(symb1) != detect_type(symb2):
        exit(53)

    # instruction order
    global instruction_order

    # jump on existing label in dictionary
    if label1 in ipp_labels:
        if symb1 != symb2:
            instruction_order = int(ipp_labels[label1])
    else:
        exit(52)

# case exit (symb)
def handle_case_exit(instruction):
    # number of arguments is 1
    if len(instruction.arguments) != 1:
        exit(53)

    # correct type
    arg_type = instruction.arguments[0].type
    if not ( bool(re.match(symbol_regex, arg_type)) ):
        exit(53)

    # arguments
    symb1 = return_symbol_value(instruction.arguments[0].value, instruction.arguments[0].type)

    # cast to int
    try:
        exit_code = int(symb1)
    except:
        exit(53)
    if exit_code < 0 or exit_code > 49:
        exit(57)

    # exit
    sys.exit(exit_code)

# case dprint (symb)
def handle_case_dprint(instruction):
    # number of arguments is 1
    if len(instruction.arguments) != 1:
        exit(53)

    # correct type
    arg_type = instruction.arguments[0].type
    if not ( bool(re.match(symbol_regex, arg_type)) ):
        exit(53)

    # arguments
    symb1 = return_symbol_value(instruction.arguments[0].value, instruction.arguments[0].type)

    # write to stderr
    sys.stderr.write(symb1)

# case break
def handle_case_break(instruction):
    # number of arguments is 0
    if len(instruction.arguments) != 0:
        exit(53)

    # write to stderr
    print("Code position:", instruction_order)
    print("Global frame:", ipp_global_frame)
    print("Local frame:", ipp_local_frames_stack)
    print("Temporary frame:", ipp_temporary_frame)

### ARGUMENT PARSING ###

# arguments of program
argument_parser = argparse.ArgumentParser()
argument_parser.add_argument('--source', metavar='file', help='Path to source file?')
argument_parser.add_argument('--input', metavar='file', help='Path to input file?')
program_args = argument_parser.parse_args()

# mandatory argument source or input
if not (program_args.source or program_args.input):
    argument_parser.error('No source file')

# source : file does not exist
if program_args.source and not os.path.isfile(program_args.source):
    argument_parser.error(f"Source: {program_args.source} does not exist")

# input : file does not exist
if program_args.input and not os.path.isfile(program_args.input):
    argument_parser.error(f"Input: {program_args.input} does not exist")

### LOADING XML FILE ###

# xml element tree
element_tree = xmltree.parse(program_args.source)

# root of the tree
tree_root = element_tree.getroot()

### XML CHECK ###

# root must be a program
if tree_root.tag != 'program':
    exit(31)

# childs of the root
for root_child in tree_root:

    # root child is instruction
    if root_child.tag != 'instruction':
        exit(31)

    # child_attrib[0] is order, child_attrib[1] is opcode
    child_attrib = list(root_child.attrib.keys())
    if child_attrib[0] != 'order' or child_attrib[1] != 'opcode':
        exit(31)

    # child_arg is arg[123]
    for child_arg in root_child:
        if not (re.match(r"arg[123]", child_arg.tag)):
            exit(31)

### XML TO INSTRUCTIONS ###

# stack
data_stack = []

# array of all instructions
ipp_instructions = []

# dictionary of all labels
ipp_labels = {} # value : insctruction_order
ipp_calls = [] # instruction_order

# instruction factory
for root_child in tree_root:

    # new instruction
    instruction = IPP_instruction(order=root_child.attrib['order'], opcode=root_child.attrib['opcode'])

    # instruction arguments
    for child_arg in root_child:
        if 'type' in child_arg.attrib:
            instruction.new_argument(child_arg.attrib['type'], child_arg.text)
        else:
            exit(57)

    # add instruction to array
    ipp_instructions.append(instruction)

### INTERPRETER ###

# ONLY LABELS
# order count
order_count = 1
for instruction in ipp_instructions:
    if instruction.opcode == 'LABEL':
        # correct order
        if ( int(instruction.order) != order_count ):
            exit(32)

        # number of arguments is 1
        if len(instruction.arguments) != 1:
            exit(53)

        # correct type
        if instruction.arguments[0].type != 'label':
            exit(53)

        # check if there's identical label
        if instruction.arguments[0].value in ipp_labels:
            exit(52)

        # adding label to dictionary, with order of instruction
        ipp_labels[instruction.arguments[0].value] = order_count
    # add 1 to order count
    order_count += 1

# ALL INSTRUCTIONS
# order of instruction
instruction_order = 1
# every index of instructions array
while instruction_order - 1 < len(ipp_instructions):
    interpreter(ipp_instructions[instruction_order - 1])
    instruction_order += 1

### EXIT ###
exit(0)
