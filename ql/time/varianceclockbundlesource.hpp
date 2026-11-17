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

/*! \file varianceclockbundlesource.hpp
    \brief variance-clock bundle byte source interface
*/

#ifndef quantlib_variance_clock_bundle_source_hpp
#define quantlib_variance_clock_bundle_source_hpp

#include <cstddef>
#include <memory>
#include <string>
#include <vector>

namespace QuantLib {
    namespace detail {

        class VarianceClockBundleSource {
          public:
            virtual ~VarianceClockBundleSource() = default;
            virtual std::vector<unsigned char> read(const std::string& flatName,
                                                    std::size_t maxBytes) const = 0;
        };

        class VarianceClockDirectorySource final : public VarianceClockBundleSource {
          public:
            explicit VarianceClockDirectorySource(std::string nativeDirectory);
            ~VarianceClockDirectorySource() override;

            VarianceClockDirectorySource(const VarianceClockDirectorySource&) = delete;
            VarianceClockDirectorySource& operator=(const VarianceClockDirectorySource&) = delete;

            std::vector<unsigned char> read(const std::string& flatName,
                                            std::size_t maxBytes) const override;

          private:
            class Impl;
            std::unique_ptr<Impl> impl_;
        };

    }
}

#endif
