import asyncio
import time
import os
import random
import string
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import sqlite3
import pymysql
import re
import logging
import traceback
import sys
import datetime
import json

global data, logs_channels

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
	TOKEN = config['TOKEN']
	db_ip = config['database_ip']
	db_user = config['database_username']
	db_pass = config['database_password']
	db_name = config['database_name']
	footer_icon = config['footer_icon_url']
	online_message = config['online_message']
	prefix = config['prefix']

start_time = time.time()

conn = pymysql.connect(db_ip,user=db_user,passwd=db_pass,db=db_name,connect_timeout=30)
cur = conn.cursor(pymysql.cursors.DictCursor)

create_db = """CREATE TABLE IF NOT EXISTS """ + adi_table + """ (ID INT NOT NULL IDENTITY PRIMARY KEY, Title text, Link text, Email text, Password text, Size text, Desktop text, Mobile text, PID text, Thumbnail text, MessageID text, Timestamp text, Proxy text, HMAC text);"""
cur.execute(create_db)
create_db = """CREATE TABLE IF NOT EXISTS """ + latch_table + """ (ID INT NOT NULL IDENTITY PRIMARY KEY, Title text, Link text, Email text, Password text, Size text, Region text, PID text, Thumbnail text, MessageID text);"""
cur.execute(create_db)
create_db = """CREATE TABLE IF NOT EXISTS """ + phantom_table + """ (ID INT NOT NULL IDENTITY PRIMARY KEY, Title text, Description text, Name text, Size text, Profile text, Site text, Account text, MessageID text);"""
cur.execute(create_db)
create_db = """CREATE TABLE IF NOT EXISTS """ + balko_table + """ (ID INT NOT NULL IDENTITY PRIMARY KEY, Title text, Link text, Email text, Password text, Size text, Region text, PID text, Thumbnail text, MessageID text);"""
cur.execute(create_db)
conn.commit()

if os.path.isfile(data_file):
	file = open(data_file).read()
	if len(file) > 0:
		data = json.loads(file)
		print(data)
	else:
		data = {}
		data['IsDeleting'], data['AdiSplashMessages'], data['LatchKeyMessages'], data['PhantomMessages'], data['BalkoMessages'] = [], [], [], [], []
else:
	file = open(data_file, 'w+')
	file.close()
	data = {}
	data['IsDeleting'], data['AdiSplashMessages'], data['LatchKeyMessages'], data['PhantomMessages'], data['BalkoMessages'] = [], [], [], [], []

file = open(data_file, 'w+')
file.write(json.dumps(data, indent=4, sort_keys=True))
file.close()

"""
Writing data to json method:

file = open(data_file, 'w+')
file.write(json.dumps(data, indent=4, sort_keys=True))
file.close()
"""

Client = discord.Client()

bot = commands.Bot(command_prefix = "?")

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

