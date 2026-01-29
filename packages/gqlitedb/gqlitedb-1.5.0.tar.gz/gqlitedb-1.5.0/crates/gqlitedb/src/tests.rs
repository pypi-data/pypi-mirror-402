mod compiler;
mod connection;
mod evaluators;
mod parser;
mod store;
mod templates;

#[cfg(all(feature = "postgres", not(windows)))]
pub(crate) mod postgres
{
  use std::{
    net::TcpStream,
    process::Command,
    thread::sleep,
    time::{Duration, Instant},
  };

  pub(crate) fn create_tmp_db(port_inc: u16) -> pgtemp::PgTempDB
  {
    let output = Command::new("pg_config")
      .arg("--bindir")
      .output()
      .expect("failed to execute pg_config");

    let bin_path = String::from_utf8_lossy(&output.stdout).trim().to_string();

    let db = pgtemp::PgTempDB::builder()
      .with_port(5000 + port_inc)
      .with_bin_path(bin_path)
      .start();

    const MAX_WAIT: Duration = Duration::from_secs(30);
    const INTERVAL: Duration = Duration::from_secs(1);
    const CONNECT_TIMEOUT: Duration = Duration::from_secs(1);

    let deadline = Instant::now() + MAX_WAIT;

    while Instant::now() < deadline
    {
      if TcpStream::connect_timeout(
        &format!("127.0.0.1:{}", db.db_port()).parse().unwrap(),
        CONNECT_TIMEOUT,
      )
      .is_ok()
      {
        println!("Port {} is open!", db.db_port());
        break;
      }
      sleep(INTERVAL);
    }

    db
  }
}

pub(crate) fn create_tmp_file() -> ccutils::temporary::TemporaryFile
{
  ccutils::temporary::TemporaryFile::builder()
    .should_create_file(false)
    .label("gqlite")
    .create()
}

fn check_stats<TStore: crate::store::Store>(
  store: &TStore,
  transaction: Option<&mut TStore::TransactionBox>,
  nodes_count: usize,
  edges_count: usize,
  labels_node_count: usize,
  properties_count: usize,
)
{
  let stats = match transaction
  {
    Some(tx) => store.compute_statistics(tx).unwrap(),
    None =>
    {
      // use crate::store::TransactionBoxable;
      let mut tx = store.begin_read().unwrap();
      store.compute_statistics(&mut tx).unwrap()
    }
  };

  assert_eq!(stats.nodes_count, nodes_count);
  assert_eq!(stats.edges_count, edges_count);
  assert_eq!(stats.labels_nodes_count, labels_node_count);
  assert_eq!(stats.properties_count, properties_count);
}
