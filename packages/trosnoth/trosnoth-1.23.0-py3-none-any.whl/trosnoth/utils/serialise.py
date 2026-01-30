# Trosnoth (UberTweak Platform Game)
# Copyright (C) Joshua D Bartlett
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import dataclasses
import enum
import msgpack
from types import UnionType
import typing


class Dumpable:
    '''
    Designed to be used with dataclasses.
    '''

    def dump(self):
        return msgpack.packb(self.dump_to_objects(), use_bin_type=True)

    def dump_to_objects(self):
        coder = DataClassCoder(self)
        return coder.encode(self)

    @classmethod
    def _recurse(cls, value):
        if isinstance(value, Dumpable):
            return value.dump_to_objects()
        if isinstance(value, (list, tuple)):
            return [cls._recurse(child) for child in value]
        if isinstance(value, dict):
            return {
                cls._recurse(k): cls._recurse(v)
                for k, v in value.items()
            }
        return value

    @classmethod
    def rebuild(cls, data_string, validate=True):
        data = msgpack.unpackb(data_string, raw=False, strict_map_key=False)
        return cls.rebuild_from_objects(data, validate=validate)

    @classmethod
    def rebuild_from_objects(cls, data, validate=True):
        coder = DataClassCoder(cls)
        return coder.decode(data, validate=validate)

    def clone(self, validate=True):
        return type(self).rebuild_from_objects(self.dump_to_objects(), validate=validate)

    def validate(self):
        '''
        Subclasses can override this and raise TypeError or ValueError
        if any fields do not have allowable values.
        '''
        pass


class CoderField:
    def __init__(self, field, class_name):
        self.name = field.name
        self.description = f'{class_name}.{self.name}'

        if isinstance(field.type, UnionType):
            possible_types = typing.get_args(field.type)
        else:
            possible_types = [field.type]

        self.coder_by_decoded_type = {}
        self.coder_by_indicator = {}
        self.indicator_by_coder = {}
        for i, t in enumerate(possible_types):
            coder = TypeCoder.build(t, self.description)
            self.coder_by_decoded_type[t] = coder
            self.indicator_by_coder[coder] = i
            self.coder_by_indicator[i] = coder

        if float in possible_types:
            self.coder_by_decoded_type[int] = self.coder_by_decoded_type[float]

        self.coder_by_encoded_type = {}
        use_indicators = False
        for coder in self.coder_by_indicator.values():
            for encoded_type in coder.encoded_types:
                if encoded_type in self.coder_by_encoded_type:
                    # Two options may begin with the same type
                    use_indicators = True
                    break
                self.coder_by_encoded_type[encoded_type] = coder

        if use_indicators:
            self.coder_by_encoded_type = None
        else:
            self.indicator_by_coder = None
            self.coder_by_indicator = None

    def get_possible_encoded_types(self):
        if self.indicator_by_coder:
            return {int}
        return set(self.coder_by_encoded_type)

    def encode(self, value):
        coder = self.coder_by_decoded_type[type(value)]
        result = coder.encode(value)
        if self.indicator_by_coder:
            result.insert(0, self.indicator_by_coder[coder])
            if coder.type == type(None):
                # Once the indicator's there we don't need to encode the None
                result[1:] = []
        return result

    def decode(self, data, validate=True):
        try:
            if self.indicator_by_coder:
                indicator = data.pop(0)
                coder = self.coder_by_indicator[indicator]
                if coder.type == type(None):
                    return None
            else:
                coder = self.coder_by_encoded_type[type(data[0])]
        except KeyError as e:
            raise ValueError(f'While decoding {self.description}: KeyError: {e}')
        return coder.decode(data, validate=validate)


class TypeCoder:
    encoded_types = NotImplemented

    @staticmethod
    def build(field_type, description):
        if field_type in {int, float, str, bytes, bool, type(None)}:
            return PrimitiveTypeCoder(field_type)
        if isinstance(field_type, type) and issubclass(field_type, Dumpable):
            return DumpableTypeCoder(field_type)
        if isinstance(field_type, type) and issubclass(field_type, enum.Enum):
            return EnumTypeCoder(field_type)
        raise TypeError(f'Cannot serialise {field_type} ({description})')

    def __init__(self, field_type):
        self.type = field_type

    def encode(self, value):
        raise NotImplementedError()

    def decode(self, data, validate=True):
        raise NotImplementedError()


class PrimitiveTypeCoder(TypeCoder):
    def __init__(self, field_type):
        super().__init__(field_type)
        self.encoded_types = {field_type}
        if field_type == float:
            self.encoded_types.add(int)

    def encode(self, value):
        return [value]

    def decode(self, data, validate=True):
        result = data.pop(0)
        if validate and type(result) not in self.encoded_types:
            raise TypeError(f'{result} is not a valid {self.type}')
        return result


class DumpableTypeCoder(TypeCoder):
    def __init__(self, field_type):
        super().__init__(field_type)
        self.subcoder = DataClassCoder(field_type)
        self.encoded_types = self.subcoder.fields[0].get_possible_encoded_types()

    def encode(self, value):
        return self.subcoder.encode(value)

    def decode(self, data, validate=True):
        return self.subcoder.decode(data, validate=validate)


class EnumTypeCoder(TypeCoder):
    def __init__(self, field_type):
        super().__init__(field_type)
        self.encoded_types = {
            type(v.value) for v in field_type
        }

    def encode(self, value):
        return [value.value]

    def decode(self, data, validate=True):
        return self.type(data.pop(0))


class DataClassCoder:
    def __init__(self, dataclass_or_instance):
        self.dataclass = (
            dataclass_or_instance if isinstance(dataclass_or_instance, type)
            else (type(dataclass_or_instance)))
        self.name = self.dataclass.__name__
        self.fields = [CoderField(f, self.name) for f in dataclasses.fields(dataclass_or_instance)]

    def encode(self, instance):
        result = []
        for f in self.fields:
            value = getattr(instance, f.name)
            coded = f.encode(value)
            result.extend(coded)
        return result

    def decode(self, data, validate=True):
        args = {}
        for f in self.fields:
            args[f.name] = f.decode(data, validate=validate)
        result = self.dataclass(**args)
        if validate:
            result.validate()
        return result
