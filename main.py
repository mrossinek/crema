#!/usr/bin/python3
import argparse
import configparser
import pdftotext
import re
import requests
import sqlite3
import sys

API_URL = "https://doi.org/"
HEADER = {'Accept': "application/x-bibtex"}
DOI_REGEX = r'(10\.[0-9a-zA-Z]+\/(?:(?!["&\'])\S)+)\b'
TABLE_KEYS = {
    'doi':      "primary key not null",
    'type':     "not null",
    'label':    "not null",
    'file':     "",
    'tags':     "",
    'abstract': ""
    }
BIBTEX_TYPES = {
    'article': ['author', 'title', 'journal', 'year'],
    'book': ['author', 'title', 'year'],
    'collection': ['editor', 'title', 'year'],
    'proceedings': ['title', 'year'],
    'report': ['author', 'title', 'type', 'institution', 'year'],
    'thesis': ['author', 'title', 'type', 'institution', 'year'],
    'unpublished': ['author', 'title', 'year']
    }

config = configparser.ConfigParser()
config.read('config.ini')
conf_database = dict(config['DATABASE'])


def init(args):
    conn = sqlite3.connect(conf_database['path'])
    cmd = "create table "+conf_database['table']+"(\n"
    for type, keys in BIBTEX_TYPES.items():
        for key in keys:
            if key not in TABLE_KEYS.keys():
                TABLE_KEYS[key] = ""
    for key, params in TABLE_KEYS.items():
        cmd += key+' text '+params+',\n'
    cmd = cmd[:-2]+'\n)'
    conn.execute(cmd)
    conn.commit()


def list(args):
    conn = sqlite3.connect(conf_database['path'])
    cursor = conn.execute("SELECT rowid, doi, label FROM "+conf_database['table'])
    for row in cursor:
        print(row)


def show(args):
    conn = sqlite3.connect(conf_database['path'])
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM "+conf_database['table']+" WHERE rowid = "+str(args.id))
    for row in cursor:
        print(dict_to_bibtex(dict(row)))


def add(args):
    dois = []
    def flatten(l): return [item for sublist in l for item in sublist]
    if args.pdf is not None:
        def most_common(lst: list): return max(set(matches), key=matches.count)
        for pdf in args.pdf:
            pdf = pdftotext.PDF(pdf)
            text = "".join(pdf)
            matches = re.findall(DOI_REGEX, text)
            dois.append(most_common(matches))
    if args.doi is not None:
        dois.extend(args.doi)
    for doi in dois:
        assert(re.match(DOI_REGEX, doi))
        page = requests.get(API_URL+doi, headers=HEADER)
        insert_from_bibtex(page.text)


def insert_from_bibtex(bibtex: str):
    # load database info
    conn = sqlite3.connect(conf_database['path'])
    cursor = conn.execute("PRAGMA table_info("+conf_database['table']+")")
    table_keys = [row[1] for row in cursor]

    # extract information from bibtex
    entry = bibtex_to_dict(bibtex)
    keys = ''
    values = ''
    for key, value in entry.items():
        if key not in table_keys:
            cursor.execute("ALTER TABLE "+conf_database['table']+" ADD COLUMN "+key+" text")
            cursor = conn.execute("PRAGMA table_info("+conf_database['table']+")")
            table_keys = [row[1] for row in cursor]
        keys = "{},{}".format(keys, key)
        values = "{},'{}'".format(values, value)

    keys = keys.strip(',')
    values = values.strip(',')

    # insert into table
    cmd = "INSERT INTO "+conf_database['table']+" ("+keys+") VALUES ("+values+")"
    cursor.execute(cmd)
    conn.commit()
    conn.close()


def bibtex_to_dict(bibtex: str):
    entry = {}
    lines = bibtex.split('\n')
    entry['type'] = re.findall(r'^@([a-zA-Z]*){', lines[0])[0]
    entry['label'] = re.findall(r'{(\w*),$', lines[0])[0]
    for line in lines[1:-1]:
        key, value = line.split('=')
        entry[key.strip()] = value.strip(' ,{}')
    return entry


def dict_to_bibtex(entry: dict):
    bibtex = "@"+entry['type']+"{"+entry['label']
    for key in sorted(entry):
        if entry[key] is not None and key not in ['type', 'label']:
            bibtex += "\n\t"+key+" = {"+str(entry[key])+"},"
    bibtex = bibtex.strip(',')+"\n}"
    return bibtex


def main():
    parser = argparse.ArgumentParser(description="Process input arguments.")
    subparsers = parser.add_subparsers(help="sub-command help")
    parser_init = subparsers.add_parser("init", help="initialize the database")
    parser_init.set_defaults(func=init)
    parser_list = subparsers.add_parser("list", help="list entries from the database")
    parser_list.set_defaults(func=list)
    parser_show = subparsers.add_parser("show", help="show an entry from the database")
    parser_show.add_argument("id", type=int, help="row ID of the entry")
    parser_show.set_defaults(func=show)
    parser_add = subparsers.add_parser("add", help="add help")
    group_add = parser_add.add_mutually_exclusive_group()
    group_add.add_argument("-d", "--doi", type=str, nargs='+',
                           help="DOI of the new references")
    group_add.add_argument("-p", "--pdf", type=argparse.FileType('rb'),
                           nargs='+', help="PDFs files to be added")
    parser_add.set_defaults(func=add)

    if (len(sys.argv) == 1):
        parser.print_usage(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
