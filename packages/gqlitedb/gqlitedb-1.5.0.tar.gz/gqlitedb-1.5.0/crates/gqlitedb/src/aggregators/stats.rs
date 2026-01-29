use std::fmt::Debug;

use super::AggregatorState;

use crate::prelude::*;

#[derive(Debug)]
struct AvgState
{
  value: value::Value,
  count: usize,
}

impl AvgState
{
  fn new() -> Result<Self>
  {
    Ok(Self {
      value: value::Value::Null,
      count: 0,
    })
  }
}

impl AggregatorState for AvgState
{
  fn next(&mut self, value: value::Value) -> crate::Result<()>
  {
    if self.value.is_null()
    {
      self.value = value;
    }
    else
    {
      match value
      {
        value::Value::Null =>
        {}
        value::Value::Integer(i) =>
        {
          self.count += 1;
          match self.value
          {
            value::Value::Integer(vi) => self.value = (vi + i).into(),
            value::Value::Float(vf) => self.value = (vf + i as f64).into(),
            _ => Err(InternalError::InvalidAggregationState)?,
          }
        }
        value::Value::Float(f) =>
        {
          self.count += 1;
          match self.value
          {
            value::Value::Integer(vi) => self.value = (vi as f64 + f).into(),
            value::Value::Float(vf) => self.value = (vf + f).into(),
            _ => Err(InternalError::InvalidAggregationState)?,
          }
        }
        _ => Err(RunTimeError::InvalidArgumentType)?,
      }
    }
    Ok(())
  }
  fn finalise(self: Box<Self>) -> crate::Result<crate::value::Value>
  {
    match self.value
    {
      value::Value::Null => Ok(value::Value::Null),
      value::Value::Integer(vi) => Ok((vi / self.count as i64).into()),
      value::Value::Float(vf) => Ok((vf / self.count as f64).into()),
      _ => Err(InternalError::InvalidAggregationState)?,
    }
  }
}

super::declare_aggregator!(avg, Avg, AvgState, () -> value::Value);

#[derive(Debug)]
struct MinState
{
  value: value::Value,
}

impl MinState
{
  fn new() -> Result<Self>
  {
    Ok(Self {
      value: value::Value::Null,
    })
  }
}

impl AggregatorState for MinState
{
  fn next(&mut self, value: value::Value) -> crate::Result<()>
  {
    if self.value.is_null()
      || (!value.is_null() && value.orderability(&self.value) == std::cmp::Ordering::Less)
    {
      self.value = value;
    }
    Ok(())
  }
  fn finalise(self: Box<Self>) -> crate::Result<crate::value::Value>
  {
    Ok(self.value)
  }
}

super::declare_aggregator!(min, Min, MinState, () -> i64);

#[derive(Debug)]
struct MaxState
{
  value: value::Value,
}

impl MaxState
{
  fn new() -> Result<Self>
  {
    Ok(Self {
      value: value::Value::Null,
    })
  }
}

impl AggregatorState for MaxState
{
  fn next(&mut self, value: value::Value) -> crate::Result<()>
  {
    if self.value.is_null()
      || (!value.is_null() && value.orderability(&self.value) == std::cmp::Ordering::Greater)
    {
      self.value = value;
    }
    Ok(())
  }
  fn finalise(self: Box<Self>) -> crate::Result<crate::value::Value>
  {
    Ok(self.value)
  }
}

super::declare_aggregator!(max, Max, MaxState, () -> i64);

#[derive(Debug)]
struct PercentileDiscState
{
  values: Vec<f64>,
  percentile: f64,
}

impl PercentileDiscState
{
  fn new(percentile: value::Value) -> Result<Self>
  {
    Ok(Self {
      values: Default::default(),
      percentile: percentile.try_into()?,
    })
  }
}

impl AggregatorState for PercentileDiscState
{
  fn next(&mut self, value: value::Value) -> crate::Result<()>
  {
    if !value.is_null()
    {
      self.values.push(value.try_into()?);
    }
    Ok(())
  }
  fn finalise(self: Box<Self>) -> crate::Result<crate::value::Value>
  {
    if !self.percentile.is_finite() || !(0.0..=1.0).contains(&self.percentile)
    {
      return Err(
        RunTimeError::NumberOutOfRange {
          value: self.percentile,
          min: 0.0,
          max: 1.0,
        }
        .into(),
      );
    }

    if self.values.is_empty()
    {
      return Ok(0.0.into());
    }

    let mut sorted = self.values;
    sorted.sort_by(|a, b| a.total_cmp(b));

    let n = sorted.len() as f64;
    let index = (self.percentile * (n - 1.0)).round() as usize;

    Ok(sorted[index].into())
  }
}

super::declare_aggregator!(percentiledisc, PercentileDisc, PercentileDiscState, (value::Value) -> f64);

#[derive(Debug)]
struct PercentileContState
{
  values: Vec<f64>,
  percentile: f64,
}

impl PercentileContState
{
  fn new(percentile: value::Value) -> Result<Self>
  {
    Ok(Self {
      values: Default::default(),
      percentile: percentile.try_into()?,
    })
  }
}

impl AggregatorState for PercentileContState
{
  fn next(&mut self, value: value::Value) -> crate::Result<()>
  {
    if !value.is_null()
    {
      self.values.push(value.try_into()?);
    }
    Ok(())
  }
  fn finalise(self: Box<Self>) -> crate::Result<crate::value::Value>
  {
    if !self.percentile.is_finite() || !(0.0..=1.0).contains(&self.percentile)
    {
      return Err(
        RunTimeError::NumberOutOfRange {
          value: self.percentile,
          min: 0.0,
          max: 1.0,
        }
        .into(),
      );
    }

    if self.values.is_empty()
    {
      return Ok(0.0.into());
    }

    let mut sorted = self.values;
    sorted.sort_by(|a, b| a.total_cmp(b));

    let n = sorted.len() as f64;
    let pos = self.percentile * (n - 1.0);
    let lower_index = pos.floor() as usize;
    let upper_index = lower_index + 1;

    if lower_index >= sorted.len() - 1
    {
      return Ok(sorted[sorted.len() - 1].into());
    }

    let weight = pos - pos.floor();
    let lower = sorted[lower_index];
    let upper = sorted[upper_index];

    Ok((lower + weight * (upper - lower)).into())
  }
}

super::declare_aggregator!(percentilecont, PercentileCont, PercentileContState, (value::Value) -> f64);
