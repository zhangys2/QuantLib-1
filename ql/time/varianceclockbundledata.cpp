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

#include <ql/time/varianceclockbundledata.hpp>
#include <ql/time/varianceclockcsv.hpp>
#include <ql/errors.hpp>
#include <algorithm>
#include <array>
#include <charconv>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <limits>
#include <locale>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <string_view>
#include <tuple>
#include <type_traits>
#include <utility>
#include <vector>

namespace QuantLib {
    namespace detail {
        namespace {

            using Fields =
                std::vector<std::array<std::string, VarianceClockSlotEvidenceCsv::columnCount>>;

            void addCharge(VarianceClockLoadBudget::Reservation& charge, std::size_t bytes) {
                QL_REQUIRE(bytes <= std::numeric_limits<std::size_t>::max() - charge.bytes(),
                           "variance-clock load accounting overflow");
                charge.resize(charge.bytes() + bytes);
            }

            struct RowCount {
                std::size_t value = 0;
            };

            bool countRow(void* opaque, const std::string_view*, std::size_t) {
                ++static_cast<RowCount*>(opaque)->value;
                return true;
            }

            std::size_t countRows(std::string_view bytes,
                                  VarianceClockCsvSchema schema,
                                  VarianceClockLoadBudget& budget) {
                if (schema == VarianceClockCsvSchema::SessionSegments)
                    budget.recordSessionSegmentsScan();
                else if (schema == VarianceClockCsvSchema::SlotEvidence)
                    budget.recordSlotEvidenceScan();
                RowCount rows;
                QL_REQUIRE(visitVarianceClockCsvRows(bytes, schema, &rows, countRow),
                           "variance-clock CSV row visitor stopped unexpectedly");
                return rows.value;
            }

            struct RowContext {
                Fields* rows;
            };

            bool saveRow(void* opaque, const std::string_view* fields, std::size_t count) {
                auto& context = *static_cast<RowContext*>(opaque);
                std::array<std::string, VarianceClockSlotEvidenceCsv::columnCount> row;
                for (std::size_t i = 0; i < count; ++i)
                    row[i] = decodeVarianceClockCsvField(fields[i]);
                context.rows->push_back(std::move(row));
                return true;
            }

            Fields readRows(std::string_view bytes,
                            VarianceClockCsvSchema schema,
                            VarianceClockLoadBudget& budget,
                            VarianceClockLoadBudget::Reservation& rowCharge) {
                const std::size_t count = countRows(bytes, schema, budget);
                constexpr std::size_t rowOverheadPerField = 8;
                const auto format = varianceClockCsvFormat(schema);
                QL_REQUIRE(format.columnCount != 0, "unknown variance-clock CSV schema");
                const std::size_t perRow =
                    sizeof(std::array<std::string, VarianceClockSlotEvidenceCsv::columnCount>) +
                    format.columnCount * rowOverheadPerField;
                QL_REQUIRE(count <= (std::numeric_limits<std::size_t>::max() - bytes.size()) /
                                        perRow,
                           "variance-clock CSV accounting overflow");
                rowCharge = budget.reserve(bytes.size() + count * perRow);
                Fields rows;
                rows.reserve(count);
                RowContext context{&rows};
                if (schema == VarianceClockCsvSchema::SessionSegments)
                    budget.recordSessionSegmentsScan();
                else if (schema == VarianceClockCsvSchema::SlotEvidence)
                    budget.recordSlotEvidenceScan();
                QL_REQUIRE(visitVarianceClockCsvRows(bytes, schema, &context, saveRow),
                           "variance-clock CSV row visitor stopped unexpectedly");
                QL_ENSURE(rows.size() == count, "variance-clock CSV row count changed");
                return rows;
            }

            template <class T>
            T unsignedInteger(std::string_view value, const char* name) {
                QL_REQUIRE(!value.empty() && (value == "0" || value.front() != '0'),
                           "invalid canonical unsigned integer in " << name);
                for (char c : value)
                    QL_REQUIRE(c >= '0' && c <= '9',
                               "invalid canonical unsigned integer in " << name);
                T result = 0;
                const auto parsed = std::from_chars(value.data(), value.data() + value.size(),
                                                    result);
                QL_REQUIRE(parsed.ec == std::errc() && parsed.ptr == value.data() + value.size(),
                           "unsigned integer out of range in " << name);
                return result;
            }

            std::int32_t signedInt32(std::string_view value) {
                QL_REQUIRE(!value.empty(), "empty signed integer");
                std::size_t position = value.front() == '-' ? 1U : 0U;
                QL_REQUIRE(position < value.size(), "invalid canonical signed integer");
                if (value[position] == '0') {
                    QL_REQUIRE(position + 1 == value.size() && position == 0,
                               "invalid canonical signed integer");
                } else {
                    QL_REQUIRE(value[position] >= '1' && value[position] <= '9',
                               "invalid canonical signed integer");
                    ++position;
                    for (; position < value.size(); ++position)
                        QL_REQUIRE(value[position] >= '0' && value[position] <= '9',
                                   "invalid canonical signed integer");
                }
                std::int32_t result = 0;
                const auto parsed = std::from_chars(value.data(), value.data() + value.size(),
                                                    result);
                QL_REQUIRE(parsed.ec == std::errc() && parsed.ptr == value.data() + value.size() &&
                               !(value.size() > 1 && value.front() == '-' && value[1] == '0'),
                           "invalid canonical signed integer");
                return result;
            }

