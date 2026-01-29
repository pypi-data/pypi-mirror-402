%define name              ligo-scald
%define distname          ligo_scald
%define version           0.8.5
%define release           1

Summary:   SCalable Analytics for Ligo/virgo/kagra Data
Name:      %{name}
Version:   %{version}
Release:   %{release}%{?dist}
Source0:   %pypi_source %{distname}
License:   GPLv2+
Group:     Development/Libraries
Prefix:    %{_prefix}
Vendor:    Olivia Godwin <olivia.godwin@ligo.org>
Url:       https://git.ligo.org/gstlal-visualisation/ligo-scald

BuildArch: noarch

BuildRequires: rpm-build
BuildRequires: epel-rpm-macros

# python3-ligo-scald
BuildRequires: python3-rpm-macros
BuildRequires: python%{python3_pkgversion}
BuildRequires: python%{python3_pkgversion}-setuptools
BuildRequires: python%{python3_pkgversion}-wheel
BuildRequires: python%{python3_pkgversion}-pip

# -- ligo-scald

Requires: python%{python3_pkgversion}-ligo-scald = %{version}-%{release}

%description
ligo-scald is a gravitational-wave monitoring and dynamic data visualization
tool.  This package provides the `scald` command-line interface.

# -- python3-ligo-scald

%package -n python%{python3_pkgversion}-%{name}
Summary:  %{summary}
Requires: python%{python3_pkgversion}-bottle
Requires: python%{python3_pkgversion}-dateutil
Requires: python%{python3_pkgversion}-numpy
Requires: python%{python3_pkgversion}-PyYAML
Requires: python%{python3_pkgversion}-urllib3

%{?python_provide:%python_provide python%{python3_pkgversion}-%{name}}

%description -n python%{python3_pkgversion}-%{name}
ligo-scald is a gravitational-wave monitoring and dynamic data visualization
tool.  This package provides the Python %{python3_version} library.

# -- build steps

%prep
%autosetup -n %{distname}-%{version}

%build
%py3_build_wheel

%install
%py3_install_wheel *.whl

%clean
rm -rf $RPM_BUILD_ROOT

%files
%license LICENSE
%{_bindir}/scald

%files -n python%{python3_pkgversion}-%{name}
%license LICENSE
%{python3_sitelib}/*
