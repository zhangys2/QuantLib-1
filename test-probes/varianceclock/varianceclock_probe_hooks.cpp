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

// Interposers for the standalone variance-clock probe.
//
// Allocation, exception and file-I/O events are observed only when the
// corresponding event kind is armed; otherwise every hook forwards to the
// real implementation with no observable effect.
//
// Allocation:
//   * replaceable scalar/array, aligned and nothrow operator new are defined
//     here, so they replace the library ones process-wide;
//   * malloc, calloc and realloc are intercepted with GNU ld --wrap, which
//     rewrites references from objects linked into this executable only.
//     Calls made inside libc, libstdc++ or another shared object are not
//     rewritten, so this probe cannot observe allocations performed by a
//     separately linked shared library.  Proving that the clock itself does
//     not allocate requires a statically linked clock or a cross-DSO
//     interposer with its own positive control; A1d does not claim that.
//   * __cxa_allocate_exception is intercepted with --wrap as well, again for
//     direct references from this executable only.
// File I/O:
//   * open, read and write are intercepted with --wrap for the same reason.
//
// Define QL_VARIANCECLOCK_PROBE_DISABLED to build the runtime-red binary:
// the interposers still forward, but record() observes nothing, so every
// positive control fails.  That is how the harness proves the controls
// would catch a missing hook.

#include "varianceclock_probe.hpp"

#include <atomic>
#include <cstdarg>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <fcntl.h>
#include <new>
#include <sys/types.h>
#include <unistd.h>

extern "C" {
void* __real_malloc(std::size_t size) noexcept;
void* __real_calloc(std::size_t count, std::size_t size) noexcept;
void* __real_realloc(void* memory, std::size_t size) noexcept;
int __real_open(const char* path, int flags, ...) noexcept;
ssize_t __real_read(int descriptor, void* buffer, std::size_t size) noexcept;
ssize_t __real_write(int descriptor, const void* buffer, std::size_t size) noexcept;
void* __real___cxa_allocate_exception(std::size_t size) noexcept;
}

namespace QuantLib {
namespace varianceclockprobe {

    namespace {

        constexpr std::size_t N = numEvents;

        std::atomic<std::uint8_t> armed_[N];
        std::atomic<std::uint64_t> count_[N];
        std::atomic<std::uint64_t> bytes_[N];

        bool valid(Event event) noexcept {
            return static_cast<std::size_t>(event) < N;
        }

        std::size_t index(Event event) noexcept {
            return static_cast<std::size_t>(event);
        }

    } // namespace

    void arm(Event event) noexcept {
        if (valid(event))
            armed_[index(event)].store(std::uint8_t(1), std::memory_order_relaxed);
    }

    void disarm(Event event) noexcept {
        if (valid(event))
            armed_[index(event)].store(std::uint8_t(0), std::memory_order_relaxed);
    }

    void disarmAll() noexcept {
        for (std::size_t i = 0; i < N; ++i)
            armed_[i].store(std::uint8_t(0), std::memory_order_relaxed);
    }

    void reset() noexcept {
        for (std::size_t i = 0; i < N; ++i) {
            count_[i].store(std::uint64_t(0), std::memory_order_relaxed);
            bytes_[i].store(std::uint64_t(0), std::memory_order_relaxed);
        }
    }

    std::uint64_t count(Event event) noexcept {
        return valid(event) ? count_[index(event)].load(std::memory_order_relaxed)
                            : std::uint64_t(0);
    }

    std::uint64_t bytes(Event event) noexcept {
        return valid(event) ? bytes_[index(event)].load(std::memory_order_relaxed)
                            : std::uint64_t(0);
    }

    void record(Event event, std::size_t size) noexcept {
#ifdef QL_VARIANCECLOCK_PROBE_DISABLED
        (void)event;
        (void)size;
#else
        if (!valid(event))
            return;
        const std::size_t i = index(event);
        if (armed_[i].load(std::memory_order_relaxed) == 0)
            return;
        count_[i].fetch_add(std::uint64_t(1), std::memory_order_relaxed);
        if (size != 0) {
            const std::uint64_t increment = size;
            const std::uint64_t previous =
                bytes_[i].load(std::memory_order_relaxed);
            const std::uint64_t next = previous + increment;
            bytes_[i].store(next < previous ? UINT64_MAX : next,
                            std::memory_order_relaxed);
        }
#endif
    }

    const char* name(Event event) noexcept {
        switch (event) {
            case Event::New:                    return "new";
            case Event::NewArray:               return "new[]";
            case Event::NewAligned:             return "new(align)";
            case Event::NewArrayAligned:        return "new[](align)";
            case Event::NewNothrow:             return "new(nothrow)";
            case Event::NewArrayNothrow:        return "new[](nothrow)";
            case Event::NewAlignedNothrow:      return "new(align,nothrow)";
            case Event::NewArrayAlignedNothrow: return "new[](align,nothrow)";
            case Event::Malloc:                 return "malloc";
            case Event::Calloc:                 return "calloc";
            case Event::Realloc:                return "realloc";
            case Event::Exception:              return "__cxa_allocate_exception";
            case Event::Open:                   return "open";
            case Event::Read:                   return "read";
            case Event::Write:                  return "write";
            case Event::Count:                  break;
        }
        return "unknown";
    }

} // namespace varianceclockprobe
} // namespace QuantLib

// Replaceable allocation functions ---------------------------------------

