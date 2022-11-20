import sys

program_vars = dict()
program_functions = dict()


class DeclareFunction:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"DeclareFunction: {self.name}"


class Return:
    def __init__(self):
        ()

    def __str__(self):
        return "Return"


class CallFunction:
    def __init__(self, fun_name):
        self.fun_name = fun_name

    def __str__(self):
        return f"CallFunction: {self.fun_name}"

    def run(self):
        run_function(self.fun_name)


class Increment:
    def __init__(self, var, step):
        self.var = var
        self.step = step

    def __str__(self):
        return f"Increment: {self.var} {self.step}"

    def run(self):
        assert (self.var in program_vars)
        program_vars[self.var] = program_vars[self.var] + self.step


class DeclareVar:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return f"DeclareVar: {self.name} {self.value}"

    def run(self):
        assert (self.name not in program_vars)
        program_vars[self.name] = self.value


class Comp:
    def __init__(self, op_str):
        self.op_str = op_str

    def compare(self, left, right):
        if self.op_str == "==":
            return left == right
        elif self.op_str == "!=":
            return left != right
        elif self.op_str == "<":
            return left < right
        elif self.op_str == "<=":
            return left <= right
        elif self.op_str == ">":
            return left > right
        elif self.op_str == ">=":
            return left >= right


class VarRef:
    def __init__(self, var_name):
        self.var_name = var_name

    def __str__(self):
        return f"VarRef: {self.var_name}"

    def get_value(self):
        assert (self.var_name in program_vars)
        return program_vars[self.var_name]

    def get_string(self):
        v = self.get_value()
        return str(v)


class Condition:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        self.body = None

    def __str__(self):
        return f"Condition: {self.left} {self.operator} {self.right}, Body: {self.body}"

    def run(self):
        if isinstance(self.left, int):
            left = self.left
        elif isinstance(self.left, VarRef):
            left = self.left.get_value()
        if isinstance(self.right, int):
            right = self.right
        elif isinstance(self.right, VarRef):
            right = self.right.get_value()
        if self.operator.compare(left, right):
            run_ast(self.body)


class EndCondition:
    def __init__(self):
        ()

    def __str__(self):
        return "EndCondition"


class String:
    def __init__(self, value, quoted):
        self.value = value
        self.quoted = quoted

    def __str__(self):
        if self.quoted:
            return f"Quoted String: \"{self.value}\""
        else:
            return f"Unquoted String: \"{self.value}\""

    def get_string(self):
        return self.value


class Message:
    def __init__(self, elements):
        self.elements = elements

    def __str__(self):
        return "Message: " + ", ".join(map(str, self.elements))

    def run(self):
        if self.elements == None or len(self.elements) == 0:
            return

        s = self.elements[0].get_string()
        if isinstance(self.elements[0], VarRef):
            previous_item_was_quoted = False
            previous_item_was_var = True
        elif isinstance(self.elements[0], String):
            previous_item_was_quoted = self.elements[0].quoted
            previous_item_was_var = True

        for e in self.elements[1:]:
            if isinstance(e, VarRef):
                if (not previous_item_was_quoted) & (not previous_item_was_var):
                    s += " "
                s += e.get_string()
                previous_item_was_quoted = False
                previous_item_was_var = True
            elif isinstance(e, String):
                if e.quoted:
                    if not previous_item_was_quoted and not previous_item_was_var:
                        s += " " + e.get_string()
                    else:
                        s += e.get_string()
                else:
                    s += " " + e.get_string()
                previous_item_was_quoted = e.quoted
                previous_item_was_var = False

        print(s)


# Statement: TypeAlias = DeclareFunction | Return | CallFunction | Increment | DeclareVar | Condition | EndCondition | Message


def aux_parse_message(text, elements):
    text = text.lstrip().rstrip()
    if len(text) == 0:
        return
    if text[0] == '$':
        # this is a variable reference
        # read until the next whitespace
        l = text[1:].partition(" ")
        elements.append(VarRef(l[0]))
        aux_parse_message(l[2], elements)
    elif text[0] == "\"":
        # this is a string. Read until the next quote
        l = text[1:].partition("\"")
        elements.append(String(l[0], quoted=True))
        aux_parse_message(l[2], elements)
    else:
        l = text.partition(" ")
        elements.append(String(l[0], quoted=False))
        aux_parse_message(l[2], elements)


