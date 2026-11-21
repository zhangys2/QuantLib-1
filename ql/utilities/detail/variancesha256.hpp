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

/*! \file variancesha256.hpp
    \brief internal incremental SHA-256 digest for variance-clock bytes
*/

#ifndef quantlib_variance_sha256_hpp
#define quantlib_variance_sha256_hpp

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace QuantLib {
    namespace detail {

        class VarianceSha256 {
          public:
            VarianceSha256();
            void update(std::string_view bytes);
            std::string finishHex();

          private:
            void transform(const unsigned char* block);

            std::array<std::uint32_t, 8> state_;
            std::array<unsigned char, 64> buffer_;
            std::size_t bufferSize_;
            std::uint64_t totalBytes_;
            bool finished_;
        };

    }
}

#endif
