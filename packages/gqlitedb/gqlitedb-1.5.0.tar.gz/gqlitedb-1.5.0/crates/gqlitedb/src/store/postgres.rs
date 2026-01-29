use std::cell::RefCell;

use ccutils::pool::{self, Pool};

use crate::{
  prelude::*,
  store::{
    sqlbase::{SqlBindingValue, SqlResultValue},
    TransactionBoxable,
  },
};

ccutils::assert_impl_all!(Store: Sync, Send);

use askama::Template;
use postgres::{types::ToSql, NoTls};

const SCHEMA: &str = "public";

//  _____     _____                    ____        _
// |_   _|__ |  ___| __ ___  _ __ ___ / ___|  __ _| |
//   | |/ _ \| |_ | '__/ _ \| '_ ` _ \\___ \ / _` | |
//   | | (_) |  _|| | | (_) | | | | | |___) | (_| | |
//   |_|\___/|_|  |_|  \___/|_| |_| |_|____/ \__, |_|
//                                              |_|

fn into_to_sql<'a>(value: SqlBindingValue<'a>) -> Result<Box<dyn ToSql + Sync + 'a>>
{
  Ok(match value
  {
    SqlBindingValue::String(s) => Box::new(s),
    SqlBindingValue::Key(k) => Box::new(uuid::Uuid::from_u128(k.uuid())),
    SqlBindingValue::Keys(keys) => Box::new(
      keys
        .iter()
        .map(|k| uuid::Uuid::from_u128(k.uuid()))
        .collect::<Vec<_>>(),
    ),
    SqlBindingValue::Labels(labels) => Box::new(labels.0),
    SqlBindingValue::Properties(properties) =>
    {
      let json = serde_json::to_value(properties.0)?;
      Box::new(json)
    }
  })
}

fn with_sql_params<'a, T, F, R>(bindings: T, f: F) -> Result<R>
where
  T: sqlbase::IntoBindings<'a>,
  F: FnOnce(&[&(dyn ToSql + Sync)]) -> R,
{
  let params: Vec<Box<dyn ToSql + Sync>> = bindings
    .into_bindings_iter()
    .map(|v| into_to_sql(v))
    .collect::<Result<_>>()?;

  let refs: Vec<&(dyn ToSql + Sync)> = params.iter().map(|b| b.as_ref()).collect();
  Ok(f(&refs))
}

fn bundle_query_in_error<T>(value: Result<T, postgres::Error>, query: &str) -> Result<T, Error>
{
  value.map_err(|error| {
    StoreError::PostgresErrorWithQuery {
      error,
      query: query.to_string(),
    }
    .into()
  })
}

impl sqlbase::Row for postgres::Row
{
  fn get_value(&self, index: usize) -> Result<SqlResultValue<'_>>
  {
    use postgres::types::Type;

    let ty = self.columns()[index].type_();
    match ty
    {
      &Type::TEXT => Ok(SqlResultValue::String(self.try_get::<_, String>(index)?)),
      &Type::BOOL => Ok(SqlResultValue::Integer(
        self.try_get::<_, bool>(index)? as i64
      )),
      &Type::TEXT_ARRAY => Ok(SqlResultValue::StringList(
        self.try_get::<_, Vec<String>>(index)?,
      )),
      &Type::BYTEA => Ok(SqlResultValue::Blob(self.try_get::<_, &[u8]>(index)?)),
      &Type::FLOAT8 => Ok(SqlResultValue::Float(self.try_get::<_, f64>(index)?)),
      &Type::INT4 => Ok(SqlResultValue::Integer(
        self.try_get::<_, i32>(index)? as i64
      )),
      &Type::INT8 => Ok(SqlResultValue::Integer(self.try_get::<_, i64>(index)?)),
      &Type::VARCHAR | &Type::CHAR => Ok(SqlResultValue::String(self.try_get::<_, String>(index)?)),
      &Type::UUID => Ok(SqlResultValue::Uuid(
        self.try_get::<_, uuid::Uuid>(index)?.as_u128(),
      )),
      &Type::UUID_ARRAY => Ok(SqlResultValue::Uuids(
        self
          .try_get::<_, Vec<uuid::Uuid>>(index)?
          .into_iter()
          .map(|k| k.as_u128())
          .collect(),
      )),
      &Type::JSONB => Ok(SqlResultValue::JsonValue(self.try_get(index)?)),
      _ => Err(StoreError::UnsupportedPostgresType(ty.name().to_string()).into()),
    }
  }
}

