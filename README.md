# mockupfle

## Install

```
python -m pip install git+https://github.com/mongodb-labs/mongo-mockup-fle.git
```

## Run

```
$ mockupfle
Listening with domain socket /tmp/mongofle.sock
URI is mongodb://%2Ftmp%2Fmongofle.sock
```

Connect to the server with the mongo shell and issue a command:

```
$ mongo 'mongodb://%2Ftmp%2Fmongofle.sock'
Server has startup warnings:
hello from mockupfle!
> db.runCommand({markFields: 'foo', data: [{x: 1, encryptMe: 1}], schema: {}})
{
	"ok" : 1,
	"data" : [
		{
			"x" : 1,
			"encryptMe" : BinData(7,"")
		}
	]
}
```

Stop the server with Ctrl-C from the terminal where you started ``mockupfle``,
or with ``db.shutdownServer()`` from the mongo shell.

### Run as a Daemon
Runs mockupfle in the background, and only permits one mockupfle to run at once.
```
$ mockupfle --daemonize
Running as a background process
PID=51701
Logging to /usr/local/var/log/mockupfle.log
```
