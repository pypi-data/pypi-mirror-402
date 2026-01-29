CREATE TABLE gqlite_{{ graph_name }}_nodes(
    id SERIAL PRIMARY KEY,
    node_key UUID NOT NULL,
    labels TEXT[] NOT NULL,
    properties JSONB NOT NULL);
CREATE TABLE gqlite_{{ graph_name }}_edges(
        id SERIAL PRIMARY KEY,
        edge_key UUID NOT NULL, 
        labels TEXT[] NOT NULL,
        properties JSONB NOT NULL,
        "left" INTEGER NOT NULL,
        "right" INTEGER NOT NULL,
        FOREIGN KEY("left") REFERENCES gqlite_{{ graph_name }}_nodes(id),
        FOREIGN KEY("right") REFERENCES gqlite_{{ graph_name }}_nodes(id));

---------------- views ----------------

-- view for querying for undirected edges
CREATE VIEW gqlite_{{ graph_name }}_edges_undirected (id, edge_key, labels, properties, "left", "right", reversed) AS
        SELECT id, edge_key, labels, properties, "left", "right", 0 FROM gqlite_{{ graph_name }}_edges
        UNION SELECT id, edge_key, labels, properties, "right", "left", 1 FROM gqlite_{{ graph_name }}_edges;