//  _____                               _   _
// |_   _| __ __ _ _ __  ___  __ _  ___| |_(_) ___  _ __
//   | || '__/ _` | '_ \/ __|/ _` |/ __| __| |/ _ \| '_ \
//   | || | | (_| | | | \__ \ (_| | (__| |_| | (_) | | | |
//   |_||_|  \__,_|_| |_|___/\__,_|\___|\__|_|\___/|_| |_|

struct TransactionBase
{
  client: pool::Handle<postgres::Client>,
  active: RefCell<bool>,
}

impl Drop for TransactionBase
{
  fn drop(&mut self)
  {
    if *self.active.borrow()
    {
      if let Err(e) = self.client.query("ROLLBACK", &[])
      {
        println!(
          "Rollback failed with error {:?}, future use of the connection are likely to fail.",
          e
        );
      }
    }
  }
}

pub(crate) struct ReadTransaction
{
  transaction_base: TransactionBase,
}

impl super::ReadTransaction for ReadTransaction
{
  fn discard(mut self) -> Result<()>
  {
    self.transaction_base.client.query("ROLLBACK", &[])?;
    *self.transaction_base.active.get_mut() = false;
    Ok(())
  }
}

pub(crate) struct WriteTransaction
{
  transaction_base: TransactionBase,
}

impl super::ReadTransaction for WriteTransaction
{
  fn discard(mut self) -> Result<()>
  {
    self.transaction_base.client.query("ROLLBACK", &[])?;
    *self.transaction_base.active.get_mut() = false;
    Ok(())
  }
}
impl super::WriteTransaction for WriteTransaction
{
  fn commit(mut self) -> Result<()>
  {
    self.transaction_base.client.query("COMMIT", &[])?;
    *self.transaction_base.active.get_mut() = false;
    Ok(())
  }
}

trait GetClient
{
  fn get_client(&mut self) -> &mut postgres::Client;
}

impl GetClient for super::TransactionBox<ReadTransaction, WriteTransaction>
{
  fn get_client(&mut self) -> &mut postgres::Client
  {
    use std::ops::DerefMut as _;
    match self
    {
      super::TransactionBox::Read(read) => read.transaction_base.client.deref_mut(),
      super::TransactionBox::Write(write) => write.transaction_base.client.deref_mut(),
    }
  }
}

//  _____                    _       _
// |_   _|__ _ __ ___  _ __ | | __ _| |_ ___  ___
//   | |/ _ \ '_ ` _ \| '_ \| |/ _` | __/ _ \/ __|
//   | |  __/ | | | | | |_) | | (_| | ||  __/\__ \
//   |_|\___|_| |_| |_| .__/|_|\__,_|\__\___||___/
//                    |_|

mod templates
{
  use askama::Template;

