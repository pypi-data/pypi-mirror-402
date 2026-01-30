import inspect
import json
import re
from collections import namedtuple
from pathlib import Path
from typing import Callable, Iterable, Optional

import black


class TemplateException(Exception):
    """Used for exceptions during template construction and fill."""

    pass


def _get_body(func):

    source_lines = inspect.getsource(func).splitlines()
    first_line = source_lines[0]
    if not re.match(r"def \w+\((\w+(, \w+)*)?\):", first_line.strip()):
        # Parsing to AST and unparsing is a more robust option,
        # but more complicated.
        raise TemplateException(
            f"def and parameters should fit on one line: {first_line}"
        )

    # The "def" should not be in the output,
    # and cleandoc handles the first line differently.
    source_lines[0] = ""
    body = inspect.cleandoc("\n".join(source_lines))

    return body


def _check_repr(value):
    """
    Confirms that the string returned by repr()
    can be evaluated to recreate the original value.
    Takes a conservative approach by checking
    if the value can be serialized to JSON.
    """
    try:
        json.dumps(value)
    except TypeError as e:
        raise TemplateException(e.args[0])
    return repr(value)


def _check_kwargs(func):
    def wrapper(*args, **kwargs):
        WHEN = "when"
        OPTIONAL = "optional"
        errors = []
        for k in kwargs.keys():
            if k in args[0]._ignore:
                errors.append(f'kwarg "{k}" is an ignored slot name')
            if not (re.fullmatch(_slot_re, k) or k == WHEN or k == OPTIONAL):
                errors.append(f'kwarg "{k}" is not a valid slot name')
        if errors:
            raise TemplateException(
                "; ".join(errors)
                + f'. Slots should match "{_slot_re}". '
                + "Some slots are ignored, and should not be filled: "
                + ",".join(f'"{v}"' for v in args[0]._ignore)
            )
        if not kwargs.get(WHEN, True):
            # return self:
            return args[0]
        kwargs.pop(WHEN, None)
        return func(*args, **kwargs)

    return wrapper


_Token = namedtuple("_Token", ["string", "is_slot", "is_prefix", "is_period"])


_line_re = re.compile(r"(^[ \t]*(?:#\s*)?)", flags=re.MULTILINE)
_slot_re = re.compile(r"(\.?)(\b[A-Z][A-Z_]{2,}\b)")


def _text_token(string):
    return _Token(
        string,
        is_prefix=False,
        is_slot=False,
        is_period=False,
    )


class _Slots:

    def __init__(self, template: str):
        self._tokens = []
        for i, line_substring in enumerate(_line_re.split(template)):
            if i % 2 == 1:
                # Include prefix, even if empty string.
                self._tokens.append(
                    _Token(
                        line_substring,
                        is_prefix=True,
                        is_slot=False,
                        is_period=False,
                    )
                )
            else:
                for j, slot_substring in enumerate(_slot_re.split(line_substring)):
                    if slot_substring:
                        self._tokens.append(
                            _Token(
                                slot_substring,
                                is_prefix=False,
                                is_slot=j % 3 == 2,
                                is_period=j % 3 == 1,
                            )
                        )

    def _fill(
        self,
        slot_name: str,
        new_value: str,
        error_if_no_match=True,
        fill_inline=True,
        require_period=False,
    ):
        found_match = False
        for i in range(len(self._tokens)):
            if self._tokens[i].is_slot and self._tokens[i].string == slot_name:
                found_match = True
                if require_period and not new_value:
                    if i == 0 or not self._tokens[i - 1].is_period:
                        raise TemplateException(f"No preceding period: {slot_name=}")
                    self._tokens[i - 1] = _text_token("")
                if fill_inline:
                    self._tokens[i] = _text_token(new_value)
                else:
                    prev = self._tokens[i - 1]
                    if not prev.is_prefix:
                        raise TemplateException("expected prefix")
                    prefix = prev.string
                    self._tokens[i] = _text_token(
                        f"\n{prefix}".join(new_value.splitlines())
                    )
        if error_if_no_match and not found_match:
            raise TemplateException(f"no '{slot_name}' slot to fill with '{new_value}'")

    def fill_inline(
        self,
        slot_name: str,
        new_value: str,
        error_if_no_match=True,
        require_period=False,
    ):
        self._fill(
            slot_name,
            new_value,
            error_if_no_match=error_if_no_match,
            require_period=require_period,
        )

    def fill_block(
        self,
        slot_name: str,
        new_value: str,
        error_if_no_match=True,
    ):
        self._fill(
            slot_name,
            new_value,
            error_if_no_match=error_if_no_match,
            fill_inline=False,
        )

    def finish(self, ignore: Iterable[str] = tuple()):
        unfilled = ", ".join(
            token.string
            for token in self._tokens
            if token.is_slot and token.string not in ignore
        )
        if unfilled:
            raise TemplateException(f"unfilled slots: {unfilled}")
        return self.preview()

    def preview(self):
        return "".join(token.string for token in self._tokens)


