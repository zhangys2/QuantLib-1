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
*/

// Self-checking control harness for the standalone variance-clock probe.
//
// Every control runs the tested operation twice: first with hooks unarmed
// (the clean control, which must observe nothing), then with exactly one
// event kind armed before the operation and disarmed immediately after
// (the positive control, which must observe exactly one event).
//
// The executable returns zero only when every control passes.  Built with
// QL_VARIANCECLOCK_PROBE_DISABLED, record() observes nothing and the positive
// controls fail, which is the runtime red for a missing or ineffective hook.

#include "varianceclock_probe.hpp"

#ifdef QL_VARIANCECLOCK_PROBE_CLOCK_CONTROLS
#include <ql/time/varianceclock.hpp>
#endif

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cxxabi.h>
#include <fcntl.h>
#include <fstream>
#include <new>
#include <sys/types.h>
#include <unistd.h>
#include <utility>

namespace vcp = QuantLib::varianceclockprobe;

namespace {

    int failures = 0;
    int controls = 0;

    void reportFailure(const char* event,
                       bool clean,
                       std::uint64_t observed,
                       std::uint64_t observedBytes,
                       std::uint64_t expectedBytes) {
        ++failures;
        std::printf("[FAIL] %-27s clean=%s observed=%llu bytes=%llu "
                    "expected=1/%llu%s\n",
                    event, clean ? "ok" : "unexpected event",
                    static_cast<unsigned long long>(observed),
                    static_cast<unsigned long long>(observedBytes),
                    static_cast<unsigned long long>(expectedBytes),
                    (clean && observed == 0 && observedBytes == 0)
                        ? " -- hook missing or ineffective"
                        : "");
    }

#ifndef QL_VARIANCECLOCK_PROBE_BASE_CONTROLS_ONLY
    void reportCustomFailure(const char* event, const char* reason) {
        ++failures;
        std::printf("[FAIL] %s %s\n", event, reason);
    }
#endif

    template <typename Operation>
    void expectOne(vcp::Event event, std::uint64_t expectedBytes, Operation operation) {
        ++controls;

        // Controls first: hooks are unarmed outside the measured operation,
        // so the clean control must observe nothing.
        vcp::disarmAll();
        vcp::reset();
        vcp::arm(event);
        [] {}();
        vcp::disarm(event);
        const bool armedClean = vcp::count(event) == 0 && vcp::bytes(event) == 0;
        vcp::reset();
        operation();
        const bool clean = armedClean && vcp::count(event) == 0 &&
                           vcp::bytes(event) == 0;

        // Arm exactly one kind, run the operation, disarm immediately.
        vcp::arm(event);
        operation();
        vcp::disarm(event);

        const std::uint64_t observed = vcp::count(event);
        const std::uint64_t observedBytes = vcp::bytes(event);
        if (clean && observed == 1 && observedBytes == expectedBytes) {
            std::printf("[ ok ] %-27s count=1 bytes=%llu\n", vcp::name(event),
                        static_cast<unsigned long long>(observedBytes));
            return;
        }
        reportFailure(vcp::name(event), clean, observed, observedBytes, expectedBytes);
    }

    char* temporaryPath(char* buffer, std::size_t size) {
        const char* directory = std::getenv("TMPDIR");
        if (directory == nullptr || *directory == '\0')
            directory = ".";
        std::snprintf(buffer, size, "%s/quantlib-varianceclock-probe-%ld",
                      directory, static_cast<long>(::getpid()));
        return buffer;
    }

    // The compiler may fold an unobserved malloc/free pair away, and with it
    // the call the probe is supposed to observe.  Calling through a volatile
    // function pointer keeps the call in the object, so the link-time hook is
    // exercised.
    void* (*volatile mallocCall)(std::size_t) = std::malloc;
    void* (*volatile callocCall)(std::size_t, std::size_t) = std::calloc;
    void* (*volatile reallocCall)(void*, std::size_t) = std::realloc;

#ifdef QL_VARIANCECLOCK_PROBE_CLOCK_CONTROLS
    QuantLib::VarianceClockInstant probeClockInstant(std::int64_t seconds) {
        QuantLib::VarianceClockInstant result;
        if (!QuantLib::VarianceClockInstant::tryCreate(seconds, 0, result))
            std::abort();
        return result;
    }

