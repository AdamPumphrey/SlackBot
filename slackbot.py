import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from random import randrange

# based off of https://www.youtube.com/playlist?list=PLzMcBGfZo4-kqyzTzJWCV6lyK-ZMYECDc

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']
TRIAGE_ID = "C02NT3DTRF1"
CHANNELS = [TRIAGE_ID]

message_counts = {}
welcome_messages = {}

# test to see if bot connects to channel
#client.chat_postMessage(channel='#triage-servicedesk', text='Test message')

class WelcomeMessage:
    START_TEXT = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': (
                'Welcome! \n\n'
                '*Get started by completing the tasks:*'
            )
        }
    }

    DIVIDER = {'type': 'divider'}

    def __init__(self, channel, user):
        self.channel = channel
        self.user = user
        self.timestamp = ''
        self.completed = False

    def get_message(self):
        return {
            'ts': self.timestamp,
            'channel': self.channel,
            'blocks': [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task() 
            ]
        }

    def _get_reaction_task(self):
        checkmark = ':white_check_mark:'
        if not self.completed:
            checkmark = ':white_large_square:'

        text = f'{checkmark} *React to this message!*'

        return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': text}}

def send_welcome_message(channel, user):
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    if channel not in welcome_messages:
        welcome_messages[channel] = {}
        welcome_messages[channel][user] = welcome

# event on team join send welcome message

@slack_event_adapter.on('message')
def message(payload):
    print(payload)
    event= payload.get('event', {})
    channel_id = event.get('channel')
    # print(channel_id)
    user_id = event.get('user')
    text = event.get('text')

    if user_id != None and BOT_ID != user_id:
        if user_id in message_counts and channel_id in CHANNELS:
            message_counts[user_id] += 1
           #client.chat_postMessage(channel='#triage-servicedesk', text=text)
        else:
            message_counts[user_id] = 1
        #client.chat_postMessage(channel='#triage-servicedesk', text=text)
        if text.lower() == 'start':
            send_welcome_message(f'@{user_id}', user_id)

@slack_event_adapter.on('reaction_added')
def reaction(payload):
    event= payload.get('event', {})
    channel_id = event.get('item', {}).get('channel')
    user_id = event.get('user')

    # if channel_id in CHANNELS:
    if f'@{user_id}' not in welcome_messages:
        return
    
    welcome = welcome_messages[f'@{user_id}'][user_id]
    welcome.completed = True
    welcome.channel = channel_id
    message = welcome.get_message()
    updated_message = client.chat_update(**message)
    welcome.timestamp = updated_message['ts']


@app.route('/ticket-count', methods=['POST'])
def ticket_count():
    data = request.form
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    ticket_count = message_counts.get(user_id, 0)
    client.chat_postMessage(channel=channel_id, text=f"Message: {ticket_count}")
    return Response(), 200

@app.route('/create-ticket', methods=['POST'])
def create_ticket():
    data = request.form
    print(data)
    user_name = data.get('user_name')
    channel_id = data.get('channel_id')
    text = data.get('text')
    ticket_id = randrange(1000, 10000)
    client.chat_postMessage(channel=CHANNELS[0], text=f'Ticket #{ticket_id}:\n\nUser: {user_name}\n\nDescription: {text}\n\nStatus: Unassigned')
    client.chat_postMessage(channel=channel_id, text=f'Your ticket #{ticket_id} has been generated.\n\nDescription: {text}\n\nStatus: Unassigned')
    return Response(), 200

if __name__ == "__main__":
    app.run(debug=True)