slepc4py.SLEPc.NEP
==================

.. autoclass:: slepc4py.SLEPc.NEP
   :show-inheritance:

   
   .. rubric:: Enumerations
   .. autosummary::
      :toctree:
   
      ~slepc4py.SLEPc.NEP.CISSExtraction
      ~slepc4py.SLEPc.NEP.Conv
      ~slepc4py.SLEPc.NEP.ConvergedReason
      ~slepc4py.SLEPc.NEP.ErrorType
      ~slepc4py.SLEPc.NEP.ProblemType
      ~slepc4py.SLEPc.NEP.Refine
      ~slepc4py.SLEPc.NEP.RefineScheme
      ~slepc4py.SLEPc.NEP.Stop
      ~slepc4py.SLEPc.NEP.Type
      ~slepc4py.SLEPc.NEP.Which

   
   .. rubric:: Methods Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.NEP.appendOptionsPrefix
      ~slepc4py.SLEPc.NEP.applyResolvent
      ~slepc4py.SLEPc.NEP.cancelMonitor
      ~slepc4py.SLEPc.NEP.computeError
      ~slepc4py.SLEPc.NEP.create
      ~slepc4py.SLEPc.NEP.destroy
      ~slepc4py.SLEPc.NEP.errorView
      ~slepc4py.SLEPc.NEP.getBV
      ~slepc4py.SLEPc.NEP.getCISSExtraction
      ~slepc4py.SLEPc.NEP.getCISSKSPs
      ~slepc4py.SLEPc.NEP.getCISSRefinement
      ~slepc4py.SLEPc.NEP.getCISSSizes
      ~slepc4py.SLEPc.NEP.getCISSThreshold
      ~slepc4py.SLEPc.NEP.getConverged
      ~slepc4py.SLEPc.NEP.getConvergedReason
      ~slepc4py.SLEPc.NEP.getConvergenceTest
      ~slepc4py.SLEPc.NEP.getDS
      ~slepc4py.SLEPc.NEP.getDimensions
      ~slepc4py.SLEPc.NEP.getEigenpair
      ~slepc4py.SLEPc.NEP.getEigenvalueComparison
      ~slepc4py.SLEPc.NEP.getErrorEstimate
      ~slepc4py.SLEPc.NEP.getFunction
      ~slepc4py.SLEPc.NEP.getInterpolInterpolation
      ~slepc4py.SLEPc.NEP.getInterpolPEP
      ~slepc4py.SLEPc.NEP.getIterationNumber
      ~slepc4py.SLEPc.NEP.getJacobian
      ~slepc4py.SLEPc.NEP.getLeftEigenvector
      ~slepc4py.SLEPc.NEP.getMonitor
      ~slepc4py.SLEPc.NEP.getNArnoldiKSP
      ~slepc4py.SLEPc.NEP.getNArnoldiLagPreconditioner
      ~slepc4py.SLEPc.NEP.getNLEIGSEPS
      ~slepc4py.SLEPc.NEP.getNLEIGSFullBasis
      ~slepc4py.SLEPc.NEP.getNLEIGSInterpolation
      ~slepc4py.SLEPc.NEP.getNLEIGSKSPs
      ~slepc4py.SLEPc.NEP.getNLEIGSLocking
      ~slepc4py.SLEPc.NEP.getNLEIGSRKShifts
      ~slepc4py.SLEPc.NEP.getNLEIGSRestart
      ~slepc4py.SLEPc.NEP.getOptionsPrefix
      ~slepc4py.SLEPc.NEP.getProblemType
      ~slepc4py.SLEPc.NEP.getRG
      ~slepc4py.SLEPc.NEP.getRIIConstCorrectionTol
      ~slepc4py.SLEPc.NEP.getRIIDeflationThreshold
      ~slepc4py.SLEPc.NEP.getRIIHermitian
      ~slepc4py.SLEPc.NEP.getRIIKSP
      ~slepc4py.SLEPc.NEP.getRIILagPreconditioner
      ~slepc4py.SLEPc.NEP.getRIIMaximumIterations
      ~slepc4py.SLEPc.NEP.getRefine
      ~slepc4py.SLEPc.NEP.getRefineKSP
      ~slepc4py.SLEPc.NEP.getSLPDeflationThreshold
      ~slepc4py.SLEPc.NEP.getSLPEPS
      ~slepc4py.SLEPc.NEP.getSLPEPSLeft
      ~slepc4py.SLEPc.NEP.getSLPKSP
      ~slepc4py.SLEPc.NEP.getSplitOperator
      ~slepc4py.SLEPc.NEP.getSplitPreconditioner
      ~slepc4py.SLEPc.NEP.getStoppingTest
      ~slepc4py.SLEPc.NEP.getTarget
      ~slepc4py.SLEPc.NEP.getTolerances
      ~slepc4py.SLEPc.NEP.getTrackAll
      ~slepc4py.SLEPc.NEP.getTwoSided
      ~slepc4py.SLEPc.NEP.getType
      ~slepc4py.SLEPc.NEP.getWhichEigenpairs
      ~slepc4py.SLEPc.NEP.reset
      ~slepc4py.SLEPc.NEP.setBV
      ~slepc4py.SLEPc.NEP.setCISSExtraction
      ~slepc4py.SLEPc.NEP.setCISSRefinement
      ~slepc4py.SLEPc.NEP.setCISSSizes
      ~slepc4py.SLEPc.NEP.setCISSThreshold
      ~slepc4py.SLEPc.NEP.setConvergenceTest
      ~slepc4py.SLEPc.NEP.setDS
      ~slepc4py.SLEPc.NEP.setDimensions
      ~slepc4py.SLEPc.NEP.setEigenvalueComparison
      ~slepc4py.SLEPc.NEP.setFromOptions
      ~slepc4py.SLEPc.NEP.setFunction
      ~slepc4py.SLEPc.NEP.setInitialSpace
      ~slepc4py.SLEPc.NEP.setInterpolInterpolation
      ~slepc4py.SLEPc.NEP.setInterpolPEP
      ~slepc4py.SLEPc.NEP.setJacobian
      ~slepc4py.SLEPc.NEP.setMonitor
      ~slepc4py.SLEPc.NEP.setNArnoldiKSP
      ~slepc4py.SLEPc.NEP.setNArnoldiLagPreconditioner
      ~slepc4py.SLEPc.NEP.setNLEIGSEPS
      ~slepc4py.SLEPc.NEP.setNLEIGSFullBasis
      ~slepc4py.SLEPc.NEP.setNLEIGSInterpolation
      ~slepc4py.SLEPc.NEP.setNLEIGSLocking
      ~slepc4py.SLEPc.NEP.setNLEIGSRKShifts
      ~slepc4py.SLEPc.NEP.setNLEIGSRestart
      ~slepc4py.SLEPc.NEP.setOptionsPrefix
      ~slepc4py.SLEPc.NEP.setProblemType
      ~slepc4py.SLEPc.NEP.setRG
      ~slepc4py.SLEPc.NEP.setRIIConstCorrectionTol
      ~slepc4py.SLEPc.NEP.setRIIDeflationThreshold
      ~slepc4py.SLEPc.NEP.setRIIHermitian
      ~slepc4py.SLEPc.NEP.setRIIKSP
      ~slepc4py.SLEPc.NEP.setRIILagPreconditioner
      ~slepc4py.SLEPc.NEP.setRIIMaximumIterations
      ~slepc4py.SLEPc.NEP.setRefine
      ~slepc4py.SLEPc.NEP.setSLPDeflationThreshold
      ~slepc4py.SLEPc.NEP.setSLPEPS
      ~slepc4py.SLEPc.NEP.setSLPEPSLeft
      ~slepc4py.SLEPc.NEP.setSLPKSP
      ~slepc4py.SLEPc.NEP.setSplitOperator
      ~slepc4py.SLEPc.NEP.setSplitPreconditioner
      ~slepc4py.SLEPc.NEP.setStoppingTest
      ~slepc4py.SLEPc.NEP.setTarget
      ~slepc4py.SLEPc.NEP.setTolerances
      ~slepc4py.SLEPc.NEP.setTrackAll
      ~slepc4py.SLEPc.NEP.setTwoSided
      ~slepc4py.SLEPc.NEP.setType
      ~slepc4py.SLEPc.NEP.setUp
      ~slepc4py.SLEPc.NEP.setWhichEigenpairs
      ~slepc4py.SLEPc.NEP.solve
      ~slepc4py.SLEPc.NEP.valuesView
      ~slepc4py.SLEPc.NEP.vectorsView
      ~slepc4py.SLEPc.NEP.view

   
   .. rubric:: Attributes Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.NEP.bv
      ~slepc4py.SLEPc.NEP.ds
      ~slepc4py.SLEPc.NEP.max_it
      ~slepc4py.SLEPc.NEP.problem_type
      ~slepc4py.SLEPc.NEP.rg
      ~slepc4py.SLEPc.NEP.target
      ~slepc4py.SLEPc.NEP.tol
      ~slepc4py.SLEPc.NEP.track_all
      ~slepc4py.SLEPc.NEP.which

   
   .. rubric:: Methods Documentation
   
   .. automethod:: appendOptionsPrefix
   .. automethod:: applyResolvent
   .. automethod:: cancelMonitor
   .. automethod:: computeError
   .. automethod:: create
   .. automethod:: destroy
   .. automethod:: errorView
   .. automethod:: getBV
   .. automethod:: getCISSExtraction
   .. automethod:: getCISSKSPs
   .. automethod:: getCISSRefinement
   .. automethod:: getCISSSizes
   .. automethod:: getCISSThreshold
   .. automethod:: getConverged
   .. automethod:: getConvergedReason
   .. automethod:: getConvergenceTest
   .. automethod:: getDS
   .. automethod:: getDimensions
   .. automethod:: getEigenpair
   .. automethod:: getEigenvalueComparison
   .. automethod:: getErrorEstimate
   .. automethod:: getFunction
   .. automethod:: getInterpolInterpolation
   .. automethod:: getInterpolPEP
   .. automethod:: getIterationNumber
   .. automethod:: getJacobian
   .. automethod:: getLeftEigenvector
   .. automethod:: getMonitor
   .. automethod:: getNArnoldiKSP
   .. automethod:: getNArnoldiLagPreconditioner
   .. automethod:: getNLEIGSEPS
   .. automethod:: getNLEIGSFullBasis
   .. automethod:: getNLEIGSInterpolation
   .. automethod:: getNLEIGSKSPs
   .. automethod:: getNLEIGSLocking
   .. automethod:: getNLEIGSRKShifts
   .. automethod:: getNLEIGSRestart
   .. automethod:: getOptionsPrefix
   .. automethod:: getProblemType
   .. automethod:: getRG
   .. automethod:: getRIIConstCorrectionTol
   .. automethod:: getRIIDeflationThreshold
   .. automethod:: getRIIHermitian
   .. automethod:: getRIIKSP
   .. automethod:: getRIILagPreconditioner
   .. automethod:: getRIIMaximumIterations
   .. automethod:: getRefine
   .. automethod:: getRefineKSP
   .. automethod:: getSLPDeflationThreshold
   .. automethod:: getSLPEPS
   .. automethod:: getSLPEPSLeft
   .. automethod:: getSLPKSP
   .. automethod:: getSplitOperator
   .. automethod:: getSplitPreconditioner
   .. automethod:: getStoppingTest
   .. automethod:: getTarget
   .. automethod:: getTolerances
   .. automethod:: getTrackAll
   .. automethod:: getTwoSided
   .. automethod:: getType
   .. automethod:: getWhichEigenpairs
   .. automethod:: reset
   .. automethod:: setBV
   .. automethod:: setCISSExtraction
   .. automethod:: setCISSRefinement
   .. automethod:: setCISSSizes
   .. automethod:: setCISSThreshold
   .. automethod:: setConvergenceTest
   .. automethod:: setDS
   .. automethod:: setDimensions
   .. automethod:: setEigenvalueComparison
   .. automethod:: setFromOptions
   .. automethod:: setFunction
   .. automethod:: setInitialSpace
   .. automethod:: setInterpolInterpolation
   .. automethod:: setInterpolPEP
   .. automethod:: setJacobian
   .. automethod:: setMonitor
   .. automethod:: setNArnoldiKSP
   .. automethod:: setNArnoldiLagPreconditioner
   .. automethod:: setNLEIGSEPS
   .. automethod:: setNLEIGSFullBasis
   .. automethod:: setNLEIGSInterpolation
   .. automethod:: setNLEIGSLocking
   .. automethod:: setNLEIGSRKShifts
   .. automethod:: setNLEIGSRestart
   .. automethod:: setOptionsPrefix
   .. automethod:: setProblemType
   .. automethod:: setRG
   .. automethod:: setRIIConstCorrectionTol
   .. automethod:: setRIIDeflationThreshold
   .. automethod:: setRIIHermitian
   .. automethod:: setRIIKSP
   .. automethod:: setRIILagPreconditioner
   .. automethod:: setRIIMaximumIterations
   .. automethod:: setRefine
   .. automethod:: setSLPDeflationThreshold
   .. automethod:: setSLPEPS
   .. automethod:: setSLPEPSLeft
   .. automethod:: setSLPKSP
   .. automethod:: setSplitOperator
   .. automethod:: setSplitPreconditioner
   .. automethod:: setStoppingTest
   .. automethod:: setTarget
   .. automethod:: setTolerances
   .. automethod:: setTrackAll
   .. automethod:: setTwoSided
   .. automethod:: setType
   .. automethod:: setUp
   .. automethod:: setWhichEigenpairs
   .. automethod:: solve
   .. automethod:: valuesView
   .. automethod:: vectorsView
   .. automethod:: view

   
   .. rubric:: Attributes Documentation
   
   .. autoattribute:: bv
   .. autoattribute:: ds
   .. autoattribute:: max_it
   .. autoattribute:: problem_type
   .. autoattribute:: rg
   .. autoattribute:: target
   .. autoattribute:: tol
   .. autoattribute:: track_all
   .. autoattribute:: which
