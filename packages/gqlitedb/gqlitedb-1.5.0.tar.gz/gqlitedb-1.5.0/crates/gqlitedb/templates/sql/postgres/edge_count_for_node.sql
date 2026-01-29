SELECT COUNT(*) FROM gqlite_{{ graph_name }}_edges AS e
  JOIN gqlite_{{ graph_name }}_nodes AS n ON n.id = e.left OR n.id = e.right
  WHERE n.node_key = ANY (ARRAY['{{ keys | join("'::uuid, '") }}'::uuid])
