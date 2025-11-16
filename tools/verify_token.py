import os
import sys
import json
from urllib import request, error
from dotenv import load_dotenv

# Prefer session env var; only load .env if not present
if not os.getenv('DISCORD_TOKEN'):
    load_dotenv()

token = os.getenv('DISCORD_TOKEN')
if not token:
    print('No DISCORD_TOKEN found in environment or .env')
    sys.exit(2)

token = token.strip()
if token.lower().startswith('bot '):
    token = token[4:].strip()

url = 'https://discord.com/api/v10/users/@me'
req = request.Request(url, headers={
    'Authorization': f'Bot {token}',
    'User-Agent': 'DiscordBot (verify, 1.0)'
})
try:
    with request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print('OK: token valid for bot user:', data.get('username'), '#', data.get('id'))
        sys.exit(0)
except error.HTTPError as e:
    body = e.read().decode('utf-8','ignore')
    print('HTTPError', e.code, body[:200])
    if e.code == 401:
        print('Result: 401 Unauthorized — token invalid or not a bot token')
    sys.exit(1)
except Exception as e:
    print('Error:', repr(e))
    sys.exit(1)
