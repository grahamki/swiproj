import csv
print("done1")
import os
print("done1")
import re
print("done1")
import pandas as pd
print("done1")
import ast
print("done1")
import re
print("done1")
from openai import OpenAI
print("done1")
import nltk
print("done1")
from nltk.corpus import wordnet
print("done1")
from keybert import KeyBERT
print("done1")

#nltk.download('wordnet') ### comment out this line if already downloaded
#nltk.download('punkt_tab') ### comment out this line if already downloaded

print("\nWelcome to the LLM leetcode Reasoning Tester!")

print("Reading datafile...")

try:
    # Attempt to read the CSV file
    df = pd.read_csv('test_problems.csv')
    df.fillna("", inplace=True)  # Replaces null values with an empty string (fixes test case for question 1763)
    print("File 1 read successfully!")
except FileNotFoundError:
    print("Error: The file 'test_problems.csv' was not found.")
except pd.errors.EmptyDataError:
    print("Error: The file 'test_problems.csv' is empty.")
except Exception as e:
    print(f"An error occurred: {e}")

try:
    lexicon = pd.read_csv('SUBTLEXus74286wordstextversion.txt', sep='\t')
    print("File 2 read successfully!")
except FileNotFoundError:
    print("Error: The lexicon was not found.")
except pd.errors.EmptyDataError:
    print("Error: The lexicon file is empty.")
except Exception as e:
    print(f"An error occurred: {e}")

LLM_Source = "None selected yet"
Model = "None selected yet"
problem_num = -1
prompt = "No prompt has been entered yet"
original_prompt = ""
prompt_portion = ""
algorithm_text = "No algorithm has been generated yet"
full_output = "No LLM output has been generated yet"
api_key = ""

selectedwords = []
newwords = []

