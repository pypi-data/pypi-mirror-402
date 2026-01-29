"""
managed files
=============

this portion of the ``ae`` namespace creates files from templates, to maintain and keep similar files up-to-date.
files that are mostly identical, like e.g. the license or contribution info of your software projects, can
automatically be checked and renewed. variations in the file content, like the name and version of a concrete project,
are getting replaced dynamically with actual values from project-specific context variables.

template files are dynamically compiled into destination files, by evaluating embedded f-string-expressions or
special replacers. replacers are useful especially to generate python code files because they are syntactically
treated as comments in the template file, replaceable by code statements or code snippets from external files.

use the function :func:`deploy_template` to convert a single template into a destination file. fpr bulk destination
file deployments from multiple templates, use the :class:`TemplateMngr` class.
"""
import os
from typing import Any, Callable, Iterable, Optional, Protocol, cast, runtime_checkable

from ae.base import (                                                                       # type: ignore
    UNSET,
    norm_path, os_path_basename, os_path_isfile, os_path_join, os_path_splitext, read_file, write_file)
from ae.dynamicod import try_eval                                                           # type: ignore
from ae.literal import Literal                                                              # type: ignore


__version__ = '0.3.4'


DEPLOY_LOCK_EXT = '.locked'                             #: additional file ext; blocking the deployment of a template

F_STRINGS_PATH_PFX = 'de_tpl_'                          #: file name prefix if template contains f-strings

MANAGED_FILE_ENCODING = None                            #: managed file default read/write encoding
MANAGED_FILE_EXTRA_MODE = 'b'                           #: managed file default read/write extra mode (binary)

MANAGED_FILE_ERROR_COMMENT = '* error: '                #: managed file error comment marker
MANAGED_FILE_SKIP_COMMENT = '- skip reason: '           #: managed file skip-reason comment marker
MANAGED_FILE_WARNING_COMMENT = '# '                     #: managed file warning comment marker

PATH_PREFIXES_ARGS_SEP = '_'                            #: seperator/suffix of template file/path prefixes arguments

REFRESHABLE_TEMPLATE_MARKER = 'THIS FILE IS EXCLUSIVELY MAINTAINED'
""" to mark the content (header) of a refreshable project file that gets created and updated from a template. """
REFRESHABLE_TEMPLATE_PATH_PFX = 'de_otf_'
""" file name prefix of an refreshable/externally maintained file, that get created and updated from a template. """

STOP_PARSING_PATH_PFX = '_z_'                           #: file name prefix to support template of template

TEMPLATE_PLACEHOLDER_ID_PREFIX = "# "                   #: template replacers id prefix marker
TEMPLATE_PLACEHOLDER_ID_SUFFIX = "#("                   #: template replacers id suffix marker
TEMPLATE_PLACEHOLDER_ARGS_SUFFIX = ")#"                 #: template replacers args suffix marker
TEMPLATE_INCLUDE_FILE_PLACEHOLDER_ID = "IncludeFile"    #: replacers id of :func:`replace_with_file_content_or_default`
TEMPLATE_REPLACE_WITH_PLACEHOLDER_ID = "ReplaceWith"    #: replacers id of :func:`replace_with_template_args`


# types ---------------------------------------------------------------------------------------------------------------

ContentTransformer = Callable[['ManagedFile'], str]     #: text file content transformer function
ContentType = str | bytes | None                        #: content type of managed file (None==file-not-exists)

ContextVars = dict[str, Any]                            #: template placeholder variables to be replaced by its value


# pylint: disable=missing-class-docstring,too-few-public-methods
@runtime_checkable  # PathPrefixesFunc = Callable[['ManagedFile'], None] does not support multiple *args
class PathPrefixesFunc(Protocol):                       #: path prefixes parser function
    def __call__(self, managed_file: 'ManagedFile', *path_prefix_args: str) -> None: ...


PathPrefixesParsers = dict[str, tuple[int, PathPrefixesFunc]]  #: registered path prefixes parsers

PathPrefixesArgCounts = Iterable[tuple[str, int]]       #: path prefixes with its arg counts
PathPrefixesArgs = list[tuple[str, tuple[str, ...]]]    #: path prefixes with its arg values

Replacer = Callable[[str], str]                         #: template content replacers function type

TemplateFiles = list[tuple[str, str, str]]              #: (patcher id, template file path, destination path prefixes)

TplVars = dict[str, Any]                                #: template placeholder variables to be replaced by its value


