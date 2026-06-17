import os
import argparse
from google.genai import types
from dotenv import load_dotenv
from google import genai
from prompts import system_prompt
from call_function import available_functions, call_function


load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if api_key is None:
    raise RuntimeError("GEMINI_API_KEY not found in environment variables.")


parser = argparse.ArgumentParser(description="Chatbot")
parser.add_argument("user_prompt", type=str, help="User prompt")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
args = parser.parse_args()
    
messages: list[types.Content] = [
    types.Content(role="user", parts=[types.Part(text=args.user_prompt)])
]

def generate_content(client, messages) -> types.GenerateContentResponse:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=messages,
        config=types.GenerateContentConfig(
            tools=[available_functions], system_instruction=system_prompt
        )
    )
    return response
client = genai.Client(api_key=api_key)
response = generate_content(client, messages)

if response.usage_metadata is None:
    raise RuntimeError("Usage metadata is missing from the response.")

if args.verbose:
    print(f"User prompt: {args.user_prompt}",)
    print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}",)
    print(f"Response tokens: {response.usage_metadata.candidates_token_count}",)

if not response.function_calls:
    print(f"Response:\n{response.text}",)
else:
    function_results = []
    for function_call in response.function_calls:
        function_response = call_function(function_call, args.verbose)
        if not function_response.parts:
            raise Exception("Error: No parts in function call result.")
        if function_response.parts[0].function_response is None:
            raise Exception("Error: No response in function call result.")
        if function_response.parts[0].function_response.response is None:
            raise Exception("Error: No response in function call result.")
        function_results.append(function_response.parts[0])
        if args.verbose:
            print(f"-> {function_results[-1].function_response.response}")