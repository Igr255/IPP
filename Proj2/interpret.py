import argparse
import xml.etree.ElementTree as ElementTree
import sys
from FrameHandle import FrameHandle
import operations

# function used for processing every argument from given XML
# calls functions for every different operation from operations.py
# returns:
# ret_val, ret_labels, ret_distinct_labels
# based on every function and if they update labes/distinct labes in any way
def process_instruction(instruction, frame_handle, labels, i, instruction_list, distinct_label_names: list, input_path):
    try:
        instruction_name = instruction.attrib["opcode"].upper()
    except:
        print("Opcode attribute is missing")
        sys.exit(32)

    arg_list = list(instruction)

    if instruction_name == "WRITE":
        operations.write_op(arg_list, frame_handle)
    elif instruction_name == "READ":
        operations.read_op(arg_list, frame_handle, input_path)
    elif instruction_name == "DEFVAR":
        operations.defvar_op(arg_list, frame_handle)
    elif instruction_name == "MOVE":
        operations.move_op(arg_list, frame_handle)
    elif instruction_name == "EXIT":
        operations.exit_op(arg_list, frame_handle)
    elif instruction_name == "JUMP":
        return operations.jump_op(arg_list, instruction_list), None, None  # index, None
    elif instruction_name == "JUMPIFEQ":
        return operations.jumpifeq_or_noneq_op(arg_list, instruction_list, frame_handle, True), None, None  # index, None
    elif instruction_name == "JUMPIFNEQ":
        return operations.jumpifeq_or_noneq_op(arg_list, instruction_list, frame_handle, False), None, None  # index, None
    elif instruction_name == "CALL":
        ret_index, labels = operations.call_op(arg_list, labels, instruction_list, i)
        return ret_index, labels, None  # index, labels_update
    elif instruction_name == "RETURN":
        ret_index, labels = operations.return_op(labels)
        return ret_index, labels, None  # index, labels_update
    elif instruction_name == "LABEL":
        return None, None, operations.label_op(arg_list, distinct_label_names)
    elif instruction_name == "ADD" or instruction_name == "MUL" or instruction_name == "IDIV" or instruction_name == "SUB":
        operations.aritmethic_op(arg_list, frame_handle, instruction_name)
    elif instruction_name == "CREATEFRAME":
        operations.createframe_op(frame_handle)
    elif instruction_name == "PUSHFRAME":
        operations.pushframe_op(frame_handle)
    elif instruction_name == "POPFRAME":
        operations.popframe_op(frame_handle)
    elif instruction_name == "PUSHS":
        operations.pushs_op(frame_handle, arg_list)
    elif instruction_name == "POPS":
        operations.pops_op(frame_handle, arg_list)
    elif instruction_name == "AND":
        operations.and_op(frame_handle, arg_list)
    elif instruction_name == "OR":
        operations.or_op(frame_handle, arg_list)
    elif instruction_name == "NOT":
        operations.not_op(frame_handle, arg_list)
    elif instruction_name == "INT2CHAR":
        operations.int2char_op(frame_handle, arg_list)
    elif instruction_name == "STRI2INT":
        operations.stri2int_op(frame_handle, arg_list)
    elif instruction_name == "LT":
        operations.lt_op(frame_handle, arg_list)
    elif instruction_name == "GT":
        operations.gt_op(frame_handle, arg_list)
    elif instruction_name == "EQ":
        operations.eq_op(frame_handle, arg_list)
    elif instruction_name == "DPRINT":
        operations.dprint_op(frame_handle, arg_list)
    elif instruction_name == "BREAK":
        operations.break_op(frame_handle, arg_list)
    elif instruction_name == "CONCAT":
        operations.concat_op(frame_handle, arg_list)
    elif instruction_name == "STRLEN":
        operations.strlen_op(frame_handle, arg_list)
    elif instruction_name == "GETCHAR":
        operations.getchar_op(frame_handle, arg_list)
    elif instruction_name == "SETCHAR":
        operations.setchar_op(frame_handle, arg_list)
    elif instruction_name == "TYPE":
        operations.type_op(frame_handle, arg_list)
    else:
        print("Operation does not exist")
        sys.exit(32)

    # ret_val, ret_labels, ret_distinct_labels
    return None, None, None


def load_xml(src_path):
    try:
        source_xml = ElementTree.parse(src_path)
    except:
        print("Could not load XML")
        sys.exit(31)

    if source_xml.getroot().tag != "program":
        print("Incorrect root")
        sys.exit(32)

    if not check_header(source_xml):
        print("Incorrect header")
        sys.exit(32)

    return source_xml

# simple helper function if the header is correct
def check_header(xml: ElementTree.ElementTree):
    return xml.getroot().attrib["language"].upper() == "IPPCODE22"

# adding supported arguments
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, required=False, help = "pass file to the tested file")
    parser.add_argument('--input', type=str, required=False, help="redirect input for tested file")
    args = parser.parse_args()

    src_path = args.source
    input_path = args.input

    input_stdin = False
    source_stdin = False

    # at least one parameter has to be used
    if src_path is None and input_path is None:
        print("At least one arg must be passed")
        exit(10)

    # if input is None try to read it from stdin
    # sets flags
    if input_path is None:
        input_stdin = True
    elif src_path is None:
        source_stdin = True

    return src_path, input_path, input_stdin, source_stdin

# checking if child elements are not anythin else than instructions
# so no elements named incorrectly pass into operation calling
def check_child_elements(source_xml):
    child_elements = list(source_xml.getroot())
    for element in child_elements:
        if element.tag != "instruction":
            print("Incorrect instruction")
            sys.exit(32)

# sorts instructions into correct order and checks for duplicates
def sort_instructions(instruction_list):
    try:
        instruction_list.sort(key=(lambda x: int(x.attrib["order"])))
    except:
        print("Could not process order")
        sys.exit(32)

    list_of_ord_num = list(map(lambda x: int(x.attrib["order"]), instruction_list))

    if len(list_of_ord_num) != len(set(list_of_ord_num)):
        print("Ords with same number")
        sys.exit(32)

    for item in list_of_ord_num:
        if item <= 0:
            print("Negative order")
            sys.exit(32)

    return instruction_list


def main():
    # setting up class for frames
    frame_handle = FrameHandle()

    # setting up lists for labels
    labels = []
    distinct_label_names = []

    src_path, input_path, input_stdin, source_stdin = parse_arguments()

    if source_stdin:
        source_xml = load_xml(sys.stdin)
    else:
        source_xml = load_xml(src_path)

    # checks if all elements are instructions
    check_child_elements(source_xml)

    # load all instructions into list
    instruction_list = source_xml.findall("instruction")
    instruction_list = sort_instructions(instruction_list)

    # checks if input is loaded trough argument and strips it from newlines
    # otherwise sets input_list to none and read op will read from stdin
    input_list = None
    if input_path is not None:
        if not input_stdin:
            file = open(input_path, 'r')
            input_list = list(map(lambda x: x.strip(), file.readlines()))
        else:
            input_list = None

    # iteration trough all loaded instructions
    i = 0
    max_len = len(instruction_list)

    while i < max_len:
        ret_val, ret_labels, ret_distinct_labels = process_instruction(instruction_list[i], frame_handle, labels, i,
                                                                       instruction_list, distinct_label_names, input_list)
        # ret_val checks if code jumped to a different operation
        # labels and distinc_labes for label saving and chcking for duplicates
        if ret_val is not None:
            i = ret_val
        if ret_labels is not None:
            labels = ret_labels
        if ret_distinct_labels is not None:
            distinct_label_names = ret_distinct_labels
        i += 1


if __name__ == '__main__':
    main()