class ManagedFile:          # pylint: disable=too-many-instance-attributes
    """ represents a template/managed file """
    def __init__(self, manager: 'TemplateMngr', patcher: str, template_path: str, dst_path: str = "."):
        """ create new managed file instance

        :param manager:         :class:`TemplateMngr` instance, to reference path prefixes, context vars and replacers.
        :param patcher:         templates collection (project) name and version (to be added into the destination file).
        :param template_path:   template/source file path.
        :param dst_path:        destination file path with optional path prefixes in its file and/or folder names.
        """
        self.manager = manager
        self.patcher = patcher
        self.template_path = template_path
        self._dst_file_path = patch_string(dst_path, manager.context_vars)
        self._dst_path_stripped = False
        self._dst_path_extension = ""

        self._content_transformers: list[ContentTransformer] = []

        self.file_content: ContentType = None
        self._file_encoding = UNSET
        self._file_mode = UNSET
        self.old_content: ContentType = None     #: old dst file content loaded if unskipped in path prefixes

        self.comments: list[str] = []       #: to collect comments, errors and skip-reasons of this managed file

        self.refreshable = False            #: set to True in path prefix parser to allow to overwrite destination file
        self.up_to_date = False             #: set to True if destination file is up-to-date

    def __repr__(self):
        """ show destination path, patcher and attributes of this managed file. """
        attrs = "/".join([_ for _ in ('refreshable', 'up_to_date', 'skip_or_error') if getattr(self, _)])
        return f"{self.__class__.__name__}:{hex(id(self))} {self._dst_file_path} {self.patcher} {attrs}"

    def add_content_transformer(self, tf: ContentTransformer, extra_mode: str = '', encoding: str | None = None):
        """ add a content transformer callable to this managed file.

        :param tf:              content transformer callable, to be called with this instance as argument and returning
                                the new/transformed content.
        :param extra_mode:      extra file mode (passed to :func:`~ae.base.read_file`/:func:`~ae.base.write_file`).
        :param encoding:        content encoding (passed to :func:`~ae.base.read_file`/:func:`~ae.base.write_file`).
        """
        if self._file_mode not in (UNSET, extra_mode):
            self.error(f"file extra mode mismatch {extra_mode=} != {self._file_mode=}")
        self._file_mode = extra_mode

        if self._file_encoding not in (UNSET, encoding):
            self.error(f"file encoding mismatch {encoding=} != {self._file_encoding=}")
        self._file_encoding = encoding

        self._content_transformers.append(tf)

    def content_transformations(self):
        """ load the file contents of the source and destination file and run all the collected content transformers """
        if self.file_content is None:
            self.file_content = read_file(self.template_path, extra_mode=self.file_mode, encoding=self.file_encoding)

        if self.old_content is None and os_path_isfile(dst_file_path := self.dst_file_path):
            self.old_content = read_file(dst_file_path, extra_mode=self.file_mode, encoding=self.file_encoding)

        for content_transformer in self._content_transformers:
            self.file_content = content_transformer(self)

    @property
    def dst_file_path(self) -> str:
        """ return relative destination path of this managed file (cleaned from path/file name prefixes). """
        if self._dst_path_stripped:
            return self._dst_file_path

        man = self.manager
        return prefix_parser(self._dst_file_path, man.path_prefixes_arg_counts, args_sep=man.path_prefixes_args_sep)[0]

    def extend_dst_file_path(self, ext_path: str):
        """ extend destination file path with the specified folder path.

        :param ext_path:        path to extend the destination path with, e.g. move from project root to package path.
        """
        if self._dst_path_extension:
            self.warning(f"multiple destination path extension overwriting '{self._dst_path_extension}' w/ {ext_path=}")
        self._dst_path_extension = ext_path

    def error(self, message: str):
        """ add an error comment to this managed file.

        :param message:         error comment text to add.
        """
        self.comments.append(MANAGED_FILE_ERROR_COMMENT + message)

    @property
    def file_encoding(self) -> str | None:
        """ return the encoding of this managed file. """
        return MANAGED_FILE_ENCODING if self._file_mode is UNSET else self._file_encoding

    @property
    def file_mode(self) -> str:
        """ return the file mode of this managed file. """
        return MANAGED_FILE_EXTRA_MODE if self._file_mode is UNSET else self._file_mode

    def process_path_prefixes(self) -> bool:
        """ parse, reduce and call back the template file name/path prefixes to check for early deploy skip or errors.

        :return:                False if one of the path prefixes parsers errored or skipped this managed file.
        """
        arg_counts = self.manager.path_prefixes_arg_counts
        prefixes_parsers = self.manager.path_prefixes_parsers
        prefixes_args_sep = self.manager.path_prefixes_args_sep

        stripped_dst_path, prefixes_args = prefix_parser(self._dst_file_path, arg_counts, args_sep=prefixes_args_sep)

        refreshable_args = None
        for prefix, args in prefixes_args:
            if prefix == REFRESHABLE_TEMPLATE_PATH_PFX:
                if refreshable_args is not None:
                    self.warning(f"ignoring multiple {REFRESHABLE_TEMPLATE_PATH_PFX=} in {self._dst_file_path}")
                refreshable_args = args     # postpone call of refreshable content check to have the final file content
                continue
            func = prefixes_parsers[prefix][1]
            func(self, *args)

        if refreshable_args is not None:
            prefixes_parsers[REFRESHABLE_TEMPLATE_PATH_PFX][1](self, *refreshable_args)

        self._dst_file_path = os_path_join(self._dst_path_extension, stripped_dst_path)
        self._dst_path_stripped = True
        return not self.skip_or_error

    def skip(self, message: str):
        """ add a skip reason comment to this managed file.

        :param message:         skip reason comment text to add.
        """
        self.comments.append(MANAGED_FILE_SKIP_COMMENT + message)

    @property
    def skip_or_error(self) -> bool:
        """ return True if this managed file got skipped or added an error comment. """
        return any(_.startswith((MANAGED_FILE_ERROR_COMMENT, MANAGED_FILE_SKIP_COMMENT)) for _ in self.comments)

    def warning(self, message: str):
        """ add a warning comment to this managed file.

        :param message:         warning comment text to add.
        """
        self.comments.append(MANAGED_FILE_WARNING_COMMENT + message)

    def write_file_content(self):
        """ deploy file content of this managed file to its :attr:`dst_file_path`, creating not-existing folders. """
        write_file(self.dst_file_path, self.file_content,
                   extra_mode=self.file_mode, encoding=self.file_encoding, make_dirs=True)


