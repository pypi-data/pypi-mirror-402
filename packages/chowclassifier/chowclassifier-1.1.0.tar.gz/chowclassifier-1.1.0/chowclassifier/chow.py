"""Implementation of a Chow Classifier"""

import numpy as np
import pandas as pd
from scipy.stats import f as Fdist
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from typing import Union
from .utilities import conf_int_to_trend, parse_cmap
from .utilities import SCATTERPARAMS, FILLPARAMS, FITPARAMS, CI_COLORS, TREND_COLORS

### Set plot style
sns.set_style('white')
plt.rcParams.update({'font.family':'serif',
                     'font.size':14,
                     "xtick.bottom" : True,
                     "ytick.left" : True})
plt.rcParams['font.serif'] = ['EB Garamond', 'Garamond','Times New Roman','Times']


class Chow(object):
    """
    Class handling the chow analysis
    Call `run()` to run the analysis (find breakpoint and classify)
    Call afterwards `params()` to get the regressions (y=k * x + b) parameters as
    [[model1_k, model1_b, model1_Rsquared],[model2_k, model2_b, model2_Rsquared]]
    (if the breakpoint is not significant, model1 = model2)
    The significance level of the breakpoint is adjusted with Bonferroni correction,
    i.e. dividing alpha by the number of tests. The confidence interval of the slope
    and intercept are at significance level alpha (not corrected).

    :param df: data on which to perform the Chow categorisation
    :param name: name of the dataset (optional)
    :param initial_breakpoint: breakpoint (if None, midpoint of X series will be used)
    :param timecol: name of time column (X)
    :param ycol: name of the variable column (y)
    :param groupcol: name of the group column (g) if not in df will be ignored
    :param alpha: significance level (without Bonferroni correction), can be changed with ``Chow.set_alpha(0.01)``
    :param margin: range of indexes around breakpoint (or midpoint) where the best breakpoint
                    will be searched. E.g. if X = [0,1,1.5,2,3,4,5], breakpoint = 2 and margin = 1,
                    the set of breakpoints [1.5,2,3] will be tested.
                    (set = 0 if you want to look only at the given breakpoint or the midpoint)
    """
    def __init__(self, df,
                name:str = "",
                initial_breakpoint:float = None,
                timecol:str = 'year',
                ycol:str = 'value',
                groupcol:str = 'g',
                alpha = 0.01,
                margin:int = 2):
        """
        Initialize a Chow classifier object.
        
        :param df: DataFrame containing the data to analyze
        :param name: Name identifier for this dataset
        :param initial_breakpoint: Initial breakpoint value (if None, uses midpoint)
        :param timecol: Name of the time column in df
        :param ycol: Name of the dependent variable column in df
        :param groupcol: Name of the grouping column in df (optional)
        :param alpha: Significance level for statistical tests
        :param margin: Range around breakpoint to search for optimal break
        """
        try:
            self.df = df.loc[:,[timecol,groupcol, ycol]]
            self.df.columns = ('X','g','y')
        except KeyError:
            self.df = df.loc[:,[timecol,ycol]]
            self.df.columns = ('X','y')
            self.df['g'] = 'a'
        self.name = name
        self.df['X'] = pd.to_numeric(self.df['X'])
        self.df['y'] = pd.to_numeric(self.df['y'])
        self.initial_breakpoint = initial_breakpoint
        self.margin=margin
        self.breakpoints = None
        self.normalise=False
        self.tt = -1
        self.m = margin*2+1 # number of hypotheses tested, will be used for Bonferroni correction
        self.F=None
        self.alpha0 = alpha # original significance level
        self.alpha = None # significance level with Bonferroni correction
        self.model0=None
        self.model1=None
        self.model2=None
        self.gCs = {}# sub analysis with grouping on 'g'
        self.successful=None
        self.color = "#000000"
    def get_breakpoint_indices(self):
        """
        Calculate and set the breakpoint indices to search.
        
        :return: List of breakpoint indices to test
        """
        X = sorted(set(self.df['X']))
        if self.breakpoints is not None:
            self.breakpoints = sorted(set(self.breakpoints).intersection(set(X)))
            breakpoint_indices = range(0,len(self.breakpoints))
        else:
            breakpoint_indices = range(0,len(X))
            self.breakpoints = X
        if self.initial_breakpoint is None:
            self.initial_breakpoint = self.breakpoints[int(len(self.breakpoints)/2)]
        if self.initial_breakpoint not in self.breakpoints:
            s = min(range(len(X)), key=lambda i: abs(X[i]-self.initial_breakpoint))
            self.initial_breakpoint = X[s]
        breakpoint_index = self.breakpoints.index(self.initial_breakpoint)
        if breakpoint_index < 3:
            breakpoint_index = 3
            self.initial_breakpoint = self.breakpoints[breakpoint_index]
            print(f"breakpoint index for {self.name} is below 3, will be replace by 3.\n The new breakpoint is {self.initial_breakpoint}")
        elif breakpoint_index > len(X)-4:
            breakpoint_index = len(X)-4
            self.initial_breakpoint = self.breakpoints[breakpoint_index]
            print(f"breakpoint index for {self.name} is above {len(X)-4}, will be replace by {len(X)-4}.\n The new breakpoint is {self.initial_breakpoint}")
        breakpoint_indices = list(range(breakpoint_index - self.margin, breakpoint_index+self.margin))
        return breakpoint_indices
    def find_best_bkp(self, breakpoint_indices=None,**kwargs):
        """
        Find the best breakpoint and run Chow test to find OLS parameters.
        
        Tests multiple breakpoints and selects the one with the best score.
        Updates self.initial_breakpoint with the optimal value.
        
        :param breakpoint_indices: Optional list of indices to test. If None, uses get_breakpoint_indices()
        :param kwargs: Additional keyword arguments (currently unused)
        """
        if breakpoint_indices is not None:
            if not isinstance(breakpoint_indices, list):
                breakpoint_indices=[breakpoint_indices]
            midpoint_index = int(np.median(breakpoint_indices))
        else:
            breakpoint_indices = self.get_breakpoint_indices()
            midpoint_index = breakpoint_indices[int(len(breakpoint_indices)/2)]
        results = {}
        for bk in breakpoint_indices:
            results[bk]=self.run_chow(bkp=self.breakpoints[bk])
        self.results=pd.DataFrame(results)
        self.results = self.results.transpose()
        self.results['delay'] = np.abs(midpoint_index - self.results.index)
        self.results = self.results.sort_values('score')
        #find best breakpoint
        self.initial_breakpoint = self.breakpoints[self.results.score.idxmin()]
        self.m = len(breakpoint_indices)
        self.set_alpha(self.alpha0)
    def run_chow(self, bkp, normalise = False):
        """
        Run Chow test at specified breakpoint.
        
        Fits OLS models to the full dataset and two subsets (before and after breakpoint),
        then calculates the F-statistic to test for structural break.
        
        :param bkp: Breakpoint value at which to split the data
        :param normalise: Whether to normalize the y values before fitting
        :return: Dictionary containing score, F-statistic, and residual sum of squares
        """
        if self.normalise:
            self.df['y']=(self.df['y']-self.df['y'].mean())/self.df['y'].std()
        X=self.df.loc[:,'X']
        y=self.df.loc[:,'y']
        X1=self.df.loc[self.df['X']<bkp,'X']
        X2=self.df.loc[self.df['X']>=bkp,'X']
        y1=self.df.loc[self.df['X']<bkp,'y']
        y2=self.df.loc[self.df['X']>=bkp,'y']
        self.successful = False
        if np.any(X1) and np.any(X2):
            X1=sm.add_constant(X1)
            X2=sm.add_constant(X2)
            X=sm.add_constant(X)
            self.model0=sm.OLS(y,X).fit()
            self.model1=sm.OLS(y1,X1).fit()
            self.model2=sm.OLS(y2,X2).fit()
            self.ss_res_0=np.sum((y-self.model0.predict(X))**2)
            self.ss_res_1=np.sum((y1-self.model1.predict(X1))**2)
            self.ss_res_2=np.sum((y2-self.model2.predict(X2))**2)
            k = 2 # Total number of parameters
            self.F=((self.ss_res_0-(self.ss_res_1+self.ss_res_2))/k) / ((self.ss_res_1+self.ss_res_2)/(X.shape[0]-2*k))
            if X.shape[0]-2*k >0:
                self.score=Fdist.sf(self.F, 2, X.shape[0]-2*k)
                self.successful=True
        if self.successful is False and np.any(X) and X.shape[0]>1:
            X=sm.add_constant(X)
            self.model0=sm.OLS(y,X).fit()
            self.model1 = self.model0
            self.model2 = self.model0
            self.ss_res_0=np.sum((y-self.model0.predict(X))**2)
            self.ss_res_1 = None
            self.ss_res_2 = None
            self.F = None
            self.score = 1
            #self.successful = False
        elif self.successful is False:
            raise ValueError("Data missing for at least one period for {}, with breakpoint {}".format(self.name,self.initial_breakpoint))
        return {"score" : self.score,
                "F" : self.F,
                "ss_res_0" : self.ss_res_0,
                "ss_res_1" : self.ss_res_1,
                "ss_res_2" : self.ss_res_2,}
    def classify(self,**kwargs):
        """
        Classify the dataset based on results of Chow test at significance level alpha.
        
        Possible classification values:
        
        **No significant breakpoint:**

        1. N: non-significant overall trend
        2. I: significant increasing overall trend
        3. D: significant decreasing overall trend

        **Significant breakpoint** (set1 and set2 indicate points before/after breakpoint):

        4. NN: non-significant trend on set1 and non-significant trend on set2
        5. NI: non-significant trend on set1 and significant increasing trend on set2
        6. ND: non-significant trend on set1 and significant decreasing trend on set2
        7. IN: significant increasing trend on set1 and non-significant trend on set2
        8. ID: significant increasing trend on set1 and significant decreasing trend on set2
        9. iI: significant increasing trend on both set1 and set2 with greater increase in set2
        10. Ii: significant increasing trend on both set1 and set2 with greater increase in set1
        11. DN: significant decreasing trend on set1 and non-significant trend on set2
        12. DI: significant decreasing trend on set1 and significant increasing trend on set2
        13. dD: significant decreasing trend on both set1 and set2 with greater decrease in set2
        14. Dd: significant decreasing trend on both set1 and set2 with greater decrease in set1
        
        :param kwargs: Additional keyword arguments (currently unused)
        :return: Dictionary with model parameters
        """
        if self.alpha is None:
            self.set_alpha(self.alpha0)
        if self.score < self.alpha:#
            tt1= conf_int_to_trend(self.model1.conf_int(alpha = self.alpha0))
            tt2= conf_int_to_trend(self.model2.conf_int(alpha = self.alpha0))
            # correction for insignificant trend on one period when actually
            # the trend is significantly higher or lower than the next/previous period
            # at the initial_breakpoint year (i.e. confidence intervals are disjoints at that point)
            if (tt1==0 or tt2==0) and self.initial_breakpoint:
                lci1, uci1 = self.model1.conf_int(alpha = self.alpha0).loc['X',:]
                lci2, uci2 = self.model2.conf_int(alpha = self.alpha0).loc['X',:]
                b1, a1 = self.model1.params
                b2, a2 = self.model2.params
                right_limit = b1 + self.initial_breakpoint * a1  #right limit of first period
                left_limit = b2 + self.initial_breakpoint * a2#left limit of second period
                if right_limit >= left_limit:
                    if b2 + lci2 * self.initial_breakpoint > b1 + uci1 * self.initial_breakpoint:
                        if tt1==0:
                            tt1=1 # the trend is in fact increasing
                        if tt2==0:
                            tt2=2 # the trend is in fact decreasing
                else:
                    if b2 + uci2 * self.initial_breakpoint < b1 + lci1 * self.initial_breakpoint:
                        if tt1==0:
                            tt1=2 # the trend is in fact decreasing
                        if tt2==0:
                            tt2=1 # the trend is in fact increasing
            if tt1==0:
                tc=['NN','NI','ND'][tt2]
            elif tt1==1:
                if tt2==1:
                    tc = ['iI','Ii'][1*(self.model1.params['X']>self.model2.params['X'])]
                else:
                    tc=['IN','','ID'][tt2]
            elif tt1==2:
                if tt2==2:
                    tc = ['dD','Dd'][1*(self.model1.params['X']<self.model2.params['X'])]
                else:
                    tc=['DN','DI'][tt2]
        else:
            #N0, N1 or N2
            self.tt= conf_int_to_trend(self.model0.conf_int(alpha = self.alpha0))
            tc = ['N','I','D'][self.tt]
            self.initial_breakpoint=None
        self.treeclass = tc
        self.set_color()
        return self.params()
    def set_color(self):
        """
        Set the color attribute based on the trend type (tt).
        
        Uses predefined color scheme from TREND_COLORS.
        """
        colors = {'Ii':'#8c510a','iI':'#bf812d','IN':'#dfc27d','NI':'#f6e8c3',
        'Dd':'#c7eae5','dD':'#80cdc1','DN':'#35978f','ND':'#01665e',
        'NN':'#555555','NI':'#006837','ND':'#d73027','N':'#AAAAAA','I':'#1a9850','D':'#a50026',
        'ID':'#9970ab','DI':'#762a83'}
        self.color = TREND_COLORS[self.tt]
    def params_names(self):
        """
        Get list of parameter names for model output.
        
        :return: List of parameter name strings
        """
        return ['intercept','slope',
                'R2','se_intercept','se_slope','n',
                'intercept_pvalue', 'slope_pvalue',
                'intercept_ci_lower','intercept_ci_upper',
                'slope_ci_lower','slope_ci_upper',
                'alpha','alpha_Bonferroni_corrected']
    def params(self):
        """
        Return parameters of the fitted model(s).
        
        :return: Dictionary containing model0, model1, and model2 parameters.
                 If breakpoint is significant, model0 is empty and model1/model2 are populated.
                 Otherwise, model0 is populated and model1/model2 are empty.
        """
        def get_params(model):
            d = [*[i for i in model.params],\
                model.rsquared,\
                *[i for i in model.bse],\
                self.df.shape[0],\
                *[i for i in model.pvalues],\
                *[i for i in model.conf_int(alpha = self.alpha0).loc['const',:]],\
                *[i for i in model.conf_int(alpha = self.alpha0).loc['X',:]],\
                self.alpha0,\
                self.alpha]
            return {k:v for v,k in zip(d,self.params_names())}
        if self.score < self.alpha:
            return {'model0':{},
                    'model1':get_params(self.model1),
                    'model2':get_params(self.model2)}
        else:
            return {'model0':get_params(self.model0),
                    'model1':{},
                    'model2':{}}    
    def run(self, **kwargs):
        """
        Run the complete Chow classification analysis.
        
        Finds best breakpoint, runs Chow test, and classifies the trend.
        
        :param kwargs: Keyword arguments forwarded to find_best_bkp and classify.
                      Can include 'normalise' for run_chow, 'alpha' for classify.
        :return: Classification code (string) or None if analysis fails
        """
        if np.any(self.df):
            try:
                self.find_best_bkp(**kwargs)
            except IndexError:
                print(f"No suitable breakpoint found for {self.name}.")
            self.run_chow(bkp = self.initial_breakpoint, normalise = kwargs.get('normalise',False))
            self.classify(**kwargs)
            return self.treeclass
        else:
            self.successful=False
            return None
    def set_alpha(self, alpha:float):
        """
        Change the current statistical significance level.
        
        The Bonferroni correction will be applied based on the number of tests.

        :param alpha: Significance level, positive float in (0,1)
        """
        self.alpha0 = alpha
        self.alpha = self.alpha0 / max(self.m,1) # applying bonferroni correction

    def summary(self):
        """
        Print the statistical summary of the fitted model(s).
        
        If breakpoint is significant, prints summaries for both model1 and model2.
        Otherwise, prints summary for model0 (whole dataset).
        """
        if self.score < self.alpha:
            print(f"Summary model 1: start-{self.initial_breakpoint}")
            self.model1.summary()
            print(f"Summary model 2: {self.initial_breakpoint}-end")
            self.model2.summary()
        else:
            print(f"Summary model 0: whole dataset")
            self.model0.summary()
    def plot(self, filename:str = None, ax = None, figsize = (16,8),
            ylog:bool=False,
            fill:bool = True,
            scatter:bool = True,
            scatterparams:dict = {},
            fillparams:dict = {},
            fitparams:dict = {},
            linestyles:list = ['dashed','solid','solid'],
            show_legend:bool = True,
            **params):
        """
        Plot the regression model(s).

        :param filename: Filename (with extension format), if None, will call plt.show() instead
        :param ax: Matplotlib axis on which to plot, if None will create new figure
        :param figsize: Tuple with figure size
        :param ylog: Make the y-axis log-scale
        :param fill: Plot the confidence interval
        :param scatter: Plot individual points
        :param scatterparams: Parameters for the scatter plot
        :param fillparams: Parameters for the confidence intervals
        :param fitparams: Parameters for the fitted line
        :param linestyles: Select the linestyle of each trend (list of size 3), set to None if you want to define it in fitparams
        :param show_legend: Legend options passed to ax.legend()
        :param params: Additional parameters including color, xlabel, ylabel, title, xlim, ylim
        """
        ### update plot parameters
        SCATTERPARAMS.update(scatterparams)
        FILLPARAMS.update(fillparams)
        FITPARAMS.update(fitparams)
        # record if it is plotting for parent process
        main_p = ax is None
        # create the plot:
        self.set_color()
        def add_reg_plot(sub_df, model):
            # X values
            X = sorted(set(sub_df['X']))
            inc = (max(X)-min(X))/max(1,len(X)-1)
            X = np.linspace(min(X)-0.5*inc, max(X)+0.5*inc, 2*(len(X)+1))
            Xc = sm.add_constant(X)
            # get confidence interval
            ci_l,ci_u = zip(*model.get_prediction(Xc).conf_int(alpha = self.alpha))
            tt = conf_int_to_trend(model.conf_int(alpha = self.alpha))
            if fill is True:
                # set color depending on time trend
                FILLPARAMS['color'] = fillparams.get('color',CI_COLORS[tt])   
                ax.fill_between(x = X, y1=ci_l, y2 = ci_u, **FILLPARAMS)
            FITPARAMS['color'] = fitparams.get('color',TREND_COLORS[tt])
            try:
                FITPARAMS['linestyle'] = linestyles[tt]
            except:
                FITPARAMS['linestyle'] = FITPARAMS.get('linestyle','solid')
            intercept, slope = model.params
            y0 = intercept + slope * min(X)
            y1 = intercept + slope * max(X)
            ax.plot((min(X),max(X)),(y0,y1), marker = None, **FITPARAMS)
        if ax is None:
            plt.clf()
            f, (ax) = plt.subplots(nrows=1, ncols=1, figsize=figsize)
        if self.score < self.alpha:
            df1 = self.df.loc[self.df['X'] <  self.initial_breakpoint,]
            df2 = self.df.loc[self.df['X'] >= self.initial_breakpoint,]
            add_reg_plot(df1,self.model1)
            add_reg_plot(df2,self.model2)
        else:
            add_reg_plot(self.df,self.model0)
        if scatter is True:
            SCATTERPARAMS['color'] = scatterparams.get('color',self.color)
            ax.scatter(self.df['X'],self.df['y'],
                        **SCATTERPARAMS)
        # Tweak the visual presentation
        ax.xaxis.grid(True)
        ax.yaxis.grid(True)
        ax.minorticks_on()
        ax.set(ylabel=params.get("ylabel", 'y'),
            xlabel=params.get("xlabel",'X'),
            title=params.get("title",self.name))
        ax.set_xlim(*params.get('xlim',(self.df['X'].min(), self.df['X'].max())))
        if params.get('ylim') is not None:
            ax.set_ylim(*params.get('ylim',(self.df['y'].min(), self.df['y'].max())))
        if ylog is True:
            ax.set_yscale('log')
        if show_legend is False:
            ax.get_legend().remove()
        #sns.despine(trim=True, left=True)
        #f.suptitle("")
        if filename is not None and main_p is True:
            plt.savefig(f'{filename}')
        elif main_p is True:
            plt.show()
    def plot_by_group(self,
                      filename:str = None,
                      ax = None,
                      figsize = (16,8),
                      cmap:str = 'Set1',
                      show_legend:bool=True,
                      plot_overall:bool=True,
                      plot_individual_fill:bool = True,
                      scatterparams:dict = {},
                      fillparams:dict = {},
                      fitparams:dict = {},
                      groups_order:list = None,
                      **params):
        """
        Plot the regression model(s) grouped by the group column.

        :param filename: Filename (with extension format), if None, will call plt.show() instead
        :param ax: Matplotlib axis on which to plot, if None will create new figure
        :param figsize: Tuple with figure size
        :param cmap: Colormap name (from matplotlib) or custom color mapping
        :param show_legend: Include the legend
        :param plot_overall: Plot overall trend and confidence interval
        :param plot_individual_fill: Plot confidence interval for each individual group
        :param scatterparams: Parameters for the scatter plot
        :param fillparams: Parameters for the confidence intervals
        :param fitparams: Parameters for the fitted line
        :param groups_order: List showing the order in which the groups must be plotted
        :param params: Additional parameters including xlabel, ylabel, title, ylog, scatter
        """
        cmap = parse_cmap(cmap)
        scatterparams = params.get('scatterparams',{})
        fillparams = params.get('fillparams',{})
        fitparams = params.get('fitparams',{})
        params['xlabel'] = params.get('xlabel','X')
        params['ylabel'] = params.get('ylabel','y')
        # record if it is plotting for parent process
        main_p = ax is None
        if ax is None:
            plt.clf()
            f, (ax) = plt.subplots(nrows=1,
                    ncols=1,
                    sharey=params.get("sharey",True),
                    figsize=params.get('figsize',figsize))
        if groups_order is None:
            groups_order = []
        params['title'] = self.name
        groups_order = groups_order + [x for x in set(self.df['g']) if x not in groups_order]
        self.df['go'] = [groups_order.index(x) for x in self.df['g']]
        for i,(n,dfg) in enumerate(self.df.groupby(['go','g'],sort=True)):
            n = n[1]
            if n not in self.gCs.keys():
                self.gCs[n] = Chow(df = dfg,
                            name = n,
                            initial_breakpoint = self.initial_breakpoint,
                            timecol = 'X',
                            ycol = 'y',
                            groupcol = 'g',
                            alpha = self.alpha,
                            margin = self.margin)
            success = self.gCs[n].run()
            if success is None:
                print(f"Analysis failed for {self.name} {n}")
            else:
                scatterparams['color'] = cmap.get(n,cmap[i])
                fitparams['color'] = cmap.get(n,cmap[i])
                fillparams['color'] = cmap.get(n,cmap[i])
                scatterparams['label'] = n
                self.gCs[n].plot(ax = ax,
                    fill = plot_individual_fill,
                    scatterparams = scatterparams,
                    fillparams = fillparams,
                    fitparams = fitparams,
                    **params)
        if plot_overall is True:
            scatterparams['color'] = (0,0,0)
            fitparams['color'] = (0,0,0)
            fillparams['color'] = (0,0,0)
            scatterparams['label'] = params.get('overall_label','Overall')
            self.plot(ax = ax,
                        scatter = False,
                        scatterparams = scatterparams,
                        fillparams = fillparams,
                        fitparams = fitparams,
                        **params)
        if show_legend is True:
            ax.legend()
        if filename is not None and main_p is True:
            plt.savefig(f'{filename}')
        elif main_p is True:
            plt.show()