""" managed_files unit tests """
import os

import pytest
from mypy.util import os_path_join

from ae.base import norm_path, os_path_isfile, os_path_join, read_file, write_file

from ae.managed_files import (
    DEFAULT_PATH_PREFIXES_PARSERS, DEPLOY_LOCK_EXT,
    F_STRINGS_PATH_PFX, REFRESHABLE_TEMPLATE_PATH_PFX, STOP_PARSING_PATH_PFX,
    TEMPLATE_PLACEHOLDER_ID_PREFIX, TEMPLATE_PLACEHOLDER_ID_SUFFIX, TEMPLATE_PLACEHOLDER_ARGS_SUFFIX,
    TEMPLATE_INCLUDE_FILE_PLACEHOLDER_ID, TEMPLATE_REPLACE_WITH_PLACEHOLDER_ID,
    ManagedFile, TemplateMngr,
    deploy_template, patch_refreshable_content, patch_string,
    path_pfx_parametrize_with_context, path_pfx_refreshable_content,
    prefix_parser, replace_with_file_content_or_default, replace_with_template_args,
    transform_parametrize_content, transform_refreshable_content,
    REFRESHABLE_TEMPLATE_MARKER, MANAGED_FILE_ERROR_COMMENT, PATH_PREFIXES_ARGS_SEP)


tst_patcher = 'tst_patcher'
tst_ctx_vars = {'var_name': "_var_value"}
tst_prefix_arg1 = 'pre-fix-arg1'
tst_prefix_arg2 = 'pre-fix-arg2'
tst_tpl_name_rest = "rest{var_name}.tpl"
tst_tpl_file_name = F_STRINGS_PATH_PFX + REFRESHABLE_TEMPLATE_PATH_PFX + tst_tpl_name_rest
tst_dst_file_name = tst_tpl_name_rest.format(**tst_ctx_vars)
tst_tpl_content = "# template file content with {var_name}."
tst_dst_ends_content = tst_tpl_content.format(**tst_ctx_vars)
tst_dst_full_content = patch_refreshable_content("", tst_dst_ends_content, tst_patcher)


def tst_prefix_args_parser(mf: ManagedFile, *args: str):
    assert isinstance(mf, ManagedFile)
    assert args[0] == tst_prefix_arg1
    assert args[1] == tst_prefix_arg2


TST_ARGS_PREFIX = "tst_args_"
TST_PREFIX_PARSERS = {**DEFAULT_PATH_PREFIXES_PARSERS,
                      TST_ARGS_PREFIX: (2, tst_prefix_args_parser)}


@pytest.fixture
def tpl_dir(tmp_path, monkeypatch):
    tmp_dir = str(tmp_path)
    monkeypatch.chdir(tmp_dir)
    return tmp_dir


@pytest.fixture
def man_tst(tpl_dir):
    tpl_file_name = REFRESHABLE_TEMPLATE_PATH_PFX + F_STRINGS_PATH_PFX + STOP_PARSING_PATH_PFX + tst_tpl_file_name
    tpl_file_path = os_path_join(tpl_dir, 'source', tpl_file_name)
    write_file(tpl_file_path, tst_tpl_content, make_dirs=True)
    dst_file_path = os_path_join("dst_dir", tpl_file_name)
    dst_strip_path = os_path_join("dst_dir", tst_tpl_file_name).format(**tst_ctx_vars)
    write_file(os_path_join(tpl_dir, dst_strip_path), REFRESHABLE_TEMPLATE_MARKER, make_dirs=True)

    return TemplateMngr([(tst_patcher, tpl_file_path, dst_file_path)], TST_PREFIX_PARSERS, tst_ctx_vars)


