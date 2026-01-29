import os
import ast
import json
import random

from collections import Counter

# import matplotlib.pyplot as plt


def get_all_files(path_to_file_or_folder:str) -> dict:
    all_files = dict()
    all_files["path"] = []
    all_files["name"] = []

    if os.path.isfile(path_to_file_or_folder):
        all_files["path"] += [path_to_file_or_folder]
        all_files["name"] += [os.path.basename(path_to_file_or_folder)]
    else:
        for cur_root, cur_dirs, cur_files in os.walk(path_to_file_or_folder):
            for cur_file in cur_files:
                cur_file_path = os.path.join(cur_root, cur_file)
                all_files["path"] += [cur_file_path]
                all_files["name"] += [cur_file]
                

        if len(all_files["path"]) == 0 or len(all_files["path"]) == 0:
            raise ValueError(f"Did not found any python or notebook file in the given folder path. Folder path: {path_to_file_or_folder}")

    return all_files

def load_code(cur_file:str) -> ast.AST:
    code = ""
    if cur_file.endswith(".py"):
        with open(cur_file, "r", encoding="utf-8") as f:
            code += f.read() + "\n"
    elif cur_file.endswith(".ipynb"):
        last_error = ""
        with open(cur_file, "r", encoding="utf-8") as f:
            notebook = json.load(f)
        for cell in notebook.get("cells", []):
            if cell.get("cell_type") == "code":
                new_code = code + "".join(cell.get("source", [])) + "\n"

                try:
                    ast.parse(new_code, filename=os.path.basename(cur_file), mode='exec')
                    code = new_code
                except Exception as e:
                    last_error = e
                    continue

        if not code.strip():
            raise last_error

    # if code == "":
    #     raise ValueError(f"Did not found any python or notebook file in the given folder path. Folder path: {path_to_file_or_folder}")

    tree = ast.parse(code, filename=os.path.basename(cur_file), mode='exec')

    return tree


def analyse_calls(tree) -> dict:
    calls = dict()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call = node.func
            call_name = None
            
            while call:
                if isinstance(call, ast.Attribute):
                    if isinstance(call.value, ast.Name) and call.attr:
                        call_name = f"{call.value.id}.{call.attr}"
                        break
                    call = call.value
                elif isinstance(call, ast.Call):
                    call = call.func
                elif isinstance(call, ast.Name):
                    call_name = call.id
                    break
                else:
                    break
            
            if call_name:
                calls[call_name] = calls.get(call_name, 0) + 1

    return calls


def analyse_imports(tree) -> list:
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports += [f"{name.name}"]
        elif isinstance(node, ast.ImportFrom):
            for name in node.names:
                imports += [f"{node.module}.{name.name}"]

    return imports


def analyse_definitions(tree) -> None:
    defs = []
    lambdas = 0
    classes = []
    returns = 0
    yields = 0
    globals = 0
    nonlocals = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defs += [node.name]
        elif isinstance(node, ast.Lambda):
            lambdas += 1
        elif isinstance(node, ast.ClassDef):
            classes += [node.name]
        elif isinstance(node, ast.Return):
            returns += 1
        elif isinstance(node, ast.Yield):
            yields += 1
        elif isinstance(node, ast.Global):
            globals += 1
        elif isinstance(node, ast.Nonlocal):
            nonlocals += 1

    return defs, lambdas, classes, returns, yields, globals, nonlocals


# Control Flow
def analyse_structures(tree) -> None:
    ifs = 0
    fors = 0
    whiles = 0
    breaks = 0
    continues = 0
    tries = 0
    withs = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            ifs += 1
        elif isinstance(node, ast.For):
            fors += 1
        elif isinstance(node, ast.While):
            whiles += 1
        elif isinstance(node, ast.Break):
            breaks += 1
        elif isinstance(node, ast.Continue):
            continues += 1
        elif isinstance(node, ast.Try):
            tries += 1
        elif isinstance(node, ast.With):
            withs += 1

    return ifs, fors, whiles, breaks, continues, tries, withs


