%global srcname  igwn-segments
%global distname %{lua:name = string.gsub(rpm.expand("%{srcname}"), "[.-]", "_"); print(name)}
%global version 2.1.1
%global release 1

Name:           python-%{srcname}
Version:        %{version}
Release:        %{release}%{?dist}
Summary:        Representations of semi-open intervals

Packager:       Duncan Macleod <duncan.macleod@ligo.org>
Vendor:         Duncan Macleod <duncan.macleod@ligo.org>

License:        GPLv3
URL:            https://git.ligo.org/computing/software/igwn-segments/
Source0:        %pypi_source %distname

Prefix:         %{_prefix}

BuildRequires:  python3-devel
BuildRequires:  python3dist(pip)
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(setuptools-scm)
BuildRequires:  python3dist(wheel)

%description
This module defines the segment and segmentlist objects, as well as the
infinity object used to define semi-infinite and infinite segments.

%package -n python3-%{srcname}
Summary:  %{summary}
Recommends: python3-lal
%description -n python3-%{srcname}
This module defines the segment and segmentlist objects, as well as the
infinity object used to define semi-infinite and infinite segments.
%files -n python3-%{srcname}
%license LICENSE
%doc README.rst
%{python3_sitearch}/*

%prep
%autosetup -n %{distname}-%{version}
# for RHEL < 10 hack together setup.cfg for old setuptools
%if 0%{?rhel} && 0%{?rhel} < 10
cat > setup.cfg << SETUP_CFG
[metadata]
name = %{srcname}
version = %{version}
author-email = %{packager}
description = %{summary}
license = %{license}
license_files = LICENSE
url = %{url}
[options]
packages = find:
package_dir =
    =src
python_requires = >=%{python3_version}
[options.packages.find]
where = src
SETUP_CFG
%endif

%build
%py3_build_wheel

%install
%py3_install_wheel %{distname}-%{version}-*.whl

%check
export PYTHONPATH="%{buildroot}%{python3_sitearch}:%{buildroot}%{python3_sitelib}"
%python3 -m pip show %{srcname} -f
%python3 - << SIMPLE_TEST
from igwn_segments import segment;
a = segment(1, 2);
b = segment(2, 3);
c = segment(5, 6);
assert a.connects(b);
assert a in (a + b);
assert (a + b).intersects(b);
assert a.disjoint(c);
SIMPLE_TEST

%changelog
* Tue Jan 19 2026 Leo Singer <leo.singer@ligo.org> - 2.1.1-1
- New upstream release
- Don't install C sources in site-packages

* Tue May 06 2025 Leo Singer <leo.singer@ligo.org> - 2.1.0-1
- New upstream release

* Thu Dec 19 2024 Duncan Macleod <duncan.macleod@ligo.org> - 2.0.0-1
- First release after fork from ligo-segments
- Remove Python 2 packages
- Hack together a setup.cfg file to support old setuptools
- Use wheels in build
- Add simple tests for check stage

* Thu May 10 2018 Duncan Macleod <duncan.macleod@ligo.org>
- 1.0.0: first release of ligo.segments, should be funtionally identical to glue.segments
