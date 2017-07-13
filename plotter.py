### this script takes cmd line options, opens a config,
### uses the to create and instruct the plotting class,
### and finally displays/saves the plot

import argparse
import modules.ConfigReader as cfgr
import modules.ToolsNew as Tools
import modules.SampleHist as sh
import modules.UserHistoError as uhe
import ROOT
import collections
import fnmatch

def makeChanName(bcateg, taucateg):
    """ mini helper to create a nice string from chans name for plots"""
    chname = 'XX XX'

    if 'bb' in bcateg:
        # chname = 'bb'
        chname = '2b'
    elif 'bj' in bcateg:
        # chname = 'bj'
        chname = '1b1j'
    elif 'jj' in bcateg:
        # chname = 'jj'
        chname = '0b2j'

    ## b part    
    if 'bst' in bcateg or 'boosted' in bcateg:
        chname = 'boost. ' + chname
        # chname = 'boosted' ## as in the paper notation
    # elif 'res' in bcateg or 'resolved' in bcateg:
    else:
        # chname = 'resolved ' + chname
        chname = 'res. ' + chname
    # space
    chname += ' '

    # tau part
    if taucateg == 'MuTau' or taucateg == 'mutau':
        chname += '#tau_{#mu}#tau_{h}'
    elif taucateg == 'ETau' or taucateg == 'etau':
        chname += '#tau_{e}#tau_{h}'
    elif taucateg == 'TauTau' or taucateg == 'tautau':
        chname += '#tau_{h}#tau_{h}'
    elif taucateg == 'MuMu' or taucateg == 'mumu':
        chname += '#mu#mu'

    if 'Ltag' in bcateg:
        chname += ' L WP'
    elif 'Mtag' in bcateg:
        chname += ' M WP'

    return chname

def parsePostiftFile(fname, chan):
    pfyieldfile = open(fname)
    scales = {}
    errors = {}
    for line in pfyieldfile:
        tokens = line.split()
        if tokens[0] != ('ch'+str(chan)):
            continue
        procname = tokens[1]
        yprefit  = float(tokens[2])
        ypostfit = float(tokens[8])
        scale = ypostfit/yprefit if yprefit > 0 else 0
        scales[procname] = scale

        errpostfit = float(tokens[10])
        err = errpostfit/ypostfit if ypostfit > 0 else 0
        errors[procname] = err

    return (scales, errors)

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
parser.add_argument('--SRtype', dest='SRtype',   help='SR type: nonres, resLM, resHM', default=None)
parser.add_argument('--siglegextratext', dest='siglegextratext', help='additional optional text to be plotted in legend after signal block', default=None)
parser.add_argument('--channame', dest='channame', help='explicit chan name (overrides automatic creation)', default=None)

#bool opts
parser.add_argument('--log',     dest='log', help='use log scale',  action='store_true', default=False)
# parser.add_argument('--postfit', dest='postfit', help = 'scale to postfit values', action='store_true', default=False)
parser.add_argument('--no-data', dest='dodata', help='disable plotting data',  action='store_false', default=True)
parser.add_argument('--no-sig',  dest='dosig',  help='disable plotting signal',  action='store_false', default=True)
parser.add_argument('--no-legend',   dest='legend',   help = 'disable drawing legend',       action='store_false', default=True)
parser.add_argument('--no-binwidth', dest='binwidth', help = 'disable scaling by bin width', action='store_false', default=True)
parser.add_argument('--ratio',    dest='ratio', help = 'do ratio plot at the botton', action='store_true', default=False)
parser.add_argument('--sbplot',    dest='sbplot', help = 'do s/b plot at the botton', action='store_true', default=False)
parser.add_argument('--no-print', dest='printplot', help = 'no pdf output', action='store_false', default=True)
parser.add_argument('--root',     dest='root', help = 'print root canvas', action='store_true', default=False)
parser.add_argument('--quit',     dest='quit', help = 'quit at the end of the script, no interactive window', action='store_true', default=False)
parser.add_argument('--no-sr-namecompl',  dest='srnamecompl', help = 'complete the sel name with string SR if not specified by the user', action='store_false', default=True)
parser.add_argument('--tab',      dest='tab', help = 'print table with yields', action='store_true', default=False)
parser.add_argument('--postfit',  dest='postfit', help = 'draw postfit plots', action='store_true', default=False)


