slepc4py.SLEPc.SVD
==================

.. autoclass:: slepc4py.SLEPc.SVD
   :show-inheritance:

   
   .. rubric:: Enumerations
   .. autosummary::
      :toctree:
   
      ~slepc4py.SLEPc.SVD.Conv
      ~slepc4py.SLEPc.SVD.ConvergedReason
      ~slepc4py.SLEPc.SVD.ErrorType
      ~slepc4py.SLEPc.SVD.ProblemType
      ~slepc4py.SLEPc.SVD.Stop
      ~slepc4py.SLEPc.SVD.TRLanczosGBidiag
      ~slepc4py.SLEPc.SVD.Type
      ~slepc4py.SLEPc.SVD.Which

   
   .. rubric:: Methods Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.SVD.appendOptionsPrefix
      ~slepc4py.SLEPc.SVD.cancelMonitor
      ~slepc4py.SLEPc.SVD.computeError
      ~slepc4py.SLEPc.SVD.create
      ~slepc4py.SLEPc.SVD.destroy
      ~slepc4py.SLEPc.SVD.errorView
      ~slepc4py.SLEPc.SVD.getBV
      ~slepc4py.SLEPc.SVD.getConverged
      ~slepc4py.SLEPc.SVD.getConvergedReason
      ~slepc4py.SLEPc.SVD.getConvergenceTest
      ~slepc4py.SLEPc.SVD.getCrossEPS
      ~slepc4py.SLEPc.SVD.getCrossExplicitMatrix
      ~slepc4py.SLEPc.SVD.getCyclicEPS
      ~slepc4py.SLEPc.SVD.getCyclicExplicitMatrix
      ~slepc4py.SLEPc.SVD.getDS
      ~slepc4py.SLEPc.SVD.getDimensions
      ~slepc4py.SLEPc.SVD.getImplicitTranspose
      ~slepc4py.SLEPc.SVD.getIterationNumber
      ~slepc4py.SLEPc.SVD.getLanczosOneSide
      ~slepc4py.SLEPc.SVD.getMonitor
      ~slepc4py.SLEPc.SVD.getOperators
      ~slepc4py.SLEPc.SVD.getOptionsPrefix
      ~slepc4py.SLEPc.SVD.getProblemType
      ~slepc4py.SLEPc.SVD.getSignature
      ~slepc4py.SLEPc.SVD.getSingularTriplet
      ~slepc4py.SLEPc.SVD.getStoppingTest
      ~slepc4py.SLEPc.SVD.getTRLanczosExplicitMatrix
      ~slepc4py.SLEPc.SVD.getTRLanczosGBidiag
      ~slepc4py.SLEPc.SVD.getTRLanczosKSP
      ~slepc4py.SLEPc.SVD.getTRLanczosLocking
      ~slepc4py.SLEPc.SVD.getTRLanczosOneSide
      ~slepc4py.SLEPc.SVD.getTRLanczosRestart
      ~slepc4py.SLEPc.SVD.getThreshold
      ~slepc4py.SLEPc.SVD.getTolerances
      ~slepc4py.SLEPc.SVD.getTrackAll
      ~slepc4py.SLEPc.SVD.getType
      ~slepc4py.SLEPc.SVD.getValue
      ~slepc4py.SLEPc.SVD.getVectors
      ~slepc4py.SLEPc.SVD.getWhichSingularTriplets
      ~slepc4py.SLEPc.SVD.isGeneralized
      ~slepc4py.SLEPc.SVD.isHyperbolic
      ~slepc4py.SLEPc.SVD.reset
      ~slepc4py.SLEPc.SVD.setBV
      ~slepc4py.SLEPc.SVD.setConvergenceTest
      ~slepc4py.SLEPc.SVD.setCrossEPS
      ~slepc4py.SLEPc.SVD.setCrossExplicitMatrix
      ~slepc4py.SLEPc.SVD.setCyclicEPS
      ~slepc4py.SLEPc.SVD.setCyclicExplicitMatrix
      ~slepc4py.SLEPc.SVD.setDS
      ~slepc4py.SLEPc.SVD.setDimensions
      ~slepc4py.SLEPc.SVD.setFromOptions
      ~slepc4py.SLEPc.SVD.setImplicitTranspose
      ~slepc4py.SLEPc.SVD.setInitialSpace
      ~slepc4py.SLEPc.SVD.setLanczosOneSide
      ~slepc4py.SLEPc.SVD.setMonitor
      ~slepc4py.SLEPc.SVD.setOperators
      ~slepc4py.SLEPc.SVD.setOptionsPrefix
      ~slepc4py.SLEPc.SVD.setProblemType
      ~slepc4py.SLEPc.SVD.setSignature
      ~slepc4py.SLEPc.SVD.setStoppingTest
      ~slepc4py.SLEPc.SVD.setTRLanczosExplicitMatrix
      ~slepc4py.SLEPc.SVD.setTRLanczosGBidiag
      ~slepc4py.SLEPc.SVD.setTRLanczosKSP
      ~slepc4py.SLEPc.SVD.setTRLanczosLocking
      ~slepc4py.SLEPc.SVD.setTRLanczosOneSide
      ~slepc4py.SLEPc.SVD.setTRLanczosRestart
      ~slepc4py.SLEPc.SVD.setThreshold
      ~slepc4py.SLEPc.SVD.setTolerances
      ~slepc4py.SLEPc.SVD.setTrackAll
      ~slepc4py.SLEPc.SVD.setType
      ~slepc4py.SLEPc.SVD.setUp
      ~slepc4py.SLEPc.SVD.setWhichSingularTriplets
      ~slepc4py.SLEPc.SVD.solve
      ~slepc4py.SLEPc.SVD.valuesView
      ~slepc4py.SLEPc.SVD.vectorsView
      ~slepc4py.SLEPc.SVD.view

   
   .. rubric:: Attributes Summary
   .. autosummary::
   
      ~slepc4py.SLEPc.SVD.ds
      ~slepc4py.SLEPc.SVD.max_it
      ~slepc4py.SLEPc.SVD.problem_type
      ~slepc4py.SLEPc.SVD.tol
      ~slepc4py.SLEPc.SVD.track_all
      ~slepc4py.SLEPc.SVD.transpose_mode
      ~slepc4py.SLEPc.SVD.which

   
   .. rubric:: Methods Documentation
   
   .. automethod:: appendOptionsPrefix
   .. automethod:: cancelMonitor
   .. automethod:: computeError
   .. automethod:: create
   .. automethod:: destroy
   .. automethod:: errorView
   .. automethod:: getBV
   .. automethod:: getConverged
   .. automethod:: getConvergedReason
   .. automethod:: getConvergenceTest
   .. automethod:: getCrossEPS
   .. automethod:: getCrossExplicitMatrix
   .. automethod:: getCyclicEPS
   .. automethod:: getCyclicExplicitMatrix
   .. automethod:: getDS
   .. automethod:: getDimensions
   .. automethod:: getImplicitTranspose
   .. automethod:: getIterationNumber
   .. automethod:: getLanczosOneSide
   .. automethod:: getMonitor
   .. automethod:: getOperators
   .. automethod:: getOptionsPrefix
   .. automethod:: getProblemType
   .. automethod:: getSignature
   .. automethod:: getSingularTriplet
   .. automethod:: getStoppingTest
   .. automethod:: getTRLanczosExplicitMatrix
   .. automethod:: getTRLanczosGBidiag
   .. automethod:: getTRLanczosKSP
   .. automethod:: getTRLanczosLocking
   .. automethod:: getTRLanczosOneSide
   .. automethod:: getTRLanczosRestart
   .. automethod:: getThreshold
   .. automethod:: getTolerances
   .. automethod:: getTrackAll
   .. automethod:: getType
   .. automethod:: getValue
   .. automethod:: getVectors
   .. automethod:: getWhichSingularTriplets
   .. automethod:: isGeneralized
   .. automethod:: isHyperbolic
   .. automethod:: reset
   .. automethod:: setBV
   .. automethod:: setConvergenceTest
   .. automethod:: setCrossEPS
   .. automethod:: setCrossExplicitMatrix
   .. automethod:: setCyclicEPS
   .. automethod:: setCyclicExplicitMatrix
   .. automethod:: setDS
   .. automethod:: setDimensions
   .. automethod:: setFromOptions
   .. automethod:: setImplicitTranspose
   .. automethod:: setInitialSpace
   .. automethod:: setLanczosOneSide
   .. automethod:: setMonitor
   .. automethod:: setOperators
   .. automethod:: setOptionsPrefix
   .. automethod:: setProblemType
   .. automethod:: setSignature
   .. automethod:: setStoppingTest
   .. automethod:: setTRLanczosExplicitMatrix
   .. automethod:: setTRLanczosGBidiag
   .. automethod:: setTRLanczosKSP
   .. automethod:: setTRLanczosLocking
   .. automethod:: setTRLanczosOneSide
   .. automethod:: setTRLanczosRestart
   .. automethod:: setThreshold
   .. automethod:: setTolerances
   .. automethod:: setTrackAll
   .. automethod:: setType
   .. automethod:: setUp
   .. automethod:: setWhichSingularTriplets
   .. automethod:: solve
   .. automethod:: valuesView
   .. automethod:: vectorsView
   .. automethod:: view

   
   .. rubric:: Attributes Documentation
   
   .. autoattribute:: ds
   .. autoattribute:: max_it
   .. autoattribute:: problem_type
   .. autoattribute:: tol
   .. autoattribute:: track_all
   .. autoattribute:: transpose_mode
   .. autoattribute:: which
