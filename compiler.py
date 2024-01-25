import sys
import re
import ply.yacc as yacc
from lexer import tokens

memory = 0
variables = {}
tables = {}
jumps = 0
initialized = {}
iterators = {}


# Tickets for instructions that could be simplifiable
def simple_():
    string = "simple\n"

    return string


# Memory management
# Number generator in machine code
def generate_number(number, register):
    string = ""
    while number > 0:
        if number % 2 == 0:
            string = "SHL " + register + "\n" + string
            number = number / 2
        else:
            string = "INC " + register + "\n" + string
            number = number - 1
    return "RESET " + register + "\n" + string


# Memory address loading
def load_variable_addres(variable, lineno):
    if variable[0] == "var":
        error_variable_declaration(variable[1], lineno)

        return "loadaddres" + str(variables[variable[1]]) + "\n" + \
            generate_number(variables[variable[1]], "a") + \
            "loadaddres\n"

    elif variable[0] == "tabnum":
        error_table_declaration(variable[1], lineno)

        position, begin, end = tables[variable[1]]
        index = int(variable[2])
        index = index - begin + position

        return "loadaddres" + str(index) + "\n" + \
            generate_number(index, "a") + \
            "loadaddres\n"

    else:
        error_table_declaration(variable[1], lineno)

        position, begin, end = tables[variable[1]]
        change = begin - position

        if change > 0:
            return generate_number(change, "c") + \
                load_variable(("var", variable[2]), "f", lineno) + \
                "SUB f c" + "\n"

        elif change < 0:
            return generate_number(-change, "c") + \
                load_variable(("var", variable[2]), "f", lineno) + \
                "ADD f c" + "\n"

        else:
            return load_variable(("var", variable[2]), "f", lineno)


def load_variable(variable, register, lineno):
    if variable[0] == "num":
        return generate_number(int(variable[1]), register)

    else:
        error_initialization(variable, lineno)

        if variable[0] == "tabvar":
            return load_variable_addres(variable, lineno) + \
                "LOAD " + register + " f" + "\n"
        else:
            return load_variable_addres(variable, lineno) + \
                "LOAD " + register + " a" + "\n"


# Adding tables to global dict
def add_table(name, begin, end, lineno):
    error_table_values(name, begin, end, lineno)
    error_name_exists(name, lineno)

    global memory

    tables[name] = (memory + 1, begin, end)
    memory += end - begin + 1


# Adding variables to global dict
def add_variable(name, lineno):
    error_name_exists(name, lineno)

    global memory

    memory += 1
    variables[name] = memory


# Adding temporary variables to global dict
def add_tmp():
    global memory

    add_variable(str(memory + 1), None)

    initialized[str(memory)] = True

    return 'var', str(memory)


# Jump labels generator
def generate_jumps(x):
    global jumps
    To = []
    From = []

    for i in range(0, x):
        To.append("to" + str(jumps))
        From.append("from" + str(jumps))
        jumps += 1

    return To, From


