from nosj import nosj
import numpy as np
import os

def test_myclass_big_array():



    @nosj
    class MyClass:
        a: int
        b: np.ndarray

    obj = MyClass(a=5, b=np.linspace(0,1,1000))
    obj.save('testfile.json')
    obj2 = MyClass.load('testfile.json')

    assert obj.a == obj2.a
    assert np.allclose(obj.b, obj2.b)

def test_myclass_small_array():



    @nosj
    class MyClass:
        a: int
        b: np.ndarray

    obj = MyClass(a=5, b=np.arange(10))
    obj.save('testfile.json')
    obj2 = MyClass.load('testfile.json')

    assert obj.a == obj2.a
    assert np.allclose(obj.b, obj2.b)
    os.remove('testfile.json')

def test_myclass_nested():



    @nosj
    class InnerClass:
        x: float
        y: np.ndarray
        _description: str = "innerclass"

    @nosj
    class MyClass:
        a: int
        b: InnerClass
        _description: str = "myclass"

    inner = InnerClass(x=3.14, y=np.linspace(0,1,50))
    inner.save('innerfile.json')
    obj = MyClass(a=10, b=inner)
    obj.b = 'innerfile.json'  # simulate saving only the description
    obj.save('testfile.json')
    obj2 = MyClass.load('testfile.json', load_subclasses=True)
    assert obj.a == obj2.a

    os.remove('testfile.json')

if __name__ == "__main__":

    import torch

    @nosj
    class InnerClass:
        x: float
        y: torch.Tensor

    @nosj
    class MyClass:
        a: int
        b: InnerClass
        c: torch.Tensor

    inner = InnerClass(x=3.14, y=torch.linspace(0,1,50))
    inner.save('innerfile.json')
    obj = MyClass(a=10, b=inner, c=torch.arange(20))
    obj.b = 'innerfile.json'  # simulate saving only the description
    obj.save('testfile.json')
    obj2 = MyClass.load('testfile.json', load_subclasses=True)
    obj3 = MyClass.load('testfile.json', load_subclasses=False)

    # from torch import Tensor