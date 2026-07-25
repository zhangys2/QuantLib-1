/* -*- mode: c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 Copyright (C) 2008 Andreas Gaida
 Copyright (C) 2008 Ralph Schreyer
 Copyright (C) 2008 Klaus Spanderen
 Copyright (C) 2014 Johannes Göttker-Schnetmann

 This file is part of QuantLib, a free-software/open-source library
 for financial quantitative analysts and developers - http://quantlib.org/

 QuantLib is free software: you can redistribute it and/or modify it
 under the terms of the QuantLib license.  You should have received a
 copy of the license along with this program; if not, please email
 <quantlib-dev@lists.sf.net>. The license is also available online at
 <https://www.quantlib.org/license.shtml>.

 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the license for more details.
*/

#include <ql/methods/finitedifferences/meshers/fdmmesher.hpp>
#include <ql/methods/finitedifferences/tridiagonaloperator.hpp>
#include <ql/methods/finitedifferences/operators/fdmlinearoplayout.hpp>
#include <ql/methods/finitedifferences/operators/triplebandlinearop.hpp>

namespace QuantLib {

    TripleBandLinearOp::TripleBandLinearOp(
        Size direction,
        const ext::shared_ptr<FdmMesher>& mesher)
    : direction_(direction),
      i0_       (new Size[mesher->layout()->size()]),
      i2_       (new Size[mesher->layout()->size()]),
      reverseIndex_ (new Size[mesher->layout()->size()]),
      lower_    (new Real[mesher->layout()->size()]),
      diag_     (new Real[mesher->layout()->size()]),
      upper_    (new Real[mesher->layout()->size()]),
      mesher_(mesher) {

        std::vector<Size> newDim(mesher->layout()->dim());
        std::iter_swap(newDim.begin(), newDim.begin()+direction_);
        std::vector<Size> newSpacing = FdmLinearOpLayout(newDim).spacing();
        std::iter_swap(newSpacing.begin(), newSpacing.begin()+direction_);

        for (const auto& iter : *mesher->layout()) {
            const Size i = iter.index();

            i0_[i] = mesher->layout()->neighbourhood(iter, direction, -1);
            i2_[i] = mesher->layout()->neighbourhood(iter, direction,  1);

            const std::vector<Size>& coordinates = iter.coordinates();
            const Size newIndex =
                  std::inner_product(coordinates.begin(), coordinates.end(),
                                     newSpacing.begin(), Size(0));
            reverseIndex_[newIndex] = i;
        }
    }

    TripleBandLinearOp::TripleBandLinearOp(const TripleBandLinearOp& m)
    : direction_(m.direction_),
      i0_   (new Size[m.mesher_->layout()->size()]),
      i2_   (new Size[m.mesher_->layout()->size()]),
      reverseIndex_(new Size[m.mesher_->layout()->size()]),
      lower_(new Real[m.mesher_->layout()->size()]),
      diag_ (new Real[m.mesher_->layout()->size()]),
      upper_(new Real[m.mesher_->layout()->size()]),
      mesher_(m.mesher_) {
        const Size len = m.mesher_->layout()->size();
        std::copy(m.i0_.get(), m.i0_.get() + len, i0_.get());
        std::copy(m.i2_.get(), m.i2_.get() + len, i2_.get());
        std::copy(m.reverseIndex_.get(), m.reverseIndex_.get()+len,
                  reverseIndex_.get());
        std::copy(m.lower_.get(), m.lower_.get() + len, lower_.get());
        std::copy(m.diag_.get(),  m.diag_.get() + len,  diag_.get());
        std::copy(m.upper_.get(), m.upper_.get() + len, upper_.get());
    }

    void TripleBandLinearOp::swap(TripleBandLinearOp& m) noexcept {
        mesher_.swap(m.mesher_);
        std::swap(direction_, m.direction_);

        i0_.swap(m.i0_); i2_.swap(m.i2_);
        reverseIndex_.swap(m.reverseIndex_);
        lower_.swap(m.lower_); diag_.swap(m.diag_); upper_.swap(m.upper_);
    }

