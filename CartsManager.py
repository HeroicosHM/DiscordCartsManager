"""
Hello and welcome to my code!
Before I begin, I want to make a couple disclaimers. A lot of waht I do in this program is considered
very rough around the edges and fairly brute force. For those of you developers looking at this,
I know that this program is not the cleanest, but I don't have the energy to completely redo it.

If you use this program, please give credit to me somehow.
Reach out to me on Discord:
Heroicos_HM#0310
"""

#These are the modules used by the program.
import asyncio
import time
import os
import random
import string
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import pymysql
import re
import logging
import traceback
import sys
import datetime
import json
from urllib.parse import urlparse

global data, logs_channels

#Load all of the data from the configuration file.
with open("./Config.json") as file:
	config = json.loads(file.read())

	logs_channels = config['logs_channels']
	data_file = config['data_file']
	embed_color = config['embed_color']
	footer_text = config['footer_text']
	carts_original_channel = config['carts_original_channel']
	carts_formatted_channel = config['carts_formatted_channel']
	adi_table = config['adi_table']
	latch_table = config['latch_table']
	phantom_table = config['phantom_table']
	balko_table = config['balko_table']
	sole_table = config['sole_table']
	TOKEN = config['TOKEN']
	db_ip = config['database_ip']
	db_user = config['database_username']
	db_pass = config['database_password']
	db_name = config['database_name']
	footer_icon = config['footer_icon_url']
	online_message = config['online_message']
	prefix = config['prefix']

	#Get the start time for the uptime command.
start_time = time.time()

#Establish an initial connection to the database, and make sure the necessary tables exist.
conn = pymysql.connect(db_ip,user=db_user,passwd=db_pass,db=db_name,connect_timeout=30)
cur = conn.cursor(pymysql.cursors.DictCursor)

create_db = """CREATE TABLE IF NOT EXISTS """ + adi_table + """ (ID MEDIUMINT, Title text, Link text, Email text, Password text, Size text, Desktop text, Mobile text, PID text, Thumbnail text, MessageID text, Timestamp text, Proxy text, HMAC text);"""
cur.execute(create_db)
create_db = """CREATE TABLE IF NOT EXISTS """ + latch_table + """ (ID MEDIUMINT, Title text, Link text, Email text, Password text, Size text, Region text, PID text, Thumbnail text, MessageID text);"""
cur.execute(create_db)
create_db = """CREATE TABLE IF NOT EXISTS """ + phantom_table + """ (ID MEDIUMINT, Author text, Title text, Name text, Size text, Profile text, Site text, Account text, Link text, MessageID text);"""
cur.execute(create_db)
create_db = """CREATE TABLE IF NOT EXISTS """ + balko_table + """ (ID MEDIUMINT, Title text, Link text, Email text, Password text, Size text, Region text, PID text, Thumbnail text, MessageID text);"""
cur.execute(create_db)
create_db = """CREATE TABLE IF NOT EXISTS """ + sole_table + """ (ID MEDIUMINT, Title text, Link text, Region text, Size text, Email text, Password text, Proxy text, Login text, Thumbnail text, MessageID text);"""
cur.execute(create_db)
conn.commit()

#Read information from data files (allows carts to persist through sudden shutdowns and restarts).
if os.path.isfile(data_file):
	file = open(data_file).read()
	if len(file) > 0:
		data = json.loads(file)
		print(data)
	else:
		data = {}
		data['IsDeleting'], data['AdiSplashMessages'], data['LatchKeyMessages'], data['PhantomMessages'], data['BalkoMessages'], data['SoleAIOMessages'] = [], [], [], [], [], []
else:
	file = open(data_file, 'w+')
	file.close()
	data = {}
	data['IsDeleting'], data['AdiSplashMessages'], data['LatchKeyMessages'], data['PhantomMessages'], data['BalkoMessages'], data['SoleAIOMessages'] = [], [], [], [], [], []

file = open(data_file, 'w+')
file.write(json.dumps(data, indent=4, sort_keys=True))
file.close()

"""
A personal note..I always forget how to do this right so I have it in almost all my programs.

Writing data to json method:

file = open(data_file, 'w+')
file.write(json.dumps(data, indent=4, sort_keys=True))
file.close()
"""

#Create the Discord bot object.
Client = discord.Client()
bot = commands.Bot(command_prefix = "?")