while True:
    option = -1
    option2 = -1
    while option < 0 or option > 8:
        try:
            option = int(input(f"""
    Enter 1 to select a new LLM. Current model: {Model}
    Enter 2 to select a new Leetcode Problem. Current problem: {problem_num}
    Enter 3 to select a new prompt.
    Enter 4 to replace some key word phrases in your prompt.
    Enter 5 to generate a new output with your current LLM, Problem and Prompt
    Enter 6 to test the output on the current problem
    Enter 7 to add the current information to the results csv
    Enter 8 for more options
    Enter 0 to exit
    : """))
        except ValueError:
            print("Invalid input! Please enter a valid integer between 0 and 8.")

    if option == 8:
        while option2 < 0 or option2 > 5:
            try:
                option2 = int(input(f"""
    Enter 1 to manually enter a different coding algorithm
    Enter 2 to view your current prompt
    Enter 3 to view your current LLM code output
    Enter 4 to view the full LLM output
    Enter 5 to go back to the main menu
    Enter 0 to exit
        : """))
            except ValueError:
                print("Invalid input! Please enter a valid integer between 0 and 5.")

    if option == 0 or option2 == 0: #exit
        print("Thanks for testing!")
        break

    if option == 1: # get the LLM and model

        ###Add More LLM's here

        #LLM_Source = input("What ai organizaton would you like to use? \nCurrently OpenAI is the only org implemented")
        print("Currently OpenAI is the only org implemented")

        LLM_Source = "OpenAI"
        api_key = "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"
        client = OpenAI(api_key=api_key)
        Model = "gpt-4o"
        """
        if LLM_Source == "OpenAI":
                if(api_key == ""):
                    api_key = input("Enter your OpenAI API key\n : ")
                    client = OpenAI(api_key=api_key)
                else:
                    new_key = input("Enter a new API key or press enter to continue using the current key\n : ")
                    if(new_key != api_key):
                        api_key = new_key
                        client = OpenAI(api_key=api_key)

                Model = input("\nSelect which OpenAI model to use. Valid options are gpt-4, gpt-4-turbo, gpt-4o, gpt-4o-mini, gpt-3.5-turbo\n : ")
        
                
        problem = input("\nEnter 1 to select a new Leetcode problem, Enter anything else to go back to menu: ")
        if problem != "1":
            problem = ""
            continue
        option = 2
        problem = ""
        """
        option = 2

    if option == 2: # get the problem number 
        while True:
            try:
                problem_num = int(input("\nEnter the problem index number in the CSV you want to solve (1-30): "))
                if 1 <= problem_num <= 30:
                    break  # Exit the loop if the input is valid
                else:
                    print("Invalid input! Please enter a valid integer between 1 and 30.")
            except ValueError:
                print("Invalid input! Please enter a valid integer between 1 and 30.")

        """
        new_prompt = input("\nEnter 1 to select a new prompt, Enter anything else to go back to menu: ")
        if new_prompt != "1":
            new_prompt = ""
            continue
        option = 3
        new_prompt = ""
        """
        option = 3

    if option == 3: # get the prompt
        """
        prompt = input("\nEnter a new prompt, or leave empty to use the default prompt in the csv.\n : ")
        prompt_portion = prompt
        if prompt == "":

            prompt = df["Example_Prompt_Full"][n-1]
            prompt_portion = df["Example_Prompt_Question"][n-1]

            print ("here is your default prompt:\n", prompt, "\n")
        """
        prompt = df["Example_Prompt_Full"][problem_num-1]
        prompt_portion = df["Example_Prompt_Question"][problem_num-1]

        print ("here is your default prompt:\n", prompt, "\n")
        
        original_prompt = prompt
        selectedwords = []
        run = input("\nEnter 1 to replace key word phrases in the prompt, Enter anything else to go back to menu: ")
        if run == "1":
            run = ""
            option = 4
        else:
            run = ""
            continue

    if option == 4: #replace keywords

        if prompt == "No prompt has been entered yet":
            print(prompt)
            continue

        if selectedwords:
            print("You have already replaced some keywords")
            replace = int(input("Enter 1 to replace different keywords in the unmodified prompt, enter anything else to go back to menu: "))
            if replace == 1:
                prompt = original_prompt
            else:
                continue

        print("\nExtracting keywords...")

        kw_model = KeyBERT()
        keywords = kw_model.extract_keywords(prompt_portion, top_n=20)

        print("Here are your most important keywords and their importance scores: ")

        for i in range(len(keywords)):
            print(f'{i+1}: {keywords[i][0]}, score: {keywords[i][1]}')
        
        numwords = int(input("\nHow many of these word phrases would you like to replace with synonyms?: "))

        selectedwords = []
        selectedwords_freqs = []
        selectedwords_importances = []
        selectedwords_ranks = []
        for i in range(numwords):
            nextword = int(input(f'select the index of the word you want (1-20). Select {numwords-i} more: '))
            selectedwords.append(keywords[nextword-1][0])
            selectedwords_importances.append(keywords[nextword-1][1])
            selectedwords_ranks.append(nextword)

        newwords = []
        newwords_freqs = []
        for i in range(numwords):
            print(f'\nHere is a list of synonyms for the word {selectedwords[i]}: ')
            synonym_set = set()
            synonym_list = []

            for syn in wordnet.synsets(selectedwords[i]):
                for l in syn.lemmas():
                    w = l.name()
                    if w.lower() != selectedwords[i].lower():
                        synonym_set.add(w)

            if len(synonym_set) == 0:
                print(f'No synonyms were found for {selectedwords[i]}')
                replace_nym = input("Enter your own synonym: ")
                newwords.append(replace_nym)
                continue
            
            j = 0
            for item in synonym_set:
                synonym_list.append(item)
                print(f'{j+1}: {item}')    
                j += 1

            new_index = int(input("\nselect the index of the synonym you want to use, or -1 to write your own synonym: "))
            if new_index == -1:
                new_nym = input("Enter your new synonym to be used: ")
                newwords.append(new_nym)
            else:
                newwords.append(synonym_list[new_index-1])

        print("\nHere are the word frequencies of your original words")

        for word in selectedwords:
            if word in lexicon['Word'].values:
                freq = lexicon.loc[lexicon['Word'] == word, 'FREQcount'].values[0]
                selectedwords_freqs.append(freq)
                print(f'{word}: {freq}')
            else:
                selectedwords_freqs.append(0)
                print(f'{word}: 0')

        print("\nHere are the word frequencies of your new words")

        for nym in newwords:
            if nym in lexicon['Word'].values:
                freq2 = lexicon.loc[lexicon['Word'] == nym, 'FREQcount'].values[0]
                newwords_freqs.append(freq2)
                print(f'{nym}: {freq2}')
            else:
                newwords_freqs.append(0)
                print(f'{nym}: 0')

        print("\nReplcing words with synonyms in your prompt...")

        if len(selectedwords) != len(newwords):
            raise ValueError("The words and synonyms lists must be of the same length.")

        wordsreplaced = 0
        for word, synonym in zip(selectedwords, newwords):
            # Use a regular expression for case-insensitive replacement
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            matches = len(re.findall(pattern, prompt))  # Count matches in a case-insensitive way
            if matches > 0:
                # Replace all instances of the word with its synonym
                prompt = pattern.sub(synonym, prompt)
                # Increment the counter by the number of replacements
                wordsreplaced += matches

        print(f'{wordsreplaced} words were replaced')

        print(f'\nHere is your new prompt:\n{prompt}')

        run = input("\nEnter 1 to run the current model on the prompt 10 times or Enter anything else to go back to menu: ")
        if run == "1":
            run = ""
            option = 5
        else:
            run = ""
            continue

    if option == 5: #run the model on the prompt 10 times
        

        instructions = """
Provide the Python code solution and ensure the code is wrapped as follows:
1. Place **three hashtags (###)** on a separate line immediately before the function definition.
2. Place **three hashtags (###)** on a separate line immediately after the last line of code.

Do not use three hashtags anywhere else in the response. Only use them to wrap the code block.
        """

        final_prompt = prompt + instructions

        output_list = []
        function_name_list = []

        for i in range(10):
            print(f'generating output {i+1}...')
            if LLM_Source == "OpenAI":
                ### API Call to get ChatGPT output
                # Send the request to ChatGPT
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

            else:
                print(f"invalid LLM Source, current LLM Source is: {LLM_Source}\n")
                continue

            #print("output generated...")

            code_output = re.search(r"###(.*?)###", full_output, re.DOTALL)

            if code_output:
                algorithm_text = code_output.group(1)
                output_list.append(algorithm_text)
                #print("\nExtracted code from output:", algorithm_text)
            else:
                print("No code within ### found\n")
                print("Here was the full output:\n", full_output)
                continue
            
            try:
                # Attempt to parse the algorithm_text using AST
                tree = ast.parse(algorithm_text)
                
                # Get the function name from the parsed tree
                function_name = None
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_name = node.name
                        function_name_list.append(function_name)
                        break

                if function_name is None:
                    print("No function definition found in the provided algorithm string. Please generate a new output or manually enter an output.")
                    continue

            except SyntaxError as e:
                print(f"SyntaxError while parsing the code: {e}")
                print("The provided algorithm string may not be valid Python code. Please generate a new output or manually enter an output.")
                continue
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                continue

        test = input("\nEnter 1 to test the output on the testcases, Enter anything else to go back to menu: ")
        if test != "1":
            test = ""
            continue
        test = ""
        option = 6
    
    if option2 == 1: #enter a manual algorithm
        print("\nPaste your algorithm below (end with a single line containing three hashtags ###):")

        user_input = []
        while True:
            line = input()
            if line.strip().upper() == "###":  # Stop input on "END"
                break
            user_input.append(line)

        algorithm_text = "\n".join(user_input)  # Combine lines into a single string

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
                print("No function definition found in the provided algorithm string. Please generate a new output or manually enter an output.")
                continue

        except SyntaxError as e:
            print(f"SyntaxError while parsing the code: {e}")
            print("The provided algorithm string may not be valid Python code. Please generate a new output or manually enter an output.")
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            continue
        
        test = input("\nEnter 1 to test the output on the testcases, Enter anything else to go back to menu: ")
        if test != "1":
            test = ""
            continue
        test = ""
        option = 6

    if option == 6: #test the output on the testcases
        correctness_list = []
        for j in range(10):
            correctness = 1
            # Execute the algorithm directly in the global namespace
            exec(output_list[j])

            # Access the function dynamically using the extracted function name
            function = globals()[function_name_list[j]]

            # Testing with inputs from dataframe
            passed = True
            print(f'Output {j+1}: ')
            try:
                for i in range(1, 4):  # Test Inputs_1, Inputs_2, Inputs_3
                    raw_input = df[f'Inputs_{i}'][problem_num-1]  # Already formatted as a list
                    #print(f"Raw arguments for test case {i}: {raw_input}")

                    try:
                        arguments = ast.literal_eval(raw_input)  # Converts to a list

                        if not isinstance(arguments, list):
                            raise ValueError(f"Expected a list, but got {type(arguments)}")
                    except (ValueError, SyntaxError) as e:
                        raise ValueError(f"Error parsing input: {raw_input}") from e

                    result = str(function(*arguments))  # Old function call with no multiprocessing
                    
                    ### Code below to handle differences in boolean values for csv vs pandas
                    result = result.replace("True", "TRUE").replace("False", "FALSE")

                    # Compare the result with the expected output
                    expected_output = df[f'Output_{i}'][problem_num-1]
                    print(f"Test case {i} result: {result}, Expected: {expected_output}")

                    if result != expected_output:
                        print(f"Failed test case {i}")
                        correctness -= (1/3)
                        passed = False
            except Exception as e:
                print(f"Error during test execution: {e}")
                passed = False

            if passed:
                print("Passed all 3 test cases!")

            correctness_list.append(correctness)

        option = 7

    if option == 7: #add to csv
        if prompt == "No prompt has been entered yet":
            print(prompt)
            continue
        if algorithm_text == "No algorithm has been generated yet":
            print(algorithm_text)
            continue
        if correctness == -1:
            print("algorithm has not been tested on testcases yet")
            continue

        difference_frequencies = []

        for i in range(len(selectedwords_freqs)):
            difference_frequencies.append(selectedwords_freqs[i] - newwords_freqs[i])

        prompt_upload = prompt.replace("\n", " ")

        for i in range (10):
            data = [
                df.iloc[problem_num-1,0],
                prompt_upload,  # Replace newlines with a space or another placeholder
                selectedwords,
                selectedwords_importances,
                selectedwords_ranks,
                selectedwords_freqs,
                newwords,
                newwords_freqs,
                difference_frequencies,
                wordsreplaced,
                len(newwords),
                correctness_list[i],
            ]

            print("\nWriting to csv...")
            try:
                file_exists = os.path.isfile("keyword_imp_results.csv")
                with open("keyword_imp_results.csv", "a", newline='') as csvfile:
                    writer = csv.writer(csvfile)

                    # Write the data row
                    writer.writerow(data)
                print("Data successfully written!")
            except Exception as e:
                print(f"An error occurred: {e}")

    if option2 == 2: #print the prompt
        print("\n",prompt,"\n")
        continue

    if option2 == 3: #print current code
        print("\n",algorithm_text,"\n")
        continue

    if option2 == 4: #print full output
        print("\n",full_output,"\n")
