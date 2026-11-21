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

#include <ql/time/varianceclockbundlecapture.hpp>
#include <ql/errors.hpp>
#include <ql/utilities/detail/variancesha256.hpp>
#include <algorithm>
#include <array>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>
#include <utility>

#if defined(_WIN32)
#include <windows.h>
#else
#include <dirent.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

namespace QuantLib {
    namespace detail {
        namespace {

            constexpr std::size_t maxBundleSourceManifestBytes = 4U * 1024U * 1024U;
            constexpr std::size_t maxBundleSourceCsvBytes = 32U * 1024U * 1024U;
            constexpr std::size_t maxBundleBytes = 128U * 1024U * 1024U;

            const std::array<const char*, 5> csvNames{{
                "profiles.csv", "market_days.csv", "session_segments.csv", "timezone_mapping.csv",
                "slot_evidence.csv"}};

            std::string_view charView(const std::vector<unsigned char>& bytes) noexcept {
                if (bytes.empty())
                    return {};
                return {reinterpret_cast<const char*>(bytes.data()), bytes.size()};
            }

#if !defined(_WIN32)
            class ScopedFd {
              public:
                explicit ScopedFd(int fd = -1) noexcept : fd_(fd) {}
                ScopedFd(const ScopedFd&) = delete;
                ScopedFd& operator=(const ScopedFd&) = delete;
                ~ScopedFd() {
                    if (fd_ >= 0)
                        ::close(fd_);
                }
                int get() const noexcept {
                    return fd_;
                }
                int release() noexcept {
                    const int result = fd_;
                    fd_ = -1;
                    return result;
                }

              private:
                int fd_;
            };
#else
            class ScopedHandle {
              public:
                explicit ScopedHandle(HANDLE handle = INVALID_HANDLE_VALUE) noexcept
                : handle_(handle) {}
                ScopedHandle(const ScopedHandle&) = delete;
                ScopedHandle& operator=(const ScopedHandle&) = delete;
                ~ScopedHandle() {
                    if (handle_ != INVALID_HANDLE_VALUE)
                        CloseHandle(handle_);
                }
                HANDLE get() const noexcept {
                    return handle_;
                }
                HANDLE release() noexcept {
                    const HANDLE result = handle_;
                    handle_ = INVALID_HANDLE_VALUE;
                    return result;
                }

              private:
                HANDLE handle_;
            };

            class ScopedFind {
              public:
                explicit ScopedFind(HANDLE handle) noexcept : handle_(handle) {}
                ScopedFind(const ScopedFind&) = delete;
                ScopedFind& operator=(const ScopedFind&) = delete;
                ~ScopedFind() {
                    if (handle_ != INVALID_HANDLE_VALUE)
                        FindClose(handle_);
                }
                HANDLE get() const noexcept {
                    return handle_;
                }

              private:
                HANDLE handle_;
            };
#endif

            struct ReadBuffer {
                VarianceClockLoadBudget::Reservation charge;
                std::vector<unsigned char> bytes;
            };

            ReadBuffer readCharged(const VarianceClockBundleSource& source,
                                   const std::string& name,
                                   std::size_t maxBytes,
                                   VarianceClockLoadBudget& budget) {
                auto charge = budget.reserve(maxBytes);
                auto bytes = source.read(name, maxBytes);
                QL_REQUIRE(bytes.size() <= maxBytes,
                           "variance-clock source returned more bytes than requested for "
                               << name);
                charge.resize(bytes.capacity());
                return {std::move(charge), std::move(bytes)};
            }

            std::size_t boundedReadSize(std::size_t fileLimit,
                                        std::size_t totalBytes,
                                        const VarianceClockLoadBudget& budget) {
                QL_REQUIRE(totalBytes <= maxBundleBytes,
                           "variance-clock bundle exceeds aggregate size limit");
                return std::min(fileLimit,
                                std::min(maxBundleBytes - totalBytes, budget.remaining()));
            }

