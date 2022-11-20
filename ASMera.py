import sys
from enum import Enum
from typing import Tuple, TypeAlias

program_vars = dict()
program_functions = dict()


class DeclareFunction:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"DeclareFunction: {self.name}"


class Return:
    def __init__(self):
        ()

    def __str__(self):
        return "Return"


class CallFunction:
    def __init__(self, fun_name: str):
        self.fun_name = fun_name

    def __str__(self):
        return f"CallFunction: {self.fun_name}"

    def run(self):
        run_function(self.fun_name)


class Increment:
    def __init__(self, var: str, step: int):
        self.var = var
        self.step = step

    def __str__(self):
        return f"Increment: {self.var} {self.step}"

    def run(self):
        assert (self.var in program_vars)
        program_vars[self.var] = program_vars[self.var] + self.step


class DeclareVar:
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value

    def __str__(self):
        return f"DeclareVar: {self.name} {self.value}"

    def run(self):
        assert (self.name not in program_vars)
        program_vars[self.name] = self.value


class Comp(Enum):
    EQ = 1
    NEQ = 2
    LT = 3
    LEQ = 4
    GT = 5
    GEQ = 6

    def compare(self, left: int, right: int) -> bool:
        match self:
            case Comp.EQ:
                return left == right
            case Comp.NEQ:
                return left != right
            case Comp.LT:
                return left < right
            case Comp.LEQ:
                return left <= right
            case Comp.GT:
                return left > right
            case Comp.GEQ:
                return left >= right


class VarRef:
    def __init__(self, var_name: str):
        self.var_name = var_name

    def __str__(self):
        return f"VarRef: {self.var_name}"

    def get_value(self) -> int:
        assert (self.var_name in program_vars)
        return program_vars[self.var_name]

    def get_string(self) -> str:
        v = self.get_value()
        return str(v)


class Condition:
    def __init__(self, left: int | VarRef, operator: Comp, right: int | VarRef):
        self.left = left
        self.operator = operator
        self.right = right
        self.body = None

    def __str__(self):
        return f"Condition: {self.left} {self.operator} {self.right}, Body: {self.body}"

    def run(self):
        match self.left:
            case int():
                left = self.left
            case VarRef():
                left = self.left.get_value()
        match self.right:
            case int():
                right = self.right
            case VarRef():
                right = self.right.get_value()
        if self.operator.compare(left, right):
            run_ast(self.body)


class EndCondition:
    def __init__(self):
        ()

    def __str__(self):
        return "EndCondition"


class String:
    def __init__(self, value: str, quoted: bool):
        self.value = value
        self.quoted = quoted

    def __str__(self):
        if self.quoted:
            return f"Quoted String: \"{self.value}\""
        else:
            return f"Unquoted String: \"{self.value}\""

    def get_string(self) -> str:
        return self.value


class Message:
    def __init__(self, elements: list[String | VarRef]):
        self.elements = elements

    def __str__(self):
        return "Message: " + ", ".join(map(str, self.elements))

    def run(self):
        if self.elements == None or len(self.elements) == 0:
            return

        s = self.elements[0].get_string()
        match self.elements[0]:
            case VarRef():
                previous_item_was_quoted = False
                previous_item_was_var = True
            case String():
                previous_item_was_quoted = self.elements[0].quoted
                previous_item_was_var = True

        for e in self.elements[1:]:
            match e:
                case VarRef():
                    if (not previous_item_was_quoted) & (not previous_item_was_var):
                        s += " "
                    s += e.get_string()
                    previous_item_was_quoted = False
                    previous_item_was_var = True
                case String():
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


Statement: TypeAlias = DeclareFunction | Return | CallFunction | Increment | DeclareVar | Condition | EndCondition | Message


def aux_parse_message(text: str, elements: list[String | VarRef]):
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


def parse_message(text: str) -> Message:
    # print("message strings: " + text)
    elements = list()
    aux_parse_message(text, elements)
    return Message(elements)


