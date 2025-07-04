import csv
import os
import re
import pandas as pd
import ast
from openai import OpenAI
from dotenv import load_dotenv

# --- Setup API key and client from .env file (OpenAI only for now) ---
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file.")
client = OpenAI(api_key=api_key)

LLM_Source = "OpenAI"
Model = "gpt-4o"

# --- Read your dataset (BigData.csv) into a pandas DataFrame ---
try:
    df = pd.read_csv('BigData.csv')
    df.fillna("", inplace=True)
except Exception as e:
    print(f"Error loading data: {e}")
    exit(1)

# ============= NEW SECTION: DATA STRUCTURE HELPERS =============

# --- Linked List helper ---
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def list_to_linkedlist(lst):
    """Converts a list to a ListNode linked list."""
    dummy = ListNode()
    curr = dummy
    for val in lst:
        curr.next = ListNode(val)
        curr = curr.next
    return dummy.next

def is_linked_list_problem(prompt):
    """Detect if the problem needs ListNode inputs."""
    keywords = ["linked list", "ListNode"]
    prompt_lower = prompt.lower()
    return any(kw in prompt_lower for kw in keywords)

# --- Binary Tree helper ---
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def list_to_btree(lst):
    """
    Converts a list to a binary tree (TreeNode), using level-order.
    Supports [1,2,3,null,4] style (use None for nulls).
    """
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

def is_tree_problem(prompt):
    """Detect if the problem needs TreeNode inputs."""
    keywords = ["binary tree", "TreeNode", "BST", "root.left", "root.right"]
    prompt_lower = prompt.lower()
    return any(kw in prompt_lower for kw in keywords)

# ============= END DATA STRUCTURE HELPERS =============

# --- Test case parser: Returns list of arguments and outputs for this row ---
def get_test_cases(row, convert_linkedlist=False, convert_tree=False):
    """
    For each of the three test cases, parse input from CSV (as string).
    Convert input lists to ListNode or TreeNode as needed.
    """
    argument_list = []
    expected_outputs = []
    for i in range(1, 4):
        raw_input = row[f'Inputs_{i}']
        try:
            code_input = ast.literal_eval(raw_input)
            # Linked list handling
            if convert_linkedlist and isinstance(code_input, list):
                code_input = [list_to_linkedlist(code_input)]
            # Binary tree handling
            elif convert_tree and isinstance(code_input, list):
                code_input = [list_to_btree(code_input)]
            argument_list.append(code_input)
        except (ValueError, SyntaxError):
            argument_list.append([])
        expected_outputs.append(row[f'Output_{i}'])
    return argument_list, expected_outputs



# --- Core: Ask LLM for solution, run/test it, report correctness for each attempt ---
def run_model(prompt, Model, Queries, argument_list, expected_outputs, convert_linkedlist, convert_tree):
    """
    For each query, get LLM code, extract function, run it on all test cases.
    Returns: List of (correctness, error_flag)
    """
    results = []
    for i in range(Queries):
        print(f'\nGenerating response {i+1}...')
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=Model,
        )
        full_output = chat_completion.choices[0].message.content

        # --- Warn if LLM suggests 3rd-party packages like sortedcontainers
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
                if isinstance(args, (list, tuple)) and not isinstance(args, str):
                    output = function(*args)
                else:
                    output = function(args)

                # Normalize outputs for structure comparison
                expected = expected_outputs[j]
                # Handle string-to-list for expected
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

                # Handle boolean case
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
        # Decide which flag to use for this run:
        if error_flag == 'E':
            if convert_linkedlist and convert_tree:
                ll_tree_flag = 'LT'
            elif convert_linkedlist:
                ll_tree_flag = 'L'
            elif convert_tree:
                ll_tree_flag = 'T'
            else:
                ll_tree_flag = ''
            ll_tree_flag = 'E'  # Error takes precedence
        else:
            if convert_linkedlist and convert_tree:
                ll_tree_flag = 'LT'
            elif convert_linkedlist:
                ll_tree_flag = 'L'
            elif convert_tree:
                ll_tree_flag = 'T'
            else:
                ll_tree_flag = ''
        results.append((correctness, ll_tree_flag))
    return results


# --- Save results to CSV ---
def add_results_to_report(all_results):
    with open("BigDataReport.csv", "a", newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in all_results:
            writer.writerow(row)

# --- Main menu loop: select model, test, or exit ---
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

            # --- Detect what kind of input conversion is needed for this problem ---
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
Provide the Python code solution and ensure the code is wrapped as follows:
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