class TestPathPrefixParsers:
    def test_path_pfx_parametrize_with_context(self, man_tst):
        mf = man_tst.managed_files[0]
        assert mf._content_transformers.count(transform_parametrize_content) == 1

        path_pfx_parametrize_with_context(mf)

        assert mf._content_transformers.count(transform_parametrize_content) == 2

    def test_path_pfx_parametrize_with_context_adding_content_transformer(self, man_tst):
        mf = man_tst.managed_files[0]
        
        assert transform_parametrize_content in mf._content_transformers

    def test_path_pfx_refreshable_content(self, man_tst):
        mf = man_tst.managed_files[0]
        assert mf._content_transformers.count(transform_refreshable_content) == 1

        path_pfx_refreshable_content(mf)

        assert mf._content_transformers.count(transform_refreshable_content) == 2

    def test_path_pfx_refreshable_content_adding_content_transformer(self, man_tst):
        mf = man_tst.managed_files[0]

        assert mf.refreshable is True
        assert transform_refreshable_content in mf._content_transformers


class TestContentTransformers:
    def test_transform_parametrize_content(self, man_tst):
        mf = man_tst.managed_files[0]

        assert isinstance(mf.file_content, str)
        assert mf.file_content.count(REFRESHABLE_TEMPLATE_MARKER) == 1
        assert mf.file_content.count(tst_patcher) == 1
        assert mf.file_content.count(tst_dst_ends_content) == 1
        assert mf.file_content.endswith(tst_dst_ends_content)
        assert mf.file_content == tst_dst_full_content

        new_content = transform_parametrize_content(mf)

        assert new_content == mf.file_content

    def test_transform_refreshable_content(self, man_tst):
        mf = man_tst.managed_files[0]

        assert isinstance(mf.file_content, str)
        assert mf.file_content.count(REFRESHABLE_TEMPLATE_MARKER) == 1
        assert mf.file_content.count(tst_patcher) == 1
        assert mf.file_content.count(tst_dst_ends_content) == 1
        assert mf.file_content.endswith(tst_dst_ends_content)
        assert mf.file_content == tst_dst_full_content

        new_content = transform_refreshable_content(mf)

        assert new_content.count(REFRESHABLE_TEMPLATE_MARKER) == 2
        assert new_content.count(tst_patcher) == 2
        assert new_content.count(tst_dst_ends_content) == 1
        assert new_content.endswith(tst_dst_ends_content)
        assert mf.file_content in new_content
        assert mf.file_content == tst_dst_full_content


