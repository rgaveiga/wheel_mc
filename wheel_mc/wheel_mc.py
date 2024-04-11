from numpy import full,zeros,exp,cumsum,round
from numpy.random import normal
from numpy.lib.scimath import log,sqrt
from scipy import stats

class Simulation:
    def __init__(self):
        '''
        __init__() -> class constructor.

        Returns
        -------
        None.
        '''
        self.__minprice=0.0
        self.__nperiods=120
        self.__calls_deadline=0
        self.__npaths=100000
        self.__volatility=0.2
        self.__n=100
        self.__s0=100.0
        self.__inimoney=0.0
        self.__r=0.01
        self.__call_strike_factor=0.05
        self.__put_strike_factor=0.05
        self.__money=None
        self.__stock=None
        self.__s=None
        self.__missed=None
        self.__nopencalls=None
        self.__nopenputs=None
        self.__nexercisedcalls=None
        self.__nexercisedputs=None
        self.__money_spent=None
        self.__write_puts_if_no_calls=False
        self.__savelog=False
        
    def run(self):
        '''
        run() -> runs a simulation of the Wheel strategy.

        Returns
        -------
        None.
        '''
        self.__money=zeros((self.__npaths,self.__nperiods))
        self.__money[:,0]=self.__inimoney
        self.__stock=zeros((self.__npaths,self.__nperiods),int)
        self.__missed=zeros(self.__npaths,int)
        self.__nopencalls=zeros(self.__npaths,int)
        self.__nopenputs=zeros(self.__npaths,int)
        self.__nexercisedcalls=zeros(self.__npaths,int)
        self.__nexercisedputs=zeros(self.__npaths,int)
        self.__money_spent=full(self.__npaths,self.__inimoney)
        days_per_period=21  
        T=self.__nperiods*days_per_period       # Total simulation time (in days)
        t=1.0/T                                 # Fraction of T corresponding to one trading day
        r=self.__r/12*self.__nperiods           # Risk-free interest rate for T
        sigma=self.__volatility*sqrt(T/252)     # Volatility for T
        minprice=self.__s0*self.__minprice
        
        if minprice<0.01:
            minprice=0.01
            
        if self.__calls_deadline<1 or self.__calls_deadline>days_per_period:
            self.__calls_deadline=days_per_period
                
        # Generate price paths
        self.__s=(r-0.5*sigma**2.0)*t+sigma*sqrt(t)*normal(0,1,
                                                           (self.__npaths,T))
        self.__s[:,0]=log(self.__s0)
        self.__s=round(exp(cumsum(self.__s,axis=1)),2)
        #---
        
        if self.__savelog:
            with open("log.dat","w") as f:
                f.write("-------- LOG --------\n\n")
        
        for i in range(self.__npaths):
            writtencall=writtenput=False
            purchaseprice=[]
            
            if self.__savelog:
                strlog="TRADING PATH #%d\n" % i
                
            for j in range(self.__nperiods):
                missed=True
                writeput=False
                m=(j+1)*days_per_period-1
                day_1=m-days_per_period+1
                
                if self.__savelog:
                    strlog+="   PERIOD #%d\n" % j
                    strlog+="      Spot price at day 1: %.2f\n" \
                        % self.__s[i,day_1]
                
                if j>0:
                    self.__money[i,j]=self.__money[i,j-1]
                    self.__stock[i,j]=self.__stock[i,j-1]
                
                # Open new call or put position
                if len(purchaseprice)>0:
                    xc=[0.0 for x in purchaseprice]
                    writeput=False
                    
                    for l in range(day_1,m):   
                        if 0.0 not in xc:
                            break
                        elif (l-day_1)==self.__calls_deadline:
                            if self.__write_puts_if_no_calls and \
                                not writtencall:
                                writeput=True
                                
                            break
                        else:
                            xctmp=round((self.__s[i,l]+self.__s[i,l]*
                                             self.__call_strike_factor),2)
                            t2maturity=(m-l)/252.0
                            c=self.__getoptionprice("call",self.__s[i,l],xctmp,
                                                    t2maturity)
                            
                            if c<0.01:
                                c=0.01
                        
                        for k in range(len(purchaseprice)):
                            if xc[k]>0.0:
                                continue

                            if (xctmp+c)>purchaseprice[k]:                        
                                xc[k]=xctmp
                                self.__money[i,j]+=c*self.__n
                                self.__nopencalls[i]+=1
                                        
                                if missed:
                                    missed=False
                                    
                                if not writtencall:
                                    writtencall=True
                    
                                if self.__savelog:
                                    strlog+="      ------\n"
                                    strlog+="      Covered call is written!\n"
                                    strlog+="         Spot price: %.2f\n" % \
                                        self.__s[i,l]
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
                        day_open_put=day_1+self.__calls_deadline-1
                        writeput=False
                    else:
                        day_open_put=day_1

                    t2maturity=(m-day_open_put)/252.0                    
                    xp=round((self.__s[i,day_open_put]-self.__s[i,day_open_put]*
                              self.__put_strike_factor),2)
                
                    if xp>=minprice:
                        p=self.__getoptionprice("put",self.__s[i,day_open_put],
                                                xp,t2maturity)
                        
                        if p<0.01:
                            p=0.01
                        
                        self.__money[i,j]+=p*self.__n
                        self.__nopenputs[i]+=1
                        writtenput=True
                        
                        if missed:
                            missed=False
                            
                        if self.__savelog:
                            strlog+="      ------\n"
                            strlog+="      Cash-secured put is written!\n"
                            strlog+="         Days to maturity: %d\n" \
                                % (m-day_open_put)
                            strlog+="         Put strike: %.2f\n" % xp
                            strlog+="         Put premium: %.2f\n" % p
                #---
                    
                # Check if an open call or put is exercised
                if self.__savelog:
                    strlog+="      ------\n"
                    strlog+="      Spot price at maturity: %.2f\n" \
                            %self.__s[i,m]
                                    
                if writtencall:
                    for k in range(len(purchaseprice)):                    
                        if xc[k]>0.0 and xc[k]<=self.__s[i,m]:
                            self.__money[i,j]+=xc[k]*self.__n
                            self.__stock[i,j]-=self.__n
                            self.__nexercisedcalls[i]+=1
                                    
                            if self.__savelog:
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
                    if xp>=self.__s[i,m]:
                        self.__money[i,j]-=xp*self.__n
                        self.__stock[i,j]+=self.__n
                        self.__nexercisedputs[i]+=1
                        
                        purchaseprice.append(xp)
                           
                        if self.__savelog:
                            strlog+="      ------\n"
                            strlog+="      Put was exercised!\n"
                            strlog+="         Stock purchase price: %.2f\n" % xp
                            
                        if self.__money[i,j]<0.0:
                            self.__money_spent[i]-=self.__money[i,j]
                            
                            if self.__savelog:
                                strlog+="         Money from pocket: %.2f\n" \
                                    % (-self.__money[i,j])                                    
                                    
                            self.__money[i,j]=0.0
                                
                    writtenput=False
                #---
                        
                if missed:
                    self.__missed[i]+=1
                    
                    if self.__savelog:
                        strlog+="      ------\n"
                        strlog+="      No trade was open!\n"
                        
                if self.__savelog:
                    strlog+="      ------\n"
                    strlog+="      Invested money: %.2f\n" \
                        % self.__money_spent[i]
                    strlog+="      Money in account: %.2f\n" % \
                        self.__money[i,j]
                    strlog+="      Number of shares: %d\n" % \
                        self.__stock[i,j]
                        
                    if len(purchaseprice)>0:
                        strlog+="      Purchase prices: %s\n" % purchaseprice
                        strlog+="      Stock price: %.2f\n" % self.__s[i,m]
                        strlog+="      Total stock position: %.2f\n" %\
                            (self.__s[i,m]*self.__stock[i,j])
                        
                    strlog+="      Total position (money+stock): %.2f\n" % \
                        (self.__money[i,j]+self.__stock[i,j]*
                         self.__s[i,m])
                
            if self.__savelog:
                with open("log.dat","a") as f:
                    f.write(strlog)

    def __getoptionprice(self,optype,s,x,time2maturity):
        '''
        __getoptionprice(optype,s,x,time2maturity) -> returns the premium of an 
        option.

        Parameters
        ----------
        optype : string
            Option type (either 'call' or 'put').
        s : float
            Stock price.
        x : float
            Strike.
        time2maturity : float
            Time left to maturity, in years.

        Returns
        -------
        premium : float
            Option premium.
        '''
        d1=(log(s/x)+(self.__r+self.__volatility*self.__volatility/2.0)*
            time2maturity)/(self.__volatility*sqrt(time2maturity))
        d2=d1-self.__volatility*sqrt(time2maturity)        
        
        if optype=="call":		
            premium=round((s*stats.norm.cdf(d1)-
                           x*exp(-self.__r*time2maturity)*
                           stats.norm.cdf(d2)),2)
        elif optype=="put":
            premium=round((x*exp(-self.__r*time2maturity)*
                           stats.norm.cdf(-d2)-s*stats.norm.cdf(-d1)),2)
                
        return premium
    
    '''
    Class properties
    ----------------
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
    minimum_price : float, optional
        Minimum price, as a fraction of the initial stock price, below which 
        no puts are written. Default is zero, which means US$ 0.01.
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
    '''       
    @property
    def number_of_options(self):
        return self.__n
    
    @number_of_options.setter
    def number_of_options(self,x):
        if isinstance(x,int) and x>0:
            self.__n=x
        else:
            raise ValueError("An integer greater than zero is expected!")

    @property
    def number_of_trading_paths(self):
        return self.__npaths
    
    @number_of_trading_paths.setter
    def number_of_trading_paths(self,x):
        if isinstance(x,int) and x>0:
            self.__npaths=x
        else:
            raise ValueError("An integer greater than zero is expected!")
 
    @property
    def number_of_periods(self):
        return self.__nperiods
    
    @number_of_periods.setter
    def number_of_periods(self,x):
        if isinstance(x,int) and x>0:
            self.__nperiods=x
        else:
            raise ValueError("An integer greater than zero is expected!")
        
    @property
    def initial_money(self):
        return self.__inimoney
    
    @initial_money.setter
    def initial_money(self,x):
        if isinstance(x,(int,float)) and x>=0.0:
            self.__inimoney=x
        else:
            raise ValueError("A number greater than or equal to zero is expected!")
    
    @property
    def initial_stock_price(self):
        return self.__s0
    
    @initial_stock_price.setter
    def initial_stock_price(self,x):
        if isinstance(x,(int,float)) and x>0.0:
            self.__s0=x
        else:
            raise ValueError("A number greater than zero is expected!")
            
    @property
    def minimum_price(self):
        return self.__minprice
    
    @minimum_price.setter
    def minimum_price(self,x):
        if isinstance(x,float) and x>=0.0 and x<1.0:
            self.__minprice=x
        else:
            raise ValueError("A number in the [0,1[ interval is expected!")

    @property
    def volatility(self):
        return self.__volatility
    
    @volatility.setter
    def volatility(self,x):
        if isinstance(x,float) and x>0.0:
            self.__volatility=x
        else:
            raise ValueError("A number greater than zero is expected!")

    @property
    def risk_free_rate(self):
        return self.__r
    
    @risk_free_rate.setter
    def risk_free_rate(self,x):
        if isinstance(x,float) and x>=0.0:
            self.__r=x
        else:
            raise ValueError("A number greater than or equal to zero is expected!")
            
    @property
    def call_strike_factor(self):
        return self.__call_strike_factor

    @call_strike_factor.setter
    def call_strike_factor(self,x):
        if isinstance(x,float):
            self.__call_strike_factor=x
        else:
            raise ValueError("A number is expected!")
            
    @property
    def put_strike_factor(self):
        return self.__put_strike_factor

    @put_strike_factor.setter
    def put_strike_factor(self,x):
        if isinstance(x,float):
            self.__put_strike_factor=x
        else:
            raise ValueError("A number is expected!")

    @property
    def covered_calls_deadline(self):
        return self.__calls_deadline
    
    @covered_calls_deadline.setter
    def covered_calls_deadline(self,x):
        if isinstance(x,int) and x>=0:
            self.__calls_deadline=x
        else:
            raise ValueError("An integer greater than or equal to zero is expected!")

    @property
    def write_puts_if_no_calls(self):
        return self.__write_puts_if_no_calls

    @write_puts_if_no_calls.setter
    def write_puts_if_no_calls(self,x):
        if isinstance(x,bool):
            self.__write_puts_if_no_calls=x
        else:
            raise ValueError("A boolean value is expected!")

    @property
    def save_log(self):
        return self.__savelog
    
    @save_log.setter
    def save_log(self,x):
        if isinstance(x,bool):
            self.__savelog=x
        else:
            raise ValueError("A boolean value is expected!")

    '''
    Read-only class properties
    ---------------------------
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
    '''
    @property
    def stock_prices(self):
        return self.__s
    
    @property
    def money(self):
        return self.__money
    
    @property
    def stock(self):
        return self.__stock
    
    @property
    def money_spent(self):
        return self.__money_spent
            
    @property
    def missed_trades(self):
        return self.__missed
    
    @property
    def open_calls(self):
        return self.__nopencalls
    
    @property
    def open_puts(self):
        return self.__nopenputs
    
    @property
    def exercised_calls(self):
        return self.__nexercisedcalls
    
    @property
    def exercised_puts(self):
        return self.__nexercisedputs
    