def analyse_operations(tree) -> list:
    operations = 0
    adds = 0
    subs = 0
    mults = 0
    divs = 0
    mods = 0
    floor_divs = 0
    pows = 0

    bool_operations = 0
    ands = 0
    ors = 0
    equals = 0
    not_equals = 0
    is_ = 0
    is_not = 0
    ins = 0
    not_ins = 0
    
    for node in ast.walk(tree):

        if isinstance(node, ast.BinOp):
            operations += 1
        elif isinstance(node, ast.BoolOp) or isinstance(node, ast.Compare):
            bool_operations += 1

        # OP's
        if isinstance(node, ast.Add):
            adds += 1
        elif isinstance(node, ast.Sub):
            subs += 1
        elif isinstance(node, ast.Mult):
            mults += 1
        elif isinstance(node, ast.Div):
            divs += 1
        elif isinstance(node, ast.Mod):
            mods += 1
        elif isinstance(node, ast.FloorDiv):
            floor_divs += 1
        elif isinstance(node, ast.Pow):
            pows += 1
        # OP-BOOL's
        elif isinstance(node, ast.And):
            ands += 1
        elif isinstance(node, ast.Or):
            ors += 1
        elif isinstance(node, ast.Eq):
            equals += 1
        elif isinstance(node, ast.NotEq):
            not_equals += 1
        elif isinstance(node, ast.Is):
            is_ += 1
        elif isinstance(node, ast.IsNot):
            is_not += 1
        elif isinstance(node, ast.In):
            ins += 1
        elif isinstance(node, ast.NotIn):
            not_ins += 1

    # return [('Add', adds), ('Sub', subs), ('Mult', mults), ('Div', divs), ('Mod', mods), ('Floor Div', floor_divs), ('Pow', pows), 
    #        ('And', ands), ('Or', ors), ('Equal', equals), ('Not Equal', not_equals), ('Is', is_), ('Is Not', is_not), ('In', ins), ('Not In', not_ins)]

    return operations, adds, subs, mults, divs, mods, floor_divs, pows, bool_operations, ands, ors, equals, not_equals, is_, is_not, ins, not_ins


def visualize(calls:dict, imports:list, ops:list):
    plt.style.use('seaborn-whitegrid')
    fig, ax = plt.subplots(2, 1, figsize=(20, 10))
    
    x = []
    y = []
    counter = 0
    for name, value in sorted(calls.items(), key=lambda x: x[1], reverse=True):
        if counter >= 10:
            break
        x += [name]
        y += [value]
        counter += 1

    ax[0].set_title("Popular Function-Calls")
    ax[0].bar(x, y, align='center', width=0.5)

    x = []
    y = []
    for name, value in ops:
        x += [name]
        y += [value]
    ax[1].set_title("Operations")
    ax[1].bar(x, y)

    plt.show()


