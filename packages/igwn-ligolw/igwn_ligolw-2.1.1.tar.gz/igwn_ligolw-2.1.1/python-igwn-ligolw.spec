%global srcname igwn-ligolw
%global distname igwn_ligolw
%global version 2.1.1
%global release 1

Name:     python-%{srcname}
Summary:  LIGO Light-Weight XML I/O Library
Version:  %{version}
Release:  %{release}%{?dist}
License:  GPLv3+

Packager: Duncan Macleod <duncan.macleod@ligo.org>
Vendor:    Duncan Macleod <duncan.macleod@ligo.org>

Url:     https://git.ligo.org/computing/software/igwn-ligolw
Source:  %pypi_source %{distname}

Prefix:  %{_prefix}

BuildRequires: gcc
BuildRequires: python3-devel
BuildRequires: python3dist(pip)
BuildRequires: python3dist(setuptools)
BuildRequires: python3dist(setuptools-scm)
BuildRequires: python3dist(wheel)

%description
The LIGO Light-Weight XML format is widely used within gravitational-wave
data analysis pipelines.

%package -n python3-%{srcname}
Summary:  LIGO Light-Weight XML I/O Library (python%{python3_version})
Recommends: python3-lal
Recommends: python3-lalburst
%description -n python3-%{srcname}
The LIGO Light-Weight XML format is widely used within gravitational-wave
data analysis pipelines.  This package provides the Python %{python3_version}
library to read, write, and interact with documents in this format.
%files -n python3-%{srcname}
%doc README.md
%license LICENSE
%{python3_sitearch}/*

%package -n %{srcname}
Summary: Programs for manipulating LIGO Light-Weight XML files
BuildArch: noarch
Requires: python3
Requires: python3-%{srcname} = %{version}-%{release}
Requires: python3dist(igwn-segments)
Requires: python3-lal
%description -n %{srcname}
The LIGO Light-Weight XML format is widely used within gravitational-wave
data analysis pipelines.  This package provides several programs to
perform common, basic, manipulations of files in this format.
%files -n %{srcname}
%doc README.md
%license LICENSE
%{_bindir}/*

%prep
%autosetup -n %{distname}-%{version}
# for RHEL < 10 hack together setup.cfg and setup.py for old setuptools
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
install_requires =
  igwn-segments
  numpy
  python-dateutil
  pyyaml
  tqdm
packages = find:
python_requires = >=%{python3_version}
scripts =
  bin/igwn_ligolw_add
  bin/igwn_ligolw_cut
  bin/igwn_ligolw_no_ilwdchar
  bin/igwn_ligolw_print
  bin/igwn_ligolw_run_sqlite
  bin/igwn_ligolw_segments
  bin/igwn_ligolw_sqlite
SETUP_CFG
cat > setup.py << SETUP_PY
from setuptools import Extension, setup, find_packages

setup(
    ext_modules=[
        Extension(
            "igwn_ligolw.tokenizer",
            [
                "src/igwn_ligolw/tokenizer.c",
                "src/igwn_ligolw/tokenizer.Tokenizer.c",
                "src/igwn_ligolw/tokenizer.RowBuilder.c",
                "src/igwn_ligolw/tokenizer.RowDumper.c",
            ],
            include_dirs=["src/igwn_ligolw"],
        ),
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    use_scm_version={"write_to": "src/igwn_ligolw/_version.py"},
)
SETUP_PY
%endif

%build
%py3_build_wheel

%install
%py3_install_wheel %{distname}-%{version}-*.whl

%check
export PATH="%{buildroot}%{_bindir}:${PATH}"
export PYTHONPATH="%{buildroot}%{python3_sitearch}:%{buildroot}%{python3_sitelib}"
# print metadata
%python3 -m pip show %{srcname} -f
# can't check much more without installing a lot of other requirements
# that may create a circular dependency

%changelog
* Mon Jan 19 2026 Leo Singer <leo.singer@ligo.org> - 2.1.1-1
- New upstream release.
- Don't install C sources in site-packages.
- Tolerate blank encoding for arrays; don't write the value of the encoding
  attribute if it is set to its default value.
- Fix crash in igwn_ligolw_no_ilwdchar.

* Thu May 01 2025 Leo Singer <leo.singer@ligo.org> - 2.1.0-1
- Update to 2.1.0, adding base64 array encoding support

* Tue Apr 08 2025 Duncan Macleod <duncan.macleod@ligo.org> - 2.0.1-1
- Update to 2.0.1
- Remove explicit Requires for python3 package, use Python metadata

* Fri Jan 17 2025 Duncan Macleod <duncan.macleod@ligo.org> - 2.0.0-1
- First release after fork from python-ligo-lw
- Remove Python 2 packages
- Rename scripts package (`python3-ligo-lw-bin`) to `igwn-ligolw`
- Hack together a setup.cfg file to support old setuptools
- Use wheels in build

* Thu Dec 5 2019 Duncan Macleod <duncan.macleod@ligo.org> 1.6.0-3
- Fix bug in files to not bundle ligo/__init__.py

* Thu Dec 5 2019 Duncan Macleod <duncan.macleod@ligo.org> 1.6.0-2
- Rebuild with python3 packages

* Tue May 8 2018 Kipp Cannon <kipp.cannon@ligo.org>
- Initial release.
