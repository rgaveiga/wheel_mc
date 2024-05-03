from numpy import full,zeros,exp,cumsum,round
from numpy.random import normal
from numpy.lib.scimath import log,sqrt
from scipy import stats
from .models import InputData, SimulationData
       
def run_simulation(inputs: InputData | dict) -> SimulationData:
    inputs = (
        inputs
        if isinstance(inputs, InputData)
        else InputData.model_validate(inputs)
        )
    
    money=zeros((inputs.number_of_trading_paths,inputs.number_of_periods))
    money[:,0]=inputs.initial_money
    stock=zeros((inputs.number_of_trading_paths,inputs.number_of_periods),int)
    missed_trades=zeros(inputs.number_of_trading_paths,int)
    open_calls=zeros(inputs.number_of_trading_paths,int)
    open_puts=zeros(inputs.number_of_trading_paths,int)
    exercised_calls=zeros(inputs.number_of_trading_paths,int)
    exercised_puts=zeros(inputs.number_of_trading_paths,int)
    money_spent=full(inputs.number_of_trading_paths,inputs.initial_money)
    days_per_period=21  
    T=inputs.number_of_periods*days_per_period       # Total simulation time (in days)
    t=1.0/T                                 # Fraction of T corresponding to one trading day
    r=inputs.risk_free_rate/12*inputs.number_of_periods           # Risk-free interest rate for T
    vol=inputs.volatility*sqrt(T/252)     # Volatility for T
    minimum_price=inputs.initial_stock_price*inputs.minimum_price_factor
    
    if minimum_price<0.01:
        minimum_price=0.01
        
    if inputs.covered_calls_deadline<1 or inputs.covered_calls_deadline>days_per_period:
        inputs.covered_calls_deadline=days_per_period
            
    # Generate price paths
    stock_prices=(r-0.5*vol**2.0)*t+vol*sqrt(t)*normal(0,1,(inputs.number_of_trading_paths,T))
    stock_prices[:,0]=log(inputs.initial_stock_price)
    stock_prices=round(exp(cumsum(stock_prices,axis=1)),2)
    #---
    
    if inputs.save_log:
        with open("log.dat","w") as f:
            f.write("-------- LOG --------\n\n")
    
    for i in range(inputs.number_of_trading_paths):
        writtencall=writtenput=False
        purchaseprice=[]
        
        if inputs.save_log:
            strlog="TRADING PATH #%d\n" % i
            
        for j in range(inputs.number_of_periods):
            missed=True
            writeput=False
            m=(j+1)*days_per_period-1
            day_1=m-days_per_period+1
            
            if inputs.save_log:
                strlog+="   PERIOD #%d\n" % j
                strlog+="      Spot price at day 1: %.2f\n" \
                    % stock_prices[i,day_1]
            
            if j>0:
                money[i,j]=money[i,j-1]
                stock[i,j]=stock[i,j-1]
            
            # Open new call or put position
            if len(purchaseprice)>0:
                xc=[0.0 for x in purchaseprice]
                writeput=False
                
                for l in range(day_1,m):   
                    if 0.0 not in xc:
                        break
                    elif (l-day_1)==inputs.covered_calls_deadline:
                        if inputs.write_puts_if_no_calls and \
                            not writtencall:
                            writeput=True
                            
                        break
                    else:
                        xctmp=round((stock_prices[i,l]+stock_prices[i,l]*
                                         inputs.call_strike_factor),2)
                        t2m=(m-l)/252.0
                        c=_get_option_price("call",stock_prices[i,l],xctmp,
                                                inputs.risk_free_rate,
                                                inputs.volatility,
                                                t2m)
                        
                        if c<0.01:
                            c=0.01
                    
                    for k in range(len(purchaseprice)):
                        if xc[k]>0.0:
                            continue

                        if (xctmp+c)>purchaseprice[k]:                        
                            xc[k]=xctmp
                            money[i,j]+=c*inputs.number_of_options
                            open_calls[i]+=1
                                    
                            if missed:
                                missed=False
                                
                            if not writtencall:
                                writtencall=True
                
                            if inputs.save_log:
                                strlog+="      ------\n"
                                strlog+="      Covered call is written!\n"
                                strlog+="         Spot price: %.2f\n" % \
                                    stock_prices[i,l]
                                strlog+="         Days to maturity: %d\n" % \
                                    (m-l)
                                strlog+="         Call strike: %.2f\n" % \
                                    xc[k]
                                strlog+="         Call premium: %.2f\n" % \
                                    c
                                strlog+="         Stock purchase price: %.2f\n" \
                                    % purchaseprice[k]
                        
            if len(purchaseprice)==0 or writeput:
                if writeput:
                    day_open_put=day_1+inputs.covered_calls_deadline-1
                    writeput=False
                else:
                    day_open_put=day_1

                t2m=(m-day_open_put)/252.0                    
                xp=round((stock_prices[i,day_open_put]-stock_prices[i,day_open_put]*
                          inputs.put_strike_factor),2)
            
                if xp>=minimum_price:
                    p=_get_option_price("put",stock_prices[i,day_open_put],
                                            xp,inputs.risk_free_rate,inputs.volatility,t2m)
                    
                    if p<0.01:
                        p=0.01
                    
                    money[i,j]+=p*inputs.number_of_options
                    open_puts[i]+=1
                    writtenput=True
                    
                    if missed:
                        missed=False
                        
                    if inputs.save_log:
                        strlog+="      ------\n"
                        strlog+="      Cash-secured put is written!\n"
                        strlog+="         Days to maturity: %d\n" \
                            % (m-day_open_put)
                        strlog+="         Put strike: %.2f\n" % xp
                        strlog+="         Put premium: %.2f\n" % p
            #---
                
            # Check if an open call or put is exercised
            if inputs.save_log:
                strlog+="      ------\n"
                strlog+="      Spot price at maturity: %.2f\n" \
                        %stock_prices[i,m]
                                
            if writtencall:
                for k in range(len(purchaseprice)):                    
                    if xc[k]>0.0 and xc[k]<=stock_prices[i,m]:
                        money[i,j]+=xc[k]*inputs.number_of_options
                        stock[i,j]-=inputs.number_of_options
                        exercised_calls[i]+=1
                                
                        if inputs.save_log:
                            strlog+="      ------\n"
                            strlog+="      Call was exercised!\n"
                            strlog+="         Stock sale price: %.2f\n" \
                                % xc[k]
                            strlog+="         Stock purchase price: %.2f\n" \
                                % purchaseprice[k]
                                
                        purchaseprice[k]=0.0
                                    
                purchaseprice=[x for x in purchaseprice if x>0.0]
                writtencall=False
                
            if writtenput: 
                if xp>=stock_prices[i,m]:
                    money[i,j]-=xp*inputs.number_of_options
                    stock[i,j]+=inputs.number_of_options
                    exercised_puts[i]+=1
                    
                    purchaseprice.append(xp)
                       
                    if inputs.save_log:
                        strlog+="      ------\n"
                        strlog+="      Put was exercised!\n"
                        strlog+="         Stock purchase price: %.2f\n" % xp
                        
                    if money[i,j]<0.0:
                        money_spent[i]-=money[i,j]
                        
                        if inputs.save_log:
                            strlog+="         Money from pocket: %.2f\n" \
                                % (-money[i,j])                                    
                                
                        money[i,j]=0.0
                            
                writtenput=False
            #---
                    
            if missed:
                missed_trades[i]+=1
                
                if inputs.save_log:
                    strlog+="      ------\n"
                    strlog+="      No trade was open!\n"
                    
            if inputs.save_log:
                strlog+="      ------\n"
                strlog+="      Invested money: %.2f\n" \
                    % money_spent[i]
                strlog+="      Money in account: %.2f\n" % \
                    money[i,j]
                strlog+="      Number of shares: %d\n" % \
                    stock[i,j]
                    
                if len(purchaseprice)>0:
                    strlog+="      Purchase prices: %s\n" % purchaseprice
                    strlog+="      Stock price: %.2f\n" % stock_prices[i,m]
                    strlog+="      Total stock position: %.2f\n" %\
                        (stock_prices[i,m]*stock[i,j])
                    
                strlog+="      Total position (money+stock): %.2f\n" % \
                    (money[i,j]+stock[i,j]*
                     stock_prices[i,m])
            
        if inputs.save_log:
            with open("log.dat","a") as f:
                f.write(strlog)
                
        return SimulationData(stock_prices = stock_prices,
                              money = money,                              
                              stock = stock,
                              money_spent = money,
                              missed_trades = missed_trades,
                              open_calls = open_calls,
                              open_puts = open_puts,
                              exercised_calls = exercised_calls,
                              exercised_puts = exercised_puts)

def _get_option_price(optype: str, s: float, x: float, r: float, vol: float, time_to_maturity: float) -> float:
    '''
    Returns the premium of an option calculated using the Black-Scholes model.

    Parameters
    ----------
    optype : string
        Option type (either 'call' or 'put').
    s : float
        Stock price.
    x : float
        Strike.
    time_to_maturity : float
        Time left to maturity, in years.

    Returns
    -------
    premium : float
        Option premium.
    '''
    d1=(log(s/x)+(r+vol*vol/2.0)*
        time_to_maturity)/(vol*sqrt(time_to_maturity))
    d2=d1-vol*sqrt(time_to_maturity)        
    
    if optype=="call":		
        premium=round((s*stats.norm.cdf(d1)-
                       x*exp(-r*time_to_maturity)*
                       stats.norm.cdf(d2)),2)
    elif optype=="put":
        premium=round((x*exp(-r*time_to_maturity)*
                       stats.norm.cdf(-d2)-s*stats.norm.cdf(-d1)),2)
            
    return premium