# Jump labels handler / post-compile optimization
def decode(code):
    line_id = 0
    without_to = ""
    without_from = ""
    without_simple = ""
    without_simple_o = ""
    global jumps
    list = [0] * jumps

    splited = code.split("\n")
    table = []
    loop_id = -1
    table_id = -1
    splits_count = 0
    simple_first = 0
    comple_first = 0

    badaddres_count = 0

    for line in splited:
        loop_id += 1

        if loop_id != len(splited):

            match = re.search("simple", line)
            if match or simple_first == 1:
                if simple_first == 0:
                    simple_first = 1
                    comple_first = 0
                    table.append("")
                    table_id += 1
                if match:
                    splits_count += 1
                    if splits_count % 2 == 0:
                        match = re.search("simple", splited[loop_id + 1])
                        if not match:
                            simple_first = 0

                table[table_id] += line + "\n"
            else:
                if comple_first == 0:
                    comple_first = 1
                    table.append("")
                    table_id += 1

                table[table_id] += line + "\n"

    for cell in table:
        skip = 0
        last_number = -1
        now_number = -1
        optimize = 0
        overwrite = 0
        loadaddres_count = 0

        optimized = cell.split("\n")

        match = re.search("simple", optimized[0])

        if match:

            for line in optimized[0:-1]:

                match = re.search("loadbadaddres", line)

                if match:
                    if skip == 0:
                        skip = 1
                        last_number = -1
                    else:
                        skip = 0
                        last_number = -1

                    without_simple += line + "\n"
                elif skip == 0:
                    if last_number >= 0:
                        match = re.search("loadaddres[0-9]+", line)
                        if match:
                            optimize = 1
                            now_number = int(re.sub("loadaddres", "", match.group(0)))
                            overwrite = 0

                        if optimize == 1:

                            match = re.search("loadaddres", line)
                            if match:
                                loadaddres_count += 1
                                if loadaddres_count % 2 == 0:
                                    last_number = now_number
                                    optimize = 0
                                without_simple += line + "\n"

                            else:
                                if abs(last_number - now_number) <= 2 and overwrite == 0:
                                    overwrite = 1
                                    if last_number - now_number == 1:
                                        without_simple += "DEC a\n"
                                    elif last_number - now_number == -1:
                                        without_simple += "INC a\n"
                                    elif last_number - now_number == -2:
                                        without_simple += "INC a\n" + "INC a\n"
                                    elif last_number - now_number == 2:
                                        without_simple += "DEC a\n" + "DEC a\n"
                                    elif last_number - now_number == -3:
                                        without_simple += "INC a\n" + "INC a\n" + "INC a\n"
                                    elif last_number - now_number == 3:
                                        without_simple += "DEC a\n" + "DEC a\n" + "DEC a\n"
                                    elif last_number - now_number == -4:
                                        without_simple += "INC a\n" + "INC a\n" + "INC a\n" + "INC a\n"
                                    elif last_number - now_number == 4:
                                        without_simple += "DEC a\n" + "DEC a\n" + "DEC a\n" + "DEC a\n"
                                else:
                                    if not (abs(last_number - now_number) <= 2):
                                        without_simple += line + "\n"


                        else:
                            without_simple += line + "\n"


                    else:
                        match = re.search("loadaddres[0-9]+", line)
                        if match:
                            last_number = int(re.sub("loadaddres", "", match.group(0)))
                        without_simple += line + "\n"
                else:
                    without_simple += line + "\n"


        else:
            for line in optimized[0:-1]:
                without_simple += line + "\n"

    for line in without_simple.split("\n"):

        if line != "":
            match = re.search("simple", line)
            if match:
                without_simple_o += re.sub("simple", "", line)
            else:
                match = re.search("loadaddres[0-9]*", line)
                if match:
                    without_simple_o += re.sub("loadaddres[0-9]*", "", line)
                else:
                    match = re.search("loadbadaddres", line)
                    if match:
                        without_simple_o += re.sub("loadbadaddres", "", line)
                    else:
                        without_simple_o += line + "\n"

    # print(without_simple_o)

    # for i in table:
    #	print("------------------------------------")
    #	print(i)
    #	print("------------------------------------")

    for line in without_simple_o.split("\n"):
        match = re.search("to[0-9]+to[0-9]+", line)

        if match:
            tab = match.group(0).split("to")
            list[int(tab[1])] = line_id
            list[int(tab[2])] = line_id
            line = re.sub("to[0-9]+to[0-9]+", "", line)

        else:
            match = re.search("to[0-9]+", line)
            if match:
                tab = match.group(0).split("to")
                list[int(tab[1])] = line_id
                line = re.sub("to[0-9]+", "", line)

        if line != "":
            without_to = without_to + line + "\n"
        line_id += 1

    line_id = 0

    for line in without_to.split("\n"):
        match = re.search("from[0-9]+", line)

        if match:
            fromm = int(re.sub("from", "", match.group(0)))
            jump_line = str(list[fromm] - line_id)
            line = re.sub("from[0-9]+", jump_line, line)

        if line != "":
            without_from = without_from + line + "\n"
        line_id += 1

    return without_from


# Program
def p_program(p):
    '''program : DECLARE declarations BEGIN commands END'''
    p[0] = decode(p[4]) + "HALT"


