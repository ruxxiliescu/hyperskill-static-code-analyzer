import os
import re
import ast


class Checker:
    MESSAGE_CODES = {
        "S001": "Too long",
        "S002": "Indentation is not a multiple of four",
        "S003": "Unnecessary semicolon after a statement",  # acceptable in comments
        "S004": "Less than two spaces before inline comments",
        "S005": "TODO found",  # in comments only and case-insensitive
        "S006": "More than two blank lines preceding a code line",  # applies to the first non-empty line
        "S007": "Too many spaces after {}",
        "S008": "Class name {} should be written in CamelCase",
        "S009": "Function name {} should be written in snake_case",
        "S010": "Argument name arg_name should be written in snake_case",
        "S011": "Variable var_name should be written in snake_case",
        "S012": "The default argument value is mutable"
    }

    @staticmethod
    # S001
    def check_length(line: str) -> bool:
        return len(line) > 79

    @staticmethod
    # S002
    def check_indentation(line: str) -> bool:
        t = 0
        for c in line:
            if c == " ":
                t += 1
            else:
                break
        return t % 4 != 0

    @staticmethod
    # S003
    def check_semicolons(line: str) -> bool:
        code = line.split("#")[0]
        if len(code) > 0:
            return code.strip()[-1] == ";"

    @staticmethod
    # S004
    def check_inline_comments(line: str) -> bool:
        return "  #" not in line and "#" in line and line[0] != "#"

    @staticmethod
    # S005
    def check_todos(line: str) -> bool:
        line = line.casefold()
        return any(("#todo" in line, "# todo" in line))

    @staticmethod
    # S006
    def check_blank_lines(lines: list, i: int) -> bool:
        if i > 2:
            return lines[i - 3: i] == ["", "", ""] and lines[i] != ""

    @staticmethod
    # S007
    def check_spaces(line: str) -> bool:
        return ('class' in line or 'def' in line) and (re.match(r'(class|def)\s{2,}', line.lstrip()))

    @staticmethod
    # S008
    def check_class_name(line: str) -> bool:
        return 'class' in line and not re.match(r'^class\s+[A-Z]', line)

    @staticmethod
    # S009
    def check_func_name(line: str) -> bool:
        return 'def' in line and not re.match(r'^def\s+[^A-Z]', line.lstrip())

    @staticmethod
    # S010
    def check_argument_name(objects: dict) -> set:
        # parse functions appended to the dictionary
        functions = objects[ast.FunctionDef]
        warnings = set()
        for f in functions:
            for a in f.args.args:
                # verify snake_case
                if re.match("(_{,2})?[a-z]+(_[a-z]*)*(_{,2})?", a.arg) is None:
                    # append if not
                    warnings.add(a.arg)
        return warnings

    @staticmethod
    # S011
    def check_variable_name(objects: dict) -> set:
        # parse variables appended to the dictionary
        variables = objects[ast.Name]
        warnings = set()
        for v in variables:
            if isinstance(v.ctx, ast.Store):
                # verify snake_case
                if re.match("(_{,2})?[a-z]+(_[a-z]*)*(_{,2})?", v.id) is None:
                    # append if not
                    warnings.add(v.id)
        return warnings

    @staticmethod
    # S012
    def check_mutable_value(objects: dict) -> set:
        # verify mutable default arguments
        functions = objects[ast.FunctionDef]
        warnings = set()
        for f in functions:
            for def_arg in f.args.defaults:
                if type(def_arg) in (ast.List, ast.Set, ast.Dict):
                    warnings.add(f.name)
                elif type(def_arg) == ast.Call:
                    if def_arg.func.id in ('set', 'list', 'dict'):
                        warnings.add(f)
        return warnings

    @staticmethod
    def ast_processing(f) -> dict:
        objects = {ast.FunctionDef: [],
                   ast.Name: []}
        tree = ast.parse(f.read())
        nodes = ast.walk(tree)

        # append to dictionary nodes in respective instances
        for n in nodes:
            if isinstance(n, ast.FunctionDef):
                objects[ast.FunctionDef].append(n)
            if isinstance(n, ast.Name):
                objects[ast.Name].append(n)
        return objects

    @staticmethod
    def test(path, file=None):
        if file:
            path = os.path.join(path, file)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # creates a list of lines on which the stripping function has been applied
            lines = list(map(lambda x: x.rstrip(), lines))
            # change the position of the file handler at the beginning of the file
            f.seek(0)
            objects = Checker.ast_processing(f)
            checked_args = list(Checker.check_argument_name(objects))
            checked_variables = list(Checker.check_variable_name(objects))
            checked_default_variables = list(Checker.check_mutable_value(objects))

            for i in range(len(lines)):
                if Checker.check_length(lines[i]):
                    print(f"{path}: Line {i + 1}: S001 {Checker.MESSAGE_CODES['S001']}")
                if Checker.check_indentation(lines[i]):
                    print(f"{path}: Line {i + 1}: S002 {Checker.MESSAGE_CODES['S002']}")
                if Checker.check_semicolons(lines[i]):
                    print(f"{path}: Line {i + 1}: S003 {Checker.MESSAGE_CODES['S003']}")
                if Checker.check_inline_comments(lines[i]):
                    print(f"{path}: Line {i + 1}: S004 {Checker.MESSAGE_CODES['S004']}")
                if Checker.check_todos(lines[i]):
                    print(f"{path}: Line {i + 1}: S005 {Checker.MESSAGE_CODES['S005']}")
                if Checker.check_blank_lines(lines, i):
                    print(f"{path}: Line {i + 1}: S006 {Checker.MESSAGE_CODES['S006']}")
                if Checker.check_spaces(lines[i]):
                    constructor = "'class'" if lines[i].startswith("class") else "'def'"
                    print(f"{path}: Line {i + 1}: S007 {Checker.MESSAGE_CODES['S007'].format(constructor)}")
                if Checker.check_class_name(lines[i]):
                    class_name = re.split(' +', lines[i])[1]
                    class_name = re.sub(r'\W+', '', class_name)
                    print(f"{path}: Line {i + 1}: S008 {Checker.MESSAGE_CODES['S008'].format(class_name)}")
                if Checker.check_func_name(lines[i]):
                    function_name = re.split(' +', lines[i])[1]
                    function_name = re.sub(r'\W+', '', function_name)
                    print(f"{path}: Line {i + 1}: S009 {Checker.MESSAGE_CODES['S009'].format(function_name)}")

                j = 0
                while j < len(checked_args):
                    if checked_args[j] in lines[i]:
                        print(f"{path}: Line {i + 1}: S010 {Checker.MESSAGE_CODES['S010']}")
                        checked_args.remove(checked_args[j])
                    else:
                        j += 1
                j = 0
                while j < len(checked_variables):
                    if checked_variables[j] in lines[i]:
                        print(f"{path}: Line {i + 1}: S011 {Checker.MESSAGE_CODES['S011']}")
                        checked_variables.remove(checked_variables[j])
                    else:
                        j += 1
                j = 0
                while j < len(checked_default_variables):
                    if checked_default_variables[j] in lines[i]:
                        print(f"{path}: Line {i + 1}: S012 {Checker.MESSAGE_CODES['S012']}")
                        checked_default_variables.remove(checked_default_variables[j])
                    else:
                        j += 1