            bool isDecimalGrammar(std::string_view value) {
                std::size_t position = value.front() == '-' ? 1U : 0U;
                if (position == value.size())
                    return false;
                if (value[position] == '0') {
                    ++position;
                } else if (value[position] >= '1' && value[position] <= '9') {
                    do {
                        ++position;
                    } while (position < value.size() && value[position] >= '0' &&
                             value[position] <= '9');
                } else {
                    return false;
                }
                if (position < value.size() && value[position] == '.') {
                    ++position;
                    const std::size_t fractionStart = position;
                    while (position < value.size() && value[position] >= '0' &&
                           value[position] <= '9')
                        ++position;
                    if (position == fractionStart)
                        return false;
                }
                if (position < value.size() && (value[position] == 'e' || value[position] == 'E')) {
                    ++position;
                    if (position < value.size() && (value[position] == '+' || value[position] == '-'))
                        ++position;
                    const std::size_t exponentStart = position;
                    while (position < value.size() && value[position] >= '0' &&
                           value[position] <= '9')
                        ++position;
                    if (position == exponentStart)
                        return false;
                }
                return position == value.size();
            }

            template <class T, class = void>
            struct DecimalConverter {
                static bool parse(std::string_view value, T& result) {
                    std::istringstream input{std::string(value)};
                    input.imbue(std::locale::classic());
                    input >> std::noskipws >> result;
                    if (input.fail() || !input.eof())
                        return false;

                    for (char c : value) {
                        if (c == 'e' || c == 'E')
                            break;
                        if (c >= '1' && c <= '9')
                            return result != 0.0;
                    }
                    return true;
                }
            };

            template <class T>
            struct DecimalConverter<
                T, std::void_t<decltype(std::from_chars(std::declval<const char*>(),
                                                        std::declval<const char*>(),
                                                        std::declval<T&>()))>> {
                static bool parse(std::string_view value, T& result) {
                    const auto parsed =
                        std::from_chars(value.data(), value.data() + value.size(), result);
                    return parsed.ec == std::errc() && parsed.ptr == value.data() + value.size();
                }
            };

            double decimal(std::string_view value, const char* name) {
                QL_REQUIRE(!value.empty(), "empty decimal in " << name);
                QL_REQUIRE(isDecimalGrammar(value), "invalid decimal grammar in " << name);
                double result = 0.0;
                QL_REQUIRE(DecimalConverter<double>::parse(value, result) &&
                               std::isfinite(result) && result >= 0.0,
                           "invalid nonnegative decimal in " << name);
                return result;
            }

            void validateIdentifier(std::string_view value, const char* name) {
                validateVarianceClockIdentifier(value, name);
            }

            bool leapYear(int year) {
                return year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
            }

            int monthLength(int year, int month) {
                static const int days[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
                return month == 2 ? days[1] + leapYear(year) : days[month - 1];
            }

            std::int64_t daysFromCivil(int year, unsigned int month, unsigned int day) {
                year -= month <= 2;
                const int era = (year >= 0 ? year : year - 399) / 400;
                const unsigned int yoe = static_cast<unsigned int>(year - era * 400);
                const unsigned int adjustedMonth = month > 2 ? month - 3 : month + 9;
                const unsigned int doy = (153 * adjustedMonth + 2) / 5 + day - 1;
                const unsigned int doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
                return static_cast<std::int64_t>(era) * 146097 + doe - 719468;
            }

            int fixedDigits(std::string_view text, std::size_t offset, std::size_t count) {
                QL_REQUIRE(offset + count <= text.size(), "invalid UTC timestamp");
                int value = 0;
                for (std::size_t i = offset; i < offset + count; ++i) {
                    QL_REQUIRE(text[i] >= '0' && text[i] <= '9', "invalid UTC timestamp");
                    value = value * 10 + text[i] - '0';
                }
                return value;
            }

            Date parseDate(std::string_view text,
                           const char* errorMessage = "invalid Gregorian date") {
                QL_REQUIRE(text.size() == 10 && text[4] == '-' && text[7] == '-',
                           errorMessage);
                const int year = fixedDigits(text, 0, 4);
                const int month = fixedDigits(text, 5, 2);
                const int day = fixedDigits(text, 8, 2);
                QL_REQUIRE(year > 0 && month >= 1 && month <= 12 && day >= 1 &&
                               day <= monthLength(year, month),
                           errorMessage);
                const Date result(day, static_cast<Month>(month), year);
                QL_REQUIRE(result >= Date::minDate() && result <= Date::maxDate(),
                           "date is outside QuantLib range");
                return result;
            }

            VarianceClockInstant parseInstant(
                std::string_view text,
                const char* dateErrorMessage = "invalid Gregorian date") {
                QL_REQUIRE(text.size() >= 20 && text[4] == '-' && text[7] == '-' &&
                               text[10] == 'T' && text[13] == ':' && text[16] == ':',
                           "invalid strict UTC timestamp");
                const Date date = parseDate(text.substr(0, 10), dateErrorMessage);
                const int hour = fixedDigits(text, 11, 2);
                const int minute = fixedDigits(text, 14, 2);
                const int second = fixedDigits(text, 17, 2);
                QL_REQUIRE(hour < 24 && minute < 60 && second < 60,
                           "invalid UTC time");
                std::uint32_t nanos = 0;
                std::size_t pos = 19;
                if (pos < text.size() && text[pos] == '.') {
                    ++pos;
                    const std::size_t start = pos;
                    unsigned int digits = 0;
                    while (pos < text.size() && text[pos] >= '0' && text[pos] <= '9' &&
                           digits < 9) {
                        nanos = nanos * 10 + static_cast<unsigned int>(text[pos++] - '0');
                        ++digits;
                    }
                    QL_REQUIRE(digits > 0 && (pos == text.size() || text[pos] == 'Z'),
                               "invalid UTC fractional seconds");
                    for (; digits < 9; ++digits)
                        nanos *= 10;
                    QL_REQUIRE(pos > start, "invalid UTC fractional seconds");
                }
                QL_REQUIRE(pos + 1 == text.size() && text[pos] == 'Z',
                           "UTC timestamp must end with Z");
                const std::int64_t seconds =
                    (static_cast<std::int64_t>(date.serialNumber() - Date(1, January, 1970)
                                                                        .serialNumber()) *
                         86400) +
                    hour * 3600 + minute * 60 + second;
                VarianceClockInstant result;
                QL_REQUIRE(VarianceClockInstant::tryCreate(seconds, nanos, result),
                           "invalid UTC instant");
                return result;
            }

            struct ProfileRows {
                VarianceClockProfileInput profile;
                std::array<bool, 288> filled{};
            };

        } // namespace

