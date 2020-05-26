SHELL=/bin/bash
LC=python3 plunderlist.py
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
	rm -v *.log
	touch $(LOGFILE)

clean-hard: clean
	rm -v *.err
	touch $(ERRFILE)

.PHONY: clean all clean-hard
