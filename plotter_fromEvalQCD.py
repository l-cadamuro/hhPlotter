### this script takes cmd line options, opens a config,
### uses the to create and instruct the plotting class,
### and finally displays/saves the plot

import argparse
import ConfigReader as cfgr
import Tools
import SampleHist as sh
import UserHistoError as uhe
import ROOT

def makeChanName(bcateg, taucateg):
    """ mini helper to create a nice string from chans name for plots"""
    chname = 'XX XX'

    ## b part    
    if bcateg == 'bb':
        chname = 'bb'

    # space
    chname += ' '

    # tau part
    if taucateg == 'MuTau' or taucateg == 'mutau':
        chname += '#mu#tau_{h}'
    if taucateg == 'ETau' or taucateg == 'etau':
        chname += 'e#tau_{h}'
    if taucateg == 'TauTau' or taucateg == 'tautau':
        chname += '#tau_{h}#tau_{h}'

    return chname

######################################################################################
######################################################################################
######################################################################################

ROOT.TH1.AddDirectory(0)

###########################################
#############   parse options  ############
###########################################

parser = argparse.ArgumentParser(description='Command line parser of plotting options')
#string opts
parser.add_argument('--var', dest='var', help='variable name', default=None)
parser.add_argument('--sel', dest='sel', help='selection name', default=None)
parser.add_argument('--dir', dest='dir', help='analysis output folder name', default="./")
parser.add_argument('--title',   dest='title',   help='plot title', default=None)
parser.add_argument('--channel', dest='channel', help='channel = (MuTau, ETau, TauTau)', default=None)
parser.add_argument('--bcateg',  dest='bcateg',  help='b category = (resbb, resbj, bstbb)', default=None)
parser.add_argument('--siglegextratext', dest='siglegextratext', help='additional optional text to be plotted in legend after signal block', default=None)

#bool opts
parser.add_argument('--log',     dest='log', help='use log scale',  action='store_true', default=False)
# parser.add_argument('--postfit', dest='postfit', help = 'scale to postfit values', action='store_true', default=False)
parser.add_argument('--no-data', dest='dodata', help='disable plotting data',  action='store_false', default=True)
parser.add_argument('--no-sig',  dest='dosig',  help='disable plotting signal',  action='store_false', default=True)
parser.add_argument('--no-legend',   dest='legend',   help = 'disable drawing legend',       action='store_false', default=True)
parser.add_argument('--no-binwidth', dest='binwidth', help = 'disable scaling by bin width', action='store_false', default=True)
parser.add_argument('--ratio',    dest='ratio', help = 'do ratio plot at the botton', action='store_true', default=False)
# parser.add_argument('--sbplot',    dest='sbplot', help = 'do s/b plot at the botton', action='store_true', default=False)
parser.add_argument('--no-print', dest='printplot', help = 'no pdf output', action='store_false', default=True)
parser.add_argument('--root',     dest='root', help = 'print root canvas', action='store_true', default=False)
parser.add_argument('--quit',     dest='quit', help = 'quit at the end of the script, no interactive window', action='store_true', default=False)

# par list opt
parser.add_argument('--blind-range',   dest='blindrange', nargs=2, help='start and end of blinding range', default=None)
# parser.add_argument('--arrow-xy',      dest='arrowxy', nargs=2, help='x and y (max) of the arrow of BDT WP', default=None)
parser.add_argument('--leg-coords',    dest='legcoords', nargs=4, help='x and y coordinates of the legend', default=None)

#float opt
parser.add_argument('--lxmin', dest='lxmin', type=float, help='legend min x position in pad fraction', default=None)
parser.add_argument('--lymin', dest='lymin', type=float, help='legend min y position in pad fraction', default=None)
parser.add_argument('--ymin', dest='ymin', type=float, help='min y range of plots', default=None)
parser.add_argument('--ymax', dest='ymax', type=float, help='max y range of plots', default=None)
# parser.add_argument('--xmax', dest='xmax', type=float, help='max x range of plots', default=None)
# parser.add_argument('--xmin', dest='xmin', type=float, help='min x range of plots', default=None)
# parser.add_argument('--sigscale', dest='sigscale', type=float, help='scale to apply to all signals', default=1.0)

