import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']
TRIAGE_ID = "C02NT3DTRF1"

message_counts = {}

# test to see if bot connects to channel
#client.chat_postMessage(channel='#triage-servicedesk', text='Test message')

@slack_event_adapter.on('message')
def message(payload):
    event= payload.get('event', {})
    channel_id = event.get('channel')
    print(channel_id)
    user_id = event.get('user')
    text = event.get('text')

    if BOT_ID != user_id:
        if user_id in message_counts and channel_id in []:
           client.chat_postMessage(channel='#triage-servicedesk', text=text)
        client.chat_postMessage(channel='#triage-servicedesk', text=text)


@app.route('/ticket-count', methods=['POST'])
def ticket_count():
    data = request.form
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    client.chat_postMessage(channel=channel_id, text="Command works")
    return Response(), 200

if __name__ == "__main__":
    app.run(debug=True)