class TestHelpers:
    def test_deploy_template(self, tpl_dir):
        tpl_file_name = REFRESHABLE_TEMPLATE_PATH_PFX + F_STRINGS_PATH_PFX + 'name_rest' + '{var_name}'
        tpl_file_path = os_path_join(tpl_dir, 'tpl_root', tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content, make_dirs=True)
        dst_path = os_path_join('dst_root', tpl_file_name)

        dst_file = deploy_template(tpl_file_path, dst_path=dst_path,
                                   prefixes_parsers=DEFAULT_PATH_PREFIXES_PARSERS, tpl_vars=tst_ctx_vars)

        assert dst_file
        assert dst_file.endswith(tst_ctx_vars['var_name'])
        assert os_path_isfile(dst_file)
        assert dst_file == norm_path(os_path_join(tpl_dir, 'dst_root', 'name_rest' + tst_ctx_vars['var_name']))
        dst_content = read_file(dst_file)
        assert dst_content.endswith(tst_dst_ends_content)
        assert dst_content.count(REFRESHABLE_TEMPLATE_MARKER) == 1
        assert dst_content.count('deploy_template_default_patcher') == 1
        assert dst_content == tst_dst_full_content.replace(tst_patcher, 'deploy_template_default_patcher')

    def test_deploy_template_skipped_by_locked_file_ext(self, tpl_dir):
        tpl_file_name = REFRESHABLE_TEMPLATE_PATH_PFX + F_STRINGS_PATH_PFX + 'name_rest'
        tpl_file_path = os_path_join(tpl_dir, 'tpl_root', tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content, make_dirs=True)
        dst_path = os_path_join('dst_root', tpl_file_name)
        stripped_dst_path = os_path_join(tpl_dir, 'dst_root', 'name_rest')
        write_file(stripped_dst_path + DEPLOY_LOCK_EXT, "any content", make_dirs=True)

        dst_file = deploy_template(tpl_file_path, dst_path=dst_path,
                                   prefixes_parsers=DEFAULT_PATH_PREFIXES_PARSERS, tpl_vars=tst_ctx_vars)

        assert dst_file == ""
        assert not os_path_isfile(stripped_dst_path)
        assert os_path_isfile(stripped_dst_path + DEPLOY_LOCK_EXT)

    def test_deploy_template_skipped_by_missing_refreshable_marker(self, tpl_dir):
        tpl_file_name = REFRESHABLE_TEMPLATE_PATH_PFX + F_STRINGS_PATH_PFX + 'name_rest'
        tpl_file_path = os_path_join(tpl_dir, 'tpl_root', tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content, make_dirs=True)
        dst_path = os_path_join('dst_root', tpl_file_name)
        stripped_dst_path = os_path_join(tpl_dir, 'dst_root', 'name_rest')

        write_file(stripped_dst_path, "destination file w/o REFRESHABLE_TEMPLATE_MARKER", make_dirs=True)

        dst_file = deploy_template(tpl_file_path, dst_path=dst_path,
                                   prefixes_parsers=DEFAULT_PATH_PREFIXES_PARSERS, tpl_vars=tst_ctx_vars)

        assert dst_file == ""
        assert os_path_isfile(stripped_dst_path)
        assert REFRESHABLE_TEMPLATE_MARKER not in read_file(stripped_dst_path)
        assert not os_path_isfile(stripped_dst_path + DEPLOY_LOCK_EXT)

        write_file(stripped_dst_path, REFRESHABLE_TEMPLATE_MARKER)

        dst_file = deploy_template(tpl_file_path, dst_path=dst_path,
                                   prefixes_parsers=DEFAULT_PATH_PREFIXES_PARSERS, tpl_vars=tst_ctx_vars)

        assert dst_file
        assert dst_file == stripped_dst_path
        assert os_path_isfile(dst_file)
        dst_content = read_file(dst_file)
        assert dst_content.endswith(tst_dst_ends_content)
        assert dst_content.count(REFRESHABLE_TEMPLATE_MARKER) == 1
        assert dst_content.count('deploy_template_default_patcher') == 1
        assert dst_content == tst_dst_full_content.replace(tst_patcher, 'deploy_template_default_patcher')

    def test_deploy_template_skipped_up_to_date_refreshable(self, tpl_dir):
        tpl_file_name = F_STRINGS_PATH_PFX + REFRESHABLE_TEMPLATE_PATH_PFX + 'name_rest'
        tpl_file_path = os_path_join(tpl_dir, 'tpl_root', tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content, make_dirs=True)
        dst_path = os_path_join('dst_root', tpl_file_name)
        stripped_dst_path = os_path_join(tpl_dir, 'dst_root', 'name_rest')

        write_file(stripped_dst_path, tst_dst_full_content, make_dirs=True)

        dst_file = deploy_template(tpl_file_path, dst_path=dst_path, patcher=tst_patcher,
                                   prefixes_parsers=DEFAULT_PATH_PREFIXES_PARSERS, tpl_vars=tst_ctx_vars)

        assert dst_file == ""
        assert os_path_isfile(stripped_dst_path)
        dst_content = read_file(stripped_dst_path)
        assert dst_content.endswith(tst_dst_ends_content)
        assert dst_content.count(REFRESHABLE_TEMPLATE_MARKER) == 1
        assert dst_content.count(tst_patcher) == 1
        assert dst_content == tst_dst_full_content
        assert not os_path_isfile(stripped_dst_path + DEPLOY_LOCK_EXT)

    def test_patch_refreshable_content_any_ext(self):
        content = patch_refreshable_content('patch.file', tst_tpl_content, 'tst patcher')

        assert content.startswith('# ' + REFRESHABLE_TEMPLATE_MARKER)
        assert content.count('tst patcher') == 1
        assert content.endswith(tst_tpl_content)

    def test_patch_refreshable_content_md_ext(self):
        content = patch_refreshable_content('patch.md', tst_tpl_content, 'tst patcher')

        assert content.startswith("<!-- " + REFRESHABLE_TEMPLATE_MARKER)
        assert content.count('tst patcher') == 1
        assert content.endswith(tst_tpl_content)

    def test_patch_refreshable_content_rst_ext(self):
        content = patch_refreshable_content('patch.rst', tst_tpl_content, 'tst patcher')

        assert content.startswith(os.linesep + ".." + os.linesep + " " * 4 + REFRESHABLE_TEMPLATE_MARKER)
        assert content.count('tst patcher') == 1
        assert content.endswith(tst_tpl_content)

    def test_patch_string(self):
        assert patch_string("", tst_ctx_vars) == ""
        assert patch_string(tst_tpl_content, tst_ctx_vars) == tst_dst_ends_content

    def test_patch_string_arg_replacer(self):
        tst_str = ('pre-fix'
                   + TEMPLATE_PLACEHOLDER_ID_PREFIX
                   + TEMPLATE_REPLACE_WITH_PLACEHOLDER_ID
                   + TEMPLATE_PLACEHOLDER_ID_SUFFIX
                   + 'rep-lac-er'
                   + TEMPLATE_PLACEHOLDER_ARGS_SUFFIX
                   + 'suf-fix')
        assert patch_string(tst_str, {}) == 'pre-fix' + 'rep-lac-er' + 'suf-fix'

    def test_patch_string_include_file_replacer(self, tpl_dir):
        tst_str = ('pre-fix'
                   + TEMPLATE_PLACEHOLDER_ID_PREFIX
                   + TEMPLATE_INCLUDE_FILE_PLACEHOLDER_ID
                   + TEMPLATE_PLACEHOLDER_ID_SUFFIX
                   + 'file.name'
                   + TEMPLATE_PLACEHOLDER_ARGS_SUFFIX
                   + 'suf-fix')

        assert patch_string(tst_str, {}) == 'pre-fix' + 'suf-fix'

        write_file('file.name', 'included content')

        assert patch_string(tst_str, {}) == 'pre-fix' + 'included content' + 'suf-fix'

    def test_prefix_parser(self):
        name = "pre_fix_arg1_arg2_rest/sub_rest"

        rest, args = prefix_parser(name, [('pre_fix_', 2)])

        assert rest == 'rest/sub_rest'
        assert isinstance(args, list)
        assert len(args) == 1
        assert args[0] == ('pre_fix_', ('arg1', 'arg2'))

    def test_prefix_parser_arg_sep(self):
        name = "pre_fix_arg1+arg2+arg3+rest+sub+rest"

        rest, parsed = prefix_parser(name, [('pre_fix_', 3)], args_sep="+")

        assert rest == 'rest+sub+rest'
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0] == ('pre_fix_', ('arg1', 'arg2', 'arg3'))

    def test_prefix_parser_multi_prefixes(self):
        name = "pre1_arg1_pre2_arg1_arg2_rest"

        rest, parsed = prefix_parser(name, [('pre1_', 1), ('pre2_', 2)])

        assert rest == 'rest'
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0] == ('pre1_', ('arg1', ))
        assert parsed[1] == ('pre2_', ('arg1', 'arg2'))

    def test_prefix_parser_no_prefixes(self):
        name = "no_prefix_rest"

        rest, parsed = prefix_parser(name, [('prefix_', 9)])

        assert rest == 'no_prefix_rest'
        assert isinstance(parsed, list)
        assert len(parsed) == 0

        rest, parsed = prefix_parser(name, [('prefix_', 0)])

        assert rest == 'no_prefix_rest'
        assert isinstance(parsed, list)
        assert len(parsed) == 0

    def test_prefix_parser_paths(self):
        path = "pre_fix_rest_dir1/pre_fix_rest_dir2/pre_fix_rest_name"

        rest, pfx_args = prefix_parser(path, [('pre_fix_', 0)])

        assert rest == "rest_dir1/rest_dir2/rest_name"
        assert len(pfx_args) == 3
        assert pfx_args[0] == ('pre_fix_', ())
        assert pfx_args[1] == ('pre_fix_', ())
        assert pfx_args[2] == ('pre_fix_', ())

    def test_prefix_parser_paths_with_args(self):
        path = "pfx_arg1_rest_dir1/pfx_arg2_rest_dir2/pfx_arg3_rest_name"

        rest, pfx_args = prefix_parser(path, [('pfx_', 1)])

        assert rest == "rest_dir1/rest_dir2/rest_name"
        assert len(pfx_args) == 3
        assert pfx_args[0] == ('pfx_', ('arg1', ))
        assert pfx_args[1] == ('pfx_', ('arg2', ))
        assert pfx_args[2] == ('pfx_', ('arg3', ))

    def test_prefix_parser_with_stopper(self):
        name = f"prefix_arg1_{STOP_PARSING_PATH_PFX}prefix_no_args_rest"

        rest, parsed = prefix_parser(name, [('prefix_', 1)], args_sep="_")

        assert rest == 'prefix_no_args_rest'
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0] == ('prefix_', ('arg1', ))

    def test_prefix_parser_zero_args(self):
        name = "pre_fix_rest"

        rest, parsed = prefix_parser(name, [('pre_fix_', 0)])

        assert rest == 'rest'
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0] == ('pre_fix_', ())


