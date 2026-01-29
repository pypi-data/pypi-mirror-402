WITH source_delete AS NOT MATERIALIZED (SELECT id FROM gqlite_{{ graph_name }}_nodes WHERE node_key in ('{{ keys | join("', '") }}'))
DELETE FROM gqlite_{{ graph_name }}_edges edge
USING source_delete sd
WHERE edge.left = sd.id OR edge.right = sd.id