#Triggers when the bot is ready to receive commands.
#This sends the online message.
@bot.event
async def on_ready():
	print('Logged in as {0} and connected to Discord! (ID: {0.id})'.format(bot.user))
	embed = discord.Embed(
		title = online_message,
		color = embed_color
	)
	embed.set_footer(
		text = footer_text,
		icon_url = footer_icon
	)
	if len(sys.argv) > 1:
		await bot.send_message(discord.Object(id=sys.argv[1]), embed = embed)
	else:
		for log in logs_channels:
			await bot.send_message(discord.Object(id=log), embed = embed)

#Triggers whenever a message is sent by anyone in a channel the bot can see.
@bot.event
async def on_message(message):
	#Makes sure the cart is in a server.
	if message.server:
		#A little helper bit i put in to make sure things didn't break during the deletion of claimed carts.
		if len(message.embeds) > 0 and 'title' in message.embeds[0].keys() and (message.embeds[0]['title'] == "**You must include a command.**" or message.embeds[0]['title'] == "**Unrecognized Command**" or message.embeds[0]['title'] == "**Insufficient Permissions**") and message not in data['IsDeleting']:
			data['IsDeleting'].append(message)
			await asyncio.sleep(15)
			await bot.delete_message(message)
			data['IsDeleting'].remove(message)

		#Command to get the uptime of the bot. Can be used in any channel.
		if message.content.upper().startswith(prefix + "UPTIME"):
			now_time = time.time()
			diff = int(now_time - start_time)
			hour = int(diff / 3600)
			diff = diff - (hour * 1600)
			minutes = int(diff / 60)
			if message.server:
				await bot.delete_message(message)
				await bot.send_typing(message.channel)
				embed_time = discord.Embed(
					title = "Bot Status: `ONLINE`",
					description = "I have been online for {0} hours and {1} minutes on {2}.".format(hour, minutes, message.server),
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				embed_time.set_thumbnail(
					url = message.server.icon_url
				)
			else:
				await bot.send_typing(message.author)
				embed_time = discord.Embed(
					title = "Bot Status: `ONLINE`",
					description = "I have been online for {0} hours and {1} minutes.".format(hour, minutes),
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				embed_time.set_thumbnail(
					url = bot.user.avatar_url
				)

			embed_time.set_footer(
				text = footer_text,
				icon_url = footer_icon
			)
			if message.server:
				await bot.send_message(message.channel, embed = embed_time)
			else:
				await bot.send_message(message.author, embed = embed_time)

		#This whole chunk is what gets the carts from the private channel and sends it in the public channel.
		if len(message.embeds) > 0:
			#Establish database connection.
			conn = pymysql.connect(db_ip,user=db_user,passwd=db_pass,db=db_name,connect_timeout=30)
			cur = conn.cursor(pymysql.cursors.DictCursor)

			#Make sure the message is in a carts channel.
			if str(message.channel.id) == carts_original_channel and message.author.id != bot.user.id:
				diction = message.embeds[0]
				#Check to make sure it is an acceptable cart type.
				if "AdiSplash" in str(message.embeds[0]['footer']['text']):
					#Extract all of the information from the cart.
					title = diction['title']
					link = diction['url']
					for item in diction['fields']:
						if 'ACCOUNT DETAILS' in item['name']:
							email = item['value'].split('\n')[0]
							password = item['value'].split('\n')[1]
						if 'SIZE' in item['name']:
							size = item['value']
						if 'DESKTOP' in item['name']:
							desktop_link = item['value']
						if 'MOBILE' in item['name']:
							mobile_link = item['value']
						if ('PRODUCT' in item['name']) or ('PID' in item['name']):
							pid = item['value']
						if 'PROXY' in item['name']:
							proxy = item['value']
						if 'TIMESTAMP' in item['name']:
							timestamp = item['value']
						if 'HMAC' in item['name']:
							hmac = item['value']
					try:
						thumbnail = diction['thumbnail']['url']
					except:
						thumbnail = "N/A"

					message_id = message.id

					sql = "SELECT * FROM `" + adi_table + "` ORDER BY ID DESC LIMIT 1"
					cur.execute(sql)
					entry_number = cur.fetchall()
					if len(entry_number) == 0:
						entry_number = str(1)
					else:
						entry_number = str(entry_number[0]['ID'] + 1)

					#Insert all of that information into the database for that specific cart type.
					insert_data = """INSERT INTO  """ + adi_table + """ (ID, Title, Link, Email, Password, Size, Desktop, Mobile, PID, Thumbnail, MessageID, Timestamp, Proxy, HMAC) VALUES ('""" + entry_number + """','""" + title + """', '""" + link + """', '""" + email + """', '""" + password + """', '""" + size + """', '""" + desktop_link + """', '""" + mobile_link + """', '""" + pid + """', '""" + thumbnail + """','""" + message_id + """', '""" + timestamp + """', '""" + proxy + """', '""" + hmac + """');"""
					cur.execute(insert_data)
					conn.commit()

					#Send the reformatted cart into the public cart channel.
					embed = discord.Embed(
						title = title,
						url = "https://www.google.com/search?q=" + pid,
						color = embed_color,
						timestamp = datetime.datetime.now(datetime.timezone.utc)
					)
					embed.add_field(
						name = "**PRODUCT ID**",
						value = pid
					)
					embed.add_field(
						name = "**SIZE**",
						value = size
					)
					embed.add_field(
						name = "**DOMAIN**",
						value = urlparse(link).netloc
					)
					embed.add_field(
						name = "**TIMESTAMP**",
						value = timestamp
					)
					if thumbnail != "N/A":
						pass
					else:
						embed.set_thumbnail(
							url = bot.user.avatar_url
						)
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, entry_number),
						icon_url = footer_icon
					)
					r = await bot.send_message(discord.Object(id=carts_formatted_channel), embed = embed)
					await bot.add_reaction(r, "🛒")
					data['AdiSplashMessages'].append(r.id)
					file = open(data_file, 'w+')
					file.write(json.dumps(data, indent=4, sort_keys=True))
					file.close()

				#Repeat, but for Latchkey.
				elif "LatchKey" in str(message.embeds[0]['footer']['text']):
					title = diction['title']
					link = diction['url']
					for item in diction['fields']:
						if 'Region' in item['name']:
							region = item['value']
						if ('Product ID' or 'PID') in item['name']:
							pid = item['value']
						if 'Size' in item['name']:
							size = item['value']
						if 'Email' in item['name']:
							email = item['value']
						if 'Password' in item['name']:
							password = item['value']
						if 'Cart Expires' in item['name']:
							expiry = item['value']
					try:
						thumbnail = diction['thumbnail']['url']
					except:
						thumbnail = "N/A"

					message_id = message.id

					sql = "SELECT * FROM `" + latch_table + "` ORDER BY ID DESC LIMIT 1"
					cur.execute(sql)
					entry_number = cur.fetchall()
					if len(entry_number) == 0:
						entry_number = str(1)
					else:
						entry_number = str(entry_number[0]['ID'] + 1)

					#Insert all of that information into the database for that specific cart type.
					insert_data = """INSERT INTO  """ + latch_table + """ (ID, Title, Link, Email, Password, Size, Region, PID, Thumbnail, MessageID) VALUES ('""" + entry_number + """','""" + title + """', '""" + link + """', '""" + email + """', '""" + password + """', '""" + size + """', '""" + region + """', '""" + pid + """', '""" + thumbnail + """', '""" + message_id + """');"""
					cur.execute(insert_data)
					conn.commit()

					embed = discord.Embed(
						title = title,
						url = "https://www.google.com/search?q=" + pid,
						color = embed_color,
						timestamp = datetime.datetime.now(datetime.timezone.utc)
					)
					embed.add_field(
						name = "**PRODUCT ID**",
						value = pid
					)
					embed.add_field(
						name = "**SIZE**",
						value = size
					)
					embed.add_field(
						name = "**Cart Expires**",
						value = expiry
					)
					if thumbnail != "N/A":
						pass
					else:
						embed.set_thumbnail(
							url = bot.user.avatar_url
						)
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, entry_number),
						icon_url = footer_icon
					)
					r = await bot.send_message(discord.Object(id=carts_formatted_channel), embed = embed)
					await bot.add_reaction(r, "🛒")
					data['LatchKeyMessages'].append(r.id)
					file = open(data_file, 'w+')
					file.write(json.dumps(data, indent=4, sort_keys=True))
					file.close()
				#Repeat, but for Phatom.
				elif "Phantom" in str(message.embeds[0]['footer']['text']):
					author = diction['author']['name']
					title = diction['title']
					link = diction['url']
					for item in diction['fields']:
						if 'Item' in item['name']:
							name = item['value']
						elif 'Size' in item['name']:
							size = item['value']
						elif 'Profile' in item['name']:
							profile = item['value']
						elif 'Site' in item['name']:
							site = item['value']
						elif 'Account' in item['name']:
							account = item['value']

					message_id = message.id

					sql = "SELECT * FROM `" + phantom_table + "` ORDER BY ID DESC LIMIT 1"
					cur.execute(sql)
					entry_number = cur.fetchall()
					if len(entry_number) == 0:
						entry_number = str(1)
					else:
						entry_number = str(entry_number[0]['ID'] + 1)

					#Insert all of that information into the database for that specific cart type.
					insert_data = """INSERT INTO  """ + phantom_table + """ (ID, Author, Title, Name, Size, Profile, Site, Account, Link, MessageID) VALUES ('""" + entry_number + """', '""" + author + """', '""" + title + """', '""" + name + """', '""" + size + """', '""" + profile + """', '""" + site + """', '""" + account + """', '""" + link + """', '""" + message_id + """');"""
					cur.execute(insert_data)
					conn.commit()

					embed = discord.Embed(
						title = title,
						color = embed_color,
						timestamp = datetime.datetime.now(datetime.timezone.utc)
					)
					embed.set_author(
						name = author
					)
					embed.add_field(
						name = "**Item**",
						value = name
					)
					embed.add_field(
						name = "**Size**",
						value = size
					)
					embed.add_field(
						name = "**Site**",
						value = site
					)
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, entry_number),
						icon_url = footer_icon
					)
					r = await bot.send_message(discord.Object(id=carts_formatted_channel), embed = embed)
					await bot.add_reaction(r, "🛒")
					data['PhantomMessages'].append(r.id)
					file = open(data_file, 'w+')
					file.write(json.dumps(data, indent=4, sort_keys=True))
					file.close()

				#Repeat, but for Balkobot.
				elif "Balkobot" in str(message.embeds[0]['footer']['text']):
					title = diction['title']
					link = diction['url']
					for item in diction['fields']:
						if 'Email' in item['name']:
							email = item['value']
						elif 'Password' in item['name']:
							password = item['value']
						elif 'Size' in item['name']:
							size = item['value']
						elif 'Site' in item['name']:
							site = item['value']
						elif 'Region' in item['name']:
							region = item['value']
						elif 'PID' in item['name']:
							pid = item['value']

					try:
						thumbnail = diction['thumbnail']['url']
					except:
						thumbnail = "N/A"

					message_id = message.id

					sql = "SELECT * FROM `" + balko_table + "` ORDER BY ID DESC LIMIT 1"
					cur.execute(sql)
					entry_number = cur.fetchall()
					if len(entry_number) == 0:
						entry_number = str(1)
					else:
						entry_number = str(entry_number[0]['ID'] + 1)

					#Insert all of that information into the database for that specific cart type.
					insert_data = """INSERT INTO  """ + balko_table + """ (ID, Title, Link, Email, Password, Size, Region, PID, Thumbnail, MessageID) VALUES ('""" + entry_number + """','""" + title + """', '""" + link + """', '""" + email + """', '""" + password + """', '""" + size + """', '""" + region + """', '""" + pid + """', '""" + thumbnail + """','""" + message_id + """');"""
					cur.execute(insert_data)
					conn.commit()

					embed = discord.Embed(
						title = title,
						url = link,
						color = embed_color,
						timestamp = datetime.datetime.now(datetime.timezone.utc)
					)
					embed.add_field(
						name = "**Size**",
						value = size
					)
					embed.add_field(
						name = "**Region**",
						value = region
					)
					embed.add_field(
						name = "**PID**",
						value = pid
					)
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, entry_number),
						icon_url = bot.user.avatar_url
					)
					if thumbnail == "N/A":
						pass
					else:
						embed.set_thumbnail(
							url = thumbnail
						)
					r = await bot.send_message(discord.Object(id=carts_formatted_channel), embed = embed)
					await bot.add_reaction(r, "🛒")
					data['BalkoMessages'].append(r.id)
					file = open(data_file, 'w+')
					file.write(json.dumps(data, indent=4, sort_keys=True))
					file.close()
				#Repeat, but for Sole AIO.
				elif "Sole AIO" in str(message.embeds[0]['footer']['text']):
					title = diction['title']
					link = diction['url']
					for item in diction['fields']:
						if 'Email' in item['name']:
							email = item['value']
						elif 'Password' in item['name']:
							password = item['value']
						elif 'Size' in item['name']:
							size = item['value']
						elif 'Login' in item['name']:
							login = item['value']
						elif 'Region' in item['name']:
							region = item['value']
						elif 'Proxy' in item['name']:
							proxy = item['value']

					try:
						thumbnail = diction['thumbnail']['url']
					except:
						thumbnail = "N/A"

					message_id = message.id

					sql = "SELECT * FROM `" + sole_table + "` ORDER BY ID DESC LIMIT 1"
					cur.execute(sql)
					entry_number = cur.fetchall()
					if len(entry_number) == 0:
						entry_number = str(1)
					else:
						entry_number = str(entry_number[0]['ID'] + 1)

					#Insert all of that information into the database for that specific cart type.
					insert_data = """INSERT INTO  """ + sole_table + """ (ID, Title, Link, Region, Size, Email, Password, Proxy, Login, Thumbnail, MessageID) VALUES ('""" + entry_number + """','""" + title + """', '""" + link + """', '""" + region + """', '""" + size + """', '""" + email + """', '""" + password + """', '""" + proxy + """', '""" + login + """','""" + thumbnail + """','""" + message_id + """');"""
					cur.execute(insert_data)
					conn.commit()

					embed = discord.Embed(
						title = title,
						color = embed_color,
						timestamp = datetime.datetime.now(datetime.timezone.utc)
					)
					embed.add_field(
						name = "**Region**",
						value = region
					)
					embed.add_field(
						name = "**Size**",
						value = size
					)
					embed.add_field(
						name = "**Domain**",
						value = urlparse(link).netloc
					)
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, entry_number),
						icon_url = footer_icon
					)
					if thumbnail == "N/A":
						pass
					else:
						embed.set_thumbnail(
							url = thumbnail
						)
					r = await bot.send_message(discord.Object(id=carts_formatted_channel), embed = embed)
					await bot.add_reaction(r, "🛒")
					data['SoleAIOMessages'].append(r.id)
					file = open(data_file, 'w+')
					file.write(json.dumps(data, indent=4, sort_keys=True))
					file.close()
			else:
				pass

