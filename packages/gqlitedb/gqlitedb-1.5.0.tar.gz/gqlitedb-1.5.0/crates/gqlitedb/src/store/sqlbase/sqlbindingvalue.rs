use graphcore::ValueMap;

use crate::prelude::*;

#[derive(Debug)]
pub(crate) struct LabelsRef<'a>(pub &'a Vec<String>);
#[derive(Debug)]
pub(crate) struct PropertiesRef<'a>(pub &'a ValueMap);

#[derive(Debug)]
pub(crate) enum SqlBindingValue<'a>
{
  String(&'a String),
  Key(&'a graph::Key),
  Keys(&'a Vec<graph::Key>),
  Labels(LabelsRef<'a>),
  Properties(PropertiesRef<'a>),
}

impl<'a> From<&'a Vec<graph::Key>> for SqlBindingValue<'a>
{
  fn from(val: &'a Vec<graph::Key>) -> Self
  {
    SqlBindingValue::Keys(val)
  }
}

impl<'a> From<LabelsRef<'a>> for SqlBindingValue<'a>
{
  fn from(val: LabelsRef<'a>) -> Self
  {
    SqlBindingValue::Labels(val)
  }
}

impl<'a> From<PropertiesRef<'a>> for SqlBindingValue<'a>
{
  fn from(val: PropertiesRef<'a>) -> Self
  {
    SqlBindingValue::Properties(val)
  }
}

// impl<'a> From<String> for SqlBindingValue<'a>
// {
//   fn from(val: String) -> Self
//   {
//     SqlBindingValue::String(val)
//   }
// }

impl<'a> From<&'a graph::Key> for SqlBindingValue<'a>
{
  fn from(val: &'a graph::Key) -> Self
  {
    SqlBindingValue::Key(val)
  }
}

impl<'a> From<&'a String> for SqlBindingValue<'a>
{
  fn from(val: &'a String) -> Self
  {
    SqlBindingValue::String(val)
  }
}
pub(crate) trait IntoBindings<'a>
{
  fn into_bindings_iter(self) -> impl Iterator<Item = SqlBindingValue<'a>>;
}

impl<'a> IntoBindings<'a> for ()
{
  fn into_bindings_iter(self) -> impl Iterator<Item = SqlBindingValue<'a>>
  {
    vec![].into_iter()
  }
}

impl<'a, T0> IntoBindings<'a> for (T0,)
where
  T0: Into<SqlBindingValue<'a>>,
{
  fn into_bindings_iter(self) -> impl Iterator<Item = SqlBindingValue<'a>>
  {
    vec![self.0.into()].into_iter()
  }
}

impl<'a, T0, T1> IntoBindings<'a> for (T0, T1)
where
  T0: Into<SqlBindingValue<'a>>,
  T1: Into<SqlBindingValue<'a>>,
{
  fn into_bindings_iter(self) -> impl Iterator<Item = SqlBindingValue<'a>>
  {
    vec![self.0.into(), self.1.into()].into_iter()
  }
}

impl<'a, T0, T1, T2> IntoBindings<'a> for (T0, T1, T2)
where
  T0: Into<SqlBindingValue<'a>>,
  T1: Into<SqlBindingValue<'a>>,
  T2: Into<SqlBindingValue<'a>>,
{
  fn into_bindings_iter(self) -> impl Iterator<Item = SqlBindingValue<'a>>
  {
    vec![self.0.into(), self.1.into(), self.2.into()].into_iter()
  }
}

impl<'a, T0, T1, T2, T3, T4> IntoBindings<'a> for (T0, T1, T2, T3, T4)
where
  T0: Into<SqlBindingValue<'a>>,
  T1: Into<SqlBindingValue<'a>>,
  T2: Into<SqlBindingValue<'a>>,
  T3: Into<SqlBindingValue<'a>>,
  T4: Into<SqlBindingValue<'a>>,
{
  fn into_bindings_iter(self) -> impl Iterator<Item = SqlBindingValue<'a>>
  {
    vec![
      self.0.into(),
      self.1.into(),
      self.2.into(),
      self.3.into(),
      self.4.into(),
    ]
    .into_iter()
  }
}

impl<'a> IntoBindings<'a> for Vec<SqlBindingValue<'a>>
{
  fn into_bindings_iter(self) -> impl Iterator<Item = SqlBindingValue<'a>>
  {
    self.into_iter()
  }
}
