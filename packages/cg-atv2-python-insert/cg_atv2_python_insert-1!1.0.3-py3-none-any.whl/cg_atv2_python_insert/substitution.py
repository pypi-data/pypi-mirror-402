"""
This module provides functionality to parse a Python script, identify specific
'magic comments', and substitute these comments with code from other files.
It's designed to be used in environments where code templates and supplementary
files are involved, such as automated grading or code templating systems.

The script supports command-line interaction, allowing users to specify the
file to be processed. It then reads through the specified Python script, looks
for magic comments in the format '# CG_INSERT <filename>', and replaces these
comments with the contents of the referenced file, executing it as part of the
script.
"""

import argparse
import enum
import os
import re
import traceback
import typing as t
from pathlib import Path

import libcst as cst

MAGIC_COMMENT_PREFIX = t.final('CG_INSERT')


class ExitCodes(enum.IntEnum):
    """Enumeration for exit codes."""

    #: Exit code for successful execution.
    SUBSTITUTION_CORRECT = 0
    # 1 is reserved for unknown errors.
    #: Exit code when the source file is not found.
    SOURCE_FILE_NOT_FOUND = 2
    #: Exit code when the source file has parsing errors.
    SOURCE_FILE_CONTAINS_ERRORS = 3
    #: Exit code when the source file contains magic comment in forbidden scopes.
    MAGIC_COMMENT_IN_FORBIDDEN_SCOPE = 4
    #: Exit code when the source file does not contain any magic comment.
    COMMENTS_NOT_FOUND = 5


class SourceFileMissingError(FileNotFoundError):
    """Exception raised when the source file is missing.

    filename: The filename of the source file that was not found.
    """

    def __init__(
        self, filename: t.Union[str, Path], *args: t.Any, **kwargs: t.Any
    ) -> None:
        super().__init__(
            f'Could not find template file {filename}', *args, **kwargs
        )


class SourceFileParseError(Exception):
    """Exception for parsing errors in the source file.

    filename: The filename of the source file that failed to parse.
    """

    def __init__(
        self, filename: t.Union[str, Path], *args: t.Any, **kwargs: t.Any
    ):
        super().__init__(
            f'Error while parsing template file {filename}', *args, **kwargs
        )


class DisallowedScopeError(ValueError):
    """Exception raised when a magic comment is found in a class or function."""

    def __init__(self, line_no: t.List[int], *args: t.Any, **kwargs: t.Any):
        super().__init__(
            'Magic comment found in a forbidden scope at'
            f' line(s): {", ".join(map(str, line_no))}.'
            ' Substitutions within a class or function are not allowed.',
            *args,
            **kwargs,
        )


class MissingMagicCommentsError(ValueError):
    """Exception raised when a magic comment is found in a class or function."""

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(
            'No magic CG_INSERT comments were found within the file.',
            *args,
            **kwargs,
        )


def get_exec_call(
    sub_file_name: str, config: cst.PartialParserConfig
) -> cst.CSTNode:
    """Generates an Exec call node for the AST.

    :param sub_file_name: The name of the file to be executed.
    :param config: The parsing configuration.

    :returns: The constructed Exec call node.
    """
    repr_name = repr(sub_file_name)
    return cst.parse_statement(
        f"""try:
    exec(compile(open({repr_name}).read(), {repr_name}, 'exec'), globals())
except SystemExit as e:
    raise ValueError("Exit calls are not allowed") from e
""",
        config,
    )


