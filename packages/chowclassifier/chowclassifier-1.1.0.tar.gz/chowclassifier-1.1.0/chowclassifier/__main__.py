# __main__.py
import argparse
from chowclassifier.chewdata import ChewData


def main():
    """
    run analysis on given data

    :params -f, --filename: filename
    :params -s, --sep: separator for parsing the filename (if type csv)
    :params -X, --timecol: timecol
    :params -y, --ycol: ycol
    :params -n, --namecol: name of column for groupby
    :params -b, --breakpoint: initial breakpoint (if None, midpoint will be taken)
    :params -k, --breakpoints: candidates for breakpoints (list)
    :params -m, --margin: margin around initial breakpoint
    :params -o, --output: filename for the excel or csv file output
    :params -p, --path: path where the figures will be saved
    :params -a, --alpha: significance level in (0,1)
    :params --no-figures: Do not export figures
    :params --no-table: Do not export results table
    :params --nrows: Numbers of rows in the grouped figure (leave ncols blank)
    :params --ncols: Number of columns in the groupe figure (leave nrows blank)
    :params --fig-title: title of the figure
    :params --xlabel: label of the x axis
    :params --ylabel: label of the y axis
    :params --sharey: share y axis across subplots
    :params --figsize: size of figures
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--filename', type=str)
    parser.add_argument('-X','--timecol', type=str, default = 'date')
    parser.add_argument('-y','--ycol', type=str, default = 'value')
    parser.add_argument('-n','--namecol', type=str, default = 'name')
    parser.add_argument('-b','--breakpoint', type=float, default = None)
    parser.add_argument('-k','--breakpoints', type=list, default = None)
    parser.add_argument('-m','--margin', type=int, default = 5)
    parser.add_argument('-o','--output', type=str, default = 'output.xlsx')
    parser.add_argument('-p','--path', type=str, default = 'figs')
    parser.add_argument('-s','--sep', type=str, default = ',')
    parser.add_argument('-a','--alpha', type=float, default = 0.01)
    parser.add_argument('--no-figures', type=bool, default = False)
    parser.add_argument('--no-table', type=bool, default = False)
    parser.add_argument('--nrows', type=int, default = None)
    parser.add_argument('--ncols', type=int, default = 3)
    parser.add_argument('--fig-title', type=str, default = '')
    parser.add_argument('--fig-format', type=str, default = 'pdf')
    parser.add_argument('--xlabel', type=str, default = 'X')
    parser.add_argument('--ylabel', type=str, default = 'y')
    parser.add_argument('--sharey', type=bool, default = True)
    parser.add_argument('--figsize',type = list, default = (16,8))
    args = parser.parse_args()
    if args.filename is None:
        print("No data given. Please pass filename as argument --filename 'data.csv'")
        return None
    C = ChewData(filename = args.filename,
                namecol = args.namecol,
                ycol = args.ycol,
                timecol = args.timecol,
                sep = args.sep,
                margin = args.margin,
                alpha = args.alpha,
                initial_breakpoint = args.breakpoint,
                breakpoints = args.breakpoints)                                                                  
    C.run()
    if args.no_table is False:
        C.save_to_file(filename = args.output, sep = args.sep)
    if args.no_figures is False:
        C.plot(f'output.{args.fig_format}',
               nrows = args.nrows,
               ncols = args.ncols,
               sharey = args.sharey,
               figsize = args.figsize
               )
        C.plot_individually(savingpath = args.path, format = args.fig_format)


if __name__ == "__main__":

    main()