            void verifyDigest(std::string_view bytes, const std::string& expected,
                              const std::string& name) {
                VarianceSha256 hash;
                hash.update(bytes);
                QL_REQUIRE(hash.finishHex() == expected,
                           "variance-clock digest mismatch for " << name);
            }

            std::string normalizeRootPath(std::string path) {
#if defined(_WIN32)
                while (path.size() > 3 &&
                       (path.back() == '\\' || path.back() == '/'))
                    path.pop_back();
#else
                while (path.size() > 1 && path.back() == '/')
                    path.pop_back();
#endif
                return path;
            }

            bool hasDotPathComponent(std::string_view path) {
#if defined(_WIN32)
                const auto isSeparator = [](char c) { return c == '\\' || c == '/'; };
                std::size_t position =
                    path.size() >= 2 && path[1] == ':' ? 2U : 0U;
#else
                const auto isSeparator = [](char c) { return c == '/'; };
                std::size_t position = 0;
#endif
                while (position < path.size()) {
                    while (position < path.size() && isSeparator(path[position]))
                        ++position;
                    const std::size_t start = position;
                    while (position < path.size() && !isSeparator(path[position]))
                        ++position;
                    const std::string_view component = path.substr(start, position - start);
                    if (component == "." || component == "..")
                        return true;
                }
                return false;
            }

        } // namespace

