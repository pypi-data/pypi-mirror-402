#[cfg(all(feature = "postgres", not(windows)))]
pub(crate) mod postgres;

fn test_connection(connection: crate::Connection)
{
  connection
    .execute_oc_query("CREATE (n:a)", Default::default())
    .unwrap();
  let r = connection
    .execute_oc_query("MATCH (n) RETURN n", Default::default())
    .unwrap();
  let table = r.try_into_table().unwrap();
  assert_eq!(table.columns(), 1);
  assert_eq!(table.rows(), 1);
  assert_eq!(*table.headers(), vec!["n".to_string()]);
  let node: graphcore::Node = table.value(0, 0).unwrap().try_into().unwrap();
  assert_eq!(*node.labels(), vec!["a".to_string()]);
  assert_eq!(node.properties().len(), 0);
}
