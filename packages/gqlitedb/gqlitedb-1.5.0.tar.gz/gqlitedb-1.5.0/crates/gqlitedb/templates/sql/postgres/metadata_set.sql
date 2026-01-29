INSERT INTO gqlite_metadata (name, value) VALUES ($1, $2) ON CONFLICT(name) DO UPDATE SET value=$2
