# Configurator

## Pre-requirement
* Python 3.X
Get it from here: https://www.python.org/downloads/
* Paramiko and SCP
Used for SSH connection and SCP file transfer. Install them by:
```
pip install scp
```
* PyInstaller
Used for build and pack python script on Windows. Install by:
```
pip install pyinstaller
```

## Build on Windows
Make sure python and pyinstaller are in your PATH environment variable, double click windows_build.bat and you'll get an exe file and config.json in "dist" directory.

## Config.json
All configuration settings are in this file. 
* `remote` section 
Used for setting remote connection and paths. Here's one example:
```
	"remote":
	{
		"host": "192.168.0.100",
		"username": "root",
		"password": "",
		"params_path": "/mnt/storage/Profile.txt",
		"log_path": "/mnt/storage/Fault.txt"
	},
```
* `param` section
Used for define fields in remote config file. `param` is an array, here's one example of its elements:
```
	"params":
	[
		{
			"name": "SpeedStage_Set",
			"description": "速度等级",
			"type": "unsigned char",
			"offset": 0,
			"editable": true
		},
		{
			"name": "Position_Add",
			"description": "累计里程",
			"type": "double",
			"offset": 1,
			"editable": true
		}
	]
```
If you need some new field, just append to the `param` section with some descriptions as above.
Follow this link to get more information about json files: https://www.w3schools.com/js/js_json_intro.asp