#This chunk will handle claiming the carts.
@bot.event
async def on_socket_raw_receive(the_reaction):
	#Gets the event and makes sure it is a reaction that was added.
	if not isinstance(the_reaction, str):
		return
	reaction = json.loads(the_reaction)
	type = reaction.get("t")
	dat = reaction.get("d")
	if not dat:
		return
	if type == "MESSAGE_REACTION_ADD":
		emoji = dat.get("emoji")
		user_id = dat.get("user_id")
		message_id = dat.get("message_id")
		channel_id = dat.get("channel_id")

		global data
		#Makes sure the bot isnt allowed to claim the cart.
		if user_id == bot.user.id:
			pass
		#Checks if the message the reaction was added to is a valid cart to react to.
		elif message_id in data['AdiSplashMessages']:
			#Immediately mark the cart as claimed, or rather, no longer *not* claimed.
			data['AdiSplashMessages'].remove(message_id)
			#Establish DB connection
			conn = pymysql.connect(db_ip,user=db_user,passwd=db_pass,db=db_name,connect_timeout=30)
			cur = conn.cursor(pymysql.cursors.DictCursor)
			file = open(data_file, 'w+')
			file.write(json.dumps(data, indent=4, sort_keys=True))
			file.close()
			channel = channel_id
			#Get cart information and create a message with the information.
			if str(channel) == carts_formatted_channel:
				my_channel = bot.get_channel(channel_id)
				message = await bot.get_message(my_channel, message_id)
				await bot.clear_reactions(message)
				diction = message.embeds[0]
				cart_text = diction['footer']['text'].split("|")[-1]
				cart_number = int(re.search(r'\d+', cart_text).group(0))
				sql = """SELECT * FROM  """ + adi_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				cart_info = cur.fetchall()
				cart_info = cart_info[0]
				cart_id = cart_info['ID']
				cart_title = cart_info['Title']
				cart_link = cart_info['Link']
				cart_email = cart_info['Email']
				cart_pass = cart_info['Password']
				cart_size = cart_info['Size']
				cart_desktop = cart_info['Desktop']
				cart_mobile = cart_info['Mobile']
				cart_pid = cart_info['PID']
				cart_thumbnail = cart_info['Thumbnail']
				cart_discord_link = cart_info['MessageID']
				cart_proxy = cart_info['Proxy']
				cart_hmac = cart_info['HMAC']
				cart_timestamp = cart_info['Timestamp']

				#Create message with the information extracted from the database.
				embed = discord.Embed(
					title = cart_title,
					url = cart_link,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				embed.add_field(
					name = "**PRODUCT**",
					value = cart_pid,
					inline = True
				)
				embed.add_field(
					name = "**SIZE**",
					value = cart_size,
					inline = True
				)
				embed.add_field(
					name = "**ACCOUNT DETAILS**",
					value = cart_email + "\n" + cart_pass,
					inline = False
				)
				embed.add_field(
					name = "**DESKTOP**",
					value = cart_desktop,
					inline = False
				)
				embed.add_field(
					name = "**MOBILE**",
					value = cart_mobile,
					inline = True
				)
				embed.add_field(
					name = "**HMAC**",
					value = cart_hmac,
					inline = False
				)
				embed.add_field(
					name = "**PROXY**",
					value = cart_proxy,
					inline = False
				)
				embed.add_field(
					name = "**DOMAIN**",
					value = urlparse(cart_link).netloc,
					inline = False
				)
				embed.add_field(
					name = "**TIMESTAMP**",
					value = cart_timestamp,
					inline = False
				)
				embed.set_footer(
					text = "{} | Cart #{}".format(footer_text, cart_id),
					icon_url = footer_icon
				)
				if cart_thumbnail == "N/A":
					pass
				else:
					embed.set_thumbnail(
						url = cart_thumbnail
					)
				sql = """DELETE FROM  """ + adi_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				conn.commit()
				server = message.server
				author = server.get_member(user_id)

				#Send the full cart directly to the user.
				await bot.send_message(author, embed = embed)

				user = await bot.get_user_info(user_id)
				new_title = "Cart Claimed!"
				new_link = diction['url']
				new_footer_text = "%s | Claimed by %s" % (footer_text, user.name)
				new_footer_icon_url = diction['footer']['icon_url']
				try:
					new_thumbnail = diction['thumbnail']['url']
				except:
					new_thumbnail = "N/A"

				#Edit the public cart to show that it was claimed by someone and is no longer available.
				new_embed = discord.Embed(
					title = new_title,
					url = new_link,
					description = "*This cart was claimed by `%s` and is no longer available.*" % user.name,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				new_embed.set_footer(
					text = new_footer_text,
					icon_url = new_footer_icon_url
				)
				await bot.edit_message(message, embed = new_embed)
			else:
				pass
		#Repeat for Latchkey.
		elif message_id in data['LatchKeyMessages']:
			data['LatchKeyMessages'].remove(message_id)
			conn = pymysql.connect(db_ip,user=db_user,passwd=db_pass,db=db_name,connect_timeout=30)
			cur = conn.cursor(pymysql.cursors.DictCursor)
			file = open(data_file, 'w+')
			file.write(json.dumps(data, indent=4, sort_keys=True))
			file.close()
			channel = channel_id
			if str(channel) == carts_formatted_channel:
				my_channel = bot.get_channel(channel_id)
				message = await bot.get_message(my_channel, message_id)
				await bot.clear_reactions(message)
				diction = message.embeds[0]
				cart_text = diction['footer']['text']
				cart_number = int(re.search(r'\d+', cart_text).group(0))
				sql = """SELECT * FROM  """ + latch_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				cart_info = cur.fetchall()[0]
				cart_id = cart_info['ID']
				cart_title = cart_info['Title']
				cart_link = cart_info['Link']
				cart_email = cart_info['Email']
				cart_pass = cart_info['Password']
				cart_size = cart_info['Size']
				cart_region = cart_info['Region']
				cart_pid = cart_info['PID']
				cart_thumbnail = cart_info['Thumbnail']
				cart_discord_link = cart_info['MessageID']

				embed = discord.Embed(
					title = cart_title,
					url = cart_link,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				embed.add_field(
					name = "Region",
					value = cart_region,
					inline = True
				)
				embed.add_field(
					name = "Product ID",
					value = cart_pid,
					inline = True
				)
				embed.add_field(
					name = "Size",
					value = cart_size,
					inline = True
				)
				embed.add_field(
					name = "Account Details",
					value = "||" + cart_email + "||\n||" + cart_pass + "||",
					inline = True
				)
				embed.set_footer(
					text = "{} | Cart #{}".format(footer_text, cart_id),
					icon_url = footer_icon
				)
				if cart_thumbnail == "N/A":
					pass
				else:
					embed.set_thumbnail(
						url = cart_thumbnail
					)
				sql = """DELETE FROM  """ + latch_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				conn.commit()
				server = message.server
				author = server.get_member(user_id)

				await bot.send_message(author, embed = embed)

				user = await bot.get_user_info(user_id)
				new_title = "Cart Claimed!"
				new_link = diction['url']
				new_footer_text = "%s | Claimed by %s" % (footer_text, user.name)
				new_footer_icon_url = diction['footer']['icon_url']
				try:
					new_thumbnail = diction['thumbnail']['url']
				except:
					new_thumbnail = "N/A"
				new_embed = discord.Embed(
					title = new_title,
					url = new_link,
					description = "*This cart was claimed by `%s` and is no longer available.*" % user.name,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				new_embed.set_footer(
					text = new_footer_text,
					icon_url = new_footer_icon_url
				)
				await bot.edit_message(message, embed = new_embed)
			else:
				pass
		#Repeat for Phantom.
		elif message_id in data['PhantomMessages']:
			data['PhantomMessages'].remove(message_id)
			conn = pymysql.connect(db_ip,user=db_user,passwd=db_pass,db=db_name,connect_timeout=30)
			cur = conn.cursor(pymysql.cursors.DictCursor)
			file = open(data_file, 'w+')
			file.write(json.dumps(data, indent=4, sort_keys=True))
			file.close()
			channel = channel_id
			if str(channel) == carts_formatted_channel:
				my_channel = bot.get_channel(channel_id)
				message = await bot.get_message(my_channel, message_id)
				await bot.clear_reactions(message)
				diction = message.embeds[0]
				cart_text = diction['footer']['text']
				cart_number = int(re.search(r'\d+', cart_text).group(0))
				sql = """SELECT * FROM  """ + phantom_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				cart_info = cur.fetchall()[0]
				cart_id = cart_info['ID']
				cart_title = cart_info['Title']
				cart_author = cart_info['Author']
				cart_link = cart_info['Link']
				cart_name = cart_info['Name']
				cart_size = cart_info['Size']
				cart_profile = cart_info['Profile']
				cart_site = cart_info['Site']
				cart_account = cart_info['Account']
				cart_discord_link = cart_info['MessageID']

				embed = discord.Embed(
					title = cart_title,
					color = embed_color,
					url = cart_link,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				embed.set_author(
					name = cart_author
				)
				embed.add_field(
					name = "Item",
					value = cart_name
				)
				embed.add_field(
					name = "Size",
					value = cart_size
				)
				embed.add_field(
					name = "Profile",
					value = cart_profile
				)
				embed.add_field(
					name = "Site",
					value = cart_site
				)
				embed.add_field(
					name = "Account",
					value = cart_account
				)
				embed.set_footer(
					text = "{} | Cart #{}".format(footer_text, cart_id),
					icon_url = footer_icon
				)

				sql = """DELETE FROM  """ + phantom_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				conn.commit()
				server = message.server
				author = server.get_member(user_id)

				await bot.send_message(author, embed = embed)

				user = await bot.get_user_info(user_id)
				new_title = "Cart Claimed!"
				new_footer_text = "%s | Claimed by %s" % (footer_text, user.name)
				new_footer_icon_url = diction['footer']['icon_url']
				try:
					new_thumbnail = diction['thumbnail']['url']
				except:
					new_thumbnail = "N/A"
				new_embed = discord.Embed(
					title = new_title,
					description = "*This cart was claimed by `%s` and is no longer available.*" % user.name,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				new_embed.set_footer(
					text = new_footer_text,
					icon_url = new_footer_icon_url
				)
				await bot.edit_message(message, embed = new_embed)
			else:
				pass
		#Repeat for Balkobot.
		elif message_id in data['BalkoMessages']:
			data['BalkoMessages'].remove(message_id)
			conn = pymysql.connect(db_ip,user=db_user,passwd=db_pass,db=db_name,connect_timeout=30)
			cur = conn.cursor(pymysql.cursors.DictCursor)
			file = open(data_file, 'w+')
			file.write(json.dumps(data, indent=4, sort_keys=True))
			file.close()
			channel = channel_id
			if str(channel) == carts_formatted_channel:
				my_channel = bot.get_channel(channel_id)
				message = await bot.get_message(my_channel, message_id)
				await bot.clear_reactions(message)
				diction = message.embeds[0]
				cart_text = diction['footer']['text']
				cart_number = int(re.search(r'\d+', cart_text).group(0))
				sql = """SELECT * FROM  """ + balko_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				cart_info = cur.fetchall()[0]
				cart_id = cart_info['ID']
				cart_title = cart_info['Title']
				cart_link = cart_info['Link']
				cart_email = cart_info['Email']
				cart_pass = cart_info['Password']
				cart_size = cart_info['Size']
				cart_region = cart_info['Region']
				cart_pid = cart_info['PID']
				cart_thumbnail = cart_info['Thumbnail']
				cart_discord_link = cart_info['MessageID']

				embed = discord.Embed(
					title = cart_title,
					url = cart_link,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				embed.add_field(
					name = "Account Details",
					value = "Email: ||" + cart_email + "||\nPassword: ||" + cart_pass + "||"
				)
				embed.add_field(
					name = "Region",
					value = cart_region
				)
				embed.add_field(
					name = "Product ID",
					value = cart_pid
				)
				embed.add_field(
					name = "Size",
					value = cart_size
				)
				embed.set_footer(
					text = "{} | Cart #{}".format(footer_text, cart_id),
					icon_url = footer_icon
				)
				if cart_thumbnail == "N/A":
					pass
				else:
					embed.set_thumbnail(
						url = cart_thumbnail
					)
				sql = """DELETE FROM  """ + balko_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				conn.commit()
				server = message.server
				author = server.get_member(user_id)

				await bot.send_message(author, embed = embed)

				user = await bot.get_user_info(user_id)
				new_title = "Cart Claimed!"
				new_link = diction['url']
				new_footer_text = "%s | Claimed by %s" % (footer_text, user.name)
				new_footer_icon_url = diction['footer']['icon_url']
				try:
					new_thumbnail = diction['thumbnail']['url']
				except:
					new_thumbnail = "N/A"
				new_embed = discord.Embed(
					title = new_title,
					url = new_link,
					description = "*This cart was claimed by `%s` and is no longer available.*" % user.name,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				new_embed.set_footer(
					text = new_footer_text,
					icon_url = new_footer_icon_url
				)
				await bot.edit_message(message, embed = new_embed)
			else:
				pass
		#Repeat for Sole AIO.
		elif message_id in data['SoleAIOMessages']:
			data['SoleAIOMessages'].remove(message_id)
			conn = pymysql.connect(db_ip,user=db_user,passwd=db_pass,db=db_name,connect_timeout=30)
			cur = conn.cursor(pymysql.cursors.DictCursor)
			file = open(data_file, 'w+')
			file.write(json.dumps(data, indent=4, sort_keys=True))
			file.close()
			channel = channel_id
			if str(channel) == carts_formatted_channel:
				my_channel = bot.get_channel(channel_id)
				message = await bot.get_message(my_channel, message_id)
				await bot.clear_reactions(message)
				diction = message.embeds[0]
				cart_text = diction['footer']['text']
				cart_number = int(re.search(r'\d+', cart_text).group(0))
				sql = """SELECT * FROM  """ + sole_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				cart_info = cur.fetchall()[0]
				cart_id = cart_info['ID']
				cart_title = cart_info['Title']
				cart_link = cart_info['Link']
				cart_email = cart_info['Email']
				cart_pass = cart_info['Password']
				cart_size = cart_info['Size']
				cart_region = cart_info['Region']
				cart_proxy = cart_info['Proxy']
				cart_login = cart_info['Login']
				cart_thumbnail = cart_info['Thumbnail']
				cart_discord_link = cart_info['MessageID']

				embed = discord.Embed(
					title = cart_title,
					url = cart_link,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				embed.add_field(
					name = "**Region**",
					value = cart_region,
					inline = True
				)
				embed.add_field(
					name = "**Size**",
					value = cart_size,
					inline = True
				)
				embed.add_field(
					name = "**Email**",
					value = cart_email,
					inline = False
				)
				embed.add_field(
					name = "**Password**",
					value = cart_pass,
					inline = False
				)
				embed.add_field(
					name = "**Proxy**",
					value = cart_proxy,
					inline = False
				)
				embed.add_field(
					name = "**Mobile Login**",
					value = cart_login,
					inline = False
				)
				embed.add_field(
					name = "**Domain**",
					value = urlparse(cart_link).netloc,
					inline = False
				)
				embed.set_footer(
					text = "{} | Cart #{}".format(footer_text, cart_id),
					icon_url = footer_icon
				)
				if cart_thumbnail == "N/A":
					pass
				else:
					embed.set_thumbnail(
						url = cart_thumbnail
					)
				sql = """DELETE FROM  """ + sole_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				conn.commit()
				server = message.server
				author = server.get_member(user_id)

				await bot.send_message(author, embed = embed)

				user = await bot.get_user_info(user_id)
				new_title = "Cart Claimed!"
				new_footer_text = "%s | Claimed by %s" % (footer_text, user.name)
				new_footer_icon_url = diction['footer']['icon_url']
				try:
					new_thumbnail = diction['thumbnail']['url']
				except:
					new_thumbnail = "N/A"
				new_embed = discord.Embed(
					title = new_title,
					description = "*This cart was claimed by `%s` and is no longer available.*" % user.name,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
				)
				new_embed.set_footer(
					text = new_footer_text,
					icon_url = new_footer_icon_url
				)
				await bot.edit_message(message, embed = new_embed)
			else:
				pass
		else:
			pass

#Actuallly start the dang bot.
bot.run(TOKEN)
