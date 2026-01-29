"""
Scalable Library for Eigenvalue Problem Computations
"""
from __future__ import annotations
import sys
from typing import (
    Any,
    Union,
    Optional,
    Callable,
    Sequence,
)
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

import numpy
from numpy import dtype, ndarray
from mpi4py.MPI import (
    Intracomm,
    Datatype,
    Op,
)

# -----------------------------------------------------------------------------

from petsc4py.PETSc import (
    Object,
    Comm,
    NormType,
    Random,
    Viewer,
    Vec,
    Mat,
    KSP,
)

# -----------------------------------------------------------------------------

class _dtype:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name

IntType: dtype = _dtype('IntType')
RealType: dtype =  _dtype('RealType')
ComplexType: dtype = _dtype('ComplexType')
ScalarType: dtype = _dtype('ScalarType')

class _Int(int): pass
class _Str(str): pass
class _Float(float): pass
class _Dict(dict): pass

def _repr(obj):
    try:
        return obj._name
    except AttributeError:
        return super(obj).__repr__()

def _def(cls, name):
    if cls is int:
       cls = _Int
    if cls is str:
       cls = _Str
    if cls is float:
       cls = _Float
    if cls is dict:
       cls = _Dict

    obj = cls()
    obj._name = name
    if '__repr__' not in cls.__dict__:
        cls.__repr__ = _repr
    return obj

DECIDE: int = _def(int, 'DECIDE')  #: Constant ``DECIDE`` of type :class:`int`
DEFAULT: int = _def(int, 'DEFAULT')  #: Constant ``DEFAULT`` of type :class:`int`
DETERMINE: int = _def(int, 'DETERMINE')  #: Constant ``DETERMINE`` of type :class:`int`
CURRENT: int = _def(int, 'CURRENT')  #: Constant ``CURRENT`` of type :class:`int`
__arch__: str = _def(str, '__arch__')  #: Object ``__arch__`` of type :class:`str`

class ST(Object):
    """Spectral Transformation.
    
    The Spectral Transformation (`ST`) class encapsulates the functionality
    required for acceleration techniques based on the transformation of the
    spectrum. The eigensolvers implemented in `EPS` work by applying an
    operator to a set of vectors and this operator can adopt different forms.
    The `ST` object handles all the different possibilities in a uniform way,
    so that the solver can proceed without knowing which transformation has
    been selected. Polynomial eigensolvers in `PEP` also support spectral
    transformation.
    
    """
    class Type:
        """ST type.
        
        - `SHIFT`:   Shift from origin.
        - `SINVERT`: Shift-and-invert.
        - `CAYLEY`:  Cayley transform.
        - `PRECOND`: Preconditioner.
        - `FILTER`:  Polynomial filter.
        - `SHELL`:   User-defined.
        
        See Also
        --------
        slepc.STType
        
        """
        SHIFT: str = _def(str, 'SHIFT')  #: Object ``SHIFT`` of type :class:`str`
        SINVERT: str = _def(str, 'SINVERT')  #: Object ``SINVERT`` of type :class:`str`
        CAYLEY: str = _def(str, 'CAYLEY')  #: Object ``CAYLEY`` of type :class:`str`
        PRECOND: str = _def(str, 'PRECOND')  #: Object ``PRECOND`` of type :class:`str`
        FILTER: str = _def(str, 'FILTER')  #: Object ``FILTER`` of type :class:`str`
        SHELL: str = _def(str, 'SHELL')  #: Object ``SHELL`` of type :class:`str`
    class MatMode:
        """ST matrix mode.
        
        - `COPY`:    A working copy of the matrix is created.
        - `INPLACE`: The operation is computed in-place.
        - `SHELL`:   The matrix :math:`A - \sigma B` is handled as an
          implicit matrix.
        
        See Also
        --------
        slepc.STMatMode
        
        """
        COPY: int = _def(int, 'COPY')  #: Constant ``COPY`` of type :class:`int`
        INPLACE: int = _def(int, 'INPLACE')  #: Constant ``INPLACE`` of type :class:`int`
        SHELL: int = _def(int, 'SHELL')  #: Constant ``SHELL`` of type :class:`int`
    class FilterType:
        """ST filter type.
        
        - ``FILTLAN``:  An adapted implementation of the Filtered Lanczos Package.
        - ``CHEBYSEV``: A polynomial filter based on a truncated Chebyshev series.
        
        See Also
        --------
        slepc.STFilterType
        
        """
        FILTLAN: int = _def(int, 'FILTLAN')  #: Constant ``FILTLAN`` of type :class:`int`
        CHEBYSHEV: int = _def(int, 'CHEBYSHEV')  #: Constant ``CHEBYSHEV`` of type :class:`int`
    class FilterDamping:
        """ST filter damping.
        
        - `NONE`:    No damping
        - `JACKSON`: Jackson damping
        - `LANCZOS`: Lanczos damping
        - `FEJER`:   Fejer damping
        
        See Also
        --------
        slepc.STFilterDamping
        
        """
        NONE: int = _def(int, 'NONE')  #: Constant ``NONE`` of type :class:`int`
        JACKSON: int = _def(int, 'JACKSON')  #: Constant ``JACKSON`` of type :class:`int`
        LANCZOS: int = _def(int, 'LANCZOS')  #: Constant ``LANCZOS`` of type :class:`int`
        FEJER: int = _def(int, 'FEJER')  #: Constant ``FEJER`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the ST data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.STView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:100 <slepc4py/SLEPc/ST.pyx#L100>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the ST object.
    
        Collective.
    
        See Also
        --------
        slepc.STDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:119 <slepc4py/SLEPc/ST.pyx#L119>`
    
        """
        ...
    def reset(self) -> None:
        """Reset the ST object.
    
        Collective.
    
        See Also
        --------
        slepc.STReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:133 <slepc4py/SLEPc/ST.pyx#L133>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the ST object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator; if not provided, it defaults to all processes.
    
        See Also
        --------
        slepc.STCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:145 <slepc4py/SLEPc/ST.pyx#L145>`
    
        """
        ...
    def setType(self, st_type: Type | str) -> None:
        """Set the particular spectral transformation to be used.
    
        Logically collective.
    
        Parameters
        ----------
        st_type
            The spectral transformation to be used.
    
        Notes
        -----
        The default is `SHIFT` with a zero shift. Normally, it is best
        to use `setFromOptions()` and then set the ST type from the
        options database rather than by using this routine. Using the
        options database provides the user with maximum flexibility in
        evaluating the different available methods.
    
        See Also
        --------
        getType, slepc.STSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:166 <slepc4py/SLEPc/ST.pyx#L166>`
    
        """
        ...
    def getType(self) -> str:
        """Get the ST type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The spectral transformation currently being used.
    
        See Also
        --------
        setType, slepc.STGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:193 <slepc4py/SLEPc/ST.pyx#L193>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all ST options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all ST option requests.
    
        Notes
        -----
        A hyphen (``-``) must NOT be given at the beginning of the
        prefix name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.STGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:212 <slepc4py/SLEPc/ST.pyx#L212>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all ST options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this ST object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.STGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:237 <slepc4py/SLEPc/ST.pyx#L237>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all ST options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all ST option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.STAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:256 <slepc4py/SLEPc/ST.pyx#L256>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set ST options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help`` option.
    
        This routine must be called before `setUp()` if the user is to be
        allowed to set the solver type.
    
        See Also
        --------
        setOptionsPrefix, slepc.STSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:275 <slepc4py/SLEPc/ST.pyx#L275>`
    
        """
        ...
    def setShift(self, shift: Scalar) -> None:
        """Set the shift associated with the spectral transformation.
    
        Collective.
    
        Parameters
        ----------
        shift
            The value of the shift.
    
        Notes
        -----
        In some spectral transformations, changing the shift may have
        associated a lot of work, for example recomputing a
        factorization.
    
        This function is normally not directly called by users, since the
        shift is indirectly set by `EPS.setTarget()`.
    
        See Also
        --------
        getShift, slepc.STSetShift
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:296 <slepc4py/SLEPc/ST.pyx#L296>`
    
        """
        ...
    def getShift(self) -> Scalar:
        """Get the shift associated with the spectral transformation.
    
        Not collective.
    
        Returns
        -------
        Scalar
            The value of the shift.
    
        See Also
        --------
        setShift, slepc.STGetShift
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:323 <slepc4py/SLEPc/ST.pyx#L323>`
    
        """
        ...
    def setTransform(self, flag: bool = True) -> None:
        """Set a flag to indicate whether the transformed matrices are computed or not.
    
        Logically collective.
    
        Parameters
        ----------
        flag
            This flag is intended for the case of polynomial
            eigenproblems solved via linearization.
            If this flag is ``False`` (default) the spectral transformation
            is applied to the linearization (handled by the eigensolver),
            otherwise it is applied to the original problem.
    
        See Also
        --------
        getTransform, slepc.STSetTransform
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:342 <slepc4py/SLEPc/ST.pyx#L342>`
    
        """
        ...
    def getTransform(self) -> bool:
        """Get the flag indicating whether the transformed matrices are computed or not.
    
        Not collective.
    
        Returns
        -------
        bool
            This flag is intended for the case of polynomial
            eigenproblems solved via linearization.
            If this flag is ``False`` (default) the spectral transformation
            is applied to the linearization (handled by the eigensolver),
            otherwise it is applied to the original problem.
    
        See Also
        --------
        setTransform, slepc.STGetTransform
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:364 <slepc4py/SLEPc/ST.pyx#L364>`
    
        """
        ...
    def setMatMode(self, mode: MatMode) -> None:
        """Set a flag related to management of transformed matrices.
    
        Logically collective.
    
        The flag indicates how the transformed matrices are being
        stored in the spectral transformation.
    
        Parameters
        ----------
        mode
            The mode flag.
    
        Notes
        -----
        By default (`ST.MatMode.COPY`), a copy of matrix :math:`A` is made
        and then this copy is modified explicitly, e.g.,
        :math:`A \leftarrow (A - \sigma B)`.
    
        With `ST.MatMode.INPLACE`, the original matrix :math:`A` is modified at
        `setUp()` and reverted at the end of the computations. With respect to
        the previous one, this mode avoids a copy of matrix :math:`A`. However,
        a backdraw is that the recovered matrix might be slightly different
        from the original one (due to roundoff).
    
        With `ST.MatMode.SHELL`, the solver works with an implicit shell matrix
        that represents the shifted matrix. This mode is the most efficient in
        creating the transformed matrix but it places serious limitations to the
        linear solves performed in each iteration of the eigensolver
        (typically, only iterative solvers with Jacobi preconditioning can be
        used).
    
        In the two first modes the efficiency of this computation can be
        controlled with `setMatStructure()`.
    
        See Also
        --------
        setMatrices, setMatStructure, getMatMode, slepc.STSetMatMode
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:387 <slepc4py/SLEPc/ST.pyx#L387>`
    
        """
        ...
    def getMatMode(self) -> MatMode:
        """Get a flag that indicates how the matrix is being shifted.
    
        Not collective.
    
        Get a flag that indicates how the matrix is being shifted in
        the shift-and-invert and Cayley spectral transformations.
    
        Returns
        -------
        MatMode
            The mode flag.
    
        See Also
        --------
        setMatMode, slepc.STGetMatMode
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:430 <slepc4py/SLEPc/ST.pyx#L430>`
    
        """
        ...
    def setMatrices(self, operators: list[Mat]) -> None:
        """Set the matrices associated with the eigenvalue problem.
    
        Collective.
    
        Parameters
        ----------
        operators
            The matrices associated with the eigensystem.
    
        Notes
        -----
        It must be called before `setUp()`. If it is called again after
        `setUp()` then the `ST` object is reset.
    
        In standard eigenproblems only one matrix is passed, while in
        generalized problems two matrices are provided. The number of
        matrices is larger in polynomial eigenproblems.
    
        In normal usage, matrices are provided via the corresponding
        `EPS` of `PEP` interface function.
    
        See Also
        --------
        getMatrices, setUp, reset, slepc.STSetMatrices
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:452 <slepc4py/SLEPc/ST.pyx#L452>`
    
        """
        ...
    def getMatrices(self) -> list[Mat]:
        """Get the matrices associated with the eigenvalue problem.
    
        Collective.
    
        Returns
        -------
        list of petsc4py.PETSc.Mat
            The matrices associated with the eigensystem.
    
        See Also
        --------
        setMatrices, slepc.STGetNumMatrices, slepc.STGetMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:486 <slepc4py/SLEPc/ST.pyx#L486>`
    
        """
        ...
    def setMatStructure(self, structure: petsc4py.PETSc.Mat.Structure) -> None:
        """Set the matrix structure attribute.
    
        Logically collective.
    
        Set an internal `petsc4py.PETSc.Mat.Structure` attribute to indicate
        which is the relation of the sparsity pattern of all the `ST` matrices.
    
        Parameters
        ----------
        structure
            The matrix structure specification.
    
        Notes
        -----
        By default, the sparsity patterns are assumed to be
        different. If the patterns are equal or a subset then it is
        recommended to set this attribute for efficiency reasons (in
        particular, for internal ``Mat.axpy()`` operations).
    
        This function has no effect in the case of standard eigenproblems.
    
        In case of polynomial eigenproblems, the flag applies to all
        matrices relative to the first one.
    
        See Also
        --------
        getMatStructure, setMatrices, slepc.STSetMatStructure
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:512 <slepc4py/SLEPc/ST.pyx#L512>`
    
        """
        ...
    def getMatStructure(self) -> petsc4py.PETSc.Mat.Structure:
        """Get the internal matrix structure attribute.
    
        Not collective.
    
        Get the internal `petsc4py.PETSc.Mat.Structure` attribute to
        indicate which is the relation of the sparsity pattern of the
        matrices.
    
        Returns
        -------
        petsc4py.PETSc.Mat.Structure
            The structure flag.
    
        See Also
        --------
        setMatStructure, slepc.STGetMatStructure
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:545 <slepc4py/SLEPc/ST.pyx#L545>`
    
        """
        ...
    def setKSP(self, ksp: KSP) -> None:
        """Set the ``KSP`` object associated with the spectral transformation.
    
        Collective.
    
        Parameters
        ----------
        ksp
            The linear solver object.
    
        See Also
        --------
        getKSP, slepc.STSetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:568 <slepc4py/SLEPc/ST.pyx#L568>`
    
        """
        ...
    def getKSP(self) -> KSP:
        """Get the ``KSP`` object associated with the spectral transformation.
    
        Collective.
    
        Returns
        -------
        `petsc4py.PETSc.KSP`
            The linear solver object.
    
        See Also
        --------
        setKSP, slepc.STGetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:585 <slepc4py/SLEPc/ST.pyx#L585>`
    
        """
        ...
    def setPreconditionerMat(self, P: Mat | None = None) -> None:
        """Set the matrix to be used to build the preconditioner.
    
        Collective.
    
        Parameters
        ----------
        P
            The matrix that will be used in constructing the preconditioner.
    
        Notes
        -----
        This matrix will be passed to the internal ``KSP`` object (via the last
        argument of ``KSP.setOperators()``) as the matrix to be
        used when constructing the preconditioner. If no matrix is set then
        :math:`A-\sigma B` will be used to build the preconditioner, being
        :math:`\sigma` the value set by `setShift()`.
    
        More precisely, this is relevant for spectral transformations that
        represent a rational matrix function, and use a ``KSP`` object for the
        denominator. It includes also the `PRECOND` case. If the user has a
        good approximation to matrix that can be used to build a cheap
        preconditioner, it can be passed with this function. Note that it
        affects only the ``Pmat`` argument of ``KSP.setOperators()``,
        not the ``Amat`` argument.
    
        If a preconditioner matrix is set, the default is to use an iterative
        ``KSP`` rather than a direct method.
    
        An alternative to pass an approximation of :math:`A-\sigma B` with this
        function is to provide approximations of :math:`A` and :math:`B` via
        `setSplitPreconditioner()`. The difference is that when :math:`\sigma`
        changes the preconditioner is recomputed.
    
        A call with no matrix argument will remove a previously set matrix.
    
        See Also
        --------
        getPreconditionerMat, slepc.STSetPreconditionerMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:605 <slepc4py/SLEPc/ST.pyx#L605>`
    
        """
        ...
    def getPreconditionerMat(self) -> Mat:
        """Get the matrix previously set by `setPreconditionerMat()`.
    
        Not collective.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            The matrix that will be used in constructing the preconditioner.
    
        See Also
        --------
        setPreconditionerMat, slepc.STGetPreconditionerMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:649 <slepc4py/SLEPc/ST.pyx#L649>`
    
        """
        ...
    def setSplitPreconditioner(self, operators: list[petsc4py.PETSc.Mat], structure: petsc4py.PETSc.Mat.Structure | None = None) -> None:
        """Set the matrices to be used to build the preconditioner.
    
        Collective.
    
        Parameters
        ----------
        operators
            The matrices associated with the preconditioner.
        structure
            The matrix structure specification.
    
        Notes
        -----
        The number of matrices passed here must be the same as in `setMatrices()`.
    
        For linear eigenproblems, the preconditioner matrix is computed as
        :math:`P(\sigma) = A_0-\sigma B_0`, where :math:`A_0,B_0` are
        approximations of :math:`A,B` (the eigenproblem matrices) provided via the
        ``operators`` argument in this function. Compared to `setPreconditionerMat()`,
        this function allows setting a preconditioner in a way that is independent
        of the shift :math:`\sigma`. Whenever the value of :math:`\sigma` changes
        the preconditioner is recomputed.
    
        Similarly, for polynomial eigenproblems the matrix for the preconditioner
        is expressed as :math:`P(\sigma) = \sum_i P_i \phi_i(\sigma)`, for
        :math:`i=1,\dots,n`, where :math:`P_i` are given in ``operators`` and the
        :math:`\phi_i`'s are the polynomial basis functions.
    
        The ``structure`` flag provides information about the relative nonzero
        pattern of the ``operators`` matrices, in the same way as in
        `setMatStructure()`.
    
        See Also
        --------
        getSplitPreconditioner, setPreconditionerMat, slepc.STSetSplitPreconditioner
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:669 <slepc4py/SLEPc/ST.pyx#L669>`
    
        """
        ...
    def getSplitPreconditioner(self) -> tuple[list[petsc4py.PETSc.Mat], petsc4py.PETSc.Mat.Structure]:
        """Get the matrices to be used to build the preconditioner.
    
        Not collective.
    
        Returns
        -------
        list of petsc4py.PETSc.Mat
            The list of matrices associated with the preconditioner.
        petsc4py.PETSc.Mat.Structure
            The structure flag.
    
        See Also
        --------
        slepc.STGetSplitPreconditionerInfo, slepc.STGetSplitPreconditionerTerm
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:716 <slepc4py/SLEPc/ST.pyx#L716>`
    
        """
        ...
    def setUp(self) -> None:
        """Prepare for the use of a spectral transformation.
    
        Collective.
    
        See Also
        --------
        apply, slepc.STSetUp
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:746 <slepc4py/SLEPc/ST.pyx#L746>`
    
        """
        ...
    def apply(self, x: Vec, y: Vec) -> None:
        """Apply the spectral transformation operator to a vector.
    
        Collective.
    
        Apply the spectral transformation operator to a vector, for instance
        :math:`y=(A-\sigma B)^{-1}Bx` in the case of the shift-and-invert
        transformation and generalized eigenproblem.
    
        Parameters
        ----------
        x
            The input vector.
        y
            The result vector.
    
        See Also
        --------
        applyTranspose, applyHermitianTranspose, applyMat, slepc.STApply
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:758 <slepc4py/SLEPc/ST.pyx#L758>`
    
        """
        ...
    def applyTranspose(self, x: Vec, y: Vec) -> None:
        """Apply the transpose of the operator to a vector.
    
        Collective.
    
        Apply the transpose of the operator to a vector, for instance
        :math:`y=B^T(A-\sigma B)^{-T}x` in the case of the shift-and-invert
        transformation and generalized eigenproblem.
    
        Parameters
        ----------
        x
            The input vector.
        y
            The result vector.
    
        See Also
        --------
        apply, applyHermitianTranspose, slepc.STApplyTranspose
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:781 <slepc4py/SLEPc/ST.pyx#L781>`
    
        """
        ...
    def applyHermitianTranspose(self, x: Vec, y: Vec) -> None:
        """Apply the Hermitian-transpose of the operator to a vector.
    
        Collective.
    
        Apply the Hermitian-transpose of the operator to a vector, for instance
        :math:`y=B^*(A - \sigma B)^{-*}x` in the case of the shift-and-invert
        transformation and generalized eigenproblem.
    
        Parameters
        ----------
        x
            The input vector.
        y
            The result vector.
    
        See Also
        --------
        apply, applyTranspose, slepc.STApplyHermitianTranspose
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:804 <slepc4py/SLEPc/ST.pyx#L804>`
    
        """
        ...
    def applyMat(self, X: Mat, Y: Mat) -> None:
        """Apply the spectral transformation operator to a matrix.
    
        Collective.
    
        Apply the spectral transformation operator to a matrix, for instance
        :math:`Y=(A-\sigma B)^{-1}BX` in the case of the shift-and-invert
        transformation and generalized eigenproblem.
    
        Parameters
        ----------
        X
            The input matrix.
        Y
            The result matrix.
    
        See Also
        --------
        apply, slepc.STApplyMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:827 <slepc4py/SLEPc/ST.pyx#L827>`
    
        """
        ...
    def getOperator(self) -> Mat:
        """Get a shell matrix that represents the operator of the spectral transformation.
    
        Collective.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            Operator matrix.
    
        Notes
        -----
        The operator is defined in linear eigenproblems only, not in
        polynomial ones, so the call will fail if more than 2 matrices
        were passed in `setMatrices()`.
    
        The returned shell matrix is essentially a wrapper to the `apply()`
        and `applyTranspose()` operations. The operator can often be expressed as
    
        .. math::
    
           Op = D K^{-1} M D^{-1}
    
        where :math:`D` is the balancing matrix, and :math:`M` and :math:`K` are
        two matrices corresponding to the numerator and denominator for spectral
        transformations that represent a rational matrix function.
    
        The preconditioner matrix :math:`K` typically depends on the value of the
        shift, and its inverse is handled via an internal ``KSP`` object. Normal
        usage does not require explicitly calling `getOperator()`, but it can be
        used to force the creation of :math:`K` and :math:`M`, and then :math:`K`
        is passed to the ``KSP``. This is useful for setting options associated
        with the ``PCFactor`` (to set MUMPS options, for instance).
    
        The returned matrix must NOT be destroyed by the user. Instead, when no
        longer needed it must be returned with `restoreOperator()`. In particular,
        this is required before modifying the `ST` matrices or the shift.
    
        See Also
        --------
        apply, setMatrices, setShift, restoreOperator, slepc.STGetOperator
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:850 <slepc4py/SLEPc/ST.pyx#L850>`
    
        """
        ...
    def restoreOperator(self, op: Mat) -> None:
        """Restore the previously seized operator matrix.
    
        Logically collective.
    
        Parameters
        ----------
        op
            Operator matrix previously obtained with `getOperator()`.
    
        See Also
        --------
        getOperator, slepc.STRestoreOperator
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:898 <slepc4py/SLEPc/ST.pyx#L898>`
    
        """
        ...
    def setCayleyAntishift(self, mu: Scalar) -> None:
        """Set the value of the anti-shift for the Cayley spectral transformation.
    
        Logically collective.
    
        Parameters
        ----------
        mu
            The anti-shift.
    
        Notes
        -----
        In the generalized Cayley transform, the operator can be expressed as
        :math:`(A - \sigma B)^{-1}(A + \mu B)`. This function sets the value
        of :math:`mu`.  Use `setShift()` for setting :math:`\sigma`.
    
        See Also
        --------
        setShift, getCayleyAntishift, slepc.STCayleySetAntishift
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:918 <slepc4py/SLEPc/ST.pyx#L918>`
    
        """
        ...
    def getCayleyAntishift(self) -> Scalar:
        """Get the value of the anti-shift for the Cayley spectral transformation.
    
        Not collective.
    
        Returns
        -------
        Scalar
            The anti-shift.
    
        See Also
        --------
        setCayleyAntishift, slepc.STCayleyGetAntishift
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:942 <slepc4py/SLEPc/ST.pyx#L942>`
    
        """
        ...
    def setFilterType(self, filter_type: FilterType) -> None:
        """Set the method to be used to build the polynomial filter.
    
        Logically collective.
    
        Parameter
        ---------
        filter_type
            The type of filter.
    
        See Also
        --------
        getFilterType, slepc.STFilterSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:961 <slepc4py/SLEPc/ST.pyx#L961>`
    
        """
        ...
    def getFilterType(self) -> FilterType:
        """Get the method to be used to build the polynomial filter.
    
        Not collective.
    
        Returns
        -------
        FilterType
            The type of filter.
    
        See Also
        --------
        setFilterType, slepc.STFilterGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:979 <slepc4py/SLEPc/ST.pyx#L979>`
    
        """
        ...
    def setFilterInterval(self, inta: float, intb: float) -> None:
        """Set the interval containing the desired eigenvalues.
    
        Logically collective.
    
        Parameters
        ----------
        inta
            The left end of the interval.
        intb
            The right end of the interval.
    
        Notes
        -----
        The filter will be configured to emphasize eigenvalues contained
        in the given interval, and damp out eigenvalues outside it. If the
        interval is open, then the filter is low- or high-pass, otherwise
        it is mid-pass.
    
        Common usage is to set the interval in `EPS` with `EPS.setInterval()`.
    
        The interval must be contained within the numerical range of the
        matrix, see `setFilterRange()`.
    
        See Also
        --------
        getFilterInterval, setFilterRange, slepc.STFilterSetInterval
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:998 <slepc4py/SLEPc/ST.pyx#L998>`
    
        """
        ...
    def getFilterInterval(self) -> tuple[float, float]:
        """Get the interval containing the desired eigenvalues.
    
        Not collective.
    
        Returns
        -------
        inta: float
            The left end of the interval.
        intb: float
            The right end of the interval.
    
        See Also
        --------
        setFilterInterval, slepc.STFilterGetInterval
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1031 <slepc4py/SLEPc/ST.pyx#L1031>`
    
        """
        ...
    def setFilterRange(self, left: float, right: float) -> None:
        """Set the numerical range (or field of values) of the matrix.
    
        Logically collective.
    
        Set the numerical range (or field of values) of the matrix, that is,
        the interval containing all eigenvalues.
    
        Parameters
        ----------
        left
            The left end of the spectral range.
        right
            The right end of the spectral range.
    
        Notes
        -----
        The filter will be most effective if the numerical range is tight,
        that is, ``left`` and ``right`` are good approximations to the
        leftmost and rightmost eigenvalues, respectively.
    
        See Also
        --------
        setFilterInterval, getFilterRange, slepc.STFilterSetRange
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1053 <slepc4py/SLEPc/ST.pyx#L1053>`
    
        """
        ...
    def getFilterRange(self) -> tuple[float, float]:
        """Get the interval containing all eigenvalues.
    
        Not collective.
    
        Returns
        -------
        left: float
            The left end of the spectral range.
        right: float
            The right end of the spectral range.
    
        See Also
        --------
        getFilterInterval, slepc.STFilterGetRange
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1083 <slepc4py/SLEPc/ST.pyx#L1083>`
    
        """
        ...
    def setFilterDegree(self, deg: int) -> None:
        """Set the degree of the filter polynomial.
    
        Logically collective.
    
        Parameters
        ----------
        deg
            The polynomial degree.
    
        See Also
        --------
        getFilterDegree, slepc.STFilterSetDegree
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1105 <slepc4py/SLEPc/ST.pyx#L1105>`
    
        """
        ...
    def getFilterDegree(self) -> int:
        """Get the degree of the filter polynomial.
    
        Not collective.
    
        Returns
        -------
        int
            The polynomial degree.
    
        See Also
        --------
        setFilterDegree, slepc.STFilterGetDegree
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1123 <slepc4py/SLEPc/ST.pyx#L1123>`
    
        """
        ...
    def setFilterDamping(self, damping: FilterDamping) -> None:
        """Set the type of damping to be used in the polynomial filter.
    
        Logically collective.
    
        Parameter
        ---------
        damping
            The type of damping.
    
        Notes
        -----
        Only used in `FilterType.CHEBYSHEV` filters.
    
        See Also
        --------
        getFilterDamping, slepc.STFilterSetDamping
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1142 <slepc4py/SLEPc/ST.pyx#L1142>`
    
        """
        ...
    def getFilterDamping(self) -> FilterDamping:
        """Get the type of damping used in the polynomial filter.
    
        Not collective.
    
        Returns
        -------
        FilterDamping
            The type of damping.
    
        See Also
        --------
        setFilterDamping, slepc.STFilterGetDamping
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1164 <slepc4py/SLEPc/ST.pyx#L1164>`
    
        """
        ...
    @property
    def shift(self) -> float:
        """Value of the shift.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1185 <slepc4py/SLEPc/ST.pyx#L1185>`
    
        """
        ...
    @property
    def transform(self) -> bool:
        """If the transformed matrices are computed.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1192 <slepc4py/SLEPc/ST.pyx#L1192>`
    
        """
        ...
    @property
    def mat_mode(self) -> STMatMode:
        """How the transformed matrices are being stored in the ST.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1199 <slepc4py/SLEPc/ST.pyx#L1199>`
    
        """
        ...
    @property
    def mat_structure(self) -> MatStructure:
        """Relation of the sparsity pattern of all ST matrices.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1206 <slepc4py/SLEPc/ST.pyx#L1206>`
    
        """
        ...
    @property
    def ksp(self) -> KSP:
        """KSP object associated with the spectral transformation.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/ST.pyx:1213 <slepc4py/SLEPc/ST.pyx#L1213>`
    
        """
        ...

class BV(Object):
    """Basis Vectors.
    
    The `BV` package provides the concept of a block of vectors that
    represent the basis of a subspace. It is a convenient way of handling
    a collection of vectors that often operate together, rather than
    working with an array of `petsc4py.PETSc.Vec`.
    
    """
    class Type:
        """BV type.
        
        - `MAT`: A `BV` stored as a dense `petsc.Mat`.
        - `SVEC`: A `BV` stored as a single `petsc.Vec`.
        - `VECS`: A `BV` stored as an array of independent `petsc.Vec`.
        - `CONTIGUOUS`: A `BV` stored as an array of `petsc.Vec`
          sharing a contiguous array of scalars.
        - `TENSOR`: A special `BV` represented in compact form as
          :math:`V = (I \otimes U) S`.
        
        See Also
        --------
        slepc.BVType
        
        """
        MAT: str = _def(str, 'MAT')  #: Object ``MAT`` of type :class:`str`
        SVEC: str = _def(str, 'SVEC')  #: Object ``SVEC`` of type :class:`str`
        VECS: str = _def(str, 'VECS')  #: Object ``VECS`` of type :class:`str`
        CONTIGUOUS: str = _def(str, 'CONTIGUOUS')  #: Object ``CONTIGUOUS`` of type :class:`str`
        TENSOR: str = _def(str, 'TENSOR')  #: Object ``TENSOR`` of type :class:`str`
    class OrthogType:
        """BV orthogonalization types.
        
        - `CGS`: Classical Gram-Schmidt.
        - `MGS`: Modified Gram-Schmidt.
        
        See Also
        --------
        slepc.BVOrthogType
        
        """
        CGS: int = _def(int, 'CGS')  #: Constant ``CGS`` of type :class:`int`
        MGS: int = _def(int, 'MGS')  #: Constant ``MGS`` of type :class:`int`
    class OrthogRefineType:
        """BV orthogonalization refinement types.
        
        - `IFNEEDED`: Reorthogonalize if a criterion is satisfied.
        - `NEVER`:    Never reorthogonalize.
        - `ALWAYS`:   Always reorthogonalize.
        
        See Also
        --------
        slepc.BVOrthogRefineType
        
        """
        IFNEEDED: int = _def(int, 'IFNEEDED')  #: Constant ``IFNEEDED`` of type :class:`int`
        NEVER: int = _def(int, 'NEVER')  #: Constant ``NEVER`` of type :class:`int`
        ALWAYS: int = _def(int, 'ALWAYS')  #: Constant ``ALWAYS`` of type :class:`int`
    class OrthogRefineType:
        """BV orthogonalization refinement types.
        
        - `IFNEEDED`: Reorthogonalize if a criterion is satisfied.
        - `NEVER`:    Never reorthogonalize.
        - `ALWAYS`:   Always reorthogonalize.
        
        See Also
        --------
        slepc.BVOrthogRefineType
        
        """
        IFNEEDED: int = _def(int, 'IFNEEDED')  #: Constant ``IFNEEDED`` of type :class:`int`
        NEVER: int = _def(int, 'NEVER')  #: Constant ``NEVER`` of type :class:`int`
        ALWAYS: int = _def(int, 'ALWAYS')  #: Constant ``ALWAYS`` of type :class:`int`
    class OrthogBlockType:
        """BV block-orthogonalization types.
        
        - `GS`:       Gram-Schmidt, column by column.
        - `CHOL`:     Cholesky QR method.
        - `TSQR`:     Tall-skinny QR method.
        - `TSQRCHOL`: Tall-skinny QR, but computing the triangular factor only.
        - `SVQB`:     SVQB method.
        
        See Also
        --------
        slepc.BVOrthogBlockType
        
        """
        GS: int = _def(int, 'GS')  #: Constant ``GS`` of type :class:`int`
        CHOL: int = _def(int, 'CHOL')  #: Constant ``CHOL`` of type :class:`int`
        TSQR: int = _def(int, 'TSQR')  #: Constant ``TSQR`` of type :class:`int`
        TSQRCHOL: int = _def(int, 'TSQRCHOL')  #: Constant ``TSQRCHOL`` of type :class:`int`
        SVQB: int = _def(int, 'SVQB')  #: Constant ``SVQB`` of type :class:`int`
    class OrthogBlockType:
        """BV block-orthogonalization types.
        
        - `GS`:       Gram-Schmidt, column by column.
        - `CHOL`:     Cholesky QR method.
        - `TSQR`:     Tall-skinny QR method.
        - `TSQRCHOL`: Tall-skinny QR, but computing the triangular factor only.
        - `SVQB`:     SVQB method.
        
        See Also
        --------
        slepc.BVOrthogBlockType
        
        """
        GS: int = _def(int, 'GS')  #: Constant ``GS`` of type :class:`int`
        CHOL: int = _def(int, 'CHOL')  #: Constant ``CHOL`` of type :class:`int`
        TSQR: int = _def(int, 'TSQR')  #: Constant ``TSQR`` of type :class:`int`
        TSQRCHOL: int = _def(int, 'TSQRCHOL')  #: Constant ``TSQRCHOL`` of type :class:`int`
        SVQB: int = _def(int, 'SVQB')  #: Constant ``SVQB`` of type :class:`int`
    class MatMultType:
        """BV mat-mult types.
        
        - `VECS`: Perform a matrix-vector multiply per each column.
        - `MAT`:  Carry out a Mat-Mat product with a dense matrix.
        
        See Also
        --------
        slepc.BVMatMultType
        
        """
        VECS: int = _def(int, 'VECS')  #: Constant ``VECS`` of type :class:`int`
        MAT: int = _def(int, 'MAT')  #: Constant ``MAT`` of type :class:`int`
    class SVDMethod:
        """BV methods for computing the SVD.
        
        - `REFINE`: Based on the SVD of the cross product matrix :math:`S^* S`,
          with refinement.
        - `QR`:     Based on the SVD of the triangular factor of qr(S).
        - `QR_CAA`: Variant of QR intended for use in communication-avoiding.
          Arnoldi.
        
        See Also
        --------
        slepc.BVSVDMethod
        
        """
        REFINE: int = _def(int, 'REFINE')  #: Constant ``REFINE`` of type :class:`int`
        QR: int = _def(int, 'QR')  #: Constant ``QR`` of type :class:`int`
        QR_CAA: int = _def(int, 'QR_CAA')  #: Constant ``QR_CAA`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the BV data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.BVView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:192 <slepc4py/SLEPc/BV.pyx#L192>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the BV object.
    
        Collective.
    
        See Also
        --------
        slepc.BVDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:211 <slepc4py/SLEPc/BV.pyx#L211>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the BV object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator; if not provided, it defaults to all
            processes.
    
        See Also
        --------
        createFromMat, slepc.BVCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:225 <slepc4py/SLEPc/BV.pyx#L225>`
    
        """
        ...
    def createFromMat(self, A: Mat) -> Self:
        """Create a basis vectors object from a dense matrix.
    
        Collective.
    
        Parameters
        ----------
        A
            A dense tall-skinny matrix.
    
        Notes
        -----
        The matrix values are copied to the `BV` data storage, memory is not
        shared.
    
        The communicator of the `BV` object will be the same as `A`, and so
        will be the dimensions.
    
        See Also
        --------
        create, createMat, slepc.BVCreateFromMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:247 <slepc4py/SLEPc/BV.pyx#L247>`
    
        """
        ...
    def createMat(self) -> Mat:
        """Create a new dense matrix and copy the contents of the BV.
    
        Collective.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            The new matrix.
    
        Notes
        -----
        The matrix contains all columns of the `BV`, not just the active
        columns.
    
        See Also
        --------
        createFromMat, createVec, getMat, slepc.BVCreateMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:275 <slepc4py/SLEPc/BV.pyx#L275>`
    
        """
        ...
    def duplicate(self) -> BV:
        """Duplicate the BV object with the same type and dimensions.
    
        Collective.
    
        Returns
        -------
        BV
            The new object.
    
        Notes
        -----
        This function does not copy the entries, it just allocates the
        storage for the new `BV`. Use `copy()` to copy the content.
    
        See Also
        --------
        duplicateResize, slepc.BVDuplicate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:299 <slepc4py/SLEPc/BV.pyx#L299>`
    
        """
        ...
    def duplicateResize(self, m: int) -> BV:
        """Create a BV object of the same type and dimensions as an existing one.
    
        Collective.
    
        Parameters
        ----------
        m
            The number of columns.
    
        Returns
        -------
        BV
            The new object.
    
        Notes
        -----
        This is equivalent to a call to `duplicate()` followed by `resize()`
        with possibly different number of columns.
        The contents of this `BV` are not copied to the new one.
    
        See Also
        --------
        duplicate, resize, slepc.BVDuplicateResize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:323 <slepc4py/SLEPc/BV.pyx#L323>`
    
        """
        ...
    def copy(self, result: BV | None = None) -> BV:
        """Copy a basis vector object into another one.
    
        Logically collective.
    
        Returns
        -------
        BV
            The copy.
    
        Parameters
        ----------
        result
            The copy.
    
        Notes
        -----
        Both objects must be distributed in the same manner; local copies are
        done. Only active columns (excluding the leading ones) are copied.
        In the destination BV, columns are overwritten starting from the
        leading ones. Constraints are not copied.
    
        See Also
        --------
        slepc.BVCopy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:354 <slepc4py/SLEPc/BV.pyx#L354>`
    
        """
        ...
    def setType(self, bv_type: Type | str) -> None:
        """Set the type for the BV object.
    
        Logically collective.
    
        Parameters
        ----------
        bv_type
            The basis vectors type to be used.
    
        See Also
        --------
        getType, slepc.BVSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:388 <slepc4py/SLEPc/BV.pyx#L388>`
    
        """
        ...
    def getType(self) -> str:
        """Get the BV type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The basis vectors type currently being used.
    
        See Also
        --------
        setType, slepc.BVGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:407 <slepc4py/SLEPc/BV.pyx#L407>`
    
        """
        ...
    def setSizes(self, sizes: LayoutSizeSpec, m: int) -> None:
        """Set the local and global sizes, and the number of columns.
    
        Collective.
    
        Parameters
        ----------
        sizes
            The global size ``N`` or a two-tuple ``(n, N)``
            with the local and global sizes.
        m
            The number of columns.
    
        Notes
        -----
        Either ``n`` or ``N`` (but not both) can be `DETERMINE`
        or ``None`` to have it automatically set.
    
        See Also
        --------
        setSizesFromVec, getSizes, slepc.BVSetSizes
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:426 <slepc4py/SLEPc/BV.pyx#L426>`
    
        """
        ...
    def setSizesFromVec(self, w: Vec, m: int) -> None:
        """Set the local and global sizes, and the number of columns.
    
        Collective.
    
        Local and global sizes are specified indirectly by passing a template
        vector.
    
        Parameters
        ----------
        w
            The template vector.
        m
            The number of columns.
    
        See Also
        --------
        setSizes, getSizes, slepc.BVSetSizesFromVec
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:454 <slepc4py/SLEPc/BV.pyx#L454>`
    
        """
        ...
    def getSizes(self) -> tuple[LayoutSizeSpec, int]:
        """Get the local and global sizes, and the number of columns.
    
        Not collective.
    
        Returns
        -------
        (n, N): tuple of int
            The local and global sizes.
        m: int
            The number of columns.
    
        See Also
        --------
        setSizes, setSizesFromVec, slepc.BVGetSizes
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:477 <slepc4py/SLEPc/BV.pyx#L477>`
    
        """
        ...
    def setLeadingDimension(self, ld: int) -> None:
        """Set the leading dimension.
    
        Not collective.
    
        Parameters
        ----------
        ld
            The leading dimension.
    
        Notes
        -----
        This parameter is relevant for a BV of `BV.Type.MAT`.
    
        See Also
        --------
        getLeadingDimension, slepc.BVSetLeadingDimension
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:498 <slepc4py/SLEPc/BV.pyx#L498>`
    
        """
        ...
    def getLeadingDimension(self) -> int:
        """Get the leading dimension.
    
        Not collective.
    
        Returns
        -------
        int
            The leading dimension.
    
        Notes
        -----
        The returned value may be different in different processes.
    
        The leading dimension must be used when accessing the internal
        array via `getArray()`.
    
        See Also
        --------
        setLeadingDimension, slepc.BVGetLeadingDimension
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:520 <slepc4py/SLEPc/BV.pyx#L520>`
    
        """
        ...
    def getArray(self, readonly: bool = False) -> ArrayScalar:
        """Return the array where the data is stored.
    
        Not collective.
    
        Parameters
        ----------
        readonly
            Enable to obtain a read only array.
    
        Returns
        -------
        ArrayScalar
            The array.
    
        See Also
        --------
        slepc.BVGetArray, slepc.BVGetArrayRead
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:546 <slepc4py/SLEPc/BV.pyx#L546>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all BV options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all BV option requests.
    
        Notes
        -----
        A hyphen (``-``) must NOT be given at the beginning of the
        prefix name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.BVGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:593 <slepc4py/SLEPc/BV.pyx#L593>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all BV options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all BV option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.BVAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:618 <slepc4py/SLEPc/BV.pyx#L618>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all BV options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this BV object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.BVGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:637 <slepc4py/SLEPc/BV.pyx#L637>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set BV options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help``
        option.
    
        See Also
        --------
        setOptionsPrefix, slepc.BVSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:656 <slepc4py/SLEPc/BV.pyx#L656>`
    
        """
        ...
    def getOrthogonalization(self) -> tuple[OrthogType, OrthogRefineType, float, OrthogBlockType]:
        """Get the orthogonalization settings from the BV object.
    
        Not collective.
    
        Returns
        -------
        type: OrthogType
            The type of orthogonalization technique.
        refine: OrthogRefineType
            The type of refinement.
        eta: float
            Parameter for selective refinement (used when the
            refinement type is `IFNEEDED`).
        block: OrthogBlockType
            The type of block orthogonalization.
    
        See Also
        --------
        setOrthogonalization, slepc.BVGetOrthogonalization
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:675 <slepc4py/SLEPc/BV.pyx#L675>`
    
        """
        ...
    def setOrthogonalization(self, otype: OrthogType | None = None, refine: OrthogRefineType | None = None, eta: float | None = None, block: OrthogBlockType | None = None) -> None:
        """Set the method used for the (block-)orthogonalization of vectors.
    
        Logically collective.
    
        Ortogonalization of vectors (classical or modified Gram-Schmidt
        with or without refinement), and for the block-orthogonalization
        (simultaneous orthogonalization of a set of vectors).
    
        Parameters
        ----------
        otype
            The type of orthogonalization technique.
        refine
            The type of refinement.
        eta
            Parameter for selective refinement.
        block
            The type of block orthogonalization.
    
        Notes
        -----
        The default settings work well for most problems.
    
        The parameter ``eta`` should be a real value between ``0`` and
        ``1`` (or `DETERMINE`).  The value of ``eta`` is used only when
        the refinement type is `IFNEEDED`.
    
        When using several processes, `MGS` is likely to result in bad
        scalability.
    
        If the method set for block orthogonalization is `GS`, then the
        computation is done column by column with the vector orthogonalization.
    
        See Also
        --------
        getOrthogonalization, slepc.BVSetOrthogonalization
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:704 <slepc4py/SLEPc/BV.pyx#L704>`
    
        """
        ...
    def getMatMultMethod(self) -> MatMultType:
        """Get the method used for the `matMult()` operation.
    
        Not collective.
    
        Returns
        -------
        MatMultType
            The method for the `matMult()` operation.
    
        See Also
        --------
        matMult, setMatMultMethod, slepc.BVGetMatMultMethod
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:760 <slepc4py/SLEPc/BV.pyx#L760>`
    
        """
        ...
    def setMatMultMethod(self, method: MatMultType) -> None:
        """Set the method used for the `matMult()` operation.
    
        Logically collective.
    
        Parameters
        ----------
        method
            The method for the `matMult()` operation.
    
        See Also
        --------
        matMult, getMatMultMethod, slepc.BVSetMatMultMethod
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:779 <slepc4py/SLEPc/BV.pyx#L779>`
    
        """
        ...
    def getMatrix(self) -> tuple[Mat, bool] | tuple[None, bool]:
        """Get the matrix representation of the inner product.
    
        Not collective.
    
        Returns
        -------
        B: petsc4py.PETSc.Mat
            The matrix of the inner product.
        indef: bool
            Whether the matrix is indefinite.
    
        See Also
        --------
        setMatrix, slepc.BVGetMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:799 <slepc4py/SLEPc/BV.pyx#L799>`
    
        """
        ...
    def setMatrix(self, B: Mat | None, indef: bool = False) -> None:
        """Set the bilinear form to be used for inner products.
    
        Collective.
    
        Parameters
        ----------
        B
            The matrix of the inner product.
        indef
            Whether the matrix is indefinite.
    
        Notes
        -----
        This is used to specify a non-standard inner product, whose matrix
        representation is given by ``B``. Then, all inner products required
        during orthogonalization are computed as :math:`(x,y)_B=y^*Bx` rather
        than the standard form :math:`(x,y)=y^*x`.
    
        Matrix ``B`` must be real symmetric (or complex Hermitian). A genuine
        inner product requires that ``B`` is also positive (semi-)definite.
        However, we also allow for an indefinite ``B`` (setting ``indef=True``),
        in which case the orthogonalization uses an indefinite inner product.
    
        This affects operations `dot()`, `norm()`, `orthogonalize()`, and
        variants.
    
        Omitting ``B`` has the same effect as if the identity matrix was passed.
    
        See Also
        --------
        getMatrix, slepc.BVSetMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:825 <slepc4py/SLEPc/BV.pyx#L825>`
    
        """
        ...
    def applyMatrix(self, x: Vec, y: Vec) -> None:
        """Multiply a vector with the matrix associated to the bilinear form.
    
        Neighbor-wise collective.
    
        Parameters
        ----------
        x
            The input vector.
        y
            The result vector.
    
        Notes
        -----
        If the bilinear form has no associated matrix this function
        copies the vector.
    
        See Also
        --------
        setMatrix, slepc.BVApplyMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:863 <slepc4py/SLEPc/BV.pyx#L863>`
    
        """
        ...
    def setActiveColumns(self, l: int, k: int) -> None:
        """Set the columns that will be involved in operations.
    
        Logically collective.
    
        Parameters
        ----------
        l
            The leading number of columns.
        k
            The active number of columns.
    
        Notes
        -----
        In operations such as `mult()` or `dot()`, only the first ``k`` columns
        are considered. This is useful when the BV is filled from left to right,
        so the last ``m-k`` columns do not have relevant information.
    
        Also in operations such as `mult()` or `dot()`, the first ``l`` columns
        are normally not included in the computation.
    
        In orthogonalization operations, the first ``l`` columns are treated
        differently, they participate in the orthogonalization but the computed
        coefficients are not stored.
    
        Use `CURRENT` to leave any of the values unchanged. Use `DETERMINE`
        to set ``l`` to the minimum value (``0``) and ``k`` to the maximum (``m``).
    
        See Also
        --------
        getActiveColumns, setSizes, slepc.BVSetActiveColumns
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:887 <slepc4py/SLEPc/BV.pyx#L887>`
    
        """
        ...
    def getActiveColumns(self) -> tuple[int, int]:
        """Get the current active dimensions.
    
        Not collective.
    
        Returns
        -------
        l: int
            The leading number of columns.
        k: int
            The active number of columns.
    
        See Also
        --------
        setActiveColumns, slepc.BVGetActiveColumns
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:924 <slepc4py/SLEPc/BV.pyx#L924>`
    
        """
        ...
    def scaleColumn(self, j: int, alpha: Scalar) -> None:
        """Scale a column of a BV.
    
        Logically collective.
    
        Parameters
        ----------
        j
            column index to be scaled.
        alpha
            scaling factor.
    
        See Also
        --------
        scale, slepc.BVScaleColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:945 <slepc4py/SLEPc/BV.pyx#L945>`
    
        """
        ...
    def scale(self, alpha: Scalar) -> None:
        """Multiply the entries by a scalar value.
    
        Logically collective.
    
        Parameters
        ----------
        alpha
            scaling factor.
    
        Notes
        -----
        All active columns (except the leading ones) are scaled.
    
        See Also
        --------
        scaleColumn, setActiveColumns, slepc.BVScale
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:966 <slepc4py/SLEPc/BV.pyx#L966>`
    
        """
        ...
    def insertVec(self, j: int, w: Vec) -> None:
        """Insert a vector into the specified column.
    
        Logically collective.
    
        Parameters
        ----------
        j
            The column to be overwritten.
        w
            The vector to be copied.
    
        See Also
        --------
        insertVecs, slepc.BVInsertVec
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:988 <slepc4py/SLEPc/BV.pyx#L988>`
    
        """
        ...
    def insertVecs(self, s: int, W: Vec | list[Vec], orth: bool = False) -> int:
        """Insert a set of vectors into the specified columns.
    
        Collective.
    
        Parameters
        ----------
        s
            The first column to be overwritten.
        W
            Set of vectors to be copied.
        orth
            Flag indicating if the vectors must be orthogonalized.
    
        Returns
        -------
        int
            Number of linearly independent vectors.
    
        Notes
        -----
        Copies the contents of vectors ``W`` into the BV columns ``s:s+n``,
        where ``n`` is the length of ``W``. If ``orth`` is set, then the
        vectors are copied one by one and then orthogonalized against the
        previous one. If any of them is linearly dependent then it is
        discarded and the not counted in the return value.
    
        See Also
        --------
        insertVec, orthogonalizeColumn, slepc.BVInsertVecs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1008 <slepc4py/SLEPc/BV.pyx#L1008>`
    
        """
        ...
    def insertConstraints(self, C: Vec | list[Vec]) -> int:
        """Insert a set of vectors as constraints.
    
        Collective.
    
        Parameters
        ----------
        C
            Set of vectors to be inserted as constraints.
    
        Returns
        -------
        int
            Number of linearly independent constraints.
    
        Notes
        -----
        The constraints are relevant only during orthogonalization. Constraint
        vectors span a subspace that is deflated in every orthogonalization
        operation, so they are intended for removing those directions from the
        orthogonal basis computed in regular BV columns.
    
        Constraints are not stored in regular columns, but in a special part of
        the storage. They can be accessed with negative indices in
        `getColumn()`.
    
        This operation is DESTRUCTIVE, meaning that all data contained in the
        columns of the BV is lost. This is typically invoked just after creating
        the BV. Once a set of constraints has been set, it is not allowed to
        call this function again.
    
        The vectors are copied one by one and then orthogonalized against the
        previous ones. If any of them is linearly dependent then it is discarded
        and not counted in the return value. The behavior is similar to
        `insertVecs()`.
    
        See Also
        --------
        insertVecs, setNumConstraints, slepc.BVInsertConstraints
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1051 <slepc4py/SLEPc/BV.pyx#L1051>`
    
        """
        ...
    def setNumConstraints(self, nc: int) -> None:
        """Set the number of constraints.
    
        Logically collective.
    
        Parameters
        ----------
        nc
            The number of constraints.
        Notes
        -----
        This function sets the number of constraints to ``nc`` and marks all
        remaining columns as regular. Normal usage would be to call
        `insertConstraints()` instead.
    
        If ``nc`` is smaller than the previously set value, then some of the
        constraints are discarded. In particular, using ``nc=0`` removes all
        constraints preserving the content of regular columns.
    
        See Also
        --------
        insertConstraints, getNumConstraints, slepc.BVSetNumConstraints
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1101 <slepc4py/SLEPc/BV.pyx#L1101>`
    
        """
        ...
    def getNumConstraints(self) -> int:
        """Get the number of constraints.
    
        Not collective.
    
        Returns
        -------
        int
            The number of constraints.
    
        See Also
        --------
        insertConstraints, setNumConstraints, slepc.BVGetNumConstraints
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1128 <slepc4py/SLEPc/BV.pyx#L1128>`
    
        """
        ...
    def createVec(self) -> Vec:
        """Create a vector with the type and dimensions of the columns of the BV.
    
        Collective.
    
        Returns
        -------
        petsc4py.PETSc.Vec
            New vector.
    
        See Also
        --------
        createMat, setVecType, slepc.BVCreateVec
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1147 <slepc4py/SLEPc/BV.pyx#L1147>`
    
        """
        ...
    def setVecType(self, vec_type: petsc4py.PETSc.Vec.Type | str) -> None:
        """Set the vector type to be used when creating vectors via `createVec()`.
    
        Collective.
    
        Parameters
        ----------
        vec_type
            Vector type used when creating vectors with `createVec`.
    
        Notes
        -----
        This is not needed if the BV object is set up with `setSizesFromVec()`,
        but may be required in the case of `setSizes()` if one wants to work
        with non-standard vectors.
    
        See Also
        --------
        createVec, getVecType, setSizes, setSizesFromVec, slepc.BVSetVecType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1166 <slepc4py/SLEPc/BV.pyx#L1166>`
    
        """
        ...
    def getVecType(self) -> str:
        """Get the vector type used when creating vectors via `createVec()`.
    
        Not collective.
    
        Returns
        -------
        str
            The vector type.
    
        See Also
        --------
        createVec, setVecType, slepc.BVGetVecType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1191 <slepc4py/SLEPc/BV.pyx#L1191>`
    
        """
        ...
    def copyVec(self, j: int, v: Vec) -> None:
        """Copy one of the columns of a basis vectors object into a vector.
    
        Logically collective.
    
        Parameters
        ----------
        j
            The column index to be copied.
        v
            A vector.
    
        Notes
        -----
        The BV and ``v`` must be distributed in the same manner; local copies
        are done.
    
        See Also
        --------
        copy, copyColumn, slepc.BVCopyVec
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1210 <slepc4py/SLEPc/BV.pyx#L1210>`
    
        """
        ...
    def copyColumn(self, j: int, i: int) -> None:
        """Copy the values from one of the columns to another one.
    
        Logically collective.
    
        Parameters
        ----------
        j
            The index of the source column.
        i
            The index of the destination column.
    
        See Also
        --------
        copy, copyVec, slepc.BVCopyColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1235 <slepc4py/SLEPc/BV.pyx#L1235>`
    
        """
        ...
    def setDefiniteTolerance(self, deftol: float) -> None:
        """Set the tolerance to be used when checking a definite inner product.
    
        Logically collective.
    
        Parameters
        ----------
        deftol
            The tolerance.
    
        Notes
        -----
        When using a non-standard inner product, see `setMatrix()`, the solver
        needs to compute :math:`\sqrt{z^*B z}` for various vectors :math:`z`.
        If the inner product has not been declared indefinite, the value
        :math:`z^*B z` must be positive, but due to rounding error a tiny value
        may become negative. A tolerance is used to detect this situation.
        Likewise, in complex arithmetic :math:`z^*B z` should be real, and we
        use the same tolerance to check whether a nonzero imaginary part can be
        considered negligible.
    
        See Also
        --------
        setMatrix, getDefiniteTolerance, slepc.BVSetDefiniteTolerance
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1256 <slepc4py/SLEPc/BV.pyx#L1256>`
    
        """
        ...
    def getDefiniteTolerance(self) -> float:
        """Get the tolerance to be used when checking a definite inner product.
    
        Not collective.
    
        Returns
        -------
        float
            The tolerance.
    
        See Also
        --------
        setDefiniteTolerance, slepc.BVGetDefiniteTolerance
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1285 <slepc4py/SLEPc/BV.pyx#L1285>`
    
        """
        ...
    def dotVec(self, v: Vec) -> ArrayScalar:
        """Dot products of a vector against all the column vectors of the BV.
    
        Collective.
    
        Parameters
        ----------
        v
            A vector.
    
        Returns
        -------
        ArrayScalar
            The computed values.
    
        Notes
        -----
        This is analogue to ``Vec.mDot()``, but using `BV` to represent a
        collection of vectors ``X``. The result is :math:`m = X^* v`, so
        :math:`m_i` is equal to :math:`x_j^* v`. Note that here :math:`X`
        is transposed as opposed to `dot()`.
    
        If a non-standard inner product has been specified with `setMatrix()`,
        then the result is :math:`m = X^* B v`.
    
        See Also
        --------
        dot, dotColumn, setMatrix, slepc.BVDotVec
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1304 <slepc4py/SLEPc/BV.pyx#L1304>`
    
        """
        ...
    def dotColumn(self, j: int) -> ArrayScalar:
        """Dot products of a column against all the column vectors of a BV.
    
        Collective.
    
        Parameters
        ----------
        j
            The index of the column.
    
        Returns
        -------
        ArrayScalar
            The computed values.
    
        Notes
        -----
        This operation is equivalent to `dotVec()` but it uses column ``j`` of
        the BV rather than taking a vector as an argument. The number of active
        columns of the BV is set to ``j`` before the computation, and restored
        afterwards. If the BV has leading columns specified, then these columns
        do not participate in the computation. Therefore, the length of the
        returned array will be ``j`` minus the number of leading columns.
    
        See Also
        --------
        dot, dotVec, slepc.BVDotColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1344 <slepc4py/SLEPc/BV.pyx#L1344>`
    
        """
        ...
    def getColumn(self, j: int) -> Vec:
        """Get a vector with the entries of the column of the BV object.
    
        Logically collective.
    
        Parameters
        ----------
        j
            The index of the requested column.
    
        Returns
        -------
        petsc4py.PETSc.Vec
            The vector containing the ``j``-th column.
    
        Notes
        -----
        Modifying the returned vector will change the BV entries as well.
    
        The returned vector must not be destroyed, `restoreColumn()` must be
        called when it is no longer needed. At most, two columns can be
        fetched, that is, this function can only be called twice before the
        corresponding `restoreColumn()` is invoked.
    
        A negative index ``j`` selects the ``i``-th constraint, where
        ``i=-j``. Constraints should not be modified.
    
        See Also
        --------
        restoreColumn, insertConstraints, slepc.BVGetColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1384 <slepc4py/SLEPc/BV.pyx#L1384>`
    
        """
        ...
    def restoreColumn(self, j: int, v: Vec) -> None:
        """Restore a column obtained with `getColumn()`.
    
        Logically collective.
    
        Parameters
        ----------
        j
            The index of the requested column.
        v
            The vector obtained with `getColumn()`.
    
        Notes
        -----
        The arguments must match the corresponding call to `getColumn()`.
    
        See Also
        --------
        getColumn, slepc.BVRestoreColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1422 <slepc4py/SLEPc/BV.pyx#L1422>`
    
        """
        ...
    def getMat(self) -> Mat:
        """Get a matrix of dense type that shares the memory of the BV object.
    
        Collective.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            The matrix.
    
        Notes
        -----
        The returned matrix contains only the active columns. If the content
        of the matrix is modified, these changes are also done in the BV
        object. The user must call `restoreMat()` when no longer needed.
    
        This operation implies a call to `getArray()`, which may result in
        data copies.
    
        See Also
        --------
        restoreMat, createMat, getArray, slepc.BVGetMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1447 <slepc4py/SLEPc/BV.pyx#L1447>`
    
        """
        ...
    def restoreMat(self, A: Mat) -> None:
        """Restore the matrix obtained with `getMat()`.
    
        Logically collective.
    
        Parameters
        ----------
        A
            The matrix obtained with `getMat()`.
    
        Notes
        -----
        A call to this function must match a previous call of `getMat()`.
        The effect is that the contents of the matrix are copied back to the
        BV internal data structures.
    
        See Also
        --------
        getMat, slepc.BVRestoreMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1476 <slepc4py/SLEPc/BV.pyx#L1476>`
    
        """
        ...
    def dot(self, Y: BV) -> Mat:
        """Compute the 'block-dot' product of two basis vectors objects.
    
        Collective.
    
        :math:`M = Y^* X` :math:`(m_{ij} = y_i^* x_j)` or
        :math:`M = Y^* B X`
    
        Parameters
        ----------
        Y
            Left basis vectors, can be the same as self, giving
            :math:`M = X^* X`.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            The resulting matrix.
    
        Notes
        -----
        This is the generalization of ``Vec.dot()`` for a collection of
        vectors, :math:`M = Y^* X`. The result is a matrix :math:`M` whose
        entry :math:`m_{ij}` is equal to :math:`y_i^* x_j`
        (where :math:`y_i^*` denotes the conjugate transpose of :math:`y_i`).
    
        :math:`X` and :math:`Y` can be the same object.
    
        If a non-standard inner product has been specified with `setMatrix()`,
        then the result is :math:`M = Y^* B X`. In this case, both
        :math:`X` and :math:`Y` must have the same associated matrix.
    
        Only rows (resp. columns) of :math:`M` starting from :math:`l_y` (resp.
        :math:`l_x`) are computed, where :math:`l_y` (resp. :math:`l_x`) is the
        number of leading columns of :math:`Y` (resp. :math:`X`).
    
        See Also
        --------
        dotVec, dotColumn, setActiveColumns, setMatrix, slepc.BVDot
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1500 <slepc4py/SLEPc/BV.pyx#L1500>`
    
        """
        ...
    def matProject(self, A: Mat | None, Y: BV) -> Mat:
        """Compute the projection of a matrix onto a subspace.
    
        Collective.
    
        :math:`M = Y^* A X`
    
        Parameters
        ----------
        A
            Matrix to be projected.
        Y
            Left basis vectors, can be the same as self, giving
            :math:`M = X^* A X`.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            Projection of the matrix ``A`` onto the subspace.
    
        Notes
        -----
        If ``A`` is ``None``, then it is assumed that the BV already
        contains :math:`AX`.
    
        This operation is similar to `dot()`, with important differences.
        The goal is to compute the matrix resulting from the orthogonal
        projection of ``A`` onto the subspace spanned by the columns of
        the BV, :math:`M = X^*AX`, or the oblique projection onto the BV
        along the second one ``Y``, :math:`M = Y^*AX`.
    
        A difference with respect to `dot()` is that the standard inner
        product is always used, regardless of a non-standard inner product
        being specified with `setMatrix()`.
    
        See Also
        --------
        dot, setActiveColumns, setMatrix, slepc.BVMatProject
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1549 <slepc4py/SLEPc/BV.pyx#L1549>`
    
        """
        ...
    def matMult(self, A: Mat, Y: BV | None = None) -> BV:
        """Compute the matrix-vector product for each column, :math:`Y = A V`.
    
        Neighbor-wise collective.
    
        Parameters
        ----------
        A
            The matrix.
    
        Returns
        -------
        BV
            The result.
    
        Notes
        -----
        Only active columns (excluding the leading ones) are processed.
        If ``Y`` is ``None`` a new BV is created.
    
        It is possible to choose whether the computation is done column by column
        or as a dense matrix-matrix product with `setMatMultMethod()`.
    
        See Also
        --------
        copy, matMultColumn, matMultTranspose, setMatMultMethod, slepc.BVMatMult
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1598 <slepc4py/SLEPc/BV.pyx#L1598>`
    
        """
        ...
    def matMultTranspose(self, A: Mat, Y: BV | None = None) -> BV:
        """Pre-multiplication with the transpose of a matrix.
    
        Neighbor-wise collective.
    
        :math:`Y = A^T V`.
    
        Parameters
        ----------
        A
            The matrix.
    
        Returns
        -------
        BV
            The result.
    
        Notes
        -----
        Only active columns (excluding the leading ones) are processed.
        If ``Y`` is ``None`` a new BV is created.
    
        See Also
        --------
        matMult, matMultTransposeColumn, slepc.BVMatMultTranspose
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1647 <slepc4py/SLEPc/BV.pyx#L1647>`
    
        """
        ...
    def matMultHermitianTranspose(self, A: Mat, Y: BV | None = None) -> BV:
        """Pre-multiplication with the conjugate transpose of a matrix.
    
        Neighbor-wise collective.
    
        :math:`Y = A^* V`.
    
        Parameters
        ----------
        A
            The matrix.
    
        Returns
        -------
        BV
            The result.
    
        Notes
        -----
        Only active columns (excluding the leading ones) are processed.
        If ``Y`` is ``None`` a new BV is created.
    
        See Also
        --------
        matMult, matMultHermitianTransposeColumn, slepc.BVMatMultHermitianTranspose
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1695 <slepc4py/SLEPc/BV.pyx#L1695>`
    
        """
        ...
    def matMultColumn(self, A: Mat, j: int) -> None:
        """Mat-vec product for a column, storing the result in the next column.
    
        Neighbor-wise collective.
    
        :math:`v_{j+1} = A v_j`.
    
        Parameters
        ----------
        A
            The matrix.
        j
            Index of column.
    
        See Also
        --------
        matMult, slepc.BVMatMultColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1743 <slepc4py/SLEPc/BV.pyx#L1743>`
    
        """
        ...
    def matMultTransposeColumn(self, A: Mat, j: int) -> None:
        """Transpose matrix-vector product for a specified column.
    
        Neighbor-wise collective.
    
        Store the result in the next column: :math:`v_{j+1} = A^T v_j`.
    
        Parameters
        ----------
        A
            The matrix.
        j
            Index of column.
    
        See Also
        --------
        matMultColumn, slepc.BVMatMultTransposeColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1765 <slepc4py/SLEPc/BV.pyx#L1765>`
    
        """
        ...
    def matMultHermitianTransposeColumn(self, A: Mat, j: int) -> None:
        """Conjugate-transpose matrix-vector product for a specified column.
    
        Neighbor-wise collective.
    
        Store the result in the next column: :math:`v_{j+1} = A^* v_j`.
    
        Parameters
        ----------
        A
            The matrix.
        j
            Index of column.
    
        See Also
        --------
        matMultColumn, slepc.BVMatMultHermitianTransposeColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1787 <slepc4py/SLEPc/BV.pyx#L1787>`
    
        """
        ...
    def mult(self, delta: Scalar, gamma: Scalar, X: BV, Q: Mat | None) -> None:
        """Compute :math:`Y = \gamma Y + \delta X Q`.
    
        Logically collective.
    
        Parameters
        ----------
        delta
            Coefficient that multiplies ``X``.
        gamma
            Coefficient that multiplies self (``Y``).
        X
            Input basis vectors.
        Q
            Input matrix, if not given the identity matrix is assumed.
    
        Notes
        -----
        ``X`` must be different from self (``Y``). The case ``X=Y`` can be
        addressed with `multInPlace()`.
    
        See Also
        --------
        multVec, multColumn, multInPlace, slepc.BVMult
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1809 <slepc4py/SLEPc/BV.pyx#L1809>`
    
        """
        ...
    def multInPlace(self, Q: Mat, s: int, e: int) -> None:
        """Update a set of vectors as :math:`V(:,s:e-1) = V Q(:,s:e-1)`.
    
        Logically collective.
    
        Parameters
        ----------
        Q
            A sequential dense matrix.
        s
            First column to be overwritten.
        e
            Last column to be overwritten.
    
        See Also
        --------
        mult, multVec, slepc.BVMultInPlace
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1840 <slepc4py/SLEPc/BV.pyx#L1840>`
    
        """
        ...
    def multColumn(self, delta: Scalar, gamma: Scalar, j: int, q: Sequence[Scalar]) -> None:
        """Compute :math:`y = \gamma y + \delta X q`.
    
        Logically collective.
    
        Compute :math:`y = \gamma y + \delta X q`, where
        :math:`y` is the ``j``-th column.
    
        Parameters
        ----------
        delta
            Coefficient that multiplies self (``X``).
        gamma
            Coefficient that multiplies :math:`y`.
        j
            The column index.
        q
            Input coefficients.
    
        See Also
        --------
        mult, multVec, multInPlace, slepc.BVMultColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1863 <slepc4py/SLEPc/BV.pyx#L1863>`
    
        """
        ...
    def multVec(self, delta: Scalar, gamma: Scalar, y: Vec, q: Sequence[Scalar]) -> None:
        """Compute :math:`y = \gamma y + \delta X q`.
    
        Logically collective.
    
        Parameters
        ----------
        delta
            Coefficient that multiplies self (``X``).
        gamma
            Coefficient that multiplies ``y``.
        y
            Input/output vector.
        q
            Input coefficients.
    
        See Also
        --------
        mult, multColumn, multInPlace, slepc.BVMultVec
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1898 <slepc4py/SLEPc/BV.pyx#L1898>`
    
        """
        ...
    def normColumn(self, j: int, norm_type: NormType | None = None) -> float:
        """Compute the vector norm of a selected column.
    
        Collective.
    
        Parameters
        ----------
        j
            Index of column.
        norm_type
            The norm type.
    
        Returns
        -------
        float
            The norm.
    
        Notes
        -----
        The norm of :math:`v_j` is computed (``NORM_1``, ``NORM_2``, or
        ``NORM_INFINITY``).
    
        If a non-standard inner product has been specified with `setMatrix()`,
        then the returned value is :math:`\sqrt{v_j^* B v_j}`,
        where :math:`B` is the inner product matrix (argument 'norm_type' is
        ignored).
    
        See Also
        --------
        norm, setMatrix, slepc.BVNormColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1929 <slepc4py/SLEPc/BV.pyx#L1929>`
    
        """
        ...
    def norm(self, norm_type: NormType | None = None) -> float:
        """Compute the matrix norm of the BV.
    
        Collective.
    
        Parameters
        ----------
        norm_type
            The norm type.
    
        Returns
        -------
        float
            The norm.
    
        Notes
        -----
        All active columns (except the leading ones) are considered as a
        matrix. The allowed norms are ``NORM_1``, ``NORM_FROBENIUS``, and
        ``NORM_INFINITY``.
    
        This operation fails if a non-standard inner product has been specified
        with `setMatrix()`.
    
        See Also
        --------
        normColumn, setMatrix, slepc.BVNorm
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:1967 <slepc4py/SLEPc/BV.pyx#L1967>`
    
        """
        ...
    def resize(self, m: int, copy: bool = True) -> None:
        """Change the number of columns.
    
        Collective.
    
        Parameters
        ----------
        m
            The new number of columns.
        copy
            A flag indicating whether current values should be kept.
    
        Notes
        -----
        Internal storage is reallocated. If ``copy`` is ``True``, then the
        contents are copied to the leading part of the new space.
    
        See Also
        --------
        setSizes, setSizesFromVec, slepc.BVResize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2002 <slepc4py/SLEPc/BV.pyx#L2002>`
    
        """
        ...
    def setRandom(self) -> None:
        """Set the active columns of the BV to random numbers.
    
        Logically collective.
    
        Notes
        -----
        All active columns (except the leading ones) are modified.
    
        See Also
        --------
        setRandomContext, setRandomColumn, setRandomNormal, slepc.BVSetRandom
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2028 <slepc4py/SLEPc/BV.pyx#L2028>`
    
        """
        ...
    def setRandomNormal(self) -> None:
        """Set the active columns of the BV to normal random numbers.
    
        Logically collective.
    
        Notes
        -----
        All active columns (except the leading ones) are modified.
    
        See Also
        --------
        setRandomContext, setRandom, setRandomSign, slepc.BVSetRandomNormal
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2044 <slepc4py/SLEPc/BV.pyx#L2044>`
    
        """
        ...
    def setRandomSign(self) -> None:
        """Set the entries of a BV to values 1 or -1 with equal probability.
    
        Logically collective.
    
        Notes
        -----
        All active columns (except the leading ones) are modified.
    
        See Also
        --------
        setRandomContext, setRandom, setRandomNormal, slepc.BVSetRandomSign
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2060 <slepc4py/SLEPc/BV.pyx#L2060>`
    
        """
        ...
    def setRandomColumn(self, j: int) -> None:
        """Set one column of the BV to random numbers.
    
        Logically collective.
    
        Parameters
        ----------
        j
            Column index to be set.
    
        See Also
        --------
        setRandomContext, setRandom, setRandomNormal, slepc.BVSetRandomColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2076 <slepc4py/SLEPc/BV.pyx#L2076>`
    
        """
        ...
    def setRandomCond(self, condn: float) -> None:
        """Set the columns of a BV to random numbers.
    
        Logically collective.
    
        The generated matrix has a prescribed condition number.
    
        Parameters
        ----------
        condn
            Condition number.
    
        See Also
        --------
        setRandomContext, setRandomSign, setRandomNormal, slepc.BVSetRandomCond
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2094 <slepc4py/SLEPc/BV.pyx#L2094>`
    
        """
        ...
    def setRandomContext(self, rnd: Random) -> None:
        """Set the `petsc4py.PETSc.Random` object associated with the BV.
    
        Collective.
    
        To be used in operations that need random numbers.
    
        Parameters
        ----------
        rnd
            The random number generator context.
    
        See Also
        --------
        getRandomContext, setRandom, setRandomColumn, slepc.BVSetRandomContext
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2114 <slepc4py/SLEPc/BV.pyx#L2114>`
    
        """
        ...
    def getRandomContext(self) -> Random:
        """Get the `petsc4py.PETSc.Random` object associated with the BV.
    
        Collective.
    
        Returns
        -------
        petsc4py.PETSc.Random
            The random number generator context.
    
        See Also
        --------
        setRandomContext, slepc.BVGetRandomContext
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2133 <slepc4py/SLEPc/BV.pyx#L2133>`
    
        """
        ...
    def orthogonalizeVec(self, v: Vec) -> tuple[float, bool]:
        """Orthogonalize a vector with respect to all active columns.
    
        Collective.
    
        Parameters
        ----------
        v
            Vector to be orthogonalized, modified on return.
    
        Returns
        -------
        norm: float
            The norm of the resulting vector.
        lindep: bool
            Flag indicating that refinement did not improve the
            quality of orthogonalization.
    
        Notes
        -----
        This function applies an orthogonal projector to project vector
        :math:`v` onto the orthogonal complement of the span of the columns
        of the BV.
    
        This routine does not normalize the resulting vector.
    
        See Also
        --------
        orthogonalizeColumn, setOrthogonalization slepc.BVOrthogonalizeVec
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2153 <slepc4py/SLEPc/BV.pyx#L2153>`
    
        """
        ...
    def orthogonalizeColumn(self, j: int) -> tuple[float, bool]:
        """Orthogonalize a column vector with respect to the previous ones.
    
        Collective.
    
        Parameters
        ----------
        j
            Index of the column to be orthogonalized.
    
        Returns
        -------
        norm: float
            The norm of the resulting vector.
        lindep: bool
            Flag indicating that refinement did not improve the
            quality of orthogonalization.
    
        Notes
        -----
        This function applies an orthogonal projector to project vector
        :math:`v_j` onto the orthogonal complement of the span of the columns
        :math:`V[0..j-1]`, where :math:`V[.]` are the vectors of the BV.
        The columns :math:`V[0..j-1]` are assumed to be mutually orthonormal.
    
        This routine does not normalize the resulting vector.
    
        See Also
        --------
        orthogonalizeVec, setOrthogonalization slepc.BVOrthogonalizeColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2189 <slepc4py/SLEPc/BV.pyx#L2189>`
    
        """
        ...
    def orthonormalizeColumn(self, j: int, replace: bool = False) -> tuple[float, bool]:
        """Orthonormalize a column vector with respect to the previous ones.
    
        Collective.
    
        This is equivalent to a call to `orthogonalizeColumn()` followed by a
        call to `scaleColumn()` with the reciprocal of the norm.
    
        Parameters
        ----------
        j
            Index of the column to be orthonormalized.
        replace
            Whether it is allowed to set the vector randomly.
    
        Returns
        -------
        norm: float
            The norm of the resulting vector.
        lindep: bool
            Flag indicating that refinement did not improve the
            quality of orthogonalization.
    
        See Also
        --------
        orthogonalizeColumn, setOrthogonalization slepc.BVOrthonormalizeColumn
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2227 <slepc4py/SLEPc/BV.pyx#L2227>`
    
        """
        ...
    def orthogonalize(self, R: Mat | None = None, **kargs: Any) -> None:
        """Orthogonalize all columns (except leading ones) (QR decomposition).
    
        Collective.
    
        Parameters
        ----------
        R
            A sequential dense matrix.
    
        Notes
        -----
        The output satisfies :math:`V_0 = V R` (where :math:`V_0` represent the
        input :math:`V`) and :math:`V^* V = I` (or :math:`V^*BV=I` if an inner
        product matrix :math:`B` has been specified with `setMatrix()`).
    
        See Also
        --------
        orthogonalizeColumn, setMatrix, setOrthogonalization, slepc.BVOrthogonalize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2263 <slepc4py/SLEPc/BV.pyx#L2263>`
    
        """
        ...
    @property
    def sizes(self) -> tuple[LayoutSizeSpec, int]:
        """Basis vectors local and global sizes, and the number of columns.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2290 <slepc4py/SLEPc/BV.pyx#L2290>`
    
        """
        ...
    @property
    def size(self) -> tuple[int, int]:
        """Basis vectors global size.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2295 <slepc4py/SLEPc/BV.pyx#L2295>`
    
        """
        ...
    @property
    def local_size(self) -> int:
        """Basis vectors local size.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2300 <slepc4py/SLEPc/BV.pyx#L2300>`
    
        """
        ...
    @property
    def column_size(self) -> int:
        """Basis vectors column size.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/BV.pyx:2305 <slepc4py/SLEPc/BV.pyx#L2305>`
    
        """
        ...

class DS(Object):
    """Direct Solver (or Dense System).
    
    The `DS` package provides auxiliary routines that are internally used by
    the different slepc4py solvers. It is used to represent low-dimensional
    eigenproblems that must be solved within iterative solvers with direct
    methods. It can be seen as a structured wrapper to LAPACK functionality.
    
    """
    class Type:
        """DS type.
        
        - `HEP`: Dense Hermitian Eigenvalue Problem.
        - `NHEP`: Dense Non-Hermitian Eigenvalue Problem.
        - `GHEP`: Dense Generalized Hermitian Eigenvalue Problem.
        - `GHIEP`: Dense Generalized Hermitian Indefinite Eigenvalue Problem.
        - `GNHEP`: Dense Generalized Non-Hermitian Eigenvalue Problem.
        - `NHEPTS`: Dense Non-Hermitian Eigenvalue Problem (special variant
          intended for two-sided Krylov solvers).
        - `SVD`: Dense Singular Value Decomposition.
        - `HSVD`: Dense Hyperbolic Singular Value Decomposition.
        - `GSVD`: Dense Generalized Singular Value Decomposition.
        - `PEP`: Dense Polynomial Eigenvalue Problem.
        - `NEP`: Dense Nonlinear Eigenvalue Problem.
        
        See Also
        --------
        slepc.DSType
        
        """
        HEP: str = _def(str, 'HEP')  #: Object ``HEP`` of type :class:`str`
        NHEP: str = _def(str, 'NHEP')  #: Object ``NHEP`` of type :class:`str`
        GHEP: str = _def(str, 'GHEP')  #: Object ``GHEP`` of type :class:`str`
        GHIEP: str = _def(str, 'GHIEP')  #: Object ``GHIEP`` of type :class:`str`
        GNHEP: str = _def(str, 'GNHEP')  #: Object ``GNHEP`` of type :class:`str`
        NHEPTS: str = _def(str, 'NHEPTS')  #: Object ``NHEPTS`` of type :class:`str`
        SVD: str = _def(str, 'SVD')  #: Object ``SVD`` of type :class:`str`
        HSVD: str = _def(str, 'HSVD')  #: Object ``HSVD`` of type :class:`str`
        GSVD: str = _def(str, 'GSVD')  #: Object ``GSVD`` of type :class:`str`
        PEP: str = _def(str, 'PEP')  #: Object ``PEP`` of type :class:`str`
        NEP: str = _def(str, 'NEP')  #: Object ``NEP`` of type :class:`str`
    class StateType:
        """DS state types.
        
        - `RAW`:          Not processed yet.
        - `INTERMEDIATE`: Reduced to Hessenberg or tridiagonal form (or equivalent).
        - `CONDENSED`:    Reduced to Schur or diagonal form (or equivalent).
        - `TRUNCATED`:    Condensed form truncated to a smaller size.
        
        See Also
        --------
        slepc.DSStateType
        
        """
        RAW: int = _def(int, 'RAW')  #: Constant ``RAW`` of type :class:`int`
        INTERMEDIATE: int = _def(int, 'INTERMEDIATE')  #: Constant ``INTERMEDIATE`` of type :class:`int`
        CONDENSED: int = _def(int, 'CONDENSED')  #: Constant ``CONDENSED`` of type :class:`int`
        TRUNCATED: int = _def(int, 'TRUNCATED')  #: Constant ``TRUNCATED`` of type :class:`int`
    class MatType:
        """To refer to one of the matrices stored internally in DS.
        
        - `A`:  first matrix of eigenproblem/singular value problem.
        - `B`:  second matrix of a generalized eigenproblem.
        - `C`:  third matrix of a quadratic eigenproblem.
        - `T`:  tridiagonal matrix.
        - `D`:  diagonal matrix.
        - `Q`:  orthogonal matrix of (right) Schur vectors.
        - `Z`:  orthogonal matrix of left Schur vectors.
        - `X`:  right eigenvectors.
        - `Y`:  left eigenvectors.
        - `U`:  left singular vectors.
        - `V`:  right singular vectors.
        - `W`:  workspace matrix.
        
        See Also
        --------
        slepc.DSMatType
        
        """
        A: int = _def(int, 'A')  #: Constant ``A`` of type :class:`int`
        B: int = _def(int, 'B')  #: Constant ``B`` of type :class:`int`
        C: int = _def(int, 'C')  #: Constant ``C`` of type :class:`int`
        T: int = _def(int, 'T')  #: Constant ``T`` of type :class:`int`
        D: int = _def(int, 'D')  #: Constant ``D`` of type :class:`int`
        Q: int = _def(int, 'Q')  #: Constant ``Q`` of type :class:`int`
        Z: int = _def(int, 'Z')  #: Constant ``Z`` of type :class:`int`
        X: int = _def(int, 'X')  #: Constant ``X`` of type :class:`int`
        Y: int = _def(int, 'Y')  #: Constant ``Y`` of type :class:`int`
        U: int = _def(int, 'U')  #: Constant ``U`` of type :class:`int`
        V: int = _def(int, 'V')  #: Constant ``V`` of type :class:`int`
        W: int = _def(int, 'W')  #: Constant ``W`` of type :class:`int`
    class ParallelType:
        """Indicates the parallel mode that the direct solver will use.
        
        - `REDUNDANT`:    Every process performs the computation redundantly.
        - `SYNCHRONIZED`: The first process sends the result to the rest.
        - `DISTRIBUTED`:  Used in some cases to distribute the computation among
          processes.
        
        See Also
        --------
        slepc.DSParallelType
        
        """
        REDUNDANT: int = _def(int, 'REDUNDANT')  #: Constant ``REDUNDANT`` of type :class:`int`
        SYNCHRONIZED: int = _def(int, 'SYNCHRONIZED')  #: Constant ``SYNCHRONIZED`` of type :class:`int`
        DISTRIBUTED: int = _def(int, 'DISTRIBUTED')  #: Constant ``DISTRIBUTED`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the DS data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.DSView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:127 <slepc4py/SLEPc/DS.pyx#L127>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the DS object.
    
        Collective.
    
        See Also
        --------
        slepc.DSDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:146 <slepc4py/SLEPc/DS.pyx#L146>`
    
        """
        ...
    def reset(self) -> None:
        """Reset the DS object.
    
        Collective.
    
        See Also
        --------
        allocate, slepc.DSReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:160 <slepc4py/SLEPc/DS.pyx#L160>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the DS object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator; if not provided, it defaults to all processes.
    
        See Also
        --------
        duplicate, slepc.DSCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:172 <slepc4py/SLEPc/DS.pyx#L172>`
    
        """
        ...
    def setType(self, ds_type: Type | str) -> None:
        """Set the type for the DS object.
    
        Logically collective.
    
        Parameters
        ----------
        ds_type
            The direct solver type to be used.
    
        See Also
        --------
        getType, slepc.DSSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:193 <slepc4py/SLEPc/DS.pyx#L193>`
    
        """
        ...
    def getType(self) -> str:
        """Get the DS type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The direct solver type currently being used.
    
        See Also
        --------
        setType, slepc.DSGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:212 <slepc4py/SLEPc/DS.pyx#L212>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all DS options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all DS option requests.
    
        Notes
        -----
        A hyphen (``-``) must NOT be given at the beginning of the
        prefix name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.DSSetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:231 <slepc4py/SLEPc/DS.pyx#L231>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all DS options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all DS option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.DSSetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:256 <slepc4py/SLEPc/DS.pyx#L256>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all DS options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this DS object.
    
        See Also
        --------
        appendOptionsPrefix, setOptionsPrefix, slepc.DSSetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:275 <slepc4py/SLEPc/DS.pyx#L275>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set DS options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help``
        option.
    
        See Also
        --------
        setOptionsPrefix, slepc.DSSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:294 <slepc4py/SLEPc/DS.pyx#L294>`
    
        """
        ...
    def duplicate(self) -> DS:
        """Duplicate the DS object with the same type and dimensions.
    
        Collective.
    
        Returns
        -------
        DS
            The new object.
    
        Notes
        -----
        This method does not copy the matrices, and the new object does not
        even have internal arrays allocated. Use `allocate()` to use the new
        `DS`.
    
        See Also
        --------
        create, allocate, slepc.DSDuplicate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:311 <slepc4py/SLEPc/DS.pyx#L311>`
    
        """
        ...
    def allocate(self, ld: int) -> None:
        """Allocate memory for internal storage or matrices in DS.
    
        Logically collective.
    
        Parameters
        ----------
        ld
            Leading dimension (maximum allowed dimension for the
            matrices, including the extra row if present).
    
        Notes
        -----
        If the leading dimension is different from a previously set value, then
        all matrices are destroyed with `reset()`.
    
        See Also
        --------
        getLeadingDimension, setDimensions, setExtraRow, reset, slepc.DSAllocate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:338 <slepc4py/SLEPc/DS.pyx#L338>`
    
        """
        ...
    def getLeadingDimension(self) -> int:
        """Get the leading dimension of the allocated matrices.
    
        Not collective.
    
        Returns
        -------
        int
            Leading dimension (maximum allowed dimension for the matrices).
    
        See Also
        --------
        allocate, setDimensions, slepc.DSGetLeadingDimension
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:362 <slepc4py/SLEPc/DS.pyx#L362>`
    
        """
        ...
    def setState(self, state: StateType) -> None:
        """Set the state of the DS object.
    
        Logically collective.
    
        Parameters
        ----------
        state
            The new state.
    
        Notes
        -----
        The state indicates that the dense system is in an initial
        state (raw), in an intermediate state (such as tridiagonal,
        Hessenberg or Hessenberg-triangular), in a condensed state
        (such as diagonal, Schur or generalized Schur), or in a
        truncated state.
    
        The state is automatically changed in functions such as `solve()`
        or `truncate()`. This function is normally used to return to the
        raw state when the condensed structure is destroyed, or to indicate
        that `solve()` must start with a problem that already has an
        intermediate form.
    
        See Also
        --------
        getState, solve, truncate, slepc.DSSetState
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:381 <slepc4py/SLEPc/DS.pyx#L381>`
    
        """
        ...
    def getState(self) -> StateType:
        """Get the current state.
    
        Not collective.
    
        Returns
        -------
        StateType
            The current state.
    
        See Also
        --------
        setState, slepc.DSGetState
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:413 <slepc4py/SLEPc/DS.pyx#L413>`
    
        """
        ...
    def setParallel(self, pmode: ParallelType) -> None:
        """Set the mode of operation in parallel runs.
    
        Logically collective.
    
        Parameters
        ----------
        pmode
            The parallel mode.
    
        See Also
        --------
        getParallel, slepc.DSSetParallel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:432 <slepc4py/SLEPc/DS.pyx#L432>`
    
        """
        ...
    def getParallel(self) -> ParallelType:
        """Get the mode of operation in parallel runs.
    
        Not collective.
    
        Returns
        -------
        ParallelType
            The parallel mode.
    
        See Also
        --------
        setParallel, slepc.DSGetParallel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:450 <slepc4py/SLEPc/DS.pyx#L450>`
    
        """
        ...
    def setDimensions(self, n: int | None = None, l: int | None = None, k: int | None = None) -> None:
        """Set the matrix sizes in the DS object.
    
        Logically collective.
    
        Parameters
        ----------
        n
            The new size.
        l
            Number of locked (inactive) leading columns.
        k
            Intermediate dimension (e.g., position of arrow).
    
        Notes
        -----
        The internal arrays are not reallocated.
    
        Some `DS` types have additional dimensions, e.g., the number of columns
        in `DS.Type.SVD`. For these, you should call a specific interface
        function.
    
        See Also
        --------
        getDimensions, allocate, slepc.DSSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:469 <slepc4py/SLEPc/DS.pyx#L469>`
    
        """
        ...
    def getDimensions(self) -> tuple[int, int, int, int]:
        """Get the current dimensions.
    
        Not collective.
    
        Returns
        -------
        n: int
            The new size.
        l: int
            Number of locked (inactive) leading columns.
        k: int
            Intermediate dimension (e.g., position of arrow).
        t: int
            Truncated length.
    
        Notes
        -----
        The ``t`` value makes sense only if `truncate()` has been called.
        Otherwise it is equal to ``n``.
    
        See Also
        --------
        setDimensions, truncate, getLeadingDimension, slepc.DSGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:504 <slepc4py/SLEPc/DS.pyx#L504>`
    
        """
        ...
    def setBlockSize(self, bs: int) -> None:
        """Set the block size.
    
        Logically collective.
    
        Parameters
        ----------
        bs
            The block size.
    
        See Also
        --------
        getBlockSize, slepc.DSSetBlockSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:537 <slepc4py/SLEPc/DS.pyx#L537>`
    
        """
        ...
    def getBlockSize(self) -> int:
        """Get the block size.
    
        Not collective.
    
        Returns
        -------
        int
            The block size.
    
        See Also
        --------
        setBlockSize, slepc.DSGetBlockSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:555 <slepc4py/SLEPc/DS.pyx#L555>`
    
        """
        ...
    def setMethod(self, meth: int) -> None:
        """Set the method to be used to solve the problem.
    
        Logically collective.
    
        Parameters
        ----------
        meth
            An index identifying the method.
    
        See Also
        --------
        getMethod, slepc.DSSetMethod
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:574 <slepc4py/SLEPc/DS.pyx#L574>`
    
        """
        ...
    def getMethod(self) -> int:
        """Get the method currently used in the DS.
    
        Not collective.
    
        Returns
        -------
        int
            Identifier of the method.
    
        See Also
        --------
        setMethod, slepc.DSGetMethod
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:592 <slepc4py/SLEPc/DS.pyx#L592>`
    
        """
        ...
    def setCompact(self, comp: bool) -> None:
        """Set the compact flag for storage of matrices.
    
        Logically collective.
    
        Parameters
        ----------
        comp
            ``True`` means compact storage.
    
        Notes
        -----
        Compact storage is used in some `DS` types such as
        `DS.Type.HEP` when the matrix is tridiagonal. This flag
        can be used to indicate whether the user provides the
        matrix entries via the compact form (the tridiagonal
        `DS.MatType.T`) or the non-compact one (`DS.MatType.A`).
    
        The default is ``False``.
    
        See Also
        --------
        getCompact, slepc.DSSetCompact
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:611 <slepc4py/SLEPc/DS.pyx#L611>`
    
        """
        ...
    def getCompact(self) -> bool:
        """Get the compact storage flag.
    
        Not collective.
    
        Returns
        -------
        bool
            The flag.
    
        See Also
        --------
        setCompact, slepc.DSGetCompact
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:639 <slepc4py/SLEPc/DS.pyx#L639>`
    
        """
        ...
    def setExtraRow(self, ext: bool) -> None:
        """Set a flag to indicate that the matrix has one extra row.
    
        Logically collective.
    
        Parameters
        ----------
        ext
            ``True`` if the matrix has extra row.
    
        Notes
        -----
        In Krylov methods it is useful that the matrix representing the direct
        solver has one extra row, i.e., has :math:`(n+1)` rows and :math:`(n+1)`
        columns. If this flag is activated, all transformations applied to the
        right of the matrix also affect this additional row. In that case,
        :math:`(n+1)` must be less or equal than the leading dimension.
    
        The default is ``False``.
    
        See Also
        --------
        getExtraRow, solve, allocate, slepc.DSSetExtraRow
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:658 <slepc4py/SLEPc/DS.pyx#L658>`
    
        """
        ...
    def getExtraRow(self) -> bool:
        """Get the extra row flag.
    
        Not collective.
    
        Returns
        -------
        bool
            The flag.
    
        See Also
        --------
        setExtraRow, slepc.DSGetExtraRow
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:686 <slepc4py/SLEPc/DS.pyx#L686>`
    
        """
        ...
    def setRefined(self, ref: bool) -> None:
        """Set a flag to indicate that refined vectors must be computed.
    
        Logically collective.
    
        Parameters
        ----------
        ref
            ``True`` if refined vectors must be used.
    
        Notes
        -----
        Normally the vectors returned in `DS.MatType.X` are eigenvectors of
        the projected matrix. With this flag activated, `vectors()` will return
        the right singular vector of the smallest singular value of matrix
        :math:`\hat A - \eta I`, where :math:`\hat A` is the extended
        matrix (with extra row) and :math:`\eta` is the Ritz value.
        This is used in the refined Ritz approximation.
    
        The default is ``False``.
    
        See Also
        --------
        getRefined, vectors, setExtraRow, slepc.DSSetRefined
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:705 <slepc4py/SLEPc/DS.pyx#L705>`
    
        """
        ...
    def getRefined(self) -> bool:
        """Get the refined vectors flag.
    
        Not collective.
    
        Returns
        -------
        bool
            The flag.
    
        See Also
        --------
        setRefined, slepc.DSGetRefined
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:734 <slepc4py/SLEPc/DS.pyx#L734>`
    
        """
        ...
    def truncate(self, n: int, trim: bool = False) -> None:
        """Truncate the system represented in the DS object.
    
        Logically collective.
    
        Parameters
        ----------
        n
            The new size.
        trim
            A flag to indicate if the factorization must be trimmed.
    
        See Also
        --------
        setDimensions, setExtraRow, slepc.DSTruncate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:753 <slepc4py/SLEPc/DS.pyx#L753>`
    
        """
        ...
    def updateExtraRow(self) -> None:
        """Ensure that the extra row gets up-to-date after a call to `DS.solve()`.
    
        Logically collective.
    
        Perform all necessary operations so that the extra row gets up-to-date
        after a call to `DS.solve()`.
    
        See Also
        --------
        slepc.DSUpdateExtraRow
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:774 <slepc4py/SLEPc/DS.pyx#L774>`
    
        """
        ...
    def getMat(self, matname: MatType) -> Mat:
        """Get the requested matrix as a sequential dense ``Mat`` object.
    
        Not collective.
    
        Parameters
        ----------
        matname
            The requested matrix.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            The matrix.
    
        Notes
        -----
        The returned matrix has sizes equal to the current `DS` dimensions
        (see `setDimensions()`), and contains the values that would be
        obtained with `getArray()`. If the `DS` was truncated, then the number
        of rows is equal to the dimension prior to truncation, see `truncate()`.
    
        When no longer needed the user must call `restoreMat()`.
    
        See Also
        --------
        restoreMat, setDimensions, getArray, truncate, slepc.DSGetMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:789 <slepc4py/SLEPc/DS.pyx#L789>`
    
        """
        ...
    def restoreMat(self, matname: MatType, mat: petsc4py.PETSc.Mat) -> None:
        """Restore the previously seized matrix.
    
        Not collective.
    
        Parameters
        ----------
        matname
            The selected matrix.
        mat
            The matrix previously obtained with `getMat()`.
    
        See Also
        --------
        getMat, slepc.DSRestoreMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:824 <slepc4py/SLEPc/DS.pyx#L824>`
    
        """
        ...
    def getArray(self, matname: MatType) -> ArrayScalar:
        """Return the array where the data is stored.
    
        Not collective.
    
        Parameters
        ----------
        matname
            The selected matrix.
    
        Returns
        -------
        ArrayScalar
            The array.
    
        See Also
        --------
        slepc.DSGetArray
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:845 <slepc4py/SLEPc/DS.pyx#L845>`
    
        """
        ...
    def setIdentity(self, matname: MatType) -> None:
        """Set the identity on the active part of a matrix.
    
        Logically collective.
    
        Parameters
        ----------
        matname
            The matrix to be changed.
    
        See Also
        --------
        slepc.DSSetIdentity
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:885 <slepc4py/SLEPc/DS.pyx#L885>`
    
        """
        ...
    def cond(self) -> float:
        """Compute the inf-norm condition number of the first matrix.
    
        Logically collective.
    
        Returns
        -------
        float
            Condition number.
    
        See Also
        --------
        slepc.DSCond
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:905 <slepc4py/SLEPc/DS.pyx#L905>`
    
        """
        ...
    def solve(self) -> ArrayScalar:
        """Solve the problem.
    
        Logically collective.
    
        Returns
        -------
        ArrayScalar
            Eigenvalues or singular values.
    
        See Also
        --------
        slepc.DSSolve
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:924 <slepc4py/SLEPc/DS.pyx#L924>`
    
        """
        ...
    def vectors(self, matname=MatType.X) -> None:
        """Compute vectors associated to the dense system such as eigenvectors.
    
        Logically collective.
    
        Parameters
        ----------
        matname
           The matrix, used to indicate which vectors are required.
    
        See Also
        --------
        slepc.DSVectors
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:952 <slepc4py/SLEPc/DS.pyx#L952>`
    
        """
        ...
    def setSVDDimensions(self, m: int) -> None:
        """Set the number of columns of a `DS` of type `SVD`.
    
        Logically collective.
    
        Parameters
        ----------
        m
            The number of columns.
    
        Notes
        -----
        This call is complementary to `setDimensions()`, to provide a dimension
        that is specific to this `DS.Type`.
    
        See Also
        --------
        setDimensions, getSVDDimensions, slepc.DSSVDSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:972 <slepc4py/SLEPc/DS.pyx#L972>`
    
        """
        ...
    def getSVDDimensions(self) -> int:
        """Get the number of columns of a `DS` of type `SVD`.
    
        Not collective.
    
        Returns
        -------
        int
            The number of columns.
    
        See Also
        --------
        setSVDDimensions, slepc.DSSVDGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:995 <slepc4py/SLEPc/DS.pyx#L995>`
    
        """
        ...
    def setHSVDDimensions(self, m: int) -> None:
        """Set the number of columns of a `DS` of type `HSVD`.
    
        Logically collective.
    
        Parameters
        ----------
        m
            The number of columns.
    
        Notes
        -----
        This call is complementary to `setDimensions()`, to provide a dimension
        that is specific to this `DS.Type`.
    
        See Also
        --------
        setDimensions, getHSVDDimensions, slepc.DSHSVDSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1014 <slepc4py/SLEPc/DS.pyx#L1014>`
    
        """
        ...
    def getHSVDDimensions(self) -> int:
        """Get the number of columns of a `DS` of type `HSVD`.
    
        Not collective.
    
        Returns
        -------
        int
            The number of columns.
    
        See Also
        --------
        setHSVDDimensions, slepc.DSHSVDGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1037 <slepc4py/SLEPc/DS.pyx#L1037>`
    
        """
        ...
    def setGSVDDimensions(self, m: int, p: int) -> None:
        """Set the number of columns and rows of a `DS` of type `GSVD`.
    
        Logically collective.
    
        Parameters
        ----------
        m
            The number of columns.
        p
            The number of rows for the second matrix.
    
        Notes
        -----
        This call is complementary to `setDimensions()`, to provide dimensions
        that are specific to this `DS.Type`.
    
        See Also
        --------
        setDimensions, getGSVDDimensions, slepc.DSGSVDSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1056 <slepc4py/SLEPc/DS.pyx#L1056>`
    
        """
        ...
    def getGSVDDimensions(self) -> tuple[int, int]:
        """Get the number of columns and rows of a `DS` of type `GSVD`.
    
        Not collective.
    
        Returns
        -------
        m: int
            The number of columns.
        p: int
            The number of rows for the second matrix.
    
        See Also
        --------
        setGSVDDimensions, slepc.DSGSVDGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1082 <slepc4py/SLEPc/DS.pyx#L1082>`
    
        """
        ...
    def setPEPDegree(self, deg: int) -> None:
        """Set the polynomial degree of a `DS` of type `PEP`.
    
        Logically collective.
    
        Parameters
        ----------
        deg
            The polynomial degree.
    
        See Also
        --------
        getPEPDegree, slepc.DSPEPSetDegree
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1104 <slepc4py/SLEPc/DS.pyx#L1104>`
    
        """
        ...
    def getPEPDegree(self) -> int:
        """Get the polynomial degree of a `DS` of type `PEP`.
    
        Not collective.
    
        Returns
        -------
        int
            The polynomial degree.
    
        See Also
        --------
        setPEPDegree, slepc.DSPEPGetDegree
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1122 <slepc4py/SLEPc/DS.pyx#L1122>`
    
        """
        ...
    def setPEPCoefficients(self, pbc: Sequence[float]) -> None:
        """Set the polynomial basis coefficients of a `DS` of type `PEP`.
    
        Logically collective.
    
        Parameters
        ----------
        pbc
            Coefficients.
    
        Notes
        -----
        This function is required only in the case of a polynomial specified in
        a non-monomial basis, to provide the coefficients that will be used
        during the linearization, multiplying the identity blocks on the three
        main diagonal blocks. Depending on the polynomial basis (Chebyshev,
        Legendre, ...) the coefficients must be different.
    
        There must be a total of :math:`3(d+1)` coefficients, where :math:`d` is
        the degree of the polynomial. The coefficients are arranged in three
        groups, :math:`a_i, b_i, c_i`, according to the definition
        of the three-term recurrence. In the case of the monomial basis,
        :math:`a_i=1` and :math:`b_i=c_i=0`, in which case it is
        not necessary to invoke this function.
    
        See Also
        --------
        getPEPCoefficients, slepc.DSPEPSetCoefficients
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1141 <slepc4py/SLEPc/DS.pyx#L1141>`
    
        """
        ...
    def getPEPCoefficients(self) -> ArrayReal:
        """Get the polynomial basis coefficients of a `DS` of type `PEP`.
    
        Not collective.
    
        Returns
        -------
        ArrayReal
            Coefficients.
    
        See Also
        --------
        setPEPCoefficients, slepc.DSPEPGetCoefficients
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1176 <slepc4py/SLEPc/DS.pyx#L1176>`
    
        """
        ...
    @property
    def state(self) -> DSStateType:
        """The state of the DS object.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1204 <slepc4py/SLEPc/DS.pyx#L1204>`
    
        """
        ...
    @property
    def parallel(self) -> DSParallelType:
        """The mode of operation in parallel runs.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1211 <slepc4py/SLEPc/DS.pyx#L1211>`
    
        """
        ...
    @property
    def block_size(self) -> int:
        """The block size.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1218 <slepc4py/SLEPc/DS.pyx#L1218>`
    
        """
        ...
    @property
    def method(self) -> int:
        """The method to be used to solve the problem.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1225 <slepc4py/SLEPc/DS.pyx#L1225>`
    
        """
        ...
    @property
    def compact(self) -> bool:
        """Compact storage of matrices.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1232 <slepc4py/SLEPc/DS.pyx#L1232>`
    
        """
        ...
    @property
    def extra_row(self) -> bool:
        """If the matrix has one extra row.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1239 <slepc4py/SLEPc/DS.pyx#L1239>`
    
        """
        ...
    @property
    def refined(self) -> bool:
        """If refined vectors must be computed.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/DS.pyx:1246 <slepc4py/SLEPc/DS.pyx#L1246>`
    
        """
        ...

class FN(Object):
    """Mathematical Function.
    
    The `FN` package provides the functionality to represent a simple
    mathematical function such as an exponential, a polynomial or a rational
    function. This is used as a building block for defining the function
    associated to the nonlinear eigenproblem, as well as for specifying which
    function to use when computing the action of a matrix function on a vector.
    
    """
    class Type:
        """FN type.
        
        - `COMBINE`: A math function defined by combining two functions.
        - `RATIONAL`: A rational function :math:`f(x)=p(x)/q(x)`.
        - `EXP`: The exponential function :math:`f(x)=e^x`.
        - `LOG`: The logarithm function :math:`f(x)=\log{x}`.
        - `PHI`: One of the Phi_k functions with index k.
        - `SQRT`: The square root function :math:`f(x)=\sqrt{x}`.
        - `INVSQRT`: The inverse square root function.
        
        See Also
        --------
        slepc.FNType
        
        """
        COMBINE: str = _def(str, 'COMBINE')  #: Object ``COMBINE`` of type :class:`str`
        RATIONAL: str = _def(str, 'RATIONAL')  #: Object ``RATIONAL`` of type :class:`str`
        EXP: str = _def(str, 'EXP')  #: Object ``EXP`` of type :class:`str`
        LOG: str = _def(str, 'LOG')  #: Object ``LOG`` of type :class:`str`
        PHI: str = _def(str, 'PHI')  #: Object ``PHI`` of type :class:`str`
        SQRT: str = _def(str, 'SQRT')  #: Object ``SQRT`` of type :class:`str`
        INVSQRT: str = _def(str, 'INVSQRT')  #: Object ``INVSQRT`` of type :class:`str`
    class CombineType:
        """FN type of combination of child functions.
        
        - `ADD`:       Addition       :math:`f(x) = f_1(x)+f_2(x)`
        - `MULTIPLY`:  Multiplication :math:`f(x) = f_1(x)f_2(x)`
        - `DIVIDE`:    Division       :math:`f(x) = f_1(x)/f_2(x)`
        - `COMPOSE`:   Composition    :math:`f(x) = f_2(f_1(x))`
        
        See Also
        --------
        slepc.FNCombineType
        
        """
        ADD: int = _def(int, 'ADD')  #: Constant ``ADD`` of type :class:`int`
        MULTIPLY: int = _def(int, 'MULTIPLY')  #: Constant ``MULTIPLY`` of type :class:`int`
        DIVIDE: int = _def(int, 'DIVIDE')  #: Constant ``DIVIDE`` of type :class:`int`
        COMPOSE: int = _def(int, 'COMPOSE')  #: Constant ``COMPOSE`` of type :class:`int`
    class ParallelType:
        """FN parallel types.
        
        - `REDUNDANT`:    Every process performs the computation redundantly.
        - `SYNCHRONIZED`: The first process sends the result to the rest.
        
        See Also
        --------
        slepc.FNParallelType
        
        """
        REDUNDANT: int = _def(int, 'REDUNDANT')  #: Constant ``REDUNDANT`` of type :class:`int`
        SYNCHRONIZED: int = _def(int, 'SYNCHRONIZED')  #: Constant ``SYNCHRONIZED`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the FN data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.FNView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:149 <slepc4py/SLEPc/FN.pyx#L149>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the FN object.
    
        Collective.
    
        See Also
        --------
        slepc.FNDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:168 <slepc4py/SLEPc/FN.pyx#L168>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the FN object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator; if not provided, it defaults to all processes.
    
        See Also
        --------
        slepc.FNCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:182 <slepc4py/SLEPc/FN.pyx#L182>`
    
        """
        ...
    def setType(self, fn_type: Type | str) -> None:
        """Set the type for the FN object.
    
        Logically collective.
    
        Parameters
        ----------
        fn_type
            The math function type to be used.
    
        See Also
        --------
        getType, slepc.FNSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:203 <slepc4py/SLEPc/FN.pyx#L203>`
    
        """
        ...
    def getType(self) -> str:
        """Get the FN type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The math function type currently being used.
    
        See Also
        --------
        setType, slepc.FNGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:222 <slepc4py/SLEPc/FN.pyx#L222>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all FN options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all FN option requests.
    
        Notes
        -----
        A hyphen (``-``) must NOT be given at the beginning of the
        prefix name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.FNGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:241 <slepc4py/SLEPc/FN.pyx#L241>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all FN options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all FN option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.FNAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:266 <slepc4py/SLEPc/FN.pyx#L266>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all FN options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this FN object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.FNGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:285 <slepc4py/SLEPc/FN.pyx#L285>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set FN options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help``
        option.
    
        See Also
        --------
        setOptionsPrefix, slepc.FNSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:304 <slepc4py/SLEPc/FN.pyx#L304>`
    
        """
        ...
    def duplicate(self, comm: Comm | None = None) -> FN:
        """Duplicate the FN object copying all parameters.
    
        Collective.
    
        Duplicate the FN object copying all parameters, possibly with a
        different communicator.
    
        Parameters
        ----------
        comm
            MPI communicator; if not provided, it defaults to the
            object's communicator.
    
        Returns
        -------
        FN
            The new object.
    
        See Also
        --------
        create, slepc.FNDuplicate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:321 <slepc4py/SLEPc/FN.pyx#L321>`
    
        """
        ...
    def evaluateFunction(self, x: Scalar) -> Scalar:
        """Compute the value of the function :math:`f(x)` for a given x.
    
        Not collective.
    
        Parameters
        ----------
        x
            Value where the function must be evaluated.
    
        Returns
        -------
        Scalar
            The result of :math:`f(x)`.
    
        Notes
        -----
        Scaling factors are taken into account, so the actual function
        evaluation will return :math:`b f(a x)`.
    
        See Also
        --------
        evaluateDerivative, evaluateFunctionMat, setScale, slepc.FNEvaluateFunction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:352 <slepc4py/SLEPc/FN.pyx#L352>`
    
        """
        ...
    def evaluateDerivative(self, x: Scalar) -> Scalar:
        """Compute the value of the derivative :math:`f'(x)` for a given x.
    
        Not collective.
    
        Parameters
        ----------
        x
            Value where the derivative must be evaluated.
    
        Returns
        -------
        Scalar
            The result of :math:`f'(x)`.
    
        Notes
        -----
        Scaling factors are taken into account, so the actual derivative
        evaluation will return :math:`ab f'(a x)`.
    
        See Also
        --------
        evaluateFunction, setScale, slepc.FNEvaluateDerivative
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:382 <slepc4py/SLEPc/FN.pyx#L382>`
    
        """
        ...
    def evaluateFunctionMat(self, A: Mat, B: Mat | None = None) -> Mat:
        """Compute the value of the function :math:`f(A)` for a given matrix A.
    
        Logically collective.
    
        Parameters
        ----------
        A
            Matrix on which the function must be evaluated.
        B
            Placeholder for the result.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            The result of :math:`f(A)`.
    
        Notes
        -----
        Scaling factors are taken into account, so the actual function
        evaluation will return :math:`b f(a A)`.
    
        See Also
        --------
        evaluateFunction, evaluateFunctionMatVec, slepc.FNEvaluateFunctionMat
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:412 <slepc4py/SLEPc/FN.pyx#L412>`
    
        """
        ...
    def evaluateFunctionMatVec(self, A: Mat, v: Vec | None = None) -> Vec:
        """Compute the first column of the matrix :math:`f(A)`.
    
        Logically collective.
    
        Parameters
        ----------
        A
            Matrix on which the function must be evaluated.
    
        Returns
        -------
        petsc4py.PETSc.Vec
            The first column of the result :math:`f(A)`.
    
        Notes
        -----
        This operation is similar to `evaluateFunctionMat()` but returns only
        the first column of :math:`f(A)`, hence saving computations in most
        cases.
    
        See Also
        --------
        evaluateFunctionMat, slepc.FNEvaluateFunctionMatVec
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:443 <slepc4py/SLEPc/FN.pyx#L443>`
    
        """
        ...
    def setScale(self, alpha: Scalar | None = None, beta: Scalar | None = None) -> None:
        """Set the scaling parameters that define the matematical function.
    
        Logically collective.
    
        Parameters
        ----------
        alpha
            Inner scaling (argument), default is 1.0.
        beta
            Outer scaling (result), default is 1.0.
    
        See Also
        --------
        getScale, evaluateFunction, slepc.FNSetScale
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:473 <slepc4py/SLEPc/FN.pyx#L473>`
    
        """
        ...
    def getScale(self) -> tuple[Scalar, Scalar]:
        """Get the scaling parameters that define the matematical function.
    
        Not collective.
    
        Returns
        -------
        alpha: Scalar
            Inner scaling (argument).
        beta: Scalar
            Outer scaling (result).
    
        See Also
        --------
        setScale, slepc.FNGetScale
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:496 <slepc4py/SLEPc/FN.pyx#L496>`
    
        """
        ...
    def setMethod(self, meth: int) -> None:
        """Set the method to be used to evaluate functions of matrices.
    
        Logically collective.
    
        Parameters
        ----------
        meth
            An index identifying the method.
    
        Notes
        -----
        In some `FN` types there are more than one algorithms available
        for computing matrix functions. In that case, this function allows
        choosing the wanted method.
    
        If ``meth`` is currently set to 0 and the input argument of
        `FN.evaluateFunctionMat()` is a symmetric/Hermitian matrix, then
        the computation is done via the eigendecomposition, rather than
        with the general algorithm.
    
        See Also
        --------
        getMethod, slepc.FNSetMethod
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:517 <slepc4py/SLEPc/FN.pyx#L517>`
    
        """
        ...
    def getMethod(self) -> int:
        """Get the method currently used for matrix functions.
    
        Not collective.
    
        Returns
        -------
        int
            An index identifying the method.
    
        See Also
        --------
        setMethod, slepc.FNGetMethod
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:546 <slepc4py/SLEPc/FN.pyx#L546>`
    
        """
        ...
    def setParallel(self, pmode: ParallelType) -> None:
        """Set the mode of operation in parallel runs.
    
        Logically collective.
    
        Parameters
        ----------
        pmode
            The parallel mode.
    
        Notes
        -----
        This is relevant only when the function is evaluated on a matrix, with
        either `evaluateFunctionMat()` or `evaluateFunctionMatVec()`.
    
        See Also
        --------
        evaluateFunctionMat, getParallel, slepc.FNSetParallel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:565 <slepc4py/SLEPc/FN.pyx#L565>`
    
        """
        ...
    def getParallel(self) -> ParallelType:
        """Get the mode of operation in parallel runs.
    
        Not collective.
    
        Returns
        -------
        ParallelType
            The parallel mode.
    
        See Also
        --------
        setParallel, slepc.FNGetParallel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:588 <slepc4py/SLEPc/FN.pyx#L588>`
    
        """
        ...
    def setRationalNumerator(self, alpha: Sequence[Scalar]) -> None:
        """Set the coefficients of the numerator of the rational function.
    
        Logically collective.
    
        Parameters
        ----------
        alpha
            Coefficients.
    
        See Also
        --------
        setRationalDenominator, slepc.FNRationalSetNumerator
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:609 <slepc4py/SLEPc/FN.pyx#L609>`
    
        """
        ...
    def getRationalNumerator(self) -> ArrayScalar:
        """Get the coefficients of the numerator of the rational function.
    
        Not collective.
    
        Returns
        -------
        ArrayScalar
            Coefficients.
    
        See Also
        --------
        setRationalNumerator, slepc.FNRationalGetNumerator
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:629 <slepc4py/SLEPc/FN.pyx#L629>`
    
        """
        ...
    def setRationalDenominator(self, alpha: Sequence[Scalar]) -> None:
        """Set the coefficients of the denominator of the rational function.
    
        Logically collective.
    
        Parameters
        ----------
        alpha
            Coefficients.
    
        See Also
        --------
        setRationalNumerator, slepc.FNRationalSetDenominator
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:654 <slepc4py/SLEPc/FN.pyx#L654>`
    
        """
        ...
    def getRationalDenominator(self) -> ArrayScalar:
        """Get the coefficients of the denominator of the rational function.
    
        Not collective.
    
        Returns
        -------
        ArrayScalar
            Coefficients.
    
        See Also
        --------
        setRationalDenominator, slepc.FNRationalGetDenominator
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:674 <slepc4py/SLEPc/FN.pyx#L674>`
    
        """
        ...
    def setCombineChildren(self, comb: CombineType, f1: FN, f2: FN) -> None:
        """Set the two child functions that constitute this combined function.
    
        Logically collective.
    
        Set the two child functions that constitute this combined function,
        and the way they must be combined.
    
        Parameters
        ----------
        comb
            How to combine the functions (addition, multiplication, division,
            composition).
        f1
            First function.
        f2
            Second function.
    
        See Also
        --------
        getCombineChildren, slepc.FNCombineSetChildren
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:699 <slepc4py/SLEPc/FN.pyx#L699>`
    
        """
        ...
    def getCombineChildren(self) -> tuple[CombineType, FN, FN]:
        """Get the two child functions that constitute this combined function.
    
        Not collective.
    
        Get the two child functions that constitute this combined
        function, and the way they must be combined.
    
        Returns
        -------
        comb: CombineType
            How to combine the functions (addition, multiplication, division,
            composition).
        f1: FN
            First function.
        f2: FN
            Second function.
    
        See Also
        --------
        setCombineChildren, slepc.FNCombineGetChildren
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:725 <slepc4py/SLEPc/FN.pyx#L725>`
    
        """
        ...
    def setPhiIndex(self, k: int) -> None:
        """Set the index of the phi-function.
    
        Logically collective.
    
        Parameters
        ----------
        k
            The index.
    
        Notes
        -----
        If not set, the default index is 1.
    
        See Also
        --------
        getPhiIndex, slepc.FNPhiSetIndex
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:756 <slepc4py/SLEPc/FN.pyx#L756>`
    
        """
        ...
    def getPhiIndex(self) -> int:
        """Get the index of the phi-function.
    
        Not collective.
    
        Returns
        -------
        int
            The index.
    
        See Also
        --------
        setPhiIndex, slepc.FNPhiGetIndex
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:778 <slepc4py/SLEPc/FN.pyx#L778>`
    
        """
        ...
    @property
    def method(self) -> int:
        """The method to be used to evaluate functions of matrices.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:799 <slepc4py/SLEPc/FN.pyx#L799>`
    
        """
        ...
    @property
    def parallel(self) -> FNParallelType:
        """The mode of operation in parallel runs.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/FN.pyx:806 <slepc4py/SLEPc/FN.pyx#L806>`
    
        """
        ...

class RG(Object):
    """Region.
    
    The `RG` package provides a way to define a region of the complex plane.
    This is used in various eigensolvers to specify where the wanted
    eigenvalues are located.
    
    """
    class Type:
        """RG type.
        
        - `INTERVAL`: A (generalized) interval.
        - `POLYGON`: A polygonal region defined by its vertices.
        - `ELLIPSE`: An ellipse defined by its center, radius and vertical scale.
        - `RING`: A ring region.
        
        See Also
        --------
        slepc.RGType
        
        """
        INTERVAL: str = _def(str, 'INTERVAL')  #: Object ``INTERVAL`` of type :class:`str`
        POLYGON: str = _def(str, 'POLYGON')  #: Object ``POLYGON`` of type :class:`str`
        ELLIPSE: str = _def(str, 'ELLIPSE')  #: Object ``ELLIPSE`` of type :class:`str`
        RING: str = _def(str, 'RING')  #: Object ``RING`` of type :class:`str`
    class QuadRule:
        """RG quadrature rule for contour integral methods.
        
        - `TRAPEZOIDAL`: Trapezoidal rule.
        - `CHEBYSHEV`:   Chebyshev points.
        
        See Also
        --------
        slepc.RGQuadRule
        
        """
        TRAPEZOIDAL: int = _def(int, 'TRAPEZOIDAL')  #: Constant ``TRAPEZOIDAL`` of type :class:`int`
        CHEBYSHEV: int = _def(int, 'CHEBYSHEV')  #: Constant ``CHEBYSHEV`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the RG data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.RGView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:54 <slepc4py/SLEPc/RG.pyx#L54>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the RG object.
    
        Collective.
    
        See Also
        --------
        slepc.RGDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:73 <slepc4py/SLEPc/RG.pyx#L73>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the RG object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator; if not provided, it defaults to all processes.
    
        See Also
        --------
        slepc.RGCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:87 <slepc4py/SLEPc/RG.pyx#L87>`
    
        """
        ...
    def setType(self, rg_type: Type | str) -> None:
        """Set the type for the RG object.
    
        Logically collective.
    
        Parameters
        ----------
        rg_type
            The region type to be used.
    
        See Also
        --------
        getType, slepc.RGSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:108 <slepc4py/SLEPc/RG.pyx#L108>`
    
        """
        ...
    def getType(self) -> str:
        """Get the RG type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The region type currently being used.
    
        See Also
        --------
        setType, slepc.RGGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:127 <slepc4py/SLEPc/RG.pyx#L127>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all RG options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all RG option requests.
    
        Notes
        -----
        A hyphen (``-``) must NOT be given at the beginning of the
        prefix name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.RGGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:146 <slepc4py/SLEPc/RG.pyx#L146>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all RG options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this RG object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.RGGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:171 <slepc4py/SLEPc/RG.pyx#L171>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all RG options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all RG option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.RGAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:190 <slepc4py/SLEPc/RG.pyx#L190>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set RG options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help``
        option.
    
        See Also
        --------
        setOptionsPrefix, slepc.RGSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:209 <slepc4py/SLEPc/RG.pyx#L209>`
    
        """
        ...
    def isTrivial(self) -> bool:
        """Tell whether it is the trivial region (whole complex plane).
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if the region is equal to the whole complex plane, e.g.,
            an interval region with all four endpoints unbounded or an
            ellipse with infinite radius.
    
        See Also
        --------
        checkInside, slepc.RGIsTrivial
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:228 <slepc4py/SLEPc/RG.pyx#L228>`
    
        """
        ...
    def isAxisymmetric(self, vertical: bool = False) -> bool:
        """Determine if the region is axisymmetric.
    
        Not collective.
    
        Determine if the region is symmetric with respect to the real or
        imaginary axis.
    
        Parameters
        ----------
        vertical
            ``True`` if symmetry must be checked against the vertical axis.
    
        Returns
        -------
        bool
            ``True`` if the region is axisymmetric.
    
        See Also
        --------
        canUseConjugates, slepc.RGIsAxisymmetric
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:249 <slepc4py/SLEPc/RG.pyx#L249>`
    
        """
        ...
    def getComplement(self) -> bool:
        """Get the flag indicating whether the region is complemented or not.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether the region is complemented or not.
    
        See Also
        --------
        setComplement, slepc.RGGetComplement
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:277 <slepc4py/SLEPc/RG.pyx#L277>`
    
        """
        ...
    def setComplement(self, comp: bool = True) -> None:
        """Set a flag to indicate that the region is the complement of the specified one.
    
        Logically collective.
    
        Parameters
        ----------
        comp
            Activate/deactivate the complementation of the region.
    
        See Also
        --------
        getComplement, slepc.RGSetComplement
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:296 <slepc4py/SLEPc/RG.pyx#L296>`
    
        """
        ...
    def setScale(self, sfactor: float = None) -> None:
        """Set the scaling factor to be used.
    
        Logically collective.
    
        Set the scaling factor to be used when checking that a
        point is inside the region and when computing the contour.
    
        Parameters
        ----------
        sfactor
            The scaling factor (default=1).
    
        See Also
        --------
        getScale, checkInside, computeContour, slepc.RGSetScale
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:314 <slepc4py/SLEPc/RG.pyx#L314>`
    
        """
        ...
    def getScale(self) -> float:
        """Get the scaling factor.
    
        Not collective.
    
        Returns
        -------
        float
            The scaling factor.
    
        See Also
        --------
        setScale, slepc.RGGetScale
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:336 <slepc4py/SLEPc/RG.pyx#L336>`
    
        """
        ...
    def checkInside(self, a: Sequence[complex]) -> ArrayInt:
        """Determine if a set of given points are inside the region or not.
    
        Not collective.
    
        Parameters
        ----------
        a
            The coordinates of the points.
    
        Returns
        -------
        ArrayInt
            Computed result for each point (1=inside, 0=on the contour, -1=outside).
    
        Notes
        -----
        If a scaling factor was set, the points are scaled before checking.
    
        See Also
        --------
        setScale, setComplement, slepc.RGCheckInside
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:355 <slepc4py/SLEPc/RG.pyx#L355>`
    
        """
        ...
    def computeContour(self, n: int) -> list[complex]:
        """Compute points on the contour of the region.
    
        Not collective.
    
        Compute the coordinates of several points lying on the contour
        of the region.
    
        Parameters
        ----------
        n
            The number of points to compute.
    
        Returns
        -------
        list of complex
            Computed points.
    
        See Also
        --------
        computeBoundingBox, setScale, slepc.RGComputeContour
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:395 <slepc4py/SLEPc/RG.pyx#L395>`
    
        """
        ...
    def computeBoundingBox(self) -> tuple[float, float, float, float]:
        """Compute box containing the region.
    
        Not collective.
    
        Determine the endpoints of a rectangle in the complex plane that
        contains the region.
    
        Returns
        -------
        a: float
            The left endpoint of the bounding box in the real axis.
        b: float
            The right endpoint of the bounding box in the real axis.
        c: float
            The bottom endpoint of the bounding box in the imaginary axis.
        d: float
            The top endpoint of the bounding box in the imaginary axis.
    
        See Also
        --------
        computeContour, setScale, slepc.RGComputeBoundingBox
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:430 <slepc4py/SLEPc/RG.pyx#L430>`
    
        """
        ...
    def canUseConjugates(self, realmats: bool = True) -> bool:
        """Half of integration points can be avoided (use their conjugates).
    
        Not collective.
    
        Used in contour integral methods to determine whether half of
        integration points can be avoided (use their conjugates).
    
        Parameters
        ----------
        realmats
            ``True`` if the problem matrices are real.
    
        Returns
        -------
        bool
            Whether it is possible to use conjugates.
    
        Notes
        -----
        If some integration points are the conjugates of other points, then the
        associated computational cost can be saved. This depends on the problem
        matrices being real and also the region being symmetric with respect to
        the horizontal axis. The result is ``false`` if using real arithmetic or
        in the case of a flat region (height equal to zero).
    
        See Also
        --------
        isAxisymmetric, slepc.RGCanUseConjugates
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:458 <slepc4py/SLEPc/RG.pyx#L458>`
    
        """
        ...
    def computeQuadrature(self, quad: QuadRule, n: int) -> tuple[ArrayScalar, ArrayScalar, ArrayScalar]:
        """Compute the values of the parameters used in a quadrature rule.
    
        Not collective.
    
        Compute the values of the parameters used in a quadrature rule for a
        contour integral around the boundary of the region.
    
        Parameters
        ----------
        quad
            The type of quadrature.
        n
            The number of quadrature points to compute.
    
        Returns
        -------
        z: ArrayScalar
            Quadrature points.
        zn: ArrayScalar
            Normalized quadrature points.
        w: ArrayScalar
            Quadrature weights.
    
        Notes
        -----
        In complex scalars, the values returned in ``z`` are often the same as
        those computed by `computeContour()`, but this is not the case in real
        scalars where all output arguments are real.
    
        The computed values change for different quadrature rules.
    
        See Also
        --------
        computeContour, slepc.RGComputeQuadrature
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:494 <slepc4py/SLEPc/RG.pyx#L494>`
    
        """
        ...
    def setEllipseParameters(self, center: Scalar, radius: float, vscale: float | None = None) -> None:
        """Set the parameters defining the ellipse region.
    
        Logically collective.
    
        Parameters
        ----------
        center
            The center.
        radius
            The radius.
        vscale
            The vertical scale.
    
        Notes
        -----
        When PETSc is built with real scalars, the center is restricted to a
        real value.
    
        See Also
        --------
        getEllipseParameters, slepc.RGEllipseSetParameters
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:542 <slepc4py/SLEPc/RG.pyx#L542>`
    
        """
        ...
    def getEllipseParameters(self) -> tuple[Scalar, float, float]:
        """Get the parameters that define the ellipse region.
    
        Not collective.
    
        Returns
        -------
        center: Scalar
            The center.
        radius: float
            The radius.
        vscale: float
            The vertical scale.
    
        See Also
        --------
        setEllipseParameters, slepc.RGEllipseGetParameters
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:572 <slepc4py/SLEPc/RG.pyx#L572>`
    
        """
        ...
    def setIntervalEndpoints(self, a: float, b: float, c: float, d: float) -> None:
        """Set the parameters defining the interval region.
    
        Logically collective.
    
        Parameters
        ----------
        a
            The left endpoint in the real axis.
        b
            The right endpoint in the real axis.
        c
            The bottom endpoint in the imaginary axis.
        d
            The top endpoint in the imaginary axis.
    
        Notes
        -----
        The region is defined as :math:`[a,b] x [c,d]`. Particular cases are an
        interval on the real axis (:math:`c=d=0`), similarly for the imaginary
        axis (:math:`a=b=0`), the whole complex plane
        (:math:`a=-\infty,b=\infty,c=-\infty,d=\infty`), and so on.
    
        When PETSc is built with real scalars, the region must be symmetric with
        respect to the real axis.
    
        See Also
        --------
        getIntervalEndpoints, slepc.RGIntervalSetEndpoints
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:597 <slepc4py/SLEPc/RG.pyx#L597>`
    
        """
        ...
    def getIntervalEndpoints(self) -> tuple[float, float, float, float]:
        """Get the parameters that define the interval region.
    
        Not collective.
    
        Returns
        -------
        a: float
            The left endpoint in the real axis.
        b: float
            The right endpoint in the real axis.
        c: float
            The bottom endpoint in the imaginary axis.
        d: float
            The top endpoint in the imaginary axis.
    
        See Also
        --------
        setIntervalEndpoints, slepc.RGIntervalGetEndpoints
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:634 <slepc4py/SLEPc/RG.pyx#L634>`
    
        """
        ...
    def setPolygonVertices(self, v: Sequence[float] | Sequence[Scalar]) -> None:
        """Set the vertices that define the polygon region.
    
        Logically collective.
    
        Parameters
        ----------
        v
            The vertices.
    
        See Also
        --------
        getPolygonVertices, slepc.RGPolygonSetVertices
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:662 <slepc4py/SLEPc/RG.pyx#L662>`
    
        """
        ...
    def getPolygonVertices(self) -> ArrayComplex:
        """Get the parameters that define the interval region.
    
        Not collective.
    
        Returns
        -------
        ArrayComplex
            The vertices.
    
        See Also
        --------
        setPolygonVertices, slepc.RGPolygonGetVertices
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:690 <slepc4py/SLEPc/RG.pyx#L690>`
    
        """
        ...
    def setRingParameters(self, center: Scalar, radius: float, vscale: float, start_ang: float, end_ang: float, width: float) -> None:
        """Set the parameters defining the ring region.
    
        Logically collective.
    
        Parameters
        ----------
        center
            The center.
        radius
            The radius.
        vscale
            The vertical scale.
        start_ang
            The right-hand side angle.
        end_ang
            The left-hand side angle.
        width
            The width of the ring.
    
        Notes
        -----
        The values of ``center``, ``radius`` and ``vscale`` have the same
        meaning as in the ellipse region. The ``start_ang`` and ``end_ang``
        define the span of the ring (by default it is the whole ring), while
        the ``width`` is the separation between the two concentric ellipses
        (above and below the radius by ``width/2``).
    
        The start and end angles are expressed as a fraction of the
        circumference. The allowed range is :math:`[0,\dots,1]`, with ``0``
        corresponding to 0 radians, ``0.25`` to :math:`\pi/2` radians, and so
        on. It is allowed to have ``start_ang`` > ``end_ang``, in which case
        the ring region crosses over the zero angle.
    
        When PETSc is built with real scalars, the center is restricted to a
        real value, and the start and end angles must be such that the region
        is symmetric with respect to the real axis.
    
        See Also
        --------
        getRingParameters, slepc.RGRingSetParameters
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:716 <slepc4py/SLEPc/RG.pyx#L716>`
    
        """
        ...
    def getRingParameters(self) -> tuple[Scalar, float, float, float, float, float]:
        """Get the parameters that define the ring region.
    
        Not collective.
    
        Returns
        -------
        center: Scalar
            The center.
        radius: float
            The radius.
        vscale: float
            The vertical scale.
        start_ang: float
            The right-hand side angle.
        end_ang: float
            The left-hand side angle.
        width: float
            The width of the ring.
    
        See Also
        --------
        setRingParameters, slepc.RGRingGetParameters
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:775 <slepc4py/SLEPc/RG.pyx#L775>`
    
        """
        ...
    @property
    def complement(self) -> bool:
        """If the region is the complement of the specified one.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:811 <slepc4py/SLEPc/RG.pyx#L811>`
    
        """
        ...
    @property
    def scale(self) -> float:
        """The scaling factor to be used.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/RG.pyx:818 <slepc4py/SLEPc/RG.pyx#L818>`
    
        """
        ...

class EPS(Object):
    """Eigenvalue Problem Solver.
    
    The Eigenvalue Problem Solver (`EPS`) is the object provided by slepc4py
    for specifying a linear eigenvalue problem, either in standard or
    generalized form. It provides uniform and efficient access to all of the
    linear eigensolvers included in the package.
    
    """
    class Type:
        """EPS type.
        
        Native eigenvalue solvers.
        
        - `POWER`:        Power Iteration, Inverse Iteration, RQI.
        - `SUBSPACE`:     Subspace Iteration.
        - `ARNOLDI`:      Arnoldi.
        - `LANCZOS`:      Lanczos.
        - `KRYLOVSCHUR`:  Krylov-Schur (default).
        - `GD`:           Generalized Davidson.
        - `JD`:           Jacobi-Davidson.
        - `RQCG`:         Rayleigh Quotient Conjugate Gradient.
        - `LOBPCG`:       Locally Optimal Block Preconditioned Conjugate Gradient.
        - `CISS`:         Contour Integral Spectrum Slicing.
        - `LYAPII`:       Lyapunov inverse iteration.
        
        Wrappers to external eigensolvers
        (should be enabled during installation of SLEPc).
        
        - `LAPACK`:       Sequential dense eigensolver.
        - `ARPACK`:       Iterative Krylov-based eigensolver.
        - `BLOPEX`:       Implementation of LOBPCG.
        - `PRIMME`:       Iterative eigensolvers of Davidson type.
        - `FEAST`:        Contour integral eigensolver.
        - `SCALAPACK`:    Parallel dense eigensolver for symmetric problems.
        - `ELPA`:         Parallel dense eigensolver for symmetric problems.
        - `ELEMENTAL`:    Parallel dense eigensolver for symmetric problems.
        - `EVSL`:         Iterative eigensolver based on polynomial filters.
        - `CHASE`:        Subspace iteration accelerated with polynomials.
        
        See Also
        --------
        slepc.EPSType
        
        """
        POWER: str = _def(str, 'POWER')  #: Object ``POWER`` of type :class:`str`
        SUBSPACE: str = _def(str, 'SUBSPACE')  #: Object ``SUBSPACE`` of type :class:`str`
        ARNOLDI: str = _def(str, 'ARNOLDI')  #: Object ``ARNOLDI`` of type :class:`str`
        LANCZOS: str = _def(str, 'LANCZOS')  #: Object ``LANCZOS`` of type :class:`str`
        KRYLOVSCHUR: str = _def(str, 'KRYLOVSCHUR')  #: Object ``KRYLOVSCHUR`` of type :class:`str`
        GD: str = _def(str, 'GD')  #: Object ``GD`` of type :class:`str`
        JD: str = _def(str, 'JD')  #: Object ``JD`` of type :class:`str`
        RQCG: str = _def(str, 'RQCG')  #: Object ``RQCG`` of type :class:`str`
        LOBPCG: str = _def(str, 'LOBPCG')  #: Object ``LOBPCG`` of type :class:`str`
        CISS: str = _def(str, 'CISS')  #: Object ``CISS`` of type :class:`str`
        LYAPII: str = _def(str, 'LYAPII')  #: Object ``LYAPII`` of type :class:`str`
        LAPACK: str = _def(str, 'LAPACK')  #: Object ``LAPACK`` of type :class:`str`
        ARPACK: str = _def(str, 'ARPACK')  #: Object ``ARPACK`` of type :class:`str`
        BLOPEX: str = _def(str, 'BLOPEX')  #: Object ``BLOPEX`` of type :class:`str`
        PRIMME: str = _def(str, 'PRIMME')  #: Object ``PRIMME`` of type :class:`str`
        FEAST: str = _def(str, 'FEAST')  #: Object ``FEAST`` of type :class:`str`
        SCALAPACK: str = _def(str, 'SCALAPACK')  #: Object ``SCALAPACK`` of type :class:`str`
        ELPA: str = _def(str, 'ELPA')  #: Object ``ELPA`` of type :class:`str`
        ELEMENTAL: str = _def(str, 'ELEMENTAL')  #: Object ``ELEMENTAL`` of type :class:`str`
        EVSL: str = _def(str, 'EVSL')  #: Object ``EVSL`` of type :class:`str`
        CHASE: str = _def(str, 'CHASE')  #: Object ``CHASE`` of type :class:`str`
    class ProblemType:
        """EPS problem type.
        
        - `HEP`:    Hermitian eigenproblem.
        - `NHEP`:   Non-Hermitian eigenproblem.
        - `GHEP`:   Generalized Hermitian eigenproblem.
        - `GNHEP`:  Generalized Non-Hermitian eigenproblem.
        - `PGNHEP`: Generalized Non-Hermitian eigenproblem
          with positive definite :math:`B`.
        - `GHIEP`:  Generalized Hermitian-indefinite eigenproblem.
        - `BSE`:    Structured Bethe-Salpeter eigenproblem.
        - `HAMILT`: Hamiltonian eigenproblem.
        
        See Also
        --------
        slepc.EPSProblemType
        
        """
        HEP: int = _def(int, 'HEP')  #: Constant ``HEP`` of type :class:`int`
        NHEP: int = _def(int, 'NHEP')  #: Constant ``NHEP`` of type :class:`int`
        GHEP: int = _def(int, 'GHEP')  #: Constant ``GHEP`` of type :class:`int`
        GNHEP: int = _def(int, 'GNHEP')  #: Constant ``GNHEP`` of type :class:`int`
        PGNHEP: int = _def(int, 'PGNHEP')  #: Constant ``PGNHEP`` of type :class:`int`
        GHIEP: int = _def(int, 'GHIEP')  #: Constant ``GHIEP`` of type :class:`int`
        BSE: int = _def(int, 'BSE')  #: Constant ``BSE`` of type :class:`int`
        HAMILT: int = _def(int, 'HAMILT')  #: Constant ``HAMILT`` of type :class:`int`
    class Extraction:
        """EPS extraction technique.
        
        - `RITZ`:              Standard Rayleigh-Ritz extraction.
        - `HARMONIC`:          Harmonic extraction.
        - `HARMONIC_RELATIVE`: Harmonic extraction relative to the eigenvalue.
        - `HARMONIC_RIGHT`:    Harmonic extraction for rightmost eigenvalues.
        - `HARMONIC_LARGEST`:  Harmonic extraction for largest magnitude (without
          target).
        - `REFINED`:           Refined extraction.
        - `REFINED_HARMONIC`:  Refined harmonic extraction.
        
        See Also
        --------
        slepc.EPSExtraction
        
        """
        RITZ: int = _def(int, 'RITZ')  #: Constant ``RITZ`` of type :class:`int`
        HARMONIC: int = _def(int, 'HARMONIC')  #: Constant ``HARMONIC`` of type :class:`int`
        HARMONIC_RELATIVE: int = _def(int, 'HARMONIC_RELATIVE')  #: Constant ``HARMONIC_RELATIVE`` of type :class:`int`
        HARMONIC_RIGHT: int = _def(int, 'HARMONIC_RIGHT')  #: Constant ``HARMONIC_RIGHT`` of type :class:`int`
        HARMONIC_LARGEST: int = _def(int, 'HARMONIC_LARGEST')  #: Constant ``HARMONIC_LARGEST`` of type :class:`int`
        REFINED: int = _def(int, 'REFINED')  #: Constant ``REFINED`` of type :class:`int`
        REFINED_HARMONIC: int = _def(int, 'REFINED_HARMONIC')  #: Constant ``REFINED_HARMONIC`` of type :class:`int`
    class Balance:
        """EPS type of balancing used for non-Hermitian problems.
        
        - `NONE`:     None.
        - `ONESIDE`:  One-sided balancing.
        - `TWOSIDE`:  Two-sided balancing.
        - `USER`:     User-provided balancing matrices.
        
        See Also
        --------
        slepc.EPSBalance
        
        """
        NONE: int = _def(int, 'NONE')  #: Constant ``NONE`` of type :class:`int`
        ONESIDE: int = _def(int, 'ONESIDE')  #: Constant ``ONESIDE`` of type :class:`int`
        TWOSIDE: int = _def(int, 'TWOSIDE')  #: Constant ``TWOSIDE`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class ErrorType:
        """EPS error type to assess accuracy of computed solutions.
        
        - `ABSOLUTE`: Absolute error.
        - `RELATIVE`: Relative error.
        - `BACKWARD`: Backward error.
        
        See Also
        --------
        slepc.EPSErrorType
        
        """
        ABSOLUTE: int = _def(int, 'ABSOLUTE')  #: Constant ``ABSOLUTE`` of type :class:`int`
        RELATIVE: int = _def(int, 'RELATIVE')  #: Constant ``RELATIVE`` of type :class:`int`
        BACKWARD: int = _def(int, 'BACKWARD')  #: Constant ``BACKWARD`` of type :class:`int`
    class Which:
        """EPS desired part of spectrum.
        
        - `LARGEST_MAGNITUDE`:  Largest magnitude (default).
        - `SMALLEST_MAGNITUDE`: Smallest magnitude.
        - `LARGEST_REAL`:       Largest real parts.
        - `SMALLEST_REAL`:      Smallest real parts.
        - `LARGEST_IMAGINARY`:  Largest imaginary parts in magnitude.
        - `SMALLEST_IMAGINARY`: Smallest imaginary parts in magnitude.
        - `TARGET_MAGNITUDE`:   Closest to target (in magnitude).
        - `TARGET_REAL`:        Real part closest to target.
        - `TARGET_IMAGINARY`:   Imaginary part closest to target.
        - `ALL`:                All eigenvalues in an interval.
        - `USER`:               User defined selection.
        
        See Also
        --------
        slepc.EPSWhich
        
        """
        LARGEST_MAGNITUDE: int = _def(int, 'LARGEST_MAGNITUDE')  #: Constant ``LARGEST_MAGNITUDE`` of type :class:`int`
        SMALLEST_MAGNITUDE: int = _def(int, 'SMALLEST_MAGNITUDE')  #: Constant ``SMALLEST_MAGNITUDE`` of type :class:`int`
        LARGEST_REAL: int = _def(int, 'LARGEST_REAL')  #: Constant ``LARGEST_REAL`` of type :class:`int`
        SMALLEST_REAL: int = _def(int, 'SMALLEST_REAL')  #: Constant ``SMALLEST_REAL`` of type :class:`int`
        LARGEST_IMAGINARY: int = _def(int, 'LARGEST_IMAGINARY')  #: Constant ``LARGEST_IMAGINARY`` of type :class:`int`
        SMALLEST_IMAGINARY: int = _def(int, 'SMALLEST_IMAGINARY')  #: Constant ``SMALLEST_IMAGINARY`` of type :class:`int`
        TARGET_MAGNITUDE: int = _def(int, 'TARGET_MAGNITUDE')  #: Constant ``TARGET_MAGNITUDE`` of type :class:`int`
        TARGET_REAL: int = _def(int, 'TARGET_REAL')  #: Constant ``TARGET_REAL`` of type :class:`int`
        TARGET_IMAGINARY: int = _def(int, 'TARGET_IMAGINARY')  #: Constant ``TARGET_IMAGINARY`` of type :class:`int`
        ALL: int = _def(int, 'ALL')  #: Constant ``ALL`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class Conv:
        """EPS convergence test.
        
        - `ABS`:  Absolute convergence test.
        - `REL`:  Convergence test relative to the eigenvalue.
        - `NORM`: Convergence test relative to the matrix norms.
        - `USER`: User-defined convergence test.
        
        See Also
        --------
        slepc.EPSConv
        
        """
        ABS: int = _def(int, 'ABS')  #: Constant ``ABS`` of type :class:`int`
        REL: int = _def(int, 'REL')  #: Constant ``REL`` of type :class:`int`
        NORM: int = _def(int, 'NORM')  #: Constant ``NORM`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class Stop:
        """EPS stopping test.
        
        - `BASIC`:     Default stopping test.
        - `USER`:      User-defined stopping test.
        - `THRESHOLD`: Threshold stopping test.
        
        See Also
        --------
        slepc.EPSStop
        
        """
        BASIC: int = _def(int, 'BASIC')  #: Constant ``BASIC`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
        THRESHOLD: int = _def(int, 'THRESHOLD')  #: Constant ``THRESHOLD`` of type :class:`int`
    class ConvergedReason:
        """EPS convergence reasons.
        
        - `CONVERGED_TOL`:          All eigenpairs converged to requested tolerance.
        - `CONVERGED_USER`:         User-defined convergence criterion satisfied.
        - `DIVERGED_ITS`:           Maximum number of iterations exceeded.
        - `DIVERGED_BREAKDOWN`:     Solver failed due to breakdown.
        - `DIVERGED_SYMMETRY_LOST`: Lanczos-type method could not preserve symmetry.
        - `CONVERGED_ITERATING`:    Iteration not finished yet.
        
        See Also
        --------
        slepc.EPSConvergedReason
        
        """
        CONVERGED_TOL: int = _def(int, 'CONVERGED_TOL')  #: Constant ``CONVERGED_TOL`` of type :class:`int`
        CONVERGED_USER: int = _def(int, 'CONVERGED_USER')  #: Constant ``CONVERGED_USER`` of type :class:`int`
        DIVERGED_ITS: int = _def(int, 'DIVERGED_ITS')  #: Constant ``DIVERGED_ITS`` of type :class:`int`
        DIVERGED_BREAKDOWN: int = _def(int, 'DIVERGED_BREAKDOWN')  #: Constant ``DIVERGED_BREAKDOWN`` of type :class:`int`
        DIVERGED_SYMMETRY_LOST: int = _def(int, 'DIVERGED_SYMMETRY_LOST')  #: Constant ``DIVERGED_SYMMETRY_LOST`` of type :class:`int`
        CONVERGED_ITERATING: int = _def(int, 'CONVERGED_ITERATING')  #: Constant ``CONVERGED_ITERATING`` of type :class:`int`
        ITERATING: int = _def(int, 'ITERATING')  #: Constant ``ITERATING`` of type :class:`int`
    class PowerShiftType:
        """EPS Power shift type.
        
        - `CONSTANT`:  Constant shift.
        - `RAYLEIGH`:  Rayleigh quotient.
        - `WILKINSON`: Wilkinson shift.
        
        See Also
        --------
        slepc.EPSPowerShiftType
        
        """
        CONSTANT: int = _def(int, 'CONSTANT')  #: Constant ``CONSTANT`` of type :class:`int`
        RAYLEIGH: int = _def(int, 'RAYLEIGH')  #: Constant ``RAYLEIGH`` of type :class:`int`
        WILKINSON: int = _def(int, 'WILKINSON')  #: Constant ``WILKINSON`` of type :class:`int`
    class KrylovSchurBSEType:
        """EPS Krylov-Schur method for BSE problems.
        
        - `SHAO`:         Lanczos recurrence for H square.
        - `GRUNING`:      Lanczos recurrence for H.
        - `PROJECTEDBSE`: Lanczos where the projected problem has BSE structure.
        
        See Also
        --------
        slepc.EPSKrylovSchurBSEType
        
        """
        SHAO: int = _def(int, 'SHAO')  #: Constant ``SHAO`` of type :class:`int`
        GRUNING: int = _def(int, 'GRUNING')  #: Constant ``GRUNING`` of type :class:`int`
        PROJECTEDBSE: int = _def(int, 'PROJECTEDBSE')  #: Constant ``PROJECTEDBSE`` of type :class:`int`
    class LanczosReorthogType:
        """EPS Lanczos reorthogonalization type.
        
        - `LOCAL`:     Local reorthogonalization only.
        - `FULL`:      Full reorthogonalization.
        - `SELECTIVE`: Selective reorthogonalization.
        - `PERIODIC`:  Periodic reorthogonalization.
        - `PARTIAL`:   Partial reorthogonalization.
        - `DELAYED`:   Delayed reorthogonalization.
        
        See Also
        --------
        slepc.EPSLanczosReorthogType
        
        """
        LOCAL: int = _def(int, 'LOCAL')  #: Constant ``LOCAL`` of type :class:`int`
        FULL: int = _def(int, 'FULL')  #: Constant ``FULL`` of type :class:`int`
        SELECTIVE: int = _def(int, 'SELECTIVE')  #: Constant ``SELECTIVE`` of type :class:`int`
        PERIODIC: int = _def(int, 'PERIODIC')  #: Constant ``PERIODIC`` of type :class:`int`
        PARTIAL: int = _def(int, 'PARTIAL')  #: Constant ``PARTIAL`` of type :class:`int`
        DELAYED: int = _def(int, 'DELAYED')  #: Constant ``DELAYED`` of type :class:`int`
    class CISSQuadRule:
        """EPS CISS quadrature rule.
        
        - `TRAPEZOIDAL`: Trapezoidal rule.
        - `CHEBYSHEV`:   Chebyshev points.
        
        See Also
        --------
        slepc.EPSCISSQuadRule
        
        """
        TRAPEZOIDAL: int = _def(int, 'TRAPEZOIDAL')  #: Constant ``TRAPEZOIDAL`` of type :class:`int`
        CHEBYSHEV: int = _def(int, 'CHEBYSHEV')  #: Constant ``CHEBYSHEV`` of type :class:`int`
    class CISSExtraction:
        """EPS CISS extraction technique.
        
        - `RITZ`:   Ritz extraction.
        - `HANKEL`: Extraction via Hankel eigenproblem.
        
        See Also
        --------
        slepc.EPSCISSExtraction
        
        """
        RITZ: int = _def(int, 'RITZ')  #: Constant ``RITZ`` of type :class:`int`
        HANKEL: int = _def(int, 'HANKEL')  #: Constant ``HANKEL`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the EPS data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.EPSView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:351 <slepc4py/SLEPc/EPS.pyx#L351>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the EPS object.
    
        Collective.
    
        See Also
        --------
        slepc.EPSDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:370 <slepc4py/SLEPc/EPS.pyx#L370>`
    
        """
        ...
    def reset(self) -> None:
        """Reset the EPS object.
    
        Collective.
    
        See Also
        --------
        slepc.EPSReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:384 <slepc4py/SLEPc/EPS.pyx#L384>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the EPS object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator; if not provided, it defaults to all processes.
    
        See Also
        --------
        slepc.EPSCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:396 <slepc4py/SLEPc/EPS.pyx#L396>`
    
        """
        ...
    def setType(self, eps_type: Type | str) -> None:
        """Set the particular solver to be used in the EPS object.
    
        Logically collective.
    
        Parameters
        ----------
        eps_type
            The solver to be used.
    
        Notes
        -----
        The default is `KRYLOVSCHUR`. Normally, it is best to use
        `setFromOptions()` and then set the EPS type from the options
        database rather than by using this routine. Using the options
        database provides the user with maximum flexibility in
        evaluating the different available methods.
    
        See Also
        --------
        getType, slepc.EPSSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:417 <slepc4py/SLEPc/EPS.pyx#L417>`
    
        """
        ...
    def getType(self) -> str:
        """Get the EPS type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The solver currently being used.
    
        See Also
        --------
        setType, slepc.EPSGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:444 <slepc4py/SLEPc/EPS.pyx#L444>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all EPS options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this EPS object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.EPSGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:463 <slepc4py/SLEPc/EPS.pyx#L463>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all EPS options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all EPS option requests.
    
        Notes
        -----
        A hyphen (-) must NOT be given at the beginning of the prefix
        name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        For example, to distinguish between the runtime options for
        two different EPS contexts, one could call::
    
            E1.setOptionsPrefix("eig1_")
            E2.setOptionsPrefix("eig2_")
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.EPSGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:482 <slepc4py/SLEPc/EPS.pyx#L482>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all EPS options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all EPS option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.EPSAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:513 <slepc4py/SLEPc/EPS.pyx#L513>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set EPS options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help`` option.
    
        This routine must be called before `setUp()` if the user is to be
        allowed to set the solver type.
    
        See Also
        --------
        setOptionsPrefix, slepc.EPSSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:532 <slepc4py/SLEPc/EPS.pyx#L532>`
    
        """
        ...
    def getProblemType(self) -> ProblemType:
        """Get the problem type from the EPS object.
    
        Not collective.
    
        Returns
        -------
        ProblemType
            The problem type that was previously set.
    
        See Also
        --------
        setProblemType, slepc.EPSGetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:553 <slepc4py/SLEPc/EPS.pyx#L553>`
    
        """
        ...
    def setProblemType(self, problem_type: ProblemType) -> None:
        """Set the type of the eigenvalue problem.
    
        Logically collective.
    
        Parameters
        ----------
        problem_type
            The problem type to be set.
    
        Notes
        -----
        This function must be used to instruct SLEPc to exploit symmetry or
        other kind of structure. If
        no problem type is specified, by default a non-Hermitian problem is
        assumed (either standard or generalized). If the user knows that the
        problem is Hermitian (i.e., :math:`A=A^*`) or generalized Hermitian
        (i.e., :math:`A=A^*`, :math:`B=B^*`, and :math:`B` positive definite)
        then it is recommended to set the problem type so that eigensolver can
        exploit these properties.
    
        If the user does not call this function, the solver will use a
        reasonable guess.
    
        For structured problem types such as `BSE`, the matrices passed in via
        `setOperators()` must have been created with the corresponding helper
        function, i.e., `createMatBSE()`.
    
        See Also
        --------
        setOperators, createMatBSE, getProblemType, slepc.EPSSetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:572 <slepc4py/SLEPc/EPS.pyx#L572>`
    
        """
        ...
    def isGeneralized(self) -> bool:
        """Tell if the EPS object corresponds to a generalized eigenproblem.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if the problem is generalized.
    
        See Also
        --------
        isHermitian, isPositive, isStructured, slepc.EPSIsGeneralized
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:608 <slepc4py/SLEPc/EPS.pyx#L608>`
    
        """
        ...
    def isHermitian(self) -> bool:
        """Tell if the EPS object corresponds to a Hermitian eigenproblem.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if the problem is Hermitian.
    
        See Also
        --------
        isGeneralized, isPositive, isStructured, slepc.EPSIsHermitian
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:627 <slepc4py/SLEPc/EPS.pyx#L627>`
    
        """
        ...
    def isPositive(self) -> bool:
        """Eigenproblem requiring a positive (semi-) definite matrix :math:`B`.
    
        Not collective.
    
        Tell if the EPS corresponds to an eigenproblem requiring a positive
        (semi-) definite matrix :math:`B`.
    
        Returns
        -------
        bool
            ``True`` if the problem is positive (semi-) definite.
    
        See Also
        --------
        isGeneralized, isHermitian, isStructured, slepc.EPSIsPositive
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:646 <slepc4py/SLEPc/EPS.pyx#L646>`
    
        """
        ...
    def isStructured(self) -> bool:
        """Tell if the EPS object corresponds to a structured eigenvalue problem.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if the problem is structured.
    
        Notes
        -----
        The result will be ``True`` if the problem type has been set to some
        structured type such as `BSE`. This is independent of whether the input
        matrix has been built with a certain structure with a helper function.
    
        See Also
        --------
        isGeneralized, isHermitian, isPositive, slepc.EPSIsStructured
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:668 <slepc4py/SLEPc/EPS.pyx#L668>`
    
        """
        ...
    def getBalance(self) -> tuple[Balance, int, float]:
        """Get the balancing type used by the EPS, and the associated parameters.
    
        Not collective.
    
        Returns
        -------
        balance: Balance
            The balancing method.
        iterations: int
            Number of iterations of the balancing algorithm.
        cutoff: float
            Cutoff value.
    
        See Also
        --------
        setBalance, slepc.EPSGetBalance
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:693 <slepc4py/SLEPc/EPS.pyx#L693>`
    
        """
        ...
    def setBalance(self, balance: Balance | None = None, iterations: int | None = None, cutoff: float | None = None) -> None:
        """Set the balancing technique to be used by the eigensolver.
    
        Logically collective.
    
        Parameters
        ----------
        balance
            The balancing method.
        iterations
            Number of iterations of the balancing algorithm.
        cutoff
            Cutoff value.
    
        Notes
        -----
        When balancing is enabled, the solver works implicitly with matrix
        :math:`DAD^{-1}`, where :math:`D` is an appropriate diagonal matrix.
        This improves the accuracy of the computed results in some cases.
    
        Balancing makes sense only for non-Hermitian problems when the
        required precision is high (i.e., with a small tolerance).
    
        By default, balancing is disabled. The two-sided method is much more
        effective than the one-sided counterpart, but it requires the system
        matrices to have the ``Mat.multTranspose()`` operation defined.
    
        The parameter ``iterations`` is the number of iterations performed
        by the method. The ``cutoff`` value is used only in the two-side
        variant.
    
        See Also
        --------
        setBalance, slepc.EPSGetBalance
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:718 <slepc4py/SLEPc/EPS.pyx#L718>`
    
        """
        ...
    def getExtraction(self) -> Extraction:
        """Get the extraction type used by the EPS object.
    
        Not collective.
    
        Returns
        -------
        Extraction
            The method of extraction.
    
        See Also
        --------
        setExtraction, slepc.EPSGetExtraction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:768 <slepc4py/SLEPc/EPS.pyx#L768>`
    
        """
        ...
    def setExtraction(self, extraction: Extraction) -> None:
        """Set the extraction type used by the eigensolver.
    
        Logically collective.
    
        Parameters
        ----------
        extraction
            The extraction method to be used by the solver.
    
        Notes
        -----
        Not all eigensolvers support all types of extraction.
    
        By default, a standard Rayleigh-Ritz extraction is used. Other
        extractions may be useful when computing interior eigenvalues.
    
        Harmonic-type extractions are used in combination with a
        *target*, see `setTarget()`.
    
        See Also
        --------
        getExtraction, setTarget, slepc.EPSSetExtraction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:787 <slepc4py/SLEPc/EPS.pyx#L787>`
    
        """
        ...
    def getWhichEigenpairs(self) -> Which:
        """Get which portion of the spectrum is to be sought.
    
        Not collective.
    
        Returns
        -------
        Which
            The portion of the spectrum to be sought by the solver.
    
        See Also
        --------
        setWhichEigenpairs, slepc.EPSGetWhichEigenpairs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:815 <slepc4py/SLEPc/EPS.pyx#L815>`
    
        """
        ...
    def setWhichEigenpairs(self, which: Which) -> None:
        """Set which portion of the spectrum is to be sought.
    
        Logically collective.
    
        Parameters
        ----------
        which
            The portion of the spectrum to be sought by the solver.
    
        Notes
        -----
        Not all eigensolvers implemented in EPS account for all the
        possible values. Also, some values make sense only for certain
        types of problems. If SLEPc is compiled for real numbers
        `EPS.Which.LARGEST_IMAGINARY` and
        `EPS.Which.SMALLEST_IMAGINARY` use the absolute value of the
        imaginary part for eigenvalue selection.
    
        The target is a scalar value provided with `setTarget()`.
    
        The criterion `EPS.Which.TARGET_IMAGINARY` is available only
        in case PETSc and SLEPc have been built with complex scalars.
    
        `EPS.Which.ALL` is intended for use in combination with an
        interval (see `setInterval()`), when all eigenvalues within the
        interval are requested, or in the context of the `EPS.Type.CISS`
        solver for computing all eigenvalues in a region.
    
        See Also
        --------
        setTarget, setInterval, getWhichEigenpairs, slepc.EPSSetWhichEigenpairs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:834 <slepc4py/SLEPc/EPS.pyx#L834>`
    
        """
        ...
    def getThreshold(self) -> tuple[float, bool]:
        """Get the threshold used in the threshold stopping test.
    
        Not collective.
    
        Returns
        -------
        thres: float
            The threshold.
        rel: bool
            Whether the threshold is relative or not.
    
        See Also
        --------
        setThreshold, slepc.EPSGetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:871 <slepc4py/SLEPc/EPS.pyx#L871>`
    
        """
        ...
    def setThreshold(self, thres: float, rel: bool = False) -> None:
        """Set the threshold used in the threshold stopping test.
    
        Logically collective.
    
        Parameters
        ----------
        thres
            The threshold.
        rel
            Whether the threshold is relative or not.
    
        Notes
        -----
        This function internally sets a special stopping test based on
        the threshold, where eigenvalues are computed in sequence
        until one of the computed eigenvalues is below/above the
        threshold (depending on whether largest or smallest eigenvalues
        are computed). The details are given in `slepc.EPSSetThreshold`.
    
        See Also
        --------
        setStoppingTest, getThreshold, slepc.EPSSetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:893 <slepc4py/SLEPc/EPS.pyx#L893>`
    
        """
        ...
    def getTarget(self) -> Scalar:
        """Get the value of the target.
    
        Not collective.
    
        Returns
        -------
        Scalar
            The value of the target.
    
        Notes
        -----
        If the target was not set by the user, then zero is returned.
    
        See Also
        --------
        setTarget, slepc.EPSGetTarget
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:922 <slepc4py/SLEPc/EPS.pyx#L922>`
    
        """
        ...
    def setTarget(self, target: Scalar) -> None:
        """Set the value of the target.
    
        Logically collective.
    
        Parameters
        ----------
        target
            The value of the target.
    
        Notes
        -----
        The target is a scalar value used to determine the portion of
        the spectrum of interest. It is used in combination with
        `setWhichEigenpairs()`.
    
        When PETSc is built with real scalars, it is not possible to
        specify a complex target.
    
        See Also
        --------
        getTarget, slepc.EPSSetTarget
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:945 <slepc4py/SLEPc/EPS.pyx#L945>`
    
        """
        ...
    def getInterval(self) -> tuple[float, float]:
        """Get the computational interval for spectrum slicing.
    
        Not collective.
    
        Returns
        -------
        inta: float
            The left end of the interval.
        intb: float
            The right end of the interval.
    
        Notes
        -----
        If the interval was not set by the user, then zeros are returned.
    
        See Also
        --------
        setInterval, slepc.EPSGetInterval
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:972 <slepc4py/SLEPc/EPS.pyx#L972>`
    
        """
        ...
    def setInterval(self, inta: float, intb: float) -> None:
        """Set the computational interval for spectrum slicing.
    
        Logically collective.
    
        Parameters
        ----------
        inta
            The left end of the interval.
        intb
            The right end of the interval.
    
        Notes
        -----
        Spectrum slicing is a technique employed for computing all
        eigenvalues of symmetric eigenproblems in a given interval.
        This function provides the interval to be considered. It must
        be used in combination with `EPS.Which.ALL`, see
        `setWhichEigenpairs()`.
    
        A computational interval is also needed when using polynomial
        filters, see `slepc.STFILTER`.
    
        See Also
        --------
        getInterval, setWhichEigenpairs, slepc.EPSSetInterval, slepc.STFILTER
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:998 <slepc4py/SLEPc/EPS.pyx#L998>`
    
        """
        ...
    def getTolerances(self) -> tuple[float, int]:
        """Get the tolerance and max. iter. count used for convergence tests.
    
        Not collective.
    
        Get the tolerance and iteration limit used by the default EPS
        convergence tests.
    
        Returns
        -------
        tol: float
            The convergence tolerance.
        max_it: int
            The maximum number of iterations.
    
        See Also
        --------
        setTolerances, slepc.EPSGetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1032 <slepc4py/SLEPc/EPS.pyx#L1032>`
    
        """
        ...
    def setTolerances(self, tol: float | None = None, max_it: int | None = None) -> None:
        """Set the tolerance and max. iter. used by the default EPS convergence tests.
    
        Logically collective.
    
        Parameters
        ----------
        tol
            The convergence tolerance.
        max_it
            The maximum number of iterations.
    
        Notes
        -----
        Use `DETERMINE` for ``max_it`` to assign a reasonably good value,
        which is dependent on the solution method.
    
        See Also
        --------
        getTolerances, slepc.EPSSetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1057 <slepc4py/SLEPc/EPS.pyx#L1057>`
    
        """
        ...
    def getTwoSided(self) -> bool:
        """Get the flag indicating if a two-sided variant of the algorithm is being used.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether the two-sided variant is to be used or not.
    
        See Also
        --------
        setTwoSided, slepc.EPSGetTwoSided
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1085 <slepc4py/SLEPc/EPS.pyx#L1085>`
    
        """
        ...
    def setTwoSided(self, twosided: bool) -> None:
        """Set to use a two-sided variant that also computes left eigenvectors.
    
        Logically collective.
    
        Parameters
        ----------
        twosided
            Whether the two-sided variant is to be used or not.
    
        Notes
        -----
        If the user sets ``twosided`` to ``True`` then the solver uses a
        variant of the algorithm that computes both right and left
        eigenvectors. This is usually much more costly. This option is not
        available in all solvers.
    
        When using two-sided solvers, the problem matrices must have both
        the ``Mat.mult`` and ``Mat.multTranspose`` operations defined.
    
        See Also
        --------
        getTwoSided, getLeftEigenvector, slepc.EPSSetTwoSided
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1104 <slepc4py/SLEPc/EPS.pyx#L1104>`
    
        """
        ...
    def getPurify(self) -> bool:
        """Get the flag indicating whether purification is activated or not.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether purification is activated or not.
    
        See Also
        --------
        setPurify, slepc.EPSGetPurify
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1132 <slepc4py/SLEPc/EPS.pyx#L1132>`
    
        """
        ...
    def setPurify(self, purify: bool = True) -> None:
        """Set (toggle) eigenvector purification.
    
        Logically collective.
    
        Parameters
        ----------
        purify
            ``True`` to activate purification (default).
    
        Notes
        -----
        By default, eigenvectors of generalized symmetric eigenproblems are
        purified in order to purge directions in the nullspace of matrix
        :math:`B`. If the user knows that :math:`B` is non-singular, then
        purification can be safely deactivated and some computational cost
        is avoided (this is particularly important in interval computations).
    
        See Also
        --------
        getPurify, setInterval, slepc.EPSSetPurify
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1151 <slepc4py/SLEPc/EPS.pyx#L1151>`
    
        """
        ...
    def getConvergenceTest(self) -> Conv:
        """Get how to compute the error estimate used in the convergence test.
    
        Not collective.
    
        Returns
        -------
        Conv
            The method used to compute the error estimate
            used in the convergence test.
    
        See Also
        --------
        setConvergenceTest, slepc.EPSGetConvergenceTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1177 <slepc4py/SLEPc/EPS.pyx#L1177>`
    
        """
        ...
    def setConvergenceTest(self, conv: Conv) -> None:
        """Set how to compute the error estimate used in the convergence test.
    
        Logically collective.
    
        Parameters
        ----------
        conv
            The method used to compute the error estimate
            used in the convergence test.
    
        See Also
        --------
        getConvergenceTest, slepc.EPSSetConvergenceTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1197 <slepc4py/SLEPc/EPS.pyx#L1197>`
    
        """
        ...
    def getTrueResidual(self) -> bool:
        """Get the flag indicating if true residual must be computed explicitly.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether the solver computes true residuals or not.
    
        See Also
        --------
        setTrueResidual, slepc.EPSGetTrueResidual
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1216 <slepc4py/SLEPc/EPS.pyx#L1216>`
    
        """
        ...
    def setTrueResidual(self, trueres: bool) -> None:
        """Set if the solver must compute the true residual explicitly or not.
    
        Logically collective.
    
        Parameters
        ----------
        trueres
            Whether the solver computes true residuals or not.
    
        See Also
        --------
        getTrueResidual, slepc.EPSSetTrueResidual
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1235 <slepc4py/SLEPc/EPS.pyx#L1235>`
    
        """
        ...
    def getTrackAll(self) -> bool:
        """Get the flag indicating if all residual norms must be computed or not.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether the solver computes all residuals or not.
    
        See Also
        --------
        setTrackAll, slepc.EPSGetTrackAll
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1253 <slepc4py/SLEPc/EPS.pyx#L1253>`
    
        """
        ...
    def setTrackAll(self, trackall: bool) -> None:
        """Set if the solver must compute the residual of all approximate eigenpairs.
    
        Logically collective.
    
        Parameters
        ----------
        trackall
            Whether to compute all residuals or not.
    
        See Also
        --------
        getTrackAll, slepc.EPSSetTrackAll
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1272 <slepc4py/SLEPc/EPS.pyx#L1272>`
    
        """
        ...
    def getDimensions(self) -> tuple[int, int, int]:
        """Get number of eigenvalues to compute and the dimension of the subspace.
    
        Not collective.
    
        Returns
        -------
        nev: int
            Number of eigenvalues to compute.
        ncv: int
            Maximum dimension of the subspace to be used by the solver.
        mpd: int
            Maximum dimension allowed for the projected problem.
    
        See Also
        --------
        setDimensions, slepc.EPSGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1290 <slepc4py/SLEPc/EPS.pyx#L1290>`
    
        """
        ...
    def setDimensions(self, nev: int | None = None, ncv: int | None = None, mpd: int | None = None) -> None:
        """Set number of eigenvalues to compute and the dimension of the subspace.
    
        Logically collective.
    
        Parameters
        ----------
        nev
            Number of eigenvalues to compute.
        ncv
            Maximum dimension of the subspace to be used by the solver.
        mpd
            Maximum dimension allowed for the projected problem.
    
        Notes
        -----
        Use `DETERMINE` for ``ncv`` and ``mpd`` to assign a reasonably good
        value, which is dependent on the solution method.
    
        The parameters ``ncv`` and ``mpd`` are intimately related, so that
        the user is advised to set one of them at most. Normal usage
        is the following:
    
        + In cases where ``nev`` is small, the user sets ``ncv``
          (a reasonable default is 2 * ``nev``).
    
        + In cases where ``nev`` is large, the user sets ``mpd``.
    
        The value of ``ncv`` should always be between ``nev`` and (``nev`` +
        ``mpd``), typically ``ncv`` = ``nev`` + ``mpd``. If ``nev`` is not too
        large, ``mpd`` = ``nev`` is a reasonable choice, otherwise a
        smaller value should be used.
    
        When computing all eigenvalues in an interval, see `setInterval()`,
        these parameters lose relevance, and tuning must be done with
        `setKrylovSchurDimensions()`.
    
        See Also
        --------
        getDimensions, setKrylovSchurDimensions, slepc.EPSSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1315 <slepc4py/SLEPc/EPS.pyx#L1315>`
    
        """
        ...
    def getST(self) -> ST:
        """Get the spectral transformation object associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        ST
            The spectral transformation.
    
        See Also
        --------
        setST, slepc.EPSGetST
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1370 <slepc4py/SLEPc/EPS.pyx#L1370>`
    
        """
        ...
    def setST(self, st: ST) -> None:
        """Set a spectral transformation object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        st
            The spectral transformation.
    
        See Also
        --------
        getST, slepc.EPSSetST
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1390 <slepc4py/SLEPc/EPS.pyx#L1390>`
    
        """
        ...
    def getBV(self) -> BV:
        """Get the basis vectors object associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        BV
            The basis vectors context.
    
        See Also
        --------
        setBV, slepc.EPSGetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1407 <slepc4py/SLEPc/EPS.pyx#L1407>`
    
        """
        ...
    def setBV(self, bv: BV) -> None:
        """Set a basis vectors object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        bv
            The basis vectors context.
    
        See Also
        --------
        getBV, slepc.EPSSetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1427 <slepc4py/SLEPc/EPS.pyx#L1427>`
    
        """
        ...
    def getDS(self) -> DS:
        """Get the direct solver associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        DS
            The direct solver context.
    
        See Also
        --------
        setDS, slepc.EPSGetDS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1444 <slepc4py/SLEPc/EPS.pyx#L1444>`
    
        """
        ...
    def setDS(self, ds: DS) -> None:
        """Set a direct solver object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        ds
            The direct solver context.
    
        See Also
        --------
        getDS, slepc.EPSSetDS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1464 <slepc4py/SLEPc/EPS.pyx#L1464>`
    
        """
        ...
    def getRG(self) -> RG:
        """Get the region object associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        RG
            The region context.
    
        See Also
        --------
        setRG, slepc.EPSGetRG
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1481 <slepc4py/SLEPc/EPS.pyx#L1481>`
    
        """
        ...
    def setRG(self, rg: RG) -> None:
        """Set a region object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        rg
            The region context.
    
        See Also
        --------
        getRG, slepc.EPSSetRG
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1501 <slepc4py/SLEPc/EPS.pyx#L1501>`
    
        """
        ...
    def getOperators(self) -> tuple[Mat, Mat] | tuple[Mat, None]:
        """Get the matrices associated with the eigenvalue problem.
    
        Collective.
    
        Returns
        -------
        A: petsc4py.PETSc.Mat
            The matrix associated with the eigensystem.
        B: petsc4py.PETSc.Mat
            The second matrix in the case of generalized eigenproblems.
    
        See Also
        --------
        setOperators, slepc.EPSGetOperators
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1518 <slepc4py/SLEPc/EPS.pyx#L1518>`
    
        """
        ...
    def setOperators(self, A: Mat, B: Mat | None = None) -> None:
        """Set the matrices associated with the eigenvalue problem.
    
        Collective.
    
        Parameters
        ----------
        A
            The matrix associated with the eigensystem.
        B
            The second matrix in the case of generalized eigenproblems;
            if not provided, a standard eigenproblem is assumed.
    
        Notes
        -----
        It must be called before `setUp()`. If it is called again after
        `setUp()` and the matrix sizes have changed then the `EPS` object
        is reset.
    
        For structured eigenproblem types such as `BSE`, see `setProblemType()`,
        the provided matrices must have been created with the corresponding
        helper function, i.e., `createMatBSE()`.
    
        See Also
        --------
        getOperators, solve, setUp, reset, setProblemType, slepc.EPSSetOperators
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1545 <slepc4py/SLEPc/EPS.pyx#L1545>`
    
        """
        ...
    def setDeflationSpace(self, space: Vec | list[Vec]) -> None:
        """Set vectors to form a basis of the deflation space.
    
        Collective.
    
        Parameters
        ----------
        space
            Set of basis vectors of the deflation space.
    
        Notes
        -----
        When a deflation space is given, the eigensolver seeks the
        eigensolution in the restriction of the problem to the
        orthogonal complement of this space. This can be used for
        instance in the case that an invariant subspace is known
        beforehand (such as the nullspace of the matrix).
    
        These vectors do not persist from one `solve()` call to the other,
        so the deflation space should be set every time.
    
        The vectors do not need to be mutually orthonormal, since they
        are explicitly orthonormalized internally.
    
        See Also
        --------
        setInitialSpace, slepc.EPSSetDeflationSpace
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1576 <slepc4py/SLEPc/EPS.pyx#L1576>`
    
        """
        ...
    def setInitialSpace(self, space: Vec | list[Vec]) -> None:
        """Set the initial space from which the eigensolver starts to iterate.
    
        Collective.
    
        Parameters
        ----------
        space
            Set of basis vectors of the initial space.
    
        Notes
        -----
        Some solvers start to iterate on a single vector (initial vector).
        In that case, only the first vector is taken into account and the
        other vectors are ignored. But other solvers such as `SUBSPACE` are
        able to make use of the whole initial subspace as an initial guess.
    
        These vectors do not persist from one `solve()` call to the other,
        so the initial space should be set every time.
    
        The vectors do not need to be mutually orthonormal, since they are
        explicitly orthonormalized internally.
    
        Common usage of this function is when the user can provide a rough
        approximation of the wanted eigenspace. Then, convergence may be faster.
    
        See Also
        --------
        setDeflationSpace, setLeftInitialSpace, slepc.EPSSetInitialSpace
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1614 <slepc4py/SLEPc/EPS.pyx#L1614>`
    
        """
        ...
    def setLeftInitialSpace(self, space: Vec | list[Vec]) -> None:
        """Set a left initial space from which the eigensolver starts to iterate.
    
        Collective.
    
        Parameters
        ----------
        space
            Set of basis vectors of the left initial space.
    
        Notes
        -----
        Left initial vectors are used to initiate the left search space
        in two-sided eigensolvers. Users should pass here an approximation
        of the left eigenspace, if available.
    
        The same comments in `setInitialSpace()` are applicable here.
    
        See Also
        --------
        setInitialSpace, setTwoSided, slepc.EPSSetLeftInitialSpace
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1652 <slepc4py/SLEPc/EPS.pyx#L1652>`
    
        """
        ...
    def setStoppingTest(self, stopping: EPSStoppingFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set a function to decide when to stop the outer iteration of the eigensolver.
    
        Logically collective.
    
        See Also
        --------
        getStoppingTest, slepc.EPSSetStoppingTestFunction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1684 <slepc4py/SLEPc/EPS.pyx#L1684>`
    
        """
        ...
    def getStoppingTest(self) -> EPSStoppingFunction:
        """Get the stopping test function.
    
        Not collective.
    
        Returns
        -------
        EPSStoppingFunction
            The stopping test function.
    
        See Also
        --------
        setStoppingTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1708 <slepc4py/SLEPc/EPS.pyx#L1708>`
    
        """
        ...
    def setArbitrarySelection(self, arbitrary: EPSArbitraryFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set an arbitrary selection criterion function.
    
        Logically collective.
    
        Set a function to look for eigenvalues according to an arbitrary
        selection criterion. This criterion can be based on a computation
        involving the current eigenvector approximation.
    
        See Also
        --------
        getArbitrarySelection, slepc.EPSSetArbitrarySelection
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1725 <slepc4py/SLEPc/EPS.pyx#L1725>`
    
        """
        ...
    def getArbitrarySelection(self) -> EPSArbitraryFunction:
        """Get the arbitrary selection function.
    
        Not collective.
    
        Returns
        -------
        EPSArbitraryFunction
            The arbitrary selection function.
    
        See Also
        --------
        setArbitrarySelection
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1754 <slepc4py/SLEPc/EPS.pyx#L1754>`
    
        """
        ...
    def setEigenvalueComparison(self, comparison: EPSEigenvalueComparison | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set an eigenvalue comparison function.
    
        Logically collective.
    
        Notes
        -----
        This eigenvalue comparison function is used when `setWhichEigenpairs()`
        is set to `EPS.Which.USER`.
    
        See Also
        --------
        getEigenvalueComparison, slepc.EPSSetEigenvalueComparison
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1771 <slepc4py/SLEPc/EPS.pyx#L1771>`
    
        """
        ...
    def getEigenvalueComparison(self) -> EPSEigenvalueComparison:
        """Get the eigenvalue comparison function.
    
        Not collective.
    
        Returns
        -------
        EPSEigenvalueComparison
            The eigenvalue comparison function.
    
        See Also
        --------
        setEigenvalueComparison
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1801 <slepc4py/SLEPc/EPS.pyx#L1801>`
    
        """
        ...
    def setMonitor(self, monitor: EPSMonitorFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Append a monitor function to the list of monitors.
    
        Logically collective.
    
        See Also
        --------
        getMonitor, cancelMonitor, slepc.EPSMonitorSet
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1818 <slepc4py/SLEPc/EPS.pyx#L1818>`
    
        """
        ...
    def getMonitor(self) -> EPSMonitorFunction:
        """Get the list of monitor functions.
    
        Not collective.
    
        Returns
        -------
        EPSMonitorFunction
            The list of monitor functions.
    
        See Also
        --------
        setMonitor
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1843 <slepc4py/SLEPc/EPS.pyx#L1843>`
    
        """
        ...
    def cancelMonitor(self) -> None:
        """Clear all monitors for an `EPS` object.
    
        Logically collective.
    
        See Also
        --------
        slepc.EPSMonitorCancel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1860 <slepc4py/SLEPc/EPS.pyx#L1860>`
    
        """
        ...
    def setUp(self) -> None:
        """Set up all the internal data structures.
    
        Collective.
    
        Notes
        -----
        Sets up all the internal data structures necessary for the execution
        of the eigensolver. This includes the setup of the internal `ST`
        object.
    
        This function need not be called explicitly in most cases,
        since `solve()` calls it. It can be useful when one wants to
        measure the set-up time separately from the solve time.
    
        See Also
        --------
        solve, setInitialSpace, setDeflationSpace, slepc.EPSSetUp
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1875 <slepc4py/SLEPc/EPS.pyx#L1875>`
    
        """
        ...
    def solve(self) -> None:
        """Solve the eigensystem.
    
        Collective.
    
        Notes
        -----
        The problem matrices are specified with `setOperators()`.
    
        `solve()` will return without generating an error regardless of
        whether all requested solutions were computed or not. Call
        `getConverged()` to get the actual number of computed solutions,
        and `getConvergedReason()` to determine if the solver converged
        or failed and why.
    
        See Also
        --------
        setUp, setOperators, getConverged, getConvergedReason, slepc.EPSSolve
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1897 <slepc4py/SLEPc/EPS.pyx#L1897>`
    
        """
        ...
    def getIterationNumber(self) -> int:
        """Get the current iteration number.
    
        Not collective.
    
        If the call to `solve()` is complete, then it returns the number of
        iterations carried out by the solution method.
    
        Returns
        -------
        int
            Iteration number.
    
        See Also
        --------
        getConvergedReason, setTolerances, slepc.EPSGetIterationNumber
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1919 <slepc4py/SLEPc/EPS.pyx#L1919>`
    
        """
        ...
    def getConvergedReason(self) -> ConvergedReason:
        """Get the reason why the `solve()` iteration was stopped.
    
        Not collective.
    
        Returns
        -------
        ConvergedReason
            Negative value indicates diverged, positive value converged.
    
        See Also
        --------
        setTolerances, solve, slepc.EPSGetConvergedReason
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1941 <slepc4py/SLEPc/EPS.pyx#L1941>`
    
        """
        ...
    def getConverged(self) -> int:
        """Get the number of converged eigenpairs.
    
        Not collective.
    
        Returns
        -------
        nconv: int
            Number of converged eigenpairs.
    
        Notes
        -----
        This function should be called after `solve()` has finished.
    
        The value ``nconv`` may be different from the number of requested
        solutions ``nev``, but not larger than ``ncv``, see `setDimensions()`.
    
        See Also
        --------
        setDimensions, solve, getEigenpair, slepc.EPSGetConverged
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1960 <slepc4py/SLEPc/EPS.pyx#L1960>`
    
        """
        ...
    def getEigenvalue(self, i: int) -> Scalar:
        """Get the i-th eigenvalue as computed by `solve()`.
    
        Not collective.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
    
        Returns
        -------
        Scalar
            The computed eigenvalue. It will be a real variable in case
            of a Hermitian or generalized Hermitian eigenproblem. Otherwise
            it will be a complex variable (possibly with zero imaginary part).
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and ``nconv-1`` (see
        `getConverged()`). Eigenpairs are indexed according to the ordering
        criterion established with `setWhichEigenpairs()`.
    
        See Also
        --------
        getConverged, setWhichEigenpairs, getEigenpair, slepc.EPSGetEigenvalue
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:1986 <slepc4py/SLEPc/EPS.pyx#L1986>`
    
        """
        ...
    def getEigenvector(self, i: int, Vr: Vec | None = None, Vi: Vec | None = None) -> None:
        """Get the i-th right eigenvector as computed by `solve()`.
    
        Collective.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
        Vr
            Placeholder for the returned eigenvector (real part).
        Vi
            Placeholder for the returned eigenvector (imaginary part).
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and
        ``nconv-1`` (see `getConverged()`). Eigenpairs are indexed
        according to the ordering criterion established with
        `setWhichEigenpairs()`.
    
        The 2-norm of the eigenvector is one unless the problem is
        generalized Hermitian. In this case the eigenvector is normalized
        with respect to the norm defined by the B matrix.
    
        See Also
        --------
        getConverged, setWhichEigenpairs, getEigenpair, slepc.EPSGetEigenvector
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2024 <slepc4py/SLEPc/EPS.pyx#L2024>`
    
        """
        ...
    def getLeftEigenvector(self, i: int, Wr: Vec | None = None, Wi: Vec | None = None) -> None:
        """Get the i-th left eigenvector as computed by `solve()`.
    
        Collective.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
        Wr
            Placeholder for the returned left eigenvector (real part).
        Wi
            Placeholder for the returned left eigenvector (imaginary part).
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and ``nconv-1`` (see
        `getConverged()`). Eigensolutions are indexed according to the
        ordering criterion established with `setWhichEigenpairs()`.
    
        Left eigenvectors are available only if the twosided flag was set
        with `setTwoSided()`.
    
        See Also
        --------
        getConverged, setWhichEigenpairs, getEigenpair, slepc.EPSGetLeftEigenvector
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2058 <slepc4py/SLEPc/EPS.pyx#L2058>`
    
        """
        ...
    def getEigenpair(self, i: int, Vr: Vec | None = None, Vi: Vec | None = None) -> Scalar:
        """Get the i-th solution of the eigenproblem as computed by `solve()`.
    
        Collective.
    
        The solution consists of both the eigenvalue and the eigenvector.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
        Vr
            Placeholder for the returned eigenvector (real part).
        Vi
            Placeholder for the returned eigenvector (imaginary part).
    
        Returns
        -------
        e: Scalar
           The computed eigenvalue. It will be a real variable in case
           of a Hermitian or generalized Hermitian eigenproblem. Otherwise
           it will be a complex variable (possibly with zero imaginary part).
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and ``nconv-1`` (see
        `getConverged()`). Eigenpairs are indexed according to the ordering
        criterion established with `setWhichEigenpairs()`.
    
        The 2-norm of the eigenvector is one unless the problem is
        generalized Hermitian. In this case the eigenvector is normalized
        with respect to the norm defined by the B matrix.
    
        See Also
        --------
        solve, getConverged, setWhichEigenpairs, slepc.EPSGetEigenpair
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2090 <slepc4py/SLEPc/EPS.pyx#L2090>`
    
        """
        ...
    def getInvariantSubspace(self) -> list[Vec]:
        """Get an orthonormal basis of the computed invariant subspace.
    
        Collective.
    
        Returns
        -------
        list of petsc4py.PETSc.Vec
            Basis of the invariant subspace.
    
        Notes
        -----
        This function should be called after `solve()` has finished.
    
        The returned vectors span an invariant subspace associated
        with the computed eigenvalues. An invariant subspace
        :math:`X` of :math:`A` satisfies :math:`A x \in X`, for all
        :math:`x \in X` (a similar definition applies for generalized
        eigenproblems).
    
        See Also
        --------
        getEigenpair, getConverged, solve, slepc.EPSGetInvariantSubspace
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2140 <slepc4py/SLEPc/EPS.pyx#L2140>`
    
        """
        ...
    def getErrorEstimate(self, i: int) -> float:
        """Get the error estimate associated to the i-th computed eigenpair.
    
        Not collective.
    
        Parameters
        ----------
        i
            Index of the solution to be considered.
    
        Returns
        -------
        float
            Error estimate.
    
        Notes
        -----
        This is the error estimate used internally by the eigensolver.
        The actual error bound can be computed with `computeError()`.
    
        See Also
        --------
        computeError, slepc.EPSGetErrorEstimate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2184 <slepc4py/SLEPc/EPS.pyx#L2184>`
    
        """
        ...
    def computeError(self, i: int, etype: ErrorType | None = None) -> float:
        """Compute the error associated with the i-th computed eigenpair.
    
        Collective.
    
        Compute the error (based on the residual norm) associated with the
        i-th computed eigenpair.
    
        Parameters
        ----------
        i
            Index of the solution to be considered.
        etype
            The error type to compute.
    
        Returns
        -------
        float
            The error bound, computed in various ways from the residual norm
            :math:`\|Ax-\lambda Bx\|_2` where :math:`\lambda` is the eigenvalue
            and :math:`x` is the eigenvector.
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and ``nconv-1``
        (see `getConverged()`).
    
        If the computation of left eigenvectors was enabled with `setTwoSided()`,
        then the error will be computed using the maximum of the value above and
        the left residual norm  :math:`\|y^*A-\lambda y^*B\|_2`, where :math:`y`
        is the approximate left eigenvector.
    
        See Also
        --------
        getErrorEstimate, setTwoSided, slepc.EPSComputeError
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2213 <slepc4py/SLEPc/EPS.pyx#L2213>`
    
        """
        ...
    def errorView(self, etype: ErrorType | None = None, viewer: petsc4py.PETSc.Viewer | None = None) -> None:
        """Display the errors associated with the computed solution.
    
        Collective.
    
        Display the errors and the eigenvalues.
    
        Parameters
        ----------
        etype
            The error type to compute.
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        Notes
        -----
        By default, this function checks the error of all eigenpairs and prints
        the eigenvalues if all of them are below the requested tolerance.
        If the viewer has format ``ASCII_INFO_DETAIL`` then a table with
        eigenvalues and corresponding errors is printed.
    
        See Also
        --------
        solve, valuesView, vectorsView, slepc.EPSErrorView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2256 <slepc4py/SLEPc/EPS.pyx#L2256>`
    
        """
        ...
    def valuesView(self, viewer: Viewer | None = None) -> None:
        """Display the computed eigenvalues in a viewer.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        solve, vectorsView, errorView, slepc.EPSValuesView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2288 <slepc4py/SLEPc/EPS.pyx#L2288>`
    
        """
        ...
    def vectorsView(self, viewer: Viewer | None = None) -> None:
        """Output computed eigenvectors to a viewer.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        solve, valuesView, errorView, slepc.EPSVectorsView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2307 <slepc4py/SLEPc/EPS.pyx#L2307>`
    
        """
        ...
    def setPowerShiftType(self, shift: PowerShiftType) -> None:
        """Set the type of shifts used during the power iteration.
    
        Logically collective.
    
        This can be used to emulate the Rayleigh Quotient Iteration (RQI)
        method.
    
        Parameters
        ----------
        shift
            The type of shift.
    
        Notes
        -----
        This call is only relevant if the type was set to
        `EPS.Type.POWER` with `setType()`.
    
        By default, shifts are constant
        (`EPS.PowerShiftType.CONSTANT`) and the iteration is the
        simple power method (or inverse iteration if a
        shift-and-invert transformation is being used).
    
        A variable shift can be specified
        (`EPS.PowerShiftType.RAYLEIGH` or
        `EPS.PowerShiftType.WILKINSON`). In this case, the iteration
        behaves rather like a cubic converging method as RQI.
    
        See Also
        --------
        getPowerShiftType, slepc.EPSPowerSetShiftType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2328 <slepc4py/SLEPc/EPS.pyx#L2328>`
    
        """
        ...
    def getPowerShiftType(self) -> PowerShiftType:
        """Get the type of shifts used during the power iteration.
    
        Not collective.
    
        Returns
        -------
        PowerShiftType
            The type of shift.
    
        See Also
        --------
        setPowerShiftType, slepc.EPSPowerGetShiftType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2364 <slepc4py/SLEPc/EPS.pyx#L2364>`
    
        """
        ...
    def setArnoldiDelayed(self, delayed: bool) -> None:
        """Set (toggle) delayed reorthogonalization in the Arnoldi iteration.
    
        Logically collective.
    
        Parameters
        ----------
        delayed
            ``True`` if delayed reorthogonalization is to be used.
    
        Notes
        -----
        This call is only relevant if the type was set to
        `EPS.Type.ARNOLDI` with `setType()`.
    
        Delayed reorthogonalization is an aggressive optimization for
        the Arnoldi eigensolver than may provide better scalability,
        but sometimes makes the solver converge more slowly compared
        to the default algorithm.
    
        See Also
        --------
        getArnoldiDelayed, slepc.EPSArnoldiSetDelayed
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2383 <slepc4py/SLEPc/EPS.pyx#L2383>`
    
        """
        ...
    def getArnoldiDelayed(self) -> bool:
        """Get the type of reorthogonalization used during the Arnoldi iteration.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if delayed reorthogonalization is to be used.
    
        See Also
        --------
        setArnoldiDelayed, slepc.EPSArnoldiGetDelayed
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2411 <slepc4py/SLEPc/EPS.pyx#L2411>`
    
        """
        ...
    def setLanczosReorthogType(self, reorthog: LanczosReorthogType) -> None:
        """Set the type of reorthogonalization used during the Lanczos iteration.
    
        Logically collective.
    
        Parameters
        ----------
        reorthog
            The type of reorthogonalization.
    
        Notes
        -----
        This call is only relevant if the type was set to
        `EPS.Type.LANCZOS` with `setType()`.
    
        See Also
        --------
        getLanczosReorthogType, slepc.EPSLanczosSetReorthog
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2430 <slepc4py/SLEPc/EPS.pyx#L2430>`
    
        """
        ...
    def getLanczosReorthogType(self) -> LanczosReorthogType:
        """Get the type of reorthogonalization used during the Lanczos iteration.
    
        Not collective.
    
        Returns
        -------
        LanczosReorthogType
            The type of reorthogonalization.
    
        See Also
        --------
        setLanczosReorthogType, slepc.EPSLanczosGetReorthog
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2453 <slepc4py/SLEPc/EPS.pyx#L2453>`
    
        """
        ...
    def setKrylovSchurBSEType(self, bse: KrylovSchurBSEType) -> None:
        """Set the Krylov-Schur variant used for BSE structured eigenproblems.
    
        Logically collective.
    
        Parameters
        ----------
        bse
            The BSE method.
    
        Notes
        -----
        This call is only relevant if the type was set to
        `EPS.Type.KRYLOVSCHUR` with `setType()` and the problem
        type to `EPS.ProblemType.BSE` with `setProblemType()`.
    
        See Also
        --------
        createMatBSE, getKrylovSchurBSEType, slepc.EPSKrylovSchurSetBSEType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2475 <slepc4py/SLEPc/EPS.pyx#L2475>`
    
        """
        ...
    def getKrylovSchurBSEType(self) -> KrylovSchurBSEType:
        """Get the method used for BSE structured eigenproblems (Krylov-Schur).
    
        Not collective.
    
        Returns
        -------
        KrylovSchurBSEType
            The BSE method.
    
        See Also
        --------
        setKrylovSchurBSEType, slepc.EPSKrylovSchurGetBSEType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2499 <slepc4py/SLEPc/EPS.pyx#L2499>`
    
        """
        ...
    def setKrylovSchurRestart(self, keep: float) -> None:
        """Set the restart parameter for the Krylov-Schur method.
    
        Logically collective.
    
        It is the proportion of basis vectors that must be kept after restart.
    
        Parameters
        ----------
        keep
            The number of vectors to be kept at restart.
    
        Notes
        -----
        Allowed values are in the range [0.1,0.9]. The default is 0.5.
    
        See Also
        --------
        getKrylovSchurRestart, slepc.EPSKrylovSchurSetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2518 <slepc4py/SLEPc/EPS.pyx#L2518>`
    
        """
        ...
    def getKrylovSchurRestart(self) -> float:
        """Get the restart parameter used in the Krylov-Schur method.
    
        Not collective.
    
        Returns
        -------
        float
            The number of vectors to be kept at restart.
    
        See Also
        --------
        setKrylovSchurRestart, slepc.EPSKrylovSchurGetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2542 <slepc4py/SLEPc/EPS.pyx#L2542>`
    
        """
        ...
    def setKrylovSchurLocking(self, lock: bool) -> None:
        """Set (toggle) locking/non-locking variants of the Krylov-Schur method.
    
        Logically collective.
    
        Parameters
        ----------
        lock
            ``True`` if the locking variant must be selected.
    
        Notes
        -----
        The default is to lock converged eigenpairs when the method restarts.
        This behavior can be changed so that all directions are kept in the
        working subspace even if already converged to working accuracy (the
        non-locking variant).
    
        See Also
        --------
        getKrylovSchurLocking, slepc.EPSKrylovSchurSetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2561 <slepc4py/SLEPc/EPS.pyx#L2561>`
    
        """
        ...
    def getKrylovSchurLocking(self) -> bool:
        """Get the locking flag used in the Krylov-Schur method.
    
        Not collective.
    
        Returns
        -------
        bool
            The locking flag.
    
        See Also
        --------
        setKrylovSchurLocking, slepc.EPSKrylovSchurGetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2586 <slepc4py/SLEPc/EPS.pyx#L2586>`
    
        """
        ...
    def setKrylovSchurPartitions(self, npart: int) -> None:
        """Set the number of partitions of the communicator (spectrum slicing).
    
        Logically collective.
    
        Set the number of partitions for the case of doing spectrum
        slicing for a computational interval with the communicator split
        in several sub-communicators.
    
        Parameters
        ----------
        npart
            The number of partitions.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        By default, ``npart=1`` so all processes in the communicator participate
        in the processing of the whole interval. If ``npart>1`` then the interval
        is divided into ``npart`` subintervals, each of them being processed by a
        subset of processes.
    
        The interval is split proportionally unless the separation points are
        specified with `setKrylovSchurSubintervals()`.
    
        See Also
        --------
        setInterval, getKrylovSchurPartitions, slepc.EPSKrylovSchurSetPartitions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2605 <slepc4py/SLEPc/EPS.pyx#L2605>`
    
        """
        ...
    def getKrylovSchurPartitions(self) -> int:
        """Get the number of partitions of the communicator (spectrum slicing).
    
        Not collective.
    
        Returns
        -------
        int
            The number of partitions.
    
        See Also
        --------
        setKrylovSchurPartitions, slepc.EPSKrylovSchurGetPartitions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2640 <slepc4py/SLEPc/EPS.pyx#L2640>`
    
        """
        ...
    def setKrylovSchurDetectZeros(self, detect: bool) -> None:
        """Set the flag that enforces zero detection in spectrum slicing.
    
        Logically collective.
    
        Set a flag to enforce the detection of zeros during the factorizations
        throughout the spectrum slicing computation.
    
        Parameters
        ----------
        detect
            ``True`` if zeros must checked for.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        A zero in the factorization indicates that a shift coincides with
        an eigenvalue.
    
        This flag is turned off by default, and may be necessary in some cases,
        especially when several partitions are being used. This feature currently
        requires an external package for factorizations with support for zero
        detection, e.g., MUMPS.
    
        See Also
        --------
        setInterval, getKrylovSchurDetectZeros, slepc.EPSKrylovSchurSetDetectZeros
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2659 <slepc4py/SLEPc/EPS.pyx#L2659>`
    
        """
        ...
    def getKrylovSchurDetectZeros(self) -> bool:
        """Get the flag that enforces zero detection in spectrum slicing.
    
        Not collective.
    
        Returns
        -------
        bool
            The zero detection flag.
    
        See Also
        --------
        setKrylovSchurDetectZeros, slepc.EPSKrylovSchurGetDetectZeros
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2693 <slepc4py/SLEPc/EPS.pyx#L2693>`
    
        """
        ...
    def setKrylovSchurDimensions(self, nev: int | None = None, ncv: int | None = None, mpd: int | None = None) -> None:
        """Set the dimensions used for each subsolve step (spectrum slicing).
    
        Logically collective.
    
        Parameters
        ----------
        nev
            Number of eigenvalues to compute.
        ncv
            Maximum dimension of the subspace to be used by the solver.
        mpd
            Maximum dimension allowed for the projected problem.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        The meaning of the parameters is the same as in `setDimensions()`, but
        the ones here apply to every subsolve done by the child `EPS` object.
    
        See Also
        --------
        setInterval, getKrylovSchurDimensions, slepc.EPSKrylovSchurSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2712 <slepc4py/SLEPc/EPS.pyx#L2712>`
    
        """
        ...
    def getKrylovSchurDimensions(self) -> tuple[int, int, int]:
        """Get the dimensions used for each subsolve step (spectrum slicing).
    
        Not collective.
    
        Returns
        -------
        nev: int
            Number of eigenvalues to compute.
        ncv: int
            Maximum dimension of the subspace to be used by the solver.
        mpd: int
            Maximum dimension allowed for the projected problem.
    
        See Also
        --------
        setKrylovSchurDimensions, slepc.EPSKrylovSchurGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2752 <slepc4py/SLEPc/EPS.pyx#L2752>`
    
        """
        ...
    def getKrylovSchurSubcommInfo(self) -> tuple[int, int, Vec]:
        """Get information related to the case of doing spectrum slicing.
    
        Collective on the subcommunicator.
    
        Get information related to the case of doing spectrum slicing
        for a computational interval with multiple communicators.
    
        Returns
        -------
        k: int
            Index of the subinterval for the calling process.
        n: int
            Number of eigenvalues found in the ``k``-th subinterval.
        v: petsc4py.PETSc.Vec
            A vector owned by processes in the subcommunicator with dimensions
            compatible for locally computed eigenvectors.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        See Also
        --------
        getKrylovSchurSubcommPairs, slepc.EPSKrylovSchurGetSubcommInfo
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2777 <slepc4py/SLEPc/EPS.pyx#L2777>`
    
        """
        ...
    def getKrylovSchurSubcommPairs(self, i: int, v: Vec | None = None) -> Scalar:
        """Get the i-th eigenpair stored in the multi-communicator of the process.
    
        Collective on the subcommunicator (if v is given).
    
        Get the i-th eigenpair stored internally in the multi-communicator
        to which the calling process belongs.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
        v
            Placeholder for the returned eigenvector.
    
        Returns
        -------
        Scalar
            The computed eigenvalue.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
        And is relevant only when the number of partitions
        (`setKrylovSchurPartitions()`) is larger than one.
    
        Argument ``v`` must be a valid ``Vec`` object, created by calling
        `getKrylovSchurSubcommInfo()`.
    
        The index ``i`` should be a value between ``0`` and ``n-1``,
        where ``n`` is the number of vectors in the local subinterval,
        see `getKrylovSchurSubcommInfo()`.
    
        See Also
        --------
        getKrylovSchurSubcommMats, slepc.EPSKrylovSchurGetSubcommPairs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2811 <slepc4py/SLEPc/EPS.pyx#L2811>`
    
        """
        ...
    def getKrylovSchurSubcommMats(self) -> tuple[Mat, Mat] | tuple[Mat, None]:
        """Get the eigenproblem matrices stored in the subcommunicator.
    
        Collective on the subcommunicator.
    
        Get the eigenproblem matrices stored internally in the subcommunicator
        to which the calling process belongs.
    
        Returns
        -------
        A: petsc4py.PETSc.Mat
            The matrix associated with the eigensystem.
        B: petsc4py.PETSc.Mat
            The second matrix in the case of generalized eigenproblems.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
        And is relevant only when the number of partitions
        (`setKrylovSchurPartitions()`) is larger than one.
    
        This is the analog of `getOperators()`, but returns the matrices distributed
        differently (in the subcommunicator rather than in the parent communicator).
    
        These matrices should not be modified by the user.
    
        See Also
        --------
        setInterval, setKrylovSchurPartitions, slepc.EPSKrylovSchurGetSubcommMats
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2855 <slepc4py/SLEPc/EPS.pyx#L2855>`
    
        """
        ...
    def updateKrylovSchurSubcommMats(self, s: Scalar = 1.0, a: Scalar = 1.0, Au: petsc4py.PETSc.Mat | None = None, t: Scalar = 1.0, b: Scalar = 1.0, Bu: petsc4py.PETSc.Mat | None = None, structure: petsc4py.PETSc.Mat.Structure | None = None, globalup: bool = False) -> None:
        """Update the eigenproblem matrices stored internally in the communicator.
    
        Collective.
    
        Update the eigenproblem matrices stored internally in the
        subcommunicator to which the calling process belongs.
    
        Parameters
        ----------
        s
            Scalar that multiplies the existing A matrix.
        a
            Scalar used in the axpy operation on A.
        Au
            The matrix used in the axpy operation on A.
        t
            Scalar that multiplies the existing B matrix.
        b
            Scalar used in the axpy operation on B.
        Bu
            The matrix used in the axpy operation on B.
        structure
            Either same, different, or a subset of the non-zero sparsity pattern.
        globalup
            Whether global matrices must be updated or not.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
        And is relevant only when the number of partitions
        (`setKrylovSchurPartitions()`) is larger than one.
    
        This function modifies the eigenproblem matrices at subcommunicator
        level, and optionally updates the global matrices in the parent
        communicator.  The updates are expressed as
        :math:`A \leftarrow s A + a Au`,
        :math:`B \leftarrow t B + b Bu`.
    
        It is possible to update one of the matrices, or both.
    
        The matrices ``Au`` and ``Bu`` must be equal in all subcommunicators.
    
        The ``structure`` flag is passed to the `petsc4py.PETSc.Mat.axpy`
        operations to perform the updates.
    
        If ``globalup`` is ``True``, communication is carried out to reconstruct
        the updated matrices in the parent communicator.
    
        See Also
        --------
        setInterval, setKrylovSchurPartitions, slepc.EPSKrylovSchurUpdateSubcommMats
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2897 <slepc4py/SLEPc/EPS.pyx#L2897>`
    
        """
        ...
    def setKrylovSchurSubintervals(self, subint: Sequence[float]) -> None:
        """Set the subinterval boundaries.
    
        Logically collective.
    
        Set the subinterval boundaries for spectrum slicing with a
        computational interval with several partitions.
    
        Parameters
        ----------
        subint
            Real values specifying subintervals.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        This function must be called after `setKrylovSchurPartitions()`.
        For ``npart`` partitions, the argument ``subint`` must contain
        ``npart+1`` real values sorted in ascending order:
        ``subint_0``, ``subint_1``, ..., ``subint_npart``,
        where the first and last values must coincide with the interval
        endpoints set with `setInterval()`.
        The subintervals are then defined by two consecutive points:
        ``[subint_0,subint_1]``, ``[subint_1,subint_2]``, and so on.
    
        See Also
        --------
        setInterval, setKrylovSchurPartitions, slepc.EPSKrylovSchurSetSubintervals
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:2968 <slepc4py/SLEPc/EPS.pyx#L2968>`
    
        """
        ...
    def getKrylovSchurSubintervals(self) -> ArrayReal:
        """Get the points that delimit the subintervals.
    
        Not collective.
    
        Get the points that delimit the subintervals used in spectrum slicing
        with several partitions.
    
        Returns
        -------
        ArrayReal
            Real values specifying subintervals.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        If the user passed values with `setKrylovSchurSubintervals()`, then the
        same values are returned here. Otherwise, the values computed internally
        are obtained.
    
        See Also
        --------
        setKrylovSchurSubintervals, slepc.EPSKrylovSchurGetSubintervals
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3012 <slepc4py/SLEPc/EPS.pyx#L3012>`
    
        """
        ...
    def getKrylovSchurInertias(self) -> tuple[ArrayReal, ArrayInt]:
        """Get the values of the shifts and their corresponding inertias.
    
        Not collective.
    
        Get the values of the shifts and their corresponding inertias in case
        of doing spectrum slicing for a computational interval.
    
        Returns
        -------
        shifts: ArrayReal
            The values of the shifts used internally in the solver.
        inertias: ArrayInt
            The values of the inertia in each shift.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        If called after `solve()`, all shifts used internally by the solver are
        returned (including both endpoints and any intermediate ones). If called
        before `solve()` and after `setUp()` then only the information of the
        endpoints of subintervals is available.
    
        See Also
        --------
        setInterval, setKrylovSchurSubintervals, slepc.EPSKrylovSchurGetInertias
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3050 <slepc4py/SLEPc/EPS.pyx#L3050>`
    
        """
        ...
    def getKrylovSchurKSP(self) -> KSP:
        """Get the linear solver object associated with the internal `EPS` object.
    
        Collective.
    
        Get the linear solver object associated with the internal `EPS`
        object in case of doing spectrum slicing for a computational interval.
    
        Returns
        -------
        `petsc4py.PETSc.KSP`
            The linear solver object.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        When invoked to compute all eigenvalues in an interval with spectrum
        slicing, `KRYLOVSCHUR` creates another `EPS` object internally that is
        used to compute eigenvalues by chunks near selected shifts. This function
        allows access to the ``KSP`` object associated to this internal `EPS`
        object.
    
        In case of having more than one partition, the returned ``KSP`` will be
        different in MPI processes belonging to different partitions. Hence, if
        required, `setKrylovSchurPartitions()` must be called BEFORE this
        function.
    
        See Also
        --------
        setInterval, setKrylovSchurPartitions, slepc.EPSKrylovSchurGetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3094 <slepc4py/SLEPc/EPS.pyx#L3094>`
    
        """
        ...
    def setGDKrylovStart(self, krylovstart: bool = True) -> None:
        """Set (toggle) starting the search subspace with a Krylov basis.
    
        Logically collective.
    
        Parameters
        ----------
        krylovstart
            ``True`` if starting the search subspace with a Krylov basis.
    
        See Also
        --------
        setGDInitialSize, getGDKrylovStart, slepc.EPSGDSetKrylovStart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3135 <slepc4py/SLEPc/EPS.pyx#L3135>`
    
        """
        ...
    def getGDKrylovStart(self) -> bool:
        """Get a flag indicating if the search subspace is started with a Krylov basis.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if starting the search subspace with a Krylov basis.
    
        See Also
        --------
        setGDKrylovStart, slepc.EPSGDGetKrylovStart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3153 <slepc4py/SLEPc/EPS.pyx#L3153>`
    
        """
        ...
    def setGDBlockSize(self, bs: int) -> None:
        """Set the number of vectors to be added to the searching space.
    
        Logically collective.
    
        Set the number of vectors to be added to the searching space in every
        iteration.
    
        Parameters
        ----------
        bs
            The number of vectors added to the search space in every iteration.
    
        See Also
        --------
        getGDBlockSize, slepc.EPSGDSetBlockSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3172 <slepc4py/SLEPc/EPS.pyx#L3172>`
    
        """
        ...
    def getGDBlockSize(self) -> int:
        """Get the number of vectors to be added to the searching space.
    
        Not collective.
    
        Get the number of vectors to be added to the searching space in every
        iteration.
    
        Returns
        -------
        int
            The number of vectors added to the search space in every iteration.
    
        See Also
        --------
        setGDBlockSize, slepc.EPSGDGetBlockSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3193 <slepc4py/SLEPc/EPS.pyx#L3193>`
    
        """
        ...
    def setGDRestart(self, minv: int = None, plusk: int = None) -> None:
        """Set the number of vectors of the search space after restart.
    
        Logically collective.
    
        Set the number of vectors of the search space after restart and
        the number of vectors saved from the previous iteration.
    
        Parameters
        ----------
        minv
            The number of vectors of the search subspace after restart.
        plusk
            The number of vectors saved from the previous iteration.
    
        See Also
        --------
        getGDRestart, slepc.EPSGDSetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3215 <slepc4py/SLEPc/EPS.pyx#L3215>`
    
        """
        ...
    def getGDRestart(self) -> tuple[int, int]:
        """Get the number of vectors of the search space after restart.
    
        Not collective.
    
        Get the number of vectors of the search space after restart and
        the number of vectors saved from the previous iteration.
    
        Returns
        -------
        minv: int
            The number of vectors of the search subspace after restart.
        plusk: int
            The number of vectors saved from the previous iteration.
    
        See Also
        --------
        setGDRestart, slepc.EPSGDGetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3241 <slepc4py/SLEPc/EPS.pyx#L3241>`
    
        """
        ...
    def setGDInitialSize(self, initialsize: int) -> None:
        """Set the initial size of the searching space.
    
        Logically collective.
    
        Parameters
        ----------
        initialsize
            The number of vectors of the initial searching subspace.
    
        Notes
        -----
        If the flag in `setGDKrylovStart()` is set to ``False`` and the user
        provides vectors with `setInitialSpace()`, up to ``initialsize``
        vectors will be used; and if the provided vectors are not enough, the
        solver completes the subspace with random vectors. In case the
        `setGDKrylovStart()` flag is ``True``, the solver gets the first
        vector provided by the user or, if not available, a random vector,
        and expands the Krylov basis up to ``initialsize`` vectors.
    
        See Also
        --------
        setGDKrylovStart, getGDInitialSize, slepc.EPSGDSetInitialSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3266 <slepc4py/SLEPc/EPS.pyx#L3266>`
    
        """
        ...
    def getGDInitialSize(self) -> int:
        """Get the initial size of the searching space.
    
        Not collective.
    
        Returns
        -------
        int
            The number of vectors of the initial searching subspace.
    
        See Also
        --------
        setGDInitialSize, slepc.EPSGDGetInitialSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3294 <slepc4py/SLEPc/EPS.pyx#L3294>`
    
        """
        ...
    def setGDBOrth(self, borth: bool) -> None:
        """Set the orthogonalization that will be used in the search subspace.
    
        Logically collective.
    
        Set the orthogonalization that will be used in the search
        subspace in case of generalized Hermitian problems.
    
        Parameters
        ----------
        borth
            Whether to B-orthogonalize the search subspace.
    
        See Also
        --------
        getGDBOrth, slepc.EPSGDSetBOrth
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3313 <slepc4py/SLEPc/EPS.pyx#L3313>`
    
        """
        ...
    def getGDBOrth(self) -> bool:
        """Get the orthogonalization used in the search subspace.
    
        Not collective.
    
        Get the orthogonalization used in the search subspace in
        case of generalized Hermitian problems.
    
        Returns
        -------
        bool
            Whether to B-orthogonalize the search subspace.
    
        See Also
        --------
        setGDBOrth, slepc.EPSGDGetBOrth
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3334 <slepc4py/SLEPc/EPS.pyx#L3334>`
    
        """
        ...
    def setGDDoubleExpansion(self, doubleexp: bool) -> None:
        """Set that the search subspace is expanded with double expansion.
    
        Logically collective.
    
        Parameters
        ----------
        doubleexp
            ``True`` if using double expansion.
    
        Notes
        -----
        In the double expansion variant the search subspace is expanded with
        :math:`K [A x, B x]` (double expansion) instead of the
        classic :math:`K r`, where :math:`K` is the preconditioner, :math:`x`
        the selected approximate eigenvector and :math:`r` its associated
        residual vector.
    
        See Also
        --------
        getGDDoubleExpansion, slepc.EPSGDSetDoubleExpansion
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3356 <slepc4py/SLEPc/EPS.pyx#L3356>`
    
        """
        ...
    def getGDDoubleExpansion(self) -> bool:
        """Get a flag indicating whether the double expansion variant is active.
    
        Not collective.
    
        Get a flag indicating whether the double expansion variant
        has been activated or not.
    
        Returns
        -------
        bool
            ``True`` if using double expansion.
    
        See Also
        --------
        setGDDoubleExpansion, slepc.EPSGDGetDoubleExpansion
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3382 <slepc4py/SLEPc/EPS.pyx#L3382>`
    
        """
        ...
    def setJDKrylovStart(self, krylovstart: bool = True) -> None:
        """Set (toggle) starting the search subspace with a Krylov basis.
    
        Logically collective.
    
        Parameters
        ----------
        krylovstart
            ``True`` if starting the search subspace with a Krylov basis.
    
        See Also
        --------
        setJDInitialSize, getJDKrylovStart, slepc.EPSJDSetKrylovStart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3406 <slepc4py/SLEPc/EPS.pyx#L3406>`
    
        """
        ...
    def getJDKrylovStart(self) -> bool:
        """Get a flag indicating if the search subspace is started with a Krylov basis.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if starting the search subspace with a Krylov basis.
    
        See Also
        --------
        setJDKrylovStart, slepc.EPSJDGetKrylovStart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3424 <slepc4py/SLEPc/EPS.pyx#L3424>`
    
        """
        ...
    def setJDBlockSize(self, bs: int) -> None:
        """Set the number of vectors to be added to the searching space.
    
        Logically collective.
    
        Set the number of vectors to be added to the searching space in every
        iteration.
    
        Parameters
        ----------
        bs
            The number of vectors added to the search space in every iteration.
    
        See Also
        --------
        getJDBlockSize, slepc.EPSJDSetBlockSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3443 <slepc4py/SLEPc/EPS.pyx#L3443>`
    
        """
        ...
    def getJDBlockSize(self) -> int:
        """Get the number of vectors to be added to the searching space.
    
        Not collective.
    
        Get the number of vectors to be added to the searching space in every
        iteration.
    
        Returns
        -------
        int
            The number of vectors added to the search space in every iteration.
    
        See Also
        --------
        setJDBlockSize, slepc.EPSJDGetBlockSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3464 <slepc4py/SLEPc/EPS.pyx#L3464>`
    
        """
        ...
    def setJDRestart(self, minv: int | None = None, plusk: int | None = None) -> None:
        """Set the number of vectors of the search space after restart.
    
        Logically collective.
    
        Set the number of vectors of the search space after restart and
        the number of vectors saved from the previous iteration.
    
        Parameters
        ----------
        minv
            The number of vectors of the search subspace after restart.
        plusk
            The number of vectors saved from the previous iteration.
    
        See Also
        --------
        getJDRestart, slepc.EPSJDSetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3486 <slepc4py/SLEPc/EPS.pyx#L3486>`
    
        """
        ...
    def getJDRestart(self) -> tuple[int, int]:
        """Get the number of vectors of the search space after restart.
    
        Not collective.
    
        Get the number of vectors of the search space after restart and
        the number of vectors saved from the previous iteration.
    
        Returns
        -------
        minv: int
            The number of vectors of the search subspace after restart.
        plusk: int
            The number of vectors saved from the previous iteration.
    
        See Also
        --------
        setJDRestart, slepc.EPSJDGetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3512 <slepc4py/SLEPc/EPS.pyx#L3512>`
    
        """
        ...
    def setJDInitialSize(self, initialsize: int) -> None:
        """Set the initial size of the searching space.
    
        Logically collective.
    
        Parameters
        ----------
        initialsize
            The number of vectors of the initial searching subspace.
    
        Notes
        -----
        If the flag in `setJDKrylovStart()` is set to ``False`` and the user
        provides vectors with `setInitialSpace()`, up to ``initialsize``
        vectors will be used; and if the provided vectors are not enough, the
        solver completes the subspace with random vectors. In case the
        `setJDKrylovStart()` flag is ``True``, the solver gets the first
        vector provided by the user or, if not available, a random vector,
        and expands the Krylov basis up to ``initialsize`` vectors.
    
        See Also
        --------
        setJDKrylovStart, getJDInitialSize, slepc.EPSJDSetInitialSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3537 <slepc4py/SLEPc/EPS.pyx#L3537>`
    
        """
        ...
    def getJDInitialSize(self) -> int:
        """Get the initial size of the searching space.
    
        Not collective.
    
        Returns
        -------
        int
            The number of vectors of the initial searching subspace.
    
        See Also
        --------
        setJDInitialSize, slepc.EPSJDGetInitialSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3565 <slepc4py/SLEPc/EPS.pyx#L3565>`
    
        """
        ...
    def setJDFix(self, fix: float) -> None:
        """Set the threshold for changing the target in the correction equation.
    
        Logically collective.
    
        Parameters
        ----------
        fix
            The threshold for changing the target.
    
        Notes
        -----
        The target in the correction equation is fixed at the first iterations.
        When the norm of the residual vector is lower than the ``fix`` value,
        the target is set to the corresponding eigenvalue.
    
        See Also
        --------
        getJDFix, slepc.EPSJDSetFix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3584 <slepc4py/SLEPc/EPS.pyx#L3584>`
    
        """
        ...
    def getJDFix(self) -> float:
        """Get the threshold for changing the target in the correction equation.
    
        Not collective.
    
        Returns
        -------
        float
            The threshold for changing the target.
    
        See Also
        --------
        setJDFix, slepc.EPSJDGetFix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3608 <slepc4py/SLEPc/EPS.pyx#L3608>`
    
        """
        ...
    def setJDConstCorrectionTol(self, constant: bool) -> None:
        """Deactivate the dynamic stopping criterion.
    
        Logically collective.
    
        Parameters
        ----------
        constant
            If ``False``, the `petsc4py.PETSc.KSP` relative tolerance is set
            to ``0.5**i``.
    
        Notes
        -----
        If this flag is set to ``False``, then the `petsc4py.PETSc.KSP`
        relative tolerance is dynamically set to ``0.5**i``, where ``i`` is
        the number of `EPS` iterations since the last converged value.
        By the default, a constant tolerance is used.
    
        See Also
        --------
        getJDConstCorrectionTol, slepc.EPSJDSetConstCorrectionTol
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3627 <slepc4py/SLEPc/EPS.pyx#L3627>`
    
        """
        ...
    def getJDConstCorrectionTol(self) -> bool:
        """Get the flag indicating if the dynamic stopping is being used.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if the dynamic stopping criterion is not being used.
    
        See Also
        --------
        setJDConstCorrectionTol, slepc.EPSJDGetConstCorrectionTol
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3653 <slepc4py/SLEPc/EPS.pyx#L3653>`
    
        """
        ...
    def setJDBOrth(self, borth: bool) -> None:
        """Set the orthogonalization that will be used in the search subspace.
    
        Logically collective.
    
        Set the orthogonalization that will be used in the search
        subspace in case of generalized Hermitian problems.
    
        Parameters
        ----------
        borth
            Whether to B-orthogonalize the search subspace.
    
        See Also
        --------
        getJDBOrth, slepc.EPSJDSetBOrth
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3672 <slepc4py/SLEPc/EPS.pyx#L3672>`
    
        """
        ...
    def getJDBOrth(self) -> bool:
        """Get the orthogonalization used in the search subspace.
    
        Not collective.
    
        Get the orthogonalization used in the search subspace in
        case of generalized Hermitian problems.
    
        Returns
        -------
        bool
            Whether to B-orthogonalize the search subspace.
    
        See Also
        --------
        setJDBOrth, slepc.EPSJDGetBOrth
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3693 <slepc4py/SLEPc/EPS.pyx#L3693>`
    
        """
        ...
    def setRQCGReset(self, nrest: int) -> None:
        """Set the reset parameter of the RQCG iteration.
    
        Logically collective.
    
        Parameters
        ----------
        nrest
            The number of iterations between resets.
    
        Notes
        -----
        Every ``nrest`` iterations the solver performs a Rayleigh-Ritz
        projection step.
    
        See Also
        --------
        getRQCGReset, slepc.EPSRQCGSetReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3717 <slepc4py/SLEPc/EPS.pyx#L3717>`
    
        """
        ...
    def getRQCGReset(self) -> int:
        """Get the reset parameter used in the RQCG method.
    
        Not collective.
    
        Returns
        -------
        int
            The number of iterations between resets.
    
        See Also
        --------
        setRQCGReset, slepc.EPSRQCGGetReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3740 <slepc4py/SLEPc/EPS.pyx#L3740>`
    
        """
        ...
    def setLOBPCGBlockSize(self, bs: int) -> None:
        """Set the block size of the LOBPCG method.
    
        Logically collective.
    
        Parameters
        ----------
        bs
            The block size.
    
        See Also
        --------
        getLOBPCGBlockSize, slepc.EPSLOBPCGSetBlockSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3759 <slepc4py/SLEPc/EPS.pyx#L3759>`
    
        """
        ...
    def getLOBPCGBlockSize(self) -> int:
        """Get the block size used in the LOBPCG method.
    
        Not collective.
    
        Returns
        -------
        int
            The block size.
    
        See Also
        --------
        setLOBPCGBlockSize, slepc.EPSLOBPCGGetBlockSize
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3777 <slepc4py/SLEPc/EPS.pyx#L3777>`
    
        """
        ...
    def setLOBPCGRestart(self, restart: float) -> None:
        """Set the restart parameter for the LOBPCG method.
    
        Logically collective.
    
        Parameters
        ----------
        restart
            The percentage of the block of vectors to force a restart.
    
        Notes
        -----
        The meaning of this parameter is the proportion of vectors within the
        current block iterate that must have converged in order to force a
        restart with hard locking.
        Allowed values are in the range [0.1,1.0]. The default is 0.9.
    
        See Also
        --------
        getLOBPCGRestart, slepc.EPSLOBPCGSetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3796 <slepc4py/SLEPc/EPS.pyx#L3796>`
    
        """
        ...
    def getLOBPCGRestart(self) -> float:
        """Get the restart parameter used in the LOBPCG method.
    
        Not collective.
    
        Returns
        -------
        float
            The restart parameter.
    
        See Also
        --------
        setLOBPCGRestart, slepc.EPSLOBPCGGetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3821 <slepc4py/SLEPc/EPS.pyx#L3821>`
    
        """
        ...
    def setLOBPCGLocking(self, lock: bool) -> None:
        """Toggle between locking and non-locking (LOBPCG method).
    
        Logically collective.
    
        Parameters
        ----------
        lock
            ``True`` if the locking variant must be selected.
    
        Notes
        -----
        This flag refers to soft locking (converged vectors within the current
        block iterate), since hard locking is always used (when ``nev`` is
        larger than the block size).
    
        See Also
        --------
        getLOBPCGLocking, slepc.EPSLOBPCGSetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3840 <slepc4py/SLEPc/EPS.pyx#L3840>`
    
        """
        ...
    def getLOBPCGLocking(self) -> bool:
        """Get the locking flag used in the LOBPCG method.
    
        Not collective.
    
        Returns
        -------
        bool
            The locking flag.
    
        See Also
        --------
        setLOBPCGLocking, slepc.EPSLOBPCGGetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3864 <slepc4py/SLEPc/EPS.pyx#L3864>`
    
        """
        ...
    def setLyapIIRanks(self, rkc: int | None = None, rkl: int | None = None) -> None:
        """Set the ranks used in the solution of the Lyapunov equation.
    
        Logically collective.
    
        Parameters
        ----------
        rkc
            The compressed rank.
        rkl
            The Lyapunov rank.
    
        Notes
        -----
        Lyapunov inverse iteration needs to solve a large-scale Lyapunov
        equation at each iteration of the eigensolver. For this, an iterative
        solver (`LME`) is used, which requires to prescribe the rank of the
        solution matrix :math:`X`. This is the meaning of parameter ``rkl``.
        Later, this matrix is compressed into another matrix of rank ``rkc``.
        If not provided, ``rkl`` is a small multiple of ``rkc``.
    
        See Also
        --------
        getLyapIIRanks, slepc.EPSLyapIISetRanks
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3883 <slepc4py/SLEPc/EPS.pyx#L3883>`
    
        """
        ...
    def getLyapIIRanks(self) -> tuple[int, int]:
        """Get the rank values used for the Lyapunov step.
    
        Not collective.
    
        Returns
        -------
        rkc: int
            The compressed rank.
        rkl: int
            The Lyapunov rank.
    
        See Also
        --------
        setLyapIIRanks, slepc.EPSLyapIIGetRanks
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3915 <slepc4py/SLEPc/EPS.pyx#L3915>`
    
        """
        ...
    def setCISSExtraction(self, extraction: CISSExtraction) -> None:
        """Set the extraction technique used in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        extraction
            The extraction technique.
    
        See Also
        --------
        getCISSExtraction, slepc.EPSCISSSetExtraction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3939 <slepc4py/SLEPc/EPS.pyx#L3939>`
    
        """
        ...
    def getCISSExtraction(self) -> CISSExtraction:
        """Get the extraction technique used in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        CISSExtraction
            The extraction technique.
    
        See Also
        --------
        setCISSExtraction, slepc.EPSCISSGetExtraction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3957 <slepc4py/SLEPc/EPS.pyx#L3957>`
    
        """
        ...
    def setCISSQuadRule(self, quad: CISSQuadRule) -> None:
        """Set the quadrature rule used in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        quad
            The quadrature rule.
    
        See Also
        --------
        getCISSQuadRule, slepc.EPSCISSSetQuadRule
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3976 <slepc4py/SLEPc/EPS.pyx#L3976>`
    
        """
        ...
    def getCISSQuadRule(self) -> CISSQuadRule:
        """Get the quadrature rule used in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        CISSQuadRule
            The quadrature rule.
    
        See Also
        --------
        setCISSQuadRule, slepc.EPSCISSGetQuadRule
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:3994 <slepc4py/SLEPc/EPS.pyx#L3994>`
    
        """
        ...
    def setCISSSizes(self, ip: int | None = None, bs: int | None = None, ms: int | None = None, npart: int | None = None, bsmax: int | None = None, realmats: bool = False) -> None:
        """Set the values of various size parameters in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        ip
            Number of integration points.
        bs
            Block size.
        ms
            Moment size.
        npart
            Number of partitions when splitting the communicator.
        bsmax
            Maximum block size.
        realmats
            ``True`` if A and B are real.
    
        Notes
        -----
        The default number of partitions is 1. This means the internal
        `petsc4py.PETSc.KSP` object is shared among all processes of the
        `EPS` communicator. Otherwise, the communicator is split into ``npart``
        communicators, so that ``npart`` `petsc4py.PETSc.KSP` solves proceed
        simultaneously.
    
        See Also
        --------
        getCISSSizes, setCISSThreshold, setCISSRefinement, slepc.EPSCISSSetSizes
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4013 <slepc4py/SLEPc/EPS.pyx#L4013>`
    
        """
        ...
    def getCISSSizes(self) -> tuple[int, int, int, int, int, bool]:
        """Get the values of various size parameters in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        ip: int
            Number of integration points.
        bs: int
            Block size.
        ms: int
            Moment size.
        npart: int
            Number of partitions when splitting the communicator.
        bsmax: int
            Maximum block size.
        realmats: bool
            ``True`` if A and B are real.
    
        See Also
        --------
        setCISSSizes, slepc.EPSCISSGetSizes
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4067 <slepc4py/SLEPc/EPS.pyx#L4067>`
    
        """
        ...
    def setCISSThreshold(self, delta: float | None = None, spur: float | None = None) -> None:
        """Set the values of various threshold parameters in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        delta
            Threshold for numerical rank.
        spur
            Spurious threshold (to discard spurious eigenpairs).
    
        See Also
        --------
        getCISSThreshold, slepc.EPSCISSSetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4101 <slepc4py/SLEPc/EPS.pyx#L4101>`
    
        """
        ...
    def getCISSThreshold(self) -> tuple[float, float]:
        """Get the values of various threshold parameters in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        delta: float
            Threshold for numerical rank.
        spur: float
            Spurious threshold (to discard spurious eigenpairs.
    
        See Also
        --------
        setCISSThreshold, slepc.EPSCISSGetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4124 <slepc4py/SLEPc/EPS.pyx#L4124>`
    
        """
        ...
    def setCISSRefinement(self, inner: int | None = None, blsize: int | None = None) -> None:
        """Set the values of various refinement parameters in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        inner
            Number of iterative refinement iterations (inner loop).
        blsize
            Number of iterative refinement iterations (blocksize loop).
    
        See Also
        --------
        getCISSRefinement, slepc.EPSCISSSetRefinement
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4146 <slepc4py/SLEPc/EPS.pyx#L4146>`
    
        """
        ...
    def getCISSRefinement(self) -> tuple[int, int]:
        """Get the values of various refinement parameters in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        inner: int
            Number of iterative refinement iterations (inner loop).
        blsize: int
            Number of iterative refinement iterations (blocksize loop).
    
        See Also
        --------
        setCISSRefinement, slepc.EPSCISSGetRefinement
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4169 <slepc4py/SLEPc/EPS.pyx#L4169>`
    
        """
        ...
    def setCISSUseST(self, usest: bool) -> None:
        """Set a flag indicating that the CISS solver will use the `ST` object.
    
        Logically collective.
    
        Parameters
        ----------
        usest
            Whether to use the `ST` object or not.
    
        Notes
        -----
        When this option is set, the linear solves can be configured by
        setting options for the `petsc4py.PETSc.KSP` object obtained with
        `ST.getKSP()`. Otherwise, several `petsc4py.PETSc.KSP` objects are
        created, which can be accessed with `getCISSKSPs()`.
    
        The default is to use the `ST`, unless several partitions have been
        specified, see `setCISSSizes()`.
    
        See Also
        --------
        getCISSUseST, getCISSKSPs, setCISSSizes, slepc.EPSCISSSetUseST
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4191 <slepc4py/SLEPc/EPS.pyx#L4191>`
    
        """
        ...
    def getCISSUseST(self) -> bool:
        """Get the flag indicating the use of the `ST` object in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether to use the `ST` object or not.
    
        See Also
        --------
        setCISSUseST, slepc.EPSCISSGetUseST
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4219 <slepc4py/SLEPc/EPS.pyx#L4219>`
    
        """
        ...
    def getCISSKSPs(self) -> list[KSP]:
        """Get the array of linear solver objects associated with the CISS solver.
    
        Not collective.
    
        Returns
        -------
        list of `petsc4py.PETSc.KSP`
            The linear solver objects.
    
        Notes
        -----
        The number of `petsc4py.PETSc.KSP` solvers is equal to the number of
        integration points divided by the number of partitions. This value is
        halved in the case of real matrices with a region centered at the real
        axis.
    
        See Also
        --------
        setCISSSizes, slepc.EPSCISSGetKSPs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4238 <slepc4py/SLEPc/EPS.pyx#L4238>`
    
        """
        ...
    @property
    def problem_type(self) -> EPSProblemType:
        """The type of the eigenvalue problem.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4266 <slepc4py/SLEPc/EPS.pyx#L4266>`
    
        """
        ...
    @property
    def extraction(self) -> EPSExtraction:
        """The type of extraction technique to be employed.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4273 <slepc4py/SLEPc/EPS.pyx#L4273>`
    
        """
        ...
    @property
    def which(self) -> EPSWhich:
        """The portion of the spectrum to be sought.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4280 <slepc4py/SLEPc/EPS.pyx#L4280>`
    
        """
        ...
    @property
    def target(self) -> float:
        """The value of the target.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4287 <slepc4py/SLEPc/EPS.pyx#L4287>`
    
        """
        ...
    @property
    def tol(self) -> float:
        """The tolerance.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4294 <slepc4py/SLEPc/EPS.pyx#L4294>`
    
        """
        ...
    @property
    def max_it(self) -> int:
        """The maximum iteration count.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4301 <slepc4py/SLEPc/EPS.pyx#L4301>`
    
        """
        ...
    @property
    def two_sided(self) -> bool:
        """Two-sided that also computes left eigenvectors.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4308 <slepc4py/SLEPc/EPS.pyx#L4308>`
    
        """
        ...
    @property
    def true_residual(self) -> bool:
        """Compute the true residual explicitly.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4315 <slepc4py/SLEPc/EPS.pyx#L4315>`
    
        """
        ...
    @property
    def purify(self) -> bool:
        """Eigenvector purification.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4322 <slepc4py/SLEPc/EPS.pyx#L4322>`
    
        """
        ...
    @property
    def track_all(self) -> bool:
        """Compute the residual norm of all approximate eigenpairs.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4329 <slepc4py/SLEPc/EPS.pyx#L4329>`
    
        """
        ...
    @property
    def st(self) -> ST:
        """The spectral transformation (`ST`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4336 <slepc4py/SLEPc/EPS.pyx#L4336>`
    
        """
        ...
    @property
    def bv(self) -> BV:
        """The basis vectors (`BV`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4343 <slepc4py/SLEPc/EPS.pyx#L4343>`
    
        """
        ...
    @property
    def rg(self) -> RG:
        """The region (`RG`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4350 <slepc4py/SLEPc/EPS.pyx#L4350>`
    
        """
        ...
    @property
    def ds(self) -> DS:
        """The direct solver (`DS`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/EPS.pyx:4357 <slepc4py/SLEPc/EPS.pyx#L4357>`
    
        """
        ...

class SVD(Object):
    """Singular Value Decomposition Solver.
    
    The Singular Value Decomposition Solver (`SVD`) is very similar to the
    `EPS` object, but intended for the computation of the partial SVD of a
    rectangular matrix. With this type of object, the user can specify an
    SVD problem and solve it with any of the different solvers encapsulated
    by the package. Some of these solvers are actually implemented through
    calls to `EPS` eigensolvers.
    
    """
    class Type:
        """SVD type.
        
        Native singular value solvers.
        
        - `CROSS`:      Eigenproblem with the cross-product matrix.
        - `CYCLIC`:     Eigenproblem with the cyclic matrix.
        - `LANCZOS`:    Explicitly restarted Lanczos.
        - `TRLANCZOS`:  Thick-restart Lanczos.
        - `RANDOMIZED`: Iterative RSVD for low-rank matrices.
        
        Wrappers to external SVD solvers
        (should be enabled during installation of SLEPc).
        
        - `LAPACK`:     Sequential dense SVD solver.
        - `SCALAPACK`:  Parallel dense SVD solver.
        - `KSVD`:       Parallel dense SVD solver.
        - `ELEMENTAL`:  Parallel dense SVD solver.
        - `PRIMME`:     Iterative SVD solvers of Davidson type.
        
        See Also
        --------
        slepc.SVDType
        
        """
        CROSS: str = _def(str, 'CROSS')  #: Object ``CROSS`` of type :class:`str`
        CYCLIC: str = _def(str, 'CYCLIC')  #: Object ``CYCLIC`` of type :class:`str`
        LAPACK: str = _def(str, 'LAPACK')  #: Object ``LAPACK`` of type :class:`str`
        LANCZOS: str = _def(str, 'LANCZOS')  #: Object ``LANCZOS`` of type :class:`str`
        TRLANCZOS: str = _def(str, 'TRLANCZOS')  #: Object ``TRLANCZOS`` of type :class:`str`
        RANDOMIZED: str = _def(str, 'RANDOMIZED')  #: Object ``RANDOMIZED`` of type :class:`str`
        SCALAPACK: str = _def(str, 'SCALAPACK')  #: Object ``SCALAPACK`` of type :class:`str`
        KSVD: str = _def(str, 'KSVD')  #: Object ``KSVD`` of type :class:`str`
        ELEMENTAL: str = _def(str, 'ELEMENTAL')  #: Object ``ELEMENTAL`` of type :class:`str`
        PRIMME: str = _def(str, 'PRIMME')  #: Object ``PRIMME`` of type :class:`str`
    class ProblemType:
        """SVD problem type.
        
        - `STANDARD`:    Standard SVD.
        - `GENERALIZED`: Generalized singular value decomposition (GSVD).
        - `HYPERBOLIC` : Hyperbolic singular value decomposition (HSVD).
        
        See Also
        --------
        slepc.SVDProblemType
        
        """
        STANDARD: int = _def(int, 'STANDARD')  #: Constant ``STANDARD`` of type :class:`int`
        GENERALIZED: int = _def(int, 'GENERALIZED')  #: Constant ``GENERALIZED`` of type :class:`int`
        HYPERBOLIC: int = _def(int, 'HYPERBOLIC')  #: Constant ``HYPERBOLIC`` of type :class:`int`
    class ErrorType:
        """SVD error type to assess accuracy of computed solutions.
        
        - `ABSOLUTE`: Absolute error.
        - `RELATIVE`: Relative error.
        - `NORM`:     Error relative to the matrix norm.
        
        See Also
        --------
        slepc.SVDErrorType
        
        """
        ABSOLUTE: int = _def(int, 'ABSOLUTE')  #: Constant ``ABSOLUTE`` of type :class:`int`
        RELATIVE: int = _def(int, 'RELATIVE')  #: Constant ``RELATIVE`` of type :class:`int`
        NORM: int = _def(int, 'NORM')  #: Constant ``NORM`` of type :class:`int`
    class Which:
        """SVD desired part of spectrum.
        
        - `LARGEST`:  Largest singular values.
        - `SMALLEST`: Smallest singular values.
        
        See Also
        --------
        slepc.SVDWhich
        
        """
        LARGEST: int = _def(int, 'LARGEST')  #: Constant ``LARGEST`` of type :class:`int`
        SMALLEST: int = _def(int, 'SMALLEST')  #: Constant ``SMALLEST`` of type :class:`int`
    class Conv:
        """SVD convergence test.
        
        - `ABS`:   Absolute convergence test.
        - `REL`:   Convergence test relative to the singular value.
        - `NORM`:  Convergence test relative to the matrix norms.
        - `MAXIT`: No convergence until maximum number of iterations has been reached.
        - `USER`:  User-defined convergence test.
        
        See Also
        --------
        slepc.SVDConv
        
        """
        ABS: int = _def(int, 'ABS')  #: Constant ``ABS`` of type :class:`int`
        REL: int = _def(int, 'REL')  #: Constant ``REL`` of type :class:`int`
        NORM: int = _def(int, 'NORM')  #: Constant ``NORM`` of type :class:`int`
        MAXIT: int = _def(int, 'MAXIT')  #: Constant ``MAXIT`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class Stop:
        """SVD stopping test.
        
        - `BASIC`:     Default stopping test.
        - `USER`:      User-defined stopping test.
        - `THRESHOLD`: Threshold stopping test.
        
        See Also
        --------
        slepc.SVDStop
        
        """
        BASIC: int = _def(int, 'BASIC')  #: Constant ``BASIC`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
        THRESHOLD: int = _def(int, 'THRESHOLD')  #: Constant ``THRESHOLD`` of type :class:`int`
    class ConvergedReason:
        """SVD convergence reasons.
        
        - `CONVERGED_TOL`: All eigenpairs converged to requested tolerance.
        - `CONVERGED_USER`: User-defined convergence criterion satisfied.
        - `CONVERGED_MAXIT`: Maximum iterations completed in case MAXIT
          convergence criterion.
        - `DIVERGED_ITS`: Maximum number of iterations exceeded.
        - `DIVERGED_BREAKDOWN`: Solver failed due to breakdown.
        - `DIVERGED_SYMMETRY_LOST`: Underlying indefinite eigensolver was not able
          to keep symmetry.
        - `CONVERGED_ITERATING`: Iteration not finished yet.
        
        See Also
        --------
        slepc.SVDConvergedReason
        
        """
        CONVERGED_TOL: int = _def(int, 'CONVERGED_TOL')  #: Constant ``CONVERGED_TOL`` of type :class:`int`
        CONVERGED_USER: int = _def(int, 'CONVERGED_USER')  #: Constant ``CONVERGED_USER`` of type :class:`int`
        CONVERGED_MAXIT: int = _def(int, 'CONVERGED_MAXIT')  #: Constant ``CONVERGED_MAXIT`` of type :class:`int`
        DIVERGED_ITS: int = _def(int, 'DIVERGED_ITS')  #: Constant ``DIVERGED_ITS`` of type :class:`int`
        DIVERGED_BREAKDOWN: int = _def(int, 'DIVERGED_BREAKDOWN')  #: Constant ``DIVERGED_BREAKDOWN`` of type :class:`int`
        DIVERGED_SYMMETRY_LOST: int = _def(int, 'DIVERGED_SYMMETRY_LOST')  #: Constant ``DIVERGED_SYMMETRY_LOST`` of type :class:`int`
        CONVERGED_ITERATING: int = _def(int, 'CONVERGED_ITERATING')  #: Constant ``CONVERGED_ITERATING`` of type :class:`int`
        ITERATING: int = _def(int, 'ITERATING')  #: Constant ``ITERATING`` of type :class:`int`
    class TRLanczosGBidiag:
        """SVD TRLanczos bidiagonalization choices for the GSVD case.
        
        - `SINGLE`: Single bidiagonalization (:math:`Q_A`).
        - `UPPER`: Joint bidiagonalization, both :math:`Q_A` and :math:`Q_B`
          in upper bidiagonal form.
        - `LOWER`: Joint bidiagonalization, :math:`Q_A` lower bidiagonal,
          :math:`Q_B` upper bidiagonal.
        
        See Also
        --------
        slepc.SVDTRLanczosGBidiag
        
        """
        SINGLE: int = _def(int, 'SINGLE')  #: Constant ``SINGLE`` of type :class:`int`
        UPPER: int = _def(int, 'UPPER')  #: Constant ``UPPER`` of type :class:`int`
        LOWER: int = _def(int, 'LOWER')  #: Constant ``LOWER`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the SVD data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.SVDView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:195 <slepc4py/SLEPc/SVD.pyx#L195>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the SVD object.
    
        Collective.
    
        See Also
        --------
        slepc.SVDDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:214 <slepc4py/SLEPc/SVD.pyx#L214>`
    
        """
        ...
    def reset(self) -> None:
        """Reset the SVD object.
    
        Collective.
    
        See Also
        --------
        slepc.SVDReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:228 <slepc4py/SLEPc/SVD.pyx#L228>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the SVD object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator; if not provided, it defaults to all processes.
    
        See Also
        --------
        slepc.SVDCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:240 <slepc4py/SLEPc/SVD.pyx#L240>`
    
        """
        ...
    def setType(self, svd_type: Type | str) -> None:
        """Set the particular solver to be used in the SVD object.
    
        Logically collective.
    
        Parameters
        ----------
        svd_type
            The solver to be used.
    
        Notes
        -----
        The default is `CROSS`. Normally, it is best to use
        `setFromOptions()` and then set the SVD type from the options
        database rather than by using this routine. Using the options
        database provides the user with maximum flexibility in
        evaluating the different available methods.
    
        See Also
        --------
        getType, slepc.SVDSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:261 <slepc4py/SLEPc/SVD.pyx#L261>`
    
        """
        ...
    def getType(self) -> str:
        """Get the SVD type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The solver currently being used.
    
        See Also
        --------
        setType, slepc.SVDGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:288 <slepc4py/SLEPc/SVD.pyx#L288>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all SVD options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this SVD object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.SVDGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:307 <slepc4py/SLEPc/SVD.pyx#L307>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all SVD options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all SVD option requests.
    
        Notes
        -----
        A hyphen (-) must NOT be given at the beginning of the prefix
        name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        For example, to distinguish between the runtime options for
        two different SVD contexts, one could call::
    
            S1.setOptionsPrefix("svd1_")
            S2.setOptionsPrefix("svd2_")
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.SVDGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:326 <slepc4py/SLEPc/SVD.pyx#L326>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all SVD options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all SVD option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.SVDAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:357 <slepc4py/SLEPc/SVD.pyx#L357>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set SVD options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help`` option.
    
        This routine must be called before `setUp()` if the user is to be
        allowed to set the solver type.
    
        See Also
        --------
        setOptionsPrefix, slepc.SVDSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:376 <slepc4py/SLEPc/SVD.pyx#L376>`
    
        """
        ...
    def getProblemType(self) -> ProblemType:
        """Get the problem type from the SVD object.
    
        Not collective.
    
        Returns
        -------
        ProblemType
            The problem type that was previously set.
    
        See Also
        --------
        setProblemType, slepc.SVDGetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:395 <slepc4py/SLEPc/SVD.pyx#L395>`
    
        """
        ...
    def setProblemType(self, problem_type: ProblemType) -> None:
        """Set the type of the singular value problem.
    
        Logically collective.
    
        Parameters
        ----------
        problem_type
            The problem type to be set.
    
        Notes
        -----
        The GSVD requires that two matrices have been passed via
        `setOperators()`. The HSVD requires that a signature matrix
        has been passed via `setSignature()`.
    
        See Also
        --------
        setOperators, setSignature, getProblemType, slepc.SVDSetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:414 <slepc4py/SLEPc/SVD.pyx#L414>`
    
        """
        ...
    def isGeneralized(self) -> bool:
        """Tell if the SVD corresponds to a generalized singular value problem.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if two matrices were set with `setOperators()`.
    
        See Also
        --------
        setProblemType, isHyperbolic, slepc.SVDIsGeneralized
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:438 <slepc4py/SLEPc/SVD.pyx#L438>`
    
        """
        ...
    def isHyperbolic(self) -> bool:
        """Tell whether the SVD object corresponds to a hyperbolic singular value problem.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if the problem was specified as hyperbolic.
    
        See Also
        --------
        setProblemType, isGeneralized, slepc.SVDIsHyperbolic
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:457 <slepc4py/SLEPc/SVD.pyx#L457>`
    
        """
        ...
    def getImplicitTranspose(self) -> bool:
        """Get the mode used to handle the transpose of the associated matrix.
    
        Not collective.
    
        Returns
        -------
        bool
            How to handle the transpose (implicitly or not).
    
        See Also
        --------
        setImplicitTranspose, slepc.SVDGetImplicitTranspose
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:478 <slepc4py/SLEPc/SVD.pyx#L478>`
    
        """
        ...
    def setImplicitTranspose(self, mode: bool) -> None:
        """Set how to handle the transpose of the associated matrix.
    
        Logically collective.
    
        Parameters
        ----------
        impl
            How to handle the transpose (implicitly or not).
    
        Notes
        -----
        By default, the transpose of the matrix is explicitly built
        (if the matrix has defined the ``Mat.transpose()`` operation).
    
        If this flag is set to ``True``, the solver does not build the
        transpose, but handles it implicitly via ``Mat.multTranspose()``
        (or ``Mat.multHermitianTranspose()`` in the complex case).
    
        See Also
        --------
        getImplicitTranspose, slepc.SVDSetImplicitTranspose
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:497 <slepc4py/SLEPc/SVD.pyx#L497>`
    
        """
        ...
    def getWhichSingularTriplets(self) -> Which:
        """Get which singular triplets are to be sought.
    
        Not collective.
    
        Returns
        -------
        Which
            The singular values to be sought (either largest or smallest).
    
        See Also
        --------
        setWhichSingularTriplets, slepc.SVDGetWhichSingularTriplets
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:524 <slepc4py/SLEPc/SVD.pyx#L524>`
    
        """
        ...
    def setWhichSingularTriplets(self, which: Which) -> None:
        """Set which singular triplets are to be sought.
    
        Logically collective.
    
        Parameters
        ----------
        which
            The singular values to be sought (either largest or smallest).
    
        See Also
        --------
        getWhichSingularTriplets, slepc.SVDSetWhichSingularTriplets
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:543 <slepc4py/SLEPc/SVD.pyx#L543>`
    
        """
        ...
    def getThreshold(self) -> tuple[float, bool]:
        """Get the threshold used in the threshold stopping test.
    
        Not collective.
    
        Returns
        -------
        thres: float
            The threshold.
        rel: bool
            Whether the threshold is relative or not.
    
        See Also
        --------
        setThreshold, slepc.SVDGetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:561 <slepc4py/SLEPc/SVD.pyx#L561>`
    
        """
        ...
    def setThreshold(self, thres: float, rel: bool = False) -> None:
        """Set the threshold used in the threshold stopping test.
    
        Logically collective.
    
        Parameters
        ----------
        thres
            The threshold.
        rel
            Whether the threshold is relative or not.
    
        Notes
        -----
        This function internally sets a special stopping test based on
        the threshold, where singular values are computed in sequence
        until one of the computed singular values is below/above the
        threshold (depending on whether largest or smallest singular
        values are computed).
    
        In the case of largest singular values, the threshold can be
        made relative with respect to the largest singular value
        (i.e., the matrix norm).
    
        The details are given in `slepc.SVDSetThreshold`.
    
        See Also
        --------
        setStoppingTest, getThreshold, slepc.SVDSetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:583 <slepc4py/SLEPc/SVD.pyx#L583>`
    
        """
        ...
    def getTolerances(self) -> tuple[float, int]:
        """Get the tolerance and maximum iteration count.
    
        Not collective.
    
        Get the tolerance and maximum iteration count used by the default SVD
        convergence tests.
    
        Returns
        -------
        tol: float
            The convergence tolerance.
        max_it: int
            The maximum number of iterations.
    
        See Also
        --------
        setTolerances, slepc.SVDGetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:618 <slepc4py/SLEPc/SVD.pyx#L618>`
    
        """
        ...
    def setTolerances(self, tol: float | None = None, max_it: int | None = None) -> None:
        """Set the tolerance and maximum iteration count used.
    
        Logically collective.
    
        Set the tolerance and maximum iteration count used by the default SVD
        convergence tests.
    
        Parameters
        ----------
        tol
            The convergence tolerance.
        max_it
            The maximum number of iterations
    
        Notes
        -----
        Use `DETERMINE` for ``max_it`` to assign a reasonably good value,
        which is dependent on the solution method.
    
        See Also
        --------
        getTolerances, slepc.SVDSetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:643 <slepc4py/SLEPc/SVD.pyx#L643>`
    
        """
        ...
    def getConvergenceTest(self) -> Conv:
        """Get the method used to compute the error estimate used in the convergence test.
    
        Not collective.
    
        Returns
        -------
        Conv
            The method used to compute the error estimate
            used in the convergence test.
    
        See Also
        --------
        setConvergenceTest, slepc.SVDGetConvergenceTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:674 <slepc4py/SLEPc/SVD.pyx#L674>`
    
        """
        ...
    def setConvergenceTest(self, conv: Conv) -> None:
        """Set how to compute the error estimate used in the convergence test.
    
        Logically collective.
    
        Parameters
        ----------
        conv
            The method used to compute the error estimate
            used in the convergence test.
    
        See Also
        --------
        getConvergenceTest, slepc.SVDSetConvergenceTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:694 <slepc4py/SLEPc/SVD.pyx#L694>`
    
        """
        ...
    def getTrackAll(self) -> bool:
        """Get the flag indicating if all residual norms must be computed or not.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether the solver computes all residuals or not.
    
        See Also
        --------
        setTrackAll, slepc.SVDGetTrackAll
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:713 <slepc4py/SLEPc/SVD.pyx#L713>`
    
        """
        ...
    def setTrackAll(self, trackall: bool) -> None:
        """Set flag to compute the residual of all singular triplets.
    
        Logically collective.
    
        Set if the solver must compute the residual of all approximate
        singular triplets or not.
    
        Parameters
        ----------
        trackall
            Whether to compute all residuals or not.
    
        See Also
        --------
        getTrackAll, slepc.SVDSetTrackAll
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:732 <slepc4py/SLEPc/SVD.pyx#L732>`
    
        """
        ...
    def getDimensions(self) -> tuple[int, int, int]:
        """Get the number of singular values to compute and the dimension of the subspace.
    
        Not collective.
    
        Returns
        -------
        nsv: int
            Number of singular values to compute.
        ncv: int
            Maximum dimension of the subspace to be used by the solver.
        mpd: int
            Maximum dimension allowed for the projected problem.
    
        See Also
        --------
        setDimensions, slepc.SVDGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:753 <slepc4py/SLEPc/SVD.pyx#L753>`
    
        """
        ...
    def setDimensions(self, nsv: int | None = None, ncv: int | None = None, mpd: int | None = None) -> None:
        """Set the number of singular values to compute and the dimension of the subspace.
    
        Logically collective.
    
        Parameters
        ----------
        nsv
            Number of singular values to compute.
        ncv
            Maximum dimension of the subspace to be used by the solver.
        mpd
            Maximum dimension allowed for the projected problem.
    
        Notes
        -----
        Use `DETERMINE` for ``ncv`` and ``mpd`` to assign a reasonably good
        value, which is dependent on the solution method.
    
        The parameters ``ncv`` and ``mpd`` are intimately related, so that
        the user is advised to set one of them at most. Normal usage
        is the following:
    
        + In cases where ``nsv`` is small, the user sets ``ncv``
          (a reasonable default is 2 * ``nsv``).
    
        + In cases where ``nsv`` is large, the user sets ``mpd``.
    
        The value of ``ncv`` should always be between ``nsv`` and (``nsv`` +
        ``mpd``), typically ``ncv`` = ``nsv`` + ``mpd``. If ``nsv`` is not too
        large, ``mpd`` = ``nsv`` is a reasonable choice, otherwise a
        smaller value should be used.
    
        See Also
        --------
        getDimensions, slepc.SVDSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:778 <slepc4py/SLEPc/SVD.pyx#L778>`
    
        """
        ...
    def getBV(self) -> tuple[BV, BV]:
        """Get the basis vectors objects associated to the SVD object.
    
        Not collective.
    
        Returns
        -------
        V: BV
            The basis vectors context for right singular vectors.
        U: BV
            The basis vectors context for left singular vectors.
    
        See Also
        --------
        setBV, slepc.SVDGetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:829 <slepc4py/SLEPc/SVD.pyx#L829>`
    
        """
        ...
    def setBV(self, V: BV, U: BV | None = None) -> None:
        """Set basis vectors objects associated to the SVD solver.
    
        Collective.
    
        Parameters
        ----------
        V
            The basis vectors context for right singular vectors.
        U
            The basis vectors context for left singular vectors.
    
        See Also
        --------
        getBV, slepc.SVDSetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:853 <slepc4py/SLEPc/SVD.pyx#L853>`
    
        """
        ...
    def getDS(self) -> DS:
        """Get the direct solver associated to the singular value solver.
    
        Not collective.
    
        Returns
        -------
        DS
            The direct solver context.
    
        See Also
        --------
        setDS, slepc.SVDGetDS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:874 <slepc4py/SLEPc/SVD.pyx#L874>`
    
        """
        ...
    def setDS(self, ds: DS) -> None:
        """Set a direct solver object associated to the singular value solver.
    
        Collective.
    
        Parameters
        ----------
        ds
            The direct solver context.
    
        See Also
        --------
        getDS, slepc.SVDSetDS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:894 <slepc4py/SLEPc/SVD.pyx#L894>`
    
        """
        ...
    def getOperators(self) -> tuple[Mat, Mat] | tuple[Mat, None]:
        """Get the matrices associated with the singular value problem.
    
        Collective.
    
        Returns
        -------
        A: petsc4py.PETSc.Mat
            The matrix associated with the singular value problem.
        B: petsc4py.PETSc.Mat
            The second matrix in the case of GSVD.
    
        See Also
        --------
        setOperators, slepc.SVDGetOperators
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:911 <slepc4py/SLEPc/SVD.pyx#L911>`
    
        """
        ...
    def setOperators(self, A: Mat, B: Mat | None = None) -> None:
        """Set the matrices associated with the singular value problem.
    
        Collective.
    
        Parameters
        ----------
        A
            The matrix associated with the singular value problem.
        B
            The second matrix in the case of GSVD.
    
        See Also
        --------
        getOperators, slepc.SVDSetOperators
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:938 <slepc4py/SLEPc/SVD.pyx#L938>`
    
        """
        ...
    def getSignature(self, omega: Vec | None = None) -> Vec:
        """Get the signature matrix defining a hyperbolic singular value problem.
    
        Collective.
    
        Parameters
        ----------
        omega
            Optional vector to store the diagonal elements of the signature matrix.
    
        Returns
        -------
        petsc4py.PETSc.Vec
            A vector containing the diagonal elements of the signature matrix.
    
        See Also
        --------
        setSignature, slepc.SVDGetSignature
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:958 <slepc4py/SLEPc/SVD.pyx#L958>`
    
        """
        ...
    def setSignature(self, omega: Vec | None = None) -> None:
        """Set the signature matrix defining a hyperbolic singular value problem.
    
        Collective.
    
        Parameters
        ----------
        omega
            A vector containing the diagonal elements of the signature matrix.
    
        See Also
        --------
        getSignature, slepc.SVDSetSignature
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:987 <slepc4py/SLEPc/SVD.pyx#L987>`
    
        """
        ...
    def setInitialSpace(self, spaceright: list[Vec] | None = None, spaceleft: list[Vec] | None = None) -> None:
        """Set the initial spaces from which the SVD solver starts to iterate.
    
        Collective.
    
        Parameters
        ----------
        spaceright
            The right initial space.
        spaceleft
            The left initial space.
    
        Notes
        -----
        The initial right and left spaces are rough approximations to the
        right and/or left singular subspaces from which the solver starts
        to iterate. It is not necessary to provide both sets of vectors.
    
        Some solvers start to iterate on a single vector (initial vector).
        In that case, the other vectors are ignored.
    
        These vectors do not persist from one `solve()` call to the other,
        so the initial spaces should be set every time.
    
        The vectors do not need to be mutually orthonormal, since they are
        explicitly orthonormalized internally.
    
        Common usage of this function is when the user can provide a rough
        approximation of the wanted singular spaces. Then, convergence may
        be faster.
    
        See Also
        --------
        slepc.SVDSetInitialSpaces
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1007 <slepc4py/SLEPc/SVD.pyx#L1007>`
    
        """
        ...
    def setStoppingTest(self, stopping: SVDStoppingFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set a function to decide when to stop the outer iteration of the eigensolver.
    
        Logically collective.
    
        See Also
        --------
        getStoppingTest, slepc.SVDSetStoppingTestFunction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1064 <slepc4py/SLEPc/SVD.pyx#L1064>`
    
        """
        ...
    def getStoppingTest(self) -> SVDStoppingFunction:
        """Get the stopping test function.
    
        Not collective.
    
        Returns
        -------
        SVDStoppingFunction
            The stopping test function.
    
        See Also
        --------
        setStoppingTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1088 <slepc4py/SLEPc/SVD.pyx#L1088>`
    
        """
        ...
    def setMonitor(self, monitor: SVDMonitorFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Append a monitor function to the list of monitors.
    
        Logically collective.
    
        See Also
        --------
        getMonitor, cancelMonitor, slepc.SVDMonitorSet
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1107 <slepc4py/SLEPc/SVD.pyx#L1107>`
    
        """
        ...
    def getMonitor(self) -> SVDMonitorFunction:
        """Get the list of monitor functions.
    
        Not collective.
    
        Returns
        -------
        SVDMonitorFunction
            The list of monitor functions.
    
        See Also
        --------
        setMonitor
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1132 <slepc4py/SLEPc/SVD.pyx#L1132>`
    
        """
        ...
    def cancelMonitor(self) -> None:
        """Clear all monitors for an `SVD` object.
    
        Logically collective.
    
        See Also
        --------
        slepc.SVDMonitorCancel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1149 <slepc4py/SLEPc/SVD.pyx#L1149>`
    
        """
        ...
    def setUp(self) -> None:
        """Set up all the internal data structures.
    
        Collective.
    
        Notes
        -----
        Sets up all the internal data structures necessary for the execution
        of the singular value solver.
    
        This function need not be called explicitly in most cases,
        since `solve()` calls it. It can be useful when one wants to
        measure the set-up time separately from the solve time.
    
        See Also
        --------
        solve, slepc.SVDSetUp
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1164 <slepc4py/SLEPc/SVD.pyx#L1164>`
    
        """
        ...
    def solve(self) -> None:
        """Solve the singular value problem.
    
        Collective.
    
        Notes
        -----
        The problem matrices are specified with `setOperators()`.
    
        `solve()` will return without generating an error regardless of
        whether all requested solutions were computed or not. Call
        `getConverged()` to get the actual number of computed solutions,
        and `getConvergedReason()` to determine if the solver converged
        or failed and why.
    
        See Also
        --------
        setUp, setOperators, getConverged, getConvergedReason, slepc.SVDSolve
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1185 <slepc4py/SLEPc/SVD.pyx#L1185>`
    
        """
        ...
    def getIterationNumber(self) -> int:
        """Get the current iteration number.
    
        Not collective.
    
        If the call to `solve()` is complete, then it returns the number of
        iterations carried out by the solution method.
    
        Returns
        -------
        int
            Iteration number.
    
        See Also
        --------
        getConvergedReason, setTolerances, slepc.SVDGetIterationNumber
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1207 <slepc4py/SLEPc/SVD.pyx#L1207>`
    
        """
        ...
    def getConvergedReason(self) -> ConvergedReason:
        """Get the reason why the `solve()` iteration was stopped.
    
        Not collective.
    
        Returns
        -------
        ConvergedReason
            Negative value indicates diverged, positive value converged.
    
        See Also
        --------
        setTolerances, solve, slepc.SVDGetConvergedReason
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1229 <slepc4py/SLEPc/SVD.pyx#L1229>`
    
        """
        ...
    def getConverged(self) -> int:
        """Get the number of converged singular triplets.
    
        Not collective.
    
        Returns
        -------
        nconv: int
            Number of converged singular triplets.
    
        Notes
        -----
        This function should be called after `solve()` has finished.
    
        The value ``nconv`` may be different from the number of requested
        solutions ``nsv``, but not larger than ``ncv``, see `setDimensions()`.
    
        See Also
        --------
        setDimensions, solve, getValue, slepc.SVDGetConverged
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1248 <slepc4py/SLEPc/SVD.pyx#L1248>`
    
        """
        ...
    def getValue(self, i: int) -> float:
        """Get the i-th singular value as computed by `solve()`.
    
        Collective.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
    
        Returns
        -------
        float
            The computed singular value.
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and
        ``nconv-1`` (see `getConverged()`. Singular triplets are
        indexed according to the ordering criterion established with
        `setWhichSingularTriplets()`.
    
        See Also
        --------
        getConverged, setWhichSingularTriplets, slepc.SVDGetSingularTriplet
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1274 <slepc4py/SLEPc/SVD.pyx#L1274>`
    
        """
        ...
    def getVectors(self, i: int, U: Vec, V: Vec) -> None:
        """Get the i-th left and right singular vectors as computed by `solve()`.
    
        Collective.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
        U
            Placeholder for the returned left singular vector.
        V
            Placeholder for the returned right singular vector.
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and
        ``nconv-1`` (see `getConverged()`. Singular triplets are
        indexed according to the ordering criterion established with
        `setWhichSingularTriplets()`.
    
        See Also
        --------
        getConverged, setWhichSingularTriplets, slepc.SVDGetSingularTriplet
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1305 <slepc4py/SLEPc/SVD.pyx#L1305>`
    
        """
        ...
    def getSingularTriplet(self, i: int, U: Vec | None = None, V: Vec | None = None) -> float:
        """Get the i-th triplet of the singular value decomposition.
    
        Collective.
    
        Get the i-th triplet of the singular value decomposition as computed
        by `solve()`. The solution consists of the singular value and its left
        and right singular vectors.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
        U
            Placeholder for the returned left singular vector.
        V
            Placeholder for the returned right singular vector.
    
        Returns
        -------
        float
            The computed singular value.
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and
        ``nconv-1`` (see `getConverged()`. Singular triplets are
        indexed according to the ordering criterion established with
        `setWhichSingularTriplets()`.
    
        See Also
        --------
        getConverged, setWhichSingularTriplets, slepc.SVDGetSingularTriplet
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1334 <slepc4py/SLEPc/SVD.pyx#L1334>`
    
        """
        ...
    def computeError(self, i: int, etype: ErrorType | None = None) -> float:
        """Compute the error associated with the i-th singular triplet.
    
        Collective.
    
        Compute the error (based on the residual norm) associated with the
        i-th singular triplet.
    
        Parameters
        ----------
        i
            Index of the solution to be considered.
        etype
            The error type to compute.
    
        Returns
        -------
        float
            The error bound, computed in various ways from the residual norm
            :math:`\sqrt{\eta_1^2+\eta_2^2}` where
            :math:`\eta_1 = \|A v - \sigma u\|_2`,
            :math:`\eta_2 = \|A^* u - \sigma v\|_2`, :math:`\sigma` is the
            approximate singular value, :math:`u` and :math:`v` are the left
            and right singular vectors.
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and ``nconv-1``
        (see `getConverged()`).
    
        In the case of the GSVD, the two components of the residual norm are
        :math:`\eta_1 = \|s^2 A^*u-cB^*Bx\|_2` and
        :math:`\eta_2 = ||c^2 B^*v-sA^*Ax||_2`, where :math:`(\sigma,u,v,x)`
        is the approximate generalized singular quadruple, with
        :math:`\sigma=c/s`.
    
        See Also
        --------
        solve, slepc.SVDComputeError
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1377 <slepc4py/SLEPc/SVD.pyx#L1377>`
    
        """
        ...
    def errorView(self, etype: ErrorType | None = None, viewer: petsc4py.PETSc.Viewer | None = None) -> None:
        """Display the errors associated with the computed solution.
    
        Collective.
    
        Display the errors and the singular values.
    
        Parameters
        ----------
        etype
            The error type to compute.
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        Notes
        -----
        By default, this function checks the error of all singular triplets and
        prints the singular values if all of them are below the requested
        tolerance. If the viewer has format ``ASCII_INFO_DETAIL`` then a table
        with singular values and corresponding errors is printed.
    
        See Also
        --------
        solve, valuesView, vectorsView, slepc.SVDErrorView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1424 <slepc4py/SLEPc/SVD.pyx#L1424>`
    
        """
        ...
    def valuesView(self, viewer: Viewer | None = None) -> None:
        """Display the computed singular values in a viewer.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        solve, vectorsView, errorView, slepc.SVDValuesView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1456 <slepc4py/SLEPc/SVD.pyx#L1456>`
    
        """
        ...
    def vectorsView(self, viewer: Viewer | None = None) -> None:
        """Output computed singular vectors to a viewer.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        solve, valuesView, errorView, slepc.SVDVectorsView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1475 <slepc4py/SLEPc/SVD.pyx#L1475>`
    
        """
        ...
    def setCrossEPS(self, eps: EPS) -> None:
        """Set an eigensolver object associated to the singular value solver.
    
        Collective.
    
        Parameters
        ----------
        eps
            The eigensolver object.
    
        See Also
        --------
        getCrossEPS, slepc.SVDCrossSetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1496 <slepc4py/SLEPc/SVD.pyx#L1496>`
    
        """
        ...
    def getCrossEPS(self) -> EPS:
        """Get the eigensolver object associated to the singular value solver.
    
        Collective.
    
        Returns
        -------
        EPS
            The eigensolver object.
    
        See Also
        --------
        setCrossEPS, slepc.SVDCrossGetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1513 <slepc4py/SLEPc/SVD.pyx#L1513>`
    
        """
        ...
    def setCrossExplicitMatrix(self, flag: bool = True) -> None:
        """Set if the eigensolver operator :math:`A^*A` must be computed.
    
        Logically collective.
    
        Parameters
        ----------
        flag
            ``True`` to build :math:`A^*A` explicitly.
    
        Notes
        -----
        In GSVD there are two cross product matrices, :math:`A^*A` and
        :math:`B^*B`. In HSVD the expression for the cross product matrix
        is different, :math:`A^*\Omega A`.
    
        By default the matrices are not built explicitly, but handled as
        shell matrices
    
        See Also
        --------
        getCrossExplicitMatrix, slepc.SVDCrossSetExplicitMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1533 <slepc4py/SLEPc/SVD.pyx#L1533>`
    
        """
        ...
    def getCrossExplicitMatrix(self) -> bool:
        """Get the flag indicating if :math:`A^*A` is built explicitly.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if :math:`A^*A` is built explicitly.
    
        See Also
        --------
        setCrossExplicitMatrix, slepc.SVDCrossGetExplicitMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1560 <slepc4py/SLEPc/SVD.pyx#L1560>`
    
        """
        ...
    def setCyclicEPS(self, eps: EPS) -> None:
        """Set an eigensolver object associated to the singular value solver.
    
        Collective.
    
        Parameters
        ----------
        eps
            The eigensolver object.
    
        See Also
        --------
        getCyclicEPS, slepc.SVDCyclicSetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1579 <slepc4py/SLEPc/SVD.pyx#L1579>`
    
        """
        ...
    def getCyclicEPS(self) -> EPS:
        """Get the eigensolver object associated to the singular value solver.
    
        Collective.
    
        Returns
        -------
        EPS
            The eigensolver object.
    
        See Also
        --------
        setCyclicEPS, slepc.SVDCyclicGetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1596 <slepc4py/SLEPc/SVD.pyx#L1596>`
    
        """
        ...
    def setCyclicExplicitMatrix(self, flag: bool = True) -> None:
        """Set if the eigensolver operator :math:`H(A)` must be computed explicitly.
    
        Logically collective.
    
        Set if the eigensolver operator :math:`H(A) = [ 0\; A ; A^T\; 0 ]`
        must be computed explicitly.
    
        Parameters
        ----------
        flag
            ``True`` if :math:`H(A)` must be built explicitly.
    
        Notes
        -----
        In GSVD and HSVD the equivalent eigenvalue problem has
        generalized form, and hence two matrices are built.
    
        By default the matrices are not built explicitly, but handled as
        shell matrices.
    
        See Also
        --------
        getCyclicExplicitMatrix, slepc.SVDCyclicSetExplicitMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1616 <slepc4py/SLEPc/SVD.pyx#L1616>`
    
        """
        ...
    def getCyclicExplicitMatrix(self) -> bool:
        """Get the flag indicating if :math:`H(A)` is built explicitly.
    
        Not collective.
    
        Get the flag indicating if :math:`H(A) = [ 0\; A ; A^T\; 0 ]`
        is built explicitly.
    
        Returns
        -------
        bool
            ``True`` if :math:`H(A)` is built explicitly.
    
        See Also
        --------
        setCyclicExplicitMatrix, slepc.SVDCyclicGetExplicitMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1645 <slepc4py/SLEPc/SVD.pyx#L1645>`
    
        """
        ...
    def setLanczosOneSide(self, flag: bool = True) -> None:
        """Set if the variant of the Lanczos method to be used is one-sided or two-sided.
    
        Logically collective.
    
        Parameters
        ----------
        flag
            ``True`` if the method is one-sided.
    
        Notes
        -----
        By default, a two-sided variant is selected, which is
        sometimes slightly more robust. However, the one-sided variant
        is faster because it avoids the orthogonalization associated
        to left singular vectors. It also saves the memory required
        for storing such vectors.
    
        See Also
        --------
        getLanczosOneSide, slepc.SVDLanczosSetOneSide
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1667 <slepc4py/SLEPc/SVD.pyx#L1667>`
    
        """
        ...
    def getLanczosOneSide(self) -> bool:
        """Get if the variant of the Lanczos method to be used is one-sided or two-sided.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if the method is one-sided.
    
        See Also
        --------
        setLanczosOneSide, slepc.SVDLanczosGetOneSide
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1693 <slepc4py/SLEPc/SVD.pyx#L1693>`
    
        """
        ...
    def setTRLanczosOneSide(self, flag: bool = True) -> None:
        """Set if the variant of the method to be used is one-sided or two-sided.
    
        Logically collective.
    
        Set if the variant of the thick-restart Lanczos method to be used is
        one-sided or two-sided.
    
        Parameters
        ----------
        flag
            ``True`` if the method is one-sided.
    
        Notes
        -----
        By default, a two-sided variant is selected, which is
        sometimes slightly more robust. However, the one-sided variant
        is faster because it avoids the orthogonalization associated
        to left singular vectors.
    
        See Also
        --------
        getTRLanczosOneSide, slepc.SVDLanczosSetOneSide
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1712 <slepc4py/SLEPc/SVD.pyx#L1712>`
    
        """
        ...
    def getTRLanczosOneSide(self) -> bool:
        """Get if the variant of the method to be used is one-sided or two-sided.
    
        Not collective.
    
        Get if the variant of the thick-restart Lanczos method to be used is
        one-sided or two-sided.
    
        Returns
        -------
        bool
            ``True`` if the method is one-sided.
    
        See Also
        --------
        setTRLanczosOneSide, slepc.SVDLanczosGetOneSide
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1740 <slepc4py/SLEPc/SVD.pyx#L1740>`
    
        """
        ...
    def setTRLanczosGBidiag(self, bidiag: TRLanczosGBidiag) -> None:
        """Set the bidiagonalization choice to use in the GSVD TRLanczos solver.
    
        Logically collective.
    
        Parameters
        ----------
        bidiag
            The bidiagonalization choice.
    
        See Also
        --------
        getTRLanczosGBidiag, slepc.SVDTRLanczosSetGBidiag
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1762 <slepc4py/SLEPc/SVD.pyx#L1762>`
    
        """
        ...
    def getTRLanczosGBidiag(self) -> TRLanczosGBidiag:
        """Get bidiagonalization choice used in the GSVD TRLanczos solver.
    
        Not collective.
    
        Returns
        -------
        TRLanczosGBidiag
            The bidiagonalization choice.
    
        See Also
        --------
        setTRLanczosGBidiag, slepc.SVDTRLanczosGetGBidiag
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1780 <slepc4py/SLEPc/SVD.pyx#L1780>`
    
        """
        ...
    def setTRLanczosRestart(self, keep: float) -> None:
        """Set the restart parameter for the thick-restart Lanczos method.
    
        Logically collective.
    
        Set the restart parameter for the thick-restart Lanczos method, in
        particular the proportion of basis vectors that must be kept
        after restart.
    
        Parameters
        ----------
        keep
            The number of vectors to be kept at restart.
    
        Notes
        -----
        Allowed values are in the range [0.1,0.9]. The default is 0.5.
    
        See Also
        --------
        getTRLanczosRestart, slepc.SVDTRLanczosSetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1799 <slepc4py/SLEPc/SVD.pyx#L1799>`
    
        """
        ...
    def getTRLanczosRestart(self) -> float:
        """Get the restart parameter used in the thick-restart Lanczos method.
    
        Not collective.
    
        Returns
        -------
        float
            The number of vectors to be kept at restart.
    
        See Also
        --------
        setTRLanczosRestart, slepc.SVDTRLanczosGetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1825 <slepc4py/SLEPc/SVD.pyx#L1825>`
    
        """
        ...
    def setTRLanczosLocking(self, lock: bool) -> None:
        """Toggle between locking and non-locking variants of TRLanczos.
    
        Logically collective.
    
        Parameters
        ----------
        lock
            ``True`` if the locking variant must be selected.
    
        Notes
        -----
        The default is to lock converged singular triplets when the method restarts.
        This behavior can be changed so that all directions are kept in the
        working subspace even if already converged to working accuracy (the
        non-locking variant).
    
        See Also
        --------
        getTRLanczosLocking, slepc.SVDTRLanczosSetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1844 <slepc4py/SLEPc/SVD.pyx#L1844>`
    
        """
        ...
    def getTRLanczosLocking(self) -> bool:
        """Get the locking flag used in the thick-restart Lanczos method.
    
        Not collective.
    
        Returns
        -------
        bool
            The locking flag.
    
        See Also
        --------
        setTRLanczosLocking, slepc.SVDTRLanczosGetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1869 <slepc4py/SLEPc/SVD.pyx#L1869>`
    
        """
        ...
    def setTRLanczosKSP(self, ksp: KSP) -> None:
        """Set a linear solver object associated to the SVD solver.
    
        Collective.
    
        Parameters
        ----------
        ``ksp``
            The linear solver object.
    
        See Also
        --------
        getTRLanczosKSP, slepc.SVDTRLanczosSetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1888 <slepc4py/SLEPc/SVD.pyx#L1888>`
    
        """
        ...
    def getTRLanczosKSP(self) -> KSP:
        """Get the linear solver object associated with the SVD solver.
    
        Collective.
    
        Returns
        -------
        `petsc4py.PETSc.KSP`
            The linear solver object.
    
        See Also
        --------
        setTRLanczosKSP, slepc.SVDTRLanczosGetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1905 <slepc4py/SLEPc/SVD.pyx#L1905>`
    
        """
        ...
    def setTRLanczosExplicitMatrix(self, flag: bool = True) -> None:
        """Set if the matrix :math:`Z=[A^*,B^*]^*` must be built explicitly.
    
        Logically collective.
    
        Parameters
        ----------
        flag
            ``True`` if :math:`Z=[A^*,B^*]^*` is built explicitly.
    
        Notes
        -----
        This option is relevant for the GSVD case only. :math:`Z` is the
        coefficient matrix of the least-squares solver used internally.
    
        See Also
        --------
        getTRLanczosExplicitMatrix, slepc.SVDTRLanczosSetExplicitMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1925 <slepc4py/SLEPc/SVD.pyx#L1925>`
    
        """
        ...
    def getTRLanczosExplicitMatrix(self) -> bool:
        """Get the flag indicating if :math:`Z=[A^*,B^*]^*` is built explicitly.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if :math:`Z=[A^*,B^*]^*` is built explicitly.
    
        See Also
        --------
        setTRLanczosExplicitMatrix, slepc.SVDTRLanczosGetExplicitMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1948 <slepc4py/SLEPc/SVD.pyx#L1948>`
    
        """
        ...
    @property
    def problem_type(self) -> SVDProblemType:
        """The type of the eigenvalue problem.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1971 <slepc4py/SLEPc/SVD.pyx#L1971>`
    
        """
        ...
    @property
    def transpose_mode(self) -> bool:
        """How to handle the transpose of the matrix.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1978 <slepc4py/SLEPc/SVD.pyx#L1978>`
    
        """
        ...
    @property
    def which(self) -> SVDWhich:
        """The portion of the spectrum to be sought.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1985 <slepc4py/SLEPc/SVD.pyx#L1985>`
    
        """
        ...
    @property
    def tol(self) -> float:
        """The tolerance.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1992 <slepc4py/SLEPc/SVD.pyx#L1992>`
    
        """
        ...
    @property
    def max_it(self) -> int:
        """The maximum iteration count.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:1999 <slepc4py/SLEPc/SVD.pyx#L1999>`
    
        """
        ...
    @property
    def track_all(self) -> bool:
        """Compute the residual norm of all approximate eigenpairs.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:2006 <slepc4py/SLEPc/SVD.pyx#L2006>`
    
        """
        ...
    @property
    def ds(self) -> DS:
        """The direct solver (`DS`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/SVD.pyx:2013 <slepc4py/SLEPc/SVD.pyx#L2013>`
    
        """
        ...

class PEP(Object):
    """Polynomial Eigenvalue Problem Solver.
    
    The Polynomial Eigenvalue Problem (`PEP`) solver is the object provided
    by slepc4py for specifying a polynomial eigenvalue problem. Apart from the
    specific solvers for this type of problems, there is an `EPS`-based solver,
    i.e., it uses a solver from `EPS` to solve a generalized eigenproblem
    obtained after linearization.
    
    """
    class Type:
        """PEP type.
        
        - `TOAR`:     Two-level orthogonal Arnoldi.
        - `STOAR`:    Symmetric TOAR.
        - `QARNOLDI`: Q-Arnoldi for quadratic problems.
        - `LINEAR`:   Linearization via EPS.
        - `JD`:       Polynomial Jacobi-Davidson.
        - `CISS`:     Contour integral spectrum slice.
        
        See Also
        --------
        slepc.PEPType
        
        """
        TOAR: str = _def(str, 'TOAR')  #: Object ``TOAR`` of type :class:`str`
        STOAR: str = _def(str, 'STOAR')  #: Object ``STOAR`` of type :class:`str`
        QARNOLDI: str = _def(str, 'QARNOLDI')  #: Object ``QARNOLDI`` of type :class:`str`
        LINEAR: str = _def(str, 'LINEAR')  #: Object ``LINEAR`` of type :class:`str`
        JD: str = _def(str, 'JD')  #: Object ``JD`` of type :class:`str`
        CISS: str = _def(str, 'CISS')  #: Object ``CISS`` of type :class:`str`
    class ProblemType:
        """PEP problem type.
        
        - `GENERAL`:    No structure.
        - `HERMITIAN`:  Hermitian structure.
        - `HYPERBOLIC`: QEP with Hermitian matrices, :math:`M>0`,
          :math:`(x^TCx)^2 > 4(x^TMx)(x^TKx)`.
        - `GYROSCOPIC`: QEP with :math:`M`, :math:`K`  Hermitian,
          :math:`M>0`, :math:`C` skew-Hermitian.
        
        See Also
        --------
        slepc.PEPProblemType
        
        """
        GENERAL: int = _def(int, 'GENERAL')  #: Constant ``GENERAL`` of type :class:`int`
        HERMITIAN: int = _def(int, 'HERMITIAN')  #: Constant ``HERMITIAN`` of type :class:`int`
        HYPERBOLIC: int = _def(int, 'HYPERBOLIC')  #: Constant ``HYPERBOLIC`` of type :class:`int`
        GYROSCOPIC: int = _def(int, 'GYROSCOPIC')  #: Constant ``GYROSCOPIC`` of type :class:`int`
    class Which:
        """PEP desired part of spectrum.
        
        - `LARGEST_MAGNITUDE`:  Largest magnitude (default).
        - `SMALLEST_MAGNITUDE`: Smallest magnitude.
        - `LARGEST_REAL`:       Largest real parts.
        - `SMALLEST_REAL`:      Smallest real parts.
        - `LARGEST_IMAGINARY`:  Largest imaginary parts in magnitude.
        - `SMALLEST_IMAGINARY`: Smallest imaginary parts in magnitude.
        - `TARGET_MAGNITUDE`:   Closest to target (in magnitude).
        - `TARGET_REAL`:        Real part closest to target.
        - `TARGET_IMAGINARY`:   Imaginary part closest to target.
        - `ALL`:                All eigenvalues in an interval.
        - `USER`:               User-defined criterion.
        
        See Also
        --------
        slepc.PEPWhich
        
        """
        LARGEST_MAGNITUDE: int = _def(int, 'LARGEST_MAGNITUDE')  #: Constant ``LARGEST_MAGNITUDE`` of type :class:`int`
        SMALLEST_MAGNITUDE: int = _def(int, 'SMALLEST_MAGNITUDE')  #: Constant ``SMALLEST_MAGNITUDE`` of type :class:`int`
        LARGEST_REAL: int = _def(int, 'LARGEST_REAL')  #: Constant ``LARGEST_REAL`` of type :class:`int`
        SMALLEST_REAL: int = _def(int, 'SMALLEST_REAL')  #: Constant ``SMALLEST_REAL`` of type :class:`int`
        LARGEST_IMAGINARY: int = _def(int, 'LARGEST_IMAGINARY')  #: Constant ``LARGEST_IMAGINARY`` of type :class:`int`
        SMALLEST_IMAGINARY: int = _def(int, 'SMALLEST_IMAGINARY')  #: Constant ``SMALLEST_IMAGINARY`` of type :class:`int`
        TARGET_MAGNITUDE: int = _def(int, 'TARGET_MAGNITUDE')  #: Constant ``TARGET_MAGNITUDE`` of type :class:`int`
        TARGET_REAL: int = _def(int, 'TARGET_REAL')  #: Constant ``TARGET_REAL`` of type :class:`int`
        TARGET_IMAGINARY: int = _def(int, 'TARGET_IMAGINARY')  #: Constant ``TARGET_IMAGINARY`` of type :class:`int`
        ALL: int = _def(int, 'ALL')  #: Constant ``ALL`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class Basis:
        """PEP basis type for the representation of the polynomial.
        
        - `MONOMIAL`:   Monomials (default).
        - `CHEBYSHEV1`: Chebyshev polynomials of the 1st kind.
        - `CHEBYSHEV2`: Chebyshev polynomials of the 2nd kind.
        - `LEGENDRE`:   Legendre polynomials.
        - `LAGUERRE`:   Laguerre polynomials.
        - `HERMITE`:    Hermite polynomials.
        
        See Also
        --------
        slepc.PEPBasis
        
        """
        MONOMIAL: int = _def(int, 'MONOMIAL')  #: Constant ``MONOMIAL`` of type :class:`int`
        CHEBYSHEV1: int = _def(int, 'CHEBYSHEV1')  #: Constant ``CHEBYSHEV1`` of type :class:`int`
        CHEBYSHEV2: int = _def(int, 'CHEBYSHEV2')  #: Constant ``CHEBYSHEV2`` of type :class:`int`
        LEGENDRE: int = _def(int, 'LEGENDRE')  #: Constant ``LEGENDRE`` of type :class:`int`
        LAGUERRE: int = _def(int, 'LAGUERRE')  #: Constant ``LAGUERRE`` of type :class:`int`
        HERMITE: int = _def(int, 'HERMITE')  #: Constant ``HERMITE`` of type :class:`int`
    class Scale:
        """PEP scaling strategy.
        
        - `NONE`:     No scaling.
        - `SCALAR`:   Parameter scaling.
        - `DIAGONAL`: Diagonal scaling.
        - `BOTH`:     Both parameter and diagonal scaling.
        
        See Also
        --------
        slepc.PEPScale
        
        """
        NONE: int = _def(int, 'NONE')  #: Constant ``NONE`` of type :class:`int`
        SCALAR: int = _def(int, 'SCALAR')  #: Constant ``SCALAR`` of type :class:`int`
        DIAGONAL: int = _def(int, 'DIAGONAL')  #: Constant ``DIAGONAL`` of type :class:`int`
        BOTH: int = _def(int, 'BOTH')  #: Constant ``BOTH`` of type :class:`int`
    class Refine:
        """PEP refinement strategy.
        
        - `NONE`:     No refinement.
        - `SIMPLE`:   Refine eigenpairs one by one.
        - `MULTIPLE`: Refine all eigenpairs simultaneously (invariant pair).
        
        See Also
        --------
        slepc.PEPRefine
        
        """
        NONE: int = _def(int, 'NONE')  #: Constant ``NONE`` of type :class:`int`
        SIMPLE: int = _def(int, 'SIMPLE')  #: Constant ``SIMPLE`` of type :class:`int`
        MULTIPLE: int = _def(int, 'MULTIPLE')  #: Constant ``MULTIPLE`` of type :class:`int`
    class RefineScheme:
        """PEP scheme for solving linear systems during iterative refinement.
        
        - `SCHUR`:    Schur complement.
        - `MBE`:      Mixed block elimination.
        - `EXPLICIT`: Build the explicit matrix.
        
        See Also
        --------
        slepc.PEPRefineScheme
        
        """
        SCHUR: int = _def(int, 'SCHUR')  #: Constant ``SCHUR`` of type :class:`int`
        MBE: int = _def(int, 'MBE')  #: Constant ``MBE`` of type :class:`int`
        EXPLICIT: int = _def(int, 'EXPLICIT')  #: Constant ``EXPLICIT`` of type :class:`int`
    class Extract:
        """PEP extraction strategy used.
        
        PEP extraction strategy used to obtain eigenvectors of the PEP from the
        eigenvectors of the linearization.
        
        - `NONE`:       Use the first block.
        - `NORM`:       Use the first or last block depending on norm of H.
        - `RESIDUAL`:   Use the block with smallest residual.
        - `STRUCTURED`: Combine all blocks in a certain way.
        
        See Also
        --------
        slepc.PEPExtract
        
        """
        NONE: int = _def(int, 'NONE')  #: Constant ``NONE`` of type :class:`int`
        NORM: int = _def(int, 'NORM')  #: Constant ``NORM`` of type :class:`int`
        RESIDUAL: int = _def(int, 'RESIDUAL')  #: Constant ``RESIDUAL`` of type :class:`int`
        STRUCTURED: int = _def(int, 'STRUCTURED')  #: Constant ``STRUCTURED`` of type :class:`int`
    class ErrorType:
        """PEP error type to assess accuracy of computed solutions.
        
        - `ABSOLUTE`: Absolute error.
        - `RELATIVE`: Relative error.
        - `BACKWARD`: Backward error.
        
        See Also
        --------
        slepc.PEPErrorType
        
        """
        ABSOLUTE: int = _def(int, 'ABSOLUTE')  #: Constant ``ABSOLUTE`` of type :class:`int`
        RELATIVE: int = _def(int, 'RELATIVE')  #: Constant ``RELATIVE`` of type :class:`int`
        BACKWARD: int = _def(int, 'BACKWARD')  #: Constant ``BACKWARD`` of type :class:`int`
    class Conv:
        """PEP convergence test.
        
        - `ABS`:  Absolute convergence test.
        - `REL`:  Convergence test relative to the eigenvalue.
        - `NORM`: Convergence test relative to the matrix norms.
        - `USER`: User-defined convergence test.
        
        See Also
        --------
        slepc.PEPConv
        
        """
        ABS: int = _def(int, 'ABS')  #: Constant ``ABS`` of type :class:`int`
        REL: int = _def(int, 'REL')  #: Constant ``REL`` of type :class:`int`
        NORM: int = _def(int, 'NORM')  #: Constant ``NORM`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class Stop:
        """PEP stopping test.
        
        - `BASIC`: Default stopping test.
        - `USER`:  User-defined stopping test.
        
        See Also
        --------
        slepc.PEPStop
        
        """
        BASIC: int = _def(int, 'BASIC')  #: Constant ``BASIC`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class ConvergedReason:
        """PEP convergence reasons.
        
        - `CONVERGED_TOL`:          All eigenpairs converged to requested tolerance.
        - `CONVERGED_USER`:         User-defined convergence criterion satisfied.
        - `DIVERGED_ITS`:           Maximum number of iterations exceeded.
        - `DIVERGED_BREAKDOWN`:     Solver failed due to breakdown.
        - `DIVERGED_SYMMETRY_LOST`: Lanczos-type method could not preserve symmetry.
        - `CONVERGED_ITERATING`:    Iteration not finished yet.
        
        See Also
        --------
        slepc.PEPConvergedReason
        
        """
        CONVERGED_TOL: int = _def(int, 'CONVERGED_TOL')  #: Constant ``CONVERGED_TOL`` of type :class:`int`
        CONVERGED_USER: int = _def(int, 'CONVERGED_USER')  #: Constant ``CONVERGED_USER`` of type :class:`int`
        DIVERGED_ITS: int = _def(int, 'DIVERGED_ITS')  #: Constant ``DIVERGED_ITS`` of type :class:`int`
        DIVERGED_BREAKDOWN: int = _def(int, 'DIVERGED_BREAKDOWN')  #: Constant ``DIVERGED_BREAKDOWN`` of type :class:`int`
        DIVERGED_SYMMETRY_LOST: int = _def(int, 'DIVERGED_SYMMETRY_LOST')  #: Constant ``DIVERGED_SYMMETRY_LOST`` of type :class:`int`
        CONVERGED_ITERATING: int = _def(int, 'CONVERGED_ITERATING')  #: Constant ``CONVERGED_ITERATING`` of type :class:`int`
        ITERATING: int = _def(int, 'ITERATING')  #: Constant ``ITERATING`` of type :class:`int`
    class JDProjection:
        """PEP type of projection to be used in the Jacobi-Davidson solver.
        
        - `HARMONIC`:   Harmonic projection.
        - `ORTHOGONAL`: Orthogonal projection.
        
        See Also
        --------
        slepc.PEPJDProjection
        
        """
        HARMONIC: int = _def(int, 'HARMONIC')  #: Constant ``HARMONIC`` of type :class:`int`
        ORTHOGONAL: int = _def(int, 'ORTHOGONAL')  #: Constant ``ORTHOGONAL`` of type :class:`int`
    class CISSExtraction:
        """PEP CISS extraction technique.
        
        - `RITZ`:   Ritz extraction.
        - `HANKEL`: Extraction via Hankel eigenproblem.
        - `CAA`:    Communication-avoiding Arnoldi.
        
        See Also
        --------
        slepc.PEPCISSExtraction
        
        """
        RITZ: int = _def(int, 'RITZ')  #: Constant ``RITZ`` of type :class:`int`
        HANKEL: int = _def(int, 'HANKEL')  #: Constant ``HANKEL`` of type :class:`int`
        CAA: int = _def(int, 'CAA')  #: Constant ``CAA`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the PEP data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.PEPView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:305 <slepc4py/SLEPc/PEP.pyx#L305>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the PEP object.
    
        Collective.
    
        See Also
        --------
        slepc.PEPDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:324 <slepc4py/SLEPc/PEP.pyx#L324>`
    
        """
        ...
    def reset(self) -> None:
        """Reset the PEP object.
    
        Collective.
    
        See Also
        --------
        slepc.PEPReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:338 <slepc4py/SLEPc/PEP.pyx#L338>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the PEP object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator. If not provided, it defaults to all processes.
    
        See Also
        --------
        slepc.PEPCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:350 <slepc4py/SLEPc/PEP.pyx#L350>`
    
        """
        ...
    def setType(self, pep_type: Type | str) -> None:
        """Set the particular solver to be used in the PEP object.
    
        Logically collective.
    
        Parameters
        ----------
        pep_type
            The solver to be used.
    
        Notes
        -----
        The default is `TOAR`. Normally, it is best to use
        `setFromOptions()` and then set the PEP type from the options
        database rather than by using this routine. Using the options
        database provides the user with maximum flexibility in
        evaluating the different available methods.
    
        See Also
        --------
        getType, slepc.PEPSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:371 <slepc4py/SLEPc/PEP.pyx#L371>`
    
        """
        ...
    def getType(self) -> str:
        """Get the PEP type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The solver currently being used.
    
        See Also
        --------
        setType, slepc.PEPGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:398 <slepc4py/SLEPc/PEP.pyx#L398>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all PEP options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this PEP object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.PEPGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:417 <slepc4py/SLEPc/PEP.pyx#L417>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all PEP options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all PEP option requests.
    
        Notes
        -----
        A hyphen (-) must NOT be given at the beginning of the prefix
        name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        For example, to distinguish between the runtime options for
        two different PEP contexts, one could call::
    
            P1.setOptionsPrefix("pep1_")
            P2.setOptionsPrefix("pep2_")
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.PEPGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:436 <slepc4py/SLEPc/PEP.pyx#L436>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all PEP options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all PEP option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.PEPAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:467 <slepc4py/SLEPc/PEP.pyx#L467>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set PEP options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help`` option.
    
        This routine must be called before `setUp()` if the user is to be
        allowed to set the solver type.
    
        See Also
        --------
        setOptionsPrefix, slepc.PEPSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:486 <slepc4py/SLEPc/PEP.pyx#L486>`
    
        """
        ...
    def getBasis(self) -> Basis:
        """Get the type of polynomial basis used.
    
        Not collective.
    
        Returns
        -------
        Basis
            The basis that was previously set.
    
        See Also
        --------
        setBasis, slepc.PEPGetBasis
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:505 <slepc4py/SLEPc/PEP.pyx#L505>`
    
        """
        ...
    def setBasis(self, basis: Basis) -> None:
        """Set the type of polynomial basis used.
    
        Logically collective.
    
        Set the type of polynomial basis used to describe the polynomial
        eigenvalue problem.
    
        Parameters
        ----------
        basis
            The basis to be set.
    
        Notes
        -----
        By default, the coefficient matrices passed via `setOperators()` are
        expressed in the monomial basis, i.e.
        :math:`P(\lambda)=A_0+\lambda A_1+\lambda^2 A_2+\dots+\lambda^d A_d`.
        Other polynomial bases may have better numerical behavior, but the user
        must then pass the coefficient matrices accordingly.
    
        See Also
        --------
        getBasis, setOperators, slepc.PEPSetBasis
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:524 <slepc4py/SLEPc/PEP.pyx#L524>`
    
        """
        ...
    def getProblemType(self) -> ProblemType:
        """Get the problem type from the PEP object.
    
        Not collective.
    
        Returns
        -------
        ProblemType
            The problem type that was previously set.
    
        See Also
        --------
        setProblemType, slepc.PEPGetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:553 <slepc4py/SLEPc/PEP.pyx#L553>`
    
        """
        ...
    def setProblemType(self, problem_type: ProblemType) -> None:
        """Set the type of the polynomial eigenvalue problem.
    
        Logically collective.
    
        Parameters
        ----------
        problem_type
            The problem type to be set.
    
        Notes
        -----
        This function is used to instruct SLEPc to exploit certain
        structure in the polynomial eigenproblem. By default, no
        particular structure is assumed.
    
        If the problem matrices are Hermitian (symmetric in the real
        case) or Hermitian/skew-Hermitian then the solver can exploit
        this fact to perform less operations or provide better stability.
        Hyperbolic problems are a particular case of Hermitian problems,
        some solvers may treat them simply as Hermitian.
    
        See Also
        --------
        setOperators, setType, getProblemType, slepc.PEPSetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:572 <slepc4py/SLEPc/PEP.pyx#L572>`
    
        """
        ...
    def getWhichEigenpairs(self) -> Which:
        """Get which portion of the spectrum is to be sought.
    
        Not collective.
    
        Returns
        -------
        Which
            The portion of the spectrum to be sought by the solver.
    
        See Also
        --------
        setWhichEigenpairs, slepc.PEPGetWhichEigenpairs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:602 <slepc4py/SLEPc/PEP.pyx#L602>`
    
        """
        ...
    def setWhichEigenpairs(self, which: Which) -> None:
        """Set which portion of the spectrum is to be sought.
    
        Logically collective.
    
        Parameters
        ----------
        which
            The portion of the spectrum to be sought by the solver.
    
        Notes
        -----
        Not all eigensolvers implemented in PEP account for all the
        possible values. Also, some values make sense only for certain
        types of problems. If SLEPc is compiled for real numbers
        `PEP.Which.LARGEST_IMAGINARY` and
        `PEP.Which.SMALLEST_IMAGINARY` use the absolute value of the
        imaginary part for eigenvalue selection.
    
        The target is a scalar value provided with `setTarget()`.
    
        The criterion `PEP.Which.TARGET_IMAGINARY` is available only
        in case PETSc and SLEPc have been built with complex scalars.
    
        `PEP.Which.ALL` is intended for use in combination with an
        interval (see `setInterval()`), when all eigenvalues within the
        interval are requested, or in the context of the `PEP.Type.CISS`
        solver for computing all eigenvalues in a region.
    
        See Also
        --------
        getWhichEigenpairs, setTarget, setInterval, slepc.PEPSetWhichEigenpairs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:621 <slepc4py/SLEPc/PEP.pyx#L621>`
    
        """
        ...
    def getTarget(self) -> Scalar:
        """Get the value of the target.
    
        Not collective.
    
        Returns
        -------
        Scalar
            The value of the target.
    
        Notes
        -----
        If the target was not set by the user, then zero is returned.
    
        See Also
        --------
        setTarget, slepc.PEPGetTarget
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:658 <slepc4py/SLEPc/PEP.pyx#L658>`
    
        """
        ...
    def setTarget(self, target: Scalar) -> None:
        """Set the value of the target.
    
        Logically collective.
    
        Parameters
        ----------
        target
            The value of the target.
    
        Notes
        -----
        The target is a scalar value used to determine the portion of
        the spectrum of interest. It is used in combination with
        `setWhichEigenpairs()`.
    
        When PETSc is built with real scalars, it is not possible to
        specify a complex target.
    
        See Also
        --------
        getTarget, setWhichEigenpairs, slepc.PEPSetTarget
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:681 <slepc4py/SLEPc/PEP.pyx#L681>`
    
        """
        ...
    def getTolerances(self) -> tuple[float, int]:
        """Get the tolerance and maximum iteration count.
    
        Not collective.
    
        Get the tolerance and maximum iteration count used by the default PEP
        convergence tests.
    
        Returns
        -------
        tol: float
            The convergence tolerance.
        max_it: int
            The maximum number of iterations.
    
        See Also
        --------
        setTolerances, slepc.PEPGetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:708 <slepc4py/SLEPc/PEP.pyx#L708>`
    
        """
        ...
    def setTolerances(self, tol: float | None = None, max_it: int | None = None) -> None:
        """Set the tolerance and maximum iteration count.
    
        Logically collective.
    
        Set the tolerance and maximum iteration count used by the default PEP
        convergence tests.
    
        Parameters
        ----------
        tol
            The convergence tolerance.
        max_it
            The maximum number of iterations
    
        Notes
        -----
        Use `DETERMINE` for ``max_it`` to assign a reasonably good value,
        which is dependent on the solution method.
    
        See Also
        --------
        getTolerances, slepc.PEPSetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:733 <slepc4py/SLEPc/PEP.pyx#L733>`
    
        """
        ...
    def getInterval(self) -> tuple[float, float]:
        """Get the computational interval for spectrum slicing.
    
        Not collective.
    
        Returns
        -------
        inta: float
            The left end of the interval.
        intb: float
            The right end of the interval.
    
        Notes
        -----
        If the interval was not set by the user, then zeros are returned.
    
        See Also
        --------
        setInterval, slepc.PEPGetInterval
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:764 <slepc4py/SLEPc/PEP.pyx#L764>`
    
        """
        ...
    def setInterval(self, inta: float, intb: float) -> None:
        """Set the computational interval for spectrum slicing.
    
        Logically collective.
    
        Parameters
        ----------
        inta
            The left end of the interval.
        intb
            The right end of the interval.
    
        Notes
        -----
        Spectrum slicing is a technique employed for computing all
        eigenvalues of symmetric quadratic eigenproblems in a given interval.
        This function provides the interval to be considered. It must
        be used in combination with `PEP.Which.ALL`, see
        `setWhichEigenpairs()`. Note that in polynomial eigenproblems
        spectrum slicing is implemented in `STOAR` only.
    
        See Also
        --------
        getInterval, slepc.PEPSetInterval
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:790 <slepc4py/SLEPc/PEP.pyx#L790>`
    
        """
        ...
    def getConvergenceTest(self) -> Conv:
        """Get the method used to compute the error estimate used in the convergence test.
    
        Not collective.
    
        Returns
        -------
        Conv
            The method used to compute the error estimate
            used in the convergence test.
    
        See Also
        --------
        setConvergenceTest, slepc.PEPGetConvergenceTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:820 <slepc4py/SLEPc/PEP.pyx#L820>`
    
        """
        ...
    def setConvergenceTest(self, conv: Conv) -> None:
        """Set how to compute the error estimate used in the convergence test.
    
        Logically collective.
    
        Parameters
        ----------
        conv
            The method used to compute the error estimate
            used in the convergence test.
    
        See Also
        --------
        getConvergenceTest, slepc.PEPSetConvergenceTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:840 <slepc4py/SLEPc/PEP.pyx#L840>`
    
        """
        ...
    def getRefine(self) -> tuple[Refine, int, float, int, RefineScheme]:
        """Get the refinement strategy used by the PEP object.
    
        Not collective.
    
        Returns
        -------
        ref: Refine
            The refinement type.
        npart: int
            The number of partitions of the communicator.
        tol: float
            The convergence tolerance.
        its: int
            The maximum number of refinement iterations.
        scheme: RefineScheme
            Scheme for solving linear systems.
    
        See Also
        --------
        setRefine, slepc.PEPGetRefine
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:859 <slepc4py/SLEPc/PEP.pyx#L859>`
    
        """
        ...
    def setRefine(self, ref: Refine, npart: int | None = None, tol: float | None = None, its: int | None = None, scheme: RefineScheme | None = None) -> None:
        """Set the refinement strategy used by the PEP object.
    
        Logically collective.
    
        Set the refinement strategy used by the PEP object, and the associated
        parameters.
    
        Parameters
        ----------
        ref
            The refinement type.
        npart
            The number of partitions of the communicator.
        tol
            The convergence tolerance.
        its
            The maximum number of refinement iterations.
        scheme
            Scheme for solving linear systems.
    
        See Also
        --------
        getRefine, slepc.PEPSetRefine
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:890 <slepc4py/SLEPc/PEP.pyx#L890>`
    
        """
        ...
    def getRefineKSP(self) -> KSP:
        """Get the ``KSP`` object used by the eigensolver in the refinement phase.
    
        Collective.
    
        Returns
        -------
        `petsc4py.PETSc.KSP`
            The linear solver object.
    
        See Also
        --------
        setRefine, slepc.PEPRefineGetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:934 <slepc4py/SLEPc/PEP.pyx#L934>`
    
        """
        ...
    def setExtract(self, extract: Extract) -> None:
        """Set the extraction strategy to be used.
    
        Logically collective.
    
        Parameters
        ----------
        extract
            The extraction strategy.
    
        Notes
        -----
        This is relevant for solvers based on linearization. Once the
        solver has converged, the polynomial eigenvectors can be
        extracted from the eigenvectors of the linearized problem in
        different ways.
    
        See Also
        --------
        getExtract, slepc.PEPSetExtract
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:954 <slepc4py/SLEPc/PEP.pyx#L954>`
    
        """
        ...
    def getExtract(self) -> Extract:
        """Get the extraction technique used by the `PEP` object.
    
        Not collective.
    
        Returns
        -------
        Extract
            The extraction strategy.
    
        See Also
        --------
        setExtract, slepc.PEPGetExtract
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:979 <slepc4py/SLEPc/PEP.pyx#L979>`
    
        """
        ...
    def getTrackAll(self) -> bool:
        """Get the flag indicating whether all residual norms must be computed.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether the solver computes all residuals or not.
    
        See Also
        --------
        setTrackAll, slepc.PEPGetTrackAll
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:998 <slepc4py/SLEPc/PEP.pyx#L998>`
    
        """
        ...
    def setTrackAll(self, trackall: bool) -> None:
        """Set flag to compute the residual of all approximate eigenpairs.
    
        Logically collective.
    
        Set if the solver must compute the residual of all approximate
        eigenpairs or not.
    
        Parameters
        ----------
        trackall
            Whether to compute all residuals or not.
    
        See Also
        --------
        getTrackAll, slepc.PEPSetTrackAll
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1017 <slepc4py/SLEPc/PEP.pyx#L1017>`
    
        """
        ...
    def getDimensions(self) -> tuple[int, int, int]:
        """Get the number of eigenvalues to compute and the dimension of the subspace.
    
        Not collective.
    
        Returns
        -------
        nev: int
            Number of eigenvalues to compute.
        ncv: int
            Maximum dimension of the subspace to be used by the solver.
        mpd: int
            Maximum dimension allowed for the projected problem.
    
        See Also
        --------
        setDimensions, slepc.PEPGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1038 <slepc4py/SLEPc/PEP.pyx#L1038>`
    
        """
        ...
    def setDimensions(self, nev: int | None = None, ncv: int | None = None, mpd: int | None = None) -> None:
        """Set the number of eigenvalues to compute and the dimension of the subspace.
    
        Logically collective.
    
        Parameters
        ----------
        nev
            Number of eigenvalues to compute.
        ncv
            Maximum dimension of the subspace to be used by the solver.
        mpd
            Maximum dimension allowed for the projected problem.
    
        Notes
        -----
        Use `DETERMINE` for ``ncv`` and ``mpd`` to assign a reasonably good
        value, which is dependent on the solution method.
    
        The parameters ``ncv`` and ``mpd`` are intimately related, so that
        the user is advised to set one of them at most. Normal usage
        is the following:
    
        + In cases where ``nev`` is small, the user sets ``ncv``
          (a reasonable default is 2 * ``nev``).
    
        + In cases where ``nev`` is large, the user sets ``mpd``.
    
        The value of ``ncv`` should always be between ``nev`` and (``nev`` +
        ``mpd``), typically ``ncv`` = ``nev`` + ``mpd``. If ``nev`` is not too
        large, ``mpd`` = ``nev`` is a reasonable choice, otherwise a
        smaller value should be used.
    
        See Also
        --------
        getDimensions, slepc.PEPSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1063 <slepc4py/SLEPc/PEP.pyx#L1063>`
    
        """
        ...
    def getST(self) -> ST:
        """Get the spectral transformation object associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        ST
            The spectral transformation.
    
        See Also
        --------
        setST, slepc.PEPGetST
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1114 <slepc4py/SLEPc/PEP.pyx#L1114>`
    
        """
        ...
    def setST(self, st: ST) -> None:
        """Set a spectral transformation object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        st
            The spectral transformation.
    
        See Also
        --------
        getST, slepc.PEPSetST
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1134 <slepc4py/SLEPc/PEP.pyx#L1134>`
    
        """
        ...
    def getScale(self, Dl: petsc4py.PETSc.Vec | None = None, Dr: petsc4py.PETSc.Vec | None = None) -> tuple[Scale, float, int, float]:
        """Get the strategy used for scaling the polynomial eigenproblem.
    
        Not collective.
    
        Parameters
        ----------
        Dl
            Placeholder for the returned left diagonal matrix.
        Dr
            Placeholder for the returned right diagonal matrix.
    
        Returns
        -------
        scale: Scale
            The scaling strategy.
        alpha: float
            The scaling factor.
        its: int
            The number of iterations of diagonal scaling.
        lbda: float
            Approximation of the wanted eigenvalues (modulus).
    
        See Also
        --------
        setScale, slepc.PEPGetScale
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1151 <slepc4py/SLEPc/PEP.pyx#L1151>`
    
        """
        ...
    def setScale(self, scale: Scale, alpha: float | None = None, Dl: petsc4py.PETSc.Vec | None = None, Dr: petsc4py.PETSc.Vec | None = None, its: int | None = None, lbda: float | None = None) -> None:
        """Set the scaling strategy to be used.
    
        Collective.
    
        Parameters
        ----------
        scale
            The scaling strategy.
        alpha
            The scaling factor.
        Dl
            The left diagonal matrix.
        Dr
            The right diagonal matrix.
        its
            The number of iterations of diagonal scaling.
        lbda
            Approximation of the wanted eigenvalues (modulus).
    
        See Also
        --------
        getScale, slepc.PEPSetScale
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1204 <slepc4py/SLEPc/PEP.pyx#L1204>`
    
        """
        ...
    def getBV(self) -> BV:
        """Get the basis vectors object associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        BV
            The basis vectors context.
    
        See Also
        --------
        setBV, slepc.PEPGetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1250 <slepc4py/SLEPc/PEP.pyx#L1250>`
    
        """
        ...
    def setBV(self, bv: BV) -> None:
        """Set a basis vectors object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        bv
            The basis vectors context.
    
        See Also
        --------
        getBV, slepc.PEPSetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1270 <slepc4py/SLEPc/PEP.pyx#L1270>`
    
        """
        ...
    def getRG(self) -> RG:
        """Get the region object associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        RG
            The region context.
    
        See Also
        --------
        setRG, slepc.PEPGetRG
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1287 <slepc4py/SLEPc/PEP.pyx#L1287>`
    
        """
        ...
    def setRG(self, rg: RG) -> None:
        """Set a region object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        rg
            The region context.
    
        See Also
        --------
        getRG, slepc.PEPSetRG
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1307 <slepc4py/SLEPc/PEP.pyx#L1307>`
    
        """
        ...
    def getDS(self) -> DS:
        """Get the direct solver associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        DS
            The direct solver context.
    
        See Also
        --------
        setDS, slepc.PEPGetDS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1324 <slepc4py/SLEPc/PEP.pyx#L1324>`
    
        """
        ...
    def setDS(self, ds: DS) -> None:
        """Set a direct solver object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        ds
            The direct solver context.
    
        See Also
        --------
        getDS, slepc.PEPSetDS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1344 <slepc4py/SLEPc/PEP.pyx#L1344>`
    
        """
        ...
    def getOperators(self) -> list[Mat]:
        """Get the matrices associated with the eigenvalue problem.
    
        Collective.
    
        Returns
        -------
        list of petsc4py.PETSc.Mat
            The matrices associated with the eigensystem.
    
        See Also
        --------
        setOperators, slepc.PEPGetOperators
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1361 <slepc4py/SLEPc/PEP.pyx#L1361>`
    
        """
        ...
    def setOperators(self, operators: list[Mat]) -> None:
        """Set the matrices associated with the eigenvalue problem.
    
        Collective.
    
        Parameters
        ----------
        operators
            The matrices associated with the eigensystem.
    
        Notes
        -----
        The polynomial eigenproblem is defined as :math:`P(\lambda)x=0`,
        where :math:`\lambda` is the eigenvalue, :math:`x` is the eigenvector,
        and :math:`P` is defined as
        :math:`P(\lambda) = A_0 + \lambda A_1 + \dots + \lambda^d A_d`, with
        :math:`d` = ``nmat``-1 (the degree of :math:`P`). For non-monomial
        bases, this expression is different.
    
        See Also
        --------
        getOperators, slepc.PEPSetOperators
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1387 <slepc4py/SLEPc/PEP.pyx#L1387>`
    
        """
        ...
    def setInitialSpace(self, space: Vec | list[Vec]) -> None:
        """Set the initial space from which the eigensolver starts to iterate.
    
        Collective.
    
        Parameters
        ----------
        space
            The initial space.
    
        Notes
        -----
        Some solvers start to iterate on a single vector (initial vector).
        In that case, only the first vector is taken into account and the
        other vectors are ignored.
    
        These vectors do not persist from one `solve()` call to the other,
        so the initial space should be set every time.
    
        The vectors do not need to be mutually orthonormal, since they are
        explicitly orthonormalized internally.
    
        Common usage of this function is when the user can provide a rough
        approximation of the wanted eigenspace. Then, convergence may be faster.
    
        See Also
        --------
        setUp, slepc.PEPSetInitialSpace
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1420 <slepc4py/SLEPc/PEP.pyx#L1420>`
    
        """
        ...
    def setStoppingTest(self, stopping: PEPStoppingFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set a function to decide when to stop the outer iteration of the eigensolver.
    
        Logically collective.
    
        See Also
        --------
        getStoppingTest, slepc.PEPSetStoppingTestFunction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1459 <slepc4py/SLEPc/PEP.pyx#L1459>`
    
        """
        ...
    def getStoppingTest(self) -> PEPStoppingFunction:
        """Get the stopping test function.
    
        Not collective.
    
        Returns
        -------
        PEPStoppingFunction
            The stopping test function.
    
        See Also
        --------
        setStoppingTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1483 <slepc4py/SLEPc/PEP.pyx#L1483>`
    
        """
        ...
    def setEigenvalueComparison(self, comparison: PEPEigenvalueComparison | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set an eigenvalue comparison function.
    
        Logically collective.
    
        Notes
        -----
        This eigenvalue comparison function is used when `setWhichEigenpairs()`
        is set to `PEP.Which.USER`.
    
        See Also
        --------
        getEigenvalueComparison, slepc.PEPSetEigenvalueComparison
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1500 <slepc4py/SLEPc/PEP.pyx#L1500>`
    
        """
        ...
    def getEigenvalueComparison(self) -> PEPEigenvalueComparison:
        """Get the eigenvalue comparison function.
    
        Not collective.
    
        Returns
        -------
        PEPEigenvalueComparison
            The eigenvalue comparison function.
    
        See Also
        --------
        setEigenvalueComparison
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1530 <slepc4py/SLEPc/PEP.pyx#L1530>`
    
        """
        ...
    def setMonitor(self, monitor: PEPMonitorFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Append a monitor function to the list of monitors.
    
        Logically collective.
    
        See Also
        --------
        getMonitor, cancelMonitor, slepc.PEPMonitorSet
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1547 <slepc4py/SLEPc/PEP.pyx#L1547>`
    
        """
        ...
    def getMonitor(self) -> PEPMonitorFunction:
        """Get the list of monitor functions.
    
        Not collective.
    
        Returns
        -------
        PEPMonitorFunction
            The list of monitor functions.
    
        See Also
        --------
        setMonitor
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1572 <slepc4py/SLEPc/PEP.pyx#L1572>`
    
        """
        ...
    def cancelMonitor(self) -> None:
        """Clear all monitors for a `PEP` object.
    
        Logically collective.
    
        See Also
        --------
        slepc.PEPMonitorCancel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1589 <slepc4py/SLEPc/PEP.pyx#L1589>`
    
        """
        ...
    def setUp(self) -> None:
        """Set up all the internal data structures.
    
        Collective.
    
        Notes
        -----
        Sets up all the internal data structures necessary for the execution
        of the eigensolver. This includes the setup of the internal `ST`
        object.
    
        This function need not be called explicitly in most cases,
        since `solve()` calls it. It can be useful when one wants to
        measure the set-up time separately from the solve time.
    
        See Also
        --------
        solve, slepc.PEPSetUp
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1604 <slepc4py/SLEPc/PEP.pyx#L1604>`
    
        """
        ...
    def solve(self) -> None:
        """Solve the polynomial eigenproblem.
    
        Collective.
    
        Notes
        -----
        The problem matrices are specified with `setOperators()`.
    
        `solve()` will return without generating an error regardless of
        whether all requested solutions were computed or not. Call
        `getConverged()` to get the actual number of computed solutions,
        and `getConvergedReason()` to determine if the solver converged
        or failed and why.
    
        See Also
        --------
        setUp, setOperators, getConverged, getConvergedReason, slepc.PEPSolve
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1626 <slepc4py/SLEPc/PEP.pyx#L1626>`
    
        """
        ...
    def getIterationNumber(self) -> int:
        """Get the current iteration number.
    
        Not collective.
    
        If the call to `solve()` is complete, then it returns the number of
        iterations carried out by the solution method.
    
        Returns
        -------
        int
            Iteration number.
    
        See Also
        --------
        getConvergedReason, setTolerances, slepc.PEPGetIterationNumber
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1648 <slepc4py/SLEPc/PEP.pyx#L1648>`
    
        """
        ...
    def getConvergedReason(self) -> ConvergedReason:
        """Get the reason why the `solve()` iteration was stopped.
    
        Not collective.
    
        Returns
        -------
        ConvergedReason
            Negative value indicates diverged, positive value converged.
    
        See Also
        --------
        setTolerances, solve, slepc.PEPGetConvergedReason
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1670 <slepc4py/SLEPc/PEP.pyx#L1670>`
    
        """
        ...
    def getConverged(self) -> int:
        """Get the number of converged eigenpairs.
    
        Not collective.
    
        Returns
        -------
        nconv: int
            Number of converged eigenpairs.
    
        Notes
        -----
        This function should be called after `solve()` has finished.
    
        The value ``nconv`` may be different from the number of requested
        solutions ``nev``, but not larger than ``ncv``, see `setDimensions()`.
    
        See Also
        --------
        setDimensions, solve, getEigenpair, slepc.PEPGetConverged
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1689 <slepc4py/SLEPc/PEP.pyx#L1689>`
    
        """
        ...
    def getEigenpair(self, i: int, Vr: Vec | None = None, Vi: Vec | None = None) -> complex:
        """Get the i-th solution of the eigenproblem as computed by `solve()`.
    
        Collective.
    
        The solution consists of both the eigenvalue and the eigenvector.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
        Vr
            Placeholder for the returned eigenvector (real part).
        Vi
            Placeholder for the returned eigenvector (imaginary part).
    
        Returns
        -------
        complex
            The computed eigenvalue.
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and ``nconv-1`` (see
        `getConverged()`). Eigenpairs are indexed according to the ordering
        criterion established with `setWhichEigenpairs()`.
    
        The eigenvector is normalized to have unit norm.
    
        See Also
        --------
        solve, getConverged, setWhichEigenpairs, slepc.PEPGetEigenpair
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1715 <slepc4py/SLEPc/PEP.pyx#L1715>`
    
        """
        ...
    def getErrorEstimate(self, i: int) -> float:
        """Get the error estimate associated to the i-th computed eigenpair.
    
        Not collective.
    
        Parameters
        ----------
        i
            Index of the solution to be considered.
    
        Returns
        -------
        float
            Error estimate.
    
        Notes
        -----
        This is the error estimate used internally by the eigensolver.
        The actual error bound can be computed with `computeError()`.
    
        See Also
        --------
        computeError, slepc.PEPGetErrorEstimate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1756 <slepc4py/SLEPc/PEP.pyx#L1756>`
    
        """
        ...
    def computeError(self, i: int, etype: ErrorType | None = None) -> float:
        """Compute the error associated with the i-th computed eigenpair.
    
        Collective.
    
        Compute the error (based on the residual norm) associated with the
        i-th computed eigenpair.
    
        Parameters
        ----------
        i
            Index of the solution to be considered.
        etype
            The error type to compute.
    
        Returns
        -------
        float
            The error bound, computed in various ways from the residual norm
            :math:`\|P(\lambda)x\|_2` where :math:`\lambda` is the eigenvalue
            and :math:`x` is the eigenvector.
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and ``nconv-1``
        (see `getConverged()`).
    
        See Also
        --------
        getErrorEstimate, slepc.PEPComputeError
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1785 <slepc4py/SLEPc/PEP.pyx#L1785>`
    
        """
        ...
    def errorView(self, etype: ErrorType | None = None, viewer: petsc4py.PETSc.Viewer | None = None) -> None:
        """Display the errors associated with the computed solution.
    
        Collective.
    
        Display the errors and the eigenvalues.
    
        Parameters
        ----------
        etype
            The error type to compute.
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        Notes
        -----
        By default, this function checks the error of all eigenpairs and prints
        the eigenvalues if all of them are below the requested tolerance.
        If the viewer has format ``ASCII_INFO_DETAIL`` then a table with
        eigenvalues and corresponding errors is printed.
    
        See Also
        --------
        solve, valuesView, vectorsView, slepc.PEPErrorView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1823 <slepc4py/SLEPc/PEP.pyx#L1823>`
    
        """
        ...
    def valuesView(self, viewer: Viewer | None = None) -> None:
        """Display the computed eigenvalues in a viewer.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        solve, vectorsView, errorView, slepc.PEPValuesView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1855 <slepc4py/SLEPc/PEP.pyx#L1855>`
    
        """
        ...
    def vectorsView(self, viewer: Viewer | None = None) -> None:
        """Output computed eigenvectors to a viewer.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        solve, valuesView, errorView, slepc.PEPVectorsView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1874 <slepc4py/SLEPc/PEP.pyx#L1874>`
    
        """
        ...
    def setLinearEPS(self, eps: EPS) -> None:
        """Set an eigensolver object associated to the polynomial eigenvalue solver.
    
        Collective.
    
        Parameters
        ----------
        eps
            The linear eigensolver.
    
        See Also
        --------
        getLinearEPS, slepc.PEPLinearSetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1895 <slepc4py/SLEPc/PEP.pyx#L1895>`
    
        """
        ...
    def getLinearEPS(self) -> EPS:
        """Get the eigensolver object associated to the polynomial eigenvalue solver.
    
        Collective.
    
        Returns
        -------
        EPS
            The linear eigensolver.
    
        See Also
        --------
        setLinearEPS, slepc.PEPLinearGetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1912 <slepc4py/SLEPc/PEP.pyx#L1912>`
    
        """
        ...
    def setLinearLinearization(self, alpha: float = 1.0, beta: float = 0.0) -> None:
        """Set the coefficients that define the linearization of a quadratic eigenproblem.
    
        Logically collective.
    
        Parameters
        ----------
        alpha
            First parameter of the linearization.
        beta
            Second parameter of the linearization.
    
        See Also
        --------
        getLinearLinearization, slepc.PEPLinearSetLinearization
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1932 <slepc4py/SLEPc/PEP.pyx#L1932>`
    
        """
        ...
    def getLinearLinearization(self) -> tuple[float, float]:
        """Get the coeffs. defining the linearization of a quadratic eigenproblem.
    
        Not collective.
    
        Returns
        -------
        alpha: float
            First parameter of the linearization.
        beta: float
            Second parameter of the linearization.
    
        See Also
        --------
        setLinearLinearization, slepc.PEPLinearGetLinearization
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1953 <slepc4py/SLEPc/PEP.pyx#L1953>`
    
        """
        ...
    def setLinearExplicitMatrix(self, flag: bool) -> None:
        """Set flag to explicitly build the matrices for the linearization.
    
        Logically collective.
    
        Parameters
        ----------
        flag
            Boolean flag indicating if the matrices are built explicitly.
    
        See Also
        --------
        getLinearExplicitMatrix, slepc.PEPLinearSetExplicitMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1975 <slepc4py/SLEPc/PEP.pyx#L1975>`
    
        """
        ...
    def getLinearExplicitMatrix(self) -> bool:
        """Get if the matrices for the linearization are built explicitly.
    
        Not collective.
    
        Returns
        -------
        bool
            Boolean flag indicating if the matrices are built explicitly.
    
        See Also
        --------
        getLinearExplicitMatrix, slepc.PEPLinearSetExplicitMatrix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:1993 <slepc4py/SLEPc/PEP.pyx#L1993>`
    
        """
        ...
    def setQArnoldiRestart(self, keep: float) -> None:
        """Set the restart parameter for the Q-Arnoldi method.
    
        Logically collective.
    
        Set the restart parameter for the Q-Arnoldi method, in
        particular the proportion of basis vectors that must be kept
        after restart.
    
        Parameters
        ----------
        keep
            The number of vectors to be kept at restart.
    
        Notes
        -----
        Allowed values are in the range [0.1,0.9]. The default is 0.5.
    
        See Also
        --------
        getQArnoldiRestart, slepc.PEPQArnoldiSetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2014 <slepc4py/SLEPc/PEP.pyx#L2014>`
    
        """
        ...
    def getQArnoldiRestart(self) -> float:
        """Get the restart parameter used in the Q-Arnoldi method.
    
        Not collective.
    
        Returns
        -------
        float
            The number of vectors to be kept at restart.
    
        See Also
        --------
        setQArnoldiRestart, slepc.PEPQArnoldiGetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2040 <slepc4py/SLEPc/PEP.pyx#L2040>`
    
        """
        ...
    def setQArnoldiLocking(self, lock: bool) -> None:
        """Toggle between locking and non-locking variants of the Q-Arnoldi method.
    
        Logically collective.
    
        Parameters
        ----------
        lock
            ``True`` if the locking variant must be selected.
    
        Notes
        -----
        The default is to lock converged eigenpairs when the method restarts.
        This behavior can be changed so that all directions are kept in the
        working subspace even if already converged to working accuracy (the
        non-locking variant).
    
        See Also
        --------
        getQArnoldiLocking, slepc.PEPQArnoldiSetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2059 <slepc4py/SLEPc/PEP.pyx#L2059>`
    
        """
        ...
    def getQArnoldiLocking(self) -> bool:
        """Get the locking flag used in the Q-Arnoldi method.
    
        Not collective.
    
        Returns
        -------
        bool
            The locking flag.
    
        See Also
        --------
        setQArnoldiLocking, slepc.PEPQArnoldiGetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2084 <slepc4py/SLEPc/PEP.pyx#L2084>`
    
        """
        ...
    def setTOARRestart(self, keep: float) -> None:
        """Set the restart parameter for the TOAR method.
    
        Logically collective.
    
        Set the restart parameter for the TOAR method, in
        particular the proportion of basis vectors that must be kept
        after restart.
    
        Parameters
        ----------
        keep
            The number of vectors to be kept at restart.
    
        Notes
        -----
        Allowed values are in the range [0.1,0.9]. The default is 0.5.
    
        See Also
        --------
        getTOARRestart, slepc.PEPTOARSetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2105 <slepc4py/SLEPc/PEP.pyx#L2105>`
    
        """
        ...
    def getTOARRestart(self) -> float:
        """Get the restart parameter used in the TOAR method.
    
        Not collective.
    
        Returns
        -------
        float
            The number of vectors to be kept at restart.
    
        See Also
        --------
        setTOARRestart, slepc.PEPTOARGetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2131 <slepc4py/SLEPc/PEP.pyx#L2131>`
    
        """
        ...
    def setTOARLocking(self, lock: bool) -> None:
        """Toggle between locking and non-locking variants of the TOAR method.
    
        Logically collective.
    
        Parameters
        ----------
        lock
            ``True`` if the locking variant must be selected.
    
        Notes
        -----
        The default is to lock converged eigenpairs when the method restarts.
        This behavior can be changed so that all directions are kept in the
        working subspace even if already converged to working accuracy (the
        non-locking variant).
    
        See Also
        --------
        getTOARLocking, slepc.PEPTOARSetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2150 <slepc4py/SLEPc/PEP.pyx#L2150>`
    
        """
        ...
    def getTOARLocking(self) -> bool:
        """Get the locking flag used in the TOAR method.
    
        Not collective.
    
        Returns
        -------
        bool
            The locking flag.
    
        See Also
        --------
        setTOARLocking, slepc.PEPTOARGetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2175 <slepc4py/SLEPc/PEP.pyx#L2175>`
    
        """
        ...
    def setSTOARLinearization(self, alpha: float = 1.0, beta: float = 0.0) -> None:
        """Set the coefficients that define the linearization of a quadratic eigenproblem.
    
        Logically collective.
    
        Parameters
        ----------
        alpha
            First parameter of the linearization.
        beta
            Second parameter of the linearization.
    
        See Also
        --------
        getSTOARLinearization, slepc.PEPSTOARSetLinearization
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2196 <slepc4py/SLEPc/PEP.pyx#L2196>`
    
        """
        ...
    def getSTOARLinearization(self) -> tuple[float, float]:
        """Get the coefficients that define the linearization of a quadratic eigenproblem.
    
        Not collective.
    
        Returns
        -------
        alpha: float
            First parameter of the linearization.
        beta: float
            Second parameter of the linearization.
    
        See Also
        --------
        setSTOARLinearization, slepc.PEPSTOARGetLinearization
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2217 <slepc4py/SLEPc/PEP.pyx#L2217>`
    
        """
        ...
    def setSTOARLocking(self, lock: bool) -> None:
        """Toggle between locking and non-locking variants of the STOAR method.
    
        Logically collective.
    
        Parameters
        ----------
        lock
            ``True`` if the locking variant must be selected.
    
        Notes
        -----
        The default is to lock converged eigenpairs when the method restarts.
        This behavior can be changed so that all directions are kept in the
        working subspace even if already converged to working accuracy (the
        non-locking variant).
    
        See Also
        --------
        getSTOARLocking, slepc.PEPSTOARSetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2239 <slepc4py/SLEPc/PEP.pyx#L2239>`
    
        """
        ...
    def getSTOARLocking(self) -> bool:
        """Get the locking flag used in the STOAR method.
    
        Not collective.
    
        Returns
        -------
        bool
            The locking flag.
    
        See Also
        --------
        setSTOARLocking, slepc.PEPSTOARGetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2264 <slepc4py/SLEPc/PEP.pyx#L2264>`
    
        """
        ...
    def setSTOARDetectZeros(self, detect: bool) -> None:
        """Set flag to enforce detection of zeros during the factorizations.
    
        Logically collective.
    
        Set a flag to enforce detection of zeros during the factorizations
        throughout the spectrum slicing computation.
    
        Parameters
        ----------
        detect
            ``True`` if zeros must checked for.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        A zero in the factorization indicates that a shift coincides with
        an eigenvalue.
    
        This flag is turned off by default, and may be necessary in some cases.
        This feature currently requires an external package for factorizations
        with support for zero detection, e.g. MUMPS.
    
        See Also
        --------
        setInterval, getSTOARDetectZeros, slepc.PEPSTOARSetDetectZeros
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2283 <slepc4py/SLEPc/PEP.pyx#L2283>`
    
        """
        ...
    def getSTOARDetectZeros(self) -> bool:
        """Get the flag that enforces zero detection in spectrum slicing.
    
        Not collective.
    
        Returns
        -------
        bool
            The zero detection flag.
    
        See Also
        --------
        setSTOARDetectZeros, slepc.PEPSTOARGetDetectZeros
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2316 <slepc4py/SLEPc/PEP.pyx#L2316>`
    
        """
        ...
    def setSTOARDimensions(self, nev: int | None = None, ncv: int | None = None, mpd: int | None = None) -> None:
        """Set the dimensions used for each subsolve step.
    
        Logically collective.
    
        Parameters
        ----------
        nev
            Number of eigenvalues to compute.
        ncv
            Maximum dimension of the subspace to be used by the solver.
        mpd
            Maximum dimension allowed for the projected problem.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        The meaning of the parameters is the same as in `setDimensions()`, but
        the ones here apply to every subsolve done by the child `PEP` object.
    
        See Also
        --------
        setInterval, setDimensions, getSTOARDimensions, slepc.PEPSTOARSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2335 <slepc4py/SLEPc/PEP.pyx#L2335>`
    
        """
        ...
    def getSTOARDimensions(self) -> tuple[int, int, int]:
        """Get the dimensions used for each subsolve step.
    
        Not collective.
    
        Returns
        -------
        nev: int
            Number of eigenvalues to compute.
        ncv: int
            Maximum dimension of the subspace to be used by the solver.
        mpd: int
            Maximum dimension allowed for the projected problem.
    
        See Also
        --------
        setSTOARDimensions, slepc.PEPSTOARGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2375 <slepc4py/SLEPc/PEP.pyx#L2375>`
    
        """
        ...
    def getSTOARInertias(self) -> tuple[ArrayReal, ArrayInt]:
        """Get the values of the shifts and their corresponding inertias.
    
        Not collective.
    
        Get the values of the shifts and their corresponding inertias
        in case of doing spectrum slicing for a computational interval.
    
        Returns
        -------
        shifts: ArrayReal
            The values of the shifts used internally in the solver.
        inertias: ArrayInt
            The values of the inertia in each shift.
    
        Notes
        -----
        This call makes sense only for spectrum slicing runs, that is, when
        an interval has been given with `setInterval()` and `SINVERT` is set.
    
        If called after `solve()`, all shifts used internally by the solver are
        returned (including both endpoints and any intermediate ones). If called
        before `solve()` and after `setUp()` then only the information of the
        endpoints of subintervals is available.
    
        See Also
        --------
        setInterval, slepc.PEPSTOARGetInertias
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2400 <slepc4py/SLEPc/PEP.pyx#L2400>`
    
        """
        ...
    def setSTOARCheckEigenvalueType(self, flag: bool) -> None:
        """Set flag to check if all eigenvalues have the same definite type.
    
        Logically collective.
    
        Set a flag to check that all the eigenvalues obtained throughout the
        spectrum slicing computation have the same definite type.
    
        Parameters
        ----------
        flag
            Whether the eigenvalue type is checked or not.
    
        Notes
        -----
        This option is relevant only for spectrum slicing computations, but
        is ignored in `slepc4py.SLEPc.PEP.ProblemType.HYPERBOLIC` problems.
    
        This flag is turned on by default, to guarantee that the computed
        eigenvalues have the same type (otherwise the computed solution might
        be wrong). But since the check is computationally quite expensive,
        the check may be turned off if the user knows for sure that all
        eigenvalues in the requested interval have the same type.
    
        See Also
        --------
        getSTOARCheckEigenvalueType, slepc.PEPSTOARSetCheckEigenvalueType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2444 <slepc4py/SLEPc/PEP.pyx#L2444>`
    
        """
        ...
    def getSTOARCheckEigenvalueType(self) -> bool:
        """Get the flag for the eigenvalue type check in spectrum slicing.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether the eigenvalue type is checked or not.
    
        See Also
        --------
        setSTOARCheckEigenvalueType, slepc.PEPSTOARGetCheckEigenvalueType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2476 <slepc4py/SLEPc/PEP.pyx#L2476>`
    
        """
        ...
    def setJDRestart(self, keep: float) -> None:
        """Set the restart parameter for the Jacobi-Davidson method.
    
        Logically collective.
    
        Set the restart parameter for the Jacobi-Davidson method, in
        particular the proportion of basis vectors that must be kept
        after restart.
    
        Parameters
        ----------
        keep
            The number of vectors to be kept at restart.
    
        Notes
        -----
        Allowed values are in the range [0.1,0.9]. The default is 0.5.
    
        See Also
        --------
        getJDRestart, slepc.PEPJDSetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2497 <slepc4py/SLEPc/PEP.pyx#L2497>`
    
        """
        ...
    def getJDRestart(self) -> float:
        """Get the restart parameter used in the Jacobi-Davidson method.
    
        Not collective.
    
        Returns
        -------
        float
            The number of vectors to be kept at restart.
    
        See Also
        --------
        setJDRestart, slepc.PEPJDGetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2523 <slepc4py/SLEPc/PEP.pyx#L2523>`
    
        """
        ...
    def setJDFix(self, fix: float) -> None:
        """Set the threshold for changing the target in the correction equation.
    
        Logically collective.
    
        Parameters
        ----------
        fix
            Threshold for changing the target.
    
        Notes
        -----
        The target in the correction equation is fixed at the first iterations.
        When the norm of the residual vector is lower than the fix value,
        the target is set to the corresponding eigenvalue.
    
        See Also
        --------
        getJDFix, slepc.PEPJDSetFix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2542 <slepc4py/SLEPc/PEP.pyx#L2542>`
    
        """
        ...
    def getJDFix(self) -> float:
        """Get threshold for changing the target in the correction equation.
    
        Not collective.
    
        Returns
        -------
        float
            The threshold for changing the target.
    
        See Also
        --------
        setJDFix, slepc.PEPJDGetFix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2566 <slepc4py/SLEPc/PEP.pyx#L2566>`
    
        """
        ...
    def setJDReusePreconditioner(self, flag: bool) -> None:
        """Set a flag indicating whether the preconditioner must be reused or not.
    
        Logically collective.
    
        Parameters
        ----------
        flag
            The reuse flag.
    
        Notes
        -----
        The default value is ``False``. If set to ``True``, the
        preconditioner is built only at the beginning, using the
        target value. Otherwise, it may be rebuilt (depending on
        the ``fix`` parameter) at each iteration from the Ritz value.
    
        See Also
        --------
        setJDFix, getJDReusePreconditioner, slepc.PEPJDSetReusePreconditioner
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2585 <slepc4py/SLEPc/PEP.pyx#L2585>`
    
        """
        ...
    def getJDReusePreconditioner(self) -> bool:
        """Get the flag for reusing the preconditioner.
    
        Not collective.
    
        Returns
        -------
        bool
            The reuse flag.
    
        See Also
        --------
        setJDReusePreconditioner, slepc.PEPJDGetReusePreconditioner
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2610 <slepc4py/SLEPc/PEP.pyx#L2610>`
    
        """
        ...
    def setJDMinimalityIndex(self, flag: int) -> None:
        """Set the maximum allowed value for the minimality index.
    
        Logically collective.
    
        Parameters
        ----------
        flag
            The maximum minimality index.
    
        Notes
        -----
        The default value is equal to the degree of the polynomial. A
        smaller value can be used if the wanted eigenvectors are known
        to be linearly independent.
    
        See Also
        --------
        getJDMinimalityIndex, slepc.PEPJDSetMinimalityIndex
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2629 <slepc4py/SLEPc/PEP.pyx#L2629>`
    
        """
        ...
    def getJDMinimalityIndex(self) -> int:
        """Get the maximum allowed value of the minimality index.
    
        Not collective.
    
        Returns
        -------
        int
            The maximum minimality index.
    
        See Also
        --------
        setJDMinimalityIndex, slepc.PEPJDGetMinimalityIndex
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2653 <slepc4py/SLEPc/PEP.pyx#L2653>`
    
        """
        ...
    def setJDProjection(self, proj: JDProjection) -> None:
        """Set the type of projection to be used in the Jacobi-Davidson solver.
    
        Logically collective.
    
        Parameters
        ----------
        proj
            The type of projection.
    
        See Also
        --------
        getJDProjection, slepc.PEPJDSetProjection
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2672 <slepc4py/SLEPc/PEP.pyx#L2672>`
    
        """
        ...
    def getJDProjection(self) -> JDProjection:
        """Get the type of projection to be used in the Jacobi-Davidson solver.
    
        Not collective.
    
        Returns
        -------
        JDProjection
            The type of projection.
    
        See Also
        --------
        setJDProjection, slepc.PEPJDGetProjection
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2690 <slepc4py/SLEPc/PEP.pyx#L2690>`
    
        """
        ...
    def setCISSExtraction(self, extraction: CISSExtraction) -> None:
        """Set the extraction technique used in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        extraction
            The extraction technique.
    
        See Also
        --------
        getCISSExtraction, slepc.PEPCISSSetExtraction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2711 <slepc4py/SLEPc/PEP.pyx#L2711>`
    
        """
        ...
    def getCISSExtraction(self) -> CISSExtraction:
        """Get the extraction technique used in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        CISSExtraction
            The extraction technique.
    
        See Also
        --------
        setCISSExtraction, slepc.PEPCISSGetExtraction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2729 <slepc4py/SLEPc/PEP.pyx#L2729>`
    
        """
        ...
    def setCISSSizes(self, ip: int | None = None, bs: int | None = None, ms: int | None = None, npart: int | None = None, bsmax: int | None = None, realmats: bool = False) -> None:
        """Set the values of various size parameters in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        ip
            Number of integration points.
        bs
            Block size.
        ms
            Moment size.
        npart
            Number of partitions when splitting the communicator.
        bsmax
            Maximum block size.
        realmats
            ``True`` if A and B are real.
    
        Notes
        -----
        The default number of partitions is 1. This means the internal
        `petsc4py.PETSc.KSP` object is shared among all processes of the `PEP`
        communicator. Otherwise, the communicator is split into ``npart``
        communicators, so that ``npart`` `petsc4py.PETSc.KSP` solves proceed
        simultaneously.
    
        See Also
        --------
        getCISSSizes, setCISSThreshold, setCISSRefinement, slepc.PEPCISSSetSizes
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2748 <slepc4py/SLEPc/PEP.pyx#L2748>`
    
        """
        ...
    def getCISSSizes(self) -> tuple[int, int, int, int, int, bool]:
        """Get the values of various size parameters in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        ip: int
            Number of integration points.
        bs: int
            Block size.
        ms: int
            Moment size.
        npart: int
            Number of partitions when splitting the communicator.
        bsmax: int
            Maximum block size.
        realmats: bool
            ``True`` if A and B are real.
    
        See Also
        --------
        setCISSSizes, slepc.PEPCISSGetSizes
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2802 <slepc4py/SLEPc/PEP.pyx#L2802>`
    
        """
        ...
    def setCISSThreshold(self, delta: float | None = None, spur: float | None = None) -> None:
        """Set the values of various threshold parameters in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        delta
            Threshold for numerical rank.
        spur
            Spurious threshold (to discard spurious eigenpairs).
    
        See Also
        --------
        getCISSThreshold, slepc.PEPCISSSetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2836 <slepc4py/SLEPc/PEP.pyx#L2836>`
    
        """
        ...
    def getCISSThreshold(self) -> tuple[float, float]:
        """Get the values of various threshold parameters in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        delta: float
            Threshold for numerical rank.
        spur: float
            Spurious threshold (to discard spurious eigenpairs.
    
        See Also
        --------
        setCISSThreshold, slepc.PEPCISSGetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2859 <slepc4py/SLEPc/PEP.pyx#L2859>`
    
        """
        ...
    def setCISSRefinement(self, inner: int | None = None, blsize: int | None = None) -> None:
        """Set the values of various refinement parameters in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        inner
            Number of iterative refinement iterations (inner loop).
        blsize
            Number of iterative refinement iterations (blocksize loop).
    
        See Also
        --------
        getCISSRefinement, slepc.PEPCISSSetRefinement
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2881 <slepc4py/SLEPc/PEP.pyx#L2881>`
    
        """
        ...
    def getCISSRefinement(self) -> tuple[int, int]:
        """Get the values of various refinement parameters in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        inner: int
            Number of iterative refinement iterations (inner loop).
        blsize: int
            Number of iterative refinement iterations (blocksize loop).
    
        See Also
        --------
        setCISSRefinement, slepc.PEPCISSGetRefinement
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2904 <slepc4py/SLEPc/PEP.pyx#L2904>`
    
        """
        ...
    def getCISSKSPs(self) -> list[KSP]:
        """Get the array of linear solver objects associated with the CISS solver.
    
        Collective.
    
        Returns
        -------
        list of `petsc4py.PETSc.KSP`
            The linear solver objects.
    
        Notes
        -----
        The number of `petsc4py.PETSc.KSP` solvers is equal to the number of
        integration points divided by the number of partitions. This value is
        halved in the case of real matrices with a region centered at the real
        axis.
    
        See Also
        --------
        setCISSSizes, slepc.PEPCISSGetKSPs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2926 <slepc4py/SLEPc/PEP.pyx#L2926>`
    
        """
        ...
    @property
    def problem_type(self) -> PEPProblemType:
        """The type of the eigenvalue problem.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2955 <slepc4py/SLEPc/PEP.pyx#L2955>`
    
        """
        ...
    @property
    def which(self) -> PEPWhich:
        """The portion of the spectrum to be sought.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2962 <slepc4py/SLEPc/PEP.pyx#L2962>`
    
        """
        ...
    @property
    def target(self) -> float:
        """The value of the target.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2969 <slepc4py/SLEPc/PEP.pyx#L2969>`
    
        """
        ...
    @property
    def extract(self) -> PEPExtract:
        """The type of extraction technique to be employed.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2976 <slepc4py/SLEPc/PEP.pyx#L2976>`
    
        """
        ...
    @property
    def tol(self) -> float:
        """The tolerance.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2983 <slepc4py/SLEPc/PEP.pyx#L2983>`
    
        """
        ...
    @property
    def max_it(self) -> int:
        """The maximum iteration count.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2990 <slepc4py/SLEPc/PEP.pyx#L2990>`
    
        """
        ...
    @property
    def track_all(self) -> bool:
        """Compute the residual norm of all approximate eigenpairs.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:2997 <slepc4py/SLEPc/PEP.pyx#L2997>`
    
        """
        ...
    @property
    def st(self) -> ST:
        """The spectral transformation (`ST`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:3004 <slepc4py/SLEPc/PEP.pyx#L3004>`
    
        """
        ...
    @property
    def bv(self) -> BV:
        """The basis vectors (`BV`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:3011 <slepc4py/SLEPc/PEP.pyx#L3011>`
    
        """
        ...
    @property
    def rg(self) -> RG:
        """The region (`RG`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:3018 <slepc4py/SLEPc/PEP.pyx#L3018>`
    
        """
        ...
    @property
    def ds(self) -> DS:
        """The direct solver (`DS`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/PEP.pyx:3025 <slepc4py/SLEPc/PEP.pyx#L3025>`
    
        """
        ...

class NEP(Object):
    """Nonlinear Eigenvalue Problem Solver.
    
    The Nonlinear Eigenvalue Problem (`NEP`) solver is the object provided
    by slepc4py for specifying an eigenvalue problem that is nonlinear with
    respect to the eigenvalue (not the eigenvector). This is intended for
    general nonlinear problems (rather than polynomial eigenproblems)
    described as :math:`T(\lambda) x=0`.
    
    """
    class Type:
        """NEP type.
        
        - `RII`:      Residual inverse iteration.
        - `SLP`:      Successive linear problems.
        - `NARNOLDI`: Nonlinear Arnoldi.
        - `NLEIGS`:   Fully rational Krylov method for nonlinear eigenproblems.
        - `CISS`:     Contour integral spectrum slice.
        - `INTERPOL`: Polynomial interpolation.
        
        See Also
        --------
        slepc.NEPType
        
        """
        RII: str = _def(str, 'RII')  #: Object ``RII`` of type :class:`str`
        SLP: str = _def(str, 'SLP')  #: Object ``SLP`` of type :class:`str`
        NARNOLDI: str = _def(str, 'NARNOLDI')  #: Object ``NARNOLDI`` of type :class:`str`
        NLEIGS: str = _def(str, 'NLEIGS')  #: Object ``NLEIGS`` of type :class:`str`
        CISS: str = _def(str, 'CISS')  #: Object ``CISS`` of type :class:`str`
        INTERPOL: str = _def(str, 'INTERPOL')  #: Object ``INTERPOL`` of type :class:`str`
    class ProblemType:
        """NEP problem type.
        
        - `GENERAL`:  General nonlinear eigenproblem.
        - `RATIONAL`: NEP defined in split form with all :math:`f_i` rational.
        
        See Also
        --------
        slepc.NEPProblemType
        
        """
        GENERAL: int = _def(int, 'GENERAL')  #: Constant ``GENERAL`` of type :class:`int`
        RATIONAL: int = _def(int, 'RATIONAL')  #: Constant ``RATIONAL`` of type :class:`int`
    class ErrorType:
        """NEP error type to assess accuracy of computed solutions.
        
        - `ABSOLUTE`: Absolute error.
        - `RELATIVE`: Relative error.
        - `BACKWARD`: Backward error.
        
        See Also
        --------
        slepc.NEPErrorType
        
        """
        ABSOLUTE: int = _def(int, 'ABSOLUTE')  #: Constant ``ABSOLUTE`` of type :class:`int`
        RELATIVE: int = _def(int, 'RELATIVE')  #: Constant ``RELATIVE`` of type :class:`int`
        BACKWARD: int = _def(int, 'BACKWARD')  #: Constant ``BACKWARD`` of type :class:`int`
    class Which:
        """NEP desired part of spectrum.
        
        - `LARGEST_MAGNITUDE`:  Largest magnitude (default).
        - `SMALLEST_MAGNITUDE`: Smallest magnitude.
        - `LARGEST_REAL`:       Largest real parts.
        - `SMALLEST_REAL`:      Smallest real parts.
        - `LARGEST_IMAGINARY`:  Largest imaginary parts in magnitude.
        - `SMALLEST_IMAGINARY`: Smallest imaginary parts in magnitude.
        - `TARGET_MAGNITUDE`:   Closest to target (in magnitude).
        - `TARGET_REAL`:        Real part closest to target.
        - `TARGET_IMAGINARY`:   Imaginary part closest to target.
        - `ALL`:                All eigenvalues in a region.
        - `USER`:               User defined selection.
        
        See Also
        --------
        slepc.NEPWhich
        
        """
        LARGEST_MAGNITUDE: int = _def(int, 'LARGEST_MAGNITUDE')  #: Constant ``LARGEST_MAGNITUDE`` of type :class:`int`
        SMALLEST_MAGNITUDE: int = _def(int, 'SMALLEST_MAGNITUDE')  #: Constant ``SMALLEST_MAGNITUDE`` of type :class:`int`
        LARGEST_REAL: int = _def(int, 'LARGEST_REAL')  #: Constant ``LARGEST_REAL`` of type :class:`int`
        SMALLEST_REAL: int = _def(int, 'SMALLEST_REAL')  #: Constant ``SMALLEST_REAL`` of type :class:`int`
        LARGEST_IMAGINARY: int = _def(int, 'LARGEST_IMAGINARY')  #: Constant ``LARGEST_IMAGINARY`` of type :class:`int`
        SMALLEST_IMAGINARY: int = _def(int, 'SMALLEST_IMAGINARY')  #: Constant ``SMALLEST_IMAGINARY`` of type :class:`int`
        TARGET_MAGNITUDE: int = _def(int, 'TARGET_MAGNITUDE')  #: Constant ``TARGET_MAGNITUDE`` of type :class:`int`
        TARGET_REAL: int = _def(int, 'TARGET_REAL')  #: Constant ``TARGET_REAL`` of type :class:`int`
        TARGET_IMAGINARY: int = _def(int, 'TARGET_IMAGINARY')  #: Constant ``TARGET_IMAGINARY`` of type :class:`int`
        ALL: int = _def(int, 'ALL')  #: Constant ``ALL`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class ConvergedReason:
        """NEP convergence reasons.
        
        - `CONVERGED_TOL`: All eigenpairs converged to requested tolerance.
        - `CONVERGED_USER`: User-defined convergence criterion satisfied.
        - `DIVERGED_ITS`: Maximum number of iterations exceeded.
        - `DIVERGED_BREAKDOWN`: Solver failed due to breakdown.
        - `DIVERGED_LINEAR_SOLVE`: Inner linear solve failed.
        - `DIVERGED_SUBSPACE_EXHAUSTED`: Run out of space for the basis in an
          unrestarted solver.
        - `CONVERGED_ITERATING`: Iteration not finished yet.
        
        See Also
        --------
        slepc.NEPConvergedReason
        
        """
        CONVERGED_TOL: int = _def(int, 'CONVERGED_TOL')  #: Constant ``CONVERGED_TOL`` of type :class:`int`
        CONVERGED_USER: int = _def(int, 'CONVERGED_USER')  #: Constant ``CONVERGED_USER`` of type :class:`int`
        DIVERGED_ITS: int = _def(int, 'DIVERGED_ITS')  #: Constant ``DIVERGED_ITS`` of type :class:`int`
        DIVERGED_BREAKDOWN: int = _def(int, 'DIVERGED_BREAKDOWN')  #: Constant ``DIVERGED_BREAKDOWN`` of type :class:`int`
        DIVERGED_LINEAR_SOLVE: int = _def(int, 'DIVERGED_LINEAR_SOLVE')  #: Constant ``DIVERGED_LINEAR_SOLVE`` of type :class:`int`
        DIVERGED_SUBSPACE_EXHAUSTED: int = _def(int, 'DIVERGED_SUBSPACE_EXHAUSTED')  #: Constant ``DIVERGED_SUBSPACE_EXHAUSTED`` of type :class:`int`
        CONVERGED_ITERATING: int = _def(int, 'CONVERGED_ITERATING')  #: Constant ``CONVERGED_ITERATING`` of type :class:`int`
        ITERATING: int = _def(int, 'ITERATING')  #: Constant ``ITERATING`` of type :class:`int`
    class Refine:
        """NEP refinement strategy.
        
        - `NONE`:     No refinement.
        - `SIMPLE`:   Refine eigenpairs one by one.
        - `MULTIPLE`: Refine all eigenpairs simultaneously (invariant pair).
        
        See Also
        --------
        slepc.NEPRefine
        
        """
        NONE: int = _def(int, 'NONE')  #: Constant ``NONE`` of type :class:`int`
        SIMPLE: int = _def(int, 'SIMPLE')  #: Constant ``SIMPLE`` of type :class:`int`
        MULTIPLE: int = _def(int, 'MULTIPLE')  #: Constant ``MULTIPLE`` of type :class:`int`
    class RefineScheme:
        """NEP scheme for solving linear systems during iterative refinement.
        
        - `SCHUR`:    Schur complement.
        - `MBE`:      Mixed block elimination.
        - `EXPLICIT`: Build the explicit matrix.
        
        See Also
        --------
        slepc.NEPRefineScheme
        
        """
        SCHUR: int = _def(int, 'SCHUR')  #: Constant ``SCHUR`` of type :class:`int`
        MBE: int = _def(int, 'MBE')  #: Constant ``MBE`` of type :class:`int`
        EXPLICIT: int = _def(int, 'EXPLICIT')  #: Constant ``EXPLICIT`` of type :class:`int`
    class Conv:
        """NEP convergence test.
        
        - `ABS`:  Absolute convergence test.
        - `REL`:  Convergence test relative to the eigenvalue.
        - `NORM`: Convergence test relative to the matrix norms.
        - `USER`: User-defined convergence test.
        
        See Also
        --------
        slepc.NEPConv
        
        """
        ABS: int = _def(int, 'ABS')  #: Constant ``ABS`` of type :class:`int`
        REL: int = _def(int, 'REL')  #: Constant ``REL`` of type :class:`int`
        NORM: int = _def(int, 'NORM')  #: Constant ``NORM`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class Stop:
        """NEP stopping test.
        
        - `BASIC`: Default stopping test.
        - `USER`:  User-defined stopping test.
        
        See Also
        --------
        slepc.NEPStop
        
        """
        BASIC: int = _def(int, 'BASIC')  #: Constant ``BASIC`` of type :class:`int`
        USER: int = _def(int, 'USER')  #: Constant ``USER`` of type :class:`int`
    class CISSExtraction:
        """NEP CISS extraction technique.
        
        - `RITZ`:   Ritz extraction.
        - `HANKEL`: Extraction via Hankel eigenproblem.
        - `CAA`:    Communication-avoiding Arnoldi.
        
        See Also
        --------
        slepc.NEPCISSExtraction
        
        """
        RITZ: int = _def(int, 'RITZ')  #: Constant ``RITZ`` of type :class:`int`
        HANKEL: int = _def(int, 'HANKEL')  #: Constant ``HANKEL`` of type :class:`int`
        CAA: int = _def(int, 'CAA')  #: Constant ``CAA`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the NEP data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.NEPView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:223 <slepc4py/SLEPc/NEP.pyx#L223>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the NEP object.
    
        Collective.
    
        See Also
        --------
        slepc.NEPDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:242 <slepc4py/SLEPc/NEP.pyx#L242>`
    
        """
        ...
    def reset(self) -> None:
        """Reset the NEP object.
    
        Collective.
    
        See Also
        --------
        slepc.NEPReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:256 <slepc4py/SLEPc/NEP.pyx#L256>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the NEP object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator. If not provided, it defaults to all processes.
    
        See Also
        --------
        slepc.NEPCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:268 <slepc4py/SLEPc/NEP.pyx#L268>`
    
        """
        ...
    def setType(self, nep_type: Type | str) -> None:
        """Set the particular solver to be used in the NEP object.
    
        Logically collective.
    
        Parameters
        ----------
        nep_type
            The solver to be used.
    
        Notes
        -----
        The default is `RII`. Normally, it is best to use
        `setFromOptions()` and then set the NEP type from the options
        database rather than by using this routine. Using the options
        database provides the user with maximum flexibility in
        evaluating the different available methods.
    
        See Also
        --------
        getType, slepc.NEPSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:289 <slepc4py/SLEPc/NEP.pyx#L289>`
    
        """
        ...
    def getType(self) -> str:
        """Get the NEP type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The solver currently being used.
    
        See Also
        --------
        setType, slepc.NEPGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:316 <slepc4py/SLEPc/NEP.pyx#L316>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all NEP options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this NEP object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.NEPGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:335 <slepc4py/SLEPc/NEP.pyx#L335>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all NEP options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all NEP option requests.
    
        Notes
        -----
        A hyphen (-) must NOT be given at the beginning of the prefix
        name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        For example, to distinguish between the runtime options for
        two different NEP contexts, one could call::
    
            N1.setOptionsPrefix("nep1_")
            N2.setOptionsPrefix("nep2_")
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.NEPGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:354 <slepc4py/SLEPc/NEP.pyx#L354>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all NEP options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all NEP option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.NEPAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:385 <slepc4py/SLEPc/NEP.pyx#L385>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set NEP options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help`` option.
    
        This routine must be called before `setUp()` if the user is to be
        allowed to set the solver type.
    
        See Also
        --------
        setOptionsPrefix, slepc.NEPSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:404 <slepc4py/SLEPc/NEP.pyx#L404>`
    
        """
        ...
    def getProblemType(self) -> ProblemType:
        """Get the problem type from the `NEP` object.
    
        Not collective.
    
        Returns
        -------
        ProblemType
            The problem type that was previously set.
    
        See Also
        --------
        setProblemType, slepc.NEPGetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:423 <slepc4py/SLEPc/NEP.pyx#L423>`
    
        """
        ...
    def setProblemType(self, problem_type: ProblemType) -> None:
        """Set the type of the eigenvalue problem.
    
        Logically collective.
    
        Parameters
        ----------
        problem_type
            The problem type to be set.
    
        Notes
        -----
        This function is used to provide a hint to the `NEP` solver
        to exploit certain properties of the nonlinear eigenproblem.
        This hint may be used or not, depending on the solver. By
        default, no particular structure is assumed.
    
        See Also
        --------
        getProblemType, slepc.NEPSetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:442 <slepc4py/SLEPc/NEP.pyx#L442>`
    
        """
        ...
    def getWhichEigenpairs(self) -> Which:
        """Get which portion of the spectrum is to be sought.
    
        Not collective.
    
        Returns
        -------
        Which
            The portion of the spectrum to be sought by the solver.
    
        See Also
        --------
        setWhichEigenpairs, slepc.NEPGetWhichEigenpairs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:467 <slepc4py/SLEPc/NEP.pyx#L467>`
    
        """
        ...
    def setWhichEigenpairs(self, which: Which) -> None:
        """Set which portion of the spectrum is to be sought.
    
        Logically collective.
    
        Parameters
        ----------
        which
            The portion of the spectrum to be sought by the solver.
    
        Notes
        -----
        Not all eigensolvers implemented in NEP account for all the
        possible values. Also, some values make sense only for certain
        types of problems. If SLEPc is compiled for real numbers
        `NEP.Which.LARGEST_IMAGINARY` and
        `NEP.Which.SMALLEST_IMAGINARY` use the absolute value of the
        imaginary part for eigenvalue selection.
    
        The target is a scalar value provided with `setTarget()`.
    
        The criterion `NEP.Which.TARGET_IMAGINARY` is available only
        in case PETSc and SLEPc have been built with complex scalars.
    
        `NEP.Which.ALL` is intended for use in the context of the
        `PEP.Type.CISS` solver for computing all eigenvalues in a region.
    
        See Also
        --------
        getWhichEigenpairs, setTarget, slepc.PEPSetWhichEigenpairs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:486 <slepc4py/SLEPc/NEP.pyx#L486>`
    
        """
        ...
    def getTarget(self) -> Scalar:
        """Get the value of the target.
    
        Not collective.
    
        Returns
        -------
        Scalar
            The value of the target.
    
        Notes
        -----
        If the target was not set by the user, then zero is returned.
    
        See Also
        --------
        setTarget, slepc.NEPGetTarget
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:521 <slepc4py/SLEPc/NEP.pyx#L521>`
    
        """
        ...
    def setTarget(self, target: Scalar) -> None:
        """Set the value of the target.
    
        Logically collective.
    
        Parameters
        ----------
        target
            The value of the target.
    
        Notes
        -----
        The target is a scalar value used to determine the portion of
        the spectrum of interest. It is used in combination with
        `setWhichEigenpairs()`.
    
        When PETSc is built with real scalars, it is not possible to
        specify a complex target.
    
        See Also
        --------
        getTarget, setWhichEigenpairs, slepc.NEPSetTarget
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:544 <slepc4py/SLEPc/NEP.pyx#L544>`
    
        """
        ...
    def getTolerances(self) -> tuple[float, int]:
        """Get the tolerance and maximum iteration count.
    
        Not collective.
    
        Get the tolerance and maximum iteration count used by the default
        NEP convergence tests.
    
        Returns
        -------
        tol: float
            The convergence tolerance.
        maxit: int
            The maximum number of iterations.
    
        See Also
        --------
        setTolerances, slepc.NEPGetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:571 <slepc4py/SLEPc/NEP.pyx#L571>`
    
        """
        ...
    def setTolerances(self, tol: float | None = None, maxit: int | None = None) -> None:
        """Set the tolerance and max. iteration count used in convergence tests.
    
        Logically collective.
    
        Parameters
        ----------
        tol
            The convergence tolerance.
        maxit
            The maximum number of iterations.
    
        Notes
        -----
        Use `DETERMINE` for ``max_it`` to assign a reasonably good value,
        which is dependent on the solution method.
    
        See Also
        --------
        getTolerances, slepc.NEPSetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:596 <slepc4py/SLEPc/NEP.pyx#L596>`
    
        """
        ...
    def getConvergenceTest(self) -> Conv:
        """Get the method used to compute the error estimate used in the convergence test.
    
        Not collective.
    
        Returns
        -------
        Conv
            The method used to compute the error estimate
            used in the convergence test.
    
        See Also
        --------
        setConvergenceTest, slepc.NEPGetConvergenceTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:624 <slepc4py/SLEPc/NEP.pyx#L624>`
    
        """
        ...
    def setConvergenceTest(self, conv: Conv) -> None:
        """Set how to compute the error estimate used in the convergence test.
    
        Logically collective.
    
        Parameters
        ----------
        conv
            The method used to compute the error estimate
            used in the convergence test.
    
        See Also
        --------
        getConvergenceTest, slepc.NEPSetConvergenceTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:644 <slepc4py/SLEPc/NEP.pyx#L644>`
    
        """
        ...
    def getRefine(self) -> tuple[Refine, int, float, int, RefineScheme]:
        """Get the refinement strategy used by the NEP object.
    
        Not collective.
    
        Returns
        -------
        ref: Refine
            The refinement type.
        npart: int
            The number of partitions of the communicator.
        tol: float
            The convergence tolerance.
        its: int
            The maximum number of refinement iterations.
        scheme: RefineScheme
            Scheme for solving linear systems.
    
        See Also
        --------
        setRefine, slepc.NEPGetRefine
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:663 <slepc4py/SLEPc/NEP.pyx#L663>`
    
        """
        ...
    def setRefine(self, ref: Refine, npart: int | None = None, tol: float | None = None, its: int | None = None, scheme: RefineScheme | None = None) -> None:
        """Set the refinement strategy used by the NEP object.
    
        Logically collective.
    
        Set the refinement strategy used by the NEP object and the associated
        parameters.
    
        Parameters
        ----------
        ref
            The refinement type.
        npart
            The number of partitions of the communicator.
        tol
            The convergence tolerance.
        its
            The maximum number of refinement iterations.
        scheme
            Scheme for solving linear systems.
    
        See Also
        --------
        getRefine, slepc.NEPSetRefine
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:694 <slepc4py/SLEPc/NEP.pyx#L694>`
    
        """
        ...
    def getRefineKSP(self) -> KSP:
        """Get the ``KSP`` object used by the eigensolver in the refinement phase.
    
        Collective.
    
        Returns
        -------
        `petsc4py.PETSc.KSP`
            The linear solver object.
    
        See Also
        --------
        setRefine, slepc.NEPRefineGetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:738 <slepc4py/SLEPc/NEP.pyx#L738>`
    
        """
        ...
    def getTrackAll(self) -> bool:
        """Get the flag indicating whether all residual norms must be computed.
    
        Not collective.
    
        Returns
        -------
        bool
            Whether the solver computes all residuals or not.
    
        See Also
        --------
        setTrackAll, slepc.NEPGetTrackAll
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:758 <slepc4py/SLEPc/NEP.pyx#L758>`
    
        """
        ...
    def setTrackAll(self, trackall: bool) -> None:
        """Set if the solver must compute the residual of all approximate eigenpairs.
    
        Logically collective.
    
        Parameters
        ----------
        trackall
            Whether to compute all residuals or not.
    
        See Also
        --------
        getTrackAll, slepc.NEPSetTrackAll
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:777 <slepc4py/SLEPc/NEP.pyx#L777>`
    
        """
        ...
    def getDimensions(self) -> tuple[int, int, int]:
        """Get the number of eigenvalues to compute.
    
        Not collective.
    
        Get the number of eigenvalues to compute, and the dimension of the
        subspace.
    
        Returns
        -------
        nev: int
            Number of eigenvalues to compute.
        ncv: int
            Maximum dimension of the subspace to be used by the solver.
        mpd: int
            Maximum dimension allowed for the projected problem.
    
        See Also
        --------
        setDimensions, slepc.NEPGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:795 <slepc4py/SLEPc/NEP.pyx#L795>`
    
        """
        ...
    def setDimensions(self, nev: int | None = None, ncv: int | None = None, mpd: int | None = None) -> None:
        """Set the number of eigenvalues to compute.
    
        Logically collective.
    
        Set the number of eigenvalues to compute and the dimension of the
        subspace.
    
        Parameters
        ----------
        nev
            Number of eigenvalues to compute.
        ncv
            Maximum dimension of the subspace to be used by the solver.
        mpd
            Maximum dimension allowed for the projected problem.
    
        Notes
        -----
        Use `DETERMINE` for ``ncv`` and ``mpd`` to assign a reasonably good
        value, which is dependent on the solution method.
    
        The parameters ``ncv`` and ``mpd`` are intimately related, so that
        the user is advised to set one of them at most. Normal usage
        is the following:
    
        + In cases where ``nev`` is small, the user sets ``ncv``
          (a reasonable default is 2 * ``nev``).
    
        + In cases where ``nev`` is large, the user sets ``mpd``.
    
        The value of ``ncv`` should always be between ``nev`` and (``nev`` +
        ``mpd``), typically ``ncv`` = ``nev`` + ``mpd``. If ``nev`` is not too
        large, ``mpd`` = ``nev`` is a reasonable choice, otherwise a
        smaller value should be used.
    
        See Also
        --------
        getDimensions, slepc.NEPSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:823 <slepc4py/SLEPc/NEP.pyx#L823>`
    
        """
        ...
    def getBV(self) -> BV:
        """Get the basis vectors object associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        BV
            The basis vectors context.
    
        See Also
        --------
        setBV, slepc.NEPGetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:877 <slepc4py/SLEPc/NEP.pyx#L877>`
    
        """
        ...
    def setBV(self, bv: BV) -> None:
        """Set the basis vectors object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        bv
            The basis vectors context.
    
        See Also
        --------
        getBV, slepc.NEPSetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:897 <slepc4py/SLEPc/NEP.pyx#L897>`
    
        """
        ...
    def getRG(self) -> RG:
        """Get the region object associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        RG
            The region context.
    
        See Also
        --------
        setRG, slepc.NEPGetRG
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:914 <slepc4py/SLEPc/NEP.pyx#L914>`
    
        """
        ...
    def setRG(self, rg: RG) -> None:
        """Set a region object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        rg
            The region context.
    
        See Also
        --------
        getRG, slepc.NEPSetRG
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:934 <slepc4py/SLEPc/NEP.pyx#L934>`
    
        """
        ...
    def getDS(self) -> DS:
        """Get the direct solver associated to the eigensolver.
    
        Not collective.
    
        Returns
        -------
        DS
            The direct solver context.
    
        See Also
        --------
        setDS, slepc.NEPGetDS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:951 <slepc4py/SLEPc/NEP.pyx#L951>`
    
        """
        ...
    def setDS(self, ds: DS) -> None:
        """Set a direct solver object associated to the eigensolver.
    
        Collective.
    
        Parameters
        ----------
        ds
            The direct solver context.
    
        See Also
        --------
        getDS, slepc.NEPSetDS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:971 <slepc4py/SLEPc/NEP.pyx#L971>`
    
        """
        ...
    def setInitialSpace(self, space: Vec or list[Vec]) -> None:
        """Set the initial space from which the eigensolver starts to iterate.
    
        Collective.
    
        Parameters
        ----------
        space
            The initial space.
    
        Notes
        -----
        Some solvers start to iterate on a single vector (initial vector).
        In that case, only the first vector is taken into account and the
        other vectors are ignored.
    
        These vectors do not persist from one `solve()` call to the other,
        so the initial space should be set every time.
    
        The vectors do not need to be mutually orthonormal, since they are
        explicitly orthonormalized internally.
    
        Common usage of this function is when the user can provide a rough
        approximation of the wanted eigenspace. Then, convergence may be faster.
    
        See Also
        --------
        setUp, slepc.NEPSetInitialSpace
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:990 <slepc4py/SLEPc/NEP.pyx#L990>`
    
        """
        ...
    def setStoppingTest(self, stopping: NEPStoppingFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set a function to decide when to stop the outer iteration of the eigensolver.
    
        Logically collective.
    
        See Also
        --------
        getStoppingTest, slepc.NEPSetStoppingTestFunction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1029 <slepc4py/SLEPc/NEP.pyx#L1029>`
    
        """
        ...
    def getStoppingTest(self) -> NEPStoppingFunction:
        """Get the stopping test function.
    
        Not collective.
    
        Returns
        -------
        NEPStoppingFunction
            The stopping test function.
    
        See Also
        --------
        setStoppingTest
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1053 <slepc4py/SLEPc/NEP.pyx#L1053>`
    
        """
        ...
    def setEigenvalueComparison(self, comparison: NEPEigenvalueComparison | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set an eigenvalue comparison function.
    
        Logically collective.
    
        Notes
        -----
        This eigenvalue comparison function is used when `setWhichEigenpairs()`
        is set to `NEP.Which.USER`.
    
        See Also
        --------
        getEigenvalueComparison, slepc.NEPSetEigenvalueComparison
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1070 <slepc4py/SLEPc/NEP.pyx#L1070>`
    
        """
        ...
    def getEigenvalueComparison(self) -> NEPEigenvalueComparison:
        """Get the eigenvalue comparison function.
    
        Not collective.
    
        Returns
        -------
        NEPEigenvalueComparison
            The eigenvalue comparison function.
    
        See Also
        --------
        setEigenvalueComparison
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1100 <slepc4py/SLEPc/NEP.pyx#L1100>`
    
        """
        ...
    def setMonitor(self, monitor: NEPMonitorFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Append a monitor function to the list of monitors.
    
        Logically collective.
    
        See Also
        --------
        getMonitor, cancelMonitor, slepc.NEPMonitorSet
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1117 <slepc4py/SLEPc/NEP.pyx#L1117>`
    
        """
        ...
    def getMonitor(self) -> NEPMonitorFunction:
        """Get the list of monitor functions.
    
        Not collective.
    
        Returns
        -------
        NEPMonitorFunction
            The list of monitor functions.
    
        See Also
        --------
        setMonitor
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1142 <slepc4py/SLEPc/NEP.pyx#L1142>`
    
        """
        ...
    def cancelMonitor(self) -> None:
        """Clear all monitors for a `NEP` object.
    
        Logically collective.
    
        See Also
        --------
        slepc.NEPMonitorCancel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1159 <slepc4py/SLEPc/NEP.pyx#L1159>`
    
        """
        ...
    def setUp(self) -> None:
        """Set up all the internal data structures.
    
        Collective.
    
        Notes
        -----
        Sets up all the internal data structures necessary for the execution
        of the eigensolver.
    
        This function need not be called explicitly in most cases,
        since `solve()` calls it. It can be useful when one wants to
        measure the set-up time separately from the solve time.
    
        See Also
        --------
        solve, slepc.NEPSetUp
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1174 <slepc4py/SLEPc/NEP.pyx#L1174>`
    
        """
        ...
    def solve(self) -> None:
        """Solve the nonlinear eigenproblem.
    
        Collective.
    
        Notes
        -----
        `solve()` will return without generating an error regardless of
        whether all requested solutions were computed or not. Call
        `getConverged()` to get the actual number of computed solutions,
        and `getConvergedReason()` to determine if the solver converged
        or failed and why.
    
        See Also
        --------
        setUp, getConverged, getConvergedReason, slepc.NEPSolve
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1195 <slepc4py/SLEPc/NEP.pyx#L1195>`
    
        """
        ...
    def getIterationNumber(self) -> int:
        """Get the current iteration number.
    
        Not collective.
    
        If the call to `solve()` is complete, then it returns the number of
        iterations carried out by the solution method.
    
        Returns
        -------
        int
            Iteration number.
    
        See Also
        --------
        getConvergedReason, setTolerances, slepc.NEPGetIterationNumber
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1215 <slepc4py/SLEPc/NEP.pyx#L1215>`
    
        """
        ...
    def getConvergedReason(self) -> ConvergedReason:
        """Get the reason why the `solve()` iteration was stopped.
    
        Not collective.
    
        Returns
        -------
        ConvergedReason
            Negative value indicates diverged, positive value converged.
    
        See Also
        --------
        setTolerances, solve, slepc.NEPGetConvergedReason
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1237 <slepc4py/SLEPc/NEP.pyx#L1237>`
    
        """
        ...
    def getConverged(self) -> int:
        """Get the number of converged eigenpairs.
    
        Not collective.
    
        Returns
        -------
        nconv: int
            Number of converged eigenpairs.
    
        Notes
        -----
        This function should be called after `solve()` has finished.
    
        The value ``nconv`` may be different from the number of requested
        solutions ``nev``, but not larger than ``ncv``, see `setDimensions()`.
    
        See Also
        --------
        setDimensions, solve, getEigenpair, slepc.NEPGetConverged
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1256 <slepc4py/SLEPc/NEP.pyx#L1256>`
    
        """
        ...
    def getEigenpair(self, i: int, Vr: Vec | None = None, Vi: Vec | None = None) -> None:
        """Get the i-th solution of the eigenproblem as computed by `solve()`.
    
        Collective.
    
        The solution consists of both the eigenvalue and the eigenvector.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
        Vr
            Placeholder for the returned eigenvector (real part).
        Vi
            Placeholder for the returned eigenvector (imaginary part).
    
        Returns
        -------
        complex
            The computed eigenvalue.
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and ``nconv-1`` (see
        `getConverged()`). Eigenpairs are indexed according to the ordering
        criterion established with `setWhichEigenpairs()`.
    
        The eigenvector is normalized to have unit norm.
    
        See Also
        --------
        solve, getConverged, setWhichEigenpairs, slepc.NEPGetEigenpair
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1282 <slepc4py/SLEPc/NEP.pyx#L1282>`
    
        """
        ...
    def getLeftEigenvector(self, i: int, Wr: Vec, Wi: Vec | None = None) -> None:
        """Get the i-th left eigenvector as computed by `solve()`.
    
        Collective.
    
        Parameters
        ----------
        i
            Index of the solution to be obtained.
        Wr
            Placeholder for the returned eigenvector (real part).
        Wi
            Placeholder for the returned eigenvector (imaginary part).
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and
        ``nconv-1`` (see `getConverged()`). Eigensolutions are indexed
        according to the ordering criterion established with
        `setWhichEigenpairs()`.
    
        Left eigenvectors are available only if the ``twosided`` flag was
        set with `setTwoSided()`.
    
        See Also
        --------
        getEigenpair, getConverged, setTwoSided, slepc.NEPGetLeftEigenvector
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1323 <slepc4py/SLEPc/NEP.pyx#L1323>`
    
        """
        ...
    def getErrorEstimate(self, i: int) -> float:
        """Get the error estimate associated to the i-th computed eigenpair.
    
        Not collective.
    
        Parameters
        ----------
        i
            Index of the solution to be considered.
    
        Returns
        -------
        float
            Error estimate.
    
        Notes
        -----
        This is the error estimate used internally by the eigensolver.
        The actual error bound can be computed with `computeError()`.
    
        See Also
        --------
        computeError, slepc.NEPGetErrorEstimate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1356 <slepc4py/SLEPc/NEP.pyx#L1356>`
    
        """
        ...
    def computeError(self, i: int, etype: ErrorType | None = None) -> float:
        """Compute the error associated with the i-th computed eigenpair.
    
        Collective.
    
        Compute the error (based on the residual norm) associated with the
        i-th computed eigenpair.
    
        Parameters
        ----------
        i
            Index of the solution to be considered.
        etype
            The error type to compute.
    
        Returns
        -------
        float
            The error bound, computed in various ways from the residual norm
            :math:`\|T(\lambda)x\|_2` where :math:`\lambda` is the eigenvalue
            and :math:`x` is the eigenvector.
    
        Notes
        -----
        The index ``i`` should be a value between ``0`` and ``nconv-1``
        (see `getConverged()`).
    
        If the computation of left eigenvectors was enabled with `setTwoSided()`,
        then the error will be computed using the maximum of the value above and
        the left residual norm  :math:`\|y^*T(\lambda)\|_2`, where :math:`y`
        is the approximate left eigenvector.
    
        See Also
        --------
        getErrorEstimate, setTwoSided, slepc.NEPComputeError
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1385 <slepc4py/SLEPc/NEP.pyx#L1385>`
    
        """
        ...
    def errorView(self, etype: ErrorType | None = None, viewer: petsc4py.PETSc.Viewer | None = None) -> None:
        """Display the errors associated with the computed solution.
    
        Collective.
    
        Display the errors and the eigenvalues.
    
        Parameters
        ----------
        etype
            The error type to compute.
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        Notes
        -----
        By default, this function checks the error of all eigenpairs and prints
        the eigenvalues if all of them are below the requested tolerance.
        If the viewer has format ``ASCII_INFO_DETAIL`` then a table with
        eigenvalues and corresponding errors is printed.
    
        See Also
        --------
        solve, valuesView, vectorsView, slepc.NEPErrorView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1428 <slepc4py/SLEPc/NEP.pyx#L1428>`
    
        """
        ...
    def valuesView(self, viewer: Viewer | None = None) -> None:
        """Display the computed eigenvalues in a viewer.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        solve, vectorsView, errorView, slepc.NEPValuesView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1460 <slepc4py/SLEPc/NEP.pyx#L1460>`
    
        """
        ...
    def vectorsView(self, viewer: Viewer | None = None) -> None:
        """Output computed eigenvectors to a viewer.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        solve, valuesView, errorView, slepc.NEPVectorsView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1479 <slepc4py/SLEPc/NEP.pyx#L1479>`
    
        """
        ...
    def setFunction(self, function: NEPFunction, F: petsc4py.PETSc.Mat | None = None, P: petsc4py.PETSc.Mat | None = None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set the function to compute the nonlinear Function :math:`T(\lambda)`.
    
        Collective.
    
        Set the function to compute the nonlinear Function :math:`T(\lambda)`
        as well as the location to store the matrix.
    
        Parameters
        ----------
        function
            Function evaluation routine.
        F
            Function matrix.
        P
            Preconditioner matrix (usually the same as ``F``).
    
        See Also
        --------
        setJacobian, getFunction, slepc.NEPSetFunction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1500 <slepc4py/SLEPc/NEP.pyx#L1500>`
    
        """
        ...
    def getFunction(self) -> tuple[petsc4py.PETSc.Mat, petsc4py.PETSc.Mat, NEPFunction]:
        """Get the function to compute the nonlinear Function :math:`T(\lambda)`.
    
        Collective.
    
        Get the function to compute the nonlinear Function :math:`T(\lambda)`
        and the matrix.
    
        Returns
        -------
        F: petsc4py.PETSc.Mat
            Function matrix.
        P: petsc4py.PETSc.Mat
            Preconditioner matrix (usually the same as the F).
        function: NEPFunction
            Function evaluation routine.
    
        See Also
        --------
        setFunction, slepc.NEPGetFunction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1540 <slepc4py/SLEPc/NEP.pyx#L1540>`
    
        """
        ...
    def setJacobian(self, jacobian: NEPJacobian, J: petsc4py.PETSc.Mat | None = None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Set the function to compute the Jacobian :math:`T'(\lambda)`.
    
        Collective.
    
        Set the function to compute the Jacobian :math:`T'(\lambda)` as well as
        the location to store the matrix.
    
        Parameters
        ----------
        jacobian
            Jacobian evaluation routine.
        J
            Jacobian matrix.
    
        See Also
        --------
        setFunction, getJacobian, slepc.NEPSetJacobian
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1570 <slepc4py/SLEPc/NEP.pyx#L1570>`
    
        """
        ...
    def getJacobian(self) -> tuple[petsc4py.PETSc.Mat, NEPJacobian]:
        """Get the function to compute the Jacobian :math:`T'(\lambda)` and J.
    
        Collective.
    
        Get the function to compute the Jacobian :math:`T'(\lambda)` and the
        matrix.
    
        Returns
        -------
        J: petsc4py.PETSc.Mat
            Jacobian matrix.
        jacobian: NEPJacobian
            Jacobian evaluation routine.
    
        See Also
        --------
        setJacobian, slepc.NEPGetJacobian
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1606 <slepc4py/SLEPc/NEP.pyx#L1606>`
    
        """
        ...
    def setSplitOperator(self, A: petsc4py.PETSc.Mat | list[petsc4py.PETSc.Mat], f: FN | list[FN], structure: petsc4py.PETSc.Mat.Structure | None = None) -> None:
        """Set the operator of the nonlinear eigenvalue problem in split form.
    
        Collective.
    
        Parameters
        ----------
        A
            Coefficient matrices of the split form.
        f
            Scalar functions of the split form.
        structure
            Structure flag for matrices.
    
        Notes
        -----
        The nonlinear operator is written as
        :math:`T(\lambda) = \sum_i A_i f_i(\lambda)`, for :math:`i=1,\dots,n`.
        The derivative :math:`T'(\lambda)` can be obtained using the
        derivatives of :math:`f_i`.
    
        The ``structure`` flag provides information about :math:`A_i`'s
        nonzero pattern.
    
        This function must be called before `setUp()`. If it is called
        again after `setUp()` then the `NEP` object is reset.
    
        See Also
        --------
        getSplitOperator, slepc.NEPSetSplitOperator
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1632 <slepc4py/SLEPc/NEP.pyx#L1632>`
    
        """
        ...
    def getSplitOperator(self) -> tuple[list[petsc4py.PETSc.Mat], list[FN], petsc4py.PETSc.Mat.Structure]:
        """Get the operator of the nonlinear eigenvalue problem in split form.
    
        Collective.
    
        Returns
        -------
        A: list of petsc4py.PETSc.Mat
            Coefficient matrices of the split form.
        f: list of FN
            Scalar functions of the split form.
        structure: petsc4py.PETSc.Mat.Structure
            Structure flag for matrices.
    
        See Also
        --------
        setSplitOperator, slepc.NEPGetSplitOperatorInfo, slepc.NEPGetSplitOperatorTerm
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1683 <slepc4py/SLEPc/NEP.pyx#L1683>`
    
        """
        ...
    def setSplitPreconditioner(self, P: petsc4py.PETSc.Mat | list[petsc4py.PETSc.Mat], structure: petsc4py.PETSc.Mat.Structure | None = None) -> None:
        """Set the operator in split form.
    
        Collective.
    
        Set the operator in split form from which to build the preconditioner
        to be used when solving the nonlinear eigenvalue problem in split form.
    
        Parameters
        ----------
        P
            Coefficient matrices of the split preconditioner.
        structure
            Structure flag for matrices.
    
        See Also
        --------
        getSplitPreconditioner, slepc.NEPSetSplitPreconditioner
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1719 <slepc4py/SLEPc/NEP.pyx#L1719>`
    
        """
        ...
    def getSplitPreconditioner(self) -> tuple[list[petsc4py.PETSc.Mat], petsc4py.PETSc.Mat.Structure]:
        """Get the operator of the split preconditioner.
    
        Not collective.
    
        Returns
        -------
        P: list of petsc4py.PETSc.Mat
            Coefficient matrices of the split preconditioner.
        structure: petsc4py.PETSc.Mat.Structure
            Structure flag for matrices.
    
        See Also
        --------
        setSplitPreconditioner, slepc.NEPGetSplitPreconditionerTerm
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1752 <slepc4py/SLEPc/NEP.pyx#L1752>`
    
        """
        ...
    def getTwoSided(self) -> bool:
        """Get the flag indicating if a two-sided variant is being used.
    
        Not collective.
    
        Get the flag indicating whether a two-sided variant of the algorithm
        is being used or not.
    
        Returns
        -------
        bool
            Whether the two-sided variant is to be used or not.
    
        See Also
        --------
        setTwoSided, slepc.NEPGetTwoSided
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1781 <slepc4py/SLEPc/NEP.pyx#L1781>`
    
        """
        ...
    def setTwoSided(self, twosided: bool) -> None:
        """Set the solver to use a two-sided variant.
    
        Logically collective.
    
        Set the solver to use a two-sided variant so that left eigenvectors
        are also computed.
    
        Parameters
        ----------
        twosided
            Whether the two-sided variant is to be used or not.
    
        Notes
        -----
        If the user sets ``twosided`` to ``True`` then the solver uses a
        variant of the algorithm that computes both right and left
        eigenvectors. This is usually much more costly. This option is not
        available in all solvers.
    
        When using two-sided solvers, the problem matrices must have both
        the ``Mat.mult`` and ``Mat.multTranspose`` operations defined.
    
        See Also
        --------
        getTwoSided, getLeftEigenvector, slepc.NEPSetTwoSided
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1803 <slepc4py/SLEPc/NEP.pyx#L1803>`
    
        """
        ...
    def applyResolvent(self, omega: Scalar, v: Vec, r: Vec, rg: RG | None = None) -> None:
        """Apply the resolvent :math:`T^{-1}(z)` to a given vector.
    
        Collective.
    
        Parameters
        ----------
        omega
            Value where the resolvent must be evaluated.
        v
            Input vector.
        r
            Placeholder for the result vector.
        rg
            Region.
    
        Notes
        -----
        The resolvent :math:`T^{-1}(z)=\sum_i(z-\lambda_i)^{-1}x_iy_i^*`
        is evaluated at :math:`z=\omega` and the matrix-vector product
        :math:`r = T^{-1}(\omega) v` is computed. Vectors :math:`x_i,y_i`
        are right and left eigenvectors, respectively, normalized so that
        :math:`y_i^*T'(\lambda_i)x_i=1`. The sum contains only eigenvectors
        that have been previously computed with `solve()`, and if a region
        ``rg`` is given then only those corresponding to eigenvalues inside
        the region are considered.
    
        See Also
        --------
        solve, getLeftEigenvector, slepc.NEPApplyResolvent
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1834 <slepc4py/SLEPc/NEP.pyx#L1834>`
    
        """
        ...
    def setRIILagPreconditioner(self, lag: int) -> None:
        """Set when the preconditioner is rebuilt in the nonlinear solve.
    
        Logically collective.
    
        Parameters
        ----------
        lag
            0 indicates NEVER rebuild, 1 means rebuild every time the Jacobian is
            computed within the nonlinear iteration, 2 means every second time
            the Jacobian is built, etc.
    
        See Also
        --------
        getRIILagPreconditioner, slepc.NEPRIISetLagPreconditioner
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1878 <slepc4py/SLEPc/NEP.pyx#L1878>`
    
        """
        ...
    def getRIILagPreconditioner(self) -> int:
        """Get how often the preconditioner is rebuilt.
    
        Not collective.
    
        Returns
        -------
        int
            The lag parameter.
    
        See Also
        --------
        setRIILagPreconditioner, slepc.NEPRIIGetLagPreconditioner
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1898 <slepc4py/SLEPc/NEP.pyx#L1898>`
    
        """
        ...
    def setRIIConstCorrectionTol(self, cct: bool) -> None:
        """Set a flag to keep the tolerance used in the linear solver constant.
    
        Logically collective.
    
        Parameters
        ----------
        cct
             If ``True``, the `petsc4py.PETSc.KSP` relative tolerance is constant.
    
        Notes
        -----
        By default, an exponentially decreasing tolerance is set in the
        ``KSP`` used within the nonlinear iteration, so that each Newton
        iteration requests better accuracy than the previous one. The
        constant correction tolerance flag stops this behavior.
    
        See Also
        --------
        getRIIConstCorrectionTol, slepc.NEPRIISetConstCorrectionTol
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1917 <slepc4py/SLEPc/NEP.pyx#L1917>`
    
        """
        ...
    def getRIIConstCorrectionTol(self) -> bool:
        """Get the constant tolerance flag.
    
        Not collective.
    
        Returns
        -------
        bool
            If ``True``, the `petsc4py.PETSc.KSP` relative tolerance is
            constant.
    
        See Also
        --------
        setRIIConstCorrectionTol, slepc.NEPRIIGetConstCorrectionTol
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1942 <slepc4py/SLEPc/NEP.pyx#L1942>`
    
        """
        ...
    def setRIIMaximumIterations(self, its: int) -> None:
        """Set the max. number of inner iterations to be used in the RII solver.
    
        Logically collective.
    
        These are the Newton iterations related to the computation of the
        nonlinear Rayleigh functional.
    
        Parameters
        ----------
        its
             Maximum inner iterations.
    
        See Also
        --------
        getRIIMaximumIterations, slepc.NEPRIISetMaximumIterations
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1962 <slepc4py/SLEPc/NEP.pyx#L1962>`
    
        """
        ...
    def getRIIMaximumIterations(self) -> int:
        """Get the maximum number of inner iterations of RII.
    
        Not collective.
    
        Returns
        -------
        int
            Maximum inner iterations.
    
        See Also
        --------
        setRIIMaximumIterations, slepc.NEPRIIGetMaximumIterations
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:1983 <slepc4py/SLEPc/NEP.pyx#L1983>`
    
        """
        ...
    def setRIIHermitian(self, herm: bool) -> None:
        """Set a flag to use the Hermitian version of the solver.
    
        Logically collective.
    
        Set a flag to indicate if the Hermitian version of the scalar
        nonlinear equation must be used by the solver.
    
        Parameters
        ----------
        herm
            If ``True``, the Hermitian version is used.
    
        Notes
        -----
        By default, the scalar nonlinear equation
        :math:`x^*T(\sigma)^{-1}T(z)x=0` is solved at each step of the
        nonlinear iteration. When this flag is set the simpler form
        :math:`x^*T(z)x=0` is used, which is supposed to be valid only
        for Hermitian problems.
    
        See Also
        --------
        getRIIHermitian, slepc.NEPRIISetHermitian
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2002 <slepc4py/SLEPc/NEP.pyx#L2002>`
    
        """
        ...
    def getRIIHermitian(self) -> bool:
        """Get if the Hermitian version must be used by the solver.
    
        Not collective.
    
        Returns
        -------
        bool
            If ``True``, the Hermitian version is used.
    
        See Also
        --------
        setRIIHermitian, slepc.NEPRIIGetHermitian
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2031 <slepc4py/SLEPc/NEP.pyx#L2031>`
    
        """
        ...
    def setRIIDeflationThreshold(self, deftol: float) -> None:
        """Set the threshold used to switch between deflated and non-deflated.
    
        Logically collective.
    
        Set the threshold value used to switch between deflated and
        non-deflated iteration.
    
        Parameters
        ----------
        deftol
            The threshold value.
    
        Notes
        -----
        Normally, the solver iterates on the extended problem in order
        to deflate previously converged eigenpairs. If this threshold
        is set to a nonzero value, then once the residual error is below
        this threshold the solver will continue the iteration without
        deflation. The intention is to be able to improve the current
        eigenpair further, despite having previous eigenpairs with
        somewhat bad precision.
    
        See Also
        --------
        getRIIDeflationThreshold, slepc.NEPRIISetDeflationThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2050 <slepc4py/SLEPc/NEP.pyx#L2050>`
    
        """
        ...
    def getRIIDeflationThreshold(self) -> float:
        """Get the threshold value that controls deflation.
    
        Not collective.
    
        Returns
        -------
        float
            The threshold value.
    
        See Also
        --------
        setRIIDeflationThreshold, slepc.NEPRIIGetDeflationThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2081 <slepc4py/SLEPc/NEP.pyx#L2081>`
    
        """
        ...
    def setRIIKSP(self, ksp: KSP) -> None:
        """Set a linear solver object associated to the nonlinear eigensolver.
    
        Collective.
    
        Parameters
        ----------
        ksp
            The linear solver object.
    
        See Also
        --------
        getRIIKSP, slepc.NEPRIISetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2100 <slepc4py/SLEPc/NEP.pyx#L2100>`
    
        """
        ...
    def getRIIKSP(self) -> KSP:
        """Get the linear solver object associated with the nonlinear eigensolver.
    
        Collective.
    
        Returns
        -------
        petsc4py.PETSc.KSP
            The linear solver object.
    
        See Also
        --------
        setRIIKSP, slepc.NEPRIIGetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2117 <slepc4py/SLEPc/NEP.pyx#L2117>`
    
        """
        ...
    def setSLPDeflationThreshold(self, deftol: float) -> None:
        """Set the threshold used to switch between deflated and non-deflated.
    
        Logically collective.
    
        Parameters
        ----------
        deftol
            The threshold value.
    
        Notes
        -----
        Normally, the solver iterates on the extended problem in order
        to deflate previously converged eigenpairs. If this threshold
        is set to a nonzero value, then once the residual error is below
        this threshold the solver will continue the iteration without
        deflation. The intention is to be able to improve the current
        eigenpair further, despite having previous eigenpairs with
        somewhat bad precision.
    
        See Also
        --------
        getSLPDeflationThreshold, slepc.NEPSLPSetDeflationThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2139 <slepc4py/SLEPc/NEP.pyx#L2139>`
    
        """
        ...
    def getSLPDeflationThreshold(self) -> float:
        """Get the threshold value that controls deflation.
    
        Not collective.
    
        Returns
        -------
        float
            The threshold value.
    
        See Also
        --------
        setSLPDeflationThreshold, slepc.NEPSLPGetDeflationThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2167 <slepc4py/SLEPc/NEP.pyx#L2167>`
    
        """
        ...
    def setSLPEPS(self, eps: EPS) -> None:
        """Set a linear eigensolver object associated to the nonlinear eigensolver.
    
        Collective.
    
        Parameters
        ----------
        eps
            The linear eigensolver.
    
        See Also
        --------
        getSLPEPS, slepc.NEPSLPSetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2186 <slepc4py/SLEPc/NEP.pyx#L2186>`
    
        """
        ...
    def getSLPEPS(self) -> EPS:
        """Get the linear eigensolver object associated with the nonlinear eigensolver.
    
        Collective.
    
        Returns
        -------
        EPS
            The linear eigensolver.
    
        See Also
        --------
        setSLPEPS, slepc.NEPSLPGetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2203 <slepc4py/SLEPc/NEP.pyx#L2203>`
    
        """
        ...
    def setSLPEPSLeft(self, eps: EPS) -> None:
        """Set a linear eigensolver object associated to the nonlinear eigensolver.
    
        Collective.
    
        Used to compute left eigenvectors in the two-sided variant of SLP.
    
        Parameters
        ----------
        eps
            The linear eigensolver.
    
        See Also
        --------
        setTwoSided, setSLPEPS, getSLPEPSLeft, slepc.NEPSLPSetEPSLeft
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2223 <slepc4py/SLEPc/NEP.pyx#L2223>`
    
        """
        ...
    def getSLPEPSLeft(self) -> EPS:
        """Get the left eigensolver.
    
        Collective.
    
        Returns
        -------
        EPS
            The linear eigensolver.
    
        See Also
        --------
        setSLPEPSLeft, slepc.NEPSLPGetEPSLeft
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2242 <slepc4py/SLEPc/NEP.pyx#L2242>`
    
        """
        ...
    def setSLPKSP(self, ksp: KSP) -> None:
        """Set a linear solver object associated to the nonlinear eigensolver.
    
        Collective.
    
        Parameters
        ----------
        ksp
            The linear solver object.
    
        See Also
        --------
        getSLPKSP, slepc.NEPSLPSetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2262 <slepc4py/SLEPc/NEP.pyx#L2262>`
    
        """
        ...
    def getSLPKSP(self) -> KSP:
        """Get the linear solver object associated with the nonlinear eigensolver.
    
        Collective.
    
        Returns
        -------
        petsc4py.PETSc.KSP
            The linear solver object.
    
        See Also
        --------
        setSLPKSP, slepc.NEPSLPGetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2279 <slepc4py/SLEPc/NEP.pyx#L2279>`
    
        """
        ...
    def setNArnoldiKSP(self, ksp: KSP) -> None:
        """Set a linear solver object associated to the nonlinear eigensolver.
    
        Collective.
    
        Parameters
        ----------
        ksp
            The linear solver object.
    
        See Also
        --------
        getNArnoldiKSP, slepc.NEPNArnoldiSetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2301 <slepc4py/SLEPc/NEP.pyx#L2301>`
    
        """
        ...
    def getNArnoldiKSP(self) -> KSP:
        """Get the linear solver object associated with the nonlinear eigensolver.
    
        Collective.
    
        Returns
        -------
        petsc4py.PETSc.KSP
            The linear solver object.
    
        See Also
        --------
        setNArnoldiKSP, slepc.NEPNArnoldiGetKSP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2318 <slepc4py/SLEPc/NEP.pyx#L2318>`
    
        """
        ...
    def setNArnoldiLagPreconditioner(self, lag: int) -> None:
        """Set when the preconditioner is rebuilt in the nonlinear solve.
    
        Logically collective.
    
        Parameters
        ----------
        lag
            0 indicates NEVER rebuild, 1 means rebuild every time the Jacobian is
            computed within the nonlinear iteration, 2 means every second time
            the Jacobian is built, etc.
    
        Notes
        -----
        The default is 1. The preconditioner is ALWAYS built in the first
        iteration of a nonlinear solve.
    
        See Also
        --------
        getNArnoldiLagPreconditioner, slepc.NEPNArnoldiSetLagPreconditioner
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2338 <slepc4py/SLEPc/NEP.pyx#L2338>`
    
        """
        ...
    def getNArnoldiLagPreconditioner(self) -> int:
        """Get how often the preconditioner is rebuilt.
    
        Not collective.
    
        Returns
        -------
        int
            The lag parameter.
    
        See Also
        --------
        setNArnoldiLagPreconditioner, slepc.NEPNArnoldiGetLagPreconditioner
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2363 <slepc4py/SLEPc/NEP.pyx#L2363>`
    
        """
        ...
    def setInterpolPEP(self, pep: PEP) -> None:
        """Set a polynomial eigensolver object associated to the nonlinear eigensolver.
    
        Collective.
    
        Parameters
        ----------
        pep
            The polynomial eigensolver.
    
        See Also
        --------
        getInterpolPEP, slepc.NEPInterpolSetPEP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2384 <slepc4py/SLEPc/NEP.pyx#L2384>`
    
        """
        ...
    def getInterpolPEP(self) -> PEP:
        """Get the associated polynomial eigensolver object.
    
        Collective.
    
        Returns
        -------
        PEP
            The polynomial eigensolver.
    
        See Also
        --------
        setInterpolPEP, slepc.NEPInterpolGetPEP
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2401 <slepc4py/SLEPc/NEP.pyx#L2401>`
    
        """
        ...
    def setInterpolInterpolation(self, tol: float | None = None, deg: int | None = None) -> None:
        """Set the tolerance and maximum degree for the interpolation polynomial.
    
        Collective.
    
        Parameters
        ----------
        tol
            The tolerance to stop computing polynomial coefficients.
        deg
            The maximum degree of interpolation.
    
        See Also
        --------
        getInterpolInterpolation, slepc.NEPInterpolSetInterpolation
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2421 <slepc4py/SLEPc/NEP.pyx#L2421>`
    
        """
        ...
    def getInterpolInterpolation(self) -> tuple[float, int]:
        """Get the tolerance and maximum degree for the interpolation polynomial.
    
        Not collective.
    
        Returns
        -------
        tol: float
            The tolerance to stop computing polynomial coefficients.
        deg: int
            The maximum degree of interpolation.
    
        See Also
        --------
        setInterpolInterpolation, slepc.NEPInterpolGetInterpolation
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2444 <slepc4py/SLEPc/NEP.pyx#L2444>`
    
        """
        ...
    def setNLEIGSRestart(self, keep: float) -> None:
        """Set the restart parameter for the NLEIGS method.
    
        Logically collective.
    
        The proportion of basis vectors that must be kept after restart.
    
        Parameters
        ----------
        keep
            The number of vectors to be kept at restart.
    
        Notes
        -----
        Allowed values are in the range [0.1,0.9]. The default is 0.5.
    
        See Also
        --------
        getNLEIGSRestart, slepc.NEPNLEIGSSetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2468 <slepc4py/SLEPc/NEP.pyx#L2468>`
    
        """
        ...
    def getNLEIGSRestart(self) -> float:
        """Get the restart parameter used in the NLEIGS method.
    
        Not collective.
    
        Returns
        -------
        float
            The number of vectors to be kept at restart.
    
        See Also
        --------
        setNLEIGSRestart, slepc.NEPNLEIGSGetRestart
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2492 <slepc4py/SLEPc/NEP.pyx#L2492>`
    
        """
        ...
    def setNLEIGSLocking(self, lock: bool) -> None:
        """Toggle between locking and non-locking variants of the NLEIGS method.
    
        Logically collective.
    
        Parameters
        ----------
        lock
            ``True`` if the locking variant must be selected.
    
        Notes
        -----
        The default is to lock converged eigenpairs when the method restarts.
        This behavior can be changed so that all directions are kept in the
        working subspace even if already converged to working accuracy (the
        non-locking variant).
    
        See Also
        --------
        getNLEIGSLocking, slepc.NEPNLEIGSSetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2511 <slepc4py/SLEPc/NEP.pyx#L2511>`
    
        """
        ...
    def getNLEIGSLocking(self) -> bool:
        """Get the locking flag used in the NLEIGS method.
    
        Not collective.
    
        Returns
        -------
        bool
            The locking flag.
    
        See Also
        --------
        setNLEIGSLocking, slepc.NEPNLEIGSGetLocking
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2536 <slepc4py/SLEPc/NEP.pyx#L2536>`
    
        """
        ...
    def setNLEIGSInterpolation(self, tol: float | None = None, deg: int | None = None) -> None:
        """Set the tolerance and maximum degree for the interpolation polynomial.
    
        Collective.
    
        Set the tolerance and maximum degree when building the interpolation
        via divided differences.
    
        Parameters
        ----------
        tol
            The tolerance to stop computing divided differences.
        deg
            The maximum degree of interpolation.
    
        See Also
        --------
        getNLEIGSInterpolation, slepc.NEPNLEIGSSetInterpolation
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2555 <slepc4py/SLEPc/NEP.pyx#L2555>`
    
        """
        ...
    def getNLEIGSInterpolation(self) -> tuple[float, int]:
        """Get the tolerance and maximum degree for the interpolation polynomial.
    
        Not collective.
    
        Get the tolerance and maximum degree when building the interpolation
        via divided differences.
    
        Returns
        -------
        tol: float
            The tolerance to stop computing divided differences.
        deg: int
            The maximum degree of interpolation.
    
        See Also
        --------
        setNLEIGSInterpolation, slepc.NEPNLEIGSGetInterpolation
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2581 <slepc4py/SLEPc/NEP.pyx#L2581>`
    
        """
        ...
    def setNLEIGSFullBasis(self, fullbasis: bool = True) -> None:
        """Set TOAR-basis (default) or full-basis variants of the NLEIGS method.
    
        Logically collective.
    
        Toggle between TOAR-basis (default) and full-basis variants of the
        NLEIGS method.
    
        Parameters
        ----------
        fullbasis
            ``True`` if the full-basis variant must be selected.
    
        Notes
        -----
        The default is to use a compact representation of the Krylov basis,
        that is, :math:`V = (I \otimes U) S`, with a `BV` of type `TENSOR`.
        This behavior can be changed so that the full basis :math:`V` is
        explicitly stored and operated with. This variant is more expensive
        in terms of memory and computation, but is necessary in some cases,
        particularly for two-sided computations, see `setTwoSided()`.
    
        In the full-basis variant, the NLEIGS solver uses an `EPS` object to
        explicitly solve the linearized eigenproblem, see `getNLEIGSEPS()`.
    
        See Also
        --------
        setTwoSided, getNLEIGSFullBasis, getNLEIGSEPS, slepc.NEPNLEIGSSetFullBasis
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2606 <slepc4py/SLEPc/NEP.pyx#L2606>`
    
        """
        ...
    def getNLEIGSFullBasis(self) -> bool:
        """Get the flag that indicates if NLEIGS is using the full-basis variant.
    
        Not collective.
    
        Returns
        -------
        bool
            ``True`` if the full-basis variant is selected.
    
        See Also
        --------
        setNLEIGSFullBasis, slepc.NEPNLEIGSGetFullBasis
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2639 <slepc4py/SLEPc/NEP.pyx#L2639>`
    
        """
        ...
    def setNLEIGSEPS(self, eps: EPS) -> None:
        """Set a linear eigensolver object associated to the nonlinear eigensolver.
    
        Collective.
    
        Parameters
        ----------
        eps
            The linear eigensolver.
    
        See Also
        --------
        getNLEIGSEPS, slepc.NEPNLEIGSSetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2658 <slepc4py/SLEPc/NEP.pyx#L2658>`
    
        """
        ...
    def getNLEIGSEPS(self) -> EPS:
        """Get the linear eigensolver object associated with the nonlinear eigensolver.
    
        Collective.
    
        Returns
        -------
        EPS
            The linear eigensolver.
    
        See Also
        --------
        setNLEIGSEPS, slepc.NEPNLEIGSGetEPS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2675 <slepc4py/SLEPc/NEP.pyx#L2675>`
    
        """
        ...
    def setNLEIGSRKShifts(self, shifts: Sequence[Scalar]) -> None:
        """Set a list of shifts to be used in the Rational Krylov method.
    
        Collective.
    
        Parameters
        ----------
        shifts
            Values specifying the shifts.
    
        Notes
        -----
        If only one shift is provided, the built subspace is equivalent
        to shift-and-invert Krylov-Schur (provided that the absolute
        convergence criterion is used). Otherwise, the rational Krylov
        variant is run.
    
        See Also
        --------
        getNLEIGSRKShifts, getNLEIGSKSPs, slepc.NEPNLEIGSSetRKShifts
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2695 <slepc4py/SLEPc/NEP.pyx#L2695>`
    
        """
        ...
    def getNLEIGSRKShifts(self) -> ArrayScalar:
        """Get the list of shifts used in the Rational Krylov method.
    
        Not collective.
    
        Returns
        -------
        ArrayScalar
            The shift values.
    
        See Also
        --------
        setNLEIGSRKShifts, slepc.NEPNLEIGSGetRKShifts
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2722 <slepc4py/SLEPc/NEP.pyx#L2722>`
    
        """
        ...
    def getNLEIGSKSPs(self) -> list[KSP]:
        """Get the list of linear solver objects associated with the NLEIGS solver.
    
        Collective.
    
        Returns
        -------
        list of `petsc4py.PETSc.KSP`
            The linear solver objects.
    
        Notes
        -----
        The number of `petsc4py.PETSc.KSP` solvers is equal to the number of
        shifts provided by the user, or 1 if the user did not provide shifts.
    
        See Also
        --------
        setNLEIGSRKShifts, slepc.NEPNLEIGSGetKSPs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2747 <slepc4py/SLEPc/NEP.pyx#L2747>`
    
        """
        ...
    def setCISSExtraction(self, extraction: CISSExtraction) -> None:
        """Set the extraction technique used in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        extraction
            The extraction technique.
    
        See Also
        --------
        getCISSExtraction, slepc.NEPCISSSetExtraction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2774 <slepc4py/SLEPc/NEP.pyx#L2774>`
    
        """
        ...
    def getCISSExtraction(self) -> CISSExtraction:
        """Get the extraction technique used in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        CISSExtraction
            The extraction technique.
    
        See Also
        --------
        setCISSExtraction, slepc.NEPCISSGetExtraction
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2792 <slepc4py/SLEPc/NEP.pyx#L2792>`
    
        """
        ...
    def setCISSSizes(self, ip: int | None = None, bs: int | None = None, ms: int | None = None, npart: int | None = None, bsmax: int | None = None, realmats: bool = False) -> None:
        """Set the values of various size parameters in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        ip
            Number of integration points.
        bs
            Block size.
        ms
            Moment size.
        npart
            Number of partitions when splitting the communicator.
        bsmax
            Maximum block size.
        realmats
            ``True`` if A and B are real.
    
        Notes
        -----
        The default number of partitions is 1. This means the internal
        `petsc4py.PETSc.KSP` object is shared among all processes of the `NEP`
        communicator. Otherwise, the communicator is split into ``npart``
        communicators, so that ``npart`` `petsc4py.PETSc.KSP` solves proceed
        simultaneously.
    
        See Also
        --------
        getCISSSizes, setCISSThreshold, setCISSRefinement, slepc.NEPCISSSetSizes
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2811 <slepc4py/SLEPc/NEP.pyx#L2811>`
    
        """
        ...
    def getCISSSizes(self) -> tuple[int, int, int, int, int, bool]:
        """Get the values of various size parameters in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        ip: int
            Number of integration points.
        bs: int
            Block size.
        ms: int
            Moment size.
        npart: int
            Number of partitions when splitting the communicator.
        bsmax: int
            Maximum block size.
        realmats: bool
            ``True`` if A and B are real.
    
        See Also
        --------
        setCISSSizes, slepc.NEPCISSGetSizes
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2865 <slepc4py/SLEPc/NEP.pyx#L2865>`
    
        """
        ...
    def setCISSThreshold(self, delta: float | None = None, spur: float | None = None) -> None:
        """Set the values of various threshold parameters in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        delta
            Threshold for numerical rank.
        spur
            Spurious threshold (to discard spurious eigenpairs).
    
        See Also
        --------
        getCISSThreshold, slepc.NEPCISSSetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2899 <slepc4py/SLEPc/NEP.pyx#L2899>`
    
        """
        ...
    def getCISSThreshold(self) -> tuple[float, float]:
        """Get the values of various threshold parameters in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        delta: float
            Threshold for numerical rank.
        spur: float
            Spurious threshold (to discard spurious eigenpairs.
    
        See Also
        --------
        setCISSThreshold, slepc.NEPCISSGetThreshold
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2922 <slepc4py/SLEPc/NEP.pyx#L2922>`
    
        """
        ...
    def setCISSRefinement(self, inner: int | None = None, blsize: int | None = None) -> None:
        """Set the values of various refinement parameters in the CISS solver.
    
        Logically collective.
    
        Parameters
        ----------
        inner
            Number of iterative refinement iterations (inner loop).
        blsize
            Number of iterative refinement iterations (blocksize loop).
    
        See Also
        --------
        getCISSRefinement, slepc.NEPCISSSetRefinement
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2944 <slepc4py/SLEPc/NEP.pyx#L2944>`
    
        """
        ...
    def getCISSRefinement(self) -> tuple[int, int]:
        """Get the values of various refinement parameters in the CISS solver.
    
        Not collective.
    
        Returns
        -------
        inner: int
            Number of iterative refinement iterations (inner loop).
        blsize: int
            Number of iterative refinement iterations (blocksize loop).
    
        See Also
        --------
        setCISSRefinement, slepc.NEPCISSGetRefinement
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2967 <slepc4py/SLEPc/NEP.pyx#L2967>`
    
        """
        ...
    def getCISSKSPs(self) -> list[KSP]:
        """Get the list of linear solver objects associated with the CISS solver.
    
        Collective.
    
        Returns
        -------
        list of `petsc4py.PETSc.KSP`
            The linear solver objects.
    
        Notes
        -----
        The number of `petsc4py.PETSc.KSP` solvers is equal to the number of
        integration points divided by the number of partitions. This value is
        halved in the case of real matrices with a region centered at the real
        axis.
    
        See Also
        --------
        setCISSSizes, slepc.NEPCISSGetKSPs
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:2989 <slepc4py/SLEPc/NEP.pyx#L2989>`
    
        """
        ...
    @property
    def problem_type(self) -> NEPProblemType:
        """The problem type from the NEP object.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:3016 <slepc4py/SLEPc/NEP.pyx#L3016>`
    
        """
        ...
    @property
    def which(self) -> NEPWhich:
        """The portion of the spectrum to be sought.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:3023 <slepc4py/SLEPc/NEP.pyx#L3023>`
    
        """
        ...
    @property
    def target(self) -> float:
        """The value of the target.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:3030 <slepc4py/SLEPc/NEP.pyx#L3030>`
    
        """
        ...
    @property
    def tol(self) -> float:
        """The tolerance used by the NEP convergence tests.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:3037 <slepc4py/SLEPc/NEP.pyx#L3037>`
    
        """
        ...
    @property
    def max_it(self) -> int:
        """The maximum iteration count used by the NEP convergence tests.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:3044 <slepc4py/SLEPc/NEP.pyx#L3044>`
    
        """
        ...
    @property
    def track_all(self) -> bool:
        """Compute the residual of all approximate eigenpairs.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:3051 <slepc4py/SLEPc/NEP.pyx#L3051>`
    
        """
        ...
    @property
    def bv(self) -> BV:
        """The basis vectors (`BV`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:3058 <slepc4py/SLEPc/NEP.pyx#L3058>`
    
        """
        ...
    @property
    def rg(self) -> RG:
        """The region (`RG`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:3065 <slepc4py/SLEPc/NEP.pyx#L3065>`
    
        """
        ...
    @property
    def ds(self) -> DS:
        """The direct solver (`DS`) object associated.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/NEP.pyx:3072 <slepc4py/SLEPc/NEP.pyx#L3072>`
    
        """
        ...

class MFN(Object):
    """Matrix Function.
    
    Matrix Function (`MFN`) is the object provided by slepc4py for computing
    the action of a matrix function on a vector. Given a matrix :math:`A` and
    a vector :math:`b`, the call ``mfn.solve(b,x)`` computes
    :math:`x=f(A)b`, where :math:`f` is a function such as the exponential.
    
    """
    class Type:
        """MFN type.
        
        - `KRYLOV`:  Restarted Krylov solver.
        - `EXPOKIT`: Implementation of the method in Expokit.
        
        See Also
        --------
        slepc.MFNType
        
        """
        KRYLOV: str = _def(str, 'KRYLOV')  #: Object ``KRYLOV`` of type :class:`str`
        EXPOKIT: str = _def(str, 'EXPOKIT')  #: Object ``EXPOKIT`` of type :class:`str`
    class ConvergedReason:
        """MFN convergence reasons.
        
        - `CONVERGED_TOL`: All eigenpairs converged to requested tolerance.
        - `CONVERGED_ITS`: Solver completed the requested number of steps.
        - `DIVERGED_ITS`: Maximum number of iterations exceeded.
        - `DIVERGED_BREAKDOWN`: Generic breakdown in method.
        
        See Also
        --------
        slepc.MFNConvergedReason
        
        """
        CONVERGED_TOL: int = _def(int, 'CONVERGED_TOL')  #: Constant ``CONVERGED_TOL`` of type :class:`int`
        CONVERGED_ITS: int = _def(int, 'CONVERGED_ITS')  #: Constant ``CONVERGED_ITS`` of type :class:`int`
        DIVERGED_ITS: int = _def(int, 'DIVERGED_ITS')  #: Constant ``DIVERGED_ITS`` of type :class:`int`
        DIVERGED_BREAKDOWN: int = _def(int, 'DIVERGED_BREAKDOWN')  #: Constant ``DIVERGED_BREAKDOWN`` of type :class:`int`
        CONVERGED_ITERATING: int = _def(int, 'CONVERGED_ITERATING')  #: Constant ``CONVERGED_ITERATING`` of type :class:`int`
        ITERATING: int = _def(int, 'ITERATING')  #: Constant ``ITERATING`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the MFN data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.MFNView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:57 <slepc4py/SLEPc/MFN.pyx#L57>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the MFN object.
    
        Logically collective.
    
        See Also
        --------
        slepc.MFNDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:76 <slepc4py/SLEPc/MFN.pyx#L76>`
    
        """
        ...
    def reset(self) -> None:
        """Reset the MFN object.
    
        Collective.
    
        See Also
        --------
        slepc.MFNReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:90 <slepc4py/SLEPc/MFN.pyx#L90>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the MFN object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator. If not provided, it defaults to all processes.
    
        See Also
        --------
        slepc.MFNCreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:102 <slepc4py/SLEPc/MFN.pyx#L102>`
    
        """
        ...
    def setType(self, mfn_type: Type | str) -> None:
        """Set the particular solver to be used in the MFN object.
    
        Logically collective.
    
        Parameters
        ----------
        mfn_type
            The solver to be used.
    
        Notes
        -----
        The default is ``KRYLOV``. Normally, it is best to use
        `setFromOptions()` and then set the MFN type from the options
        database rather than by using this routine. Using the options
        database provides the user with maximum flexibility in
        evaluating the different available methods.
    
        See Also
        --------
        getType, slepc.MFNSetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:123 <slepc4py/SLEPc/MFN.pyx#L123>`
    
        """
        ...
    def getType(self) -> str:
        """Get the MFN type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The solver currently being used.
    
        See Also
        --------
        setType, slepc.MFNGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:150 <slepc4py/SLEPc/MFN.pyx#L150>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all MFN options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this MFN object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.MFNGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:169 <slepc4py/SLEPc/MFN.pyx#L169>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all MFN options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all MFN option requests.
    
        Notes
        -----
        A hyphen (-) must NOT be given at the beginning of the prefix
        name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        For example, to distinguish between the runtime options for
        two different MFN contexts, one could call::
    
            M1.setOptionsPrefix("mfn1_")
            M2.setOptionsPrefix("mfn2_")
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.MFNGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:188 <slepc4py/SLEPc/MFN.pyx#L188>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching for all MFN options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all MFN option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.MFNAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:219 <slepc4py/SLEPc/MFN.pyx#L219>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set MFN options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help`` option.
    
        This routine must be called before `setUp()` if the user is to be
        allowed to set the solver type.
    
        See Also
        --------
        setOptionsPrefix, slepc.MFNSetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:238 <slepc4py/SLEPc/MFN.pyx#L238>`
    
        """
        ...
    def getTolerances(self) -> tuple[float, int]:
        """Get the tolerance and maximum iteration count.
    
        Not collective.
    
        Returns
        -------
        tol: float
            The convergence tolerance.
        max_it: int
            The maximum number of iterations.
    
        See Also
        --------
        setTolerances, slepc.MFNGetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:257 <slepc4py/SLEPc/MFN.pyx#L257>`
    
        """
        ...
    def setTolerances(self, tol: float | None = None, max_it: int | None = None) -> None:
        """Set the tolerance and maximum iteration count.
    
        Logically collective.
    
        Set the tolerance and maximum iteration count used by the
        default MFN convergence tests.
    
        Parameters
        ----------
        tol
            The convergence tolerance.
        max_it
            The maximum number of iterations.
    
        See Also
        --------
        getTolerances, slepc.MFNSetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:279 <slepc4py/SLEPc/MFN.pyx#L279>`
    
        """
        ...
    def getDimensions(self) -> int:
        """Get the dimension of the subspace used by the solver.
    
        Not collective.
    
        Returns
        -------
        int
            Maximum dimension of the subspace to be used by the solver.
    
        See Also
        --------
        setDimensions, slepc.MFNGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:305 <slepc4py/SLEPc/MFN.pyx#L305>`
    
        """
        ...
    def setDimensions(self, ncv: int) -> None:
        """Set the dimension of the subspace to be used by the solver.
    
        Logically collective.
    
        Parameters
        ----------
        ncv
            Maximum dimension of the subspace to be used by the solver.
    
        See Also
        --------
        getDimensions, slepc.MFNSetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:324 <slepc4py/SLEPc/MFN.pyx#L324>`
    
        """
        ...
    def getFN(self) -> FN:
        """Get the math function object associated to the MFN object.
    
        Not collective.
    
        Returns
        -------
        FN
            The math function context.
    
        See Also
        --------
        setFN, slepc.MFNGetFN
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:342 <slepc4py/SLEPc/MFN.pyx#L342>`
    
        """
        ...
    def setFN(self, fn: FN) -> None:
        """Set a math function object associated to the MFN object.
    
        Collective.
    
        Parameters
        ----------
        fn
            The math function context.
    
        See Also
        --------
        getFN, slepc.MFNSetFN
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:362 <slepc4py/SLEPc/MFN.pyx#L362>`
    
        """
        ...
    def getBV(self) -> BV:
        """Get the basis vector object associated to the MFN object.
    
        Not collective.
    
        Returns
        -------
        BV
            The basis vectors context.
    
        See Also
        --------
        setBV, slepc.MFNGetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:379 <slepc4py/SLEPc/MFN.pyx#L379>`
    
        """
        ...
    def setBV(self, bv: BV) -> None:
        """Set a basis vector object associated to the MFN object.
    
        Collective.
    
        Parameters
        ----------
        bv
            The basis vectors context.
    
        See Also
        --------
        getBV, slepc.MFNSetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:399 <slepc4py/SLEPc/MFN.pyx#L399>`
    
        """
        ...
    def getOperator(self) -> Mat:
        """Get the matrix associated with the MFN object.
    
        Collective.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            The matrix for which the matrix function is to be computed.
    
        See Also
        --------
        setOperator, slepc.MFNGetOperator
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:416 <slepc4py/SLEPc/MFN.pyx#L416>`
    
        """
        ...
    def setOperator(self, A: Mat) -> None:
        """Set the matrix associated with the MFN object.
    
        Collective.
    
        Parameters
        ----------
        A
            The problem matrix.
    
        Notes
        -----
        This must be called before `setUp()`. If called again after
        `setUp()` then the `MFN` object is reset.
    
        See Also
        --------
        getOperator, slepc.MFNSetOperator
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:436 <slepc4py/SLEPc/MFN.pyx#L436>`
    
        """
        ...
    def setMonitor(self, monitor: MFNMonitorFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Append a monitor function to the list of monitors.
    
        Logically collective.
    
        See Also
        --------
        getMonitor, cancelMonitor, slepc.MFNMonitorSet
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:460 <slepc4py/SLEPc/MFN.pyx#L460>`
    
        """
        ...
    def getMonitor(self) -> MFNMonitorFunction:
        """Get the list of monitor functions.
    
        Not collective.
    
        Returns
        -------
        MFNMonitorFunction
            The list of monitor functions.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:485 <slepc4py/SLEPc/MFN.pyx#L485>`
    
        """
        ...
    def cancelMonitor(self) -> None:
        """Clear all monitors for an `MFN` object.
    
        Logically collective.
    
        See Also
        --------
        slepc.MFNMonitorCancel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:498 <slepc4py/SLEPc/MFN.pyx#L498>`
    
        """
        ...
    def setUp(self) -> None:
        """Set up all the necessary internal data structures.
    
        Collective.
    
        Set up all the internal data structures necessary for the execution
        of the eigensolver.
    
        See Also
        --------
        solve, slepc.MFNSetUp
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:513 <slepc4py/SLEPc/MFN.pyx#L513>`
    
        """
        ...
    def solve(self, b: Vec, x: Vec) -> None:
        """Solve the matrix function problem.
    
        Collective.
    
        Given a vector :math:`b`, the vector :math:`x = f(A) b` is
        returned.
    
        Parameters
        ----------
        b
            The right hand side vector.
        x
            The solution.
    
        Notes
        -----
        The matrix :math:`A` is specified with `setOperator()`. The function
        :math:`f` is specified via the `FN` object obtained with `getFN()`
        or set with `setFN()`.
    
        See Also
        --------
        setOperator, getFN, solveTranspose, slepc.MFNSolve
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:528 <slepc4py/SLEPc/MFN.pyx#L528>`
    
        """
        ...
    def solveTranspose(self, b: Vec, x: Vec) -> None:
        """Solve the transpose matrix function problem.
    
        Collective.
    
        Given a vector :math:`b`, the vector :math:`x = f(A^T) b` is
        returned.
    
        Parameters
        ----------
        b
            The right hand side vector.
        x
            The solution.
    
        Notes
        -----
        The matrix :math:`A` is specified with `setOperator()`. The function
        :math:`f` is specified via the `FN` object obtained with `getFN()`
        or set with `setFN()`.
    
        See Also
        --------
        setOperator, getFN, solve, slepc.MFNSolveTranspose
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:556 <slepc4py/SLEPc/MFN.pyx#L556>`
    
        """
        ...
    def getIterationNumber(self) -> int:
        """Get the current iteration number.
    
        Not collective.
    
        Get the current iteration number. If the call to `solve()` is
        complete, then it returns the number of iterations carried out
        by the solution method.
    
        Returns
        -------
        int
            Iteration number.
    
        See Also
        --------
        getConvergedReason, slepc.MFNGetIterationNumber
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:584 <slepc4py/SLEPc/MFN.pyx#L584>`
    
        """
        ...
    def getConvergedReason(self) -> ConvergedReason:
        """Get the reason why the `solve()` iteration was stopped.
    
        Not collective.
    
        Returns
        -------
        ConvergedReason
            Negative value indicates diverged, positive value converged.
    
        See Also
        --------
        setTolerances, solve, setErrorIfNotConverged, slepc.MFNGetConvergedReason
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:607 <slepc4py/SLEPc/MFN.pyx#L607>`
    
        """
        ...
    def setErrorIfNotConverged(self, flg: bool = True) -> None:
        """Set `solve()` to generate an error if the solver does not converge.
    
        Logically collective.
    
        Parameters
        ----------
        flg
            ``True`` indicates you want the error generated.
    
        Notes
        -----
        Normally SLEPc continues if the solver fails to converge, you can
        call `getConvergedReason()` after a `solve()` to determine if it
        has converged.
    
        See Also
        --------
        getConvergedReason, solve, slepc.MFNSetErrorIfNotConverged
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:626 <slepc4py/SLEPc/MFN.pyx#L626>`
    
        """
        ...
    def getErrorIfNotConverged(self) -> bool:
        """Get if `solve()` generates an error if the solver does not converge.
    
        Not collective.
    
        Get a flag indicating whether `solve()` will generate an error if the
        solver does not converge.
    
        Returns
        -------
        bool
            ``True`` indicates you want the error generated.
    
        See Also
        --------
        setErrorIfNotConverged, slepc.MFNGetErrorIfNotConverged
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:650 <slepc4py/SLEPc/MFN.pyx#L650>`
    
        """
        ...
    @property
    def tol(self) -> float:
        """The tolerance count used by the MFN convergence tests.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:674 <slepc4py/SLEPc/MFN.pyx#L674>`
    
        """
        ...
    @property
    def max_it(self) -> int:
        """The maximum iteration count used by the MFN convergence tests.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:681 <slepc4py/SLEPc/MFN.pyx#L681>`
    
        """
        ...
    @property
    def fn(self) -> FN:
        """The math function (`FN`) object associated to the MFN object.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:688 <slepc4py/SLEPc/MFN.pyx#L688>`
    
        """
        ...
    @property
    def bv(self) -> BV:
        """The basis vectors (`BV`) object associated to the MFN object.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/MFN.pyx:695 <slepc4py/SLEPc/MFN.pyx#L695>`
    
        """
        ...

class LME(Object):
    """Linear Matrix Equation.
    
    Linear Matrix Equation (`LME`) is the object provided by slepc4py for
    solving linear matrix equations such as Lyapunov or Sylvester where
    the solution has low rank.
    
    """
    class Type:
        """LME type.
        
        - `KRYLOV`:  Restarted Krylov solver.
        
        See Also
        --------
        slepc.LMEType
        
        """
        KRYLOV: str = _def(str, 'KRYLOV')  #: Object ``KRYLOV`` of type :class:`str`
    class ConvergedReason:
        """LME convergence reasons.
        
        - `CONVERGED_TOL`:       All eigenpairs converged to requested tolerance.
        - `DIVERGED_ITS`:        Maximum number of iterations exceeded.
        - `DIVERGED_BREAKDOWN`:  Solver failed due to breakdown.
        - `CONVERGED_ITERATING`: Iteration not finished yet.
        
        See Also
        --------
        slepc.LMEConvergedReason
        
        """
        CONVERGED_TOL: int = _def(int, 'CONVERGED_TOL')  #: Constant ``CONVERGED_TOL`` of type :class:`int`
        DIVERGED_ITS: int = _def(int, 'DIVERGED_ITS')  #: Constant ``DIVERGED_ITS`` of type :class:`int`
        DIVERGED_BREAKDOWN: int = _def(int, 'DIVERGED_BREAKDOWN')  #: Constant ``DIVERGED_BREAKDOWN`` of type :class:`int`
        CONVERGED_ITERATING: int = _def(int, 'CONVERGED_ITERATING')  #: Constant ``CONVERGED_ITERATING`` of type :class:`int`
        ITERATING: int = _def(int, 'ITERATING')  #: Constant ``ITERATING`` of type :class:`int`
    class ProblemType:
        """LME problem type.
        
        - `LYAPUNOV`:      Continuous-time Lyapunov.
        - `SYLVESTER`:     Continuous-time Sylvester.
        - `GEN_LYAPUNOV`:  Generalized Lyapunov.
        - `GEN_SYLVESTER`: Generalized Sylvester.
        - `DT_LYAPUNOV`:   Discrete-time Lyapunov.
        - `STEIN`:         Stein.
        
        See Also
        --------
        slepc.LMEProblemType
        
        """
        LYAPUNOV: int = _def(int, 'LYAPUNOV')  #: Constant ``LYAPUNOV`` of type :class:`int`
        SYLVESTER: int = _def(int, 'SYLVESTER')  #: Constant ``SYLVESTER`` of type :class:`int`
        GEN_LYAPUNOV: int = _def(int, 'GEN_LYAPUNOV')  #: Constant ``GEN_LYAPUNOV`` of type :class:`int`
        GEN_SYLVESTER: int = _def(int, 'GEN_SYLVESTER')  #: Constant ``GEN_SYLVESTER`` of type :class:`int`
        DT_LYAPUNOV: int = _def(int, 'DT_LYAPUNOV')  #: Constant ``DT_LYAPUNOV`` of type :class:`int`
        STEIN: int = _def(int, 'STEIN')  #: Constant ``STEIN`` of type :class:`int`
    def view(self, viewer: Viewer | None = None) -> None:
        """Print the LME data structure.
    
        Collective.
    
        Parameters
        ----------
        viewer
            Visualization context; if not provided, the standard
            output is used.
    
        See Also
        --------
        slepc.LMEView
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:76 <slepc4py/SLEPc/LME.pyx#L76>`
    
        """
        ...
    def destroy(self) -> Self:
        """Destroy the LME object.
    
        Collective.
    
        See Also
        --------
        slepc.LMEDestroy
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:95 <slepc4py/SLEPc/LME.pyx#L95>`
    
        """
        ...
    def reset(self) -> None:
        """Reset the LME object.
    
        Collective.
    
        See Also
        --------
        slepc.LMEReset
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:109 <slepc4py/SLEPc/LME.pyx#L109>`
    
        """
        ...
    def create(self, comm: Comm | None = None) -> Self:
        """Create the LME object.
    
        Collective.
    
        Parameters
        ----------
        comm
            MPI communicator. If not provided, it defaults to all processes.
    
        See Also
        --------
        slepc.LMECreate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:121 <slepc4py/SLEPc/LME.pyx#L121>`
    
        """
        ...
    def setType(self, lme_type: Type | str) -> None:
        """Set the particular solver to be used in the LME object.
    
        Logically collective.
    
        Parameters
        ----------
        lme_type
            The solver to be used.
    
        Notes
        -----
        The default is ``KRYLOV``. Normally, it is best to use
        `setFromOptions()` and then set the LME type from the options
        database rather than by using this routine. Using the options
        database provides the user with maximum flexibility in
        evaluating the different available methods.
    
        See Also
        --------
        getType, slepc.LMESetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:142 <slepc4py/SLEPc/LME.pyx#L142>`
    
        """
        ...
    def getType(self) -> str:
        """Get the LME type of this object.
    
        Not collective.
    
        Returns
        -------
        str
            The solver currently being used.
    
        See Also
        --------
        setType, slepc.LMEGetType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:169 <slepc4py/SLEPc/LME.pyx#L169>`
    
        """
        ...
    def setProblemType(self, lme_problem_type: ProblemType | str) -> None:
        """Set the LME problem type of this object.
    
        Logically collective.
    
        Parameters
        ----------
        lme_problem_type
            The problem type to be used.
    
        See Also
        --------
        getProblemType, slepc.LMESetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:188 <slepc4py/SLEPc/LME.pyx#L188>`
    
        """
        ...
    def getProblemType(self) -> ProblemType:
        """Get the LME problem type of this object.
    
        Not collective.
    
        Returns
        -------
        ProblemType
            The problem type currently being used.
    
        See Also
        --------
        setProblemType, slepc.LMEGetProblemType
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:206 <slepc4py/SLEPc/LME.pyx#L206>`
    
        """
        ...
    def setCoefficients(self, A: Mat, B: Mat | None = None, D: Mat | None = None, E: Mat | None = None) -> None:
        """Set the coefficient matrices.
    
        Collective.
    
        Set the coefficient matrices that define the linear matrix equation
        to be solved.
    
        Parameters
        ----------
        A
            First coefficient matrix
        B
            Second coefficient matrix, optional
        D
            Third coefficient matrix, optional
        E
            Fourth coefficient matrix, optional
    
        Notes
        -----
        The matrix equation takes the general form :math:`AXE+DXB=C`, where
        matrix :math:`C` is not provided here but with `setRHS()`. Not all
        four matrices must be passed.
    
        This must be called before `setUp()`. If called again after `setUp()`
        then the `LME` object is reset.
    
        See Also
        --------
        getCoefficients, solve, setRHS, setUp, slepc.LMESetCoefficients
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:225 <slepc4py/SLEPc/LME.pyx#L225>`
    
        """
        ...
    def getCoefficients(self) -> tuple[Mat, Mat | None, Mat | None, Mat | None]:
        """Get the coefficient matrices of the matrix equation.
    
        Collective.
    
        Returns
        -------
        A: petsc4py.PETSc.Mat
            First coefficient matrix.
        B: petsc4py.PETSc.Mat
            Second coefficient matrix, if available.
        D: petsc4py.PETSc.Mat
            Third coefficient matrix, if available.
        E: petsc4py.PETSc.Mat
            Fourth coefficient matrix, if available.
    
        See Also
        --------
        setCoefficients, slepc.LMEGetCoefficients
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:264 <slepc4py/SLEPc/LME.pyx#L264>`
    
        """
        ...
    def setRHS(self, C: Mat) -> None:
        """Set the right-hand side of the matrix equation.
    
        Collective.
    
        Parameters
        ----------
        C
            The right-hand side matrix
    
        Notes
        -----
        The matrix equation takes the general form :math:`AXE+DXB=C`, where
        matrix :math:`C` is given with this function. It must be a low-rank
        matrix of type `petsc4py.PETSc.Mat.Type.LRC`, that is,
        :math:`C = UDV^*` where :math:`D` is diagonal of order :math:`k`,
        and :math:`U,V` are dense tall-skinny matrices with :math:`k` columns.
        No sparse matrix must be provided when creating the ``LRC`` matrix.
    
        In equation types that require :math:`C` to be symmetric, such as
        Lyapunov, ``C`` must be created with :math:`V=U`.
    
        See Also
        --------
        getRHS, setSolution, slepc.LMESetRHS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:298 <slepc4py/SLEPc/LME.pyx#L298>`
    
        """
        ...
    def getRHS(self) -> Mat:
        """Get the right-hand side of the matrix equation.
    
        Collective.
    
        Returns
        -------
        C: petsc4py.PETSc.Mat
            The low-rank matrix.
    
        See Also
        --------
        setRHS, slepc.LMEGetRHS
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:327 <slepc4py/SLEPc/LME.pyx#L327>`
    
        """
        ...
    def setSolution(self, X: Mat | None = None) -> None:
        """Set the placeholder for the solution of the matrix equation.
    
        Collective.
    
        Parameters
        ----------
        X
            The solution matrix
    
        Notes
        -----
        The matrix equation takes the general form :math:`AXE+DXB=C`, where
        the solution matrix is of low rank and is written in factored form
        :math:`X = UDV^*`. This function provides a matrix object of type
        `petsc4py.PETSc.Mat.Type.LRC` that stores :math:`U,V` and
        (optionally) :math:`D`. These factors will be computed during `solve()`.
    
        In equation types whose solution :math:`X` is symmetric, such as
        Lyapunov, ``X`` must be created with :math:`V=U`.
    
        If the user provides ``X`` with this function, then the solver will
        return a solution with rank at most the number of columns of :math:`U`.
        Alternatively, it is possible to let the solver choose the rank of the
        solution, by passing ``None`` and then calling `getSolution()` after
        `solve()`.
    
        See Also
        --------
        solve, setRHS, getSolution, slepc.LMESetSolution
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:347 <slepc4py/SLEPc/LME.pyx#L347>`
    
        """
        ...
    def getSolution(self) -> Mat:
        """Get the solution of the matrix equation.
    
        Collective.
    
        Returns
        -------
        X: petsc4py.PETSc.Mat
            The low-rank matrix.
    
        Notes
        -----
        If called after `solve()`, ``X`` will contain the solution of the
        equation.
    
        The matrix ``X`` may have been passed by the user via `setSolution()`,
        although this is not required.
    
        See Also
        --------
        solve, setSolution, slepc.LMEGetSolution
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:382 <slepc4py/SLEPc/LME.pyx#L382>`
    
        """
        ...
    def getErrorEstimate(self) -> float:
        """Get the error estimate obtained during the solve.
    
        Not collective.
    
        Returns
        -------
        float
            The error estimate.
    
        Notes
        -----
        This is the error estimated internally by the solver. The actual
        error bound can be computed with `computeError()`. Note that some
        solvers may not be able to provide an error estimate.
    
        See Also
        --------
        computeError, slepc.LMEGetErrorEstimate
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:410 <slepc4py/SLEPc/LME.pyx#L410>`
    
        """
        ...
    def computeError(self) -> float:
        """Compute the error associated with the last equation solved.
    
        Collective.
    
        Returns
        -------
        float
            The error.
    
        Notes
        -----
        The error is based on the residual norm.
    
        This function is not scalable (in terms of memory or parallel
        communication), so it should not be called except in the case of
        small problem size. For large equations, use `getErrorEstimate()`.
    
        See Also
        --------
        getErrorEstimate, slepc.LMEComputeError
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:435 <slepc4py/SLEPc/LME.pyx#L435>`
    
        """
        ...
    def getOptionsPrefix(self) -> str:
        """Get the prefix used for searching for all LME options in the database.
    
        Not collective.
    
        Returns
        -------
        str
            The prefix string set for this LME object.
    
        See Also
        --------
        setOptionsPrefix, appendOptionsPrefix, slepc.LMEGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:462 <slepc4py/SLEPc/LME.pyx#L462>`
    
        """
        ...
    def setOptionsPrefix(self, prefix: str | None = None) -> None:
        """Set the prefix used for searching for all LME options in the database.
    
        Logically collective.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all LME option requests.
    
        Notes
        -----
        A hyphen (-) must NOT be given at the beginning of the prefix
        name.  The first character of all runtime options is
        AUTOMATICALLY the hyphen.
    
        For example, to distinguish between the runtime options for
        two different LME contexts, one could call::
    
            L1.setOptionsPrefix("lme1_")
            L2.setOptionsPrefix("lme2_")
    
        See Also
        --------
        appendOptionsPrefix, getOptionsPrefix, slepc.LMEGetOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:481 <slepc4py/SLEPc/LME.pyx#L481>`
    
        """
        ...
    def appendOptionsPrefix(self, prefix: str | None = None) -> None:
        """Append to the prefix used for searching in the database.
    
        Logically collective.
    
        Append to the prefix used for searching for all LME options in the
        database.
    
        Parameters
        ----------
        prefix
            The prefix string to prepend to all LME option requests.
    
        See Also
        --------
        setOptionsPrefix, getOptionsPrefix, slepc.LMEAppendOptionsPrefix
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:512 <slepc4py/SLEPc/LME.pyx#L512>`
    
        """
        ...
    def setFromOptions(self) -> None:
        """Set LME options from the options database.
    
        Collective.
    
        Notes
        -----
        To see all options, run your program with the ``-help`` option.
    
        This routine must be called before `setUp()` if the user is to be
        allowed to set the solver type.
    
        See Also
        --------
        setOptionsPrefix, slepc.LMESetFromOptions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:534 <slepc4py/SLEPc/LME.pyx#L534>`
    
        """
        ...
    def getTolerances(self) -> tuple[float, int]:
        """Get the tolerance and maximum iteration count.
    
        Not collective.
    
        Returns
        -------
        tol: float
            The convergence tolerance.
        max_it: int
            The maximum number of iterations.
    
        See Also
        --------
        setTolerances, slepc.LMEGetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:553 <slepc4py/SLEPc/LME.pyx#L553>`
    
        """
        ...
    def setTolerances(self, tol: float | None = None, max_it: int | None = None) -> None:
        """Set the tolerance and maximum iteration count.
    
        Logically collective.
    
        Set the tolerance and maximum iteration count used by the
        default LME convergence tests.
    
        Parameters
        ----------
        tol
            The convergence tolerance.
        max_it
            The maximum number of iterations.
    
        See Also
        --------
        getTolerances, slepc.LMESetTolerances
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:575 <slepc4py/SLEPc/LME.pyx#L575>`
    
        """
        ...
    def getDimensions(self) -> int:
        """Get the dimension of the subspace used by the solver.
    
        Not collective.
    
        Returns
        -------
        int
            Maximum dimension of the subspace to be used by the solver.
    
        See Also
        --------
        setDimensions, slepc.LMEGetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:601 <slepc4py/SLEPc/LME.pyx#L601>`
    
        """
        ...
    def setDimensions(self, ncv: int) -> None:
        """Set the dimension of the subspace to be used by the solver.
    
        Logically collective.
    
        Parameters
        ----------
        ncv
            Maximum dimension of the subspace to be used by the solver.
    
        See Also
        --------
        getDimensions, slepc.LMESetDimensions
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:620 <slepc4py/SLEPc/LME.pyx#L620>`
    
        """
        ...
    def getBV(self) -> BV:
        """Get the basis vector object associated to the LME object.
    
        Not collective.
    
        Returns
        -------
        BV
            The basis vectors context.
    
        See Also
        --------
        setBV, slepc.LMEGetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:638 <slepc4py/SLEPc/LME.pyx#L638>`
    
        """
        ...
    def setBV(self, bv: BV) -> None:
        """Set a basis vector object to the LME object.
    
        Collective.
    
        Parameters
        ----------
        bv
            The basis vectors context.
    
        See Also
        --------
        getBV, slepc.LMESetBV
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:658 <slepc4py/SLEPc/LME.pyx#L658>`
    
        """
        ...
    def setMonitor(self, monitor: LMEMonitorFunction | None, args: tuple[Any, ...] | None = None, kargs: dict[str, Any] | None = None) -> None:
        """Append a monitor function to the list of monitors.
    
        Logically collective.
    
        See Also
        --------
        getMonitor, cancelMonitor, slepc.LMEMonitorSet
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:675 <slepc4py/SLEPc/LME.pyx#L675>`
    
        """
        ...
    def getMonitor(self) -> LMEMonitorFunction:
        """Get the list of monitor functions.
    
        Not collective.
    
        Returns
        -------
        LMEMonitorFunction
            The list of monitor functions.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:700 <slepc4py/SLEPc/LME.pyx#L700>`
    
        """
        ...
    def cancelMonitor(self) -> None:
        """Clear all monitors for an `LME` object.
    
        Logically collective.
    
        See Also
        --------
        slepc.LMEMonitorCancel
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:713 <slepc4py/SLEPc/LME.pyx#L713>`
    
        """
        ...
    def setUp(self) -> None:
        """Set up all the internal necessary data structures.
    
        Collective.
    
        Set up all the internal data structures necessary for the
        execution of the eigensolver.
    
        See Also
        --------
        solve, slepc.LMESetUp
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:726 <slepc4py/SLEPc/LME.pyx#L726>`
    
        """
        ...
    def solve(self) -> None:
        """Solve the linear matrix equation.
    
        Collective.
    
        Notes
        -----
        The matrix coefficients are specified with `setCoefficients()`.
        The right-hand side is specified with `setRHS()`. The placeholder
        for the solution is specified with `setSolution()`.
        See Also
        --------
        setCoefficients, setRHS, setSolution, slepc.LMESolve
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:741 <slepc4py/SLEPc/LME.pyx#L741>`
    
        """
        ...
    def getIterationNumber(self) -> int:
        """Get the current iteration number.
    
        Not collective.
    
        If the call to `solve()` is complete, then it returns the number of
        iterations carried out by the solution method.
    
        Returns
        -------
        int
            Iteration number.
    
        See Also
        --------
        getConvergedReason, slepc.LMEGetIterationNumber
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:758 <slepc4py/SLEPc/LME.pyx#L758>`
    
        """
        ...
    def getConvergedReason(self) -> ConvergedReason:
        """Get the reason why the `solve()` iteration was stopped.
    
        Not collective.
    
        Returns
        -------
        ConvergedReason
            Negative value indicates diverged, positive value converged.
    
        See Also
        --------
        setTolerances, solve, setErrorIfNotConverged, slepc.LMEGetConvergedReason
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:780 <slepc4py/SLEPc/LME.pyx#L780>`
    
        """
        ...
    def setErrorIfNotConverged(self, flg: bool = True) -> None:
        """Set `solve()` to generate an error if the solver has not converged.
    
        Logically collective.
    
        Parameters
        ----------
        flg
            ``True`` indicates you want the error generated.
    
        Notes
        -----
        Normally SLEPc continues if the solver fails to converge, you can
        call `getConvergedReason()` after a `solve()` to determine if it
        has converged.
    
        See Also
        --------
        getConvergedReason, solve, slepc.LMESetErrorIfNotConverged
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:799 <slepc4py/SLEPc/LME.pyx#L799>`
    
        """
        ...
    def getErrorIfNotConverged(self) -> bool:
        """Get if `solve()` generates an error if the solver does not converge.
    
        Not collective.
    
        Get a flag indicating whether `solve()` will generate an error if the
        solver does not converge.
    
        Returns
        -------
        bool
            ``True`` indicates you want the error generated.
    
        See Also
        --------
        setErrorIfNotConverged, slepc.LMEGetErrorIfNotConverged
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:823 <slepc4py/SLEPc/LME.pyx#L823>`
    
        """
        ...
    @property
    def tol(self) -> float:
        """The tolerance value used by the LME convergence tests.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:847 <slepc4py/SLEPc/LME.pyx#L847>`
    
        """
        ...
    @property
    def max_it(self) -> int:
        """The maximum iteration count used by the LME convergence tests.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:854 <slepc4py/SLEPc/LME.pyx#L854>`
    
        """
        ...
    @property
    def fn(self) -> FN:
        """The math function (`FN`) object associated to the LME object.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:861 <slepc4py/SLEPc/LME.pyx#L861>`
    
        """
        ...
    @property
    def bv(self) -> BV:
        """The basis vectors (`BV`) object associated to the LME object.
    
    
    
        :sources:`Source code at slepc4py/SLEPc/LME.pyx:868 <slepc4py/SLEPc/LME.pyx#L868>`
    
        """
        ...

class Sys:
    """System utilities."""
    @classmethod
    def getVersion(cls, devel: bool = False, date: bool = False, author: bool = False) -> tuple[int, int, int]:
        """Return SLEPc version information.
    
        Not collective.
    
        Parameters
        ----------
        devel
            Additionally, return whether using an in-development version.
        date
            Additionally, return date information.
        author
            Additionally, return author information.
    
        Returns
        -------
        major: int
            Major version number.
        minor: int
            Minor version number.
        micro: int
            Micro (or patch) version number.
    
        See Also
        --------
        slepc.SlepcGetVersion, slepc.SlepcGetVersionNumber
    
    
    
        :sources:`Source code at slepc4py/SLEPc/Sys.pyx:8 <slepc4py/SLEPc/Sys.pyx#L8>`
    
        """
        ...
    @classmethod
    def getVersionInfo(cls) -> dict[str, bool | int | str]:
        """Return SLEPc version information.
    
        Not collective.
    
        Returns
        -------
        info: dict
            Dictionary with version information.
    
        See Also
        --------
        slepc.SlepcGetVersion, slepc.SlepcGetVersionNumber
    
    
    
        :sources:`Source code at slepc4py/SLEPc/Sys.pyx:64 <slepc4py/SLEPc/Sys.pyx#L64>`
    
        """
        ...
    @classmethod
    def isInitialized(cls) -> bool:
        """Return whether SLEPc has been initialized.
    
        Not collective.
    
        See Also
        --------
        isFinalized
    
    
    
        :sources:`Source code at slepc4py/SLEPc/Sys.pyx:90 <slepc4py/SLEPc/Sys.pyx#L90>`
    
        """
        ...
    @classmethod
    def isFinalized(cls) -> bool:
        """Return whether SLEPc has been finalized.
    
        Not collective.
    
        See Also
        --------
        isInitialized
    
    
    
        :sources:`Source code at slepc4py/SLEPc/Sys.pyx:103 <slepc4py/SLEPc/Sys.pyx#L103>`
    
        """
        ...
    @classmethod
    def hasExternalPackage(cls, package: str) -> bool:
        """Return whether SLEPc has support for external package.
    
        Not collective.
    
        Parameters
        ----------
        package
            The external package name.
    
        See Also
        --------
        slepc.SlepcHasExternalPackage
    
    
    
        :sources:`Source code at slepc4py/SLEPc/Sys.pyx:118 <slepc4py/SLEPc/Sys.pyx#L118>`
    
        """
        ...

class Util:
    """Other utilities such as the creation of structured matrices."""
    @classmethod
    def createMatBSE(cls, R: petsc4py.PETSc.Mat, C: petsc4py.PETSc.Mat) -> petsc4py.PETSc.Mat:
        """Create a matrix that can be used to define a BSE type problem.
    
        Collective.
    
        Create a matrix that can be used to define a structured eigenvalue
        problem of type BSE (Bethe-Salpeter Equation).
    
        Parameters
        ----------
        R
            The matrix for the diagonal block (resonant).
        C
            The matrix for the off-diagonal block (coupling).
    
        Returns
        -------
        petsc4py.PETSc.Mat
            The matrix with the block form :math:`H = [ R\; C; {-C}^*\; {-R}^T ]`.
    
        See Also
        --------
        slepc.MatCreateBSE
    
    
    
        :sources:`Source code at slepc4py/SLEPc/Util.pyx:8 <slepc4py/SLEPc/Util.pyx#L8>`
    
        """
        ...
    @classmethod
    def createMatHamiltonian(cls, A: petsc4py.PETSc.Mat, B: petsc4py.PETSc.Mat, C: petsc4py.PETSc.Mat) -> petsc4py.PETSc.Mat:
        """Create matrix to be used for a structured Hamiltonian eigenproblem.
    
        Collective.
    
        Parameters
        ----------
        A
            The matrix for (0,0) block.
        B
            The matrix for (0,1) block, must be real symmetric or Hermitian.
        C
            The matrix for (1,0) block, must be real symmetric or Hermitian.
    
        Returns
        -------
        petsc4py.PETSc.Mat
            The matrix with the block form :math:`H = [ A\; B; C\; -A^* ]`.
    
        See Also
        --------
        slepc.MatCreateHamiltonian
    
    
    
        :sources:`Source code at slepc4py/SLEPc/Util.pyx:38 <slepc4py/SLEPc/Util.pyx#L38>`
    
        """
        ...

class _p_mem:
    """"""

def _initialize(args=None):
    """



    :sources:`Source code at slepc4py/SLEPc/SLEPc.pyx:262 <slepc4py/SLEPc/SLEPc.pyx#L262>`

    """
    ...
def _finalize():
    """



    :sources:`Source code at slepc4py/SLEPc/SLEPc.pyx:266 <slepc4py/SLEPc/SLEPc.pyx#L266>`

    """
    ...


from .typing import *