class TemplateMngr:
    """ checks/deploys/renews managed files from templates and context variables.

    .. hint::
        example usages of this class can be found in the helper functions :func:`deploy_template` (in this module)
        and :func:`~aedev.project_manager.templates.check_templates` (of the ``pjm`` project-manager tool).
    """
    def __init__(self, template_files: TemplateFiles, prefix_parsers: PathPrefixesParsers, context_vars: ContextVars,
                 *, prefix_args_sep: str = PATH_PREFIXES_ARGS_SEP, **replacers: Replacer):
        """
        :param template_files:  list of template description tuples with
                                [0]: patcher, e.g. the template project & version,
                                [1]: path to the template file,
                                [2]: destination file path with optional f-string-placeholders and path prefixes.
                                order this list by priority, because if there is more than one template results in the
                                same destination file path, then only the first one will be deployed.
        :param prefix_parsers:  template file/path prefixes as mapping of a path prefix string to a tuple of
                                a path prefix arg count and a processing/parsing callee.
        :param context_vars:    context variables dict to replace template placeholders. to get more globals (by
                                :func:`~ae.dynamicod.try_eval`) extend this argument with a '_add_base_globals' key.
        :param prefix_args_sep: path prefixes arguments separator/suffix; defaults to :data:`PATH_PREFIXES_ARGS_SEP`.
        :param replacers:       optional replacers: key=placeholder-id and value=replacer callable.

        """
        self.template_files = template_files

        glo_vars = globals().copy()         # provide globals of this module, e.g., os.linesep, TEMPLATE_*, ...
        glo_vars.update(context_vars)       # plus context vars, e.g., PDV_COMMIT_MSG_FILE_NAME (.gitignore/index.rst)
        self.context_vars = glo_vars

        assert not any(prefix == STOP_PARSING_PATH_PFX for prefix in prefix_parsers.keys())
        self.path_prefixes_parsers = prefix_parsers
        self.path_prefixes_args_sep = prefix_args_sep

        self.replacers = replacers

        self.managed_files: list[ManagedFile] = []
        self.deploy_files: dict[str, ManagedFile] = {}
        self._compile()

    def _compile(self):
        for patcher, tpl_file_path, dst_path in self.template_files:
            mf = ManagedFile(self, patcher, tpl_file_path, dst_path)
            self.managed_files.append(mf)

            if mf.process_path_prefixes():
                dst_file_path = norm_path(mf.dst_file_path)
                if os_path_isfile(dst_file_path + DEPLOY_LOCK_EXT):
                    mf.skip("destination .locked file exists")
                elif not mf.refreshable and os_path_isfile(dst_file_path):
                    mf.skip("destination file of this not refreshable template already exists")
                elif dst_file_path in self.deploy_files:
                    mf.skip(f"lower priority than {self.deploy_files[dst_file_path].template_path}")
                else:
                    mf.content_transformations()
                    if not mf.skip_or_error:
                        self.deploy_files[dst_file_path] = mf

    def __repr__(self):
        """ show deployed, deployable and managed file counts. """
        return (f"{self.__class__.__name__}:{hex(id(self))}"
                f" {sum(_mf.up_to_date for _mf in self.deploy_files.values())} up-to-date of"
                f" {len(self.deploy_files)} deployable of {len(self.managed_files)} managed files")

    @property
    def checked_files(self) -> set[str]:
        """ return a set of destination file paths of all the managed/checked template files. """
        return set(mf.dst_file_path for mf in self.managed_files)

    def deploy(self):
        """ deploy all the missing/outdated managed files. """
        for mf in self.deploy_files.values():
            if not mf.up_to_date:
                mf.write_file_content()

    def log_lines(self, verbose: bool = False) -> list[str]:
        """ return a list of the log lines of all the managed/checked template files.

        :param verbose:         pass True to get more verbose log entries and include also not deployed files.
        :return:                list of log entry lines (preformatted with indent to direct console printout).
        """
        lines = []
        for mf in self.managed_files if verbose else self.deploy_files.values():
            dst_file_path = mf.dst_file_path
            tpl_file = mf.template_path if verbose else os_path_basename(mf.template_path)
            lines.append(f"    = {dst_file_path} from template {tpl_file} ({mf.patcher})")
            if verbose and not mf.skip_or_error:  # not skipped or mf in self.deploy_files.values() is up-to-date:
                lines.append(" " * 6 + "+ " + ("up-to-date" if mf.up_to_date else
                                               "overwrite/refresh" if os_path_isfile(dst_file_path) else
                                               "add/miss"))
            for comment in mf.comments:
                if verbose or comment.startswith(MANAGED_FILE_ERROR_COMMENT):
                    lines.append(" " * 6 + comment)
        return lines

    @property
    def missing_files(self) -> set[str]:
        """ return a set of destination file paths of the missing files created from templates. """
        return set(dst_path for mf in self.managed_files
                   if not os_path_isfile(dst_path := mf.dst_file_path) and not mf.skip_or_error and not mf.up_to_date)

    @property
    def outdated_files(self) -> list[tuple[str, ContentType, ContentType]]:
        """ list of tuples of destination file path, new, and old file contents for each outdated refreshable file. """
        return [(dst_file_path, mf.file_content, mf.old_content) for mf in self.managed_files
                if os_path_isfile(dst_file_path := mf.dst_file_path) and not mf.skip_or_error and not mf.up_to_date]

    @property
    def path_prefixes_arg_counts(self) -> PathPrefixesArgCounts:
        """ iterable of tuples wit the prefix id/string and its args count for all registered path prefixes. """
        return [(prefix, arg_count) for prefix, (arg_count, _callee) in self.path_prefixes_parsers.items()]

    @property
    def skipped_files(self) -> set[str]:
        """ return a set of destination file paths of the skipped or erroneous managed files. """
        return set(mf.dst_file_path for mf in self.managed_files if mf.skip_or_error)