# Program without any declarations
def p_program_none_declarations(p):
    '''program : BEGIN commands END'''

    p[0] = decode(p[2]) + "HALT"


# Variable declaration
def p_declarations_variables(p):
    '''declarations	: declarations COMMA PIDENTIFIER'''

    id = p[3]

    add_variable(id, str(p.lineno(3)))


# Table declaration
def p_declarations_tables(p):
    '''declarations	: declarations COMMA PIDENTIFIER L NUM COLON NUM R'''

    id, start, stop = p[3], p[5], p[7]

    add_table(id, start, stop, str(p.lineno(3)))


# First variable declaration
def p_declarations_variable(p):
    '''declarations	: PIDENTIFIER'''

    id = p[1]

    add_variable(id, str(p.lineno(1)))


# First table declaration
def p_declarations_table(p):
    '''declarations	: PIDENTIFIER L NUM COLON NUM R'''

    id, start, stop = p[1], p[3], p[5]

    add_table(id, start, stop, str(p.lineno(1)))


# Command composition
def p_commands_command(p):
    '''commands : commands command'''
    p[0] = p[1] + p[2]


# Single command
def p_commands(p):
    '''commands : command'''
    p[0] = p[1]


# Assignments
def p_command_variable_assign(p):
    '''command : identifier ASSIGN expression SEMICOLON'''

    identifier = p[1]

    error_iterator_manipulation(identifier[1], str(p.lineno(1)))

    simp = simple_()

    if identifier[0] == "tabvar":
        p[0] = simp + \
               p[3] + \
               load_variable_addres(identifier, str(p.lineno(1))) + \
               "STORE b f\n" + \
               simp
    else:
        p[0] = simp + \
               p[3] + \
               load_variable_addres(identifier, str(p.lineno(1))) + \
               "STORE b a\n" + \
               simp

    initialized[identifier[1]] = True


# If else conditions
def p_command_else(p):
    '''command : IF condition THEN commands ELSE commands ENDIF'''

    condition = p[2]

    To, From = generate_jumps(1)

    simp = simple_()

    p[0] = simp + \
           condition[0] + \
           simp + \
           p[4] + \
           "JUMP " + From[0] + "\n" + \
           condition[1] + \
           p[6] + \
           "loadbadaddres\n" + \
           "loadbadaddres\n" + \
           To[0] + \
           "loadbadaddres\n" + \
           "loadbadaddres\n"


# If condition
def p_command_if(p):
    '''command : IF condition THEN commands ENDIF'''

    condition = p[2]

    simp = simple_()

    p[0] = simp + \
           condition[0] + \
           simp + \
           p[4] + \
           "loadbadaddres\n" + \
           "loadbadaddres\n" + \
           condition[1] + \
           "loadbadaddres\n" + \
           "loadbadaddres\n"


# While loop
def p_command_while(p):
    '''command : WHILE condition DO commands ENDWHILE'''

    To, From = generate_jumps(1)

    simp = simple_()

    condition = p[2]

    p[0] = To[0] + \
           "loadbadaddres\n" + \
           "loadbadaddres\n" + \
           simp + \
           condition[0] + \
           simp + \
           p[4] + \
           "JUMP " + From[0] + "\n" + \
           condition[1]


# Until loop
def p_command_until(p):
    '''command : REPEAT commands UNTIL condition SEMICOLON'''

    condition = p[4]

    simp = simple_()

    p[0] = "loadbadaddres\n" + \
           "loadbadaddres\n" + \
           condition[1] + \
           "loadbadaddres\n" + \
           "loadbadaddres\n" + \
           p[2] + \
           simp + \
           condition[0] + \
           simp


# Iterator implementation
def p_iterator(p):
    '''iterator : PIDENTIFIER'''

    p[0] = ("var", p[1])

    add_variable(p[1], str(p.lineno(1)))

    initialized[p[1]] = True
    iterators[p[1]] = True


