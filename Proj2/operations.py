import re
from copy import deepcopy

from FrameHandle import FrameHandle
import sys

####
#
# This file contains all the used operations in single functions,
# some of them merged together (logical operations, etc...)
# with few helper functions used by mentioned operation functions
#
####

# returns index (from operation list) based on label name
def get_label_index(lst, name):
    for i, e in enumerate(lst):
        if e.attrib["opcode"] == "LABEL":
            arg_list = list(e)
            if arg_list[get_arg_index(arg_list, "arg1")].text == name:
                return i
    print("Label does not exist")
    exit(52)

# retrieving requested argument from operation (helper function for get_label_index)
def get_arg_index(lst, name):
    for i, e in enumerate(lst):
        if e.tag == name:
            return i
    print("Incorrect arg number")
    exit(32)

# replacing scape characters to ascii characters
def replace_escape(text):

    try:
        res = re.findall(r'\\[0-9][0-9][0-9]', text)

        # creates a list of tuples (original value, new value) for every escape chracter
        # and then replaces them inside given text
        res = list(map(lambda x: (x, chr(int(x[1:]))), res))
        for item in res:
            text = text.replace(item[0], item[1])
    except:
        print("Missing value")
        sys.exit(56)

    return text

# write operaion
# prints values based on the argument type passed to it or nil (VAR, NIL, SYMBOL)
def write_op(arg_list, frame_handle: FrameHandle):
    arg = parse_arg("arg1", arg_list, frame_handle)

    if arg[0] != "var":
        if arg[0] != "nil":
            text = replace_escape(arg[1])
            print(text, end='', flush=True)
        else:
            print("", end='', flush=True)
    else:
        _, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)
        # index 1 stores value of variable
        text = replace_escape(var[1])
        print(text, end='', flush=True)


# read operation
# checks trough every possible read values
# checks if input is available or prints nil
# this does not apply to bool and prints "false" instead
def read_op(arg_list, frame_handle: FrameHandle, input_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)
    arg2 = arg_list[get_arg_index(arg_list, "arg2")].text

    if input_list is None:
        try:
            read_input = input()
        except:
            FrameHandle.set_var_value(frame_handle, frame_type, var, "nil", "nil")
            return
    else:
        if len(input_list) > 0:
            read_input = input_list.pop(0)
        else:
            FrameHandle.set_var_value(frame_handle, frame_type, var, "nil", "nil")
            return

    if arg2 == "int":
        try:
            FrameHandle.set_var_value(frame_handle, frame_type, var, "int", int(read_input))
        except:
            FrameHandle.set_var_value(frame_handle, frame_type, var, "nil", "nil")
    elif arg2 == "string":
        FrameHandle.set_var_value(frame_handle, frame_type, var, "string", read_input)
    elif arg2 == "bool":
        if read_input.lower() == "true":
            FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
        else:
            FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")


# defvar operaion
# creates a new variable based on the frame and name passed in arg_list
def defvar_op(arg_list: list, frame_handle: FrameHandle):
    frame, var_name = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)
    FrameHandle.add_var_to_frame(frame_handle, frame, var_name)

# move operation
# simply finds two src and dst variable and moves the src one
def move_op(arg_list, frame_handle: FrameHandle):
    frame_type, var_name = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1

    FrameHandle.set_var_value(frame_handle, frame_type, var_name, arg2[0], arg2[1])

# exit operation
# checks if passed parameter is int and exits the application with defined value
def exit_op(arg_list, frame_handle: FrameHandle):
    arg1 = parse_arg("arg1", arg_list, frame_handle)  # symbol 1

    if arg1[0] is None:
        print("UnsetVal")
        sys.exit(56)
    if arg1[0] != "int":
        print("Incorrect type passed")
        sys.exit(53)

    err_val = int(arg1[1])

    if err_val < 0 or err_val > 49:
        print("Invalid exit code")
        sys.exit(57)
    else:
        sys.exit(err_val)

# label operation
# adds label to label list used in interpret.py
# checks for duplicates if it was not created before
def label_op(arg_list, distinct_label_names: list):
    arg = arg_list[get_arg_index(arg_list, "arg1")].text

    if arg in distinct_label_names:
        print("Duplicate label " + arg)
        sys.exit(52)

    distinct_label_names.append(arg)
    return distinct_label_names

