#pragma once

#include <nanobind/nanobind.h>

namespace nb = nanobind;

void bind_time(nb::module_& m);
void bind_curves(nb::module_& m);
void bind_instruments(nb::module_& m);
void bind_pricing(nb::module_& m);
void bind_rates_options(nb::module_& m);
void bind_callable(nb::module_& m);
void bind_credit(nb::module_& m);
void bind_cms(nb::module_& m);
void bind_inflation(nb::module_& m);
void bind_fx(nb::module_& m);
void bind_heston(nb::module_& m);
void bind_lmm(nb::module_& m);
void bind_smile(nb::module_& m);
void bind_markov_functional(nb::module_& m);
void bind_experimental(nb::module_& m);
void bind_math(nb::module_& m);
void bind_marketmodel(nb::module_& m);