def parse_message(text):
    # print("message strings: " + text)
    elements = list()
    aux_parse_message(text, elements)
    return Message(elements)


def parse_nombre(text):
    elts = text.split(None)
    return DeclareVar(elts[0], int(elts[1]))


def parse_appel(text):
    elts = text.split(None)
    return CallFunction(elts[0])


def parse_retour(text):
    return Return()


def parse_varref_or_const(text):
    if text[0] == '$':
        return VarRef(text[1:])
    else:
        return int(text)


def parse_si(text):
    elts = text.split(None)
    left = parse_varref_or_const(elts[0])
    op = Comp(elts[1])
    right = parse_varref_or_const(elts[2])
    return Condition(left, op, right)


def parse_finsi(text):
    return EndCondition()


def parse_incrementer(text):
    elts = text.split(None)
    return Increment(elts[0], int(elts[1]))


def parse_declare_fun(text):
    return DeclareFunction(text[:-1])


def parse_line(line):
    partitions = line.partition(' ')
    # print("\"" + partitions[0] + "\"")

    if partitions[0] == 'message':
        return parse_message(partitions[2])
    elif partitions[0] == 'nombre':
        return parse_nombre(partitions[2])
    elif partitions[0] == 'appel':
        return parse_appel(partitions[2])
    elif partitions[0] == 'retour':
        return parse_retour(partitions[2])
    elif partitions[0] == 'si':
        return parse_si(partitions[2])
    elif partitions[0] == 'incrementer':
        return parse_incrementer(partitions[2])
    elif partitions[0] == 'finsi':
        return parse_finsi(partitions[2])
    else:  # should be a function declaration
        if partitions[0][-1] == ':':
            return parse_declare_fun(partitions[0])
        else:
            print("Syntax error: " + partitions[0])
            exit(-1)


def parse(filename):
    with open(filename) as f:
        count = 0
        statements = list()
        for line in f:
            line = line.rstrip()
            count += 1
            if len(line) == 0:
                # empty line, continue
                continue
            if line[0] == ';':
                # comment, continue
                continue
            s = parse_line(line)
            # print(s)
            statements.append(s)

        return statements


def append_statement_to_fun_dict(statement, fun_name, fun_dict):
    if fun_name in fun_dict:
        fun_dict[fun_name].append(statement)
    else:
        fun_dict[fun_name] = [statement]


def extract_functions(statements):
    current_fun_name = "main"
    fun_dict = dict()
    for s in statements:
        if isinstance(s, DeclareFunction):
            current_fun_name = s.name
        elif isinstance(s, Return):
            current_fun_name = "main"
        else:
            append_statement_to_fun_dict(s, current_fun_name, fun_dict)
    return fun_dict


def build_ast_helper(statements, ast_accumulator):
    if len(statements) > 0:
        if isinstance(statements[0], Condition):
            # get the body of the test
            (remaining_statements, body) = build_ast_helper(
                statements[1:], list())
            statements[0].body = body
            ast_accumulator.append(statements[0])
            return build_ast_helper(remaining_statements, ast_accumulator)
        elif isinstance(statements[0], EndCondition):
            return (statements[1:], ast_accumulator)
        else:
            ast_accumulator.append(statements[0])
            return build_ast_helper(statements[1:], ast_accumulator)
    else:
        return (None, ast_accumulator)


def build_ast(statements):
    ret = build_ast_helper(statements, list())
    (remains, ast) = ret
    assert (remains == None)
    return ast


def print_ast(statements, level=0):
    for s in statements:
        print("\t"*level + str(s))
        if s == Condition():
            print_ast(s.body, level=level+1)


def run_ast(ast):
    for s in ast:
        s.run()


def run_function(name):
    run_ast(program_functions[name])


def print_output_to_stdout():
    run_function("main")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 " + sys.argv[0] + " <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    statements = parse(filename)
    fun_dict = extract_functions(statements)
    # print(fun_dict)

    ast_dict = {k: build_ast(v) for k, v in fun_dict.items()}

    # for name, ast in ast_dict.items():
    #     print("function: " + name)
    #     print_ast(ast)
    #     print("\n\n")

    global program_functions
    program_functions = ast_dict

    print_output_to_stdout()


if __name__ == "__main__":
    main()