@bot.event
async def on_message(message):
	if message.server:
		if len(message.embeds) > 0 and 'title' in message.embeds[0].keys() and (message.embeds[0]['title'] == "**You must include a command.**" or message.embeds[0]['title'] == "**Unrecognized Command**" or message.embeds[0]['title'] == "**Insufficient Permissions**") and message not in data['IsDeleting']:
			data['IsDeleting'].append(message)
			await asyncio.sleep(15)
			await bot.delete_message(message)
			data['IsDeleting'].remove(message)

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

		if len(message.embeds) > 0:
			conn = pymysql.connect(db_ip,user=db_user,passwd=db_pass,db=db_name,connect_timeout=30)
			cur = conn.cursor(pymysql.cursors.DictCursor)
			if str(message.channel.id) == carts_original_channel and message.author.id != bot.user.id:
				diction = message.embeds[0]
				if "AdiSplash" in str(message.embeds[0]['footer']['text']):
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

					insert_data = """INSERT INTO  """ + adi_table + """ (Title, Link, Email, Password, Size, Desktop, Mobile, PID, Thumbnail, MessageID, Timestamp, Proxy, HMAC) VALUES ('""" + title + """', '""" + link + """', '""" + email + """', '""" + password + """', '""" + size + """', '""" + desktop_link + """', '""" + mobile_link + """', '""" + pid + """', '""" + thumbnail + """','""" + message_id + """', '""" + timestamp + """', '""" + proxy + """', '""" + hmac + """');"""
					cur.execute(insert_data)
					conn.commit()

					sql = "SELECT * FROM `" + adi_table + "` ORDER BY ID DESC LIMIT 1"
					cur.execute(sql)
					entry_number = cur.fetchall()
					entry_number = entry_number[0]['ID'] + 1

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
						name = "**TIMESTAMP**",
						value = timestamp
					)
					if thumbnail != "N/A":
						embed.set_thumbnail(
							url = thumbnail
						)
					else:
						embed.set_thumbnail(
							url = bot.user.avatar_url
						)
					try:
						embed.set_footer(
							text = "{} | Cart #{}".format(footer_text, entry_number),
							icon_url = bot.user.avatar_url
						)
					except:
						embed.set_footer(
							text = "{} | Cart #{}".format(footer_text, entry_number),
						)
					r = await bot.send_message(discord.Object(id=carts_formatted_channel), embed = embed)
					data['AdiSplashMessages'].append(r.id)
					file = open(data_file, 'w+')
					file.write(json.dumps(data, indent=4, sort_keys=True))
					file.close()

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

					insert_data = """INSERT INTO  """ + latch_table + """ (Title, Link, Email, Password, Size, Desktop, Mobile, PID, Thumbnail, MessageID, Timestamp, Proxy, HMAC) VALUES ('""" + title + """', '""" + link + """', '""" + email + """', '""" + password + """', '""" + size + """', '""" + desktop_link + """', '""" + mobile_link + """', '""" + pid + """', '""" + thumbnail + """','""" + message_id + """', '""" + timestamp + """', '""" + proxy + """', '""" + hmac + """');"""
					cur.execute(insert_data)
					conn.commit()

					sql = "SELECT * FROM `" + latch_table + "` ORDER BY ID DESC LIMIT 1"
					cur.execute(sql)
					entry_number = cur.fetchall()
					entry_number = entry_number[0]['ID'] + 1

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
						embed.set_thumbnail(
							url = thumbnail
						)
					else:
						embed.set_thumbnail(
							url = bot.user.avatar_url
						)
					try:
						embed.set_footer(
							text = "{} | Cart #{}".format(footer_text, entry_number),
							icon_url = bot.user.avatar_url
						)
					except:
						embed.set_footer(
							text = "{} | Cart #{}".format(footer_text, entry_number),
						)
					r = await bot.send_message(discord.Object(id=carts_formatted_channel), embed = embed)
					data['LatchKeyMessages'].append(r.id)
					file = open(data_file, 'w+')
					file.write(json.dumps(data, indent=4, sort_keys=True))
					file.close()

				elif "Phantom" in str(message.embeds[0]['footer']['text']):
					title = diction['title']
					description = diction['description']
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

					insert_data = """INSERT INTO  """ + phantom_table + """ (Title, Link, Email, Password, Size, Desktop, Mobile, PID, Thumbnail, MessageID, Timestamp, Proxy, HMAC) VALUES ('""" + title + """', '""" + link + """', '""" + email + """', '""" + password + """', '""" + size + """', '""" + desktop_link + """', '""" + mobile_link + """', '""" + pid + """', '""" + thumbnail + """','""" + message_id + """', '""" + timestamp + """', '""" + proxy + """', '""" + hmac + """');"""
					cur.execute(insert_data)
					conn.commit()

					sql = "SELECT * FROM `" + phantom_table + "` ORDER BY ID DESC LIMIT 1"
					cur.execute(sql)
					entry_number = cur.fetchall()
					entry_number = entry_number[0]['ID'] + 1

					embed = discord.Embed(
						title = title,
						description = description,
						color = embed_color,
						timestamp = datetime.datetime.now(datetime.timezone.utc)
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
						icon_url = bot.user.avatar_url
					)
					r = await bot.send_message(discord.Object(id=carts_formatted_channel), embed = embed)
					data['PhantomMessages'].append(r.id)
					file = open(data_file, 'w+')
					file.write(json.dumps(data, indent=4, sort_keys=True))
					file.close()

				elif "Balkobot" in str(message.embeds[0]['footer']['text']):
					title = diction['title']
					url = diction['url']
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

					insert_data = """INSERT INTO  """ + balko_table + """ (Title, Link, Email, Password, Size, Desktop, Mobile, PID, Thumbnail, MessageID, Timestamp, Proxy, HMAC) VALUES ('""" + title + """', '""" + link + """', '""" + email + """', '""" + password + """', '""" + size + """', '""" + desktop_link + """', '""" + mobile_link + """', '""" + pid + """', '""" + thumbnail + """','""" + message_id + """', '""" + timestamp + """', '""" + proxy + """', '""" + hmac + """');"""
					cur.execute(insert_data)
					conn.commit()

					sql = "SELECT * FROM `" + balko_table + "` ORDER BY ID DESC LIMIT 1"
					cur.execute(sql)
					entry_number = cur.fetchall()
					entry_number = entry_number[0]['ID'] + 1

					embed = discord.Embed(
						title = title,
						url = url,
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
					try:
						embed.set_footer(
							text = "{} | Cart #{}".format(footer_text, entry_number),
							icon_url = bot.user.avatar_url
						)
					except:
						embed.set_footer(
							text = "{} | Cart #{}".format(footer_text, entry_number),
						)
					if thumbnail != "N/A":
						embed.set_thumbnail(
							url = thumbnail
						)
					else:
						embed.set_thumbnail(
							url = bot.user.avatar_url
						)
					r = await bot.send_message(discord.Object(id=carts_formatted_channel), embed = embed)
					data['BalkoMessages'].append(r.id)
					file = open(data_file, 'w+')
					file.write(json.dumps(data, indent=4, sort_keys=True))
					file.close()

			elif str(message.channel.id) == carts_formatted_channel and message.author.id == bot.user.id:
				await bot.add_reaction(message, "🛒")
			else:
				pass

@bot.event
async def on_socket_raw_receive(the_reaction):
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
		if user_id == bot.user.id:
			pass
		elif message_id in data['AdiSplashMessages']:
			data['AdiSplashMessages'].remove(message_id)
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
				sql = """SELECT * FROM  """ + adi_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				cart_info = cur.fetchall()[0]
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
					name = "**TIMESTAMP**",
					value = cart_timestamp,
					inline = False
				)
				try:
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, cart_id),
						icon_url = bot.user.avatar_url
					)
				except:
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, cart_id),
					)
				if cart_thumbnail == "N/A":
					embed.set_thumbnail(
						url = bot.user.avatar_url
					)
				else:
					embed.set_thumbnail(
						url = cart_thumbnail
					)
				sql = """DELETE FROM  """ + adi_table + """ WHERE ID = %s""" % cart_number
				cur.execute(sql)
				conn.commit()
				server = message.server
				author = server.get_member(user_id)

				await bot.send_message(author, embed = embed)

				user = await bot.get_user_info(user_id)
				new_title = "Cart Claimed!"
				new_link = diction['url']
				new_footer_text = "%s | Claimed by %s" % (bot.user.name, user.name)
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
				try:
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, cart_id),
						icon_url = bot.user.avatar_url
					)
				except:
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, cart_id),
					)
				if cart_thumbnail == "N/A":
					embed.set_thumbnail(
						url = bot.user.avatar_url
					)
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
				cart_description = cart_info['Description']
				cart_name = cart_info['Name']
				cart_size = cart_info['Size']
				cart_profile = cart_info['Profile']
				cart_site = cart_info['Site']
				cart_account = cart_info['Account']
				cart_discord_link = cart_info['MessageID']

				embed = discord.Embed(
					title = cart_title,
					description = cart_description,
					color = embed_color,
					timestamp = datetime.datetime.now(datetime.timezone.utc)
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
				try:
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, cart_id),
						icon_url = bot.user.avatar_url
					)
				except:
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, cart_id),
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
				try:
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, cart_id),
						icon_url = bot.user.avatar_url
					)
				except:
					embed.set_footer(
						text = "{} | Cart #{}".format(footer_text, cart_id),
					)
				if cart_thumbnail == "N/A":
					embed.set_thumbnail(
						url = bot.user.avatar_url
					)
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
		else:
			pass

bot.run(TOKEN)
