from wheel_mc import run_simulation, InputData
import numpy as np
import time

np.random.seed(0)

inputs = InputData(
    number_of_options=100,
    number_of_trading_paths=1,
    number_of_periods=120,
    initial_money=0.0,
    initial_stock_price=25.0,
    minimum_price=0.0,
    volatility=0.2,
    risk_free_rate=0.01,
    call_strike_factor=0.05,
    put_strike_factor=0.05,
    covered_calls_deadline=7,
    write_puts_if_no_calls=True,
    save_log=True,
)

start = time.time()
ret = run_simulation(inputs)
end = time.time()
print("Time: %d ms" % ((end - start) * 1000))

print("Missed trades: %d" % ret.missed_trades)
print("Open calls: %d" % ret.open_calls)
print("Exercised calls: %d" % ret.exercised_calls)
print("Open puts: %d" % ret.open_puts)
print("Exercised puts: %d" % ret.exercised_puts)
print("Invested money: %.2f" % ret.invested_money)
