#!/usr/bin/env python3
# -*- coding: utf8 -*-
# IMPORT
# from math import *
import os
# import re
import sys
import time

import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
import telegram

from private import token_todo, token_food, todo_stack, todo_queue, todo_essen, device

# # import chunk
# import subprocess as sp
# import numpy
# import pygame


startZeit = time.time()

print("\n\nProgrammstart:", datetime.now())

database = "plunderlist.db"
outFile  = "plunderlist.txt"
logFile  = "plunderlist.log"

parseMode= "HTML"
parseMode= "Markdown"

# data = list()
updatePlan = list()

bot_todo   = telegram.Bot(token=token_todo)
bot_food   = telegram.Bot(token=token_food)

test       = (len(sys.argv) > 1 and sys.argv[1] == "test")

query_skeleton = """SELECT {}
		FROM Task
		LEFT JOIN (
			List LEFT JOIN folders ON folders.list_ids LIKE ('%' || List.onlineID || '%')
		) ON Task.parentId = List.onlineId
		LEFT JOIN Reminder ON Task.onlineId = Reminder.taskId
		LEFT JOIN Note ON Task.onlineId = Note.parentId
		LEFT JOIN Subtask ON Task.onlineId = Subtask.parentId
		WHERE Task.dueDate BETWEEN '2020-01-01' AND '{:%Y-%m-%d}'
		{}"""


def myQuery(selector, now, rules = ""):
	return query_skeleton.format(selector, now, rules)

def readDateTime(string, dateOnly = False):
	if string is None:
		return None
	return datetime.strptime(string[:19], "%Y-%m-%d" if dateOnly else "%Y-%m-%dT%H:%M:%S")

def upDateTime(string, update, dateOnly = False):
	if string is None:
		return None
	oldDate = datetime.strptime(string[:19], "%Y-%m-%d" if dateOnly else "%Y-%m-%dT%H:%M:%S")
	newDate = oldDate + relativedelta(**update)
	return datetime.strftime(newDate, "%Y-%m-%d" if dateOnly else "%Y-%m-%dT%H:%M:%S") + string[19:]

def sendMessage(bot, chat, text):
	global parseMode
	success = False
	try:
		bot.send_message(chat_id=chat, text=text, parse_mode=parseMode)
		success = True
	except telegram.error.NetworkError:
		print("Mangels Internet wurde nichts geschrieben. Programm wird abgebrochen.")
		sys.exit()
	time.sleep(1)
	return success


# logging.basicConfig(filename=logFile,level=logging.INFO)


try:
	sqliteConnection = sqlite3.connect(database)
	cursor = sqliteConnection.cursor()
	


	now = datetime.utcnow()
	print("Successfully Connected to SQLite at", now)
	nextTask = 86400
	# sqlite_select_query = 
	cursor.execute(myQuery("*", now))
	# records = cursor.fetchall()
	# print("Total rows are:  ", len(records))
	# print("Printing each row")
	for todo in cursor.fetchall():
		ID              = todo[1]
		name            = todo[8]
		createDate      = readDateTime(todo[4]) # Erstelldatum
		date            = todo[56]
		dueDate         = todo[9]
		dateObj         = readDateTime(date)
		dueDateObj      = readDateTime(dueDate, dateOnly=True)

		recurrenceType  = todo[18]
		recurrenceCount = todo[19] 

		folderTitle     = todo[43]
		kategorieTitle  = todo[29]
		anmerkung       = todo[68]
		subtask         = todo[81]


		# if recurrenceType == "week":
		# 	recurrenceCount *= 7
		# 	recurrenceType  = "day"
		
		if recurrenceType is None:
			assert recurrenceCount == 0, name
			newDate    = None
			newDueDate = None
		else:
			assert recurrenceCount is not None, name
			updater    = {recurrenceType +"s": recurrenceCount}
			newDate    = upDateTime(   date, updater)
			newDueDate = upDateTime(dueDate, updater, dateOnly=True)

		kategorie = ("" if folderTitle is None or folderTitle == kategorieTitle else (folderTitle + " - ")) + kategorieTitle
		
		if date is not None and now < dateObj:# or date.year < 2020:
			future = int((dateObj - now).total_seconds())
			nextTask = min(nextTask, future)
			# print(name, "wird ignoriert. (", future,"s in der Zukunft)") # TODO fertigschreiben
			if not test:
				continue
		
		if kategorie == "Einkaufsliste" and now.hour < 8:
			future = "?" # int( - now.timestamp()).total_seconds())
			# print("Einkauf", name, "wird aufgeschoben. (", future,"s in der Zukunft)")
			continue



		if date is None and now.hour < 7:
			future = "?" # int( - now.timestamp()).total_seconds())
			# print(name, "wird aufgeschoben. (", future,"s in der Zukunft)")
			continue

		# print("Id:              ",              ID)
		# print("Name:            ",            name)
		# print("Aktuelle Zeit:   ",             now)
		# print("Datum:           ",            date)
		# print("nächstes Datum:  ",         newDate)
		# print("Fällig:          ",         dueDate)
		# print("Nächstes fällig: ",      newDueDate)
		# print("Kategorie:       ",       kategorie)
		# print("Anmerkung:       ",       anmerkung)
		# print("Subtask:         ",         subtask)
		# print("recurrenceType:  ",  recurrenceType)
		# print("recurrenceCount: ", recurrenceCount)
		# print(                                    )

		if not test:
			updatePlan.append((ID, newDueDate, newDate))
		telegramm  = "*"+ name +"*"
		telegramm += "    ("+ kategorie +")"
		if subtask is not None:
			telegramm += "\n"+ subtask
		if anmerkung is not None:
			telegramm += "\n"+ anmerkung
		telegramm += "\n\nAktuell: "+ dueDate +("" if date is None else ", "+ date)
		if newDueDate is not None:
			telegramm += "\nNächste Wiederholung: "+ newDueDate +("" if newDate is None else ", "+ newDate)
		telegramm += "\nID = "+ str(ID) + ("" if recurrenceType is None else " (every "+ (recurrenceType if recurrenceCount == 1 else str(recurrenceCount) +" "+ recurrenceType +"s") +")")
		# telegramm += "\nGerät: Laptop"
		telegramm += "\nGerät: "+ device

		# print(telegramm, "\n\n")


		if kategorie == "Einkaufsliste":
			chat = todo_essen
			bot  =  bot_food

			text = telegramm
			text = name # TODO
			sendMessage(bot, chat, text)
			if date is None:
				continue


		chat = todo_stack if True else todo_queue # TODO
		bot  =  bot_todo
		
		sendMessage(bot, chat, telegramm)
		if test:
			break



	for todo in updatePlan:
		
		sqliteConnection.execute("UPDATE Task SET dueDate = '"+ todo[1] +"' WHERE onlineId = '"+ str(todo[0]) +"'")
		if todo[2] is not None:
			sqliteConnection.execute("UPDATE Reminder SET reminderDate = '"+ todo[2] +"' WHERE taskId = '"+ str(todo[0]) +"'")
		sqliteConnection.commit()
	print("Folgenden Update-Plan umgesetzt:")
	print(updatePlan)



	cursor.close()
except sqlite3.Error as error:
	print("Error while connecting to sqlite", error)
finally:
	if (sqliteConnection):
		sqliteConnection.close()
		print("The SQLite connection is closed")



# print(nextTask) # TODO Nutzen




laufzeit = time.time() - startZeit
print("plunderlist.py nach {:.3f} Sekunden erfolgreich beendet.".format(laufzeit))
