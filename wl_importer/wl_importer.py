#!/usr/bin/env python3

"""
Reads in a json file containing one or more whitelists and inserts them
into a redis db.
"""

import argparse
import json
import logging
import redis
from urllib.parse import urlparse
import uuid

program_version = '1.0.0'
program_name = 'wl_importer'
program_description = (
    'Program to read whitelists from a json file and insert them into '
    'a redis DB'
)
arg_list = []

arg_list.append(
    [ [ '--version', '-v' ],
      { 'action' : 'version',
        'version' : '%%(prog)s version %s' % program_version
      } ]
)
arg_list.append(
    [ [ '--wl_source', '-s' ],
      { 'dest' : 'wl_source',
        'metavar' : '<string>',
        'help' : 'File containing whitelists to read in'
      } ]
)
arg_list.append(
    [ [ '--redis_db', '-r' ],
      { 'dest' : 'redis_db',
        'metavar' : '<string>',
        'help' : 'URL used to access the redis DB'
      } ]
)


arg_parser = argparse.ArgumentParser(prog=program_name,
    description=program_description)
for arg in arg_list:
    arg_parser.add_argument(*arg[0], **arg[1])
config = arg_parser.parse_args()

with open(config.wl_source, mode='r') as f:
    data_from_file = json.load(f)

conn = redis.Redis.from_url(config.redis_db)

for (key, value) in data_from_file.items():
    for entry in value:  # expect a list of dicts
        try:
            name = entry['name']
            del entry['name']
        except KeyError:
            name = str(uuid.uuid4())
        for (ekey, evalue) in entry.items():
            conn.hset(name, ekey, evalue)
        conn.rpush(key, name)
    conn.rpush('whitelists', key)

