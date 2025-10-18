import requests

secret = os.environ.get("Secret")

def test():
    payload={
        "secret":secret,
        "round":1,
        "task":"task1",
        "brief":"Create a simple web app using Flask that displays 'Hello, World!' on the homepage.",
        "attachments":[]    
    }
    requests.post("https://rohit738-tds-project-1.hf.space/first_task",json=payload)

if __name__=="__main__":
    test()