# global helpers  -----------------------------------------------------------------------------------------------------


def deploy_template(template_file_path: str, dst_path: str = ".", patcher: str = 'deploy_template_default_patcher',
                    prefixes_parsers: Optional[PathPrefixesParsers] = None, tpl_vars: Optional[TplVars] = None) -> str:
    """ create/update a file from a template.

    :param template_file_path:  template/source file path.
    :param dst_path:            destination file name and path with optional path prefixes/args (will be removed).
                                defaults to the current working directory if not specified.
    :param patcher:             patcher id string, e.g. the template project & version.
    :param prefixes_parsers:    mapping of a prefix to a tuple of the prefix args count and the prefix callable/parser.
    :param tpl_vars:            template/project env/dev variables dict of the destination project to patch/refresh.
                                providing values for the file/path names, the templates f-string placeholders, and the
                                path prefix parser callees (e.g. to specify the `project_type`, `project_path` or
                                `package_path` values).
    :return:                    absolute and stripped destination file path if template got deployed,
                                or an empty string if any error or skip reason occurred.
    """
    man = TemplateMngr([(patcher, template_file_path, dst_path)],
                       prefixes_parsers or DEFAULT_PATH_PREFIXES_PARSERS,
                       tpl_vars or {})
    man.deploy()
    return next(iter(dst_path for dst_path, mf in man.deploy_files.items() if not mf.up_to_date), "")


