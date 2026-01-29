import pytest

from agton.ton import Cell, begin_cell
from agton.ton.cell import OrdinaryCell
from agton.ton.common import BitString

def test_traversal():
    def count_bits(c: Cell) -> int:
        ans = 0
        for b in c.data:
            ans += b
        for r in c.refs:
            ans += count_bits(r)
        return ans
    
    c = OrdinaryCell(
        BitString('001' * 3),
        refs=[
            OrdinaryCell(BitString('0110'), []),
            OrdinaryCell(BitString('01011110'), [])
        ]
    )
    assert count_bits(c) == 3 + 2 + 5

def test_rhombus():
    #    a
    #   / \
    #  b  c
    #  \ /
    #   d
    d = Cell.empty()
    b = OrdinaryCell(BitString('0'), [d])
    c = OrdinaryCell(BitString('1'), [d])
    a = OrdinaryCell(BitString(''), [b, c])
    
    cs = a.begin_parse()
    d1 = cs.load_ref().begin_parse().load_ref()
    d2 = cs.load_ref().begin_parse().load_ref()
    assert d1 is d2

def test_storing_loading():
    c = (
        begin_cell()
        .store_bit(0)
        .store_bool(True)
        .store_bytes(b'abc')
        .store_uint(90, 32)
        .store_int(-13, 32)
        .store_coins(99)
        .store_var_uint(543210, 32)
        .store_var_int(-543210, 32)
        .end_cell()
    )
    s = c.begin_parse()
    assert s.load_bit() == 0 
    assert s.load_bool() == True 
    assert s.load_bytes(3) == b'abc'
    assert s.load_uint(32) == 90
    assert s.load_int(32) == -13
    assert s.load_coins() == 99
    assert s.load_var_uint(32) == 543210
    assert s.load_var_int(32) == -543210
    s.end_parse()

def test_conversions():
    c = (
        begin_cell()
        .store_coins(777)
        .store_ref(
            begin_cell()
            .store_uint(0, 3)
            .store_ref(Cell.empty())
            .end_cell()
        )
        .store_ref(Cell.empty())
        .end_cell()
    )
    assert c.to_builder().to_cell() == c
    assert c.to_slice().to_cell() == c

@pytest.mark.parametrize("v, n, should_raise", [
    (-1337, 64, False),
    (0, 1, False),
    (-1, 1, False),
    ((1 << 256) - 1, 257, False),
    (-(1 << 256), 257, False),
    (-(1 << 40), 32, True),
    (0, 0, True),
])
def test_storing_loading_int(v: int, n: int, should_raise: bool):
    if should_raise:
        with pytest.raises(Exception):
            c = begin_cell().store_int(v, n).end_cell()
        return
    c = begin_cell().store_int(v, n).end_cell()
    cs = c.begin_parse()
    assert cs.load_int(n) == v

@pytest.mark.parametrize("v, n, should_raise", [
    (7777, 64, False),
    (0, 1, False),
    (1, 1, False),
    (0, 256, False),
    ((1 << 256) - 1, 256, False),
    (-5, 32, True),
    (1 << 40, 32, True),
    (0, 0, True),
])
def test_storing_loading_uint(v: int, n: int, should_raise: bool):
    if should_raise:
        with pytest.raises(Exception):
            c = begin_cell().store_uint(v, n).end_cell()
        return
    c = begin_cell().store_uint(v, n).end_cell()
    cs = c.begin_parse()
    assert cs.load_uint(n) == v

def test_depth_limit():
    c = Cell.empty()
    for _ in range(1023):
        c = OrdinaryCell(BitString(), refs=[c])
    with pytest.raises(Exception):
        c = OrdinaryCell(BitString(), refs=[c])

def test_data_limit():
    OrdinaryCell(BitString('0' * 1023), [])
    with pytest.raises(Exception):
        OrdinaryCell(BitString('0' * 1024), [])

def test_refs_limit():
    OrdinaryCell(BitString('0'), [Cell.empty()] * 4)
    with pytest.raises(Exception):
        OrdinaryCell(BitString('0'), [Cell.empty()] * 5)
