from aibenchmark.categories.testing import evaluate_testing, list_testing_problems
from aibenchmark.providers import PROVIDERS

problem = list_testing_problems()[0]
print('Problem:', problem['id'])
print('Prompt:', problem['prompt'])

# Get the model response
provider_module = PROVIDERS['ollama']['module']
prompt = problem["prompt"] + "\n\nReturn only a single Python code block containing the test code, no prose."

result = provider_module.run_prompt('llama3.2', prompt)
print('Provider success:', result.success)
print('Provider error:', result.error_type)
print('Response length:', len(result.response))
print('Response preview:', result.response[:500])

if result.success:
    from aibenchmark.sandbox import extract_code
    test_code = extract_code(result.response)
    print('\nExtracted test code:')
    print(test_code)
    
    # Now run the mutant testing
    from aibenchmark.sandbox import run_mutant_tests_sandboxed
    ref_impl = problem["reference_implementation"]
    mutants = problem["mutants"]
    print('\nRunning mutant tests...')
    score = run_mutant_tests_sandboxed(
        "problems/testing", test_code, ref_impl, mutants
    )
    print(f'Score: {score}')