def patch_refreshable_content(file_name: str, content: str, patcher: str) -> str:
    """ create/update the content of a refreshable text file with placeholders (compiled from a template file).

    :param file_name:           the name (and path) of the file to create/update/patch.
    :param content:             the content of the file (without the placeholder template marker).
    :param patcher:             patching entity/project name/version, to be placed with the placeholder template marker.
    :return:                    the patched content of the text file (with updated outsource marker).
    """
    ext = os_path_splitext(file_name)[1]
    sep = os.linesep
    if ext == '.md':
        beg, end = "<!-- ", " -->"
    elif ext == '.rst':
        beg, end = f"{sep}..{sep}    ", sep
    else:
        beg, end = "# ", ""
    return f"{beg}{REFRESHABLE_TEMPLATE_MARKER} {patcher}{end}{sep}{content}"


def patch_string(content: str, tpl_vars: ContextVars, **replacers: Replacer) -> str:
    """ replace f-string / dynamic placeholders in content with variable values / return values of replacers callables.

    :param content:             f-string to patch (e.g., a template file's content).
    :param tpl_vars:            dict with variables used as globals for f-string replacements. extend this argument with
                                a '_add_base_globals' key to add useful globals (see :func:`~ae.dynamicod.try_eval`).
    :param replacers:           optional kwargs dict with key/name=placeholder-id and value=replacer-callable.
                                to specify additional replacers and also to overwrite or to deactivate the default
                                template placeholder replacers specified in :data:`DEFAULT_TEMPLATE_PLACEHOLDERS`
    :return:                    string resulting from the evaluation of the specified content f-string and from the
                                default and additionally specified template :paramref;`~patch_string.replacers`.
    :raises AssertionError:     if :data:`TEMPLATE_PLACEHOLDER_ARGS_SUFFIX` is a replacers comment.
    :raises Exception:          if evaluation of the :paramref;`~patch_string.content` f-string failed (because of
                                missing-globals-NameError/SyntaxError/ValueError/...).
    """
    content = try_eval('f"""' + content.replace('"""', r'\"\"\"') + '"""', glo_vars=tpl_vars)
    if not content:
        return ""
    content = content.replace(r'\"\"\"', '"""')     # recover docstring delimiters

    suffix = TEMPLATE_PLACEHOLDER_ARGS_SUFFIX
    len_suf = len(suffix)
    all_replacers = DEFAULT_REPLACERS
    all_replacers.update(replacers)
    for key, fun in all_replacers.items():
        prefix = TEMPLATE_PLACEHOLDER_ID_PREFIX + key + TEMPLATE_PLACEHOLDER_ID_SUFFIX
        len_pre = len(prefix)

        beg = 0
        while True:
            beg = content.find(prefix, beg)
            if beg == -1:
                break

            end = content.find(suffix, beg)
            assert end != -1, f"patch_string() {key=} placeholder args-{suffix=} is missing in {content=}; {tpl_vars=}"

            replacement = fun(content[beg + len_pre: end])
            if isinstance(replacement, str):
                content = content[:beg] + replacement + content[end + len_suf:]

    return content


def path_pfx_parametrize_with_context(managed_file: ManagedFile, *_args: str):
    """ path prefix callee for the :data:`F_STRINGS_PATH_PFX` prefix.

    :param managed_file:        ManagedFile instance.
    """
    managed_file.add_content_transformer(transform_parametrize_content)


def path_pfx_refreshable_content(managed_file: ManagedFile, *_args: str):
    """ path prefix callee for the :data:`REFRESHABLE_TEMPLATE_PATH_PFX` prefix.

    :param managed_file:        ManagedFile instance.
    """
    managed_file.refreshable = True
    managed_file.add_content_transformer(transform_refreshable_content)  # postpone check of REFRESHABLE_TEMPLATE_MARKER


