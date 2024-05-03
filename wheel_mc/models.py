from pydantic import BaseModel, Field, field_validator, model_validator
from numpy import array, ndarray

class InputData(BaseModel):
    """
    number_of_options : integer, optional
        Number of options in a contract. Default is 100.
    number_of_trading_paths : integer, optional
        Number of independent trading paths generated by Monte Carlo. Default 
        is 100,000.
    number_of_periods : integer, optional
        Number of trading periods per trading path. Default is 120 (it 
        corresponds to 10 years, each period corresponding to one month).
    initial_stock_price : float, optional
        Initial price per share of the underlying asset. Default is US$ 100.
    initial_money : float, optional
        Initial capital available in the trading account before any transaction. 
        Default is zero.
    minimum_price_factor : float, optional
        Fraction of the initial stock price below which no puts are written. 
        Default is zero, which means US$ 0.01.
    volatility : float, optional
        Annualized volatility of the underlying asset. Default is 0.2.
    risk_free_rate : float, optional
        Annualized risk-free interest rate of the economy. Default is 0.01.
    call_strike_factor : float, optional
        Call option strike position above (if positive, OTM) or below (if 
        negative, ITM) the spot price in a given period. Default is 0.05 
        (strike is 5% OTM).
    put_strike_factor : float, optional
        Put option strike position below (if positive, OTM) or above (if 
        negative, ITM) the spot price in a given period. Default is 0.05 
        (strike is 5% OTM).
    covered_calls_deadline : integer, optional
        Maximum number of days in a trading month after which calls are not 
        more written. Default is 0, meaning that calls can be written until the 
        maturity.
    write_puts_if_no_calls : boolean, optional
        Puts are sold in a period where calls are supposed to be the active 
        transaction but the condition for selling calls was not fulfilled 
        until the dealine. Default is False.
    save_log : boolean, optional
        Whether or not to save a log. Default is False.    
    """
    number_of_options: int = Field(default=100, gt=0)
    number_of_trading_paths: int = Field(default=100000, gt=0)
    number_of_periods: int = Field(default=120, gt=0)
    initial_stock_price: float = Field(default=100.0, gt=0.0)
    initial_money: float = Field(default=0.0, ge=0.0)
    minimum_price_factor: float = Field(default = 0.0, ge=0.0, lt=1.0)
    volatility: float = Field(default=0.2, gt=0.0)
    risk_free_rate: float = Field(default = 0.01, gt=0.0)
    call_strike_factor: float = 0.05
    put_strike_factor: float = 0.05
    covered_calls_deadline: int = Field(default = 0, ge=0)
    write_puts_if_no_calls: bool = False
    save_log: bool = False
    
class SimulationData(BaseModel):
    """
    stock_prices : array
        2D Numpy array containing the stock prices generated by Monte Carlo.
    money : array
        2D Numpy array containing the money in the trading account.
    stock : array
        2D Numpy array containing the number of shares owned by the trader.
    money_spent : array
        Numpy array containing the money spent by the trader to cover the 
        assigned puts at the end of trading paths.
    missed_trades : array
        Numpy array containing the total number of missed trades at the end of 
        trading paths.
    open_calls : array
        Numpy array containing the total number of open calls.
    open_puts : array
        Numpy array containing the total number of open puts.
    exercised_calls : array
        Numpy array containing the total number of exercised calls.
    exercised_puts : array
        Numpy array containing the total number of exercised puts.
    """
    stock_prices: ndarray = array([])
    money: ndarray = array([])
    stock: ndarray = array([])
    money_spent: ndarray = array([])
    missed_trades: ndarray = array([])
    open_calls: ndarray = array([])
    open_puts: ndarray = array([])
    exercised_calls: ndarray = array([])
    exercised_puts: ndarray = array([])
    