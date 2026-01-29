WITH
  node_labels AS (
    SELECT DISTINCT label
    FROM gqlite_{{ graph_name }}_nodes, UNNEST(labels) AS label
  ),
  node_properties AS (
    SELECT 1
    FROM gqlite_{{ graph_name }}_nodes, jsonb_each(gqlite_{{ graph_name }}_nodes.properties)
    WHERE jsonb_each.value IS DISTINCT FROM 'null'::jsonb
  ),
  edge_properties AS (
    SELECT 1
    FROM gqlite_{{ graph_name }}_edges, jsonb_each(gqlite_{{ graph_name }}_edges.properties)
    WHERE jsonb_each.value IS DISTINCT FROM 'null'::jsonb
  )

SELECT
  (SELECT COUNT(*) FROM gqlite_{{ graph_name }}_nodes)     AS node_count,
  (SELECT COUNT(*) FROM gqlite_{{ graph_name }}_edges)     AS edge_count,
  (SELECT COUNT(*) FROM node_labels)                       AS unique_node_label_count,
  (SELECT COUNT(*) FROM node_properties)
  + (SELECT COUNT(*) FROM edge_properties)                 AS total_property_count;
