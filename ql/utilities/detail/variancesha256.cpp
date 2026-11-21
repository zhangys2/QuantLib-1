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

#include <ql/errors.hpp>
#include <ql/utilities/detail/variancesha256.hpp>
#include <algorithm>
#include <limits>

namespace QuantLib {
    namespace detail {

        namespace {

            constexpr std::array<std::uint32_t, 64> roundConstants{{
                0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
                0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
                0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
                0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
                0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
                0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
                0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
                0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
                0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
                0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
                0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
                0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
                0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
                0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
                0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
                0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
            }};

            std::uint32_t rotateRight(std::uint32_t value, unsigned int shift) {
                return (value >> shift) | (value << (32 - shift));
            }

        }

        VarianceSha256::VarianceSha256()
        : state_{{0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                  0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19}},
          buffer_{{}},
          bufferSize_(0),
          totalBytes_(0),
          finished_(false) {}

        void VarianceSha256::update(std::string_view bytes) {
            QL_REQUIRE(!finished_, "cannot update a finished SHA-256 digest");
            constexpr std::uint64_t maxBytes =
                (std::numeric_limits<std::uint64_t>::max)() / 8;
            QL_REQUIRE(bytes.size() <= maxBytes - totalBytes_,
                       "SHA-256 input exceeds the maximum representable bit length");

            if (bytes.empty())
                return;

            const auto* input =
                reinterpret_cast<const unsigned char*>(bytes.data());
            std::size_t remaining = bytes.size();
            totalBytes_ += static_cast<std::uint64_t>(remaining);

            if (bufferSize_ != 0) {
                const std::size_t count = (std::min)(remaining, buffer_.size() - bufferSize_);
                std::copy_n(input, count, buffer_.begin() + bufferSize_);
                bufferSize_ += count;
                input += count;
                remaining -= count;
                if (bufferSize_ == buffer_.size()) {
                    transform(buffer_.data());
                    bufferSize_ = 0;
                }
            }

            while (remaining >= buffer_.size()) {
                transform(input);
                input += buffer_.size();
                remaining -= buffer_.size();
            }

            if (remaining != 0) {
                std::copy_n(input, remaining, buffer_.begin());
                bufferSize_ = remaining;
            }
        }

        std::string VarianceSha256::finishHex() {
            QL_REQUIRE(!finished_, "SHA-256 digest has already been finished");
            finished_ = true;

            const std::uint64_t bitLength = totalBytes_ * 8;
            buffer_[bufferSize_++] = 0x80;
            if (bufferSize_ > 56) {
                std::fill(buffer_.begin() + bufferSize_, buffer_.end(), 0);
                transform(buffer_.data());
                bufferSize_ = 0;
            }
            std::fill(buffer_.begin() + bufferSize_, buffer_.begin() + 56, 0);
            for (std::size_t i = 0; i < 8; ++i)
                buffer_[63 - i] = static_cast<unsigned char>(bitLength >> (i * 8));
            transform(buffer_.data());

            constexpr char hexDigits[] = "0123456789abcdef";
            std::string result(64, '0');
            for (std::size_t i = 0; i < state_.size(); ++i) {
                for (std::size_t j = 0; j < 4; ++j) {
                    const unsigned char byte =
                        static_cast<unsigned char>(state_[i] >> (24 - j * 8));
                    result[2 * (4 * i + j)] = hexDigits[byte >> 4];
                    result[2 * (4 * i + j) + 1] = hexDigits[byte & 0x0f];
                }
            }
            return result;
        }

        void VarianceSha256::transform(const unsigned char* block) {
            std::array<std::uint32_t, 64> words{};
            for (std::size_t i = 0; i < 16; ++i) {
                const std::size_t offset = 4 * i;
                words[i] = (static_cast<std::uint32_t>(block[offset]) << 24) |
                           (static_cast<std::uint32_t>(block[offset + 1]) << 16) |
                           (static_cast<std::uint32_t>(block[offset + 2]) << 8) |
                           static_cast<std::uint32_t>(block[offset + 3]);
            }
            for (std::size_t i = 16; i < words.size(); ++i) {
                const std::uint32_t s0 =
                    rotateRight(words[i - 15], 7) ^ rotateRight(words[i - 15], 18) ^
                    (words[i - 15] >> 3);
                const std::uint32_t s1 =
                    rotateRight(words[i - 2], 17) ^ rotateRight(words[i - 2], 19) ^
                    (words[i - 2] >> 10);
                words[i] = words[i - 16] + s0 + words[i - 7] + s1;
            }

            std::uint32_t a = state_[0];
            std::uint32_t b = state_[1];
            std::uint32_t c = state_[2];
            std::uint32_t d = state_[3];
            std::uint32_t e = state_[4];
            std::uint32_t f = state_[5];
            std::uint32_t g = state_[6];
            std::uint32_t h = state_[7];

            for (std::size_t i = 0; i < words.size(); ++i) {
                const std::uint32_t sum1 =
                    rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
                const std::uint32_t choice = (e & f) ^ (~e & g);
                const std::uint32_t temp1 = h + sum1 + choice + roundConstants[i] + words[i];
                const std::uint32_t sum0 =
                    rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
                const std::uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
                const std::uint32_t temp2 = sum0 + majority;

                h = g;
                g = f;
                f = e;
                e = d + temp1;
                d = c;
                c = b;
                b = a;
                a = temp1 + temp2;
            }

            state_[0] += a;
            state_[1] += b;
            state_[2] += c;
            state_[3] += d;
            state_[4] += e;
            state_[5] += f;
            state_[6] += g;
            state_[7] += h;
        }

    }
}
