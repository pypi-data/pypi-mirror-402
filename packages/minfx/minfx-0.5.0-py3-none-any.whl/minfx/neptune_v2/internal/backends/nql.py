from __future__ import annotations
__all__ = ['NQLAggregator', 'NQLAttributeOperator', 'NQLAttributeType', 'NQLEmptyQuery', 'NQLQuery', 'NQLQueryAggregate', 'NQLQueryAttribute', 'RawNQLQuery']
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

@dataclass
class NQLQuery:

    def eval(self):
        return self

@dataclass
class NQLEmptyQuery(NQLQuery):

    def __str__(self):
        return ''

class NQLAggregator(str, Enum):
    AND = 'AND'
    OR = 'OR'

@dataclass
class NQLQueryAggregate(NQLQuery):
    items: Iterable[NQLQuery]
    aggregator: NQLAggregator

    def eval(self):
        self.items = list(filter(lambda nql: not isinstance(nql, NQLEmptyQuery), (item.eval() for item in self.items)))
        if len(self.items) == 0:
            return NQLEmptyQuery()
        if len(self.items) == 1:
            return self.items[0]
        return self

    def __str__(self):
        evaluated = self.eval()
        if isinstance(evaluated, NQLQueryAggregate):
            return '(' + f' {self.aggregator.value} '.join(map(str, self.items)) + ')'
        return str(evaluated)

class NQLAttributeOperator(str, Enum):
    EQUALS = '='
    CONTAINS = 'CONTAINS'
    GREATER_THAN = '>'

class NQLAttributeType(str, Enum):
    STRING = 'string'
    STRING_SET = 'stringSet'
    EXPERIMENT_STATE = 'experimentState'
    BOOLEAN = 'bool'
    DATETIME = 'datetime'
    INTEGER = 'integer'
    FLOAT = 'float'

@dataclass
class NQLQueryAttribute(NQLQuery):
    name: str
    type: NQLAttributeType
    operator: NQLAttributeOperator
    value: str | bool

    def __str__(self):
        if isinstance(self.value, bool):
            value = str(self.value).lower()
        else:
            value = f'"{self.value}"'
        return f'(`{self.name}`:{self.type.value} {self.operator.value} {value})'

@dataclass
class RawNQLQuery(NQLQuery):
    query: str

    def eval(self):
        if self.query == '':
            return NQLEmptyQuery()
        return self

    def __str__(self):
        evaluated = self.eval()
        if isinstance(evaluated, RawNQLQuery):
            return self.query
        return str(evaluated)