        class VarianceClockDirectorySource::Impl {
          public:
            explicit Impl(std::string path) : path_(normalizeRootPath(std::move(path))) {
                QL_REQUIRE(!path_.empty() && path_.find('\0') == std::string::npos,
                           "invalid native variance-clock bundle path");
                QL_REQUIRE(!hasDotPathComponent(path_),
                           "variance-clock bundle root path contains a dot component");
                // Root entries are checked once at construction. B5 must construct this
                // source inside each load call, and callers must not mutate the root during
                // capture; Windows reads still use full paths rather than the opened handle.
#if defined(_WIN32)
                ScopedHandle root(CreateFileA(
                    path_.c_str(), FILE_LIST_DIRECTORY | FILE_READ_ATTRIBUTES,
                    FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr, OPEN_EXISTING,
                    FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, nullptr));
                QL_REQUIRE(root.get() != INVALID_HANDLE_VALUE,
                           "cannot open variance-clock bundle root without following reparse "
                               "points");
                FILE_ATTRIBUTE_TAG_INFO tagInfo;
                QL_REQUIRE(GetFileInformationByHandleEx(root.get(), FileAttributeTagInfo, &tagInfo,
                                                        sizeof(tagInfo)) &&
                               (tagInfo.FileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0 &&
                               (tagInfo.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) == 0,
                           "variance-clock bundle root is not a real directory");
                WIN32_FIND_DATAA data;
                const std::string pattern = path_ + "\\*";
                ScopedFind find(FindFirstFileA(pattern.c_str(), &data));
                QL_REQUIRE(find.get() != INVALID_HANDLE_VALUE,
                           "cannot enumerate variance-clock bundle root");
                do {
                    const std::string_view entry(data.cFileName);
                    if (entry != "." && entry != "..")
                        QL_REQUIRE(isVarianceClockBundleFileName(entry),
                                   "unrecognized variance-clock bundle root entry: " << entry);
                } while (FindNextFileA(find.get(), &data));
                QL_REQUIRE(GetLastError() == ERROR_NO_MORE_FILES,
                           "cannot enumerate variance-clock bundle root");
                handle_ = root.release();
#else
                ScopedFd root(::open(path_.c_str(),
                                     O_RDONLY | O_CLOEXEC | O_DIRECTORY | O_NOFOLLOW));
                QL_REQUIRE(root.get() >= 0,
                           "cannot open variance-clock bundle root without following symlinks");
                struct stat info;
                QL_REQUIRE(::fstat(root.get(), &info) == 0 && S_ISDIR(info.st_mode),
                           "variance-clock bundle root is not a real directory");
                const int duplicate = ::dup(root.get());
                QL_REQUIRE(duplicate >= 0, "cannot enumerate variance-clock bundle root");
                DIR* directory = ::fdopendir(duplicate);
                if (!directory) {
                    ::close(duplicate);
                    QL_FAIL("cannot enumerate variance-clock bundle root");
                }
                const auto closeDirectory = [](DIR* value) { ::closedir(value); };
                std::unique_ptr<DIR, decltype(closeDirectory)> directoryGuard(directory,
                                                                               closeDirectory);
                errno = 0;
                while (const dirent* entry = ::readdir(directoryGuard.get())) {
                    const std::string_view name(entry->d_name);
                    if (name != "." && name != "..")
                        QL_REQUIRE(isVarianceClockBundleFileName(name),
                                   "unrecognized variance-clock bundle root entry: " << name);
                    errno = 0;
                }
                const int readError = errno;
                QL_REQUIRE(readError == 0, "cannot enumerate variance-clock bundle root");
                fd_ = root.release();
#endif
            }

            ~Impl() {
#if defined(_WIN32)
                if (handle_ != INVALID_HANDLE_VALUE)
                    CloseHandle(handle_);
#else
                if (fd_ >= 0)
                    ::close(fd_);
#endif
            }

            std::vector<unsigned char> read(const std::string& name, std::size_t maxBytes) const {
                QL_REQUIRE(isVarianceClockBundleFileName(name),
                           "invalid variance-clock bundle input name");
#if defined(_WIN32)
                const std::string fullPath = path_ + "\\" + name;
                ScopedHandle file(CreateFileA(fullPath.c_str(), GENERIC_READ, FILE_SHARE_READ,
                                              nullptr, OPEN_EXISTING,
                                              FILE_FLAG_OPEN_REPARSE_POINT |
                                                  FILE_FLAG_SEQUENTIAL_SCAN,
                                              nullptr));
                QL_REQUIRE(file.get() != INVALID_HANDLE_VALUE,
                           "cannot open variance-clock bundle input");
                FILE_ATTRIBUTE_TAG_INFO tagInfo;
                QL_REQUIRE(GetFileInformationByHandleEx(file.get(), FileAttributeTagInfo,
                                                        &tagInfo, sizeof(tagInfo)) &&
                               (tagInfo.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) == 0 &&
                               (tagInfo.FileAttributes & FILE_ATTRIBUTE_DIRECTORY) == 0 &&
                               GetFileType(file.get()) == FILE_TYPE_DISK,
                           "variance-clock bundle input is not a regular file");
                LARGE_INTEGER fileSize;
                QL_REQUIRE(GetFileSizeEx(file.get(), &fileSize) && fileSize.QuadPart >= 0 &&
                               static_cast<unsigned long long>(fileSize.QuadPart) <= maxBytes,
                           "variance-clock bundle input exceeds size limit");
                std::vector<unsigned char> bytes(static_cast<std::size_t>(fileSize.QuadPart));
                std::size_t offset = 0;
                while (offset < bytes.size()) {
                    const DWORD chunk = static_cast<DWORD>(
                        std::min<std::size_t>(bytes.size() - offset, MAXDWORD));
                    DWORD received = 0;
                    QL_REQUIRE(
                        ReadFile(file.get(), bytes.data() + offset, chunk, &received, nullptr) &&
                            received != 0,
                               "cannot read variance-clock bundle input");
                    offset += received;
                }
                unsigned char extra;
                DWORD received = 0;
                QL_REQUIRE(!ReadFile(file.get(), &extra, 1, &received, nullptr) || received == 0,
                           "variance-clock bundle input changed during read");
                return bytes;
#else
                ScopedFd file(::openat(fd_, name.c_str(),
                                       O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK));
                QL_REQUIRE(file.get() >= 0, "cannot open variance-clock bundle input safely");
                struct stat info;
                QL_REQUIRE(::fstat(file.get(), &info) == 0 && S_ISREG(info.st_mode) &&
                               info.st_size >= 0 &&
                               static_cast<unsigned long long>(info.st_size) <= maxBytes,
                           "variance-clock bundle input is not a bounded regular file");
                const std::size_t fileSize = static_cast<std::size_t>(info.st_size);
                std::vector<unsigned char> bytes(fileSize);
                std::size_t offset = 0;
                while (offset < fileSize) {
                    const ssize_t received =
                        ::read(file.get(), bytes.data() + offset, fileSize - offset);
                    if (received < 0 && errno == EINTR)
                        continue;
                    QL_REQUIRE(received > 0, "cannot read variance-clock bundle input");
                    offset += static_cast<std::size_t>(received);
                }
                unsigned char extra;
                ssize_t received;
                do {
                    received = ::read(file.get(), &extra, 1);
                } while (received < 0 && errno == EINTR);
                QL_REQUIRE(received == 0, "variance-clock bundle input changed during read");
                return bytes;
#endif
            }

          private:
            std::string path_;
#if defined(_WIN32)
            HANDLE handle_ = INVALID_HANDLE_VALUE;
#else
            int fd_ = -1;
#endif
        };

