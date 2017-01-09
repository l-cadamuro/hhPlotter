import ROOT
import ConfigReader as cfgr
import fnmatch
import math
# import SampleHist

class UserHistoError:
    """ parses a cfg files and reads which systematics must be applied.
    Then uses an input histogram collection to compute the bkg envelope error.
    NOTE that this is for some quick plotting and is done under some approximations,
    e.g. correlations are neglected and eveything is summed in quadrature.
    Also relies on GetBinError() for MC stat error"""

    def __init__(self, cfgSyst):
        self.cfgSystRdr = cfgr.ConfigReader(cfgSyst)
        self.histos = None
        self.doMCStatErr = True

    def matchesAny(self, name, matchList):
        match = False
        for elem in matchList:
            if fnmatch.fnmatch(name, elem):
                match = True
                break
        return match

    def getErrorEnvelope(self):
        try: self.herror
        except AttributeError:
            self.makeErrorEnvelope()
        return self.herror

    def makeErrorEnvelope(self):
        if not self.histos:
            print "** Error: UserHistoError : getErrorEnvelope : histograms were not set, cannot compute error envelope"
            raise ValueError

        if len(self.histos) == 0:
            print "** Error: UserHistoError : getErrorEnvelope : histo dictionary is empty, cannot do errors"
            raise ValueError

        self.herror = self.histos.values()[0].Clone('herrorUser')
        # if (isinstance(self.histos.values()[0], ROOT.TH1)):
        #     self.herror = self.histos.values()[0].Clone('herrorUser')
        # elif (isinstance(self.histos.values()[0], SampleHist.SampleHist)):
        #     self.herror = self.histos.values()[0].evtHist.Clone('herrorUser')
        # else:
        #     print "** Error: don't know how to handle the type of histos: " , type(self.histos.values()[0])
        #     raise ValueError
        #     # self.hsum   = self.histos.values()[0].Clone('hsumUser')

        for ibin in range(1, self.herror.GetNbinsX()+1):
            self.herror.SetBinContent(ibin, 0.0)

        for bkg in self.histos:
            self.herror.Add(self.histos[bkg])

        for ibin in range(1, self.herror.GetNbinsX()+1):
            self.herror.SetBinError(ibin, 0.0)

        ## loop over the various syst sources
        if not 'list' in self.cfgSystRdr.config:
            print "** Error: UserHistoError : getErrorEnvelope : input cfg has no [list] section, cannot find systs"
            raise ValueError
        
        # print self.cfgSystRdr.config['list']
        systList = self.cfgSystRdr.config['list'].keys()
        # print systList

        for ibin in range(1, self.herror.GetNbinsX()+1):
            for syst in systList:
                err = 0
                descr = self.cfgSystRdr.readListOption('list::'+syst)
                systMag = float(descr[0])
                for bkg in self.histos:
                    if self.matchesAny(bkg, descr[1:]): ## i.e., if the current syst affects bkg
                        err += (systMag*self.histos[bkg].GetBinContent(ibin))
                        # if ibin == 1: print "bkg : " , bkg , "is affected by syst: " , syst
                cerr = self.herror.GetBinError(ibin)
                self.herror.SetBinError(ibin, math.sqrt(cerr*cerr + err*err))

        # now MC stat error using GetBinError
        if self.doMCStatErr:
            for ibin in range(1, self.herror.GetNbinsX()+1):
                for bkg in self.histos:
                   cerr = self.herror.GetBinError(ibin)
                   err  = self.histos[bkg].GetBinError(ibin)
                   self.herror.SetBinError(ibin, math.sqrt(cerr*cerr + err*err)) ## FIXME: should I put the 5% thr. error as done in the cards?