# par list opt
parser.add_argument('--blind-range',   dest='blindrange', type=float, nargs=2, help='start and end of blinding range', default=None)
# parser.add_argument('--arrow-xy',      dest='arrowxy', nargs=2, help='x and y (max) of the arrow of BDT WP', default=None)
parser.add_argument('--leg-coords',    dest='legcoords', type=float, nargs=4, help='x and y coordinates of the legend', default=None)

#float opt
parser.add_argument('--lxmin', dest='lxmin', type=float, help='legend min x position in pad fraction', default=None)
parser.add_argument('--lymin', dest='lymin', type=float, help='legend min y position in pad fraction', default=None)
parser.add_argument('--ymin', dest='ymin', type=float, help='min y range of plots', default=None)
parser.add_argument('--ymax', dest='ymax', type=float, help='max y range of plots', default=None)
parser.add_argument('--xmax', dest='xmax', type=float, help='max x range of plots', default=None)
parser.add_argument('--xmin', dest='xmin', type=float, help='min x range of plots', default=None)
parser.add_argument('--sigscale', dest='sigscale', type=float, help='scale to apply to all signals', default=None)

args = parser.parse_args()

if args.quit : ROOT.gROOT.SetBatch(True)

# if args.ratio: args.sbplot = False
# if not args.dosig : args.sbplot = False 


###########################################
#############   read configs   ############
###########################################

cfgName        = Tools.findInFolder  (args.dir+"/", 'mainCfg*.cfg')
# outplotterName = findInFolder  (args.dir+"/", 'outPlotter3.root')
outplotterName = Tools.findInFolder  (args.dir+"/", 'analyzedOutPlotter.root')

cfg = cfgr.ConfigReader (args.dir + "/" + cfgName)
dataList = cfg.readListOption("general::data")
# dataList = ['data_obs'] ## data are merged by hand into a single collection
sigList  = cfg.readListOption("general::signals")
bkgList       = cfg.readListOption("general::backgrounds")

# the background that were merged together - either at plotting level or at postprocessings
replacements = {}
secname = 'pp_merge'
if cfg.hasSection(secname) and cfg.config[secname]:
    for name in cfg.config[secname]:
        replacements[name] = cfg.readListOption(secname+'::'+name)
secname = 'merge'
if cfg.hasSection(secname) and cfg.config[secname]:
    for name in cfg.config[secname]:
        replacements[name] = cfg.readListOption(secname+'::'+name)

for name in replacements:
    thelist = None
    if replacements[name][0] in dataList:
        thelist = dataList
    elif replacements[name][0] in bkgList:
        thelist = bkgList
    elif replacements[name][0] in sigList:
        thelist = sigList
    else:
        print "** WARNING: I cannot find the name", replacements[name][0], "to replace"
    
    for old in replacements[name]:
        thelist.remove(old)
    thelist.append(name)

if cfg.hasSection('pp_QCD') and args.srnamecompl:
    bkgList.append('QCD')
else:
    print "** Warning: No QCD section was found in mainCfg, was it computed?"

###########################################
#############  retrieve plots  ############
###########################################

rootFile = ROOT.TFile.Open (args.dir+"/"+outplotterName)
print '... opened file' , rootFile.GetName()
sel = args.sel
if not '_SR' in sel and args.srnamecompl: sel += '_SR'