        VarianceClockInstant parseVarianceClockInstant(std::string_view text) {
            return parseInstant(text, "invalid UTC date");
        }

        VarianceClockLoadBudget::Reservation::Reservation(
            VarianceClockLoadBudget* budget, std::size_t bytes) noexcept
        : budget_(budget), bytes_(bytes) {}

        VarianceClockLoadBudget::Reservation::Reservation(Reservation&& other) noexcept
        : budget_(other.budget_), bytes_(other.bytes_) {
            other.budget_ = nullptr;
            other.bytes_ = 0;
        }

        VarianceClockLoadBudget::Reservation&
        VarianceClockLoadBudget::Reservation::operator=(Reservation&& other) noexcept {
            if (this != &other) {
                release();
                budget_ = other.budget_;
                bytes_ = other.bytes_;
                other.budget_ = nullptr;
                other.bytes_ = 0;
            }
            return *this;
        }

        VarianceClockLoadBudget::Reservation::~Reservation() {
            release();
        }

        std::size_t VarianceClockLoadBudget::Reservation::bytes() const noexcept {
            return bytes_;
        }

        void VarianceClockLoadBudget::Reservation::resize(std::size_t bytes) {
            QL_REQUIRE(budget_, "cannot resize a released load-budget reservation");
            if (bytes > bytes_)
                budget_->increase(bytes - bytes_);
            else
                budget_->decrease(bytes_ - bytes);
            bytes_ = bytes;
        }

        void VarianceClockLoadBudget::Reservation::release() noexcept {
            if (budget_) {
                budget_->decrease(bytes_);
                budget_ = nullptr;
                bytes_ = 0;
            }
        }

        VarianceClockLoadBudget::VarianceClockLoadBudget(std::size_t limit)
        : limit_(limit) {}

        VarianceClockLoadBudget::Reservation VarianceClockLoadBudget::reserve(std::size_t bytes) {
            increase(bytes);
            return Reservation(this, bytes);
        }

        std::size_t VarianceClockLoadBudget::limit() const noexcept {
            return limit_;
        }

        std::size_t VarianceClockLoadBudget::used() const noexcept {
            return used_;
        }

        std::size_t VarianceClockLoadBudget::remaining() const noexcept {
            return limit() - used();
        }

        const VarianceClockBundleScanCounts&
        VarianceClockLoadBudget::scanCounts() const noexcept {
            return scanCounts_;
        }

        void VarianceClockLoadBudget::recordSessionSegmentsScan() noexcept {
            ++scanCounts_.sessionSegments;
        }

        void VarianceClockLoadBudget::recordSlotEvidenceScan() noexcept {
            ++scanCounts_.slotEvidence;
        }

        void VarianceClockLoadBudget::increase(std::size_t bytes) {
            QL_REQUIRE(bytes <= remaining(), "variance-clock load exceeds size limit");
            used_ += bytes;
        }

        void VarianceClockLoadBudget::decrease(std::size_t bytes) noexcept {
            used_ -= bytes;
        }

        ParsedVarianceClockTables& ParsedVarianceClockTables::operator=(
            ParsedVarianceClockTables&& other) noexcept {
            if (this != &other) {
                profiles = std::move(other.profiles);
                dates = std::move(other.dates);
                offsets = std::move(other.offsets);
                start = other.start;
                end = other.end;
                storageCharge = std::move(other.storageCharge);
            }
            return *this;
        }

