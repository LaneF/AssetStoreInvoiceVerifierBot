import discord
import requests
import json
import os
from keep_alive import keep_alive

# This is based on the tutorial here
# https://www.youtube.com/watch?v=SPTfmiYiuok

# This is the endpoint to talk to the store API
endpoint = "https://api.assetstore.unity3d.com:443/publisher/v1/invoice/verify.json?"

# This is the role name on your server.
verifiedRoleTitle = "Verified"

client = discord.Client()

@client.event
async def on_ready():
  print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  # when a user starts a message with $verify
  # followed by one space and an invoice number...
  if message.content.startswith('$verify'):
    invoice = message.content.split()[1]

    # put the asset store API key into a file named `.env`
    key = os.getenv('APIKEY')

    # formatting for the URL to talk to the API.
    requestUrl = f'{endpoint}key={key}&invoice={invoice}'
    response = requests.get(requestUrl)

    # kill the message to protect the invoice ID. 
    # won't stop a secret user bot from scrubbing the channel before deletion!
    # Discord SLASH Command API required for full protection.
    await client.http.delete_message(message.channel.id, message.id)

    # getting 403 means they API Key is wrong or the URL is corrupted somehow.
    if "403 Forbidden" in response.text:
      await message.channel.send('*Failed access to Store API. Contact administrator.*')
      return

    # getting 403 means they API Key is wrong or the URL is corrupted somehow.
    if "500 Internal Server Error" in response.text:
      await message.channel.send(f'<@{message.author.id}> provided input that broke the Store API. Try a valid invoice number (not order number).')
      return

    # invoices is an array, we only process the first data set here.
    # first, validate it. An empty response means it is invalid.
    data = json.loads(response.text)

    # fewer than this many arbitrary (but low) number of characters means something is wrong.
    # this a crappy exception, as a user could just flood a huge string and pass it.
    if len(response.text) < 100:
      await message.channel.send(f'<@{message.author.id}>, there is something wrong with that invoice ID.')
      return

    # parse out the json data
    package = data['invoices'][0]['package']
    refunded = data['invoices'][0]['refunded']
    reason = data['invoices'][0]['reason']
    purchDate = data['invoices'][0]['date']
    downloaded = data['invoices'][0]['downloaded']

    # we only differentiate between refunded and current assets
    # you could branch here and start doing different things based on the product name.
    if refunded == "Yes":
      await message.channel.send(f'<@{message.author.id}> previously owned, but **refunded** the product `{package}`, Reason: _{reason}_, Downloaded: _{downloaded}_')
      return
    else:
      await message.channel.send(f'<@{message.author.id}> is a **verified owner** of `{package}`, Purchased: _{purchDate}_, Downloaded: _{downloaded}_')
      role = discord.utils.get(message.guild.roles, name=verifiedRoleTitle)
      await message.author.add_roles(role)
      return

# this makes sure the system stays alive
keep_alive()

# this logs into Discord, put the token in a file named `.env`.
client.run(os.getenv('BOTTOKEN'))

# sample `.env` file: (dots are not in the code)
#
# BOTTOKEN=Nzk2NDI2NjcxNTM1ODE2NzQ1.X_XwIw.................
# APIKEY=mOHVu2Tl..........................................
#
