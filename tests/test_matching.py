# $ python -m pytest -v

from decimal import Decimal
from app.core.order_book import OrderBook
from app.core.order_types import Order, Side, OrderType
from app.core.matching import match_order

def test_limit_rest_and_bbo():
    """
    Best Bid and Offer
    """
    ob = OrderBook("BTC-USDT")
    o1 = Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('2'), Decimal('70000'))
    o2 = Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('11'), Decimal('60000'))
    o3 = Order("BTC-USDT", Side.BUY, OrderType.LIMIT, Decimal('1'), Decimal('50000'))
    o4 = Order("BTC-USDT", Side.BUY, OrderType.LIMIT, Decimal('17'), Decimal('40000'))
    o5 = Order("BTC-USDT", Side.BUY, OrderType.LIMIT, Decimal('10'), Decimal('20000'))
    ob.add_limit_order(o1)
    ob.add_limit_order(o2)
    ob.add_limit_order(o3)
    ob.add_limit_order(o4)
    ob.add_limit_order(o5)
    best_bid, best_ask = ob.get_bbo()
    assert best_bid == Decimal('50000')
    assert best_ask == Decimal('60000')

def test_market_consumes_levels():
    """
    ASKS[quantity, price]: [1, 100],[1.5, 200]\n
    BID[quantity, price]: MARKET [2]\n
    EXPECT: 2 orders at 100 and 200
    """
    ob = OrderBook("BTC-USDT")
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1'), Decimal('100')))
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1.5'), Decimal('200')))
    taker = Order("BTC-USDT", Side.BUY, OrderType.MARKET, Decimal('2'))
    trades = match_order(taker, ob)
    total_qty, total_price = sum(Decimal(t.quantity) for t in trades), sum(Decimal(t.price) for t in trades)
    assert total_qty == Decimal('2')
    assert total_price == Decimal('300')

def test_ioc_order():
    """
    ASKS[quantity, price]: [1, 100],[1.5, 200]\n
    BID[quantity, price]: IOC [1, 150]\n
    EXPECT: 1 order at 100
    """
    ob = OrderBook("BTC-USDT")
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1'), Decimal('100')))
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1.5'), Decimal('200')))
    taker = Order("BTC-USDT", Side.BUY, OrderType.IOC, Decimal('2'), Decimal('150'))
    trades = match_order(taker, ob)
    total_qty, total_price = sum(Decimal(t.quantity) for t in trades), sum(Decimal(t.price) for t in trades)
    assert total_qty == Decimal('1')
    assert total_price == Decimal('100')

def test_partial_ioc_order():
    """
    ASKS[quantity, price]: [1, 100],[1.5, 200]\n
    BID[quantity, price]: IOC [2, 250]\n
    EXPECT: 1 order at 100, and rest cancel
    """
    ob = OrderBook("BTC-USDT")
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1'), Decimal('100')))
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1.5'), Decimal('200')))
    taker = Order("BTC-USDT", Side.BUY, OrderType.IOC, Decimal('2'), Decimal('150'))
    trades = match_order(taker, ob)
    total_qty, total_price = sum(Decimal(t.quantity) for t in trades), sum(Decimal(t.price) for t in trades)
    assert total_qty == Decimal('1')
    assert total_price == Decimal('100')

def test_limit_order():
    """
    ASKS[quantity, price]: [1, 100],[1.5, 200]\n
    BID[quantity, price]: LIMIT [2, 250]\n
    EXPECT: 2 orders, one at 100 and another at 200
    """
    ob = OrderBook("BTC-USDT")
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1'), Decimal('100')))
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1.5'), Decimal('200')))
    taker = Order("BTC-USDT", Side.BUY, OrderType.LIMIT, Decimal('2'), Decimal('250'))
    trades = match_order(taker, ob)
    total_qty, total_price = sum(Decimal(t.quantity) for t in trades), sum(Decimal(t.price) for t in trades)
    assert total_qty == Decimal('2')
    assert total_price == Decimal('300')

def test_market_order():
    """
    ASKS[quantity, price]: [1, 100],[1.5, 110]\n
    BID[quantity, price]: MARKET [1, nil]\n
    EXPECT: 1 order at 100
    """
    ob = OrderBook("BTC-USDT")
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1'), Decimal('100')))
    ob.add_limit_order(Order("BTC-USDT", Side.SELL, OrderType.LIMIT, Decimal('1.5'), Decimal('110')))
    taker = Order("BTC-USDT", Side.BUY, OrderType.MARKET, Decimal('1'))
    trades = match_order(taker, ob)
    total_qty, total_price = sum(Decimal(t.quantity) for t in trades), sum(Decimal(t.price) for t in trades)
    assert total_qty == Decimal('1')
    assert total_price == Decimal('100')

def test_market_sell_order():
    """

    """
    ob = OrderBook("BTC-USDT")
    ob.add_limit_order(Order("BTC-USDT", Side.BUY, OrderType.LIMIT, Decimal('1'), Decimal('100')))
    ob.add_limit_order(Order("BTC-USDT", Side.BUY, OrderType.LIMIT, Decimal('1.5'), Decimal('110')))
    taker = Order("BTC-USDT", Side.SELL, OrderType.MARKET, Decimal('1'))
    trades = match_order(taker, ob)
    total_qty, total_price = sum(Decimal(t.quantity) for t in trades), sum(Decimal(t.price) for t in trades)
    assert total_qty == Decimal('1')
    assert total_price == Decimal('110')