def create_analysis_str(
        name,
        calls,
        imports,
        definitions,
        structures,
        operations,
        failed_files, 
        successfull_files,
        failed_code_strs, 
        successfull_code_strs,
        short_analysis
        ):
    
    # begin
    title = f"\n    >>> Analysis of {name} <<<    \n"
    title_len = len(title)
    analysis = f"\n\n{'_'*title_len}"
    analysis += title

    # general
    analysis += f"\n Analysed {len(successfull_files)} files ({len([i for i in successfull_files if i.endswith('.py')])} .py + {len([i for i in successfull_files if i.endswith('.ipynb')])} .ipynb)"
    analysis += f"\n Failed to analyse {len(failed_files)} files because of errors."

    analysis += f"\n\n Analysed {successfull_code_strs} given code strings."
    analysis += f"\n Failed to analyse {len(failed_code_strs)} given code strings because of errors.\n\n"

    # call
    ordered_calls = sorted(calls.items(), key=lambda x: x[1], reverse=True)
    analysis += "\n-------------------------------------"
    analysis += "\n--------  Analysis of Calls  --------"
    analysis += "\n-------------------------------------"
    analysis += f"\nThere are {sum(calls.values())} calls.\n"
    for i, x in enumerate(ordered_calls):
        analysis += f"\n{x[1]}x {x[0]}"    # {i+1:02d}
        if i == 50 and short_analysis:
            analysis += "\n..."
            break
    analysis += "\n"

    # imports
    ordered_imports = sorted(imports, key=lambda x: x, reverse=False)
    analysis += "\n-------------------------------------"
    analysis += "\n-------  Analysis of Imports  -------"
    analysis += "\n-------------------------------------"
    import_counter = Counter(ordered_imports)
    for i, x in enumerate(sorted(list(set(ordered_imports)), key=lambda x: import_counter[x], reverse=False)):
        analysis += f"\n- {x} ({import_counter[x]})"

        if i == 50 and short_analysis:
            analysis += "\n- ..."
            break
    analysis += "\n"

    # definitions
    defs, lambdas, classes, returns, yields, globals, nonlocals = definitions
    analysis += "\n-------------------------------------"
    analysis += "\n-----  Analysis of Definitions  -----"
    analysis += "\n-------------------------------------"
    analysis += f"\n- Defined Functions ({len(defs)}):"
    defs_counter = Counter(defs)
    defs_sorted = sorted(defs_counter.items(), key=lambda x: x[1], reverse=True)
    defs_unique_ordered = [item[0] for item in defs_sorted]
    size = 50 if short_analysis else len(defs_unique_ordered)
    for x in sorted(random.sample(defs_unique_ordered, size)):
        analysis += f"\n    - {x} ({defs_counter[x]})"
    analysis += f"\n    - ..."

    analysis += f"\n\n- Defined Classes ({len(classes)}):"
    classes_counter = Counter(defs)
    classes_sorted = sorted(classes_counter.items(), key=lambda x: x[1], reverse=True)
    classes_unique_ordered = [item[0] for item in classes_sorted]
    size = 50 if short_analysis else len(classes_unique_ordered)
    for x in sorted(random.sample(classes_unique_ordered, size)):
        analysis += f"\n    - {x} ({classes_counter[x]})"
    analysis += f"\n    - ..."

    analysis += f"\n\n- Lambda Functions: {lambdas}"
    analysis += f"\n\n- Returns: {returns}"
    analysis += f"\n\n- Yields: {yields}"
    analysis += f"\n\n- `global` Keywords: {globals}"
    analysis += f"\n\n- `nonlocal` Keywords: {nonlocals}"
    analysis += "\n"

    # structures
    ifs, fors, whiles, breaks, continues, tries, withs = structures
    analysis += "\n-------------------------------------"
    analysis += "\n-----  Analysis of Structures  ------"
    analysis += "\n-------------------------------------"
    analysis += f"\n- Defined loops ({fors+whiles}):"
    analysis += f"\n    - For-Loops: {fors}"
    analysis += f"\n    - While-Loops: {whiles}"
    analysis += f"\n\n- Break's: {breaks}"
    analysis += f"\n\n- Continue's: {continues}"
    analysis += f"\n\n- If-Statements: {ifs}"
    analysis += f"\n\n- Try-Blocks: {tries}"
    analysis += f"\n\n- With-Blocks: {withs}"
    analysis += "\n"

    # operations
    operations, adds, subs, mults, divs, mods, floor_divs, pows, bool_operations, ands, ors, equals, not_equals, is_, is_not, ins, not_ins = operations
    analysis += "\n-------------------------------------"
    analysis += "\n-----  Analysis of Operations  ------"
    analysis += "\n-------------------------------------"
    analysis += f"\n- Operations ({operations}):"
    analysis += f"\n    - Add's: {adds}"
    analysis += f"\n    - Sub's: {subs}"
    analysis += f"\n    - Mult's: {mults}"
    analysis += f"\n    - Div's: {divs}"
    analysis += f"\n    - Mod's: {mods}"
    analysis += f"\n    - Floor Div's: {floor_divs}"
    analysis += f"\n    - Pow's: {pows}"
    analysis += f"\n\n- Bool Operations ({bool_operations}):"
    analysis += f"\n    - And's: {ands}"
    analysis += f"\n    - Or's: {ors}"
    analysis += f"\n    - Equals's: {equals}"
    analysis += f"\n    - Not Equals's: {not_equals}"
    analysis += f"\n    - Is's: {is_}"
    analysis += f"\n    - Is not's: {is_not}"
    analysis += f"\n    - In's: {ins}"
    analysis += f"\n    - Not In's: {not_ins}"
    analysis += "\n"

    # end
    analysis += f"\n{' '*(title_len//2-(23//2))}>>> END of Analysis <<<\n"
    analysis += "_"*title_len + "\n\n\n\n"

    return analysis


