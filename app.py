from fastapi import FastAPI
import os
import requests
import json
import base64

app = FastAPI()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
AIPIPE_TOKEN = os.environ.get("AIPIPE_TOKEN")

def send_tasks(tasks):
    example = {
        "repo_name": "generated-web-app",
        "files": [
            {"path": "README.md", "content": "# Example README\n\nHow to run"},
            {"path": "app.py", "content": "# main app file"},
        ],
    }

    prompt = {
        "instruction": (
            "You are a code generator. Input: a JSON object mapping task names to descriptions, "
            "which may include attachments. Each attachment may look like:\n"
            "{ \"name\": \"sample.png\", \"url\": \"data:image/png;base64,iVBORw...\" }\n\n"
            "Output MUST be a single valid JSON object (and NOTHING else) with the schema:\n"
            "{\n"
            "  \"repo_name\": \"string\",\n"
            "  \"files\": [ { \"path\": \"path/to/file\", \"content\": \"file contents\" } ]\n"
            "}\n\n"
            "Guidelines:\n"
            "- If any task contains attachments, decode the Base64 data and save each file appropriately "
            "(for example, 'static/sample.png').\n"
            "- Reference attached images from HTML files using correct relative paths (e.g., "
            "<img src=\"static/sample.png\" alt=\"sample image\">).\n"
            "- Include a README.md explaining how to run the app.\n"
            "- Do not wrap any file content in markdown code fences.\n"
            "- If decoding or inclusion fails, still include placeholder comments or TODOs in the code.\n"
            "- If you cannot implement something, still produce a stub file with TODO notes."
        ),
        "input_tasks": tasks,
        "example_output": example,
    }

    return json.dumps(prompt, indent=2)

def create_github_repo(repo_name:str):
    header={"Accept": "application/vnd.github+json","Authorization":f"Bearer {GITHUB_TOKEN}"}
    payload={"name":repo_name,"private":False,"auto_init":False,"license_template":"mit"}
    response=requests.post("https://api.github.com/user/repos", headers = header, json=payload)
    print("Create",response)

def create_files(repo_name, files):
    header={"Accept": "application/vnd.github+json","Authorization":f"Bearer {GITHUB_TOKEN}"}
    response={}
    for file in files:
        payload={"message":"Initial commit","content":file["content"],"branch":"main"}  
        response=requests.put(f"https://api.github.com/repos/ksrohit26/{repo_name}/contents/{file['path']}", headers = header, json=payload)
    print("Added",response)
    return response.json()['content']['sha']

def enable_github_pages(repo_name):
    header={"Accept": "application/vnd.github+json","Authorization":f"Bearer {GITHUB_TOKEN}"}  
    payload={"source":{"branch":"main","path":"/"}}
    response=requests.post(f"https://api.github.com/repos/ksrohit26/{repo_name}/pages", headers = header, json=payload)
    print("Enable",response)
    return response.json()['html_url']

def receive_response(tasks):
    header={"Content-Type":"application/json","Authorization":f"Bearer {AIPIPE_TOKEN}"}
    payload={"model":"openai/gpt-4.1-nano","input":send_tasks(tasks)}
    response=requests.post("https://aipipe.org/openrouter/v1/responses",headers=header,json=payload)
    print(response)
    return json.loads(response.json()['output'][0]['content'][0]['text'])

def encode_content(files):
    for i in files:
        i['content'] = base64.b64encode(i['content'].encode()).decode()
    return files

def validate(secret):
    if secret==os.environ.get("Secret"):
        return True
    return False

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/first_task")
def first_task(data: dict):
    if validate(data.get("secret", "")):
        if data.get("round", "") == 1:
            task={data.get("task",""):{"description":data.get("brief",""),"attachments":data.get("attachments",[])}}
            
            a=receive_response(task)
            name=a["repo_name"]
            b=encode_content(a['files'])

            create_github_repo(name)
            commit_sha=create_files(name,b)
            pages_url=enable_github_pages(name)

            payload={"email":data.get("email",""),"task":data.get("task",""),"round":1,"nonce":data.get("nonce",""),"repo_url":f"https://github.com/ksrohit26/{name}","commit_sha":commit_sha,"pages_url":pages_url}
            requests.post(data.get("evaluation_url","https://rohit738-tds-project-1.hf.space/first_task/test"),json=payload)
            requests.post("https://rohit738-tds-project-1.hf.space/first_task/test",json=payload)

            return {"Message": "Success"}

    return {"Message": "Failed"}

@app.post("/first_task/test")
def second_task(data: dict):
    print(data.get("repo_url",""),data.get("pages_url",""))
    return {"Message": "Success"}