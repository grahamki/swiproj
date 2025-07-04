import csv
import os
import re
import pandas as pd
import ast
from openai import OpenAI
from dotenv import load_dotenv

# === SETUP ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file.")
client = OpenAI(api_key=api_key)

Model = "gpt-4o"

# === DATA ===
try:
    df = pd.read_csv('BigData.csv')
    df.fillna("", inplace=True)
except Exception as e:
    print(f"Error loading data: {e}")
    exit(1)

# === HELPERS ===

class ListNode:
    def __init__(self, *args, **kwargs):
        # Supports ListNode(x), ListNode(val=x), ListNode(x, next=...)
        if len(args) == 1:
            self.val = args[0]
            self.next = kwargs.get('next', None)
        elif len(args) == 2:
            self.val = args[0]
            self.next = args[1]
        elif 'val' in kwargs:
            self.val = kwargs['val']
            self.next = kwargs.get('next', None)
        else:
            self.val = 0
            self.next = None

def list_to_linkedlist(lst):
    dummy = ListNode(0)
    curr = dummy
    for val in lst:
        curr.next = ListNode(val)
        curr = curr.next
    return dummy.next

def linkedlist_to_list(node):
    result = []
    while node:
        result.append(node.val)
        node = node.next
    return result

def is_linked_list_problem(prompt):
    keywords = ["linked list", "ListNode"]
    prompt_lower = prompt.lower()
    return any(kw in prompt_lower for kw in keywords)

def convert_linked_list_inputs(code_input):
    # [[...], [...]] -> [ListNode, ListNode]; [...] -> [ListNode]; else pass
    if isinstance(code_input, list) and all(isinstance(x, list) for x in code_input):
        return [list_to_linkedlist(x) for x in code_input]
    elif isinstance(code_input, list):
        return [list_to_linkedlist(code_input)]
    else:
        return [code_input]

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def list_to_btree(lst):
    if not lst or lst[0] is None:
        return None
    nodes = [TreeNode(val) if val is not None else None for val in lst]
    kids = nodes[::-1]
    root = kids.pop()
    for node in nodes:
        if node:
            if kids: node.left = kids.pop()
            if kids: node.right = kids.pop()
    return root

def treenode_to_list(root):
    from collections import deque
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    while result and result[-1] is None:
        result.pop()
    return result

def is_tree_problem(prompt):
    keywords = ["binary tree", "TreeNode", "BST", "root.left", "root.right"]
    prompt_lower = prompt.lower()
    return any(kw in prompt_lower for kw in keywords)

def convert_tree_inputs(code_input):
    if (
        isinstance(code_input, list) and
        any(isinstance(x, list) for x in code_input)
    ):
        return [list_to_btree(x) if isinstance(x, list) else x for x in code_input]
    elif isinstance(code_input, list):
        return [list_to_btree(code_input)]
    else:
        return [code_input]

# === TEST CASE HANDLING ===

def get_test_cases(row, convert_linkedlist=False, convert_tree=False):
    argument_list = []
    expected_outputs = []
    for i in range(1, 4):
        raw_input = row[f'Inputs_{i}']
        try:
            code_input = ast.literal_eval(raw_input)
            if convert_linkedlist:
                code_input = convert_linked_list_inputs(code_input)
            elif convert_tree:
                code_input = convert_tree_inputs(code_input)
            # Ensure: if input is not a list/tuple, wrap in a list for unpacking
            if not isinstance(code_input, (list, tuple)):
                code_input = [code_input]
            argument_list.append(code_input)
        except Exception as e:
            print(f"Could not parse input: {raw_input} - Error: {e}")
            argument_list.append([])
        expected_outputs.append(row[f'Output_{i}'])
    return argument_list, expected_outputs

# === MODEL RUNNER ===

