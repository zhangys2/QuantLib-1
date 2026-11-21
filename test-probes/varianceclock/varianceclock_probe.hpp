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

#ifndef quantlib_varianceclock_probe_hpp
#define quantlib_varianceclock_probe_hpp

#include <cstddef>
#include <cstdint>

namespace QuantLib {
namespace varianceclockprobe {

    //! Events the standalone variance-clock probe can observe.
    //! The enumerator order is also the storage order.
    enum class Event : std::uint8_t {
        New = 0,                //!< scalar operator new
        NewArray,               //!< operator new[]
        NewAligned,             //!< scalar aligned operator new
        NewArrayAligned,        //!< aligned operator new[]
        NewNothrow,             //!< nothrow scalar operator new
        NewArrayNothrow,        //!< nothrow operator new[]
        NewAlignedNothrow,      //!< nothrow aligned scalar operator new
        NewArrayAlignedNothrow, //!< nothrow aligned operator new[]
        Malloc,                 //!< C malloc
        Calloc,                 //!< C calloc
        Realloc,                //!< C realloc
        Exception,              //!< __cxa_allocate_exception
        Open,                   //!< open
        Open64,                 //!< open64
        OpenAt,                 //!< openat
        Fopen,                  //!< fopen
        Fopen64,                //!< fopen64
        Read,                   //!< read
        Pread,                  //!< pread
        Write,                  //!< write
        Pwrite,                 //!< pwrite
        Fread,                  //!< fread
        Fwrite,                 //!< fwrite
        Count,                  //!< sentinel, not an event
    };

    constexpr std::size_t numEvents = static_cast<std::size_t>(Event::Count);

    //! Arms one event kind. Hooks observe nothing unless armed.
    void arm(Event event) noexcept;

    //! Disarms one event kind.
    void disarm(Event event) noexcept;

    //! Disarms every event kind. Hooks are unarmed by default.
    void disarmAll() noexcept;

    //! Clears every counter. Call only while hooks are unarmed.
    void reset() noexcept;

    //! Number of observed events of the given kind.
    std::uint64_t count(Event event) noexcept;

    //! Observed bytes of the given kind (zero for open and exceptions).
    std::uint64_t bytes(Event event) noexcept;

    //! Records one event. A no-op when the kind is unarmed. Hooks call this.
    void record(Event event, std::size_t bytes) noexcept;

    //! Human-readable event name.
    const char* name(Event event) noexcept;

    //! Count deletes on the calling thread until stopDeleteCounting().
    void startDeleteCounting() noexcept;

    //! Stop counting and return deletes observed on the calling thread.
    std::size_t stopDeleteCounting() noexcept;

    //! Records one delete when counting is enabled on the calling thread.
    void recordDelete() noexcept;

} // namespace varianceclockprobe
} // namespace QuantLib

#endif
