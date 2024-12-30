#!/usr/bin/python3
import requests, sys
# curl -XPOST -H "Content-Type: application/json;charset=utf-8" 'https://open.larksuite.com/open-apis/bot/v2/hook/xxx' -d '{"msg_type": "text", "content": {"text": "test send."}}'

LARK_BOT_URL="LARK_WEB_HOOK"

def send_lark(text, parse_mode):
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    content = {"msg_type": parse_mode, "content": {"text": text}}
    req = requests.post(LARK_BOT_URL, headers=headers, json=content)
    if req.json()['code'] == 0:
        print("lark send ok.")
    else:
        print(f"lark send error, content: {content}, req: {req.json()}")

def main():
    if len(sys.argv) != 2:
        print("please input message.")
        sys.exit(110)
    print(len(sys.argv))
    text = sys.argv[1]
    send_lark(text, 'text')

if __name__ == "__main__":
    main()