def run_model(prompt, Model, Queries, argument_list, expected_outputs, convert_linkedlist, convert_tree):
    results = []
    for i in range(Queries):
        print(f'\nGenerating response {i+1}...')
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=Model,
        )
        full_output = chat_completion.choices[0].message.content

        if "sortedcontainers" in full_output or "import SortedList" in full_output:
            print("WARNING: LLM output tries to use 3rd-party packages (e.g. sortedcontainers). This may fail unless the package is installed.")

        code_output = re.search(r"###(.*?)###", full_output, re.DOTALL)
        if not code_output:
            print("No code within ### found\n")
            print("Full response:\n", full_output)
            continue
        algorithm_text = code_output.group(1)
        try:
            tree = ast.parse(algorithm_text)
            function_name = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_name = node.name
                    break
            if function_name is None:
                print(f"No function definition found. Skipping.")
                continue
        except Exception as e:
            print(f"Code parse error: {e}. Skipping.")
            continue
        correctness = 1
        passed = True
        error_flag = None
        try:
            exec(algorithm_text, globals())
            function = globals()[function_name]
            for j in range(3):
                args = argument_list[j]
                print(f"Test {j+1}: Passing args: {args} (types: {[type(x) for x in args]})")
                # Always unpack
                output = function(*args)
                expected = expected_outputs[j]
                if isinstance(expected, str):
                    try:
                        expected = ast.literal_eval(expected)
                    except:
                        pass
                if convert_linkedlist:
                    result = linkedlist_to_list(output)
                elif convert_tree:
                    result = treenode_to_list(output)
                else:
                    result = output
                # Boolean fix
                if isinstance(expected, str):
                    if expected.lower() == "true":
                        expected = True
                    elif expected.lower() == "false":
                        expected = False
                if result != expected:
                    passed = False
        except Exception as e:
            print(f"Test execution error: {e} -- This is common for linked list/tree problems if outputs/inputs are not normalized properly.")
            passed = False
            error_flag = 'E'
        if not passed:
            correctness = 0
        if error_flag == 'E':
            ll_tree_flag = 'E'
        elif convert_linkedlist and convert_tree:
            ll_tree_flag = 'LT'
        elif convert_linkedlist:
            ll_tree_flag = 'L'
        elif convert_tree:
            ll_tree_flag = 'T'
        else:
            ll_tree_flag = ''
        results.append((correctness, ll_tree_flag))
    return results

def add_results_to_report(all_results):
    with open("BigDataReport.csv", "a", newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in all_results:
            writer.writerow(row)

# === MAIN MENU ===
while True:
    try:
        option = int(input(
            f"""
Enter 1 to select a new LLM/API key. Current model: {Model}
Enter 2 to test problems and add results to report at the end
Enter 0 to exit
: """))
    except ValueError:
        print("Invalid input! Please enter 0, 1, or 2.")
        continue

    if option == 0:
        print("Thanks for testing!")
        break

    if option == 1:
        print("Currently OpenAI is the only model type configured.")
        new_key = input("Enter a new API key or enter 1 to continue using the current key:\n: ")
        if new_key != "1":
            api_key = new_key
            client = OpenAI(api_key=api_key)
        Model = input("\nSelect which OpenAI model to use (default is gpt-4o):\n: ") or "gpt-4o"
        continue

    if option == 2:
        try:
            num_problems_str = input(
                f"\nEnter the number of problems to test (1-{len(df)}). Press Enter to test all: "
            ).strip()
            if num_problems_str == "":
                num_problems = len(df)
                start_idx = 0
            else:
                num_problems = int(num_problems_str)
                start_idx = int(input(f"Enter the starting index (0 for first problem): ").strip() or "0")
            assert 0 <= start_idx < len(df)
        except Exception as e:
            print(f"Error: {e}")
            continue

        try:
            queries_str = input("Enter the number of algorithms to generate for each problem: ").strip()
            Queries = int(queries_str) if queries_str else 1
        except Exception:
            print("Invalid number. Defaulting to 1 query per problem.")
            Queries = 1

        all_results = []
        for idx in range(start_idx, min(start_idx + num_problems, len(df))):
            row = df.iloc[idx]
            problem_id = row.get('Question_Number', idx+1)
            print(f"\nTesting problem {problem_id} (index {idx+1})")
            prompt = row.get("Example_Prompt_Full", "")
            convert_linkedlist = is_linked_list_problem(prompt)
            convert_tree = is_tree_problem(prompt)
            if convert_linkedlist:
                print("Detected linked list problem. Will convert input lists to ListNode objects.")
            if convert_tree:
                print("Detected tree problem. Will convert input lists to TreeNode objects.")
            argument_list, expected_outputs = get_test_cases(
                row,
                convert_linkedlist=convert_linkedlist,
                convert_tree=convert_tree
            )
            instructions = """
- The function signature should use the provided class definitions for ListNode or TreeNode.
- Do not parse the input from string or list. Assume arguments are ListNode or TreeNode objects.
- Do not call .split(), eval(), or ast.literal_eval() on the input.
- Only process the data structure directly (e.g., root, root.left, etc).
1. Place **three hashtags (###)** on a separate line immediately before the function definition.
2. Place **three hashtags (###)** on a separate line immediately after the last line of code.
Do not use three hashtags anywhere else in the response. Only use them to wrap the code block.
"""
            final_prompt = prompt + instructions
            results = run_model(
                final_prompt, Model, Queries, argument_list, expected_outputs,
                convert_linkedlist, convert_tree
            )
            for correctness, ll_tree_flag in results:
                all_results.append([
                    problem_id,
                    prompt.replace("\n", " "),
                    Model,
                    correctness,
                    ll_tree_flag
                ])
        print("\nTesting complete.")
        save = input("Press Enter to save all results to BigDataReport.csv, or type anything else to discard: ").strip()
        if save == "":
            add_results_to_report(all_results)
            print("Results written to BigDataReport.csv!")
        else:
            print("Results discarded.")
        print("Done!")