hSigs    = Tools.retrieveHistos  (rootFile, sigList,  args.var, sel) #, "sig": tags are unused now
hBkgs    = Tools.retrieveHistos  (rootFile, bkgList,  args.var, sel) #, "bkg": tags are unused now
hDatas   = Tools.retrieveHistos  (rootFile, dataList, args.var, sel) #, "DATA": tags are unused now
# hQCD     = Tools.retrieveQCD     (rootFile, args.var, sel, dataList)

# this is just temporary for QCD plots
# print "\n\n\n OOOOOH SCALING QCD BY 0.715 \n\n\n"
# hBkgs['QCD'].Scale(0.715)
# print "\n\n\n OOOOOH SCALING QCD BY 0.4267 \n\n\n"
# hBkgs['QCD'].Scale(0.4267)
# print "\n\n\n OOOOOH SCALING QCD BY 0.8067 \n\n\n"
# hBkgs['QCD'].Scale(0.8067)

# # this is just temporary to show effect of DY fit
# print "\n\n\n OOOOOH SCALING DY BY their fit values \n\n\n"
# # scale_DY0b = 1.12724 +/- 0.00171806
# # scale_DY1b = 1.17333 +/- 0.0154703
# # scale_DY2b = 1.14607 +/- 0.0291336
# # scale_bkgs = 1.09684 +/- 0.0233283
# hBkgs['DY0b'].Scale(1.12724)
# hBkgs['DY1b'].Scale(1.17333)
# hBkgs['DY2b'].Scale(1.14607)

# ## temporaneo!!
# if 'boosted' in sel:
#     print "REBINNO A 1"
#     for h in hSigs:
#         hSigs[h].Rebin(hSigs[h].GetNbinsX())
#     for h in hBkgs:
#         hBkgs[h].Rebin(hBkgs[h].GetNbinsX())
#     for h in hDatas:
#         hDatas[h].Rebin(hDatas[h].GetNbinsX())


## FIXME: if using pre/postfit from mlfit, do here!
if args.postfit:
    
    print "** INFO: going to scale to postfit yields"

    # translates my channel into combined card notation
    # CHANNELS: 1:etau, 2:mutau, 3:tautau
    # CATEGS  : 1: 1b1j, 2:2b0j, 3:boosted
    # chtransl(channel, category)

    if args.SRtype == 'nonres':
        chtransl = {
           (1, 1) : 4,
           (1, 2) : 13,
           (1, 3) : 22,
           (2, 1) : 8,
           (2, 2) : 17,
           (2, 3) : 23,
           (3, 1) : 12,
           (3, 2) : 21,
           (3, 3) : 24,
        }
        pfyieldfilename = 'postfitYields/lmr70.txt'

    elif args.SRtype == 'resLM':
        chtransl = {
           (1, 1) : 4,
           (1, 2) : 13,
           (1, 3) : 22,
           (2, 1) : 8,
           (2, 2) : 17,
           (2, 3) : 23,
           (3, 1) : 12,
           (3, 2) : 21,
           (3, 3) : 24,
        }
        pfyieldfilename = 'postfitYields/lmr90.txt'

    elif args.SRtype == 'resHM':
        chtransl = {
           (1, 1) : 1,
           (1, 2) : 7,
           (1, 3) : 16,
           (2, 1) : 2,
           (2, 2) : 11,
           (2, 3) : 17,
           (3, 1) : 6,
           (3, 2) : 15,
           (3, 3) : 18,
        }
        pfyieldfilename = 'postfitYields/hmr90.txt'

    else:
        print "** ERROR: I can't assess signal region type and hence postfit yields"
        sys.exit()

    ############ scale the histograms of the bkg to their postfit, read from the file
    chnumber = -1
    if   args.channel == "ETau"   : chnumber = 1
    elif args.channel == "MuTau"  : chnumber = 2
    elif args.channel == "TauTau" : chnumber = 3

    categnumber = -1
    if   args.bcateg == "bj"    : categnumber = 1
    elif args.bcateg == "bb"    : categnumber = 2
    elif args.bcateg == "bstbb" : categnumber = 3

    if chnumber < 0 or categnumber < 0:
        print "** error: cannot understand your channel/category" , chnumber, categnumber, "hence can't scale for postfit"
        sys.exit()

    postfitscales, postfiterrors = parsePostiftFile(pfyieldfilename, chtransl[(chnumber, categnumber)])
    for bkg in hBkgs:
        if bkg in postfitscales:
            # print "** scale : " , bkg, postfitscales[bkg], ' ... ' , chtransl[(chnumber, categnumber)], chnumber, categnumber
            hBkgs[bkg].Scale(postfitscales[bkg])
        else:
            print " ** warning: no postfit scale for ", bkg

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
# hBkgsDict = {key: hBkgs[key].evtHist for key in hBkgs} ## because UserHisto want a dictionary of names:histograms
# hBkgsDict = {key: hBkgs[key].evtHist for key in hBkgs if key in TOPLOT} ## FIXME: add the restriction on histograms to plot only if necessary
# uh.histos = hBkgsDict
uh.histos = dict (hBkgs)
if args.postfit:
  uh.externalDict = dict(postfiterrors)
