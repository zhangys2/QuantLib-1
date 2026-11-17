/* -*- mode: c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 Copyright (C) 2026 QuantLib contributors

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

/*! \file varianceclockbundle.hpp
    \brief end-to-end variance-clock bundle loading interface
*/

#ifndef quantlib_variance_clock_bundle_hpp
#define quantlib_variance_clock_bundle_hpp

#include <ql/time/varianceclockbundlesource.hpp>
#include <ql/time/varianceclockbundletypes.hpp>
#include <string>

namespace QuantLib {

    VarianceClockLoadedBundle loadVarianceClockBundle(
        const detail::VarianceClockBundleSource& source,
        VarianceClockLoadMode mode = VarianceClockLoadMode::Strict);

    VarianceClockLoadedBundle loadVarianceClockBundleFromDirectory(
        const std::string& nativeDirectory,
        VarianceClockLoadMode mode = VarianceClockLoadMode::Strict);

}

#endif
