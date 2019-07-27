default: front back

front:
	./node_modules/taiko/bin/taiko.js front.js --observe
back:
	pipenv run python ./worker.py
