CREATE TABLE IF NOT EXISTS options (
  id serial PRIMARY KEY,
  option_text text NOT NULL,
  votes integer NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS votes (
  id serial PRIMARY KEY,
  voter_id text UNIQUE,
  option_id integer REFERENCES options(id),
  voted_at timestamptz DEFAULT now()
);

INSERT INTO options (option_text) VALUES
('Option A'),
('Option B')
ON CONFLICT DO NOTHING;
