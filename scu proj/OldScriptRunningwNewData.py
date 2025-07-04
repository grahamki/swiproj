import csv
import os
import re
import pandas as pd
import ast
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file.")

client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {"role": "user", "content": "Hello!"}
  ]
)
print(response.choices[0].message)


LLM_Source = "OpenAI"
Model = "gpt-4o"
problem_num = -1
prompt = "No prompt has been entered yet"
full_output_list = []
algorithm_text_list = []
# This list will hold correctness values for each algorithm tested
# correctness_list = []


print("\nWelcome to the LLM leetcode Reasoning Tester!")

print("Reading datafile...")

try:
    # Attempt to read the Data file
    #df = pd.read_csv('Problem_Data.csv')
    df = pd.read_csv('BigData.csv')
    df.fillna("", inplace=True)  # Replaces null values with an empty string (fixes test case for question 1763)
    print("File 1 read successfully!")
except FileNotFoundError:
    print("Error: The file 'Problem_Data.csv' was not found.")
except pd.errors.EmptyDataError:
    print("Error: The file 'Problem_Data.csv' is empty.")
except Exception as e:
    print(f"An error occurred: {e}")



while True:
    option = -1
    option2 = -1
    while option < 0 or option > 6:
        try:
            option = int(input(f"""
    Enter 1 to select a new LLM. Current model: {Model}
    Enter 2 to select a new Leetcode Problem. Current problem: {problem_num}
    Enter 3 to select a new prompt.
    Enter 4 to generate and test algorithms
    Enter 5 to add the current information to the output report
    Enter 6 for more options
    Enter 0 to exit
    : """))
        except ValueError:
            print("Invalid input! Please enter a valid integer between 0 and 6.")

    if option == 0 or option2 == 0: #exit
        print("Thanks for testing!")
        break

    if option == 6:
        while option2 < 0 or option2 > 4:
            try:
                option2 = int(input(f"""
    Enter 1 to view your current prompt
    Enter 2 to view your current LLM code algorithm
    Enter 3 to view the full LLM response
    Enter 4 to go back to the main menu
    Enter 0 to exit
        : """))
            except ValueError:
                print("Invalid input! Please enter a valid integer between 0 and 4.")

    if option == 1: # get the LLM and model

        ###Add More LLM's here

        #LLM_Source = input("What organization's model would you like to use? \nCurrently OpenAI is the only org implemented")
        print("Currently OpenAI is the only model type configured")
        
        if LLM_Source == "OpenAI":
                if(api_key == ""):
                    api_key = input("Enter your OpenAI API key\n : ")
                    client = OpenAI(api_key=api_key)
                else:
                    new_key = input("Enter a new API key or enter 1 to continue using the current key\n : ")
                    if(new_key != 1):
                        api_key = new_key
                        client = OpenAI(api_key=api_key)

                Model = input("\nSelect which OpenAI model to use\n : ")
                
        problem = input("\nPress Enter to select a problem. To return to the main menu, type anything and press Enter: ")
        if problem != "":
            continue
        option = 2

    if option == 2: # get the problem number 
        testcases_gathered = False
        while not testcases_gathered:
            try:
                problem_num = int(input("\nEnter the index number of your problem: "))
            except ValueError:
                print("Please enter a valid integer.")
                continue

            argument_list = []
            expected_outputs = []
            print("Gathering testcases... ")

            for i in range(1, 4):  #range will be changed to length of testcases dictionary
                raw_input = df[f'Inputs_{i}'][problem_num-1]
                try:
                    code_input = ast.literal_eval(raw_input)
                    argument_list.append(code_input)  #Converts to a list ( must be a list)
                    testcases_gathered = True
                    print(f"Test case inputs {i}: {code_input}")
                except (ValueError, SyntaxError) as e:
                    print(f"Error gathering testcases: {raw_input}, \n Please pick a different problem: ") 
                    testcases_gathered = False
                    break
                output_code = df[f'Output_{i}'][problem_num-1]
                expected_outputs.append(output_code)
                print(f"Test case outputs {i}: {output_code}")
            
        print("Testcases successfully gathered!")

        new_prompt = input("\nPress Enter to select a prompt. To return to the main menu, type anything and press Enter: ")
        if new_prompt != "":
            continue
        option = 3

    if option == 3: # get the prompt
        prompt = input("\nEnter a new prompt, or leave empty to use the default prompt in the database.\n : ")
        if prompt == "":
            prompt = df["Example_Prompt_Full"][problem_num-1]

        instructions = """
Provide the Python code solution and ensure the code is wrapped as follows:
1. Place **three hashtags (###)** on a separate line immediately before the function definition.
2. Place **three hashtags (###)** on a separate line immediately after the last line of code.

Do not use three hashtags anywhere else in the response. Only use them to wrap the code block.
        """
        final_prompt = prompt + instructions

        print ("here is your final prompt:\n", final_prompt, "\n")

        run = input("\nPress Enter to run the model on the prompt. To return to the main menu, type anything and press Enter:  ")
        if run != "":
            continue
        option = 4

    if option == 4: #run the model on the prompt
        
        Queries = int(input("Enter the number of algorithms you would like to generate: "))

        

        successful_outputs = 0
        correctness_list = []

        for i in range(Queries):
            print(f'\n\nWaiting for model to generate response {i+1}...')
            if LLM_Source == "OpenAI":
                ### API Call to get LLM output
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": final_prompt,
                        }
                    ],
                    model=Model,  #gpt-4o-mini is good too and less expensive
                )
                full_output = chat_completion.choices[0].message.content

            ###add more LLM's here

            print("Parsing response...")

            code_output = re.search(r"###(.*?)###", full_output, re.DOTALL)
            if code_output:
                algorithm_text = code_output.group(1)
                print(f"Here is the generated code algorithm:\n{algorithm_text}")
            else:
                print("No code within ### found\n")
                print("Here was the full response:\n", full_output)
                continue
            
            try:
                # Attempt to parse the algorithm_text using AST
                tree = ast.parse(algorithm_text)
                
                # Get the function name from the parsed tree
                function_name = None
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_name = node.name
                        break

                if function_name is None:
                    print(f"No function definition found in LLM response #{i}. This output will not be used")
                    continue

            except SyntaxError as e:
                print(f"SyntaxError while parsing the code: {e}")
                print(f"LLM output #{i} may not be valid Python code. This response will not be used.")
                continue
            except Exception as e:
                print(f"An unexpected error occurred in LLM response #{i}: {e}. This response will not be used")
                continue
            
            successful_outputs += 1
            full_output_list.append(full_output)
            algorithm_text_list.append(code_output)

            print("Testing response...")
            correctness = 1
            passed = True

            # Execute the algorithm directly in the global namespace
            exec(algorithm_text)

            # Access the function dynamically using the extracted function name
            function = globals()[function_name]

            # Testing with inputs from dataframe
            print(f'Response {i+1}: ')
            try:
                for j in range(3):  #range will be changed to length of testcases dictionary
                    result = str(function(*argument_list[j]))  # Old function call with no multiprocessing

                    ### Code below to handle differences in boolean values for csv vs pandas
                    result = result.replace("True", "TRUE").replace("False", "FALSE")

                    # Compare the result with the expected output
                    print(f"Test case {j+1} result: {result}, Expected: {expected_outputs[j]}")

                    if result != expected_outputs[j]:
                        print(f"Failed test case {j+1}")
                        passed = False

            except Exception as e:
                print(f"Error during test execution: {e}")
                passed = False

            if not passed:
                correctness = 0

            if correctness == 1:
                print("Passed all testcases!")
            
            correctness_list.append(correctness)

        add_to_report = input("\nPress Enter to add results to the report. To return to the main menu, type anything and press Enter:  ")
        if add_to_report != "":
            continue
        option = 5

    if option == 5: #add to report
        if len(correctness_list) == 0:
            print("No results to add to report yet!")
            continue

        prompt_upload = prompt.replace("\n", " ")
        tested_problem = df.iloc[problem_num-1,0]
        for i in range(successful_outputs):
            data = [
                tested_problem,
                prompt_upload,  # Replace newlines with a space or another placeholder
                Model,
                correctness_list[i]
            ]

            print("\nWriting to csv...")
            try:
                file_exists = os.path.isfile("BigDataReport.csv")
                with open("BigDataReport.csv", "a", newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(data)
            except Exception as e:
                print(f"An error occurred: {e}")

        print("Data successfully written!")

    if option2 == 1: #print the prompt
        print("\n",final_prompt,"\n")
        continue

    if option2 == 2: #print current code
        print("Here are your current algorithms: ")
        for i in range(len(full_output_list)):
            print(f"Algorithm {i}:\n{full_output_list[i]}")
        continue

    if option2 == 3: #print full output
        print("Here are your current LLM responses: ")
        for i in range(len(algorithm_text_list)):
            print(f"Output {i}:\n{algorithm_text_list[i]}")