void* operator new(std::size_t size) {
    void* memory = __real_malloc(size);
    if (memory == nullptr)
        throw std::bad_alloc();
    QuantLib::varianceclockprobe::record(
        QuantLib::varianceclockprobe::Event::New, size);
    return memory;
}

void* operator new[](std::size_t size) {
    void* memory = __real_malloc(size);
    if (memory == nullptr)
        throw std::bad_alloc();
    QuantLib::varianceclockprobe::record(
        QuantLib::varianceclockprobe::Event::NewArray, size);
    return memory;
}

void* operator new(std::size_t size, const std::nothrow_t&) noexcept {
    void* memory = __real_malloc(size);
    if (memory != nullptr)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::NewNothrow, size);
    return memory;
}

void* operator new[](std::size_t size, const std::nothrow_t&) noexcept {
    void* memory = __real_malloc(size);
    if (memory != nullptr)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::NewArrayNothrow, size);
    return memory;
}

namespace {

    void* alignedAllocate(std::size_t size, std::align_val_t alignment) noexcept {
        const std::size_t requested = static_cast<std::size_t>(alignment);
        void* memory = nullptr;
        // The compiler only selects the aligned overload for alignments
        // greater than __STDCPP_DEFAULT_NEW_ALIGNMENT__, which always
        // satisfy posix_memalign's power-of-two and multiple-of-pointer
        // requirements.
        if (::posix_memalign(&memory, requested, size) != 0)
            memory = nullptr;
        return memory;
    }

} // namespace

void* operator new(std::size_t size, std::align_val_t alignment) {
    void* memory = alignedAllocate(size, alignment);
    if (memory == nullptr)
        throw std::bad_alloc();
    QuantLib::varianceclockprobe::record(
        QuantLib::varianceclockprobe::Event::NewAligned, size);
    return memory;
}

void* operator new[](std::size_t size, std::align_val_t alignment) {
    void* memory = alignedAllocate(size, alignment);
    if (memory == nullptr)
        throw std::bad_alloc();
    QuantLib::varianceclockprobe::record(
        QuantLib::varianceclockprobe::Event::NewArrayAligned, size);
    return memory;
}

void* operator new(std::size_t size,
                   std::align_val_t alignment,
                   const std::nothrow_t&) noexcept {
    void* memory = alignedAllocate(size, alignment);
    if (memory != nullptr)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::NewAlignedNothrow, size);
    return memory;
}

void* operator new[](std::size_t size,
                     std::align_val_t alignment,
                     const std::nothrow_t&) noexcept {
    void* memory = alignedAllocate(size, alignment);
    if (memory != nullptr)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::NewArrayAlignedNothrow, size);
    return memory;
}

// Replaceable deallocation functions -------------------------------------

void operator delete(void* memory) noexcept {
    std::free(memory);
}

void operator delete[](void* memory) noexcept {
    std::free(memory);
}

void operator delete(void* memory, std::size_t) noexcept {
    std::free(memory);
}

void operator delete[](void* memory, std::size_t) noexcept {
    std::free(memory);
}

void operator delete(void* memory, std::align_val_t) noexcept {
    std::free(memory);
}

void operator delete[](void* memory, std::align_val_t) noexcept {
    std::free(memory);
}

void operator delete(void* memory, std::size_t, std::align_val_t) noexcept {
    std::free(memory);
}

void operator delete[](void* memory, std::size_t, std::align_val_t) noexcept {
    std::free(memory);
}

// GNU ld --wrap interposers ----------------------------------------------

extern "C" void* __wrap_malloc(std::size_t size) noexcept {
    void* memory = __real_malloc(size);
    if (memory != nullptr)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::Malloc, size);
    return memory;
}

extern "C" void* __wrap_calloc(std::size_t count, std::size_t size) noexcept {
    void* memory = __real_calloc(count, size);
    if (memory != nullptr) {
        const std::size_t total = count != 0 && size > SIZE_MAX / count
                                      ? SIZE_MAX
                                      : count * size;
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::Calloc, total);
    }
    return memory;
}

extern "C" void* __wrap_realloc(void* memory, std::size_t size) noexcept {
    void* resized = __real_realloc(memory, size);
    if (resized != nullptr)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::Realloc, size);
    return resized;
}

extern "C" int __wrap_open(const char* path, int flags, ...) noexcept {
    mode_t mode = 0;
    if ((flags & O_CREAT) != 0 || (flags & O_TMPFILE) != 0) {
        va_list arguments;
        va_start(arguments, flags);
        mode = static_cast<mode_t>(va_arg(arguments, int));
        va_end(arguments);
    }
    const int descriptor = __real_open(path, flags, mode);
    if (descriptor >= 0)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::Open, 0);
    return descriptor;
}

extern "C" ssize_t __wrap_read(int descriptor,
                               void* buffer,
                               std::size_t size) noexcept {
    const ssize_t transferred = __real_read(descriptor, buffer, size);
    if (transferred > 0)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::Read,
            static_cast<std::size_t>(transferred));
    return transferred;
}

extern "C" ssize_t __wrap_write(int descriptor,
                                const void* buffer,
                                std::size_t size) noexcept {
    const ssize_t transferred = __real_write(descriptor, buffer, size);
    if (transferred > 0)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::Write,
            static_cast<std::size_t>(transferred));
    return transferred;
}

extern "C" void* __wrap___cxa_allocate_exception(std::size_t size) noexcept {
    void* memory = __real___cxa_allocate_exception(size);
    if (memory != nullptr)
        QuantLib::varianceclockprobe::record(
            QuantLib::varianceclockprobe::Event::Exception, size);
    return memory;
}