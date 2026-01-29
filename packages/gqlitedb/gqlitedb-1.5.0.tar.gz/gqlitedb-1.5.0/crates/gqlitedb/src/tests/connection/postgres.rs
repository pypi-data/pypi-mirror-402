#[test]
fn testconnection()
{
  let db = crate::tests::postgres::create_tmp_db(10);
  let builder = crate::Connection::builder().set_option("uri", db.connection_uri());
  let connection = builder.create().unwrap();
  super::test_connection(connection);
}
