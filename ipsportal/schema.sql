DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE run (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  portal_runid TEXT UNIQUE NOT NULL,
  state TEXT,
  rcomment TEXT,
  tokamak TEXT,
  shotno INTEGER,
  simname TEXT,
  host TEXT,
  user TEXT,
  startat TEXT,
  simrunid TEXT,
  outputprefix TEXT,
  tag TEXT,
  simroot TEXT
);

CREATE TABLE event (
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  code TEXT,
  eventtype TEXT,
  ok TEXT,
  comment TEXT,
  walltime TEXT,
  phystimestamp REAL,
  portal_runid TEXT,
  seqnum INTEGER,
  vizurl TEXT,
  FOREIGN KEY (portal_runid) REFERENCES run (portal_runid)
);
