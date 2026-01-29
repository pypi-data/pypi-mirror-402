slepc4py.SLEPc.BV
=================

.. autoclass:: slepc4py.SLEPc.BV
   :show-inheritance:

   
   .. rubric:: Enumerations
   .. autosummary::
      :toctree:
   
      ~slepc4py.SLEPc.BV.MatMultType
      ~slepc4py.SLEPc.BV.OrthogBlockType
      ~slepc4py.SLEPc.BV.OrthogRefineType
      ~slepc4py.SLEPc.BV.OrthogType
      ~slepc4py.SLEPc.BV.SVDMethod
      ~slepc4py.SLEPc.BV.Type

   
   .. rubric:: Methods Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.BV.appendOptionsPrefix
      ~slepc4py.SLEPc.BV.applyMatrix
      ~slepc4py.SLEPc.BV.copy
      ~slepc4py.SLEPc.BV.copyColumn
      ~slepc4py.SLEPc.BV.copyVec
      ~slepc4py.SLEPc.BV.create
      ~slepc4py.SLEPc.BV.createFromMat
      ~slepc4py.SLEPc.BV.createMat
      ~slepc4py.SLEPc.BV.createVec
      ~slepc4py.SLEPc.BV.destroy
      ~slepc4py.SLEPc.BV.dot
      ~slepc4py.SLEPc.BV.dotColumn
      ~slepc4py.SLEPc.BV.dotVec
      ~slepc4py.SLEPc.BV.duplicate
      ~slepc4py.SLEPc.BV.duplicateResize
      ~slepc4py.SLEPc.BV.getActiveColumns
      ~slepc4py.SLEPc.BV.getArray
      ~slepc4py.SLEPc.BV.getColumn
      ~slepc4py.SLEPc.BV.getDefiniteTolerance
      ~slepc4py.SLEPc.BV.getLeadingDimension
      ~slepc4py.SLEPc.BV.getMat
      ~slepc4py.SLEPc.BV.getMatMultMethod
      ~slepc4py.SLEPc.BV.getMatrix
      ~slepc4py.SLEPc.BV.getNumConstraints
      ~slepc4py.SLEPc.BV.getOptionsPrefix
      ~slepc4py.SLEPc.BV.getOrthogonalization
      ~slepc4py.SLEPc.BV.getRandomContext
      ~slepc4py.SLEPc.BV.getSizes
      ~slepc4py.SLEPc.BV.getType
      ~slepc4py.SLEPc.BV.getVecType
      ~slepc4py.SLEPc.BV.insertConstraints
      ~slepc4py.SLEPc.BV.insertVec
      ~slepc4py.SLEPc.BV.insertVecs
      ~slepc4py.SLEPc.BV.matMult
      ~slepc4py.SLEPc.BV.matMultColumn
      ~slepc4py.SLEPc.BV.matMultHermitianTranspose
      ~slepc4py.SLEPc.BV.matMultHermitianTransposeColumn
      ~slepc4py.SLEPc.BV.matMultTranspose
      ~slepc4py.SLEPc.BV.matMultTransposeColumn
      ~slepc4py.SLEPc.BV.matProject
      ~slepc4py.SLEPc.BV.mult
      ~slepc4py.SLEPc.BV.multColumn
      ~slepc4py.SLEPc.BV.multInPlace
      ~slepc4py.SLEPc.BV.multVec
      ~slepc4py.SLEPc.BV.norm
      ~slepc4py.SLEPc.BV.normColumn
      ~slepc4py.SLEPc.BV.orthogonalize
      ~slepc4py.SLEPc.BV.orthogonalizeColumn
      ~slepc4py.SLEPc.BV.orthogonalizeVec
      ~slepc4py.SLEPc.BV.orthonormalizeColumn
      ~slepc4py.SLEPc.BV.resize
      ~slepc4py.SLEPc.BV.restoreColumn
      ~slepc4py.SLEPc.BV.restoreMat
      ~slepc4py.SLEPc.BV.scale
      ~slepc4py.SLEPc.BV.scaleColumn
      ~slepc4py.SLEPc.BV.setActiveColumns
      ~slepc4py.SLEPc.BV.setDefiniteTolerance
      ~slepc4py.SLEPc.BV.setFromOptions
      ~slepc4py.SLEPc.BV.setLeadingDimension
      ~slepc4py.SLEPc.BV.setMatMultMethod
      ~slepc4py.SLEPc.BV.setMatrix
      ~slepc4py.SLEPc.BV.setNumConstraints
      ~slepc4py.SLEPc.BV.setOptionsPrefix
      ~slepc4py.SLEPc.BV.setOrthogonalization
      ~slepc4py.SLEPc.BV.setRandom
      ~slepc4py.SLEPc.BV.setRandomColumn
      ~slepc4py.SLEPc.BV.setRandomCond
      ~slepc4py.SLEPc.BV.setRandomContext
      ~slepc4py.SLEPc.BV.setRandomNormal
      ~slepc4py.SLEPc.BV.setRandomSign
      ~slepc4py.SLEPc.BV.setSizes
      ~slepc4py.SLEPc.BV.setSizesFromVec
      ~slepc4py.SLEPc.BV.setType
      ~slepc4py.SLEPc.BV.setVecType
      ~slepc4py.SLEPc.BV.view

   
   .. rubric:: Attributes Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.BV.column_size
      ~slepc4py.SLEPc.BV.local_size
      ~slepc4py.SLEPc.BV.size
      ~slepc4py.SLEPc.BV.sizes

   
   .. rubric:: Methods Documentation
   
   .. automethod:: appendOptionsPrefix
   .. automethod:: applyMatrix
   .. automethod:: copy
   .. automethod:: copyColumn
   .. automethod:: copyVec
   .. automethod:: create
   .. automethod:: createFromMat
   .. automethod:: createMat
   .. automethod:: createVec
   .. automethod:: destroy
   .. automethod:: dot
   .. automethod:: dotColumn
   .. automethod:: dotVec
   .. automethod:: duplicate
   .. automethod:: duplicateResize
   .. automethod:: getActiveColumns
   .. automethod:: getArray
   .. automethod:: getColumn
   .. automethod:: getDefiniteTolerance
   .. automethod:: getLeadingDimension
   .. automethod:: getMat
   .. automethod:: getMatMultMethod
   .. automethod:: getMatrix
   .. automethod:: getNumConstraints
   .. automethod:: getOptionsPrefix
   .. automethod:: getOrthogonalization
   .. automethod:: getRandomContext
   .. automethod:: getSizes
   .. automethod:: getType
   .. automethod:: getVecType
   .. automethod:: insertConstraints
   .. automethod:: insertVec
   .. automethod:: insertVecs
   .. automethod:: matMult
   .. automethod:: matMultColumn
   .. automethod:: matMultHermitianTranspose
   .. automethod:: matMultHermitianTransposeColumn
   .. automethod:: matMultTranspose
   .. automethod:: matMultTransposeColumn
   .. automethod:: matProject
   .. automethod:: mult
   .. automethod:: multColumn
   .. automethod:: multInPlace
   .. automethod:: multVec
   .. automethod:: norm
   .. automethod:: normColumn
   .. automethod:: orthogonalize
   .. automethod:: orthogonalizeColumn
   .. automethod:: orthogonalizeVec
   .. automethod:: orthonormalizeColumn
   .. automethod:: resize
   .. automethod:: restoreColumn
   .. automethod:: restoreMat
   .. automethod:: scale
   .. automethod:: scaleColumn
   .. automethod:: setActiveColumns
   .. automethod:: setDefiniteTolerance
   .. automethod:: setFromOptions
   .. automethod:: setLeadingDimension
   .. automethod:: setMatMultMethod
   .. automethod:: setMatrix
   .. automethod:: setNumConstraints
   .. automethod:: setOptionsPrefix
   .. automethod:: setOrthogonalization
   .. automethod:: setRandom
   .. automethod:: setRandomColumn
   .. automethod:: setRandomCond
   .. automethod:: setRandomContext
   .. automethod:: setRandomNormal
   .. automethod:: setRandomSign
   .. automethod:: setSizes
   .. automethod:: setSizesFromVec
   .. automethod:: setType
   .. automethod:: setVecType
   .. automethod:: view

   
   .. rubric:: Attributes Documentation
   
   .. autoattribute:: column_size
   .. autoattribute:: local_size
   .. autoattribute:: size
   .. autoattribute:: sizes
