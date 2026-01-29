slepc4py.SLEPc.PEP
==================

.. autoclass:: slepc4py.SLEPc.PEP
   :show-inheritance:

   
   .. rubric:: Enumerations
   .. autosummary::
      :toctree:
   
      ~slepc4py.SLEPc.PEP.Basis
      ~slepc4py.SLEPc.PEP.CISSExtraction
      ~slepc4py.SLEPc.PEP.Conv
      ~slepc4py.SLEPc.PEP.ConvergedReason
      ~slepc4py.SLEPc.PEP.ErrorType
      ~slepc4py.SLEPc.PEP.Extract
      ~slepc4py.SLEPc.PEP.JDProjection
      ~slepc4py.SLEPc.PEP.ProblemType
      ~slepc4py.SLEPc.PEP.Refine
      ~slepc4py.SLEPc.PEP.RefineScheme
      ~slepc4py.SLEPc.PEP.Scale
      ~slepc4py.SLEPc.PEP.Stop
      ~slepc4py.SLEPc.PEP.Type
      ~slepc4py.SLEPc.PEP.Which

   
   .. rubric:: Methods Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.PEP.appendOptionsPrefix
      ~slepc4py.SLEPc.PEP.cancelMonitor
      ~slepc4py.SLEPc.PEP.computeError
      ~slepc4py.SLEPc.PEP.create
      ~slepc4py.SLEPc.PEP.destroy
      ~slepc4py.SLEPc.PEP.errorView
      ~slepc4py.SLEPc.PEP.getBV
      ~slepc4py.SLEPc.PEP.getBasis
      ~slepc4py.SLEPc.PEP.getCISSExtraction
      ~slepc4py.SLEPc.PEP.getCISSKSPs
      ~slepc4py.SLEPc.PEP.getCISSRefinement
      ~slepc4py.SLEPc.PEP.getCISSSizes
      ~slepc4py.SLEPc.PEP.getCISSThreshold
      ~slepc4py.SLEPc.PEP.getConverged
      ~slepc4py.SLEPc.PEP.getConvergedReason
      ~slepc4py.SLEPc.PEP.getConvergenceTest
      ~slepc4py.SLEPc.PEP.getDS
      ~slepc4py.SLEPc.PEP.getDimensions
      ~slepc4py.SLEPc.PEP.getEigenpair
      ~slepc4py.SLEPc.PEP.getEigenvalueComparison
      ~slepc4py.SLEPc.PEP.getErrorEstimate
      ~slepc4py.SLEPc.PEP.getExtract
      ~slepc4py.SLEPc.PEP.getInterval
      ~slepc4py.SLEPc.PEP.getIterationNumber
      ~slepc4py.SLEPc.PEP.getJDFix
      ~slepc4py.SLEPc.PEP.getJDMinimalityIndex
      ~slepc4py.SLEPc.PEP.getJDProjection
      ~slepc4py.SLEPc.PEP.getJDRestart
      ~slepc4py.SLEPc.PEP.getJDReusePreconditioner
      ~slepc4py.SLEPc.PEP.getLinearEPS
      ~slepc4py.SLEPc.PEP.getLinearExplicitMatrix
      ~slepc4py.SLEPc.PEP.getLinearLinearization
      ~slepc4py.SLEPc.PEP.getMonitor
      ~slepc4py.SLEPc.PEP.getOperators
      ~slepc4py.SLEPc.PEP.getOptionsPrefix
      ~slepc4py.SLEPc.PEP.getProblemType
      ~slepc4py.SLEPc.PEP.getQArnoldiLocking
      ~slepc4py.SLEPc.PEP.getQArnoldiRestart
      ~slepc4py.SLEPc.PEP.getRG
      ~slepc4py.SLEPc.PEP.getRefine
      ~slepc4py.SLEPc.PEP.getRefineKSP
      ~slepc4py.SLEPc.PEP.getST
      ~slepc4py.SLEPc.PEP.getSTOARCheckEigenvalueType
      ~slepc4py.SLEPc.PEP.getSTOARDetectZeros
      ~slepc4py.SLEPc.PEP.getSTOARDimensions
      ~slepc4py.SLEPc.PEP.getSTOARInertias
      ~slepc4py.SLEPc.PEP.getSTOARLinearization
      ~slepc4py.SLEPc.PEP.getSTOARLocking
      ~slepc4py.SLEPc.PEP.getScale
      ~slepc4py.SLEPc.PEP.getStoppingTest
      ~slepc4py.SLEPc.PEP.getTOARLocking
      ~slepc4py.SLEPc.PEP.getTOARRestart
      ~slepc4py.SLEPc.PEP.getTarget
      ~slepc4py.SLEPc.PEP.getTolerances
      ~slepc4py.SLEPc.PEP.getTrackAll
      ~slepc4py.SLEPc.PEP.getType
      ~slepc4py.SLEPc.PEP.getWhichEigenpairs
      ~slepc4py.SLEPc.PEP.reset
      ~slepc4py.SLEPc.PEP.setBV
      ~slepc4py.SLEPc.PEP.setBasis
      ~slepc4py.SLEPc.PEP.setCISSExtraction
      ~slepc4py.SLEPc.PEP.setCISSRefinement
      ~slepc4py.SLEPc.PEP.setCISSSizes
      ~slepc4py.SLEPc.PEP.setCISSThreshold
      ~slepc4py.SLEPc.PEP.setConvergenceTest
      ~slepc4py.SLEPc.PEP.setDS
      ~slepc4py.SLEPc.PEP.setDimensions
      ~slepc4py.SLEPc.PEP.setEigenvalueComparison
      ~slepc4py.SLEPc.PEP.setExtract
      ~slepc4py.SLEPc.PEP.setFromOptions
      ~slepc4py.SLEPc.PEP.setInitialSpace
      ~slepc4py.SLEPc.PEP.setInterval
      ~slepc4py.SLEPc.PEP.setJDFix
      ~slepc4py.SLEPc.PEP.setJDMinimalityIndex
      ~slepc4py.SLEPc.PEP.setJDProjection
      ~slepc4py.SLEPc.PEP.setJDRestart
      ~slepc4py.SLEPc.PEP.setJDReusePreconditioner
      ~slepc4py.SLEPc.PEP.setLinearEPS
      ~slepc4py.SLEPc.PEP.setLinearExplicitMatrix
      ~slepc4py.SLEPc.PEP.setLinearLinearization
      ~slepc4py.SLEPc.PEP.setMonitor
      ~slepc4py.SLEPc.PEP.setOperators
      ~slepc4py.SLEPc.PEP.setOptionsPrefix
      ~slepc4py.SLEPc.PEP.setProblemType
      ~slepc4py.SLEPc.PEP.setQArnoldiLocking
      ~slepc4py.SLEPc.PEP.setQArnoldiRestart
      ~slepc4py.SLEPc.PEP.setRG
      ~slepc4py.SLEPc.PEP.setRefine
      ~slepc4py.SLEPc.PEP.setST
      ~slepc4py.SLEPc.PEP.setSTOARCheckEigenvalueType
      ~slepc4py.SLEPc.PEP.setSTOARDetectZeros
      ~slepc4py.SLEPc.PEP.setSTOARDimensions
      ~slepc4py.SLEPc.PEP.setSTOARLinearization
      ~slepc4py.SLEPc.PEP.setSTOARLocking
      ~slepc4py.SLEPc.PEP.setScale
      ~slepc4py.SLEPc.PEP.setStoppingTest
      ~slepc4py.SLEPc.PEP.setTOARLocking
      ~slepc4py.SLEPc.PEP.setTOARRestart
      ~slepc4py.SLEPc.PEP.setTarget
      ~slepc4py.SLEPc.PEP.setTolerances
      ~slepc4py.SLEPc.PEP.setTrackAll
      ~slepc4py.SLEPc.PEP.setType
      ~slepc4py.SLEPc.PEP.setUp
      ~slepc4py.SLEPc.PEP.setWhichEigenpairs
      ~slepc4py.SLEPc.PEP.solve
      ~slepc4py.SLEPc.PEP.valuesView
      ~slepc4py.SLEPc.PEP.vectorsView
      ~slepc4py.SLEPc.PEP.view

   
   .. rubric:: Attributes Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.PEP.bv
      ~slepc4py.SLEPc.PEP.ds
      ~slepc4py.SLEPc.PEP.extract
      ~slepc4py.SLEPc.PEP.max_it
      ~slepc4py.SLEPc.PEP.problem_type
      ~slepc4py.SLEPc.PEP.rg
      ~slepc4py.SLEPc.PEP.st
      ~slepc4py.SLEPc.PEP.target
      ~slepc4py.SLEPc.PEP.tol
      ~slepc4py.SLEPc.PEP.track_all
      ~slepc4py.SLEPc.PEP.which

   
   .. rubric:: Methods Documentation
   
   .. automethod:: appendOptionsPrefix
   .. automethod:: cancelMonitor
   .. automethod:: computeError
   .. automethod:: create
   .. automethod:: destroy
   .. automethod:: errorView
   .. automethod:: getBV
   .. automethod:: getBasis
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
   .. automethod:: getExtract
   .. automethod:: getInterval
   .. automethod:: getIterationNumber
   .. automethod:: getJDFix
   .. automethod:: getJDMinimalityIndex
   .. automethod:: getJDProjection
   .. automethod:: getJDRestart
   .. automethod:: getJDReusePreconditioner
   .. automethod:: getLinearEPS
   .. automethod:: getLinearExplicitMatrix
   .. automethod:: getLinearLinearization
   .. automethod:: getMonitor
   .. automethod:: getOperators
   .. automethod:: getOptionsPrefix
   .. automethod:: getProblemType
   .. automethod:: getQArnoldiLocking
   .. automethod:: getQArnoldiRestart
   .. automethod:: getRG
   .. automethod:: getRefine
   .. automethod:: getRefineKSP
   .. automethod:: getST
   .. automethod:: getSTOARCheckEigenvalueType
   .. automethod:: getSTOARDetectZeros
   .. automethod:: getSTOARDimensions
   .. automethod:: getSTOARInertias
   .. automethod:: getSTOARLinearization
   .. automethod:: getSTOARLocking
   .. automethod:: getScale
   .. automethod:: getStoppingTest
   .. automethod:: getTOARLocking
   .. automethod:: getTOARRestart
   .. automethod:: getTarget
   .. automethod:: getTolerances
   .. automethod:: getTrackAll
   .. automethod:: getType
   .. automethod:: getWhichEigenpairs
   .. automethod:: reset
   .. automethod:: setBV
   .. automethod:: setBasis
   .. automethod:: setCISSExtraction
   .. automethod:: setCISSRefinement
   .. automethod:: setCISSSizes
   .. automethod:: setCISSThreshold
   .. automethod:: setConvergenceTest
   .. automethod:: setDS
   .. automethod:: setDimensions
   .. automethod:: setEigenvalueComparison
   .. automethod:: setExtract
   .. automethod:: setFromOptions
   .. automethod:: setInitialSpace
   .. automethod:: setInterval
   .. automethod:: setJDFix
   .. automethod:: setJDMinimalityIndex
   .. automethod:: setJDProjection
   .. automethod:: setJDRestart
   .. automethod:: setJDReusePreconditioner
   .. automethod:: setLinearEPS
   .. automethod:: setLinearExplicitMatrix
   .. automethod:: setLinearLinearization
   .. automethod:: setMonitor
   .. automethod:: setOperators
   .. automethod:: setOptionsPrefix
   .. automethod:: setProblemType
   .. automethod:: setQArnoldiLocking
   .. automethod:: setQArnoldiRestart
   .. automethod:: setRG
   .. automethod:: setRefine
   .. automethod:: setST
   .. automethod:: setSTOARCheckEigenvalueType
   .. automethod:: setSTOARDetectZeros
   .. automethod:: setSTOARDimensions
   .. automethod:: setSTOARLinearization
   .. automethod:: setSTOARLocking
   .. automethod:: setScale
   .. automethod:: setStoppingTest
   .. automethod:: setTOARLocking
   .. automethod:: setTOARRestart
   .. automethod:: setTarget
   .. automethod:: setTolerances
   .. automethod:: setTrackAll
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
   .. autoattribute:: extract
   .. autoattribute:: max_it
   .. autoattribute:: problem_type
   .. autoattribute:: rg
   .. autoattribute:: st
   .. autoattribute:: target
   .. autoattribute:: tol
   .. autoattribute:: track_all
   .. autoattribute:: which