    QuantLib::VarianceClockTables probeClockTables(double weight,
                                                   std::int64_t calibration = 0) {
        QuantLib::VarianceClockTables tables;
        tables.start = probeClockInstant(0);
        tables.end = probeClockInstant(86400);
        tables.availableFrom = probeClockInstant(0);
        QuantLib::VarianceClockProfileInput profile;
        profile.id = 1;
        profile.calibrationAsOf = probeClockInstant(calibration);
        for (auto& slot : profile.slots)
            slot.weight = weight;
        tables.profiles.push_back(std::move(profile));
        tables.dates.push_back({QuantLib::Date(1, QuantLib::January, 1970), 1});
        tables.offsets.push_back({tables.start, tables.end, 0, false});
        return tables;
    }
#endif

} // namespace

int main() {
    char path[256];
    temporaryPath(path, sizeof path);

    std::printf("variance-clock probe: controls-first allocation and I/O checks\n");

    expectOne(vcp::Event::New, 96, [] {
        void* memory = ::operator new(96);
        ::operator delete(memory);
    });

    expectOne(vcp::Event::NewArray, 200, [] {
        void* memory = ::operator new[](200);
        ::operator delete[](memory);
    });

    expectOne(vcp::Event::NewAligned, 128, [] {
        void* memory = ::operator new(128, std::align_val_t(64));
        ::operator delete(memory, std::align_val_t(64));
    });

    expectOne(vcp::Event::NewArrayAligned, 192, [] {
        void* memory = ::operator new[](192, std::align_val_t(64));
        ::operator delete[](memory, std::align_val_t(64));
    });

    expectOne(vcp::Event::NewNothrow, 64, [] {
        void* memory = ::operator new(64, std::nothrow);
        ::operator delete(memory, std::nothrow);
    });

    expectOne(vcp::Event::NewArrayNothrow, 72, [] {
        void* memory = ::operator new[](72, std::nothrow);
        ::operator delete[](memory, std::nothrow);
    });

    expectOne(vcp::Event::NewAlignedNothrow, 88, [] {
        void* memory =
            ::operator new(88, std::align_val_t(64), std::nothrow);
        ::operator delete(memory, std::align_val_t(64), std::nothrow);
    });

    expectOne(vcp::Event::NewArrayAlignedNothrow, 104, [] {
        void* memory =
            ::operator new[](104, std::align_val_t(64), std::nothrow);
        ::operator delete[](memory, std::align_val_t(64), std::nothrow);
    });

    expectOne(vcp::Event::Malloc, 56, [] {
        void* memory = mallocCall(56);
        std::free(memory);
    });

    expectOne(vcp::Event::Calloc, 64, [] {
        void* memory = callocCall(4, 16);
        std::free(memory);
    });

    expectOne(vcp::Event::Realloc, 96, [] {
        void* memory = std::malloc(32);
        memory = reallocCall(memory, 96);
        std::free(memory);
    });

    expectOne(vcp::Event::Exception, 64, [] {
        void* memory = __cxxabiv1::__cxa_allocate_exception(64);
        __cxxabiv1::__cxa_free_exception(memory);
    });

    expectOne(vcp::Event::Open, 0, [&path] {
        const int descriptor = ::open(path, O_CREAT | O_TRUNC | O_RDWR, 0600);
        if (descriptor >= 0)
            ::close(descriptor);
        ::unlink(path);
    });

    expectOne(vcp::Event::Read, 3, [&path] {
        const int descriptor = ::open(path, O_CREAT | O_TRUNC | O_RDWR, 0600);
        if (descriptor < 0)
            return;
        if (::write(descriptor, "abc", 3) == 3) {
            ::lseek(descriptor, 0, SEEK_SET);
            char buffer[3];
            const ssize_t transferred = ::read(descriptor, buffer, sizeof buffer);
            (void)transferred;
        }
        ::close(descriptor);
        ::unlink(path);
    });

    expectOne(vcp::Event::Write, 3, [&path] {
        const int descriptor = ::open(path, O_CREAT | O_TRUNC | O_RDWR, 0600);
        if (descriptor < 0)
            return;
        const ssize_t transferred = ::write(descriptor, "abc", 3);
        (void)transferred;
        ::close(descriptor);
        ::unlink(path);
    });

#ifndef QL_VARIANCECLOCK_PROBE_BASE_CONTROLS_ONLY
    expectOne(vcp::Event::OpenAt, 0, [&path] {
        const int descriptor = ::openat(AT_FDCWD, path,
                                        O_CREAT | O_TRUNC | O_RDWR, 0600);
        if (descriptor >= 0)
            ::close(descriptor);
        ::unlink(path);
    });

    expectOne(vcp::Event::Open64, 0, [&path] {
        const int descriptor = ::open64(path, O_CREAT | O_TRUNC | O_RDWR, 0600);
        if (descriptor >= 0)
            ::close(descriptor);
        ::unlink(path);
    });

    expectOne(vcp::Event::Fopen, 0, [&path] {
        std::FILE* file = std::fopen(path, "w");
        if (file != nullptr)
            std::fclose(file);
        ::unlink(path);
    });

    expectOne(vcp::Event::Fopen64, 0, [&path] {
        std::FILE* file = ::fopen64(path, "w");
        if (file != nullptr)
            std::fclose(file);
        ::unlink(path);
    });

    expectOne(vcp::Event::Fwrite, 3, [&path] {
        std::FILE* file = std::fopen(path, "w");
        if (file != nullptr) {
            std::fwrite("abc", 1, 3, file);
            std::fclose(file);
        }
        ::unlink(path);
    });

    expectOne(vcp::Event::Fread, 3, [&path] {
        std::FILE* file = std::fopen(path, "w+");
        if (file != nullptr) {
            std::fwrite("abc", 1, 3, file);
            std::rewind(file);
            char buffer[3];
            const std::size_t transferred = std::fread(buffer, 1, sizeof buffer, file);
            (void)transferred;
            std::fclose(file);
        }
        ::unlink(path);
    });

    expectOne(vcp::Event::Pwrite, 3, [&path] {
        const int descriptor = ::open(path, O_CREAT | O_TRUNC | O_RDWR, 0600);
        if (descriptor >= 0) {
            const ssize_t transferred = ::pwrite(descriptor, "abc", 3, 0);
            (void)transferred;
            ::close(descriptor);
        }
        ::unlink(path);
    });

    expectOne(vcp::Event::Pread, 3, [&path] {
        const int descriptor = ::open(path, O_CREAT | O_TRUNC | O_RDWR, 0600);
        if (descriptor >= 0) {
            const ssize_t written = ::write(descriptor, "abc", 3);
            (void)written;
            char buffer[3];
            const ssize_t transferred = ::pread(descriptor, buffer, sizeof buffer, 0);
            (void)transferred;
            ::close(descriptor);
        }
        ::unlink(path);
    });

    vcp::disarmAll();
    vcp::reset();
    for (std::size_t i = 0; i < static_cast<std::size_t>(vcp::Event::Count); ++i)
        vcp::arm(static_cast<vcp::Event>(i));
    void* isolated = ::operator new(48);
    ::operator delete(isolated);
    vcp::disarmAll();
    bool onlyNewMoved = vcp::count(vcp::Event::New) == 1;
    for (std::size_t i = 1; i < static_cast<std::size_t>(vcp::Event::Count); ++i)
        onlyNewMoved = onlyNewMoved &&
                       vcp::count(static_cast<vcp::Event>(i)) == 0;
    ++controls;
    if (!onlyNewMoved)
        reportCustomFailure("all-kinds armed control",
                            "moved a counter other than the expected new event");

    vcp::disarmAll();
    vcp::reset();
    const int streamDescriptor = ::open(path, O_CREAT | O_TRUNC | O_WRONLY, 0600);
    if (streamDescriptor >= 0) {
        const ssize_t written = ::write(streamDescriptor, "abc", 3);
        (void)written;
        ::close(streamDescriptor);
    }
    vcp::reset();
    for (std::size_t i = static_cast<std::size_t>(vcp::Event::Open);
         i < static_cast<std::size_t>(vcp::Event::Count);
         ++i)
        vcp::arm(static_cast<vcp::Event>(i));
    std::ifstream stream(path);
    char character = '\0';
    stream.get(character);
    stream.close();
    ++controls;
    const bool streamOpenObserved =
        vcp::count(vcp::Event::Open) + vcp::count(vcp::Event::Open64) +
            vcp::count(vcp::Event::OpenAt) + vcp::count(vcp::Event::Fopen) +
            vcp::count(vcp::Event::Fopen64) >
        0;
    const bool streamReadObserved =
        vcp::count(vcp::Event::Read) + vcp::count(vcp::Event::Pread) +
            vcp::count(vcp::Event::Fread) >
        0;
    if (!streamOpenObserved || !streamReadObserved)
        reportCustomFailure("ifstream positive control",
                            "did not observe both file-open and file-read events");
    ::unlink(path);
#endif

#ifdef QL_VARIANCECLOCK_PROBE_CLOCK_CONTROLS
    QuantLib::VarianceClock clock(
        QuantLib::makeVarianceClockSnapshot(probeClockTables(1.0)));
    const auto oldView = clock.capture();
    QuantLib::VarianceClockExpiryToken oldToken;
    const bool oldTokenReady =
        oldView.prepareExpiry(probeClockInstant(600), oldToken) ==
        QuantLib::VarianceClockStatus::Ok;
    auto candidate = QuantLib::makeVarianceClockSnapshot(probeClockTables(2.0));

    vcp::disarmAll();
    vcp::reset();
    vcp::arm(vcp::Event::New);
    clock.activate(std::move(candidate));
    vcp::disarm(vcp::Event::New);
    ++controls;
    if (vcp::count(vcp::Event::New) > 0) {
        std::printf("[ ok ] clock activation allocation count=%llu\n",
                    static_cast<unsigned long long>(vcp::count(vcp::Event::New)));
    } else {
        ++failures;
        std::printf("[FAIL] clock activation positive control observed no allocation\n");
    }

    QuantLib::VarianceClock beforeCalibrationClock(
        QuantLib::makeVarianceClockSnapshot(probeClockTables(1.0, 10)));
    const auto beforeCalibrationView = beforeCalibrationClock.capture();
    QuantLib::VarianceClockExpiryToken beforeCalibrationToken;
    const bool beforeCalibrationExpiryReady =
        beforeCalibrationView.prepareExpiry(probeClockInstant(600),
                                            beforeCalibrationToken) ==
        QuantLib::VarianceClockStatus::Ok;

    vcp::disarmAll();
    vcp::reset();
    for (std::size_t i = 0; i < static_cast<std::size_t>(vcp::Event::Count); ++i)
        vcp::arm(static_cast<vcp::Event>(i));
    bool queryOk = oldTokenReady;
    {
        const auto view = clock.capture();
        QuantLib::VarianceClockExpiryToken expiry;
        const auto invalidView = QuantLib::VarianceClockView().remaining(
            probeClockInstant(0), expiry);
        const auto invalidToken = view.remaining(probeClockInstant(0), expiry);
        const bool expiryReady =
            view.prepareExpiry(probeClockInstant(600), expiry) ==
            QuantLib::VarianceClockStatus::Ok;
        const auto ok = view.remaining(probeClockInstant(0), expiry);
        const auto stale = view.remaining(probeClockInstant(0), oldToken);
        const auto invalidInstant = view.remaining(QuantLib::VarianceClockInstant(),
                                                   expiry);
        const auto outOfCoverage = view.remaining(probeClockInstant(86401), expiry);
        const auto expired = view.remaining(probeClockInstant(600), expiry);
        const auto beforeCalibration =
            beforeCalibrationView.remaining(probeClockInstant(0),
                                            beforeCalibrationToken);
        queryOk = queryOk &&
                  invalidView.status == QuantLib::VarianceClockStatus::InvalidView &&
                  invalidToken.status == QuantLib::VarianceClockStatus::InvalidToken &&
                  expiryReady && ok.status == QuantLib::VarianceClockStatus::Ok &&
                  stale.status == QuantLib::VarianceClockStatus::StaleToken &&
                  invalidInstant.status == QuantLib::VarianceClockStatus::InvalidInstant &&
                  outOfCoverage.status == QuantLib::VarianceClockStatus::OutOfCoverage &&
                  expired.status == QuantLib::VarianceClockStatus::Expired &&
                  beforeCalibrationExpiryReady &&
                  beforeCalibration.status == QuantLib::VarianceClockStatus::BeforeCalibration;
    }
    vcp::disarmAll();
    bool queryAllocated = false;
    for (std::size_t i = 0; i < static_cast<std::size_t>(vcp::Event::Count); ++i)
        queryAllocated = queryAllocated || vcp::count(static_cast<vcp::Event>(i)) != 0;
    ++controls;
    if (queryOk && !queryAllocated) {
        std::printf("[ ok ] clock capture/query observed no allocation or I/O\n");
    } else {
        reportCustomFailure("clock capture/query",
                            "failed or observed allocation/I/O");
    }
#endif

    if (failures == 0) {
        std::printf("\nAll %d controls passed: clean controls observed nothing, "
                    "positive controls observed exactly one event.\n", controls);
        return 0;
    }

    std::printf("\n%d of %d controls failed.\n", failures, controls);
    return 1;
}