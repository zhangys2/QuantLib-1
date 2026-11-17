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

        // Reads the six bundle files from a native directory path.
        //
        // Contract for callers (the loader in B5):
        //  - Construct a new source inside every load. The root's entries are checked once,
        //    in the constructor, so a source kept across loads does not notice entries that
        //    are added or replaced afterwards.
        //  - Do not modify the root while a capture runs. POSIX reads are relative to the
        //    directory handle opened in the constructor; Windows reads still open by full
        //    path, so a rename of the root or of a parent during capture is not detected.
        //  - The path must not contain "." or ".." components, including relative forms such
        //    as "./bundle". They are rejected without touching the filesystem, because they
        //    can route around the symlink-root check. Pass an absolute or otherwise dot-free
        //    path; a symlink as the final component is rejected, symlinks in parent
        //    components are followed.
        //  - manifest.json has no digest of its own; the CSV files are verified against it.
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
