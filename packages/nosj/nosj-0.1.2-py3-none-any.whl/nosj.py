__version__ = "0.1.2"

__all__ = ['nosj']


from dataclasses import dataclass, replace, asdict as dataclass2dict
from typing import List, _GenericAlias
import json_numpy

from numpy import ndarray, allclose, array, inf
from numpy.lib.format import descr_to_dtype, dtype_to_descr

def update(self, **kwargs):
    return replace(self, **kwargs)

def _to_nosj(self, binary_threshold=100):
    if self.extension is not None and '.' not in fname:
        fname = fname + '.' + self.extension
    if self.extension is not None:
        assert fname.endswith('.' + self.extension), 'File extension does not match class extension'

    
    other = self.copy()

    for key,val in other.__dict__.items():
        if (hasattr(val, '_description') and val._description is not None) and (hasattr(val, 'extension') and val.extension is not None):
            if val._description.endswith(val.extension):
                exec(f'other.{key} = val._description')
        elif hasattr(val, '_to_nosj'):
            exec(f'other.{key} = val._to_nosj(binary_threshold=binary_threshold)')
        elif isinstance(val, List) and len(val)>0:
            new_list = [x if not hasattr(x, '_to_nosj') else x._to_nosj(binary_threshold=binary_threshold) for x in val]
            exec(f'other.{key} = new_list')
        elif isinstance(val, ndarray) and val.size<=binary_threshold:
            descr = dtype_to_descr(val.dtype)
            array_dict = {
                '__numpy_str__': ' '.join(val.__repr__().replace('\n', '').split()),
                'dtype': descr,
                'shape': val.shape,
            }
            exec(f'other.{key} = array_dict')

    if not hasattr(other, '_description'):
        other._description = fname
    
    return dataclass2dict(other)


def save(self, fname, binary_threshold=100):
    res = json_numpy.dumps(self._to_nosj(binary_threshold=binary_threshold), indent=4)
    with open(fname, 'wt') as f:
        f.write(res)

@classmethod
def load(cls, fname, load_subclasses=False):
    with open(fname, 'rb') as f:
        res = json_numpy.loads(f.read())
    res = cls._reinstantiate_subclasses(cls, res, load_subclasses=load_subclasses)
    return res

def __hash__(self):
    descript = self._description
    self._description = 'hash'
    res = hash(self.__repr__())
    self._description = descript
    return res

def __eq__(self, other):
    is_equal = hash(self) == hash(other)
    if is_equal:
        for x in self.__class__.__annotations__.keys():
            cvar = vars(self)[x]
            ovar = vars(other)[x]

            if x == '_description':
                continue
            elif isinstance(cvar, ndarray):
                var_equal = allclose(cvar, ovar)
            else:
                var_equal = (cvar == ovar)
            is_equal = is_equal and var_equal
    return is_equal

def reinstantiate_subclasses(cls, d, load_subclasses=False):
    """recursive function to get attributes back into their right classes"""
    if not hasattr(cls, '__annotations__') and '__numpy_str__' in d:
        return eval(d['__numpy_str__']).astype(d.pop('dtype')).reshape(d.pop('shape'))
    
    if cls.__base__ != (object, str) and hasattr(cls.__base__, '__annotations__'):
        class_dict = cls.__annotations__ | cls.__base__.__annotations__
    else:
        class_dict = cls.__annotations__

    if hasattr(d, 'keys'):
        for key in d.keys():

            if class_dict[key] != type(d[key]) and type(d[key]) == dict:
                d[key] = reinstantiate_subclasses(class_dict[key], d[key])
            elif isinstance(class_dict[key], _GenericAlias):
                subclass = [x for x in class_dict[key].__args__]
                if len(subclass) < len(d[key]):
                    subclass = subclass * len(d[key])
                if hasattr(subclass[0], '__annotations__'):
                    d[key] = [reinstantiate_subclasses(const, x, load_subclasses=load_subclasses) for const, x in zip(subclass,d[key])]
                else:
                    d[key] = [x for const, x in zip(subclass,d[key])]

            elif class_dict[key] == ndarray:
                pass
            elif class_dict[key] != type(d[key]) and type(d[key]) == str and '.' in d[key] and load_subclasses:
                d[key] = class_dict[key].load(d[key])
            elif class_dict[key] != type(d[key]) and load_subclasses:
                if d[key] is not None:
                    d[key] = class_dict[key](**d[key])
                
        return cls(**d)
    elif isinstance(d, str) and load_subclasses:
        return cls.load(d)
    else:
        return d
        
def copy(self):
    return replace(self)

try:
    from torch import allclose as torch_allclose, Tensor, from_numpy
    TORCH_ENABLED = True
    print('torch detected, enabling torch tensor support in nosj')
except ImportError:
    TORCH_ENABLED = False
    print('torch not detected, skipping torch tensor support in nosj')

