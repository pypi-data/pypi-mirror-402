# Sphinx APA References

## Introduction

This Sphinx extension allows you to have APA formatting of references in your book.

> [!NOTE]
> This extension only modifies the formatting of references to comply with APA style. It does not handle citation management or reference generation; you will need to manage your references separately.

## What does it do?

This extension modifies the way references are formatted in Sphinx-generated documentation to comply with APA (American Psychological Association) style guidelines _for references_. It ensures that citations and bibliographies are presented in a manner consistent with APA standards.

This entails **forcing** the following APA-specific formatting rules:

- Proper indentation and spacing for reference entries.
- Use of round brackets for in-text citations.

## Installation

To use this extension, follow these steps:

**Step 1: Install the Package**

Install the module `sphinx-apa-references` package using `pip`:
```
pip install sphinx-apa-references
```
    
**Step 2: Add to `requirements.txt`**

Make sure that the package is included in your project's `requirements.txt` to track the dependency:
```
sphinx-apa-references
```

**Step 3: Enable in `_config.yml` or `conf.py`**

In your `_config.yml` file, add the extension to the list of Sphinx extra extensions (**important**: underscore, not dash this time) and specify the location of your bib file (note indentation of the bibtex file path specification; any number of bib files are allowed):

```yaml
sphinx: 
    extra_extensions:
        .
        .
        .
        - sphinx_apa_references
        .
        .
        .
bibtex_bibfiles:
    - "<path_to_bib_file>/<bibfile>.bib"
```

or in your `conf.py` file, add the extension to the `extensions` list and specify the location of your bib file:

```python
extensions = [...,"sphinx_apa_references",...]
bibtex_bibfiles = ["<path_to_bib_file>/<bibfile>.bib"]
```

## Configuration

No additional configuration is possible. The extension automatically applies APA formatting to all references in your Sphinx documentation.

This extensions enforces the following settings, overriding any user-defined settings in `_config.yml`/`conf.py`:

- `bibtex_reference_style = "author_year_round"`

Furthermore, the `bibliography` directive is adapted to always use the value `apa` for the `style` option if the user does not provide a value for the `style` option.

## Examples and details

To see examples of usage visit [this page in the TeachBooks manual](https://teachbooks.io/manual/features/apa.html).

## Previous APA implementation

Prior to the creation of this Sphinx extension, APA referencing was implemented by including a local extension in a book subdirectory, as described in [Issue 1090 from the Jupyter Book repository](https://github.com/jupyter-book/jupyter-book/issues/1090).

To upgrade from the previous setup, once this Sphinx extension is implemented in your book, the local extension files in `_ext` can be deleted and the four lines indicated below removed from your `_config.yml` file:

```yaml
sphinx:
  config:
    .
    .
    .
    bibtex_reference_style: author_year_round   # remove
    bibtex_default_style: myapastyle            # remove
    .
    .
    .
  local_extensions:
    apastyle: _ext/                             # remove
    bracket_citation_style: _ext/               # remove
```