class TestReplacers:
    def test_replace_with_file_content_or_default_arg_only(self, tpl_dir):
        args = " " + 'tst_fil_nam' + " \t \n "

        assert replace_with_file_content_or_default(args) == ""

        write_file('tst_fil_nam', 'tst_fil_content')

        assert replace_with_file_content_or_default(args) == 'tst_fil_content'

    def test_replace_with_file_content_or_default_defaults(self):
        args = "arg_val," + 'def_val'

        assert replace_with_file_content_or_default(args) == 'def_val'

        args = "arg_val," + "'def_val'"
        assert replace_with_file_content_or_default(args) == 'def_val'

        args = "arg_val," + "['def_val']"
        assert replace_with_file_content_or_default(args) == ['def_val']

    def test_replace_with_template_args(self):
        assert replace_with_template_args("") == ""
        assert replace_with_template_args('arg_val') == "arg_val"
        assert replace_with_template_args('arg,val') == "arg,val"
        assert replace_with_template_args('[arg,val )') == "[arg,val )"


class TestTemplateMngr:
    def test_an_empty_instance(self):
        man = TemplateMngr([], {}, {})

        assert man
        assert man.checked_files == set()
        assert 'TEMPLATE_PLACEHOLDER_ID_PREFIX' in man.context_vars
        assert man.deploy_files == {}
        assert man.log_lines() == []
        assert man.log_lines(verbose=True) == []
        assert man.managed_files == []
        assert man.missing_files == set()
        assert man.outdated_files == []
        assert man.path_prefixes_arg_counts == []
        assert man.path_prefixes_parsers == {}
        assert man.replacers == {}
        assert man.skipped_files == set()
        assert man.template_files == []

    def test_content_encoding_mismatch_error(self, tpl_dir):
        def content_transformer(_mf: ManagedFile) -> str:
            return "any new content"

        def path_pfx_parser2(mf: ManagedFile, *_args):
            mf.add_content_transformer(content_transformer, encoding='ascii')

        pfx_parsers = DEFAULT_PATH_PREFIXES_PARSERS.copy()
        pfx_parsers[REFRESHABLE_TEMPLATE_PATH_PFX] = (0, path_pfx_parser2)

        tpl_file_path = os_path_join(tpl_dir, tst_tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content)
        man = TemplateMngr(
            [(tst_patcher, tpl_file_path, tst_tpl_file_name)],
            pfx_parsers,
            tst_ctx_vars)

        assert man.deploy_files == {}
        assert len(man.log_lines()) == 0
        assert len(man.log_lines(verbose=True)) == 2
        assert man.managed_files[0].skip_or_error
        assert len(man.managed_files[0].comments) == 1
        assert man.managed_files[0].comments[0].startswith(MANAGED_FILE_ERROR_COMMENT)

    def test_content_type_mismatch_error(self, tpl_dir):
        def content_transformer(_mf: ManagedFile) -> str:
            return "any new content"

        def path_pfx_parser2(mf: ManagedFile, *_args):
            mf.add_content_transformer(content_transformer, extra_mode='b')

        pfx_parsers = DEFAULT_PATH_PREFIXES_PARSERS.copy()
        pfx_parsers[REFRESHABLE_TEMPLATE_PATH_PFX] = (0, path_pfx_parser2)

        tpl_file_path = os_path_join(tpl_dir, tst_tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content)
        man = TemplateMngr(
            [(tst_patcher, tpl_file_path, tst_tpl_file_name)],
            pfx_parsers,
            tst_ctx_vars)

        assert man.deploy_files == {}
        assert len(man.log_lines()) == 0
        assert len(man.log_lines(verbose=True)) == 2
        assert man.managed_files[0].skip_or_error
        assert len(man.managed_files[0].comments) == 1
        assert man.managed_files[0].comments[0].startswith(MANAGED_FILE_ERROR_COMMENT)

    def test_deployment(self, tpl_dir):
        write_file(tst_tpl_file_name, tst_tpl_content)
        prefixed_path = os_path_join('dst_tst_dir', tst_tpl_file_name)
        dst_file_path = os_path_join('dst_tst_dir', tst_dst_file_name)
        man = TemplateMngr(
            [(tst_patcher, tst_tpl_file_name, prefixed_path)],
            DEFAULT_PATH_PREFIXES_PARSERS,
            tst_ctx_vars)

        assert len(man.deploy_files) == 1
        assert next(iter(man.deploy_files)) == norm_path(dst_file_path)
        assert len(man.log_lines()) == 1
        assert len(man.log_lines(verbose=True)) == 2
        assert len(man.managed_files[0].comments) == 0

        assert not os_path_isfile(dst_file_path)

        man.deploy()

        assert os_path_isfile(dst_file_path)

        assert read_file(dst_file_path) == tst_dst_full_content
        assert len(man.deploy_files) == 1
        assert next(iter(man.deploy_files)) == norm_path(dst_file_path)
        assert len(man.log_lines()) == 1
        assert len(man.log_lines(verbose=True)) == 2
        assert len(man.managed_files[0].comments) == 0

    def test_file_path_extension(self, tpl_dir):
        def path_pfx_parser(mf: ManagedFile, *_args):
            mf.extend_dst_file_path('ext_dir1/ext_dir2')

        tpl_file_path = os_path_join(tpl_dir, tst_tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content)
        man = TemplateMngr(
            [(tst_patcher, tpl_file_path, tst_tpl_file_name)],
            {F_STRINGS_PATH_PFX: (0, path_pfx_parser)},
            tst_ctx_vars)

        assert len(man.log_lines()) == 1
        assert len(man.log_lines(verbose=True)) == 2
        assert man.managed_files[0].dst_file_path.startswith('ext_dir1/ext_dir2')
        assert not man.managed_files[0].comments
        assert len(man.deploy_files) == 1

    def test_file_path_extension_warning_if(self, tpl_dir):
        def path_pfx_parser(mf: ManagedFile, *_args):
            mf.extend_dst_file_path('old_dir0/old_dir2')
            mf.extend_dst_file_path('ext_dir1/ext_dir2')

        tpl_file_path = os_path_join(tpl_dir, tst_tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content)
        man = TemplateMngr(
            [(tst_patcher, tpl_file_path, tst_tpl_file_name)],
            {F_STRINGS_PATH_PFX: (0, path_pfx_parser)},
            tst_ctx_vars)

        assert len(man.log_lines()) == 1
        assert len(man.log_lines(verbose=True)) == 3
        assert man.managed_files[0].dst_file_path.startswith('ext_dir1/ext_dir2')
        assert len(man.managed_files[0].comments) == 1
        assert len(man.deploy_files) == 1

    def test_file_path_in_prefix_path_compilation(self, tpl_dir):
        def f_str_parser(mf: ManagedFile, *_args):
            assert mf.dst_file_path == tst_dst_file_name
            path_pfx_parametrize_with_context(mf)

        def refreshable_parser(mf: ManagedFile):
            assert mf.dst_file_path == tst_dst_file_name
            path_pfx_refreshable_content(mf)

        tpl_file_path = os_path_join(tpl_dir, tst_tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content)
        man = TemplateMngr(
            [(tst_patcher, tpl_file_path, tst_tpl_file_name)],
            {F_STRINGS_PATH_PFX: (0, f_str_parser),
             REFRESHABLE_TEMPLATE_PATH_PFX: (0, refreshable_parser)},
            tst_ctx_vars)

        assert len(man.deploy_files) == 1

    def test_multiple_refreshable_path_prefix_warning(self, tpl_dir):
        dst_path = os_path_join(REFRESHABLE_TEMPLATE_PATH_PFX + "dir_name", tst_tpl_file_name)
        tpl_file_path = os_path_join(tpl_dir, dst_path)
        write_file(tpl_file_path, tst_tpl_content, make_dirs=True)
        man = TemplateMngr(
            [(tst_patcher, tpl_file_path, dst_path)],
            DEFAULT_PATH_PREFIXES_PARSERS,
            tst_ctx_vars)

        assert len(man.deploy_files) == 1
        assert len(man.log_lines()) == 1
        assert len(man.log_lines(verbose=True)) == 3
        assert len(man.managed_files[0].comments) == 1

    def test_path_prefix_with_args(self, tpl_dir):
        dst_path = (TST_ARGS_PREFIX
                    + tst_prefix_arg1 + PATH_PREFIXES_ARGS_SEP
                    + tst_prefix_arg2 + PATH_PREFIXES_ARGS_SEP
                    + tst_tpl_file_name)
        write_file(tst_tpl_file_name, tst_tpl_content)
        man = TemplateMngr(
            [(tst_patcher, tst_tpl_file_name, dst_path)],
            TST_PREFIX_PARSERS,
            tst_ctx_vars)

        assert len(man.deploy_files) == 1
        assert len(man.log_lines()) == 1
        assert len(man.log_lines(verbose=True)) == 2
        assert len(man.managed_files[0].comments) == 0

    def test_refreshable_path_prefix_parser_runs_last_and_only_once(self, tpl_dir):
        def f_str_parser(mf: ManagedFile, *_args):
            if 'run-refreshable' in mf.manager.context_vars:
                mf.error("run of refreshable parser BEFORE f_str_parser")
            if 'run-f-string-parser' in mf.manager.context_vars:
                mf.error("duplicate run of f_str_parser")
            mf.manager.context_vars['run-f-string-parser'] = True
            path_pfx_parametrize_with_context(mf)

        def refreshable_parser(mf: ManagedFile):
            if 'run-f-string-parser' not in mf.manager.context_vars:
                mf.error("run of refreshable parser without run of f_str_parser")
            if 'run-refreshable' in mf.manager.context_vars:
                mf.error("duplicate run of refreshable prefix parser")
            mf.manager.context_vars['run-refreshable'] = True
            path_pfx_refreshable_content(mf)

        dst_path = REFRESHABLE_TEMPLATE_PATH_PFX + F_STRINGS_PATH_PFX + "fil_nam.xxx"
        tpl_file_path = os_path_join(tpl_dir, tst_tpl_file_name)
        write_file(tpl_file_path, tst_tpl_content)
        man = TemplateMngr(
            [(tst_patcher, tpl_file_path, dst_path)],
            {F_STRINGS_PATH_PFX: (0, f_str_parser),
             REFRESHABLE_TEMPLATE_PATH_PFX: (0, refreshable_parser)},
            tst_ctx_vars)

        assert not man.managed_files[0].skip_or_error
        assert len(man.deploy_files) == 1
        assert len(man.log_lines()) == 1
        assert len(man.log_lines(verbose=True)) == 2
        assert len(man.managed_files[0].comments) == 0

    def test_representations(self, tpl_dir):
        dst_path = "dst_file_name.ext"
        tpl_file_path = os_path_join(tpl_dir, dst_path)     # source == dest
        write_file(tpl_file_path, tst_tpl_content)
        man = TemplateMngr(
            [(tst_patcher, tpl_file_path, dst_path)],
            DEFAULT_PATH_PREFIXES_PARSERS,
            tst_ctx_vars)

        man_repr = repr(man)
        assert hex(id(man)) in man_repr

        fil_repr = repr(man.managed_files[0])
        assert hex(id(man.managed_files[0])) in fil_repr
        assert dst_path in fil_repr
        assert tst_patcher in fil_repr
        assert 'skip_or_error' in fil_repr
        assert 'refreshable' not in fil_repr
        assert 'up_to_date' not in fil_repr

    def test_skip_lower_priority(self, tpl_dir):
        dst_file = "dst_file_name.ext"
        dst_path = REFRESHABLE_TEMPLATE_PATH_PFX + dst_file
        tpl_file_path1 = os_path_join(tpl_dir, 'tpl_file_name.ext1')
        write_file(tpl_file_path1, tst_tpl_content + 'tst_content_1')
        tpl_file_path2 = os_path_join(tpl_dir, 'tpl_file_name.ext2')
        write_file(tpl_file_path2, tst_tpl_content + 'tst_content_2')

        man = TemplateMngr(
            [(tst_patcher + '1', tpl_file_path1, dst_path),
             (tst_patcher + '2', tpl_file_path2, dst_path)],
            DEFAULT_PATH_PREFIXES_PARSERS,
            tst_ctx_vars)

        assert len(man.deploy_files) == 1
        assert next(iter(man.deploy_files), "") == norm_path(dst_file)
        mf = next(iter(man.deploy_files.values()))
        assert mf.file_content.endswith('tst_content_1')
        assert not mf.up_to_date
        assert len(man.log_lines()) == 1
        assert len(man.log_lines(verbose=True)) == 4    # 2 templates processed, 1st add/miss, 2nd lower-priority-skip
        assert len(man.managed_files[0].comments) == 0

        # same test again but with existing and identical destination file; check for mf.up_to_date flag
        write_file(dst_file, patch_refreshable_content(dst_file, tst_tpl_content + 'tst_content_1', tst_patcher + '1'))

        man = TemplateMngr(
            [(tst_patcher + '1', tpl_file_path1, dst_path),
             (tst_patcher + '2', tpl_file_path2, dst_path)],
            DEFAULT_PATH_PREFIXES_PARSERS,
            tst_ctx_vars)

        assert len(man.deploy_files) == 1
        mf = next(iter(man.deploy_files.values()))
        assert mf.up_to_date
        assert mf.file_content.endswith('tst_content_1')
        assert len(man.log_lines()) == 1
        assert len(man.log_lines(verbose=True)) == 4    # 2 templates processed, 1st add/miss, 2nd lower-priority-skip
        assert len(man.managed_files[0].comments) == 0

    def test_skip_non_refreshable_if_exists(self, tpl_dir):
        dst_path = "dst_file_name.ext"
        tpl_file_path = os_path_join(tpl_dir, dst_path)     # source == dest
        write_file(tpl_file_path, tst_tpl_content)
        man = TemplateMngr(
            [(tst_patcher, tpl_file_path, dst_path)],
            DEFAULT_PATH_PREFIXES_PARSERS,
            tst_ctx_vars)

        assert len(man.deploy_files) == 0
        assert len(man.log_lines()) == 0
        assert len(man.log_lines(verbose=True)) == 2
        assert len(man.managed_files[0].comments) == 1
