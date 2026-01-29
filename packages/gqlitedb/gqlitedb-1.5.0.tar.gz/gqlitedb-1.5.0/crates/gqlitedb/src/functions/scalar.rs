use crate::prelude::*;

use super::{ExpressionType, FResult, FunctionTypeTrait};

#[derive(Debug, Default)]
pub(super) struct Coalesce {}

impl super::FunctionTrait for Coalesce
{
  fn call(&self, arguments: Vec<value::Value>) -> crate::Result<value::Value>
  {
    for arg in arguments
    {
      match arg
      {
        value::Value::Null =>
        {}
        other => return Ok(other),
      }
    }
    Ok(value::Value::Null)
  }
  fn validate_arguments(&self, _: Vec<ExpressionType>) -> crate::Result<ExpressionType>
  {
    Ok(ExpressionType::Variant)
  }
  fn is_deterministic(&self) -> bool
  {
    true
  }
}

super::declare_function!(coalesce, Coalesce, custom_trait);

#[derive(Debug, Default)]
pub(super) struct Id {}

impl Id
{
  fn call_impl(value: value::Value) -> FResult<graph::Key>
  {
    match value
    {
      value::Value::Node(n) => Ok(n.key()),
      value::Value::Edge(e) => Ok(e.key()),
      _ => Err(RunTimeError::InvalidArgument {
        function_name: "id",
        index: 0,
        expected_type: "node or edge",
        value: format!("{:?}", value),
      }),
    }
  }
}

super::declare_function!(id, Id, call_impl(crate::value::Value) -> graph::Key);

#[derive(Debug, Default)]
pub(super) struct ToBoolean {}

impl ToBoolean
{
  fn call_impl(value: value::Value) -> FResult<value::Value>
  {
    match value
    {
      value::Value::Boolean(b) => Ok(b.into()),
      value::Value::Integer(i) => Ok((i != 0).into()),
      value::Value::Float(f) => Ok((f != 0.0).into()),
      value::Value::String(s) =>
      {
        let i: Result<bool, _> = s.parse();
        Ok(i.map_or(value::Value::Null, |x| x.into()))
      }
      o => Err(RunTimeError::InvalidArgument {
        function_name: "toBoolean",
        index: 0,
        expected_type: "integer, float, or string",
        value: format!("{:?}", o),
      }),
    }
  }
}

super::declare_function!(toboolean, ToBoolean, call_impl(crate::value::Value) -> value::Value);

#[derive(Debug, Default)]
pub(super) struct ToFloat {}

impl ToFloat
{
  fn call_impl(value: value::Value) -> FResult<value::Value>
  {
    match value
    {
      value::Value::Integer(i) => Ok((i as f64).into()),
      value::Value::Float(f) => Ok(f.into()),
      value::Value::String(s) =>
      {
        let i: Result<f64, _> = s.parse();
        Ok(i.map_or(value::Value::Null, |x| x.into()))
      }
      o => Err(RunTimeError::InvalidArgument {
        function_name: "toFloat",
        index: 0,
        expected_type: "integer, float, or string",
        value: format!("{:?}", o),
      }),
    }
  }
}

super::declare_function!(tofloat, ToFloat, call_impl(crate::value::Value) -> value::Value);

#[derive(Debug, Default)]
pub(super) struct ToInteger {}

impl ToInteger
{
  fn call_impl(value: value::Value) -> FResult<value::Value>
  {
    match value
    {
      value::Value::Integer(i) => Ok(i.into()),
      value::Value::Float(f) => Ok((f as i64).into()),
      value::Value::String(s) =>
      {
        let i: Result<i64, _> = s.parse();
        Ok(i.map_or(value::Value::Null, |x| x.into()))
      }
      o => Err(RunTimeError::InvalidArgument {
        function_name: "toInteger",
        index: 0,
        expected_type: "integer, float, or string",
        value: format!("{:?}", o),
      }),
    }
  }
}

super::declare_function!(tointeger, ToInteger, call_impl(crate::value::Value) -> value::Value);

#[derive(Debug, Default)]
pub(super) struct Properties {}

impl Properties
{
  fn call_impl(value: value::Value) -> FResult<value::ValueMap>
  {
    match value
    {
      value::Value::Node(n) => Ok(n.properties().to_owned()),
      value::Value::Edge(e) => Ok(e.properties().to_owned()),
      value::Value::Map(m) => Ok(m.to_owned()),
      _ => Err(RunTimeError::InvalidArgument {
        function_name: "properties",
        index: 0,
        expected_type: "node or relationship",
        value: format!("{:?}", value),
      }),
    }
  }
}

super::declare_function!(properties, Properties, call_impl(crate::value::Value) -> value::ValueMap, validate_args(ExpressionType::Map | ExpressionType::Node | ExpressionType::Edge | ExpressionType::Null));