# jump operation
# jumps to a passed label which is found in label list
# trough get_label_index funciton
def jump_op(arg_list, instruction_list):
    return get_label_index(instruction_list, arg_list[get_arg_index(arg_list, "arg1")].text)

# call operation
# calls a jump operation to a set label
def call_op(arg_list, labels: list, instruction_list, i):
    arg = arg_list[get_arg_index(arg_list, "arg1")].text
    labels.append((arg, i))
    return jump_op(arg_list, instruction_list), labels

# return operation
# pops the label it jumped at and returns back to the index it ended at
def return_op(labels: list):
    if len(labels) > 0:
        item = labels.pop()
        return item[1], labels
    else:
        exit(56)

#
# next operations (and, or, not, lt, gt, eq)
# work on a very similar principle
# where values are comapred based on their values (if types to match)
# if values are compared with nil they are false
#
def and_op(frame_handle: FrameHandle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    if arg2[0] == arg3[0] and arg2[0] == "bool":
        if arg2[1] == arg3[1] and arg2[1] == "true":
            FrameHandle.set_var_value(frame_handle, frame_type, var, arg2[0], "true")
        else:
            FrameHandle.set_var_value(frame_handle, frame_type, var, arg2[0], "false")
    else:
        if arg2[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Incorrect type passed")
            sys.exit(53)


def or_op(frame_handle: FrameHandle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    if arg2[0] == arg3[0] and arg2[0] == "bool":
        if arg2[1] == "true" or arg3[1] == "true":
            FrameHandle.set_var_value(frame_handle, frame_type, var, arg2[0], "true")
        else:
            FrameHandle.set_var_value(frame_handle, frame_type, var, arg2[0], "false")
    else:
        if arg2[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Incorrect type passed")
            sys.exit(53)


def not_op(frame_handle: FrameHandle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1

    if arg2[0] == "bool":
        if arg2[1] == "true":
            FrameHandle.set_var_value(frame_handle, frame_type, var, arg2[0], "false")
        else:
            FrameHandle.set_var_value(frame_handle, frame_type, var, arg2[0], "true")
    else:
        if arg2[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Incorrect type passed")
            sys.exit(53)


def lt_op(frame_handle: FrameHandle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    if arg2[0] == arg3[0] and arg2[0] is not None and arg3[0] is not None:
        if arg2[0] == "int":
            if int(arg2[1]) < int(arg3[1]):
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
            else:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        elif arg2[0] == "string":
            if replace_escape(str(arg2[1] or '')) < replace_escape(str(arg3[1] or '')):
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
            else:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        elif arg2[0] == "bool":
            if arg2[1] == "false" and arg3[1] == "true":
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
            else:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        else:
            print("Invalid type")
            sys.exit(53)
    else:
        if arg2[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Incorrect type")
            sys.exit(53)

def gt_op(frame_handle: FrameHandle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    if arg2[0] == arg3[0] and arg2[0] is not None and arg3[0] is not None:
        if arg2[0] == "int":
            if int(arg2[1]) > int(arg3[1]):
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
            else:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        elif arg2[0] == "string":
            if replace_escape(str(arg2[1] or '')) > replace_escape(str(arg3[1] or '')):
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
            else:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        elif arg2[0] == "bool":
            if arg2[1] == "true" and arg3[1] == "false":
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
            else:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        else:
            print("Invalid type")
            sys.exit(53)
    else:
        if arg2[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Incorrect type")
            sys.exit(53)

def eq_op(frame_handle: FrameHandle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    if arg2[0] == arg3[0]:
        if arg2[0] == "int":
            if int(arg2[1]) == int(arg3[1]):
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
            else:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        elif arg2[0] == "string":
            if replace_escape(str(arg2[1] or '')) == replace_escape(str(arg3[1] or '')):
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
            else:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        elif arg2[0] == "bool":
            if arg2[1] == arg3[1]:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
            else:
                FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        elif arg2[0] == "nil":
            FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "true")
        else:
            print("Incorrect type")
            sys.exit(53)
    else:
        if arg2[0] == "nil" or arg3[0] == "nil":
            FrameHandle.set_var_value(frame_handle, frame_type, var, "bool", "false")
        elif arg2[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Incorrect type")
            sys.exit(53)

# dprint operation
# print value stored in passed variable
def dprint_op(frame_handle: FrameHandle, arg_list):
    arg = parse_arg("arg1", arg_list, frame_handle)  # symbol
    print(arg[1], file = sys.stderr)

# int2char operation
# returns a chr representation of given int passed (which is stored as string)
# so it is firstly converted into int
def int2char_op(frame_handle: FrameHandle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1

    if arg2[0] is None:
        print("UnsetVal")
        sys.exit(56)
    if arg2[0] != "int":
        print("Arg3 is not int")
        sys.exit(53)

    try:
        int_val = int(arg2[1])
        char_val = chr(int_val)
    except:
        print("Not a UNICODE value")
        sys.exit(58)

    FrameHandle.set_var_value(frame_handle, frame_type, var, "string", char_val)


# string2int operation
#  sets a chr value in given string on the sepcified position
def stri2int_op(frame_handle: FrameHandle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1) # var
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    if arg3[0] == "int" and arg2[0] == "string":
        int_val = int(arg3[1])

        # checks if value is not outside of boundaries of length of given string
        if len(arg2[1]) - 1 >= int_val >= 0:
            FrameHandle.set_var_value(frame_handle, frame_type, var, "int", ord(arg2[1][int_val]))
        else:
            print("Index outside of array bounds")
            sys.exit(58)
    else:
        if arg2[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Arg3 is not int")
            sys.exit(53)

# pushframe operation
# pushes a TF into frame stack if it is not None (unitialised)
def pushframe_op(frame_handle: FrameHandle):
    if frame_handle.tmp_frame is not None:
        frame_handle.frame_stack.append(deepcopy(frame_handle.tmp_frame))
    else:
        print("Trying to push undefined TF")
        sys.exit(55)
    frame_handle.tmp_frame = None

# popframe operation
# pops a from out of frame stack if it exists (if stack is > 0)
def popframe_op(frame_handle: FrameHandle):
    if len(frame_handle.frame_stack) > 0:
        frame_handle.tmp_frame = frame_handle.frame_stack.pop()
    else:
        print("No LF on frame stack")
        sys.exit(55)

# createframe operation
def createframe_op(frame_handle: FrameHandle):
    frame_handle.tmp_frame = {}

# pushs operation
# saves a variable taht is defined into stack
def pushs_op(frame_handle: FrameHandle, arg_list):
    arg1 = parse_arg("arg1", arg_list, frame_handle)  # symbol 1

    if arg1[0] is None:
        print("UnsetVal")
        sys.exit(56)

    frame_handle.stack.append((arg1[0], arg1[1]))

# pops operation
# pops a value from var stack into currently used frame
def pops_op(frame_handle: FrameHandle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var

    if len(frame_handle.stack) > 0:
        stack_var = frame_handle.stack.pop()
        FrameHandle.set_var_value(frame_handle, frame_type, var, stack_var[0], stack_var[1])
    else:
        print("Nothing to pop")
        sys.exit(56)

    frame_handle.tmp_frame = {}

# function contains all of the supported arithmetic oeprations
def aritmethic_op(arg_list, frame_handle: FrameHandle, type_of_op):
    frame_type, value = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    # checks if both arguments are numbers
    if arg2[0] == arg3[0] and arg2[0] == "int":
        try:
            arg2_int = int(arg2[1])
            arg3_int = int(arg3[1])
        except:
            print("Incorrect value")
            sys.exit(32)

        # with division it checks if second number is not 0
        if type_of_op == "ADD":
            FrameHandle.set_var_value(frame_handle, frame_type, value, arg2[0], arg2_int + arg3_int)
        elif type_of_op == "SUB":
            FrameHandle.set_var_value(frame_handle, frame_type, value, arg2[0], arg2_int - arg3_int)
        elif type_of_op == "MUL":
            FrameHandle.set_var_value(frame_handle, frame_type, value, arg2[0], arg2_int * arg3_int)
        elif type_of_op == "IDIV":
            if int(arg3[1]) != 0:
                FrameHandle.set_var_value(frame_handle, frame_type, value, arg2[0], arg2_int // arg3_int)
            else:
                print("Zero division")
                sys.exit(57)

    else:
        if arg2[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Incorrect type")
            sys.exit(53)

# function processing jumpifeq/noneq operations
def jumpifeq_or_noneq_op(arg_list, instruction_list, frame_handle: FrameHandle, switch):
    arg1 = arg_list[get_arg_index(arg_list, "arg1")].text  # label
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    # if types do not match
    if arg2[0] is None or arg3[0] is None:
        print("UnsetVal")
        sys.exit(56)
    if arg2[0] != arg3[0] and (arg2[0] != "nil" and arg3[0] != "nil"):
        print("Comparison error")
        sys.exit(53)


    # check if equal based on switch parameter which decides if
    # noneq or eq jump should be done
    if switch:
        if replace_escape(arg2[1] or '') == replace_escape(arg3[1] or ''):
            return get_label_index(instruction_list, arg1)
        else:
            get_label_index(instruction_list, arg1)
            return None
    if not switch:
        if replace_escape(arg2[1] or '') !=replace_escape(arg3[1] or ''):
            return get_label_index(instruction_list, arg1)
        else:
            get_label_index(instruction_list, arg1)
            return None


# returns (type, value) of const/var
def parse_arg(arg, arg_list, frame_handle):
    ret_arg = arg_list[get_arg_index(arg_list, arg)]

    # 1 -> variable, 0 -> constant
    if ret_arg.attrib["type"] == "var":
        ret_arg = ret_arg.text.split('@', 1)
        res = FrameHandle.get_var_from_frame(frame_handle, ret_arg[0], ret_arg[1])
        return res[0], res[1]  # (type, val)
    else:
        return ret_arg.attrib["type"], ret_arg.text

# simply checks if the passed variable is string type and saves its length into second variable
def strlen_op(frame_handle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1

    if arg2[0] == "string":
        FrameHandle.set_var_value(frame_handle, frame_type, var, "int", len(arg2[1] or ''))
    else:
        if arg2[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Invalid type")
            sys.exit(53)

# concat operation
# adds two passed trings together and saves them into the thirt variable passed
def concat_op(frame_handle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    if arg2[0] == "string" and arg3[0] == "string":
        FrameHandle.set_var_value(frame_handle, frame_type, var, "string", str(arg2[1] or '') + str(arg3[1] or ''))
    else:
        if arg2[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Invalid type")
            sys.exit(53)

# getchar operation
def getchar_op(frame_handle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    if arg3[0] == "int" and arg2[0] == "string":
        int_val = int(arg3[1])

        # check if position is inside given string
        if len(arg2[1]) - 1 >= int_val >= 0:
            FrameHandle.set_var_value(frame_handle, frame_type, var, arg2[0], arg2[1][int_val])
        else:
            print("Index outside of array bounds")
            sys.exit(58)
    else:
        if arg2[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Invalid type")
            sys.exit(53)

# same idea as getchar operation
# checks if the value is inside given string lenght
# and sets its value on given string to passed character
def setchar_op(frame_handle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var
    arg1 = parse_arg("arg1", arg_list, frame_handle)  # var 1
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1
    arg3 = parse_arg("arg3", arg_list, frame_handle)  # symbol 2

    if arg1[0] == "string" and arg2[0] == "int" and arg3[0] == "string":
        int_val = int(arg2[1])

        if arg3[1] is None:
            sys.exit(58)
        else:
            char_val = replace_escape(arg3[1])[0]

        if len(arg1[1]) - 1 >= int_val >= 0:
            # placing new character into given string
            replaced_val = arg1[1][:int_val] + char_val + arg1[1][int_val+1:]
            FrameHandle.set_var_value(frame_handle, frame_type, var, "string", replaced_val)
        else:
            print("Index outside of array bounds")
            sys.exit(58)
    else:
        if arg2[0] is None or arg1[0] is None or arg3[0] is None:
            print("UnsetVal")
            sys.exit(56)
        else:
            print("Invalid type")
            sys.exit(53)

# gets the type and saves it to second argument
def type_op(frame_handle, arg_list):
    frame_type, var = arg_list[get_arg_index(arg_list, "arg1")].text.split('@', 1)  # var
    arg2 = parse_arg("arg2", arg_list, frame_handle)  # symbol 1

    if arg2[0] == "int" or arg2[0] == "bool" or arg2[0] == "string" or arg2[0] == "nil":
        FrameHandle.set_var_value(frame_handle, frame_type, var, "string", arg2[0])
    else:
        FrameHandle.set_var_value(frame_handle, frame_type, var, "string", "")


def break_op(frame_handle, arg_list):
    sys.stderr.write("Print current values")