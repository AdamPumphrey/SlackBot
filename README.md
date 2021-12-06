# SlackBot
Slack Bot for DMIT2034

Built with Python 3.8

Based off of [this Tech With Tim tutorial](https://www.youtube.com/playlist?list=PLzMcBGfZo4-kqyzTzJWCV6lyK-ZMYECDc).

Required packages:
* slack
* os
* copy
* random
* pathlib
* dotenv (for simulating environment variables)
* flask
* slackeventsapi

This app is meant to run on a public web server in order to send and receive requests from the Slack api.

The enviroment variables are the Slack application's auth token and signing secret.

More info regarding the Slack api can be found [here](https://api.slack.com/).

Development and testing was done on an Ubuntu server which used [ngrok](https://ngrok.com/) for a public URL.

## Purpose
This application is a very basic implementation of a rudimentary IT ticketing system. The idea is to automate the triaging process to help Tier I IT teams be more efficient.

In addition to the application, a triage channel should also be present in the Slack workspace. The application needs to be added to the triage channel, whose channel ID is specified by TRIAGE_ID on line 23.

The application has three commands:
* /create-ticket [issue]
* /ticket-update [ticket-id]
* /help

All three commands are intended to be used in private messages (DMs) with the application.

/create-ticket takes in a string as input and generates a ticket. The ticket is then posted to the triage channel in Slack, and a copy is sent back to the user via DM.

Example usage: /create-ticket Help my computer is not working!

/ticket-update takes in a string as input and provides a status update on the specified ticket. The string should be the ID of the ticket, which is provided when the ticket is created. The ticket ID will consist of four numbers (eg. 5937).

Example usage: /ticket-update 4928

/help sends the user information regarding the commands handled by the application.
