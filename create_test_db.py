import sqlite3
import glob
import json
# conn = sqlite3.connect(':memory:')
conn = sqlite3.connect('instance/ipsportal.sqlite')

c = conn.cursor()

# Create runid table
# c.execute('''create table run(id integer, portal_runid text, state text, rcomment text, tokamak text, shotno integer)''')
# Create event table
# c.execute('''create table event(code text, eventtype text, comment text, walltime text, phystimestamp real, portal_runid text, seqnum integer, time text)''')

json_files = glob.glob('/tmp/pytest-of-rwp/pytest-current/*current/**/*.json', recursive=True)

for n, json_file in enumerate(json_files):
    with open(json_file) as f:
        json_lines = f.readlines()
    for line in json_lines:
        event = json.loads(line)
        if event.get('eventtype') == "IPS_START":
            c.execute("insert into run (portal_runid, state, rcomment, tokamak, shotno, simname, host, user, startat) VALUES (?,?,?,?,?,?,?,?,?)",
                      (event.get('portal_runid'),
                       event.get('state'),
                       event.get('rcomment'),
                       event.get('tokamak'),
                       event.get('shotno'),
                       event.get('simname'),
                       event.get('host'),
                       event.get('user'),
                       event.get('startat')))

        c.execute("insert into event (code, eventtype, comment, walltime, phystimestamp, portal_runid, seqnum) VALUES (?,?,?,?,?,?,?)",
                  (event.get('code'),
                   event.get('eventtype'),
                   event.get('comment'),
                   event.get('walltime'),
                   event.get('phystimestamp'),
                   event.get('portal_runid'),
                   event.get('seqnum')))
    conn.commit()

c.execute('SELECT * FROM run')
for run in c.fetchall():
    # print('RunID = {} portal_runid = {}'.format(*run))
    print(run)
    # for e in c.execute('SELECT * FROM event WHERE portal_runid=?', (run[1],)):
    #    print(e)

conn.close()
