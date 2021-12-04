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
tickets = {}
used_ticket_ids = []

# test to see if bot connects to channel
#client.chat_postMessage(channel='#triage-servicedesk', text='Test message')

class Ticket:
    # START_TEXT = {
    #     'type': 'section',
    #     'text': {
    #         'type': 'mrkdwn',
    #         'text': (
    #         )
    #     }
    # }

    #DIVIDER = {'type': 'divider'}

    def __init__(self, user, user_name, text, ticket_id):
        self.channel = CHANNELS[0]
        self.user = user
        self.timestamp = ''
        self.status = 'Unassigned'
        self.user_name = user_name
        self.ticket_id = ticket_id
        self.text = text

    def get_message(self):
        return {
            'ts': self.timestamp,
            'channel': self.channel,
            'blocks': [
                #self.START_TEXT,
                #self.DIVIDER,
                self._get_ticket() 
            ]
        }

    def _get_ticket(self):
        #checkmark = ':white_check_mark:'
        #if not self.completed:
        #    checkmark = ':white_large_square:'
        
        ticket_info=f'Ticket #{self.ticket_id}:\n\nUser: {self.user_name}\n\nDescription: {self.text}\n\nStatus: {self.status}'
        #channel=CHANNELS[0], text=f'Ticket #{ticket_id}:\n\nUser: {user_name}\n\nDescription: {text}\n\nStatus: Unassigned'

        return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': ticket_info}}
    
    def _get_ticket_update(self):
        ticket_info=f'Status for Ticket #{self.ticket_id}: {self.status}'

        return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': ticket_info}}

def create_ticket(user, user_name, text, ticket_id):
    ticket = Ticket(user, user_name, text, ticket_id)
    message = ticket.get_message()
    response = client.chat_postMessage(**message)
    ticket.timestamp = response['ts']

    if user not in tickets:
        tickets[user] = {}
        tickets[user][ticket_id] = ticket
    else:
        tickets[user][ticket_id] = ticket

# event on team join send welcome message

@slack_event_adapter.on('message')
def message(payload):
    print(payload)
    event= payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    print(text)

    if user_id != None and BOT_ID != user_id:
        # if user_id in message_counts and channel_id in CHANNELS:
        #     message_counts[user_id] += 1
        #    #client.chat_postMessage(channel='#triage-servicedesk', text=text)
        # else:
        #     message_counts[user_id] = 1
        # #client.chat_postMessage(channel='#triage-servicedesk', text=text)
        # if text.lower() == 'start':
        #     send_welcome_message(f'@{user_id}', user_id)
        return

@slack_event_adapter.on('reaction_added')
def reaction(payload):
    print(payload)
    event= payload.get('event', {})
    channel_id = event.get('item', {}).get('channel')
    user_id = event.get('user')

    if channel_id in CHANNELS:
        return
        # welcome = welcome_messages[f'@{user_id}'][user_id]
        # welcome.completed = True
        # welcome.channel = channel_id
        # message = welcome.get_message()
        # updated_message = client.chat_update(**message)
        # welcome.timestamp = updated_message['ts']


@app.route('/ticket-count', methods=['POST'])
def ticket_count():
    data = request.form
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    ticket_count = message_counts.get(user_id, 0)
    client.chat_postMessage(channel=channel_id, text=f"Message: {ticket_count}")
    return Response(), 200

@app.route('/create-ticket', methods=['POST'])
def generate_ticket():
    data = request.form
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    channel_id = data.get('channel_id')
    text = data.get('text')
    ticket_id = randrange(1000, 10000)
    while ticket_id in used_ticket_ids:
        ticket_id = randrange(1000, 10000)
    create_ticket(user_id, user_name, text, ticket_id)
    #client.chat_postMessage(channel=CHANNELS[0], text=f'Ticket #{ticket_id}:\n\nUser: {user_name}\n\nDescription: {text}\n\nStatus: Unassigned')
    client.chat_postMessage(channel=channel_id, text=f'Your ticket #{ticket_id} has been generated.\n\nDescription: {text}\n\nStatus: Unassigned\n\nCheck the status of your ticket with the /ticket-status command.')
    return Response(), 200

# ticket-status command goes here

if __name__ == "__main__":
    app.run(debug=True)