DEFAULT_PATH_PREFIXES_PARSERS: PathPrefixesParsers = {
    F_STRINGS_PATH_PFX: (0, path_pfx_parametrize_with_context),
    REFRESHABLE_TEMPLATE_PATH_PFX: (0, path_pfx_refreshable_content),
}
""" mapping of the default path prefixes parsers with to a tuple of the prefix args count and the parser callee. """


def prefix_parser(dst_path: str, prefixes_arg_counts: PathPrefixesArgCounts, args_sep: str = PATH_PREFIXES_ARGS_SEP
                  ) -> tuple[str, PathPrefixesArgs]:
    """ detect path/file name prefixes including their prefix args returning stripped path/file name and prefixes args.

    :param dst_path:            destination file path to parse for path/file name prefixes and args.
    :param prefixes_arg_counts: iterable of tuples with a prefix and the number of args of each prefix.
    :param args_sep:            string/char used as path prefixes args seperator/suffix
    :return:                    tuple with stripped path/file name and a list of tuples with the removed prefix and its
                                prefix args.
    """
    parts = []
    prefixes_args = []
    for name in dst_path.split(os.path.sep):
        name_rest, *name_suffixes = name.split(STOP_PARSING_PATH_PFX, maxsplit=1)
        while match := next(((pfx, cnt) for pfx, cnt in prefixes_arg_counts if name_rest.startswith(pfx)), None):
            prefix, arg_count = match
            args_and_rest = name_rest[len(prefix):].split(args_sep, maxsplit=arg_count)
            prefixes_args.append((prefix, tuple(args_and_rest[:arg_count])))
            name_rest = args_and_rest[-1]
        parts.append("".join([name_rest] + name_suffixes))

    return os_path_join(*parts), prefixes_args


def replace_with_file_content_or_default(args_str: str) -> str:
    """ return file content if the file specified in first string arg exists, else return empty string or 2nd arg str.

    :param args_str:            pass either file name, or file name and default literal separated by a comma character.
                                whitespace (spaces, tabs, newline, cr) get removed from the start/end of the file name.
                                a default literal gets parsed like a config variable, the literal value gets return.
    :return:                    file content or default literal value or empty string (if the file does not exist and
                                there is no comma char in :paramref:`~replace_with_file_content_or_default.args_str`).
    """
    file_name, *default = args_str.split(",", maxsplit=1)
    file_name = file_name.strip()           # strip any surrounding spaces, tabs, and newlines
    return read_file(file_name) if os_path_isfile(file_name) else Literal(default[0]).value if default else ""


def replace_with_template_args(args_str: str) -> str:
    """ template placeholder replacer function to hide uncompleted code from code-inspections/editor-warnings.

    :param args_str:            args string to return, replacing the template placeholder (interpreted as comment in
                                python code).
    :return:                    args string specified as argument of the :data:`TEMPLATE_REPLACE_WITH_PLACEHOLDER_ID`.
    """
    return args_str


DEFAULT_REPLACERS = {
    TEMPLATE_INCLUDE_FILE_PLACEHOLDER_ID: replace_with_file_content_or_default,
    TEMPLATE_REPLACE_WITH_PLACEHOLDER_ID: replace_with_template_args,
}
""" map of default replacers callables used by :func:`patch_string`. """


def transform_parametrize_content(managed_file: ManagedFile) -> str:
    """ content transformer callee added via the :data:`F_STRINGS_PATH_PFX` path prefix.

    :param managed_file:        ManagedFile instance.
    :return:                    transformed file content.
    """
    manager = managed_file.manager
    return patch_string(cast(str, managed_file.file_content), manager.context_vars, **manager.replacers)


def transform_refreshable_content(managed_file: ManagedFile) -> str:
    """ content transformer callee added via the :data:`REFRESHABLE_TEMPLATE_PATH_PFX` path prefix.

    :param managed_file:        ManagedFile instance.
    :return:                    transformed file content.
    """
    if (old_content := managed_file.old_content) and REFRESHABLE_TEMPLATE_MARKER not in old_content[:369]:
        managed_file.skip("missing refreshable content marker in destination file")
        return ""

    new_content = patch_refreshable_content(managed_file.dst_file_path,
                                            cast(str, managed_file.file_content),
                                            managed_file.patcher)
    if old_content == new_content:
        # no managed_file.skip("is up-to-date") to allow lower-priority-skip of later template for same destination file
        managed_file.up_to_date = True

    return new_content