        ParsedVarianceClockTables parseVarianceClockBundleData(
            const VarianceClockManifest& manifest,
            const VarianceClockBundleCsvBytes& csv,
            VarianceClockLoadBudget& budget) {
            constexpr std::size_t maxCsvBytes = 32U * 1024U * 1024U;
            QL_REQUIRE(csv.profiles.size() <= maxCsvBytes &&
                           csv.marketDays.size() <= maxCsvBytes &&
                           csv.sessionSegments.size() <= maxCsvBytes &&
                           csv.timezoneMapping.size() <= maxCsvBytes &&
                           csv.slotEvidence.size() <= maxCsvBytes,
                       "variance-clock CSV exceeds size limit");
            ParsedVarianceClockTables result;
            result.start = manifest.coverageStartUtc;
            result.end = manifest.coverageEndUtc;
            QL_REQUIRE(result.start < result.end, "variance-clock coverage is empty");

            auto profileRowsCharge = budget.reserve(0);
            auto dateRowsCharge = budget.reserve(0);
            auto sessionRowsCharge = budget.reserve(0);
            auto timezoneRowsCharge = budget.reserve(0);
            const auto profileRows = readRows(csv.profiles, VarianceClockCsvSchema::Profiles,
                                              budget, profileRowsCharge);
            const auto dateRows = readRows(csv.marketDays, VarianceClockCsvSchema::MarketDays,
                                           budget, dateRowsCharge);
            const auto sessionRows =
                readRows(csv.sessionSegments, VarianceClockCsvSchema::SessionSegments,
                         budget, sessionRowsCharge);
            const auto timezoneRows =
                readRows(csv.timezoneMapping, VarianceClockCsvSchema::TimezoneMapping,
                         budget, timezoneRowsCharge);

            auto profileCharge = budget.reserve(0);
            std::map<std::uint32_t, ProfileRows> profiles;
            for (const auto& row : profileRows) {
                const auto id = unsignedInteger<std::uint32_t>(
                    row[VarianceClockProfilesCsv::profileId], "profile_id");
                const auto minute = unsignedInteger<std::uint16_t>(
                    row[VarianceClockProfilesCsv::minuteOfDay], "minute_of_day");
                QL_REQUIRE(minute < 1440 && minute % 5 == 0,
                           "profile minute is outside five-minute grid");
                auto entry = profiles.find(id);
                if (entry == profiles.end()) {
                    addCharge(profileCharge, sizeof(ProfileRows) + 4U * sizeof(void*));
                    entry = profiles.emplace(id, ProfileRows{}).first;
                }
                auto& profile = entry->second;
                profile.profile.id = id;
                const std::size_t slot = minute / 5;
                QL_REQUIRE(!profile.filled[slot], "duplicate profile slot");
                const double variance = decimal(row[VarianceClockProfilesCsv::variancePer5m],
                                                "variance_per_5m");
                const double weight =
                    decimal(row[VarianceClockProfilesCsv::weight], "weight");
                const double reference = decimal(manifest.referenceVariancePer5m,
                                                 "reference_variance_per_5m");
                QL_REQUIRE(reference > 0.0, "reference variance must be positive");
                const double expected = variance / reference;
                QL_REQUIRE((variance == 0.0 && weight == 0.0) ||
                               (variance > 0.0 && weight > 0.0 &&
                                std::abs(weight / expected - 1.0) <= 1.0e-12),
                           "profile weight does not match variance rate");
                profile.profile.slots[slot].weight = weight;
                profile.filled[slot] = true;
            }
            QL_REQUIRE(!profiles.empty(), "profiles table is empty");
            std::map<std::uint32_t, VarianceClockInstant> calibrations;
            auto calibrationCharge = budget.reserve(0);
            for (const auto& calibration : manifest.profileCalibrations) {
                addCharge(calibrationCharge, sizeof(decltype(calibrations)::value_type) +
                                                 4U * sizeof(void*));
                QL_REQUIRE(calibrations.emplace(calibration.profileId,
                                                calibration.calibrationAsOfUtc).second,
                           "duplicate profile calibration");
            }
            const std::size_t maxRetained =
                profiles.size() * sizeof(VarianceClockProfileInput) +
                dateRows.size() * sizeof(VarianceClockDateInput) +
                timezoneRows.size() * sizeof(VarianceClockOffsetInput);
            result.storageCharge = budget.reserve(maxRetained);
            result.profiles.reserve(profiles.size());
            result.dates.reserve(dateRows.size());
            result.offsets.reserve(timezoneRows.size());
            for (auto& entry : profiles) {
                QL_REQUIRE(std::all_of(entry.second.filled.begin(), entry.second.filled.end(),
                                       [](bool value) { return value; }),
                           "profile is missing one or more slots");
                const auto calibration = calibrations.find(entry.first);
                QL_REQUIRE(calibration != calibrations.end(), "missing profile calibration");
                entry.second.profile.calibrationAsOf = calibration->second;
                result.profiles.push_back(std::move(entry.second.profile));
            }
            QL_REQUIRE(calibrations.size() == profiles.size(),
                       "manifest contains an unreferenced profile calibration");
            profiles.clear();
            profileCharge.release();
            calibrations.clear();
            calibrationCharge.release();

            using PairKey = std::pair<std::uint32_t, std::string>;
            std::set<PairKey> selectedPairs;
            std::set<std::string> marketDates;
            std::set<std::uint32_t> selectedProfiles;
            auto tableIndexCharge = budget.reserve(0);
            for (const auto& row : dateRows) {
                const Date date = parseDate(row[VarianceClockMarketDaysCsv::localDate]);
                QL_REQUIRE(row[VarianceClockMarketDaysCsv::isOpen] == "true" ||
                               row[VarianceClockMarketDaysCsv::isOpen] == "false",
                           "invalid is_open value");
                QL_REQUIRE(row[VarianceClockMarketDaysCsv::dateType] == "full_day" ||
                               row[VarianceClockMarketDaysCsv::dateType] == "early_close" ||
                               row[VarianceClockMarketDaysCsv::dateType] == "holiday" ||
                               row[VarianceClockMarketDaysCsv::dateType] == "weekend" ||
                               row[VarianceClockMarketDaysCsv::dateType] == "special",
                           "invalid market date type");
                const auto id = unsignedInteger<std::uint32_t>(
                    row[VarianceClockMarketDaysCsv::profileId], "profile_id");
                const auto profile =
                    std::lower_bound(result.profiles.begin(), result.profiles.end(), id,
                                     [](const auto& item, std::uint32_t profileId) {
                                         return item.id < profileId;
                                     });
                QL_REQUIRE(profile != result.profiles.end() && profile->id == id,
                           "market day references unknown profile");
                validateIdentifier(row[VarianceClockMarketDaysCsv::targetGroupId],
                                   "target group ID");
                QL_REQUIRE(row[VarianceClockMarketDaysCsv::selectionReason] == "date_override" ||
                               row[VarianceClockMarketDaysCsv::selectionReason] ==
                                   "date_type_session_pattern" ||
                               row[VarianceClockMarketDaysCsv::selectionReason] ==
                                   "date_type_session_pattern_weekday" ||
                               row[VarianceClockMarketDaysCsv::selectionReason] ==
                                   "base_profile_fallback",
                           "invalid selection reason");
                const std::string dateKey = row[VarianceClockMarketDaysCsv::localDate];
                QL_REQUIRE(marketDates.find(dateKey) == marketDates.end(),
                           "duplicate market date");
                addCharge(tableIndexCharge,
                          sizeof(decltype(marketDates)::value_type) + 2U * dateKey.size() +
                              4U * sizeof(void*));
                marketDates.insert(dateKey);
                result.dates.push_back({date, id});
                const PairKey pair(id, row[VarianceClockMarketDaysCsv::targetGroupId]);
                if (selectedPairs.find(pair) == selectedPairs.end()) {
                    addCharge(tableIndexCharge,
                              sizeof(PairKey) + 2U * pair.second.size() +
                                  4U * sizeof(void*));
                    selectedPairs.insert(pair);
                }
                if (selectedProfiles.find(id) == selectedProfiles.end()) {
                    addCharge(tableIndexCharge,
                              sizeof(decltype(selectedProfiles)::value_type) +
                                  4U * sizeof(void*));
                    selectedProfiles.insert(id);
                }
            }
            QL_REQUIRE(!result.dates.empty(), "market_days table is empty");
            QL_REQUIRE(selectedProfiles.size() == result.profiles.size(),
                       "unreferenced profile");

            std::map<PairKey, std::array<bool, 288>> evidenceSlots;
            struct SlotEvidenceContext {
                const VarianceClockManifest* manifest;
                const std::vector<VarianceClockProfileInput>* profiles;
                const std::set<PairKey>* selectedPairs;
                std::map<PairKey, std::array<bool, 288>>* evidenceSlots;
                VarianceClockLoadBudget* budget;
                VarianceClockLoadBudget::Reservation* indexCharge;
            } evidenceContext{&manifest, &result.profiles, &selectedPairs, &evidenceSlots, &budget,
                             &tableIndexCharge};
            const auto consumeEvidenceRow =
                [](void* opaque, const std::string_view* fields, std::size_t count) {
                    auto& context = *static_cast<SlotEvidenceContext*>(opaque);
                    QL_REQUIRE(count == VarianceClockSlotEvidenceCsv::columnCount,
                               "wrong slot-evidence field count");
                    std::size_t recordBytes = 0;
                    for (std::size_t i = 0; i < count; ++i)
                        recordBytes += fields[i].size();
                    constexpr std::size_t rowFixedScratch =
                        128U * 1024U +
                        VarianceClockSlotEvidenceCsv::columnCount * (sizeof(std::string) + 32U);
                    // Bound the JSON DOM, strings, per-array storage and allocator overhead
                    // before decoding. Valid evidence_ids_json is at most 64 KiB.
                    constexpr std::size_t parserScratchPerByte = 128U;
                    QL_REQUIRE(recordBytes <=
                                   (std::numeric_limits<std::size_t>::max() - rowFixedScratch) /
                                       2U,
                               "variance-clock CSV accounting overflow");
                    const auto rowAndDecodedScratch = rowFixedScratch + 2U * recordBytes;
                    QL_REQUIRE(fields[VarianceClockSlotEvidenceCsv::evidenceIdsJson].size() <=
                                   (std::numeric_limits<std::size_t>::max() -
                                    rowAndDecodedScratch) /
                                       parserScratchPerByte,
                               "variance-clock CSV accounting overflow");
                    auto rowScratch = context.budget->reserve(
                        rowAndDecodedScratch +
                        parserScratchPerByte *
                            fields[VarianceClockSlotEvidenceCsv::evidenceIdsJson].size());
                    std::array<std::string, VarianceClockSlotEvidenceCsv::columnCount> row;
                    for (std::size_t i = 0; i < count; ++i)
                        row[i] = decodeVarianceClockCsvField(fields[i]);

                    const auto id = unsignedInteger<std::uint32_t>(
                        row[VarianceClockSlotEvidenceCsv::profileId], "profile_id");
                    const auto minute = unsignedInteger<std::uint16_t>(
                        row[VarianceClockSlotEvidenceCsv::minuteOfDay], "minute_of_day");
                    QL_REQUIRE(minute < 1440 && minute % 5 == 0,
                               "slot-evidence minute is outside five-minute grid");
                    validateIdentifier(row[VarianceClockSlotEvidenceCsv::targetGroupId],
                                       "target group ID");
                    const PairKey key(id, row[VarianceClockSlotEvidenceCsv::targetGroupId]);
                    QL_REQUIRE(context.selectedPairs->count(key),
                               "slot evidence for unselected pair");
                    auto slotEntry = context.evidenceSlots->find(key);
                    if (slotEntry == context.evidenceSlots->end()) {
                        addCharge(*context.indexCharge,
                                  sizeof(PairKey) + sizeof(std::array<bool, 288>) +
                                      2U * key.second.size() + 4U * sizeof(void*));
                        slotEntry = context.evidenceSlots
                                        ->try_emplace(key, std::array<bool, 288>{})
                                        .first;
                    }
                    auto& slots = slotEntry->second;
                    QL_REQUIRE(!slots[minute / 5], "duplicate slot-evidence key");
                    slots[minute / 5] = true;

                    const bool hasTargetCount =
                        row[VarianceClockSlotEvidenceCsv::targetReturnCount] != "unknown";
                    const std::uint32_t targetCount = hasTargetCount
                                                          ? unsignedInteger<std::uint32_t>(
                                                                row[VarianceClockSlotEvidenceCsv::
                                                                        targetReturnCount],
                                                                "target count")
                                                          : 0U;
                    const bool hasTargetDates =
                        row[VarianceClockSlotEvidenceCsv::targetDistinctLocalDateCount] !=
                        "unknown";
                    const std::uint32_t targetDates = hasTargetDates
                                                          ? unsignedInteger<std::uint32_t>(
                                                                row[VarianceClockSlotEvidenceCsv::
                                                                        targetDistinctLocalDateCount],
                                                                "target dates")
                                                          : 0U;
                    const auto evidenceIds = parseEvidenceIdsJson(
                        row[VarianceClockSlotEvidenceCsv::evidenceIdsJson]);
                    for (const auto& evidenceId : evidenceIds)
                        validateIdentifier(evidenceId, "slot evidence ID");

                    const auto profile = std::lower_bound(
                        context.profiles->begin(), context.profiles->end(), id,
                        [](const auto& item, std::uint32_t profileId) {
                            return item.id < profileId;
                        });
                    QL_REQUIRE(profile != context.profiles->end() && profile->id == id,
                               "slot evidence references unknown profile");
                    const double weight = profile->slots[minute / 5].weight;
                    const std::string& method =
                        row[VarianceClockSlotEvidenceCsv::estimationMethod];
                    QL_REQUIRE(method == "direct" || method == "pooled" ||
                                   method == "fallback" || method == "zero",
                               "invalid estimation method");
                    QL_REQUIRE((method == "zero") == (weight == 0.0),
                               "zero method and profile weight disagree");

                    if (method == "direct") {
                        QL_REQUIRE(hasTargetCount && targetCount >=
                                                       context.manifest->calibrationSettings
                                                           .minimumDirectReturns &&
                                       hasTargetDates && targetDates >= 1 &&
                                       row[VarianceClockSlotEvidenceCsv::sourceReturnCount] ==
                                           "not_applicable" &&
                                       row[VarianceClockSlotEvidenceCsv::
                                               sourceDistinctLocalDateCount] ==
                                           "not_applicable" &&
                                       row[VarianceClockSlotEvidenceCsv::sourceGroupId].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::groupingLabel].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::gapPoolReturnCount] ==
                                           "not_applicable" &&
                                       row[VarianceClockSlotEvidenceCsv::fallbackId].empty() &&
                                       !evidenceIds.empty(),
                                   "invalid direct slot evidence");
                    } else if (method == "pooled") {
                        QL_REQUIRE(hasTargetCount && targetCount <
                                                       context.manifest->calibrationSettings
                                                           .minimumDirectReturns &&
                                       hasTargetDates && targetDates >= 1 &&
                                       context.manifest->calibrationSettings
                                           .gapPoolReturnThreshold &&
                                       !row[VarianceClockSlotEvidenceCsv::sourceGroupId].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::sourceReturnCount] !=
                                           "not_applicable" &&
                                       !row[VarianceClockSlotEvidenceCsv::sourceReturnCount].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::
                                               sourceDistinctLocalDateCount] !=
                                           "not_applicable" &&
                                       !row[VarianceClockSlotEvidenceCsv::
                                                sourceDistinctLocalDateCount].empty() &&
                                       !row[VarianceClockSlotEvidenceCsv::groupingLabel].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::gapPoolReturnCount] !=
                                           "not_applicable" &&
                                       unsignedInteger<std::uint32_t>(
                                           row[VarianceClockSlotEvidenceCsv::gapPoolReturnCount],
                                           "gap-pool count") >=
                                           *context.manifest->calibrationSettings
                                                .gapPoolReturnThreshold &&
                                       row[VarianceClockSlotEvidenceCsv::fallbackId].empty() &&
                                       !evidenceIds.empty(),
                                   "invalid pooled slot evidence");
                        unsignedInteger<std::uint32_t>(
                            row[VarianceClockSlotEvidenceCsv::sourceReturnCount], "source count");
                        unsignedInteger<std::uint32_t>(
                            row[VarianceClockSlotEvidenceCsv::sourceDistinctLocalDateCount],
                            "source dates");
                    } else if (method == "zero") {
                        QL_REQUIRE(hasTargetCount && hasTargetDates &&
                                       row[VarianceClockSlotEvidenceCsv::sourceReturnCount] ==
                                           "not_applicable" &&
                                       row[VarianceClockSlotEvidenceCsv::
                                               sourceDistinctLocalDateCount] ==
                                           "not_applicable" &&
                                       row[VarianceClockSlotEvidenceCsv::sourceGroupId].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::groupingLabel].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::gapPoolReturnCount] ==
                                           "not_applicable" &&
                                       row[VarianceClockSlotEvidenceCsv::fallbackId].empty() &&
                                       !evidenceIds.empty(),
                                   "invalid zero slot evidence");
                    } else {
                        QL_REQUIRE(!row[VarianceClockSlotEvidenceCsv::fallbackId].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::sourceReturnCount] ==
                                           "not_applicable" &&
                                       row[VarianceClockSlotEvidenceCsv::
                                               sourceDistinctLocalDateCount] ==
                                           "not_applicable" &&
                                       row[VarianceClockSlotEvidenceCsv::sourceGroupId].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::groupingLabel].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::gapPoolReturnCount] ==
                                           "not_applicable" &&
                                       !evidenceIds.empty(),
                                   "invalid fallback slot evidence");
                    }
                    if (method != "fallback")
                        QL_REQUIRE(row[VarianceClockSlotEvidenceCsv::fallbackId].empty(),
                                   "fallback ID on non-fallback row");
                    if (method != "pooled")
                        QL_REQUIRE(row[VarianceClockSlotEvidenceCsv::sourceGroupId].empty() &&
                                       row[VarianceClockSlotEvidenceCsv::groupingLabel].empty(),
                                   "pooling metadata on non-pooled row");
                    return true;
                };
            budget.recordSlotEvidenceScan();
            QL_REQUIRE(visitVarianceClockCsvRows(csv.slotEvidence,
                                                 VarianceClockCsvSchema::SlotEvidence,
                                                 &evidenceContext, consumeEvidenceRow),
                       "variance-clock CSV row visitor stopped unexpectedly");

            for (const auto& pair : selectedPairs) {
                const auto slots = evidenceSlots.find(pair);
                QL_REQUIRE(slots != evidenceSlots.end() &&
                               std::all_of(slots->second.begin(), slots->second.end(),
                                           [](bool value) { return value; }),
                           "selected pair does not have exactly 288 slot evidence rows");
            }
            QL_REQUIRE(evidenceSlots.size() == selectedPairs.size(),
                       "extra selected-pair slot evidence");

            for (const auto& row : timezoneRows) {
                VarianceClockOffsetInput offset;
                offset.start = parseInstant(row[VarianceClockTimezoneMappingCsv::startUtc]);
                offset.end = parseInstant(row[VarianceClockTimezoneMappingCsv::endUtc]);
                offset.offsetSeconds =
                    signedInt32(row[VarianceClockTimezoneMappingCsv::offsetSeconds]);
                QL_REQUIRE(row[VarianceClockTimezoneMappingCsv::fold] == "0" ||
                               row[VarianceClockTimezoneMappingCsv::fold] == "1",
                           "invalid timezone fold");
                offset.fold = row[VarianceClockTimezoneMappingCsv::fold] == "1";
                QL_REQUIRE(offset.start < offset.end, "empty timezone mapping range");
                if (!result.offsets.empty())
                    QL_REQUIRE(result.offsets.back().end == offset.start,
                               "timezone mapping is not contiguous");
                result.offsets.push_back(offset);
            }
            QL_REQUIRE(!result.offsets.empty() && result.offsets.front().start <= result.start &&
                           !(result.offsets.back().end < result.end),
                       "timezone mapping does not cover variance-clock horizon");

            std::map<std::string, std::vector<std::pair<VarianceClockInstant,
                                                       VarianceClockInstant>>> sessions;
            auto sessionsCharge = budget.reserve(0);
            for (const auto& row : sessionRows) {
                const Date localDate =
                    parseDate(row[VarianceClockSessionSegmentsCsv::localDate]);
                QL_REQUIRE(marketDates.count(row[VarianceClockSessionSegmentsCsv::localDate]),
                           "session date is absent from market days");
                validateIdentifier(row[VarianceClockSessionSegmentsCsv::sessionId], "session ID");
                validateIdentifier(row[VarianceClockSessionSegmentsCsv::sourceEvidenceId],
                                   "session evidence ID");
                if (!row[VarianceClockSessionSegmentsCsv::tradingDate].empty())
                    parseDate(row[VarianceClockSessionSegmentsCsv::tradingDate]);
                if (!row[VarianceClockSessionSegmentsCsv::sourceSessionId].empty())
                    validateIdentifier(row[VarianceClockSessionSegmentsCsv::sourceSessionId],
                                       "source session ID");
                const auto start =
                    parseInstant(row[VarianceClockSessionSegmentsCsv::startUtc]);
                const auto end = parseInstant(row[VarianceClockSessionSegmentsCsv::endUtc]);
                QL_REQUIRE(start < end, "empty session segment");
                const auto firstRun = std::find_if(
                    result.offsets.begin(), result.offsets.end(),
                    [&start](const auto& offset) {
                        return offset.start <= start && start < offset.end;
                    });
                QL_REQUIRE(firstRun != result.offsets.end(),
                           "session start lacks timezone mapping");
                if (!row[VarianceClockSessionSegmentsCsv::claimedLocalOffsetSeconds].empty())
                    QL_REQUIRE(signedInt32(
                                   row[VarianceClockSessionSegmentsCsv::
                                           claimedLocalOffsetSeconds]) ==
                                   firstRun->offsetSeconds,
                               "session local offset claim disagrees with timezone mapping");
                const std::int64_t localStart = start.unixSeconds() + firstRun->offsetSeconds;
                const auto endRun = std::find_if(
                    result.offsets.begin(), result.offsets.end(), [&end](const auto& offset) {
                        return offset.start < end && end <= offset.end;
                    });
                QL_REQUIRE(endRun != result.offsets.end(), "session end lacks timezone mapping");
                const std::int64_t lastLocalSecond =
                    end.unixSeconds() - (end.nanosecond() == 0 ? 1 : 0) +
                    endRun->offsetSeconds;
                auto civilDay = [](std::int64_t seconds) {
                    const std::int64_t day = seconds >= 0 ? seconds / 86400
                                                          : (seconds - 86399) / 86400;
                    return day;
                };
                const std::int64_t expectedDay = daysFromCivil(
                    localDate.year(), static_cast<unsigned int>(localDate.month()),
                    static_cast<unsigned int>(localDate.dayOfMonth()));
                QL_REQUIRE(civilDay(localStart) == expectedDay &&
                               civilDay(lastLocalSecond) == expectedDay,
                           "session segment crosses its declared local date");
                const auto& localDateText = row[VarianceClockSessionSegmentsCsv::localDate];
                auto sessionEntry = sessions.find(localDateText);
                if (sessionEntry == sessions.end()) {
                    addCharge(sessionsCharge,
                              sizeof(decltype(sessions)::value_type) +
                                  2U * localDateText.size() +
                                  4U * sizeof(void*));
                    sessionEntry = sessions.try_emplace(localDateText).first;
                }
                addCharge(sessionsCharge, 2U * sizeof(std::pair<VarianceClockInstant,
                                                               VarianceClockInstant>));
                sessionEntry->second.emplace_back(start, end);
            }
            for (auto& item : sessions) {
                auto& ranges = item.second;
                std::sort(ranges.begin(), ranges.end(),
                          [](const auto& lhs, const auto& rhs) { return lhs.first < rhs.first; });
                for (std::size_t i = 1; i < ranges.size(); ++i)
                    QL_REQUIRE(!(ranges[i].first < ranges[i - 1].second),
                               "overlapping session segments");
            }
            for (const auto& row : dateRows) {
                const bool isOpen = row[VarianceClockMarketDaysCsv::isOpen] == "true";
                const bool hasSessions =
                    sessions.count(row[VarianceClockMarketDaysCsv::localDate]) != 0;
                QL_REQUIRE(isOpen == hasSessions, "market open status disagrees with sessions");
            }

            // Keep the charge bounded to the retained output capacities.
            const std::size_t retained =
                result.profiles.capacity() * sizeof(VarianceClockProfileInput) +
                result.dates.capacity() * sizeof(VarianceClockDateInput) +
                result.offsets.capacity() * sizeof(VarianceClockOffsetInput);
            result.storageCharge.resize(retained);
            return result;
        }
    }
}
