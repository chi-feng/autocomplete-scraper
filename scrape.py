import requests
import urllib
import sqlite3
import json

options = {
    "allowed_chars": "0123456789 abcdefghijklmnopqrstuvwxyz()-+,'.", # characters that can be entered into the autocomplete field
    "max_suggestions": 10, # maximum number of autocomplete suggestions
    "sqlite_db": "data.db",
    "threads": 4,
    "test": True,
    "test-server-port":8888,
    "queries": 0
}

if options['test']:
    options['allowed_chars'] = 'abcdefghijklmnopqrstuvwxyz'

def init_tables(cursor):
    ''' create and initialize tables if they don't exist'''
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", ('search_strings',));
    result = cursor.fetchone()
    if result == None:
        print('Initializing tables')
        cursor.execute("CREATE TABLE search_strings (search_string text, complete, count, results text)")
        cursor.execute("CREATE UNIQUE INDEX search_string_idx ON search_strings(search_string)")
        cursor.execute("CREATE TABLE entries (entry text, search_string text)")
        cursor.execute("CREATE UNIQUE INDEX entry_idx ON entries(entry)")
        # initial starting points
        cursor.executemany("INSERT INTO search_strings VALUES (?,?,?,?)", [(c, 0, 0, '') for c in options['allowed_chars']])
        conn.commit()
    else:
        print('Continuing from last run')

def get_suggestions(search_str):
    ''' returns a list of autocomplete suggestions from a search string '''
    options['queries'] += 1;
    if options['test']:
        return requests.post('http://localhost:{}/autocomplete'.format(options['test-server-port']), data={'search_string':search_str}).json()
    else:
        encoded = urllib.quote_plus(search_str)
        url = r'https://iaspub.epa.gov/apex/pesticides/wwv_flow.show?p_flow_id=303&p_instance=10711788035550&p_flow_step_id=1&x01=' + encoded + '&p_request=APPLICATION_PROCESS%3DgetChemicals';
        result = requests.get(url).json()
        return [suggestion[u'LABEL'] for suggestion in result[u'row']]

def search(cursor, prefix, depth=0):
    ''' performs a recursive search on autocomplete suggestions with a given prefix
        and skips any searches that have been marked as complete in the sqlite db '''

    # check if prefix is present in search_strings table
    cursor.execute("SELECT complete FROM search_strings WHERE search_string=?", (prefix,))
    result = cursor.fetchone()
    # if the prefix is marked as complete, then we are done
    if result != None and result[0] == 1:
        print('%-10s complete' % (prefix))
        return
    else:
        suggestions = get_suggestions(prefix)
        if len(suggestions) > 0:
            print('%-10s %3d' % (prefix, len(suggestions)))
        else:
            print('%-10s' % prefix)
        cursor.execute("INSERT OR REPLACE INTO search_strings VALUES (?,?,?,?)", (prefix, 0, len(suggestions), json.dumps(suggestions)))

    # no suggestions
    if len(suggestions) == 0:
        pass

    # suggestions are complete, add entries to database
    elif len(suggestions) < options['max_suggestions']:
        cursor.executemany("INSERT OR REPLACE INTO entries VALUES (?,?)", [(suggestion, prefix) for suggestion in suggestions])

    # suggestions are incomplete (assume some got cut off) need to recurse
    elif len(suggestions) == options['max_suggestions']:
        for char in options['allowed_chars']:
            search(cursor, prefix + char, depth + 1)

    # at this point, all strings with the given prefix have been searched
    cursor.execute("UPDATE search_strings SET complete=1 WHERE search_string=?", (prefix,))
    conn.commit()


# connect to sqlite db and initialize tables if necessary
conn = sqlite3.connect(options['sqlite_db'])
cursor = conn.cursor()
init_tables(cursor)

# get search strings that still need to be processed
cursor.execute('SELECT search_string FROM search_strings WHERE complete=0')
rows = cursor.fetchall()
incomplete = [row[0] for row in rows]

for prefix in incomplete:
    search(cursor, prefix)

''' This is a bad idea: from the SQLite documentation:
    Do not use the same database connection at the same time in more than one thread.

def f(prefix):
    search(cursor, prefix)

from multiprocessing import Pool

p = Pool(options['threads'])
p.map(f, incomplete_search_strings)

'''

conn.close()

print(options['queries'])