    void TripleBandLinearOp::axpyb(const Array& a,
                                   const TripleBandLinearOp& x,
                                   const TripleBandLinearOp& y,
                                   const Array& b) {
        const Size size = mesher_->layout()->size();

        Real *diag(diag_.get());
        Real *lower(lower_.get());
        Real *upper(upper_.get());

        const Real *y_diag (y.diag_.get());
        const Real *y_lower(y.lower_.get());
        const Real *y_upper(y.upper_.get());

        if (a.empty()) {
            if (b.empty()) {
                //#pragma omp parallel for
                for (Size i=0; i < size; ++i) {
                    diag[i]  = y_diag[i];
                    lower[i] = y_lower[i];
                    upper[i] = y_upper[i];
                }
            }
            else {
                Array::const_iterator bptr(b.begin());
                const Size binc = (b.size() > 1) ? 1 : 0;
                //#pragma omp parallel for
                for (Size i=0; i < size; ++i) {
                    diag[i]  = y_diag[i] + bptr[i*binc];
                    lower[i] = y_lower[i];
                    upper[i] = y_upper[i];
                }
            }
        }
        else if (b.empty()) {
            Array::const_iterator aptr(a.begin());
            const Size ainc = (a.size() > 1) ? 1 : 0;

            const Real *x_diag (x.diag_.get());
            const Real *x_lower(x.lower_.get());
            const Real *x_upper(x.upper_.get());

            //#pragma omp parallel for
            for (Size i=0; i < size; ++i) {
                const Real s = aptr[i*ainc];
                diag[i]  = y_diag[i]  + s*x_diag[i];
                lower[i] = y_lower[i] + s*x_lower[i];
                upper[i] = y_upper[i] + s*x_upper[i];
            }
        }
        else {
            Array::const_iterator bptr(b.begin());
            const Size binc = (b.size() > 1) ? 1 : 0;

            Array::const_iterator aptr(a.begin());
            const Size ainc = (a.size() > 1) ? 1 : 0;

            const Real *x_diag (x.diag_.get());
            const Real *x_lower(x.lower_.get());
            const Real *x_upper(x.upper_.get());

            //#pragma omp parallel for
            for (Size i=0; i < size; ++i) {
                const Real s = aptr[i*ainc];
                diag[i]  = y_diag[i]  + s*x_diag[i] + bptr[i*binc];
                lower[i] = y_lower[i] + s*x_lower[i];
                upper[i] = y_upper[i] + s*x_upper[i];
            }
        }
    }

    TripleBandLinearOp TripleBandLinearOp::add(const TripleBandLinearOp& m) const {

        TripleBandLinearOp retVal(direction_, mesher_);
        const Size size = mesher_->layout()->size();
        //#pragma omp parallel for
        for (Size i=0; i < size; ++i) {
            retVal.lower_[i]= lower_[i] + m.lower_[i];
            retVal.diag_[i] = diag_[i]  + m.diag_[i];
            retVal.upper_[i]= upper_[i] + m.upper_[i];
        }

        return retVal;
    }


    TripleBandLinearOp TripleBandLinearOp::mult(const Array& u) const {

        TripleBandLinearOp retVal(direction_, mesher_);

        const Size size = mesher_->layout()->size();
        //#pragma omp parallel for
        for (Size i=0; i < size; ++i) {
            const Real s = u[i];
            retVal.lower_[i]= lower_[i]*s;
            retVal.diag_[i] = diag_[i]*s;
            retVal.upper_[i]= upper_[i]*s;
        }

        return retVal;
    }

    TripleBandLinearOp TripleBandLinearOp::multR(const Array& u) const {
        const Size size = mesher_->layout()->size();
        QL_REQUIRE(u.size() == size, "inconsistent size of rhs");
        TripleBandLinearOp retVal(direction_, mesher_);

        #pragma omp parallel for
        for (long i=0; i < (long)size; ++i) {
            const Real sm1 = i > 0? u[i-1] : 1.0;
            const Real s0 = u[i];
            const Real sp1 = i < (long)size-1? u[i+1] : 1.0;
            retVal.lower_[i]= lower_[i]*sm1;
            retVal.diag_[i] = diag_[i]*s0;
            retVal.upper_[i]= upper_[i]*sp1;
        }

        return retVal;
    }

    TripleBandLinearOp TripleBandLinearOp::add(const Array& u) const {

        TripleBandLinearOp retVal(direction_, mesher_);

        const Size size = mesher_->layout()->size();
        //#pragma omp parallel for
        for (Size i=0; i < size; ++i) {
            retVal.lower_[i]= lower_[i];
            retVal.upper_[i]= upper_[i];
            retVal.diag_[i] = diag_[i]+u[i];
        }

        return retVal;
    }

    Array TripleBandLinearOp::apply(const Array& r) const {
        QL_REQUIRE(r.size() == mesher_->layout()->size(), "inconsistent length of r");

        const Real* lptr = lower_.get();
        const Real* dptr = diag_.get();
        const Real* uptr = upper_.get();
        const Size* i0ptr = i0_.get();
        const Size* i2ptr = i2_.get();

        array_type retVal(r.size());
        //#pragma omp parallel for
        for (Size i=0; i < mesher_->layout()->size(); ++i) {
            retVal[i] = r[i0ptr[i]]*lptr[i]+r[i]*dptr[i]+r[i2ptr[i]]*uptr[i];
        }

        return retVal;
    }

