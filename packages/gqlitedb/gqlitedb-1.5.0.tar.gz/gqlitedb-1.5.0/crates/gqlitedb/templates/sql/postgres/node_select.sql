SELECT node_key, labels, properties
FROM gqlite_{{ graph_name }}_nodes AS nodes
WHERE
    -- Filter by key list (if not empty)
    {% if let Some(keys_var) = keys_var %}
    (
        nodes.node_key = ANY( ${{ keys_var }}::uuid[] )
    )
    {% else %}
    TRUE
    {% endif %}
    AND
    {% if let Some(labels_var) = labels_var %}
    -- Filter by required labels (must all be in nodes.labels)
    (
        nodes.labels @> ${{ labels_var }}::text[]
    )
    {% else %}
    TRUE
    {% endif %}

    {% if let Some(properties_var) = properties_var %}
    -- Filter by required properties (must all exist and match)
    AND (
        NOT EXISTS (
            SELECT 1
            FROM jsonb_each(${{ properties_var }}) AS required_prop
            WHERE (nodes.properties -> required_prop.key) IS NULL
               OR (nodes.properties -> required_prop.key) != required_prop.value
        )
    );
    {% endif %}
