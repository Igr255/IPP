import sys


class FrameHandle:

    def __init__(self):
        # dictionary for global frame {[name] : (type, val)}
        self.global_frame = {}
        # dictionary for global frame
        self.tmp_frame = None
        self.frame_stack = []
        self.stack = []

    def pop_frame(self):
        self.frame_stack.pop()

    def push_frame(self, frame):
        self.frame_stack.append(frame)

    # returns wanted frame based on type that is passed
    def get_frame_based_on_type(self, frame_type):
        if frame_type == "GF": return self.global_frame
        elif frame_type == "TF":
            return self.tmp_frame
        elif frame_type == "LF":
            if len(self.frame_stack) > 0:
                return self.frame_stack[-1]
            else:
                print("Stack value does not exist")
                sys.exit(55)
        else:
            return None

    # sets a variab le for returned (available/current) frame
    def add_var_to_frame(self, frame_type, var):
        frame = self.get_frame_based_on_type(frame_type)

        if frame is not None:
            if var not in frame:
                frame[var] = (None, None)
            else:
                print("Variable " + var + " in " + frame_type + " already exists.")
                exit(52)
        else:
            print("No TF created")
            exit(55)

    # adds value to a variable stored on passed frame
    def set_var_value(self, frame_type, var, value_type, value):
        frame = self.get_frame_based_on_type(frame_type)

        if frame is not None:
            if var in frame:
                if value_type is not None:
                    frame[var] = (value_type, "{}".format(value))
                else:
                    exit(56)
            else:
                exit(54)
        else:
            print("No TF created")
            exit(55)

    # retrieving a variable from given frame
    def get_var_from_frame(self, frame_type, var):
        frame = self.get_frame_based_on_type(frame_type)
        # variable init
        if frame is not None:
            if var not in frame:
                print("Trying to access non-existent variable")
                exit(54)
            else:
                return frame[var]
        else:
            print("No TF created")
            exit(55)
