use graphcore::ValueMap;

use crate::prelude::*;

#[derive(Debug)]
pub(crate) struct Labels(pub Vec<String>);
#[derive(Debug)]
pub(crate) struct Properties(pub ValueMap);

#[derive(Debug)]
pub(crate) enum SqlResultValue<'a>
{
  String(String),
  Uuid(u128),
  Uuids(Vec<u128>),
  Blob(&'a [u8]),
  Text(&'a [u8]),
  #[allow(dead_code)]
  Float(f64),
  Integer(i64),
  StringList(Vec<String>),
  JsonValue(serde_json::Value),
  Null,
}

pub(crate) trait FromSqlResultValue: Sized
{
  fn from_sql_value<'a>(value: SqlResultValue<'a>) -> Result<Self>;
}

impl FromSqlResultValue for String
{
  fn from_sql_value<'a>(value: SqlResultValue<'a>) -> Result<Self>
  {
    match value
    {
      SqlResultValue::Text(text) => Ok(std::str::from_utf8(text)?.to_string()),
      SqlResultValue::String(string) => Ok(string),
      _ => Err(InternalError::InvalidQueryResultCast.into()),
    }
  }
}

impl FromSqlResultValue for usize
{
  fn from_sql_value<'a>(value: SqlResultValue<'a>) -> Result<Self>
  {
    match value
    {
      SqlResultValue::Integer(i) => Ok(i as usize),
      _ => Err(InternalError::InvalidQueryResultCast.into()),
    }
  }
}

impl FromSqlResultValue for u32
{
  fn from_sql_value<'a>(value: SqlResultValue<'a>) -> Result<Self>
  {
    match value
    {
      SqlResultValue::Integer(i) => Ok(i as u32),
      _ => Err(InternalError::InvalidQueryResultCast.into()),
    }
  }
}

impl FromSqlResultValue for graph::Key
{
  fn from_sql_value<'a>(value: SqlResultValue<'a>) -> Result<Self>
  {
    match value
    {
      SqlResultValue::Integer(i) => Ok(graphcore::Key::new(i as u128)),
      SqlResultValue::Uuid(k) => Ok(graphcore::Key::new(k)),
      SqlResultValue::Blob(b) => <[u8; 16]>::try_from(b)
        .map(u128::from_be_bytes)
        .map(graphcore::Key::new)
        .map_err(|_| InternalError::InvalidQueryResultCast.into()),
      _ => Err(InternalError::InvalidQueryResultCast.into()),
    }
  }
}

impl FromSqlResultValue for Vec<graph::Key>
{
  fn from_sql_value<'a>(value: SqlResultValue<'a>) -> Result<Self>
  {
    match value
    {
      SqlResultValue::Uuids(uuids) => Ok(uuids.into_iter().map(graphcore::Key::new).collect()),
      SqlResultValue::Text(text) => Ok(serde_json::from_slice(text)?),
      SqlResultValue::String(string) => Ok(serde_json::from_str(&string)?),
      _ => Err(InternalError::InvalidQueryResultCast.into()),
    }
  }
}
impl FromSqlResultValue for Labels
{
  fn from_sql_value<'a>(value: SqlResultValue<'a>) -> Result<Self>
  {
    match value
    {
      SqlResultValue::Text(text) => Ok(Labels(serde_json::from_slice(text)?)),
      SqlResultValue::String(string) => Ok(Labels(serde_json::from_str(&string)?)),
      SqlResultValue::StringList(string_list) => Ok(Labels(string_list)),
      _ => Err(InternalError::InvalidQueryResultCast.into()),
    }
  }
}

impl FromSqlResultValue for Properties
{
  fn from_sql_value<'a>(value: SqlResultValue<'a>) -> Result<Self>
  {
    match value
    {
      SqlResultValue::Text(text) => Ok(Properties(serde_json::from_slice(text)?)),
      SqlResultValue::String(string) => Ok(Properties(serde_json::from_str(&string)?)),
      SqlResultValue::JsonValue(value) => Ok(Properties(serde_json::from_value(value)?)),
      _ => Err(InternalError::InvalidQueryResultCast.into()),
    }
  }
}