  // Graph related templates
  #[derive(Template)]
  #[template(path = "sql/postgres/graph_create.sql", escape = "none")]
  pub(super) struct GraphCreate<'a>
  {
    pub graph_name: &'a str,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/graph_delete.sql", escape = "none")]
  pub(super) struct GraphDelete<'a>
  {
    pub graph_name: &'a str,
  }
  // Node related templates
  #[derive(Template)]
  #[template(path = "sql/postgres/node_create.sql", escape = "none")]
  pub(super) struct NodeCreate<'a>
  {
    pub graph_name: &'a str,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/node_delete.sql", escape = "none")]
  pub(super) struct NodeDelete<'a>
  {
    pub graph_name: &'a str,
    pub keys: &'a Vec<String>,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/node_update.sql", escape = "none")]
  pub(super) struct NodeUpdate<'a>
  {
    pub graph_name: &'a str,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/node_select.sql", escape = "none")]
  pub(super) struct NodeSelect<'a>
  {
    pub graph_name: &'a str,
    pub keys_var: &'a Option<usize>,
    pub labels_var: &'a Option<usize>,
    pub properties_var: &'a Option<usize>,
  }
  // Edge queries
  #[derive(Template)]
  #[template(path = "sql/postgres/edge_count_for_node.sql", escape = "none")]
  pub(super) struct EdgeCountForNode<'a>
  {
    pub graph_name: &'a str,
    pub keys: &'a Vec<String>,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/edge_create.sql", escape = "none")]
  pub(super) struct EdgeCreate<'a>
  {
    pub graph_name: &'a str,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/edge_delete_by_nodes.sql", escape = "none")]
  pub(super) struct EdgeDeleteByNodes<'a>
  {
    pub graph_name: &'a str,
    pub keys: &'a Vec<String>,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/edge_delete.sql", escape = "none")]
  pub(super) struct EdgeDelete<'a>
  {
    pub graph_name: &'a str,
    pub keys: &'a Vec<String>,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/edge_update.sql", escape = "none")]
  pub(super) struct EdgeUpdate<'a>
  {
    pub graph_name: &'a str,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/edge_select.sql", escape = "none")]
  pub(super) struct EdgeSelect<'a>
  {
    pub graph_name: &'a str,
    pub is_undirected: bool,
    pub table_suffix: &'a str,
    pub edge_keys_var: Option<usize>,
    pub edge_labels_var: Option<usize>,
    pub edge_properties_var: Option<usize>,
    pub left_keys_var: Option<usize>,
    pub left_labels_var: Option<usize>,
    pub left_properties_var: Option<usize>,
    pub right_keys_var: Option<usize>,
    pub right_labels_var: Option<usize>,
    pub right_properties_var: Option<usize>,
  }
  #[derive(Template)]
  #[template(path = "sql/postgres/call_stats.sql", escape = "none")]
  pub(super) struct CallStats<'a>
  {
    pub graph_name: &'a str,
  }
}

//  ____  _
// / ___|| |_ ___  _ __ ___
// \___ \| __/ _ \| '__/ _ \
//  ___) | || (_) | | |  __/
// |____/ \__\___/|_|  \___|

type TransactionBox = store::TransactionBox<ReadTransaction, WriteTransaction>;

pub(crate) struct Store
{
  client: Pool<postgres::Client, ErrorType>,
}
ccutils::assert_impl_all!(Store: Sync, Send);

impl Store
{
  /// Crate a new store, with a default graph
  pub(crate) fn connect(config: postgres::Config) -> Result<Store>
  {
    let client = Pool::new(
      move || Ok(config.connect(NoTls)?),
      pool::Options::default().minimum_pool_size(1).pool_size(3),
    )?;

    let s = Self { client };
    s.initialise()?;
    Ok(s)
  }
  fn upgrade_database(&self, _transaction: &mut TransactionBox, _from: utils::Version)
    -> Result<()>
  {
    // No release with postgres, so nothing to upgrade
    Ok(())
  }
  /// Check if table exists
  pub(crate) fn check_if_table_exists(
    &self,
    transaction: &mut TransactionBox,
    table_name: &str,
  ) -> Result<bool>
  {
    let client = transaction.get_client();
    let stmt = client.prepare(include_str!(
      "../../templates/sql/postgres/table_exists.sql"
    ))?;

    let row = client.query_one(&stmt, &[&SCHEMA, &table_name])?;
    Ok(row.get(0))
  }
}

impl super::sqlbase::SqlMetaDataQueries for Store
{
  fn metadata_get_query() -> Result<String>
  {
    Ok(include_str!("../../templates/sql/postgres/metadata_get.sql").to_string())
  }
  fn metadata_set_query() -> Result<String>
  {
    Ok(include_str!("../../templates/sql/postgres/metadata_set.sql").to_string())
  }
}

impl super::sqlbase::SqlStore for Store
{
  type TransactionBox = TransactionBox;
  type Row<'a> = postgres::Row;

  fn initialise(&self) -> Result<()>
  {
    use crate::store::Store;
    let mut tx = self.begin_sql_write()?;
    if self.check_if_table_exists(&mut tx, "gqlite_metadata")?
    {
      let version_raw = self
        .get_metadata_value::<String>(&mut tx, "version")?
        .replace("'", "\"");
      let version: utils::Version = serde_json::from_str(&version_raw)?;
      if version.major != consts::GQLITE_VERSION.major
        || version.minor != consts::GQLITE_VERSION.minor
      {
        self.upgrade_database(&mut tx, version)?;
      }
    }
    else
    {
      tx.get_client().execute(
        include_str!("../../templates/sql/postgres/metadata_create_table.sql"),
        &[],
      )?;
      self.set_metadata_value_json(&mut tx, "graphs", &Vec::<String>::new())?;
      self.create_graph(&mut tx, "default", true)?;
    }
    self.set_metadata_value_json(&mut tx, "version", &consts::GQLITE_VERSION)?;
    tx.close()?;
    Ok(())
  }

