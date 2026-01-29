fn create_test_store(port_inc: u16) -> (crate::store::postgres::Store, pgtemp::PgTempDB)
{
  let db = crate::tests::postgres::create_tmp_db(port_inc);
  let config = db.connection_uri().parse().unwrap();
  (crate::store::postgres::Store::connect(config).unwrap(), db)
}

#[test]
fn test_graphs()
{
  let (store, _db) = create_test_store(100);
  super::test_graphs(store);
}

#[test]
fn test_select_nodes()
{
  let (store, _db) = create_test_store(101);
  super::test_select_nodes(store);
}

#[test]
fn test_update_nodes()
{
  let (store, _db) = create_test_store(102);
  super::test_update_nodes(store);
}

#[test]
fn test_select_edges()
{
  let (store, _db) = create_test_store(103);
  super::test_select_edges(store);
}

#[test]
fn test_update_edges()
{
  let (store, _db) = create_test_store(104);
  super::test_update_edges(store);
}
