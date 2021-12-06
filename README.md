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

This app is meant to run on a public web server in order to send and receive requests from the Slack API.

The enviroment variables are the Slack application's auth token and signing secret.

More info regarding the Slack API can be found [here](https://api.slack.com/).

Development and testing was done on an Ubuntu server which used [ngrok](https://ngrok.com/) for a public URL.

## Purpose
This application is a very basic implementation of a rudimentary IT ticketing system, built as part of a school project. The idea is to automate the triaging process to help Tier I IT teams be more efficient.

In addition to the application, a triage channel should also be present in the Slack workspace. The application needs to be added to the triage channel, whose channel ID is specified by TRIAGE_ID on line 23.

The application has three commands:
* /create-ticket [issue]
* /ticket-update [ticket-id]
* /help

<img src="https://camo.githubusercontent.com/39f71f393cb0005ec7070eb417ddccf800de82c29dbb351e9b1463bc7c446b67/68747470733a2f2f692e696d6775722e636f6d2f555638376d52362e706e67" alt="test" data-canonical-src="https://i.imgur.com/UV87mR6.png" width=800 height=600>

All three commands are intended to be used in private messages (DMs) with the application.

/create-ticket takes in a string as input and generates a ticket. The ticket is then posted to the triage channel in Slack, and a copy is sent back to the user via DM.

Example usage: /create-ticket Help my computer is not working!

/ticket-update takes in a string as input and provides a status update on the specified ticket. The string should be the ID of the ticket, which is provided when the ticket is created. The ticket ID will consist of four numbers (eg. 5937).

Example usage: /ticket-update 4928

/help sends the user information regarding the commands handled by the application.

The application uses reactions on messages to update the status of a ticket. If a technician reacts to the ticket message with the 'eyes' emoji, the status is changed to "In progress", because the tech is "taking a look" at the ticket. Similarly, if the eyes reaction is removed and a checkmark reaction is added, the status is changed to "Completed".

Video demo below:

[![Video Demo](https://img.youtube.com/vi/wkeUGJKRiuw/maxresdefault.jpg)](https://www.youtube.com/watch?v=wkeUGJKRiuw)
