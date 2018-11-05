# mockupcryptd

## Install

```
python -m pip install git+https://github.com/mongodb-labs/mockupcryptd.git
```

## Run

```
$ mockupcryptd
Listening with domain socket /tmp/mongocryptd.sock
URI is mongodb://%2Ftmp%2Fmongocryptd.sock
```

Connect to the server with the mongo shell and issue a command:

```
$ mongo 'mongodb://%2Ftmp%2Fmongocryptd.sock'
Server has startup warnings:
hello from mockupcryptd!
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

Stop the server with Ctrl-C from the terminal where you started ``mockupcryptd``,
or with ``db.shutdownServer()`` from the mongo shell.

### Run as a Daemon

Runs mockupcryptd in the background, and only permits one mockupcryptd to run at
once.

```
$ mockupcryptd --daemonize
Running as a background process
PID=51701
Logging to /usr/local/var/log/mockupcryptd.log
```
