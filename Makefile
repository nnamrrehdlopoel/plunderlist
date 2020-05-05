SHELL=/bin/bash
LC=./plunderlist.py
FOLDER=Logs/ # ?
LOGFILE=plunderlist.log
ERRFILE=plunderlist.err
FLAGS=1>>$(LOGFILE) 2>>$(ERRFILE)

all:
	$(LC) $(FLAGS)

test:
	$(LC) test $(FLAGS)

bot:
	./bot.py $(FLAGS)

clean:
	rm -v $(LOGFILE)
	touch $(LOGFILE)

clean-hard: clean
	rm -v $(ERRFILE)
	touch $(ERRFILE)

.PHONY: clean all clean-hard
