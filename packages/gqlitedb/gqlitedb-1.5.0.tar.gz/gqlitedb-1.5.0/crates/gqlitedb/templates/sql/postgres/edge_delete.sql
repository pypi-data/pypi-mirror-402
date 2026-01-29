DELETE FROM gqlite_{{ graph_name }}_edges WHERE edge_key = ANY (ARRAY['{{ keys | join("'::uuid, '") }}'::uuid])
