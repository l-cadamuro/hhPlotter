import ROOT
import SampleHist as sh
import UserHistoError as uhe
from array import *

## fake hists
f1 = ROOT.TF1 ('f1', 'TMath::Gaus(x, 50, 15)')
f2 = ROOT.TF1 ('f2', 'TMath::Gaus(x, 70, 20)')
f3 = ROOT.TF1 ('f3', 'TMath::Gaus(x, 30, 3)')
f4 = ROOT.TF1 ('f4', 'TMath::Gaus(x*x, 30, 3)')

# aa = [0, 1,2,3,4,5,10,20,50,100]
# runArray = array('d',aa)
# data = ROOT.TH1F ('data', 'data', len(aa)-1, runArray )
# bkg1 = ROOT.TH1F ('bkg1', 'bkg1', len(aa)-1, runArray )
# bkg2 = ROOT.TH1F ('bkg2', 'bkg2', len(aa)-1, runArray )
# signal = ROOT.TH1F ('signal', 'signal', len(aa)-1, runArray )

ROOT.TH1.SetDefaultSumw2(True)

data = ROOT.TH1F ('data', 'data', 50, 0, 100)
bkg1 = ROOT.TH1F ('bkg1', 'bkg1', 50, 0, 100)
bkg2 = ROOT.TH1F ('bkg2', 'bkg2', 50, 0, 100)
signal = ROOT.TH1F ('signal', 'signal', 50, 0, 100)

bkg1.FillRandom('f1', 10000)
bkg2.FillRandom('f2', 10000)
data.FillRandom('f1', 10000)
signal.FillRandom('f4', 500)

bkgSum = bkg1.Clone('sum')
bkgSum.Add(bkg2)

fillColors = {
    'Bkg1' : ROOT.kOrange ,
    'Bkg2' : ROOT.kCyan+3 ,
}

lineStyles = {
    'Signal' : 7 ,
}

#### user histo error
uh = uhe.UserHistoError('userSystCfgExample.cfg')
uh.histos = {
    'Bkg1' : bkg1,
    'Bkg2' : bkg2
}

shc = sh.SampleHistColl()
shc.setLogY(False)
shc.ratio    = True
shc.lumi     = 36.39
shc.title    = ';var1;Eventi ciao ciao'
shc.chan  = 'bb #tau_{h}#tau_{h}'
shc.addHisto (data, 'Data', 'data', 'data')
shc.addHisto (bkg1, 'Bkg1', 'bkg', 'bkg')
shc.addHisto (bkg2, 'Bkg2', 'bkg', 'bkg')
shc.addHisto (signal, 'Signal', 'sig', 'signal')
shc.setListToPlot(['Bkg2', 'Bkg1'], 'bkg')
shc.setListToPlot(['Signal'], 'sig')
shc.setListToPlot(['Data'], 'data')
shc.setDivideByBinWidth(False)
shc.setFillColors(fillColors)
shc.setLineStyles(lineStyles)
# shc.stackErrorHist = bkgSum
shc.stackErrorHist = uh.getErrorEnvelope()
shc.blindrange = [20, 30]
# shc.xmin = 20
# shc.xmax = 80

shc.makePlot()
shc.c1.cd()
shc.c1.Update()
raw_input()
shc.c1.Print("testmacro.pdf", "pdf")
shc.c1.Print("testmacro.png", "png")