def parse_nombre(text: str) -> DeclareVar:
    elts = text.split(None)
    return DeclareVar(elts[0], int(elts[1]))


def parse_appel(text: str) -> CallFunction:
    elts = text.split(None)
    return CallFunction(elts[0])


def parse_retour(text: str) -> Return:
    return Return()


def parse_varref_or_const(text: str) -> VarRef | int:
    if text[0] == '$':
        return VarRef(text[1:])
    else:
        return int(text)


def parse_comp_operator(text: str) -> Comp:
    match text:
        case '==':
            return Comp.EQ
        case '!=':
            return Comp.NEQ
        case '<':
            return Comp.LT
        case '>':
            return Comp.GT
        case '<=':
            return Comp.LEQ
        case '>=':
            return Comp.GEQ


def parse_si(text: str) -> Condition:
    elts = text.split(None)
    left = parse_varref_or_const(elts[0])
    op = parse_comp_operator(elts[1])
    right = parse_varref_or_const(elts[2])
    return Condition(left, op, right)


def parse_finsi(text: str) -> EndCondition:
    return EndCondition()


def parse_incrementer(text: str) -> Increment:
    elts = text.split(None)
    return Increment(elts[0], int(elts[1]))


def parse_declare_fun(text: str) -> DeclareFunction:
    return DeclareFunction(text[:-1])


def parse_line(line: str) -> Statement:
    partitions = line.partition(' ')
    # print("\"" + partitions[0] + "\"")

    match partitions[0]:
        case 'message':
            return parse_message(partitions[2])
        case 'nombre':
            return parse_nombre(partitions[2])
        case 'appel':
            return parse_appel(partitions[2])
        case 'retour':
            return parse_retour(partitions[2])
        case 'si':
            return parse_si(partitions[2])
        case 'incrementer':
            return parse_incrementer(partitions[2])
        case 'finsi':
            return parse_finsi(partitions[2])
        case _:  # should be a function declaration
            if partitions[0][-1] == ':':
                return parse_declare_fun(partitions[0])
            else:
                print("Syntax error: " + partitions[0])
                exit(-1)


def parse(filename: str) -> list[Statement]:
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


def append_statement_to_fun_dict(statement: Statement, fun_name: str, fun_dict: dict[list[Statement]]):
    if fun_name in fun_dict:
        fun_dict[fun_name].append(statement)
    else:
        fun_dict[fun_name] = [statement]


def extract_functions(statements: list[Statement]) -> dict[list[Statement]]:
    current_fun_name = "main"
    fun_dict = dict()
    for s in statements:
        match s:
            case DeclareFunction():
                current_fun_name = s.name
            case Return():
                current_fun_name = "main"
            case _:
                append_statement_to_fun_dict(s, current_fun_name, fun_dict)
    return fun_dict


def build_ast_helper(statements: list[Statement], ast_accumulator: list[Statement]) -> Tuple[list[Statement], list[Statement]]:
    if len(statements) > 0:
        match statements[0]:
            case Condition():
                # get the body of the test
                (remaining_statements, body) = build_ast_helper(
                    statements[1:], list())
                statements[0].body = body
                ast_accumulator.append(statements[0])
                return build_ast_helper(remaining_statements, ast_accumulator)
            case EndCondition():
                return (statements[1:], ast_accumulator)
            case _:
                ast_accumulator.append(statements[0])
                return build_ast_helper(statements[1:], ast_accumulator)
    else:
        return (None, ast_accumulator)


def build_ast(statements: list[Statement]) -> list[Statement]:
    ret = build_ast_helper(statements, list())
    (remains, ast) = ret
    assert (remains == None)
    return ast


def print_ast(statements: list[Statement], level=0):
    for s in statements:
        print("\t"*level + str(s))
        match s:
            case Condition():
                print_ast(s.body, level=level+1)


def run_ast(ast: list[Statement]):
    for s in ast:
        s.run()


def run_function(name: str):
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
