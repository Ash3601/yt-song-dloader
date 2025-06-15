import ollama
original_title = 'Taras | Munjya | Sharvari & Abhay Verma | Sachin-Jigar, Jasmine Sandlas | Amitabh Bhattacharya'
ai_prompt = f"Rename this song I have to a proper format give only one result: '{original_title}'"

response = ollama.chat(
    model='phi',
    messages=[{'role': 'user', 'content': ai_prompt}]
)
print(response['message']['content'])