    SparseMatrix TripleBandLinearOp::toMatrix() const {
        const Size n = mesher_->layout()->size();

        SparseMatrix retVal(n, n, 3*n);
        for (Size i=0; i < n; ++i) {
            retVal(i, i0_[i]) += lower_[i];
            retVal(i, i     ) += diag_[i];
            retVal(i, i2_[i]) += upper_[i];
        }

        return retVal;
    }


    Array TripleBandLinearOp::solve_splitting(const Array& r, Real a, Real b) const {
        QL_REQUIRE(r.size() == mesher_->layout()->size(), "inconsistent size of rhs");

#ifdef QL_EXTRA_SAFETY_CHECKS
        for (const auto& iter : *mesher_->layout()) {
            const std::vector<Size>& coordinates = iter.coordinates();
            QL_REQUIRE(   coordinates[direction_] != 0
                       || lower_[iter.index()] == 0,"removing non zero entry!");
            QL_REQUIRE(   coordinates[direction_] != mesher_->layout()->dim()[direction_]-1
                       || upper_[iter.index()] == 0,"removing non zero entry!");
        }
#endif

        const Size size = mesher_->layout()->size();
        const Size lineSize = mesher_->layout()->dim()[direction_];
        const Size stride = mesher_->layout()->spacing()[direction_];
        const Size lines = size/lineSize;

        /* Lines are solved in groups. Each line is a serial dependency chain
           whose critical path is one division per point, so a single line
           leaves the divider mostly idle; running several independent chains
           at once fills it. Four is enough to saturate a current x86 divider,
           and measures ~4x against one line at a time. Explicit SIMD is not
           needed for this -- the gain is instruction-level parallelism over
           independent chains, which the hardware already extracts once the
           chains are interleaved.
        */
        constexpr Size group = 4;

        Array retVal(size);
        std::vector<Real> tmp(lineSize*group);

        const Real* lptr = lower_.get();
        const Real* dptr = diag_.get();
        const Real* uptr = upper_.get();

        /* This is one tridiagonal system per line of the grid along
           direction_, and the lines are independent: the operator has a zero
           lower band at the first point of a line and a zero upper band at the
           last, which is what the safety checks above assert. Walking each
           line explicitly with the layout stride replaces a dependent load per
           point (reverseIndex_[j]) with one per line, and makes the inner loop
           a strided access the hardware can prefetch. reverseIndex_ orders
           points so that direction_ varies fastest, so entry k*lineSize is the
           first point of line k and successive points are stride apart.

           The arithmetic is unchanged, including operand order, so results are
           bit-identical to the previous flattened sweep.
        */
#ifdef QL_EXTRA_SAFETY_CHECKS
        for (Size k=0; k < lines; ++k) {
            const Size base = reverseIndex_[k*lineSize];
            for (Size m=0; m < lineSize; ++m)
                QL_REQUIRE(reverseIndex_[k*lineSize+m] == base + m*stride,
                           "reverseIndex_ is not affine along direction " << direction_);
        }
#endif

        // Thomson algorithm to solve a tridiagonal system.
        // Example code taken from Tridiagonalopertor and
        // changed to fit for the triple band operator.
        // Each line is solved exactly as before, so results are unchanged.
        Size base[group], rim1[group];
        Real bet[group];

        for (Size k=0; k < lines; k += group) {
            const Size width = std::min(group, lines-k);

            for (Size c=0; c < width; ++c) {
                base[c] = reverseIndex_[(k+c)*lineSize];
                rim1[c] = base[c];
                bet[c] = 1.0/(a*dptr[rim1[c]]+b);
                QL_REQUIRE(bet[c] != 0.0, "division by zero");
                retVal[rim1[c]] = r[rim1[c]]*bet[c];
            }

            for (Size m=1; m < lineSize; ++m) {
                for (Size c=0; c < width; ++c) {
                    const Size ri = base[c] + m*stride;
                    Real& t = tmp[m*group+c];
                    t = a*uptr[rim1[c]]*bet[c];

                    bet[c]=b+a*(dptr[ri]-t*lptr[ri]);
                    QL_ENSURE(bet[c] != 0.0, "division by zero");
                    bet[c]=1.0/bet[c];

                    retVal[ri] = (r[ri]-a*lptr[ri]*retVal[rim1[c]])*bet[c];
                    rim1[c] = ri;
                }
            }

            for (Size m=lineSize-1; m > 0; --m)
                for (Size c=0; c < width; ++c)
                    retVal[base[c]+(m-1)*stride] -=
                        tmp[m*group+c]*retVal[base[c]+m*stride];
        }

        return retVal;
    }
}
