
SUBDIRS = ql m4 man Docs Examples test-suite

ACLOCAL_AMFLAGS = -I m4

bin_SCRIPTS = quantlib-config

if EMACS_FOUND
dist_lisp_LISP = quantlib.el
endif

m4datadir = $(datadir)/aclocal
dist_m4data_DATA = quantlib.m4

pkgconfigdir = $(libdir)/pkgconfig
nodist_pkgconfig_DATA = quantlib.pc

EXTRA_DIST = \
	CMakeLists.txt \
	Contributors.txt \
	LICENSE.TXT \
	News.md \
	QuantLib.natvis \
	QuantLib.props \
	QuantLib.spec \
	QuantLib.sln \
	QuantLib.vcxproj \
	QuantLib.vcxproj.filters \
	README.md \
	ql/utilities/detail/thirdparty/LICENSE-nlohmann-json.txt \
	ql/utilities/detail/thirdparty/THIRD_PARTY_NOTICES.md \
	autogen.sh \
	test-probes/varianceclock/CMakeLists.txt \
	test-probes/varianceclock/varianceclock_probe.hpp \
	test-probes/varianceclock/varianceclock_probe_controls.cpp \
	test-probes/varianceclock/varianceclock_probe_hooks.cpp \
	test-probes/varianceclock/varianceclock_probe.vcxproj

.PHONY: examples check-examples
examples:
	$(MAKE) -C Examples examples
check-examples:
	$(MAKE) -C Examples check-examples

.PHONY: benchmark
benchmark:
	$(MAKE) -C test-suite benchmark

.PHONY: docs
docs:
	$(MAKE) -C Docs docs

dist-hook:
	mkdir -p $(distdir)/build
	mkdir -p $(distdir)/cmake
	cp -p $(srcdir)/cmake/CheckGeneratedHeaders.cmake $(distdir)/cmake
	cp -p $(srcdir)/cmake/GenerateHeaders.cmake $(distdir)/cmake
	cp -p $(srcdir)/cmake/Platform.cmake $(distdir)/cmake
	cp -p $(srcdir)/cmake/QuantLibConfig.cmake.in $(distdir)/cmake
