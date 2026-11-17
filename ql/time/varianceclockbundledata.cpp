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
#include <map>
#include <set>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

namespace QuantLib {
    namespace detail {
        namespace {

            using Fields = std::vector<std::array<std::string, 14>>;

            struct RowContext {
                Fields* rows;
            };

            bool saveRow(void* opaque, const std::string_view* fields, std::size_t count) {
                auto& context = *static_cast<RowContext*>(opaque);
                std::array<std::string, 14> row;
                for (std::size_t i = 0; i < count; ++i)
                    row[i] = decodeVarianceClockCsvField(fields[i]);
                context.rows->push_back(std::move(row));
                return true;
            }

            std::size_t dataRowCount(std::string_view bytes) {
                const std::size_t newlines =
                    static_cast<std::size_t>(std::count(bytes.begin(), bytes.end(), '\n'));
                const std::size_t lines =
                    newlines + (!bytes.empty() && bytes.back() != '\n' ? 1U : 0U);
                return lines == 0 ? 0 : lines - 1;
            }

            Fields readRows(std::string_view bytes, VarianceClockCsvSchema schema) {
                Fields rows;
                rows.reserve(dataRowCount(bytes));
                RowContext context{&rows};
                QL_REQUIRE(visitVarianceClockCsvRows(bytes, schema, &context, saveRow),
                           "variance-clock CSV row visitor stopped unexpectedly");
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
                std::int32_t result = 0;
                const auto parsed = std::from_chars(value.data(), value.data() + value.size(),
                                                    result);
                QL_REQUIRE(parsed.ec == std::errc() && parsed.ptr == value.data() + value.size() &&
                               !(value.size() > 1 && value.front() == '-' && value[1] == '0') &&
                               value.front() != '+',
                           "invalid canonical signed integer");
                return result;
            }

            double decimal(std::string_view value, const char* name) {
                QL_REQUIRE(!value.empty(), "empty decimal in " << name);
                double result = 0.0;
                const auto parsed = std::from_chars(value.data(), value.data() + value.size(),
                                                    result, std::chars_format::general);
                QL_REQUIRE(parsed.ec == std::errc() && parsed.ptr == value.data() + value.size() &&
                               std::isfinite(result) && result >= 0.0,
                           "invalid nonnegative decimal in " << name);
                return result;
            }