class MagicCommentTransformer(cst.CSTTransformer):
    """AST transformer for handling magic comments.

    This class traverses the AST and replaces nodes with special
    magic comments with corresponding Exec call nodes.

        :param config: Configuration for module parsing.
    """

    METADATA_DEPENDENCIES = (
        cst.metadata.PositionProvider,  # type: ignore[attr-defined]
    )

    def __init__(self, module_config: cst.PartialParserConfig):
        self.config = module_config
        self.class_count = 0
        self.func_count = 0
        self.magic_comment_count = 0
        self.invalid_magic_comment_lines: t.List[int] = []

    def visit_FunctionDef_body(self, node: cst.FunctionDef) -> None:
        self.func_count += 1

    def visit_ClassDef_body(self, node: cst.ClassDef) -> None:
        self.class_count += 1

    def leave_EmptyLine(
        self,
        original_node: cst.EmptyLine,
        updated_node: cst.CSTNodeT,
    ) -> cst.CSTNodeT:
        """Replaces EmptyLine nodes with magic comments with Exec call nodes.

        :param original_node: The node that is being left.
        :param updated_node: The updated node.

        :returns: The updated node, possibly replaced by an Exec call node.
        """
        if (
            isinstance(original_node, cst.EmptyLine)
            and original_node.comment is not None
        ):
            re_result = re.search(
                r'^#+\s+(CG_INSERT)\s+(?P<file>\S+)$',
                original_node.comment.value,
            )
            if re_result is not None:
                if self.class_count != 0 or self.func_count != 0:
                    pos = self.get_metadata(
                        cst.metadata.PositionProvider,  # type: ignore[attr-defined]
                        original_node,
                    ).start
                    self.invalid_magic_comment_lines.append(pos.line)
                    return t.cast(cst.CSTNodeT, original_node)

                sub_file = str(re_result.group('file'))
                # The typing in libCST do not really allow to substitute a
                # Node for one that is of another type even if they do provide
                # example where this is done.
                # An issue has been opened on GitHub
                # https://github.com/Instagram/LibCST/issues/1055
                updated_node = t.cast(
                    cst.CSTNodeT, get_exec_call(sub_file, self.config)
                )
                self.magic_comment_count += 1
        return updated_node

    def leave_FunctionDef_body(self, _: cst.FunctionDef) -> None:
        self.func_count -= 1

    def leave_ClassDef_body(
        self,
        _: cst.ClassDef,
    ) -> None:
        self.class_count -= 1


def parse_file(filename: Path) -> cst.MetadataWrapper:
    """Parses the given file into an AST module.

    :param filename: The name of the file to parse.

    :returns: The parsed module.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        return cst.metadata.MetadataWrapper(  # type: ignore[attr-defined]
            cst.parse_module(content),
        )


def substitute(filename: Path) -> str:
    """Performs substitution in the given file based on magic comments.

    :param filename: The name of the file to perform substitution in.

    :returns: The modified file content after substitution.

    raises:
        SourceFileMissingError: If the file is missing.
        SourceFileParseError: If there is a parsing error in the file.
    """
    if not os.path.exists(filename):
        raise SourceFileMissingError(filename)
    try:
        tree = parse_file(filename)
    except cst.ParserSyntaxError as e:
        raise SourceFileParseError(filename) from e

    transformer = MagicCommentTransformer(tree.module.config_for_parsing)
    output = tree.visit(transformer).code
    if len(transformer.invalid_magic_comment_lines) > 0:
        raise DisallowedScopeError(transformer.invalid_magic_comment_lines)
    if transformer.magic_comment_count == 0:
        raise MissingMagicCommentsError
    return output


def main(argv: t.List[str]) -> int:
    """The main function for the script.

    Parses command-line arguments and processes the file accordingly.

        :param argv: Command-line arguments passed to the script.
    """
    parser = argparse.ArgumentParser(
        prog='cg_atv2_python_insert',
        description=(
            'This program reads through a python script, and'
            ' incorporates additional code from other files where it finds'
            f' a specific comment reading {MAGIC_COMMENT_PREFIX} filename'
        ),
        epilog='Usage: python cg_simple_python_test [filename]',
    )

    parser.add_argument(
        'filename',
        type=Path,
        help='The relative path to the template file containing the magic comments.',
    )

    filename = parser.parse_args(argv).filename

    try:
        output = substitute(filename)
    except SourceFileMissingError:
        traceback.print_exc()
        return ExitCodes.SOURCE_FILE_NOT_FOUND
    except SourceFileParseError:
        traceback.print_exc()
        return ExitCodes.SOURCE_FILE_CONTAINS_ERRORS
    except DisallowedScopeError:
        traceback.print_exc()
        return ExitCodes.MAGIC_COMMENT_IN_FORBIDDEN_SCOPE
    except MissingMagicCommentsError:
        traceback.print_exc()
        return ExitCodes.COMMENTS_NOT_FOUND

    output_file = filename.name
    with open(f'filled_{output_file}', 'w', encoding='utf-8') as f:
        f.write(output)

    return ExitCodes.SUBSTITUTION_CORRECT