        VarianceClockDirectorySource::VarianceClockDirectorySource(std::string nativeDirectory)
        : impl_(std::make_unique<Impl>(std::move(nativeDirectory))) {}

        VarianceClockDirectorySource::~VarianceClockDirectorySource() = default;

        std::vector<unsigned char> VarianceClockDirectorySource::read(
            const std::string& flatName, std::size_t maxBytes) const {
            return impl_->read(flatName, maxBytes);
        }

        std::string_view VarianceClockVerifiedBytes::bytes() const noexcept {
            return charView(bytes_);
        }

        const VarianceClockManifest& VarianceClockCapturedBundle::manifest() const noexcept {
            return manifest_;
        }

        VarianceClockBundleCsvBytes VarianceClockCapturedBundle::csvBytes() const noexcept {
            return {profiles_.bytes(), marketDays_.bytes(), sessionSegments_.bytes(),
                    timezoneMapping_.bytes(), slotEvidence_.bytes()};
        }

        bool isVarianceClockBundleFileName(std::string_view name) noexcept {
            if (name == "manifest.json")
                return true;
            return std::any_of(csvNames.begin(), csvNames.end(),
                               [name](const char* candidate) { return name == candidate; });
        }

        VarianceClockCapturedBundle captureVarianceClockBundle(
            const VarianceClockBundleSource& source,
            VarianceClockLoadBudget& budget) {
            QL_REQUIRE(budget.remaining() > 0, "variance-clock load budget is exhausted");
            std::size_t totalBytes = 0;
            VarianceClockManifest manifest;
            {
                const std::size_t maxBytes =
                    boundedReadSize(maxBundleSourceManifestBytes, totalBytes, budget);
                auto rawManifest = readCharged(source, "manifest.json", maxBytes, budget);
                totalBytes += rawManifest.bytes.size();
                manifest = parseVarianceClockManifest(charView(rawManifest.bytes));
            }

            VarianceClockCapturedBundle result;
            result.manifest_ = std::move(manifest);
            const std::array<VarianceClockVerifiedBytes*, 5> destinations{{
                &result.profiles_, &result.marketDays_, &result.sessionSegments_,
                &result.timezoneMapping_, &result.slotEvidence_}};
            for (std::size_t i = 0; i < csvNames.size(); ++i) {
                const std::string name = csvNames[i];
                const std::size_t maxBytes =
                    boundedReadSize(maxBundleSourceCsvBytes, totalBytes, budget);
                auto captured = readCharged(source, name, maxBytes, budget);
                totalBytes += captured.bytes.size();
                const auto expected = result.manifest_.files.find(name);
                QL_REQUIRE(expected != result.manifest_.files.end(),
                           "variance-clock manifest is missing digest for " << name);
                verifyDigest(charView(captured.bytes), expected->second, name);
                destinations[i]->bytes_ = std::move(captured.bytes);
                destinations[i]->charge_ = std::move(captured.charge);
            }
            return result;
        }
    }
}