# For loop
def p_command_for_to(p):
    '''command : FOR iterator FROM value TO value DO commands ENDFOR'''

    To, From = generate_jumps(5)

    tmp = add_tmp()

    iterator, start, stop, commands = p[2], p[4], p[6], p[8]

    error_loop_initials(iterator[1], start, stop, str(p.lineno(4)), str(p.lineno(6)))

    simp = simple_()

    p[0] = simp + \
           load_variable(start, "b", str(p.lineno(4))) + \
           load_variable(stop, "c", str(p.lineno(6))) + \
           load_variable_addres(tmp, str(p.lineno(6))) + \
           "STORE c a\n" + \
           load_variable_addres(iterator, str(p.lineno(2))) + \
           simp + \
           "STORE b a\n" + \
           "SUB b c\n" + \
           "JZERO b " + From[1] + "\n" + \
           "JUMP " + From[2] + "\n" + \
           To[4] + \
           "RESET d\n" + \
           "ADD d c\n" + \
           "SUB c b\n" + \
           "JZERO c " + From[3] + "\n" + \
           "JUMP " + From[2] + "\n" + \
           To[3] + \
           "STORE d a\n" + \
           To[1] + commands + \
           simp + \
           load_variable(tmp, "b", str(p.lineno(6))) + \
           load_variable(iterator, "c", str(p.lineno(2))) + \
           simp + \
           "INC c\n" + \
           "JUMP " + From[4] + "\n" + \
           To[2]

    variables.pop(iterator[1])


# Reversed for loop
def p_command_for_downto(p):
    '''command : FOR iterator FROM value DOWNTO value DO commands ENDFOR'''

    To, From = generate_jumps(5)
    tmp = add_tmp()

    iterator, start, stop, commands = p[2], p[4], p[6], p[8]

    error_loop_initials(iterator[1], start, stop, str(p.lineno(4)), str(p.lineno(6)))

    simp = simple_()

    p[0] = simp + \
           load_variable(stop, "b", str(p.lineno(6))) + \
           load_variable(start, "c", str(p.lineno(4))) + \
           load_variable_addres(tmp, str(p.lineno(6))) + \
           "STORE b a\n" + \
           load_variable_addres(iterator, str(p.lineno(2))) + \
           simp + \
           "STORE c a\n" + \
           "SUB b c\n" + \
           "JZERO b " + From[1] + "\n" + \
           "JUMP " + From[2] + "\n" + \
           To[4] + \
           "SUB b c\n" + \
           "JZERO b " + From[3] + "\n" + \
           "JUMP " + From[2] + "\n" + \
           To[3] + \
           "STORE c a\n" + \
           To[1] + commands + \
           simp + \
           load_variable(tmp, "b", str(p.lineno(6))) + \
           load_variable(iterator, "c", str(p.lineno(2))) + \
           simp + \
           "JZERO c " + From[2] + "\n" + \
           "DEC c\n" + \
           "JUMP " + From[4] + "\n" + \
           To[2]

    variables.pop(iterator[1])


# Input
def p_command_read(p):
    '''command : READ identifier SEMICOLON'''
    identifier = p[2]

    error_iterator_manipulation(identifier[1], str(p.lineno(2)))

    simp = simple_()

    if identifier[0] == "tabvar":
        p[0] = simp + \
               load_variable_addres(p[2], str(p.lineno(2))) + \
               "GET f\n" + \
               simp
    else:
        p[0] = simp + \
               load_variable_addres(p[2], str(p.lineno(2))) + \
               "GET a\n" + \
               simp

    initialized[identifier[1]] = True


# Output
def p_command_write(p):
    '''command : WRITE value SEMICOLON'''
    value = p[2]

    simp = simple_()

    if value[0] == "num":
        p[0] = simp + \
               load_variable(value, "b", str(p.lineno(2))) + \
               "RESET c\n" + \
               "STORE b c\n" + \
               "PUT c\n" + \
               simp
    else:
        error_initialization(value, str(p.lineno(2)))

        if value[0] == "tabvar":
            p[0] = simp + \
                   load_variable_addres(value, str(p.lineno(2))) + \
                   "PUT f\n" + \
                   simp
        else:
            p[0] = simp + \
                   load_variable_addres(value, str(p.lineno(2))) + \
                   "PUT a\n" + \
                   simp


