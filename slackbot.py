import slack
import os
from pathlib import Path

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

# test to see if bot connects to channel
# client.chat_postMessage(channel='#triage-servicedesk', text='Test message')
