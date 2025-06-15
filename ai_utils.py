# ai_utils.py
import ollama

def smart_rename_title(title: str) -> str:
    prompt = f"Rename this song I have to a proper format give only one result: '{title}'"
    try:
        response = ollama.chat(
            model='phi',
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content'].strip().strip('"')
    except Exception as e:
        print(f"⚠️ AI rename failed: {e}")
        return title  # fallback to original title