  fn begin_sql_read(&self) -> Result<Self::TransactionBox>
  {
    let mut client = self.client.get()?;
    client.query("BEGIN", &[])?;
    Ok(super::TransactionBox::from_read(ReadTransaction {
      transaction_base: TransactionBase {
        client,
        active: RefCell::new(true),
      },
    }))
  }

  fn begin_sql_write(&self) -> Result<Self::TransactionBox>
  {
    let mut client = self.client.get()?;
    client.query("BEGIN", &[])?;
    Ok(super::TransactionBox::from_write(WriteTransaction {
      transaction_base: TransactionBase {
        client,
        active: RefCell::new(true),
      },
    }))
  }

  fn execute_batch(
    &self,
    transaction: &mut Self::TransactionBox,
    sql: impl AsRef<str>,
  ) -> Result<()>
  {
    let sql = sql.as_ref();
    bundle_query_in_error(transaction.get_client().batch_execute(sql), sql)?;
    Ok(())
  }

  fn execute<'a>(
    &self,
    transaction: &mut Self::TransactionBox,
    sql: impl AsRef<str>,
    bindings: impl sqlbase::IntoBindings<'a>,
  ) -> Result<()>
  {
    let sql = sql.as_ref();
    bundle_query_in_error(
      with_sql_params(bindings, |bindings| {
        transaction.get_client().execute(sql, bindings)
      })?,
      sql,
    )?;
    Ok(())
  }

  fn query_row<'a, 'tx, T>(
    &self,
    transaction: &'tx mut Self::TransactionBox,
    sql: impl AsRef<str>,
    bindings: impl sqlbase::IntoBindings<'a>,
    f: impl for<'b> FnOnce(&Self::Row<'b>) -> Result<T>,
  ) -> Result<T>
  {
    let sql = sql.as_ref();

    let row = bundle_query_in_error(
      with_sql_params(bindings, |bindings| {
        transaction.get_client().query_one(sql, bindings)
      })?,
      sql,
    )?;
    f(&row)
  }

  fn query_rows<'a, 'tx>(
    &self,
    transaction: &'tx mut Self::TransactionBox,
    sql: impl AsRef<str>,
    bindings: impl sqlbase::IntoBindings<'a>,
    mut f: impl for<'b> FnMut(&Self::Row<'b>) -> Result<()>,
  ) -> Result<()>
  {
    let sql = sql.as_ref();

    let rows = bundle_query_in_error(
      with_sql_params(bindings, |bindings| {
        transaction.get_client().query(sql, bindings)
      })?,
      sql,
    )?;

    for row in rows
    {
      f(&row)?;
    }
    Ok(())
  }
}

impl super::sqlbase::SqlQueries for Store
{
  fn graph_create_query(graph_name: impl AsRef<str>) -> Result<String>
  {
    Ok(
      templates::GraphCreate {
        graph_name: graph_name.as_ref(),
      }
      .render()?,
    )
  }
  fn graph_delete(graph_name: impl AsRef<str>) -> Result<String>
  {
    Ok(
      templates::GraphDelete {
        graph_name: graph_name.as_ref(),
      }
      .render()?,
    )
  }
  fn node_create_query(graph_name: impl AsRef<str>) -> Result<String>
  {
    Ok(
      templates::NodeCreate {
        graph_name: graph_name.as_ref(),
      }
      .render()?,
    )
  }
  fn edge_delete_by_nodes_query(
    graph_name: impl AsRef<str>,
    keys: impl AsRef<Vec<String>>,
  ) -> Result<String>
  {
    Ok(
      templates::EdgeDeleteByNodes {
        graph_name: graph_name.as_ref(),
        keys: keys.as_ref(),
      }
      .render()?,
    )
  }

  fn edge_count_for_nodes_query(
    graph_name: impl AsRef<str>,
    keys: impl AsRef<Vec<String>>,
  ) -> Result<String>
  {
    Ok(
      templates::EdgeCountForNode {
        graph_name: graph_name.as_ref(),
        keys: keys.as_ref(),
      }
      .render()?,
    )
  }