# def add_new_entry(
#                 calls
#                 imports
#                 definitions
#                 structures
#                 operations
#                 )

def merge_analysis_results(results_1:list, results_2:list):
    calls_1, imports_1, definitions_1, structures_1, operations_1 = results_1
    calls_2, imports_2, definitions_2, structures_2, operations_2 = results_2

    calls_3 = dict(Counter(calls_1) + Counter(calls_2))
    imports_3 = imports_1 + imports_2
    # unique_imports_3 = list(dict.fromkeys(imports_1 + imports_2))
    definitions_3 = [definitions_1[idx] + definitions_2[idx] for idx in range(len(definitions_1))]
    structures_3 = [structures_1[idx] + structures_2[idx] for idx in range(len(structures_1))]
    operations_3 = [operations_1[idx] + operations_2[idx] for idx in range(len(operations_1))]

    return calls_3, imports_3, definitions_3, structures_3, operations_3

def analyse_code(path_to_file_or_dir:str=None, code_strs:list=None, 
                 name:str="My Awesome Project", save_path:str="./", 
                 should_print:bool=True, should_save:bool=True,
                 short_analysis=True) -> str: 
    # Analysis of files
    failed_files = []
    successfull_files = []
    code_results = []
    if path_to_file_or_dir is not None:
        all_files = get_all_files(path_to_file_or_dir)
        for index in range(len(all_files["path"])):
            cur_file = all_files["path"][index]
            try:
                tree = load_code(cur_file)
            except Exception as e:
                failed_files += [[cur_file, e]]
                continue

            calls = analyse_calls(tree)
            imports = analyse_imports(tree)
            definitions = analyse_definitions(tree)
            structures = analyse_structures(tree)
            operations = analyse_operations(tree)

            cur_code_results = [calls, imports, definitions, structures, operations]

            successfull_files += [cur_file]

            if len(code_results) <= 0:
                code_results = cur_code_results
            else:
                code_results = merge_analysis_results(cur_code_results, code_results)

    # Analysis of given code_strs
    failed_code_strs = []
    successfull_code_strs = 0
    if code_strs is not None:
        for cur_code_str in code_strs:
            try:
                tree = ast.parse(cur_code_str, filename="", mode='exec')
            except Exception as e:
                failed_code_strs += [e]
                continue

            calls = analyse_calls(tree)
            imports = analyse_imports(tree)
            definitions = analyse_definitions(tree)
            structures = analyse_structures(tree)
            operations = analyse_operations(tree)

            cur_code_results = [calls, imports, definitions, structures, operations]

            successfull_code_strs += 1

            if len(code_results) <= 0:
                code_results = cur_code_results
            else:
                code_results = merge_analysis_results(cur_code_results, code_results)


    calls, imports, definitions, structures, operations = code_results
    analysis_str = create_analysis_str(name=name, calls=calls, 
                                       imports=imports, definitions=definitions, 
                                       structures=structures, operations=operations, 
                                       failed_files=failed_files, successfull_files=successfull_files,
                                       failed_code_strs=failed_code_strs, successfull_code_strs=successfull_code_strs,
                                       short_analysis=short_analysis)

    if should_print:
        print(analysis_str)

    if should_save:
        with open(os.path.join(save_path, "code_analysis.txt"), "w") as file:
            file.write(analysis_str)

    # Visualisation
    # if should_visualize:
    #     visualize(calls, imports, operations)

    return analysis_str