            void validateIdentifier(std::string_view value, const char* name) {
                QL_REQUIRE(!value.empty() && value.size() <= 128,
                           name << " must contain between 1 and 128 UTF-8 bytes");
                QL_REQUIRE(std::isspace(static_cast<unsigned char>(value.front())) == 0 &&
                               std::isspace(static_cast<unsigned char>(value.back())) == 0,
                           name << " has surrounding whitespace");
                for (unsigned char c : value)
                    QL_REQUIRE(c >= 0x20 && c != 0x7f,
                               name << " contains a control character");
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

            Date parseDate(std::string_view text) {
                QL_REQUIRE(text.size() == 10 && text[4] == '-' && text[7] == '-',
                           "invalid Gregorian date");
                const int year = fixedDigits(text, 0, 4);
                const int month = fixedDigits(text, 5, 2);
                const int day = fixedDigits(text, 8, 2);
                QL_REQUIRE(year > 0 && month >= 1 && month <= 12 && day >= 1 &&
                               day <= monthLength(year, month),
                           "invalid Gregorian date");
                const Date result(day, static_cast<Month>(month), year);
                QL_REQUIRE(result >= Date::minDate() && result <= Date::maxDate(),
                           "date is outside QuantLib range");
                return result;
            }

            VarianceClockInstant parseInstant(std::string_view text) {
                QL_REQUIRE(text.size() >= 20 && text[4] == '-' && text[7] == '-' &&
                               text[10] == 'T' && text[13] == ':' && text[16] == ':',
                           "invalid strict UTC timestamp");
                const Date date = parseDate(text.substr(0, 10));
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

        VarianceClockLoadBudget::Reservation::Reservation(VarianceClockLoadBudget* budget,
                                                           std::size_t bytes) noexcept
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

        VarianceClockLoadBudget::VarianceClockLoadBudget(std::size_t limit) noexcept
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
            return limit_ - used_;
        }

        void VarianceClockLoadBudget::increase(std::size_t bytes) {
            QL_REQUIRE(bytes <= remaining(), "variance-clock load exceeds size limit");
            used_ += bytes;
        }

        void VarianceClockLoadBudget::decrease(std::size_t bytes) noexcept {
            used_ -= bytes;
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
            const std::size_t inputBytes = csv.profiles.size() + csv.marketDays.size() +
                                           csv.sessionSegments.size() +
                                           csv.timezoneMapping.size() + csv.slotEvidence.size();
            const std::size_t rowCount = dataRowCount(csv.profiles) +
                                         dataRowCount(csv.marketDays) +
                                         dataRowCount(csv.sessionSegments) +
                                         dataRowCount(csv.timezoneMapping) +
                                         dataRowCount(csv.slotEvidence);
            QL_REQUIRE(dataRowCount(csv.profiles) <= 400000 &&
                           dataRowCount(csv.marketDays) <= 400000 &&
                           dataRowCount(csv.sessionSegments) <= 400000 &&
                           dataRowCount(csv.timezoneMapping) <= 400000 &&
                           dataRowCount(csv.slotEvidence) <= 400000,
                       "variance-clock CSV exceeds row limit");
            QL_REQUIRE(rowCount <= 5U * 400000U, "variance-clock CSV exceeds row limit");
            QL_REQUIRE(rowCount <=
                           (std::numeric_limits<std::size_t>::max() - inputBytes) /
                               sizeof(std::array<std::string, 14>),
                       "variance-clock CSV accounting overflow");
            auto temporaryCharge =
                budget.reserve(inputBytes + rowCount * sizeof(std::array<std::string, 14>));
            ParsedVarianceClockTables result;
            result.start = parseInstant(manifest.coverageStartUtc);
            result.end = parseInstant(manifest.coverageEndUtc);
            QL_REQUIRE(result.start < result.end, "variance-clock coverage is empty");

            const auto profileRows = readRows(csv.profiles, VarianceClockCsvSchema::Profiles);
            const auto dateRows = readRows(csv.marketDays, VarianceClockCsvSchema::MarketDays);
            const auto sessionRows =
                readRows(csv.sessionSegments, VarianceClockCsvSchema::SessionSegments);
            const auto timezoneRows =
                readRows(csv.timezoneMapping, VarianceClockCsvSchema::TimezoneMapping);
            const auto evidenceRows =
                readRows(csv.slotEvidence, VarianceClockCsvSchema::SlotEvidence);
            QL_REQUIRE(profileRows.size() <= 400000 && dateRows.size() <= 400000 &&
                           sessionRows.size() <= 400000 && timezoneRows.size() <= 400000 &&
                           evidenceRows.size() <= 400000,
                       "variance-clock CSV exceeds row limit");
            const std::size_t maxRetained =
                profileRows.size() * sizeof(VarianceClockProfileInput) +
                dateRows.size() * sizeof(VarianceClockDateInput) +
                timezoneRows.size() * sizeof(VarianceClockOffsetInput);
            result.storageCharge = budget.reserve(maxRetained);
            result.profiles.reserve(profileRows.size());
            result.dates.reserve(dateRows.size());
            result.offsets.reserve(timezoneRows.size());

            std::map<std::uint32_t, ProfileRows> profiles;
            for (const auto& row : profileRows) {
                const auto id = unsignedInteger<std::uint32_t>(row[0], "profile_id");
                const auto minute = unsignedInteger<std::uint16_t>(row[1], "minute_of_day");
                QL_REQUIRE(minute < 1440 && minute % 5 == 0,
                           "profile minute is outside five-minute grid");
                auto& profile = profiles[id];
                profile.profile.id = id;
                const std::size_t slot = minute / 5;
                QL_REQUIRE(!profile.filled[slot], "duplicate profile slot");
                const double variance = decimal(row[2], "variance_per_5m");
                const double weight = decimal(row[3], "weight");
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
            for (const auto& calibration : manifest.profileCalibrations) {
                QL_REQUIRE(calibrations.emplace(
                               calibration.profileId,
                               parseInstant(calibration.calibrationAsOfUtc)).second,
                           "duplicate profile calibration");
            }
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

            std::set<std::string> selectedPairs;
            std::set<std::string> marketDates;
            for (const auto& row : dateRows) {
                const Date date = parseDate(row[0]);
                QL_REQUIRE(row[2] == "true" || row[2] == "false", "invalid is_open value");
                QL_REQUIRE(row[1] == "full_day" || row[1] == "early_close" ||
                               row[1] == "holiday" || row[1] == "weekend" ||
                               row[1] == "special",
                           "invalid market date type");
                const auto id = unsignedInteger<std::uint32_t>(row[3], "profile_id");
                const auto profile =
                    std::find_if(result.profiles.begin(), result.profiles.end(),
                                 [id](const auto& item) { return item.id == id; });
                QL_REQUIRE(profile != result.profiles.end(), "market day references unknown profile");
                validateIdentifier(row[4], "target group ID");
                QL_REQUIRE(row[5] == "regular" || row[5] == "date_override" ||
                               row[5] == "emergency_override" ||
                               row[5] == "closed_override",
                           "invalid selection reason");
                const std::string dateKey = row[0];
                QL_REQUIRE(marketDates.insert(dateKey).second, "duplicate market date");
                result.dates.push_back({date, id});
                selectedPairs.insert(std::to_string(id) + "\n" + row[4]);
            }
            QL_REQUIRE(!result.dates.empty(), "market_days table is empty");
            QL_REQUIRE(std::all_of(result.profiles.begin(), result.profiles.end(),
                                   [&result](const auto& profile) {
                                       return std::any_of(result.dates.begin(), result.dates.end(),
                                                          [&profile](const auto& day) {
                                                              return day.profile == profile.id;
                                                          });
                                   }),
                       "unreferenced profile");

            std::map<std::pair<std::uint32_t, std::string>, std::array<bool, 288>> evidenceSlots;
            for (const auto& row : evidenceRows) {
                const auto id = unsignedInteger<std::uint32_t>(row[0], "profile_id");
                const auto minute = unsignedInteger<std::uint16_t>(row[2], "minute_of_day");
                QL_REQUIRE(minute < 1440 && minute % 5 == 0,
                           "slot-evidence minute is outside five-minute grid");
                const std::string pair = std::to_string(id) + "\n" + row[1];
                QL_REQUIRE(selectedPairs.count(pair), "slot evidence for unselected pair");
                const auto key = std::make_pair(id, row[1]);
                auto& slots = evidenceSlots[key];
                QL_REQUIRE(!slots[minute / 5], "duplicate slot-evidence key");
                slots[minute / 5] = true;

                const auto targetCount = row[4] == "unknown"
                                             ? std::optional<std::uint32_t>()
                                             : std::optional<std::uint32_t>(
                                                   unsignedInteger<std::uint32_t>(row[4],
                                                                                  "target count"));
                const auto evidenceIds = parseEvidenceIdsJson(row[13]);
                std::set<std::string> uniqueEvidenceIds;
                for (const auto& evidenceId : evidenceIds) {
                    validateIdentifier(evidenceId, "slot evidence ID");
                    QL_REQUIRE(uniqueEvidenceIds.insert(evidenceId).second,
                               "duplicate slot evidence ID");
                }
                const std::string& method = row[8];
                const auto& profile = *std::find_if(
                    result.profiles.begin(), result.profiles.end(),
                    [id](const auto& item) { return item.id == id; });
                const double weight = profile.slots[minute / 5].weight;
                QL_REQUIRE(method == "direct" || method == "pooled" || method == "fallback" ||
                               method == "zero",
                           "invalid estimation method");
                QL_REQUIRE((method == "zero") == (weight == 0.0),
                           "zero method and profile weight disagree");
                if (method == "direct")
                    QL_REQUIRE(targetCount && *targetCount >=
                                                   manifest.calibrationSettings.minimumDirectReturns &&
                                   row[5] == "not_applicable" && row[6] != "not_applicable" &&
                                   unsignedInteger<std::uint32_t>(row[6], "target dates") >= 1 &&
                                   row[7] == "not_applicable" && row[3].empty() &&
                                   row[9].empty() && row[10] == "not_applicable" &&
                                   row[11].empty() && !evidenceIds.empty(),
                               "invalid direct slot evidence");
                if (method == "pooled")
                    QL_REQUIRE(targetCount && *targetCount <
                                                   manifest.calibrationSettings.minimumDirectReturns &&
                                   manifest.calibrationSettings.gapPoolReturnThreshold &&
                                   !row[3].empty() && row[5] != "not_applicable" &&
                                   unsignedInteger<std::uint32_t>(row[5], "source count") > 0 &&
                                   unsignedInteger<std::uint32_t>(row[6], "target dates") > 0 &&
                                   row[7] != "not_applicable" &&
                                   unsignedInteger<std::uint32_t>(row[7], "source dates") > 0 &&
                                   !row[9].empty() && row[10] != "not_applicable" &&
                                   unsignedInteger<std::uint32_t>(row[10], "gap-pool count") >=
                                       *manifest.calibrationSettings.gapPoolReturnThreshold &&
                                   row[11].empty(),
                               "invalid pooled slot evidence");
                if (method == "zero")
                    QL_REQUIRE(targetCount &&
                                   unsignedInteger<std::uint32_t>(row[6], "target dates") > 0 &&
                                   row[5] == "not_applicable" &&
                                   row[7] == "not_applicable" && row[3].empty() &&
                                   row[9].empty() && row[10] == "not_applicable" &&
                                   row[11].empty() && !evidenceIds.empty(),
                               "invalid zero slot evidence");
                if (method == "fallback")
                    QL_REQUIRE(!row[11].empty() &&
                                   unsignedInteger<std::uint32_t>(row[6], "target dates") > 0 &&
                                   row[5] == "not_applicable" &&
                                   row[7] == "not_applicable" && row[3].empty() &&
                                   row[9].empty() && row[10] == "not_applicable" &&
                                   !evidenceIds.empty(),
                               "invalid fallback slot evidence");
                else
                    QL_REQUIRE(row[11].empty(), "fallback ID on non-fallback row");
                if (method != "pooled")
                    QL_REQUIRE(row[3].empty() && row[9].empty(),
                               "pooling metadata on non-pooled row");
            }
            for (const auto& pair : selectedPairs) {
                const auto separator = pair.find('\n');
                const auto key = std::make_pair(
                    unsignedInteger<std::uint32_t>(std::string_view(pair).substr(0, separator),
                                                   "profile_id"),
                    pair.substr(separator + 1));
                const auto slots = evidenceSlots.find(key);
                QL_REQUIRE(slots != evidenceSlots.end() &&
                               std::all_of(slots->second.begin(), slots->second.end(),
                                           [](bool value) { return value; }),
                           "selected pair does not have exactly 288 slot evidence rows");
            }
            QL_REQUIRE(evidenceSlots.size() == selectedPairs.size(),
                       "extra selected-pair slot evidence");

            for (const auto& row : timezoneRows) {
                VarianceClockOffsetInput offset;
                offset.start = parseInstant(row[0]);
                offset.end = parseInstant(row[1]);
                offset.offsetSeconds = signedInt32(row[2]);
                QL_REQUIRE(row[3] == "0" || row[3] == "1", "invalid timezone fold");
                offset.fold = row[3] == "1";
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
            for (const auto& row : sessionRows) {
                const Date localDate = parseDate(row[0]);
                QL_REQUIRE(marketDates.count(row[0]), "session date is absent from market days");
                validateIdentifier(row[3], "session ID");
                validateIdentifier(row[7], "session evidence ID");
                if (!row[4].empty())
                    validateIdentifier(row[4], "trading date");
                if (!row[5].empty())
                    validateIdentifier(row[5], "source session ID");
                const auto start = parseInstant(row[1]);
                const auto end = parseInstant(row[2]);
                QL_REQUIRE(start < end, "empty session segment");
                const auto firstRun = std::find_if(
                    result.offsets.begin(), result.offsets.end(),
                    [&start](const auto& offset) { return offset.start <= start && start < offset.end; });
                QL_REQUIRE(firstRun != result.offsets.end(), "session start lacks timezone mapping");
                if (!row[6].empty())
                    QL_REQUIRE(signedInt32(row[6]) == firstRun->offsetSeconds,
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
                sessions[row[0]].emplace_back(start, end);
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
                const bool isOpen = row[2] == "true";
                const bool hasSessions = sessions.count(row[0]) != 0;
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
