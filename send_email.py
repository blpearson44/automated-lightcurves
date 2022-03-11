#!/usr/bin/env python3
"""Generate an email of data plots to send to recipient(s)."""

import smtplib
from email.message import EmailMessage

sender = "blpearson.dev@gmail.com"
password = "72Potsy1"
receiver = "blpearson44@gmail.com"

# creating the SMTP server object by giving SMPT server address and port number
smtp_server = smtplib.SMTP("smtp.gmail.com", 465)
smtp_server.ehlo()  # setting the ESMTP protocol
smtp_server.starttls()  # setting up to TLS connection
smtp_server.ehlo()  # calling the ehlo() again as encryption happens on calling startttls()
smtp_server.login(sender, password)  # logging into out email id
msg_to_be_sent = """
Hello, receiver!
Hope you are doing well.
Welcome to PythonGeeks!
"""
# sending the mail by specifying the from and to address and the message
smtp_server.sendmail(sender, receiver, msg_to_be_sent)
print("Successfully the mail is sent")  # priting a message on sending the mail
smtp_server.quit()  # terminating the server
