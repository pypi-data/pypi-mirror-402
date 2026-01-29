slepc4py.SLEPc.EPS
==================

.. autoclass:: slepc4py.SLEPc.EPS
   :show-inheritance:

   
   .. rubric:: Enumerations
   .. autosummary::
      :toctree:
   
      ~slepc4py.SLEPc.EPS.Balance
      ~slepc4py.SLEPc.EPS.CISSExtraction
      ~slepc4py.SLEPc.EPS.CISSQuadRule
      ~slepc4py.SLEPc.EPS.Conv
      ~slepc4py.SLEPc.EPS.ConvergedReason
      ~slepc4py.SLEPc.EPS.ErrorType
      ~slepc4py.SLEPc.EPS.Extraction
      ~slepc4py.SLEPc.EPS.KrylovSchurBSEType
      ~slepc4py.SLEPc.EPS.LanczosReorthogType
      ~slepc4py.SLEPc.EPS.PowerShiftType
      ~slepc4py.SLEPc.EPS.ProblemType
      ~slepc4py.SLEPc.EPS.Stop
      ~slepc4py.SLEPc.EPS.Type
      ~slepc4py.SLEPc.EPS.Which

   
   .. rubric:: Methods Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.EPS.appendOptionsPrefix
      ~slepc4py.SLEPc.EPS.cancelMonitor
      ~slepc4py.SLEPc.EPS.computeError
      ~slepc4py.SLEPc.EPS.create
      ~slepc4py.SLEPc.EPS.destroy
      ~slepc4py.SLEPc.EPS.errorView
      ~slepc4py.SLEPc.EPS.getArbitrarySelection
      ~slepc4py.SLEPc.EPS.getArnoldiDelayed
      ~slepc4py.SLEPc.EPS.getBV
      ~slepc4py.SLEPc.EPS.getBalance
      ~slepc4py.SLEPc.EPS.getCISSExtraction
      ~slepc4py.SLEPc.EPS.getCISSKSPs
      ~slepc4py.SLEPc.EPS.getCISSQuadRule
      ~slepc4py.SLEPc.EPS.getCISSRefinement
      ~slepc4py.SLEPc.EPS.getCISSSizes
      ~slepc4py.SLEPc.EPS.getCISSThreshold
      ~slepc4py.SLEPc.EPS.getCISSUseST
      ~slepc4py.SLEPc.EPS.getConverged
      ~slepc4py.SLEPc.EPS.getConvergedReason
      ~slepc4py.SLEPc.EPS.getConvergenceTest
      ~slepc4py.SLEPc.EPS.getDS
      ~slepc4py.SLEPc.EPS.getDimensions
      ~slepc4py.SLEPc.EPS.getEigenpair
      ~slepc4py.SLEPc.EPS.getEigenvalue
      ~slepc4py.SLEPc.EPS.getEigenvalueComparison
      ~slepc4py.SLEPc.EPS.getEigenvector
      ~slepc4py.SLEPc.EPS.getErrorEstimate
      ~slepc4py.SLEPc.EPS.getExtraction
      ~slepc4py.SLEPc.EPS.getGDBOrth
      ~slepc4py.SLEPc.EPS.getGDBlockSize
      ~slepc4py.SLEPc.EPS.getGDDoubleExpansion
      ~slepc4py.SLEPc.EPS.getGDInitialSize
      ~slepc4py.SLEPc.EPS.getGDKrylovStart
      ~slepc4py.SLEPc.EPS.getGDRestart
      ~slepc4py.SLEPc.EPS.getInterval
      ~slepc4py.SLEPc.EPS.getInvariantSubspace
      ~slepc4py.SLEPc.EPS.getIterationNumber
      ~slepc4py.SLEPc.EPS.getJDBOrth
      ~slepc4py.SLEPc.EPS.getJDBlockSize
      ~slepc4py.SLEPc.EPS.getJDConstCorrectionTol
      ~slepc4py.SLEPc.EPS.getJDFix
      ~slepc4py.SLEPc.EPS.getJDInitialSize
      ~slepc4py.SLEPc.EPS.getJDKrylovStart
      ~slepc4py.SLEPc.EPS.getJDRestart
      ~slepc4py.SLEPc.EPS.getKrylovSchurBSEType
      ~slepc4py.SLEPc.EPS.getKrylovSchurDetectZeros
      ~slepc4py.SLEPc.EPS.getKrylovSchurDimensions
      ~slepc4py.SLEPc.EPS.getKrylovSchurInertias
      ~slepc4py.SLEPc.EPS.getKrylovSchurKSP
      ~slepc4py.SLEPc.EPS.getKrylovSchurLocking
      ~slepc4py.SLEPc.EPS.getKrylovSchurPartitions
      ~slepc4py.SLEPc.EPS.getKrylovSchurRestart
      ~slepc4py.SLEPc.EPS.getKrylovSchurSubcommInfo
      ~slepc4py.SLEPc.EPS.getKrylovSchurSubcommMats
      ~slepc4py.SLEPc.EPS.getKrylovSchurSubcommPairs
      ~slepc4py.SLEPc.EPS.getKrylovSchurSubintervals
      ~slepc4py.SLEPc.EPS.getLOBPCGBlockSize
      ~slepc4py.SLEPc.EPS.getLOBPCGLocking
      ~slepc4py.SLEPc.EPS.getLOBPCGRestart
      ~slepc4py.SLEPc.EPS.getLanczosReorthogType
      ~slepc4py.SLEPc.EPS.getLeftEigenvector
      ~slepc4py.SLEPc.EPS.getLyapIIRanks
      ~slepc4py.SLEPc.EPS.getMonitor
      ~slepc4py.SLEPc.EPS.getOperators
      ~slepc4py.SLEPc.EPS.getOptionsPrefix
      ~slepc4py.SLEPc.EPS.getPowerShiftType
      ~slepc4py.SLEPc.EPS.getProblemType
      ~slepc4py.SLEPc.EPS.getPurify
      ~slepc4py.SLEPc.EPS.getRG
      ~slepc4py.SLEPc.EPS.getRQCGReset
      ~slepc4py.SLEPc.EPS.getST
      ~slepc4py.SLEPc.EPS.getStoppingTest
      ~slepc4py.SLEPc.EPS.getTarget
      ~slepc4py.SLEPc.EPS.getThreshold
      ~slepc4py.SLEPc.EPS.getTolerances
      ~slepc4py.SLEPc.EPS.getTrackAll
      ~slepc4py.SLEPc.EPS.getTrueResidual
      ~slepc4py.SLEPc.EPS.getTwoSided
      ~slepc4py.SLEPc.EPS.getType
      ~slepc4py.SLEPc.EPS.getWhichEigenpairs
      ~slepc4py.SLEPc.EPS.isGeneralized
      ~slepc4py.SLEPc.EPS.isHermitian
      ~slepc4py.SLEPc.EPS.isPositive
      ~slepc4py.SLEPc.EPS.isStructured
      ~slepc4py.SLEPc.EPS.reset
      ~slepc4py.SLEPc.EPS.setArbitrarySelection
      ~slepc4py.SLEPc.EPS.setArnoldiDelayed
      ~slepc4py.SLEPc.EPS.setBV
      ~slepc4py.SLEPc.EPS.setBalance
      ~slepc4py.SLEPc.EPS.setCISSExtraction
      ~slepc4py.SLEPc.EPS.setCISSQuadRule
      ~slepc4py.SLEPc.EPS.setCISSRefinement
      ~slepc4py.SLEPc.EPS.setCISSSizes
      ~slepc4py.SLEPc.EPS.setCISSThreshold
      ~slepc4py.SLEPc.EPS.setCISSUseST
      ~slepc4py.SLEPc.EPS.setConvergenceTest
      ~slepc4py.SLEPc.EPS.setDS
      ~slepc4py.SLEPc.EPS.setDeflationSpace
      ~slepc4py.SLEPc.EPS.setDimensions
      ~slepc4py.SLEPc.EPS.setEigenvalueComparison
      ~slepc4py.SLEPc.EPS.setExtraction
      ~slepc4py.SLEPc.EPS.setFromOptions
      ~slepc4py.SLEPc.EPS.setGDBOrth
      ~slepc4py.SLEPc.EPS.setGDBlockSize
      ~slepc4py.SLEPc.EPS.setGDDoubleExpansion
      ~slepc4py.SLEPc.EPS.setGDInitialSize
      ~slepc4py.SLEPc.EPS.setGDKrylovStart
      ~slepc4py.SLEPc.EPS.setGDRestart
      ~slepc4py.SLEPc.EPS.setInitialSpace
      ~slepc4py.SLEPc.EPS.setInterval
      ~slepc4py.SLEPc.EPS.setJDBOrth
      ~slepc4py.SLEPc.EPS.setJDBlockSize
      ~slepc4py.SLEPc.EPS.setJDConstCorrectionTol
      ~slepc4py.SLEPc.EPS.setJDFix
      ~slepc4py.SLEPc.EPS.setJDInitialSize
      ~slepc4py.SLEPc.EPS.setJDKrylovStart
      ~slepc4py.SLEPc.EPS.setJDRestart
      ~slepc4py.SLEPc.EPS.setKrylovSchurBSEType
      ~slepc4py.SLEPc.EPS.setKrylovSchurDetectZeros
      ~slepc4py.SLEPc.EPS.setKrylovSchurDimensions
      ~slepc4py.SLEPc.EPS.setKrylovSchurLocking
      ~slepc4py.SLEPc.EPS.setKrylovSchurPartitions
      ~slepc4py.SLEPc.EPS.setKrylovSchurRestart
      ~slepc4py.SLEPc.EPS.setKrylovSchurSubintervals
      ~slepc4py.SLEPc.EPS.setLOBPCGBlockSize
      ~slepc4py.SLEPc.EPS.setLOBPCGLocking
      ~slepc4py.SLEPc.EPS.setLOBPCGRestart
      ~slepc4py.SLEPc.EPS.setLanczosReorthogType
      ~slepc4py.SLEPc.EPS.setLeftInitialSpace
      ~slepc4py.SLEPc.EPS.setLyapIIRanks
      ~slepc4py.SLEPc.EPS.setMonitor
      ~slepc4py.SLEPc.EPS.setOperators
      ~slepc4py.SLEPc.EPS.setOptionsPrefix
      ~slepc4py.SLEPc.EPS.setPowerShiftType
      ~slepc4py.SLEPc.EPS.setProblemType
      ~slepc4py.SLEPc.EPS.setPurify
      ~slepc4py.SLEPc.EPS.setRG
      ~slepc4py.SLEPc.EPS.setRQCGReset
      ~slepc4py.SLEPc.EPS.setST
      ~slepc4py.SLEPc.EPS.setStoppingTest
      ~slepc4py.SLEPc.EPS.setTarget
      ~slepc4py.SLEPc.EPS.setThreshold
      ~slepc4py.SLEPc.EPS.setTolerances
      ~slepc4py.SLEPc.EPS.setTrackAll
      ~slepc4py.SLEPc.EPS.setTrueResidual
      ~slepc4py.SLEPc.EPS.setTwoSided
      ~slepc4py.SLEPc.EPS.setType
      ~slepc4py.SLEPc.EPS.setUp
      ~slepc4py.SLEPc.EPS.setWhichEigenpairs
      ~slepc4py.SLEPc.EPS.solve
      ~slepc4py.SLEPc.EPS.updateKrylovSchurSubcommMats
      ~slepc4py.SLEPc.EPS.valuesView
      ~slepc4py.SLEPc.EPS.vectorsView
      ~slepc4py.SLEPc.EPS.view

   
   .. rubric:: Attributes Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.EPS.bv
      ~slepc4py.SLEPc.EPS.ds
      ~slepc4py.SLEPc.EPS.extraction
      ~slepc4py.SLEPc.EPS.max_it
      ~slepc4py.SLEPc.EPS.problem_type
      ~slepc4py.SLEPc.EPS.purify
      ~slepc4py.SLEPc.EPS.rg
      ~slepc4py.SLEPc.EPS.st
      ~slepc4py.SLEPc.EPS.target
      ~slepc4py.SLEPc.EPS.tol
      ~slepc4py.SLEPc.EPS.track_all
      ~slepc4py.SLEPc.EPS.true_residual
      ~slepc4py.SLEPc.EPS.two_sided
      ~slepc4py.SLEPc.EPS.which

   
   .. rubric:: Methods Documentation
   
   .. automethod:: appendOptionsPrefix
   .. automethod:: cancelMonitor
   .. automethod:: computeError
   .. automethod:: create
   .. automethod:: destroy
   .. automethod:: errorView
   .. automethod:: getArbitrarySelection
   .. automethod:: getArnoldiDelayed
   .. automethod:: getBV
   .. automethod:: getBalance
   .. automethod:: getCISSExtraction
   .. automethod:: getCISSKSPs
   .. automethod:: getCISSQuadRule
   .. automethod:: getCISSRefinement
   .. automethod:: getCISSSizes
   .. automethod:: getCISSThreshold
   .. automethod:: getCISSUseST
   .. automethod:: getConverged
   .. automethod:: getConvergedReason
   .. automethod:: getConvergenceTest
   .. automethod:: getDS
   .. automethod:: getDimensions
   .. automethod:: getEigenpair
   .. automethod:: getEigenvalue
   .. automethod:: getEigenvalueComparison
   .. automethod:: getEigenvector
   .. automethod:: getErrorEstimate
   .. automethod:: getExtraction
   .. automethod:: getGDBOrth
   .. automethod:: getGDBlockSize
   .. automethod:: getGDDoubleExpansion
   .. automethod:: getGDInitialSize
   .. automethod:: getGDKrylovStart
   .. automethod:: getGDRestart
   .. automethod:: getInterval
   .. automethod:: getInvariantSubspace
   .. automethod:: getIterationNumber
   .. automethod:: getJDBOrth
   .. automethod:: getJDBlockSize
   .. automethod:: getJDConstCorrectionTol
   .. automethod:: getJDFix
   .. automethod:: getJDInitialSize
   .. automethod:: getJDKrylovStart
   .. automethod:: getJDRestart
   .. automethod:: getKrylovSchurBSEType
   .. automethod:: getKrylovSchurDetectZeros
   .. automethod:: getKrylovSchurDimensions
   .. automethod:: getKrylovSchurInertias
   .. automethod:: getKrylovSchurKSP
   .. automethod:: getKrylovSchurLocking
   .. automethod:: getKrylovSchurPartitions
   .. automethod:: getKrylovSchurRestart
   .. automethod:: getKrylovSchurSubcommInfo
   .. automethod:: getKrylovSchurSubcommMats
   .. automethod:: getKrylovSchurSubcommPairs
   .. automethod:: getKrylovSchurSubintervals
   .. automethod:: getLOBPCGBlockSize
   .. automethod:: getLOBPCGLocking
   .. automethod:: getLOBPCGRestart
   .. automethod:: getLanczosReorthogType
   .. automethod:: getLeftEigenvector
   .. automethod:: getLyapIIRanks
   .. automethod:: getMonitor
   .. automethod:: getOperators
   .. automethod:: getOptionsPrefix
   .. automethod:: getPowerShiftType
   .. automethod:: getProblemType
   .. automethod:: getPurify
   .. automethod:: getRG
   .. automethod:: getRQCGReset
   .. automethod:: getST
   .. automethod:: getStoppingTest
   .. automethod:: getTarget
   .. automethod:: getThreshold
   .. automethod:: getTolerances
   .. automethod:: getTrackAll
   .. automethod:: getTrueResidual
   .. automethod:: getTwoSided
   .. automethod:: getType
   .. automethod:: getWhichEigenpairs
   .. automethod:: isGeneralized
   .. automethod:: isHermitian
   .. automethod:: isPositive
   .. automethod:: isStructured
   .. automethod:: reset
   .. automethod:: setArbitrarySelection
   .. automethod:: setArnoldiDelayed
   .. automethod:: setBV
   .. automethod:: setBalance
   .. automethod:: setCISSExtraction
   .. automethod:: setCISSQuadRule
   .. automethod:: setCISSRefinement
   .. automethod:: setCISSSizes
   .. automethod:: setCISSThreshold
   .. automethod:: setCISSUseST
   .. automethod:: setConvergenceTest
   .. automethod:: setDS
   .. automethod:: setDeflationSpace
   .. automethod:: setDimensions
   .. automethod:: setEigenvalueComparison
   .. automethod:: setExtraction
   .. automethod:: setFromOptions
   .. automethod:: setGDBOrth
   .. automethod:: setGDBlockSize
   .. automethod:: setGDDoubleExpansion
   .. automethod:: setGDInitialSize
   .. automethod:: setGDKrylovStart
   .. automethod:: setGDRestart
   .. automethod:: setInitialSpace
   .. automethod:: setInterval
   .. automethod:: setJDBOrth
   .. automethod:: setJDBlockSize
   .. automethod:: setJDConstCorrectionTol
   .. automethod:: setJDFix
   .. automethod:: setJDInitialSize
   .. automethod:: setJDKrylovStart
   .. automethod:: setJDRestart
   .. automethod:: setKrylovSchurBSEType
   .. automethod:: setKrylovSchurDetectZeros
   .. automethod:: setKrylovSchurDimensions
   .. automethod:: setKrylovSchurLocking
   .. automethod:: setKrylovSchurPartitions
   .. automethod:: setKrylovSchurRestart
   .. automethod:: setKrylovSchurSubintervals
   .. automethod:: setLOBPCGBlockSize
   .. automethod:: setLOBPCGLocking
   .. automethod:: setLOBPCGRestart
   .. automethod:: setLanczosReorthogType
   .. automethod:: setLeftInitialSpace
   .. automethod:: setLyapIIRanks
   .. automethod:: setMonitor
   .. automethod:: setOperators
   .. automethod:: setOptionsPrefix
   .. automethod:: setPowerShiftType
   .. automethod:: setProblemType
   .. automethod:: setPurify
   .. automethod:: setRG
   .. automethod:: setRQCGReset
   .. automethod:: setST
   .. automethod:: setStoppingTest
   .. automethod:: setTarget
   .. automethod:: setThreshold
   .. automethod:: setTolerances
   .. automethod:: setTrackAll
   .. automethod:: setTrueResidual
   .. automethod:: setTwoSided
   .. automethod:: setType
   .. automethod:: setUp
   .. automethod:: setWhichEigenpairs
   .. automethod:: solve
   .. automethod:: updateKrylovSchurSubcommMats
   .. automethod:: valuesView
   .. automethod:: vectorsView
   .. automethod:: view

   
   .. rubric:: Attributes Documentation
   
   .. autoattribute:: bv
   .. autoattribute:: ds
   .. autoattribute:: extraction
   .. autoattribute:: max_it
   .. autoattribute:: problem_type
   .. autoattribute:: purify
   .. autoattribute:: rg
   .. autoattribute:: st
   .. autoattribute:: target
   .. autoattribute:: tol
   .. autoattribute:: track_all
   .. autoattribute:: true_residual
   .. autoattribute:: two_sided
   .. autoattribute:: which