# Value
def p_expression_value(p):
    '''expression : value'''
    p[0] = load_variable(p[1], "b", str(p.lineno(1)))


# Adding
def p_expression_plu(p):
    '''expression : value PLU value'''
    if p[3][0] == "num" and p[3][1] == 1:
        p[0] = load_variable(p[1], "b", str(p.lineno(1))) + \
               "INC b\n"

    elif p[1][0] == "num" and p[1][1] == 1:
        p[0] = load_variable(p[3], "b", str(p.lineno(3))) + \
               "INC b\n"
    else:
        p[0] = load_variable(p[1], "b", str(p.lineno(1))) + \
               load_variable(p[3], "c", str(p.lineno(3))) + \
               "ADD b c\n"

# Subtraction
def p_expression_min(p):
    '''expression : value MIN value'''
    if p[3][0] == "num" and p[3][1] == 1:
        p[0] = load_variable(p[1], "b", str(p.lineno(1))) + \
               "DEC b\n"
    else:
        p[0] = load_variable(p[1], "b", str(p.lineno(1))) + \
               load_variable(p[3], "c", str(p.lineno(3))) + \
               "SUB b c\n"


# Multiplication
def p_expression_mul(p):
    '''expression : value MUL value'''

    To, From = generate_jumps(9)

    if p[1][0] == "num" and p[1][1] == 2:
        p[0] = load_variable(p[3], "b", str(p.lineno(3))) + \
               "SHL b\n"

    elif p[3][0] == "num" and p[3][1] == 2:
        p[0] = load_variable(p[1], "b", str(p.lineno(1))) + \
               "SHL b\n"
    else:
        p[0] = load_variable(p[1], "b", str(p.lineno(1))) + \
               load_variable(p[3], "c", str(p.lineno(3))) + \
               "RESET d\n" + \
               "ADD d c\n" + \
               "SUB d b\n" + \
               "JZERO d " + From[8] + "\n" + \
               "RESET d\n" + \
               To[3] + "JZERO b " + From[0] + "\n" + \
               "JODD b " + From[1] + "\n" + \
               "JUMP " + From[2] + "\n" + \
               To[1] + "ADD d c\n" + \
               To[2] + "SHR b\n" + \
               "SHL c\n" + \
               "JUMP " + From[3] + "\n" + \
               To[8] + To[7] + "JZERO c " + From[4] + "\n" + \
               "JODD c " + From[5] + "\n" + \
               "JUMP " + From[6] + "\n" + \
               To[5] + "ADD d b\n" + \
               To[6] + "SHR c\n" + \
               "SHL b\n" + \
               "JUMP " + From[7] + "\n" + \
               To[4] + "RESET b\n" + \
               To[0] + "ADD b d\n"


# Division
def p_expression_div(p):
    '''expression : value DIV value'''
    To, From = generate_jumps(7)

    if p[1][0] == "var" and p[1][0] == p[3][0] and p[1][1] == p[3][1]:
        p[0] = "RESET b\n" + \
               "INC b\n"

    elif p[3][0] == "num" and p[3][1] == 2:
        p[0] = load_variable(p[1], "b", str(p.lineno(1))) + \
               "SHR b\n"
    else:

        p[0] = load_variable(p[1], "b", str(p.lineno(1))) + \
               load_variable(p[3], "c", str(p.lineno(3))) + \
               "JZERO c " + From[0] + "\n" + \
               "RESET d\n" + \
               "INC d\n" + \
               To[2] + "RESET f\n" + \
               "ADD f b\n" + \
               "SUB f c\n" + \
               "JZERO f " + From[1] + "\n" + \
               "SHL d\n" + \
               "SHL c\n" + \
               "JUMP " + From[2] + "\n" + \
               To[1] + "RESET e\n" + \
               "ADD e b\n" + \
               "RESET b\n" + \
               To[6] + "RESET f\n" + \
               "ADD f c\n" + \
               "SUB f e\n" + \
               "JZERO f " + From[3] + "\n" + \
               "JUMP " + From[4] + "\n" + \
               To[3] + "SUB e c\n" + \
               "ADD b d\n" + \
               To[4] + "SHR c\n" + \
               "SHR d\n" + \
               "JZERO d " + From[5] + "\n" + \
               "JUMP " + From[6] + "\n" + \
               To[0] + "RESET b\n" + \
               To[5]


