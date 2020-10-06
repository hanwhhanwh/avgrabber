'''
INI configuration file read/write demo

@author hanwhhanwh@gmail.com
@date 2020-10-06
'''

import configparser

config = configparser.ConfigParser()

config.read('./config/db.ini')
sec = config.sections()
print(sec)