histoErr = uh.getErrorEnvelope()

#####################################
#####################################
# inv masses
########## Titles ##########
titles = {
    'TT'    : 't#bar{t}',
    'DY'    : 'Drell-Yan',
    'DY0b'  : 'Drell-Yan 0b',
    'DY1b'  : 'Drell-Yan 1b',
    'DY2b'  : 'Drell-Yan 2b',
    'VV'    : 'VV',
    # 'ZH'    : 'SM Higgs',
    'ZH'    : 'SM Higgs boson',
    'WJets' : 'W+jets',
    'QCD'   : 'QCD',
    'other' : 'Other bkg.',
    'HHSM'  : '100 #times k_{#lambda} = 1 (SM)',
    'lambdarew21' : '(k_{#lambda} = 1, SM) #times 100',
    # 'lambdarew21' : 'k_{#lambda} = 1',
    'lambdarew40' : '(k_{#lambda} = 20) #times 10',
    'lambdarew41' : '(k_{#lambda} = 21) #times 10',
    # 'HHSM'  : 'k_{#lambda} = 1 (SM)',
    'Radion270' : 'm_{S} = 270 GeV',
    'Radion300' : 'm_{S} = 300 GeV',
    'Radion600' : 'm_{S} = 600 GeV',
    'Radion650' : 'm_{S} = 650 GeV',
    'Radion750' : 'm_{S} = 750 GeV',
    'Radion800' : 'm_{S} = 800 GeV',
    'Radion900' : 'm_{S} = 900 GeV',
}

########## Signal scales ##########
## sigs produced with 1 pb of cross section

sigscales = {
    'HHSM'    : 100.*33.49*0.073/1000.,
    'lambdarew21' : 100.*33.49*0.073/1000.,
    'lambdarew40' : 10.*90.11*33.49*0.073/1000.,
    'lambdarew41' : 10.*90.11*33.49*0.073/1000.,
     # 'Radion*' : 0.073/1.,
    'Radion270' : 1.*0.073/1.,
    'Radion300' : 1.*0.073/1.,
    'Radion600' : 1.*0.073/1.,
    'Radion650' : 1.*0.073/1.,
    'Radion750' : 1.*0.073/1.,
    'Radion800' : 1.*0.073/1.,
    'Radion900' : 1.*0.073/1.,
}
#####################################
#####################################