if TORCH_ENABLED:

    def _to_nosj(self, binary_threshold=100):
        if self.extension is not None and '.' not in fname:
            fname = fname + '.' + self.extension
        if self.extension is not None:
            assert fname.endswith('.' + self.extension), 'File extension does not match class extension'

        
        other = self.copy()
        torch_keys = []
        for key,val in other.__dict__.items():
            if isinstance(val, Tensor):
                exec(f'other.{key} = val.numpy()')
                if key in other.__annotations__:
                    torch_keys.append(key)

        for key,val in other.__dict__.items():
            if (hasattr(val, '_description') and val._description is not None) and (hasattr(val, 'extension') and val.extension is not None):
                if val._description.endswith(val.extension):
                    exec(f'other.{key} = val._description')
            elif isinstance(val, ndarray) and val.size<=binary_threshold:
                descr = dtype_to_descr(val.dtype)
                array_dict = {
                    '__numpy_str__': ' '.join(val.__repr__().replace('\n', '').split()),
                    'dtype': descr,
                    'shape': val.shape,
                }
                exec(f'other.{key} = array_dict')
            elif hasattr(val, '_to_nosj'):
                exec(f'other.{key} = val._to_nosj(binary_threshold=binary_threshold)')                

        if not hasattr(other, '_description'):
            other._description = fname
        
        dictionary_rep = dataclass2dict(other)
        if len(torch_keys)>0: dictionary_rep['_torch_keys'] = torch_keys
        return dictionary_rep

    def reinstantiate_subclasses(cls, d, load_subclasses=False):
        """recursive function to get attributes back into their right classes"""
        if '_torch_keys' in d:
            torch_keys = d.pop('_torch_keys')
        else:
            torch_keys = []

        if '__numpy_str__' in d:
            cdata = eval(d['__numpy_str__']).astype(d.pop('dtype')).reshape(d.pop('shape'))
            if cls == Tensor: cdata = from_numpy(cdata)
            return cdata
        
        if cls.__base__ != (object, str) and hasattr(cls.__base__, '__annotations__'):
            class_dict = cls.__annotations__ | cls.__base__.__annotations__
        else:
            class_dict = cls.__annotations__

        if hasattr(d, 'keys'):
            for key in d.keys():
                if class_dict[key] != type(d[key]) and type(d[key]) == dict:
                    d[key] = reinstantiate_subclasses(class_dict[key], d[key])
                elif isinstance(class_dict[key], _GenericAlias):
                    subclass = [x for x in class_dict[key].__args__]
                    if len(subclass) < len(d[key]):
                        subclass = subclass * len(d[key])
                    if hasattr(subclass[0], '__annotations__'):
                        d[key] = [reinstantiate_subclasses(const, x, load_subclasses=load_subclasses) for const, x in zip(subclass,d[key])]
                    else:
                        d[key] = [x for const, x in zip(subclass,d[key])]

                elif class_dict[key] == ndarray or class_dict[key] == Tensor:
                    pass

                elif class_dict[key] != type(d[key]) and type(d[key]) == str and '.' in d[key] and load_subclasses:
                    d[key] = class_dict[key].load(d[key])
                elif class_dict[key] != type(d[key]) and load_subclasses:
                    if d[key] is not None:
                        d[key] = class_dict[key](**d[key])
            if len(torch_keys)>0:
                for key in torch_keys:
                    if isinstance(d[key], ndarray):
                        d[key] = from_numpy(array(d[key]))
            return cls(**d)

        elif isinstance(d, str) and load_subclasses:
            return cls.load(d)
        else:
            return d

    def __eq__(self, other):
        is_equal = hash(self) == hash(other)
        if is_equal:
            for x in self.__class__.__annotations__.keys():
                cvar = vars(self)[x]
                ovar = vars(other)[x]

                if x == '_description':
                    continue
                elif isinstance(cvar, ndarray):
                    var_equal = allclose(cvar, ovar)
                elif isinstance(cvar, Tensor):
                    var_equal = torch_allclose(cvar, ovar)
                else:
                    var_equal = (cvar == ovar)
                is_equal = is_equal and var_equal
        return is_equal




def nosj(cls):   
    cls._description = cls.__name__.split('.')[-1]
    if 'extension' not in cls.__dict__:
        cls.extension = None
    cls.update       = update
    cls._to_nosj     = _to_nosj
    cls.__hash__     = __hash__
    cls.__eq__       = __eq__
    cls.save         = save
    cls.load         = load
    cls._reinstantiate_subclasses = reinstantiate_subclasses
    cls.copy         = copy
    

    return dataclass(cls)

# how to upload to pypi
# 1. do a version bump in nosj.py
# 2. run>>> python -m build
# 3. run>>> python -m twine upload --repository pypi upload dist/nosj-<version>*