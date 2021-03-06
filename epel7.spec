{{ data.credit_line }}
{% from 'macros.spec' import dependencies, for_python_versions, underscored_or_pypi -%}
%global pypi_name {{ data.name }}
{%- if data.srcname %}
%global srcname {{ data.srcname }}
{%- endif %}

Name:           {{ data.pkg_name|macroed_pkg_name(data.srcname) }}
Version:        {{ data.version }}
Release:        1%{?dist}
Summary:        {{ data.summary }}

License:        {{ data.license }}
URL:            {{ data.home_page }}
Source0:        {{ data.source0|replace(data.name, '%{pypi_name}')|replace(data.version, '%{version}') }}

{%- if not data.has_extension %}
BuildArch:      noarch
{%- endif %}
{%- for pv in data.sorted_python_versions %}
{{ dependencies(data.build_deps, False, pv, data.base_python_version, use_with=False) }}
{%- endfor %}

%description
{{ data.description|truncate(400)|wordwrap }}
{% for pv in data.sorted_python_versions %}
%package -n     {{data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(pv, True)}}
Summary:        {{ data.summary }}
%{?python_enable_dependency_generator}
%description -n {{data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(pv, True)}}
{{ data.description|truncate(400)|wordwrap }}
{% endfor -%}
{%- if data.sphinx_dir %}
%package -n python-%{pypi_name}-doc
Summary:        {{ data.name }} documentation
%description -n python-%{pypi_name}-doc
Documentation for {{ data.name }}
{%- endif %}

%prep
%autosetup -n {{ data.dirname|replace(data.name, '%{pypi_name}')|replace(data.version, '%{version}')|default('%{pypi_name}-%{version}', true) }}
{%- if data.has_bundled_egg_info %}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
{%- endif %}

%build
{%- for pv in data.sorted_python_versions %}
{% if data.has_extension %}CFLAGS="$RPM_OPT_FLAGS" {% endif %}%{__python{{ pv }}} setup.py build
{%- endfor %}
{%- if data.sphinx_dir %}
# generate html docs 
PYTHONPATH=${PWD} {{ "sphinx-build"|script_name_for_python_version(data.base_python_version, False, False) }} {{ data.sphinx_dir }} html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}
{%- endif %}

%install
{%- if data.python_versions|length > 0 %}
# Must do the default python version install last because
# the scripts in /usr/bin are overwritten with every setup.py install.
{%- endif %}
{%- for pv in data.python_versions + [data.base_python_version] %}
{%- if pv == data.base_python_version and data.python_versions and data.scripts %}
rm -rf %{buildroot}%{_bindir}/*
{%- endif %}
%{__python{{ pv }}} setup.py install --skip-build --root %{buildroot}
mv %{buildroot}%{_sysconfdir}/%{pypi_name}/%{pypi_name}.yaml.dist %{buildroot}%{_sysconfdir}/%{pypi_name}/%{pypi_name}.yaml
{%- endfor -%}
{% if data.has_test_suite %}

%check
{%- for pv in data.sorted_python_versions %}
%{__python{{ pv }}} setup.py test
{%- endfor %}
{%- endif %}
{% for pv in data.sorted_python_versions %}
%files -n {{ data.pkg_name|macroed_pkg_name(data.srcname)|name_for_python_version(pv, True) }}
{%- if data.doc_files %}
%doc %{_docdir}/%{pypi_name}/{{data.doc_files|join(' ') }}
{%- endif %}
{%- if data.doc_license %}
%license %{_datarootdir}/licenses/%{pypi_name}/{{data.doc_license|join(' ')}}
{%- endif %}
%config(noreplace) %{_sysconfdir}/%{pypi_name}/%{pypi_name}.yaml
{%- if pv == data.base_python_version %}
{%- for script in data.scripts %}
%{_bindir}/{{ script }}
{%- endfor %}
{%- endif %}
{%- if data.py_modules %}
{%- for module in data.py_modules -%}
{%- if pv == '3' %}
%dir %{python{{ pv }}_sitelib}/__pycache__/
%{python{{ pv }}_sitelib}/__pycache__/*
{%- endif %}
%{python{{ pv }}_sitelib}/{{ data.name | module_to_path(module) }}.py{% if pv != '3'%}*{% endif %}
{%- endfor %}
{%- endif %}
{%- if data.has_extension %}
{%- if data.has_packages %}
{%- for package in data.packages %}
%{python{{ pv }}_sitearch}/{{ package | package_to_path(data.name) }}
{%- endfor %}
{%- endif %}
{%- if data.has_pth %}
%{python{{ pv }}_sitearch}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py%{python{{ pv }}_version}-*.pth
{%- endif %}
%{python{{ pv }}_sitearch}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py%{python{{ pv }}_version}.egg-info
{%- else %}
#{%- if data.has_packages %}
#{%- for package in data.packages %}
#%{python{{ pv }}_sitelib}/{{ package | package_to_path(data.name) }}
#{%- endfor %}
#{%- endif %}
{%- if data.has_pth %}
%{python{{ pv }}_sitelib}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py%{python{{ pv }}_version}-*.pth
{%- endif %}
%{python{{ pv }}_sitelib}/{{ underscored_or_pypi(data.name, data.underscored_name) }}-%{version}-py%{python{{ pv }}_version}.egg-info
{%- endif %}
{% endfor %}
{%- if data.sphinx_dir %}
%files -n python-%{pypi_name}-doc
%doc html 
{%- if data.doc_license %}
%license {{data.doc_license|join(' ')}}
{%- endif %}
{% endif %}
%changelog
* {{ data.changelog_date_packager }} - {{ data.version }}-1
- Allow to set multivalue argument as an array.
* Wed Mar 31 2021 Marco F <m.faverof@gmail.com> - 1.1.1-1
- Handle KeyError loading config file.
* Fri Mar 26 2021 Marco F <m.faverof@gmail.com> - 1.1.0-1
- Introduced FALSE_ERRORS in config file to ease error handling.
* Thu Mar 25 2021 Marco F <m.faverof@gmail.com> - 1.0.10-1
- Fixed a bug for duplicated keys management.
* Tue Mar 02 2021 Marco F <m.faverof@gmail.com> - 1.0.9-1
- Allow any repl-agmt command.
* Mon Mar 01 2021 Marco F <m.faverof@gmail.com> - 1.0.8-1
- Finally fixed a severe bug in dsconf command build.
* Mon Mar 01 2021 Marco F <m.faverof@gmail.com> - 1.0.7-1
- Fixed a severe bug in dsconf command build.
* Fri Feb 12 2021 Marco Favero <m.faverof@gmail.com> - 1.0.6-1
- Added arg "-c" in order to select custom config yaml file.
* Mon Feb 01 2021 Marco Favero <m.faverof@gmail.com> - 1.0.5-1
- Allow relative path in ldapmodify ldif file.
* Mon Feb 01 2021 Marco Favero <m.faverof@gmail.com> - 1.0.4-1
- Fix an error in setup.py.
* Mon Feb 01 2021 Marco Favero <m.faverof@gmail.com> - 1.0.3-1
- Renamed ds-easyconf.conf in ds-easyconf.yaml.
* Mon Feb 01 2021 Marco Favero <m.faverof@gmail.com> - 1.0.2-1
- Fixed an error in instance parsing.
* Wed Jan 27 2021 Marco Favero <m.faverof@gmail.com> - 1.0.1-1
- Initial package.