# #####################################
# #####################################
# # BDT output
# ########## Titles ##########
# titles = {
#     'TT'    : 't#bar{t}',
#     'DY'    : 'Drell-Yan',
#     'DY0b'  : 'Drell-Yan 0b',
#     'DY1b'  : 'Drell-Yan 1b',
#     'DY2b'  : 'Drell-Yan 2b',
#     'VV'    : 'VV',
#     'WJets' : 'W+jets',
#     'QCD'   : 'QCD',
#     'other' : 'Other bkg.',
#     'HHSM'  : '1000 #times k_{#lambda} = 1 (SM)',
#     # 'HHSM'  : 'k_{#lambda} = 1 (SM)',
#     'Radion300' : 'm_{X} = 300 GeV',
#     'Radion650' : 'm_{X} = 650 GeV',
#     'Radion900' : 'm_{X} = 900 GeV',
# }

# ########## Signal scales ##########
# ## sigs produced with 1 pb of cross section

# sigscales = {
#     'HHSM'    : 1000.*33.49*0.073/1000.,
#     # 'Radion*' : 0.073/1.,
#     'Radion300' : 10.*0.073/1.,
#     'Radion650' : 10.*0.073/1.,
#     'Radion900' : 10.*0.073/1.,
# }
# #####################################
# #####################################


########## Colors ##########
fillcolors = {
    'TT'    : 8,
    'DY'    : 92,
    'DY0b'    : 92,
    'DY1b'    : 94,
    'DY2b'    : 96,
    'ZH'    : ROOT.TColor.GetColor('#64B6E4'),
    'VV'    : ROOT.kRed-7,
    'WJets' : ROOT.kGray,
    'QCD'   : 606,
    'other' : ROOT.kRed-7,
}

# fillcolors = {
#     'TT'    : ROOT.TColor.GetColor('#00AACC'), #B3E8CA
#     'DY'    : 92,
#     'VV'    : ROOT.kRed-7,
#     'WJets' : ROOT.kGray,
#     'QCD'   : 606,
#     'other' : ROOT.kRed-7,
# }

# fillcolors = {
#     'TT'    : ROOT.TColor.GetColor('#FF6A5A'),
#     'DY'    : ROOT.TColor.GetColor('#FFB350'),
#     # 'VV'    : ROOT.kRed-7,
#     # 'WJets' : ROOT.kGray,
#     'QCD'   : ROOT.TColor.GetColor('#83B8AA'),
#     'other' : ROOT.TColor.GetColor('#272D4D'),
# }

linecolors = {
    'TT'    : ROOT.kGreen+3,
    'DY'    : 94,
    'DY0b'    : 92,
    'DY1b'    : 94,
    'DY2b'    : 96,
    'ZH'    : ROOT.TColor.GetColor('#0C6AA1'),
    'VV'    : ROOT.kRed-6,
    'WJets' : ROOT.kGray,
    'QCD'   : 607,
    'other' : ROOT.kRed-6,
    'Radion270' : 926,
    'Radion300' : 1,
    'Radion600' : 634,
    'Radion650' : 634,
    'Radion750' : 926,
    'Radion800' : 926,
    'Radion900' : 926,
    'lambdarew21' : ROOT.kBlue,
    'lambdarew40' : ROOT.kBlack,
    'lambdarew41' : ROOT.kBlack,
}


linestyles = {
    'HHSM' : 7,
    'lambdarew21' : 7,
    'lambdarew40' : 1,
    'lambdarew41' : 1,
    'Radion270' : 1,
    'Radion300' : 1,
    'Radion650' : 1,
    'Radion750' : 1,
    'Radion800' : 1,
    'Radion900' : 1,
}

######### Things to plot ##################
# sigList = ["HHSM"]
bkgToPlot = collections.OrderedDict()

# bkgToPlot['other'] = ['WJets', 'TWtop', 'TWantitop', 'WWToLNuQQ', 'WZTo1L1Nu2Q', 'WZTo1L3Nu', 'WZTo2L2Q', 'ZZTo2L2Q']
# bkgToPlot['DY' ]   = ['DY0b', 'DY1b', 'DY2b']
# if 'QCD' in bkgList: bkgToPlot['QCD']   = ['QCD']
# bkgToPlot['TT' ]   = ['TT']