# Modulo
def p_expression_mod(p):
    '''expression : value MOD value'''

    To, From = generate_jumps(8)

    if p[1][0] == "var" and p[1][0] == p[3][0] and p[1][1] == p[3][1]:
        p[0] = "RESET b\n"

    elif p[3][0] == "num" and p[3][1] == 2:
        p[0] = load_variable(p[1], "c", str(p.lineno(1))) + \
               "RESET b\n" + \
               "JODD c" + From[0] + "\n" + \
               "JUMP " + From[1] + "\n" + \
               To[0] + "INC b\n" + \
               To[1]
    else:

        p[0] = load_variable(p[1], "b", str(p.lineno(1))) + \
               load_variable(p[3], "c", str(p.lineno(3))) + \
               "JZERO c " + From[0] + "\n" + \
               "RESET d\n" + \
               "INC d\n" + \
               To[2] + "RESET f\n" + \
               "ADD f b\n" + \
               "SUB f c\n" + \
               "JZERO f " + From[1] + "\n" + \
               "SHL d\n" + \
               "SHL c\n" + \
               "JUMP " + From[2] + "\n" + \
               To[1] + "RESET e\n" + \
               "ADD e b\n" + \
               "RESET b\n" + \
               To[6] + "RESET f\n" + \
               "ADD f c\n" + \
               "SUB f e\n" + \
               "JZERO f " + From[3] + "\n" + \
               "JUMP " + From[4] + "\n" + \
               To[3] + "SUB e c\n" + \
               "ADD b d\n" + \
               To[4] + "SHR c\n" + \
               "SHR d\n" + \
               "JZERO d " + From[5] + "\n" + \
               "JUMP " + From[6] + "\n" + \
               To[0] + "RESET b\n" + \
               "JUMP " + From[7] + "\n" + \
               To[5] + "RESET b\n" + \
               "ADD b e\n" + \
               To[7]


# Equality comparison
def p_condition_equals(p):
    '''condition : value EQ value'''

    To, From = generate_jumps(3)

    p[0] = (load_variable(p[1], "b", str(p.lineno(1))) + \
            load_variable(p[3], "c", str(p.lineno(3))) + \
            "RESET d\n" + \
            "ADD d b\n" + \
            "SUB d c\n" + \
            "JZERO d " + From[0] + "\n" + \
            "JUMP " + From[1] + "\n" + \
            To[0] + "SUB c b\n" + \
            "JZERO c " + From[2] + "\n" + \
            "JUMP " + From[1] + "\n" + \
            To[2],
            To[1])


# Not equal comparison
def p_condition_nequals(p):
    '''condition : value NEQ value'''

    To, From = generate_jumps(3)

    p[0] = (load_variable(p[1], "b", str(p.lineno(1))) + \
            load_variable(p[3], "c", str(p.lineno(3))) + \
            "RESET d\n" + \
            "ADD d b\n" + \
            "SUB d c\n" + \
            "JZERO d " + From[0] + "\n" + \
            "JUMP " + From[1] + "\n" + \
            To[0] + "SUB c b\n" + \
            "JZERO c " + From[2] + "\n" + \
            To[1],
            To[2])


# Less than comparison
def p_condition_lessthen(p):
    '''condition : value LT value'''

    To, From = generate_jumps(1)

    p[0] = (load_variable(p[1], "b", str(p.lineno(1))) + \
            load_variable(p[3], "c", str(p.lineno(3))) + \
            "SUB c b\n" + \
            "JZERO c " + From[0] + "\n",
            To[0])


# Greater than comparison
def p_condition_greaterthen(p):
    '''condition : value GT value'''

    To, From = generate_jumps(1)

    p[0] = (load_variable(p[1], "b", str(p.lineno(1))) + \
            load_variable(p[3], "c", str(p.lineno(3))) + \
            "SUB b c\n" + \
            "JZERO b " + From[0] + "\n",
            To[0])


