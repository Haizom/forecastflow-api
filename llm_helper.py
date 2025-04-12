import requests

API_KEY = "2e88e11724ee0a42480543ef3f0f6cde7e6a7307e08626a17aca00038032e96f"
TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"

def summarize_changepoints(prompt: str):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes changepoints in time series."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    response = requests.post(TOGETHER_URL, headers=headers, json=body)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"[LLM Error] {response.status_code}: {response.text}"
