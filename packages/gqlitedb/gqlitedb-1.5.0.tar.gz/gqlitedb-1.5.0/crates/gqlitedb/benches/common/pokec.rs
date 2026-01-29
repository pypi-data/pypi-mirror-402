use std::{collections::HashSet, fs};

use ccutils::temporary::TemporaryFile;
use gqlitedb::{value_map, Connection};
use rand::{seq::IndexedRandom, Rng};
use regex::Regex;

/// Marker trait to keep backend-specific resources alive for the benchmark lifetime.
trait BackendResource {}
impl BackendResource for TemporaryFile {}
impl BackendResource for pgtemp::PgTempDB {}

pub(crate) struct Pokec
{
  #[allow(dead_code)]
  file_handle: Box<dyn BackendResource>,
  connection: Connection,
  ids: Vec<i64>,
}

#[allow(dead_code)]
pub(crate) enum PokecSize
{
  Micro,
  Tiny,
}

impl Pokec
{
  pub(crate) fn load(backend: &str, size: PokecSize) -> Pokec
  {
    let backend = match backend
    {
      "sqlite" => gqlitedb::Backend::SQLite,
      "redb" => gqlitedb::Backend::Redb,
      "postgres" => gqlitedb::Backend::Postgres,
      o => panic!("Unknown backend '{}'", o),
    };
    let (file_handle, connection): (Box<dyn BackendResource>, _) = match backend
    {
      gqlitedb::Backend::Redb | gqlitedb::Backend::SQLite =>
      {
        let temporary_file = TemporaryFile::builder()
          .should_create_file(false)
          .label("gqlite_bench")
          .create();
        let connection = Connection::builder()
          .path(temporary_file.path())
          .backend(backend)
          .create()
          .unwrap();
        (Box::new(temporary_file), connection)
      }
      gqlitedb::Backend::Postgres =>
      {
        use std::{
          thread::sleep,
          time::{Duration, Instant},
        };
        let output = std::process::Command::new("pg_config")
          .arg("--bindir")
          .output()
          .expect("failed to execute pg_config");

        let bin_path = String::from_utf8_lossy(&output.stdout).trim().to_string();

        let db = pgtemp::PgTempDB::builder().with_bin_path(bin_path).start();

        const MAX_WAIT: Duration = Duration::from_secs(30);
        const INTERVAL: Duration = Duration::from_secs(1);

        let deadline = Instant::now() + MAX_WAIT;

        let mut connection = Connection::builder()
          .set_option("url", db.connection_uri())
          .backend(backend)
          .create();
        while connection.is_err() && Instant::now() < deadline
        {
          sleep(INTERVAL);
          connection = Connection::builder()
            .set_option("url", db.connection_uri())
            .backend(backend)
            .create()
        }
        let connection = connection.expect("Failed to connect to temporary Postgres DB within 30s");
        (Box::new(db), connection)
      }
      gqlitedb::Backend::Automatic =>
      {
        panic!("Should not be selected.")
      }
    };

    let filename = match size
    {
      PokecSize::Micro => "gqlite_bench_data/pokec_micro_import.cypher",
      PokecSize::Tiny => "gqlite_bench_data/pokec_tiny_import.cypher",
    };

    let import_query = fs::read_to_string(filename).unwrap();

    connection
      .execute_oc_query(import_query, Default::default())
      .unwrap();
    Self {
      file_handle,
      connection,
      ids: Default::default(),
    }
  }
  pub(crate) fn read_ids(mut self) -> Self
  {
    let re = Regex::new(r"id:\s*(\d+)").unwrap();
    let mut ids = HashSet::new();
    let content = fs::read_to_string("gqlite_bench_data/pokec_tiny_import.cypher")
      .expect("Failed to read the file");
    for cap in re.captures_iter(&content)
    {
      if let Some(id_match) = cap.get(1)
      {
        let id = id_match.as_str().parse::<i64>().unwrap();
        ids.insert(id);
      }
    }
    self.ids = ids.into_iter().collect();
    self
  }
  pub(crate) fn single_vertex<R>(&self, rng: &mut R)
  where
    R: Rng + ?Sized,
  {
    let random_id = self.ids.choose(rng).unwrap();
    self
      .connection
      .execute_oc_query(
        "MATCH (n:User {id: $id}) RETURN n",
        value_map!("$id" => *random_id),
      )
      .unwrap();
  }
  pub(crate) fn single_vertex_where<R>(&self, rng: &mut R)
  where
    R: Rng + ?Sized,
  {
    let random_id = self.ids.choose(rng).unwrap();
    self
      .connection
      .execute_oc_query(
        "MATCH (n:User) WHERE n.id = $id RETURN n",
        value_map!("$id" => *random_id),
      )
      .unwrap();
  }
  pub(crate) fn friend_of<R>(&self, rng: &mut R)
  where
    R: Rng + ?Sized,
  {
    let random_id = self.ids.choose(rng).unwrap();
    self
      .connection
      .execute_oc_query(
        "MATCH (s:User {id: $id})-->(n:User) RETURN n.id",
        value_map!("$id" => *random_id),
      )
      .unwrap();
  }
  pub(crate) fn friend_of_filter<R>(&self, rng: &mut R)
  where
    R: Rng + ?Sized,
  {
    let random_id = self.ids.choose(rng).unwrap();
    self
      .connection
      .execute_oc_query(
        "MATCH (s:User {id: $id})-->(n:User) WHERE n.age >= 18 RETURN n.id",
        value_map!("$id" => *random_id),
      )
      .unwrap();
  }
  pub(crate) fn friend_of_friend_of<R>(&self, rng: &mut R)
  where
    R: Rng + ?Sized,
  {
    let random_id = self.ids.choose(rng).unwrap();
    self
      .connection
      .execute_oc_query(
        "MATCH (s:User {id: $id})-->()-->(n:User) RETURN n.id",
        value_map!("$id" => *random_id),
      )
      .unwrap();
  }
  pub(crate) fn friend_of_friend_of_filter<R>(&self, rng: &mut R)
  where
    R: Rng + ?Sized,
  {
    let random_id = self.ids.choose(rng).unwrap();
    self
      .connection
      .execute_oc_query(
        "MATCH (s:User {id: $id})-->()-->(n:User) WHERE n.age >= 18 RETURN n.id",
        value_map!("$id" => *random_id),
      )
      .unwrap();
  }
  pub(crate) fn reciprocal_friends<R>(&self, rng: &mut R)
  where
    R: Rng + ?Sized,
  {
    let random_id = self.ids.choose(rng).unwrap();
    self
      .connection
      .execute_oc_query(
        "MATCH (n:User {id: $id})-[e1]->(m)-[e2]->(n) RETURN e1, m, e2",
        value_map!("$id" => *random_id),
      )
      .unwrap();
  }
  pub(crate) fn aggregate_count(&self)
  {
    self
      .connection
      .execute_oc_query("MATCH (n:User) RETURN n.age, count(*)", Default::default())
      .unwrap();
  }
  pub(crate) fn aggregate_count_filter(&self)
  {
    self
      .connection
      .execute_oc_query(
        "MATCH (n:User) WHERE n.age >= 18 RETURN n.age, count(*)",
        Default::default(),
      )
      .unwrap();
  }
  pub(crate) fn aggregate_min_max_avg(&self)
  {
    self
      .connection
      .execute_oc_query(
        "MATCH (n) RETURN min(n.age), max(n.age), avg(n.age)",
        Default::default(),
      )
      .unwrap();
  }
}