bkgToPlot['other'] = ['WJets' , 'TW' , 'WW' , 'WZ' , 'ZZ', 'EWKW', 'EWKZ2Jets_ZToLL', 'ZH']
bkgToPlot['TT' ]   = ['TT']
# bkgToPlot['QCD']   = ['QCD']
bkgToPlot['DY0b' ]   = ['DY0b']
bkgToPlot['DY1b' ]   = ['DY1b']
bkgToPlot['DY2b' ]   = ['DY2b']

#######################################
### uncoment this for paper plots
# ######  updated to summer16
# bkgToPlot['ZH']    = ['ZH']
# bkgToPlot['other'] = ['WJets' , 'TW' , 'WW' , 'WZ' , 'ZZ', 'EWKW', 'EWKZ2Jets_ZToLL']
# bkgToPlot['DY' ]   = ['DY0b', 'DY1b', 'DY2b']
# # bkgToPlot['DY0b' ]   = ['DY0b']
# # bkgToPlot['DY1b' ]   = ['DY1b']
# # bkgToPlot['DY2b' ]   = ['DY2b']
# if 'QCD' in bkgList: bkgToPlot['QCD']   = ['QCD']
# bkgToPlot['TT' ]   = ['TT']

#### for ee / mumu control plots
# # bkgToPlot['ZH']    = []
# bkgToPlot['other'] = ['WJets' , 'TW' , 'WW' , 'WZ' , 'ZZ', 'EWKW', 'EWKZ2Jets_ZToLL', 'ZH']
# bkgToPlot['DY' ]   = ['DY']
# # bkgToPlot['DY0b' ]   = ['DY0b']
# # bkgToPlot['DY1b' ]   = ['DY1b']
# # bkgToPlot['DY2b' ]   = ['DY2b']
# # if 'QCD' in bkgList: bkgToPlot['QCD']   = ['QCD']
# bkgToPlot['TT' ]   = ['TT']



######  updated to summer16 - for DY mumu
# bkgToPlot['other'] = ['WJets' , 'TW' , 'WW' , 'WZ' , 'ZZ', 'EWKW', 'EWKZ2Jets_ZToLL', 'ZH']
# bkgToPlot['TT' ]   = ['TT']
# # bkgToPlot['QCD' ]   = ['QCD']
# bkgToPlot['DY0b' ]   = ['DY0b']
# bkgToPlot['DY1b' ]   = ['DY1b']
# bkgToPlot['DY2b' ]   = ['DY2b']



# bkgToPlot['other'] = ['WJets' , 'TW' , 'WW' , 'WZ' , 'ZZ', 'EWKW', 'EWKZ2Jets_ZToLL', 'ZH']
# bkgToPlot['TT' ]   = ['TT']
# bkgToPlot['DY0b' ]   = ['DY0b']
# bkgToPlot['DY1b' ]   = ['DY1b']
# bkgToPlot['DY2b' ]   = ['DY2b']
# if 'QCD' in bkgList: bkgToPlot['QCD']   = ['QCD']


### to print an exhaustive table:
# bkgToPlot['TT' ]   = ['TT']
# if 'QCD' in bkgList: bkgToPlot['QCD']   = ['QCD']
# bkgToPlot['DY' ]   = ['DY0b', 'DY1b', 'DY2b']
# bkgToPlot['WJets'] = ['WJets']
# bkgToPlot['singleTop'] = ['TWtop', 'TWantitop']
# bkgToPlot['diboson'] = ['WWToLNuQQ', 'WZTo1L1Nu2Q', 'WZTo1L3Nu', 'WZTo2L2Q', 'ZZTo2L2Q']


## from binned tauH mass fit
# hBkgs['DY0b'].Scale(9.44841e-01)
# hBkgs['DY1b'].Scale(1.29404e+00)
# hBkgs['DY2b'].Scale(1.28542e+00)

## from fit to yields
# hBkgs['DY0b'].Scale(0.944)
# hBkgs['DY1b'].Scale(1.289)
# hBkgs['DY2b'].Scale(1.247)

