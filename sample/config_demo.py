'''
INI configuration file read/write demo

@author hanwhhanwh@gmail.com
@date 2020-10-06
'''

import configparser

config = configparser.ConfigParser()

config.read('./config/db.ini')
sec = config.sections()
print('sections() = ', sec)

if ("DB" in config):
	print("\n'DB' in config")
	db = config["DB"]
	print(db)

if (config.has_section("DB")):
	print("\nconfig.has_section('DB')")
	items = config.items("DB")
	print(items)

	options = config.options("DB")
	print(options)

if (config.has_option("DB", "host")):
	print("\nconfig.has_option('DB', 'host')")
	host = config.get("DB", "host")
	print(host)

if ("db_name" in db):
	print("\n'db_name' in db")
	print(db["db_name"])

if ("option_nothing" in db):
	print(db["option_nothing"])

# occur >> KeyError: 'option_nothing'
print(db["option_nothing"])