args = parser.parse_args()

if args.quit : ROOT.gROOT.SetBatch(True)
# if args.ratio: args.sbplot = False
# if not args.dosig : args.sbplot = False 


###########################################
#############   read configs   ############
###########################################

cfgName        = Tools.findInFolder  (args.dir+"/", '*.cfg')
# outplotterName = findInFolder  (args.dir+"/", 'outPlotter3.root')
outplotterName = Tools.findInFolder  (args.dir+"/", 'outPlotter.root')

cfg = cfgr.ConfigReader (args.dir + "/" + cfgName)
bkgList  = cfg.readListOption("general::backgrounds")
dataList = cfg.readListOption("general::data")
sigList  = cfg.readListOption("general::signals")

###########################################
#############  retrieve plots  ############
###########################################

rootFile = ROOT.TFile.Open (args.dir+"/"+outplotterName)
hSigs    = Tools.retrieveHistos  (rootFile, sigList,  args.var, args.sel, "sig")
hBkgs    = Tools.retrieveHistos  (rootFile, bkgList,  args.var, args.sel, "bkg")
hDatas   = Tools.retrieveHistos  (rootFile, dataList, args.var, args.sel, "DATA")
hQCD     = Tools.retrieveQCD     (rootFile, args.var, args.sel, dataList)

###########################################
########  retrieve/compute errors  ########
###########################################

if args.channel == 'MuTau':
    uh = uhe.UserHistoError('userSystCfgExample.cfg')
elif args.channel == 'MuTau':
    uh = uhe.UserHistoError('userSystCfgExample.cfg')
elif args.channel == 'MuTau':
    uh = uhe.UserHistoError('userSystCfgExample.cfg')
else:
    print 'Cannot state channel type ' , args.channel, ' --> no way to determine errors, using dummy cfg'
    uh = uhe.UserHistoError('userSystCfgExample.cfg')
uh.histos = dict(hBkgs)

## FIXME: if using pre/postfit from mlfit, do here!

histoErr = uh.getErrorEnvelope()

###########################################
############  prepare plotter  ############
###########################################

shc = sh.SampleHistColl()
shc.stackErrorHist = histoErr
shc.logy       = args.log
shc.ratio      = args.ratio
shc.lumi       = float(cfg.readOption ("general::lumi"))/1000. # from pb to fb
shc.title      = args.title
shc.chan       = makeChanName(args.bcateg, args.channel)
shc.divByBW    = args.binwidth
shc.plotData   = args.dodata
shc.plotSig    = args.dosig
shc.plotLegend = args.legend
shc.ymin       = args.ymin
shc.ymax       = args.ymax
shc.xmin       = args.xmin
shc.xmax       = args.xmax
shc.legxmin    = args.lxmin
shc.legymin    = args.lymin
shc.legcoords  = None if not args.legcoords else list([args.legcoords[0], args.legcoords[1], args.legcoords[2], args.legcoords[3]])
shc.siglegextratext = args.siglegextratext
shc.blindrange = None if not args.blindrange else list([args.blindrange[0], args.blindrange[1]])

### decide what to plot
## FIXME: could be done from a config? manual edit here!

sigList = ["HHSM"]

for sig in sigList:
    if not sig in hSigs:
        print '** Warning: signal' , sig , ' not found in the input, removing from plotting list...'
sigList[:] = [x for x in sigList if x in hSigs]

## mu, e, for pre-mass cut
# sigNameList = ["k_{#lambda} = 1 (SM) #times 5000"]
# sigScale = [5000.*(0.073/1.)*33.45/1000.] # tutto a 1 pb di rpoduzione hh (tolgo il BR in bbtautau)

