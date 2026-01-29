DELETE FROM gqlite_{{ graph_name }}_nodes WHERE node_key = ANY (ARRAY['{{ keys | join("'::uuid, '") }}'::uuid])
