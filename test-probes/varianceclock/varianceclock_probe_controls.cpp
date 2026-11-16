/* -*- mode: c++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/*
 Copyright (C) 2024 QuantLib contributors

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

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cxxabi.h>
#include <fcntl.h>
#include <new>
#include <sys/types.h>
#include <unistd.h>

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

    template <typename Operation>
    void expectOne(vcp::Event event, std::uint64_t expectedBytes, Operation operation) {
        ++controls;

        // Controls first: hooks are unarmed outside the measured operation,
        // so the clean control must observe nothing.
        vcp::disarmAll();
        vcp::reset();
        operation();
        const bool clean = vcp::count(event) == 0 && vcp::bytes(event) == 0;

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
        memory = std::realloc(memory, 96);
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

    if (failures == 0) {
        std::printf("\nAll %d controls passed: clean controls observed nothing, "
                    "positive controls observed exactly one event.\n", controls);
        return 0;
    }

    std::printf("\n%d of %d controls failed.\n", failures, controls);
    return 1;
}