class Template:
    """
    For all `fill_*` methods, all-caps kwargs should match slots in the template.

    Additionally:
    - With `when=False` slot filling will be skipped.
      This allows method chaining that is more readable than using `if`.
    - With `optional=True` there will be no exceptions for missing slots.
    """

    def __init__(
        self,
        template: str | Callable,
        root: Optional[Path] = None,
        ignore: Iterable[str] = ("TODO",),
    ):
        """
        If called without `root`, either a function or
        a string literal `template` can be given.

        If called with a `root` path, `template` is
        prefixed with "_" and suffixed with ".py"
        and the corresponding file is read.

        Use `ignore` to specify all-caps strings
        which should not be treated as slots.
        """
        if root is None:
            if callable(template):
                self._source = "function template"
                body = _get_body(template)
            else:
                self._source = "string template"
                body = template
        else:
            if callable(template):
                raise TemplateException(
                    "If template is function, root kwarg not allowed"
                )
            else:
                template_name = f"_{template}.py"
                template_path = root / template_name
                self._source = f"'{template_name}'"
                body = template_path.read_text()

        comments_to_strip = [
            # Not perfect, but without getting an AST
            # we can't relly tell if one of these is a comment or not.
            r"\s*#\s*type:\s*ignore\s*$",
            r"\s*#\s*noqa:\s*\w+\s*$",
            r"\s*#\s*pragma:\s*no cover\s*$",
        ]
        for comment_re in comments_to_strip:
            body = re.sub(
                comment_re,
                "",
                body,
                flags=re.MULTILINE,
            )
        self._slots = _Slots(body)

        self._ignore = ignore

    def _make_message(self, errors: list[str]) -> str:
        return (
            f"In {self._source}, "
            + ", ".join(sorted(errors))
            + f":\n{self._slots.preview()}"
        )

    def _loop_kwargs(
        self,
        function: Callable[[str, str, list[str]], None],
        **kwargs,
    ) -> None:
        errors = []
        for k, v in kwargs.items():
            function(k, v, errors)
        if errors:
            raise TemplateException(self._make_message(errors))

    def _fill_inline_slots(
        self,
        stringifier: Callable[[str], str],
        optional: bool,
        require_period: bool = False,
        **kwargs,
    ) -> None:
        def function(k, v, errors):
            try:
                self._slots.fill_inline(
                    k,
                    stringifier(v),
                    error_if_no_match=not optional,
                    require_period=require_period,
                )
            except TemplateException as e:
                errors.append(", ".join(e.args))

        self._loop_kwargs(function, **kwargs)

    def _fill_block_slots(
        self,
        stringifier: Callable[[str], str],
        optional: bool,
        **kwargs,
    ) -> None:
        def function(k, v, errors):
            try:
                self._slots.fill_block(
                    k, stringifier(v), error_if_no_match=not optional
                )
            except TemplateException as e:
                errors.append(", ".join(e.args))

        self._loop_kwargs(function, **kwargs)

    @_check_kwargs
    def fill_expressions(self, optional=False, **kwargs) -> "Template":
        """
        Fill in variable names and anything else that should be filled verbatim.
        """
        self._fill_inline_slots(stringifier=str, optional=optional, **kwargs)
        return self

    @_check_kwargs
    def fill_values(self, optional=False, **kwargs) -> "Template":
        """
        Fill in JSON-serializable values.
        """
        self._fill_inline_slots(stringifier=_check_repr, optional=optional, **kwargs)
        return self

    @_check_kwargs
    def fill_attributes(self, optional=False, **kwargs) -> "Template":
        """
        If value is falsy, preceding `.` in the template is also cleared.
        """

        def make_falsy_empty(input):
            if not input:
                return ""
            return str(input)

        self._fill_inline_slots(
            stringifier=make_falsy_empty,
            optional=optional,
            require_period=True,
            **kwargs,
        )
        return self

    @_check_kwargs
    def fill_blocks(self, optional=False, **kwargs) -> "Template":
        """
        Fill in code or comment blocks. Leading whitespace and "#" will be
        repeated for each line in the fill value.
        """
        self._fill_block_slots(stringifier=str, optional=optional, **kwargs)
        return self

    def finish(self, reformat: bool = False) -> str:
        """
        Confirms that all slots are filled and returns the resulting string.
        If `reformat` is supplied, code is formatted with black.

        If you have values that that should be optional defaults,
        consider subclassing `Template`, and overriding `finish()`. For example:
        ```python
        class TemplateWithDefaultVersion(Template):
            def finish(self, reformat=False):
                self.fill_expressions(VERSION="0.1.2.3", optional=True)
                return super().finish(reformat=reformat)
        ```
        """
        # The reformat default is False here,
        # because it is true downstream for notebook generation,
        # and we don't need to be redundant.

        finished = self._slots.finish(self._ignore)
        if not reformat:
            return finished

        # Final strip() helps with tutorial.md doctests:
        # With a "\n" at the end, doctests need to include
        # <BLANKLINE>
        return black.format_str(finished, mode=black.Mode()).strip()