###########################################
############  prepare plotter  ############
###########################################

shc = sh.SampleHistColl()
shc.stackErrorHist = histoErr
shc.logy       = args.log
shc.ratio      = args.ratio
shc.sbplot     = args.sbplot
shc.lumi       = float(cfg.readOption ("general::lumi"))/1000. # from pb to fb
shc.chan       = makeChanName(args.bcateg, args.channel) if not args.channame else args.channame
shc.title      = args.title
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
shc.linecolors = dict(linecolors)
shc.fillcolors = dict(fillcolors)
shc.linestyles = dict(linestyles)
shc.sigscale   = args.sigscale
# shc.legtextsize  = 23
shc.legtextsize  = 19
shc.chantextsize  = 23
shc.cmstextinframe = True
shc.ispreliminary = True
shc.ytitleoffset  = 1.3

### decide what to plot
## FIXME: could be done from a config? manual edit here!

# sigList = ["lambdarew21", "Radion300", "Radion600"]
# sigList = ["HHSM", "Radion300", "Radion650", "Radion900"]
# sigList = ["Radion300", "Radion650", "Radion800"]
# sigList = ["Radion300", "Radion600", "Radion900"]

# sigList = ["Radion300", "Radion600", "Radion900"]
# sigList = ["Radion270"]
# sigList = ["Radion300", "Radion600", "Radion900"]
# sigList = ["Radion600", "Radion900"]
# sigList = ["HHSM"]
sigList = ["lambdarew21"]

# "smart" selection of sigList
if args.SRtype == 'nonres':
    sigList = ["lambdarew21", "lambdarew40"]
elif args.SRtype == 'resLM':
    sigList = ["Radion270"]
elif args.SRtype == 'resHM':
    sigList = ["Radion750"]


for sig in sigList:
    if not sig in hSigs:
        print '** Warning: signal' , sig , ' not found in the input, removing from plotting list...'
sigList[:] = [x for x in sigList if x in hSigs]

# scale to expected sigscale before. NOTE: a second sigscale can be applied in the plotter
for h in hSigs:
    match = [key for key in sigscales if fnmatch.fnmatch(h, key)]
    if len(match) == 1:
        print " >> info: histo of sample", h, ('scaled by factor %.3g' % sigscales[match[0]])
        hSigs[h].Scale(sigscales[match[0]])
    shc.addHisto (hSigs[h], h, 'sig', (titles[h] if h in titles else hSigs[h].GetName()))

# for h in hBkgs:
for hname in bkgToPlot:
    for h in bkgToPlot[hname]:
        shc.addHisto (hBkgs[h], hname, 'bkg', (titles[hname] if hname in titles else hBkgs[h].GetName()))
for h in hDatas:
    shc.addHisto (hDatas[h], h, 'data', 'Data')
## mu, e, for pre-mass cut
# sigNameList = ["k_{#lambda} = 1 (SM) #times 5000"]
# sigScale = [5000.*(0.073/1.)*33.45/1000.] # tutto a 1 pb di rpoduzione hh (tolgo il BR in bbtautau)
shc.setListToPlot(bkgToPlot.keys(), 'bkg')
shc.setListToPlot(reversed(sigList), 'sig') # sigs instead are listed from top to bottom of the legend
shc.setListToPlot(dataList, 'data')

shc.makePlot()
shc.c1.cd()
shc.c1.Update()

if args.tab: shc.printTable(floatFormat='.6', printMCstat=True)

if not args.quit:
    raw_input()

if args.printplot:
    outname = '_'.join(['plot', args.var, args.sel, args.channel])
    if args.log: outname += ('_'+'log')
    if args.postfit: outname += '_postfit'
    outname += '.pdf'
    # print outname
    shc.c1.Print(outname, 'pdf')

if args.root:
    shc.c1.SaveAs(rootname)