  fn node_delete_query(graph_name: impl AsRef<str>, keys: impl AsRef<Vec<String>>)
    -> Result<String>
  {
    Ok(
      templates::NodeDelete {
        graph_name: graph_name.as_ref(),
        keys: keys.as_ref(),
      }
      .render()?,
    )
  }

  fn node_update_query(graph_name: impl AsRef<str>) -> Result<String>
  {
    Ok(
      templates::NodeUpdate {
        graph_name: graph_name.as_ref(),
      }
      .render()?,
    )
  }

  fn node_select_query(
    graph_name: impl AsRef<str>,
    keys_var: Option<usize>,
    labels_var: Option<usize>,
    properties_var: Option<usize>,
  ) -> Result<String>
  {
    Ok(
      templates::NodeSelect {
        graph_name: graph_name.as_ref(),
        keys_var: &keys_var,
        labels_var: &labels_var,
        properties_var: &properties_var,
      }
      .render()?,
    )
  }

  fn edge_create_query(graph_name: impl AsRef<str>) -> Result<String>
  {
    Ok(
      templates::EdgeCreate {
        graph_name: graph_name.as_ref(),
      }
      .render()?,
    )
  }
  fn edge_delete_query(graph_name: impl AsRef<str>, keys: impl AsRef<Vec<String>>)
    -> Result<String>
  {
    Ok(
      templates::EdgeDelete {
        graph_name: graph_name.as_ref(),
        keys: keys.as_ref(),
      }
      .render()?,
    )
  }
  fn edge_update_query(graph_name: impl AsRef<str>) -> Result<String>
  {
    Ok(
      templates::EdgeUpdate {
        graph_name: graph_name.as_ref(),
      }
      .render()?,
    )
  }
  fn edge_select_query(
    graph_name: impl AsRef<str>,
    is_undirected: bool,
    table_suffix: impl AsRef<str>,
    edge_keys_var: Option<usize>,
    edge_labels_var: Option<usize>,
    edge_properties_var: Option<usize>,
    left_keys_var: Option<usize>,
    left_labels_var: Option<usize>,
    left_properties_var: Option<usize>,
    right_keys_var: Option<usize>,
    right_labels_var: Option<usize>,
    right_properties_var: Option<usize>,
  ) -> Result<String>
  {
    Ok(
      templates::EdgeSelect {
        graph_name: graph_name.as_ref(),
        is_undirected,
        table_suffix: table_suffix.as_ref(),
        edge_keys_var,
        edge_labels_var,
        edge_properties_var,
        left_keys_var,
        left_labels_var,
        left_properties_var,
        right_keys_var,
        right_labels_var,
        right_properties_var,
      }
      .render()?,
    )
  }
  fn compute_statistics_query(graph_name: impl AsRef<str>) -> Result<String>
  {
    Ok(
      templates::CallStats {
        graph_name: graph_name.as_ref(),
      }
      .render()?,
    )
  }
}

#[cfg(all(test, not(windows)))]
mod tests
{
  use crate::{prelude::*, store::TransactionBoxable};
  #[test]
  fn test_postgres_metadata()
  {
    let db = crate::tests::postgres::create_tmp_db(0);
    let config: postgres::Config = db.connection_uri().parse().unwrap();
    let store = super::Store::connect(config.clone()).unwrap();
    let mut tx = store.begin_sql_read().unwrap();
    let version: utils::Version = store.get_metadata_value_json(&mut tx, "version").unwrap();
    assert_eq!(version.major, consts::GQLITE_VERSION.major);
    assert_eq!(version.minor, consts::GQLITE_VERSION.minor);
    assert_eq!(version.patch, consts::GQLITE_VERSION.patch);
    tx.close().unwrap();
    drop(store);

    // Try to reopen
    let store = super::Store::connect(config).unwrap();
    let mut tx = store.begin_sql_read().unwrap();
    let version: utils::Version = store.get_metadata_value_json(&mut tx, "version").unwrap();
    assert_eq!(version.major, consts::GQLITE_VERSION.major);
    assert_eq!(version.minor, consts::GQLITE_VERSION.minor);
    assert_eq!(version.patch, consts::GQLITE_VERSION.patch);
    tx.close().unwrap();
    drop(store);
  }
}
