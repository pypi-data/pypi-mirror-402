import sys, os, egglib, pathlib

sys.path.insert(0, os.path.abspath('theme'))
sys.path.insert(0, os.path.join(r".", "src", "egglib"))
sys.path.append('scripts')

# -- get Version of module -----------------------
HERE = os.path.abspath(os.path.dirname(__file__))

def read(rel_path):
    """read the file and return the lines"""
    with open(os.path.join(HERE, rel_path), 'r') as fp:
        return fp.read()

VERSION = egglib.__version__

# -- generate dynamic parts of the documentation -----------------------
import make_muscle_arguments
import make_list_stats
import make_genetic_codes
import make_coal_models

sys.path.append(str(pathlib.Path('.').resolve()))

# -- General configuration ---------------------------------------------
extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'numpydoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.napoleon',
    'sphinx.ext.imgconverter',
    'gitlab_issue_role'
    ]

gitlab_base_url = 'https://gitlab.com/demita/egglib/-/issues/'

autosummary_generate = True
autosummary_generate_overwrite = True
autosummary_imported_members = True

# sphinx.ext.mathjax settings
mathjax_path = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS-MML_HTMLorMML"

# numpydoc settings
numpydoc_show_class_members = True
numpydoc_show_inherited_class_members = True
numpydoc_attributes_as_param_list = False
numpydoc_class_members_toctree = False

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

# sphinx.ext.intersphinx settings
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['templates']

# The suffix of source filenames.
source_suffix = ['.rst']

# The encoding of source files.
source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'contents'

# General information about the project.
project = 'EggLib'
copyright = 'Stéphane De Mita & Mathieu Siol'
github_doc_root = 'https://egglib.org/'
issues_github_path = 'https://gitlab.com/demita/egglib/-/issues'

# The short X.Y version.
version = VERSION
# The full version, including alpha/beta/rc tags.
release = VERSION

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['build', 'old', 'doxygen', 'stats_notice, doc_egglib2']

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# define a role for method parameters
rst_prolog = """
.. raw:: html

   <style type="text/css">
     span.fparam {
       font-weight: bold;
     }
   </style>

.. role:: fparam
   :class: fparam

"""

# -- Options for HTML output ---------------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'egglibdoc'
#html_theme_options = {}
html_theme_path = ['theme']
html_title = "EggLib's documentation"
#html_short_title = None
html_logo = './logo/egglib_small.bmp'
html_favicon = './logo/icon.ico'
#html_static_path = ['_static']
#html_last_updated_fmt = '%b %d, %Y'
#html_use_smartypants = True
#html_sidebars = {}
#html_additional_pages = {}
#html_domain_indices = True
html_use_index = True
#html_split_index = False
#html_show_sourcelink = True
html_show_sphinx = False
html_show_copyright = False
#html_use_opensearch = ''
#html_file_suffix = None
htmlhelp_basename = 'EggLibdoc'
html_additional_pages = {
    'index': 'index.html',
    'contents': 'contents.html'}
html_extra_path = ['doc_egglib2', 'data']

# -- Options for LaTeX output --------------------------------------------------
latex_engine = 'pdflatex'

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    'papersize': 'a4paper',
    # The font size ('10pt', '11pt' or '12pt').
    'pointsize': '12pt',
    # Latex figure (float) alignment
    'figure_align':'htbp',
    'extraclassoptions': 'openany',
    'preamble': r'''
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        %%%add number to subsubsection 2=subsection, 3=subsubsection
        \setcounter{secnumdepth}{0}
        %%%% Table of content upto 2=subsection, 3=subsubsection
        \setcounter{tocdepth}{2}
    ''',

    'sphinxsetup': \
        'hmargin={0.7in,0.7in}, vmargin={0.7in,0.7in}, \
        marginpar=1in, \
        verbatimwithframe=false, \
        TitleColor={RGB}{252,83,0}, \
        HeaderFamily=\\rmfamily\\bfseries, \
        InnerLinkColor={rgb}{0,0,1}, \
        OuterLinkColor={rgb}{0,0,1}',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).

latex_documents = [
  ('manual/index', 'tutorial.tex', 'EggLib Tutorial',
   u'Stéphane De Mita \\& Mathieu Siol', 'manual', True),

  ('py/index', 'reference.tex', 'EggLib Reference Manual',
   u'Stéphane De Mita \\& Mathieu Siol', 'manual', True),

  ('stats/index', 'stats.tex', 'EggLib Statistics Reference',
   u'Stéphane De Mita \\& Mathieu Siol', 'manual', True)

]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
latex_logo = 'logo/egglib.png'
# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False
# If true, show URL addresses after external links.
#latex_show_urls = False
# Documents to append as an appendix to all manuals.
#latex_appendices = []
# If false, no module index is generated.
#latex_domain_indices = True

# -- Options for manual page output --------------------------------------------

man_pages = [
    ('index', 'egglib', u'EggLib Documentation',
     [u'Stéphane De Mita & Mathieu Siol'], 1)
]
#man_show_urls = False

# -- Options for Texinfo output ------------------------------------------------

texinfo_documents = [
  ('index', 'EggLib', u'EggLib\'s documentation',
   u'Stéphane De Mita & Mathieu Siol', 'EggLib', 'One line description of project.',
   'Miscellaneous'),
]
