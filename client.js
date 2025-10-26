const symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "ADA-USDT"];
const sides = ["buy", "sell"];
const orderTypes = ["market", "limit", "ioc", "fok"];

const orders = Array.from({ length: 1000 }, () => {
  const symbol = symbols[Math.floor(Math.random() * symbols.length)];
  const side = sides[Math.floor(Math.random() * sides.length)];
  const order_type = orderTypes[Math.floor(Math.random() * orderTypes.length)];
  const quantity = parseFloat((Math.random() * 1000 + 1).toFixed(2));
  const price = parseFloat((Math.random() * 100000 + 10).toFixed(2));
  return { symbol, side, order_type, quantity, price };
});

const makeOrder = async (order) => {
  fetch("http://127.0.0.1:8000/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(order),
  }).catch(console.error);
};

let i = 0;
const intervalId = setInterval(() => {
  if (i >= orders.length) {
    clearInterval(intervalId);
  } else {
    for (let j = 0; j < 100 && i < orders.length; j++) makeOrder(orders[i++]);
    console.log(i, "requests sent");
  }
}, 1);
