__all__ = ['NoValue', 'atomic_attribute_types_map', 'map_attribute_result_to_value']
from minfx.neptune_v2.internal.backends.api_model import Attribute as ApiAttribute, AttributeType

class NoValue:
    pass
VALUE = 'value'
LAST_VALUE = 'last'
VALUES = 'values'
atomic_attribute_types_map = {AttributeType.FLOAT.value: 'floatProperties', AttributeType.INT.value: 'intProperties', AttributeType.BOOL.value: 'boolProperties', AttributeType.STRING.value: 'stringProperties', AttributeType.DATETIME.value: 'datetimeProperties', AttributeType.RUN_STATE.value: 'experimentStateProperties', AttributeType.NOTEBOOK_REF.value: 'notebookRefProperties'}
value_series_attribute_types_map = {AttributeType.FLOAT_SERIES.value: 'floatSeriesProperties', AttributeType.STRING_SERIES.value: 'stringSeriesProperties'}
value_set_attribute_types_map = {AttributeType.STRING_SET.value: 'stringSetProperties'}
_unmapped_attribute_types_map = {AttributeType.FILE_SET.value: 'fileSetProperties', AttributeType.FILE.value: 'fileProperties', AttributeType.IMAGE_SERIES.value: 'imageSeriesProperties', AttributeType.GIT_REF.value: 'gitRefProperties'}

def map_attribute_result_to_value(attribute):
    for attribute_map, value_key in [(atomic_attribute_types_map, VALUE), (value_series_attribute_types_map, LAST_VALUE), (value_set_attribute_types_map, VALUES)]:
        source_property = attribute_map.get(attribute.type)
        if source_property is not None:
            mapped_attribute_entry = getattr(attribute, source_property)
            return getattr(mapped_attribute_entry, value_key)
    return NoValue