# Less than or equal comparison
def p_condition_lesse(p):
    '''condition : value LEQ value'''

    To, From = generate_jumps(2)

    p[0] = (load_variable(p[1], "b", str(p.lineno(1))) + \
            load_variable(p[3], "c", str(p.lineno(3))) + \
            "SUB b c\n" + \
            "JZERO b " + From[0] + "\n" + \
            "JUMP " + From[1] + "\n" + \
            To[0],
            To[1])


# Greater than or equal comparison
def p_condition_greatere(p):
    '''condition : value GEQ value'''

    To, From = generate_jumps(2)

    p[0] = (load_variable(p[1], "b", str(p.lineno(1))) + \
            load_variable(p[3], "c", str(p.lineno(3))) + \
            "SUB c b\n" + \
            "JZERO c " + From[0] + "\n" + \
            "JUMP " + From[1] + "\n" + \
            To[0],
            To[1])


# Variables,constants,tables
def p_value_number(p):
    '''value : NUM'''

    p[0] = ("num", p[1])


def p_value_identifier(p):
    '''value : identifier'''

    p[0] = p[1]


def p_identifier_var(p):
    '''identifier : PIDENTIFIER'''

    p[0] = ("var", p[1])


def p_identifier_tabvar(p):
    '''identifier : PIDENTIFIER L PIDENTIFIER R'''

    p[0] = ("tabvar", p[1], p[3])


def p_identifier_tabnum(p):
    '''identifier : PIDENTIFIER L NUM R'''

    p[0] = ("tabnum", p[1], p[3])


# Error handling
def p_error(p):
    raise Exception("Błąd w linii " + str(p.lineno) + ": nierozpoznany napis: " + str(p.value))


def error_table_values(name, start, stop, lineno):
    if start > stop:
        raise Exception("Błąd w linii " + lineno + ": niewłaściwy zakres tablicy " + name)


def error_name_exists(name, lineno):
    if name in variables:
        raise Exception("Błąd w linii " + lineno + ": druga deklaracja " + name)
    if name in tables:
        raise Exception("Błąd w linii " + lineno + ": druga deklaracja " + name)


def error_variable_declaration(name, lineno):
    if name in tables:
        raise Exception("Błąd w linii " + lineno + ": niewłaściwe użycie zmiennej tablicowej " + name)

    if name not in variables:
        raise Exception("Błąd w linii " + lineno + ": niezadeklarowana zmienna " + name)


def error_table_declaration(name, lineno):
    if name in variables:
        raise Exception("Błąd w linii " + lineno + ": niewłaściwe użycie zmiennej " + name)

    if name not in tables:
        raise Exception("Błąd w linii " + lineno + ": niezadeklarowana zmienna tablicowa " + name)


def error_initialization(variable, lineno):
    if variable[0] == "var":
        if variable[1] not in initialized:
            raise Exception("Błąd w linii " + lineno + ": użycie niezainicjowanej zmiennej " + variable[1])


def error_loop_initials(iterator, start, stop, lineno1, lineno2):
    if start[0] == "var":
        if start[1] == iterator:
            raise Exception("Błąd w linii " + lineno1 + ": użycie niezadeklarowanej zmiennej " + start[
                1] + " o tej samej nazwie co iterator w zakresie petli ")
    if stop[0] == "var":
        if stop[1] == iterator:
            raise Exception("Błąd w linii " + lineno2 + ": użycie niezadeklarowanej zmiennej " + stop[
                1] + " o tej samej nazwie co iterator w zakresie petli ")


def error_iterator_manipulation(name, lineno):
    if name in iterators:
        raise Exception("Błąd w linii " + lineno + ": modyfikacja iteratora " + name + " w petli")


# Parsing
input = open(sys.argv[1], "r")
output = open(sys.argv[2], "w")
parser = yacc.yacc()

try:
    code = parser.parse(input.read(), tracking=True)
except Exception as e:
    print(e)
    exit()


# Machine code output
output.write(code)
