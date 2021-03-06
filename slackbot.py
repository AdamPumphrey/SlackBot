import slack
import os
import copy
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from random import randrange

# based off of https://www.youtube.com/playlist?list=PLzMcBGfZo4-kqyzTzJWCV6lyK-ZMYECDc


# sensitive info stored in separate .env file
# signing_secret and slack_token in this case
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']
TRIAGE_ID = "C02NT3DTRF1"
# channels as a list in case we want to apply the app to other channels
CHANNELS = [TRIAGE_ID]

tickets = {}

# test to see if app connects to channel
# client.chat_postMessage(channel='#triage-servicedesk', text='Test message')

# Ticket class objects = very basic IT tickets

class Ticket:

    def __init__(self, user, user_name, text, ticket_id):
        self.channel = CHANNELS[0]
        self.user = user
        self.timestamp = ''
        self.status = 'Unassigned'
        self.user_name = user_name
        self.ticket_id = ticket_id
        self.text = text

    # need timestamp and channel in order to post messages
    # blocks is formatted text to be posted
    def get_message(self, mode=0):
        ret_dict = {
            'ts': self.timestamp,
            'channel': self.channel
        }
        if mode:
            ret_dict['blocks'] = [self._get_ticket_update()]
        else:
            ret_dict['blocks'] = [self._get_ticket()]
        return ret_dict

    # create the formatted text to be posted
    def _get_ticket(self):
        ticket_info=f'Ticket #{self.ticket_id}:\n\nUser: {self.user_name}\n\nDescription: {self.text}\n\nStatus: {self.status}'

        return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': ticket_info}}
    
    # same as _get_ticket but with different text
    def _get_ticket_update(self):
        ticket_info=f'Status update for Ticket #{self.ticket_id}:\n\nStatus: {self.status}'

        return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': ticket_info}}

# ticket is posted to the triage channel and added to internal ticket storage upon creation
def create_ticket(user, user_name, text, ticket_id):
    ticket = Ticket(user, user_name, text, ticket_id)
    message = ticket.get_message()
    response = client.chat_postMessage(**message)
    ticket.timestamp = response['ts']

    # ticket added to internal ticket storage with ticket ID as key
    # ticket IDs should be unique
    tickets[ticket_id] = ticket

# tid = ticket_id
def update_ticket(tid, new_info):
    ticket = tickets[tid]
    ticket.status = new_info
    tickets[tid] = ticket
    return ticket

# on-message event handling not needed here
# if it was needed, this is how to do it

# @slack_event_adapter.on('message')
# def message(payload):
#     event= payload.get('event', {})
#     channel_id = event.get('channel')
#     user_id = event.get('user')
#     text = event.get('text')

#     if user_id != None and BOT_ID != user_id:
#         return

# reaction-added event handling
@slack_event_adapter.on('reaction_added')
def reaction(payload):
    event= payload.get('event', {})
    channel_id = event.get('item', {}).get('channel')
    ts = event.get('item', {}).get('ts')

    # only activate if reaction added in triage channel
    if channel_id in CHANNELS:
        # get the actual message via timestamp
        # need the message in order to edit the message
        old_message = client.conversations_history(channel=channel_id, inclusive=True, oldest=ts, latest=ts)
        message_text = old_message['messages'][0]['blocks'][0]['text']['text']
        reaction = old_message['messages'][0]['reactions'][0]['name']
        temp = message_text.rsplit(':', 1)
        # tid = ticket id
        tid = int(temp[0].split(':', 1)[0].split('#')[1])
        # different reactions = different statuses for the ticket
        if reaction == 'eyes':
            temp[1] = 'In progress'
        elif reaction == 'white_check_mark':
            temp[1] = 'Completed'
        # use the ticket id from the message to update the ticket object in storage
        updated_ticket = update_ticket(tid, temp[1])
        updated_message = updated_ticket.get_message()
        # update the message with new status based on reaction
        response = client.chat_update(**updated_message, as_user=True)
        updated_ticket.timestamp = response['ts']
        tickets[tid] = updated_ticket
        # need a deepcopy of the Ticket object to send it to the user via DM
        # since the Ticket.channel property has to be changed.
        # We don't want to edit the actual ticket's channel since it should always be the triage channel
        user_ticket = copy.deepcopy(updated_ticket)
        user_ticket.channel = user_ticket.user
        user_message = user_ticket.get_message(1)
        # send a DM to the user in question notifying them of a status update for their ticket
        client.chat_postMessage(**user_message)
        return

# slash command to create a new ticket
# /create-ticket [issue]
# eg) /create-ticket Help my computer isn't working!
@app.route('/create-ticket', methods=['POST'])
def generate_ticket():
    data = request.form
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    channel_id = data.get('channel_id')
    text = data.get('text')
    # randomly generate a unique ticket id
    ticket_id = randrange(1000, 10000)
    while ticket_id in tickets:
        ticket_id = randrange(1000, 10000)
    create_ticket(user_id, user_name, text, ticket_id)
    client.chat_postMessage(channel=channel_id, text=f'Your ticket #{ticket_id} has been generated.\n\nDescription: {text}\n\nStatus: Unassigned\n\nCheck the status of your ticket with the /ticket-update command.')
    return Response(), 200

# slash command to send a status update to the user for a specific ticket
# /ticket-update [ticket-id]
# eg) /ticket-update 9478
@app.route('/ticket-update', methods=['POST'])
def ticket_update():
    data = request.form
    channel_id = data.get('channel_id')
    ticket_id = int(data.get('text'))
    user_ticket = tickets[ticket_id]
    # another deepcopy of a ticket since we are posting to a channel that is not the triage channel
    user_ticket_copy = copy.deepcopy(user_ticket)
    user_ticket_copy.channel = channel_id
    user_message = user_ticket_copy.get_message(1)
    client.chat_postMessage(**user_message)
    return Response(), 200

# slash command to list info about the other commands
# /help
@app.route('/help', methods=['POST'])
def help():
    data = request.form
    channel_id = data.get('channel_id')
    # i know the string is long and ugly
    ret_string = 'ServiceDesk Application Commands\n\n/create-ticket [issue]:\nThis command creates a ticket with the provided issue.\nServiceDesk will provide you with a copy of the created ticket, including the ticket ID number, which can be used to obtain status updates for the ticket.\nExample: /create-ticket My computer is not working.\n\n/ticket-update [ticket-id]:\nThis command provides a status update for the specified ticket.\nExample: /ticket-update 1234'
    formatted = {'type': 'section', 'text': {'type': 'mrkdwn', 'text': ret_string}}
    message = {
        'ts': '',
        'channel': channel_id,
        'blocks': [formatted]
    }
    client.chat_postMessage(**message)
    return Response(), 200

# run in debug mode for proof of concept
if __name__ == "__main__":
    app.run(debug=True)