import re
from pathlib import Path

import pytest

from dp_wizard_templates.code_template import (
    Template,
    TemplateException,
    _line_re,
    _slot_re,
    _Slots,
    _Token,
)


def test_line_re():
    assert _line_re.split("normal\n  indent\n  # comment") == [
        "",  # Always zero-length
        "",  # prefix
        "normal\n",
        "  ",  # prefix
        "indent\n",
        "  # ",  # prefix
        "comment",
    ]


def test_slot_re():
    assert _slot_re.split("A AB ABC.ABC_XYZ TODO N0_NUMBERS") == [
        "A AB ",
        "",  # optional period
        "ABC",  # slot
        "",
        ".",  # optional period
        "ABC_XYZ",  # slot
        " ",
        "",  # optional period
        "TODO",  # slot
        " N0_NUMBERS",
    ]


def prefix(string):
    return _Token(string, is_slot=False, is_prefix=True, is_period=False)


def slot(string):
    return _Token(string, is_slot=True, is_prefix=False, is_period=False)


def text(string):
    return _Token(string, is_slot=False, is_prefix=False, is_period=False)


def period(string):
    return _Token(string, is_slot=False, is_prefix=False, is_period=True)


def test_slots_fill_inline():
    slots = _Slots("START and THE.END.")
    assert slots._tokens == [
        prefix(""),
        slot("START"),
        text(" and "),
        slot("THE"),
        period("."),
        slot("END"),
        text("."),
    ]
    slots.fill_inline("START", "END")
    slots.fill_inline("END", "START")
    slots.fill_inline("THE", "")
    assert slots.finish() == "END and .START."


def test_slots_fill_block():
    slots = _Slots(
        """intro
CODE
    INDENTED
    # COMMENT"""
    )
    assert slots._tokens == [
        prefix(""),
        text("intro\n"),
        prefix(""),
        slot("CODE"),
        text("\n"),
        prefix("    "),
        slot("INDENTED"),
        text("\n"),
        prefix("    # "),
        slot("COMMENT"),
    ]
    slots.fill_block("CODE", "if 'hello world':")
    slots.fill_block("INDENTED", "if foo:\n    bar()")
    slots.fill_block("COMMENT", "multi\nline")
    assert (
        slots.finish()
        == """intro
if 'hello world':
    if foo:
        bar()
    # multi
    # line"""
    )


def test_non_repr_value():
    def template(VALUE):
        print(VALUE)

    with pytest.raises(
        TemplateException,
        match=r"Object of type set is not JSON serializable",
    ):
        Template(template).fill_values(VALUE={1, 2, 3})


def test_ignore_todo_by_default():
    def template():
        print("TODO")

    assert Template(template).finish() == 'print("TODO")'


def test_todo_kwarg():
    def template():
        print("hello")  # TODO: add "world"

    with pytest.raises(
        TemplateException, match=re.escape('kwarg "TODO" is an ignored slot name')
    ):
        Template(template).fill_values(TODO="should not work")


def test_ignore_kwarg():
    def template():
        print("IGNORE_ME")

    with pytest.raises(
        TemplateException,
        match=r"unfilled slots: IGNORE_ME",
    ):
        Template(template).finish()

    assert Template(template, ignore={"IGNORE_ME"}).finish() == 'print("IGNORE_ME")'


def test_strip_pragma():
    def template():
        pass  # pragma: no cover

    assert Template(template).finish() == "pass"


def test_strip_noqa():
    def template():
        pass  # noqa: B950

    assert Template(template).finish() == "pass"


def test_strip_type_ignore():
    def template():
        pass  # type: ignore

    assert Template(template).finish() == "pass"


def test_noqa_leak():
    def template():
        print("# noqa: B950")

    assert Template(template).finish() == 'print("# noqa: B950")'


@pytest.mark.xfail(reason="The regex can not cover all possible cases")
def test_strip_noqa_with_extra_comment():
    def template():
        pass  # noqa: B950 ... and here's why!

    assert Template(template).finish() == "pass"


@pytest.mark.xfail(reason="The regex covers some cases it shouldn't")
def test_strip_noqa_inside_string():
    def template():
        print(
            """
            not really a comment:  # noqa: B950
        """
        )

    assert (
        Template(template).finish()
        == '''print("""
    not really a comment:  # noqa: B950
""")'''
    )


def test_def_too_long():
    def template(
        BEGIN,
        END,
    ):
        print(BEGIN, END)

    with pytest.raises(
        TemplateException, match=r"def and parameters should fit on one line"
    ):
        Template(template)


def test_def_template():
    def template(BEGIN, END):
        print(BEGIN, END)

    assert (
        Template(template).fill_values(BEGIN="abc", END="xyz").finish()
        == "print('abc', 'xyz')"
    )


def test_fill_expressions():
    template = Template("No one VERB the ADJ NOUN!")
    filled = template.fill_expressions(
        VERB="expects",
        ADJ="Spanish",
        NOUN="Inquisition",
    ).finish()
    assert filled == "No one expects the Spanish Inquisition!"


def test_fill_expressions_missing_slots_in_template():
    template = Template("No one ... the ... ...!")
    with pytest.raises(
        TemplateException,
        match=r"no 'ADJ' slot to fill with 'Spanish', "
        r"no 'NOUN' slot to fill with 'Inquisition', "
        r"no 'VERB' slot to fill with 'expects':",
    ):
        template.fill_expressions(
            VERB="expects",
            ADJ="Spanish",
            NOUN="Inquisition",
        ).finish()


def test_fill_expressions_extra_slots_in_template():
    template = Template("No one VERB ARTICLE ADJ NOUN!")
    with pytest.raises(TemplateException, match=r"unfilled slots: VERB, ARTICLE"):
        template.fill_expressions(
            ADJ="Spanish",
            NOUN="Inquisition",
        ).finish()


def test_fill_values():
    template = Template("assert [STRING] * NUM == LIST")
    filled = template.fill_values(
        STRING="🙂",
        NUM=3,
        LIST=["🙂", "🙂", "🙂"],
    ).finish()
    assert filled == "assert ['🙂'] * 3 == ['🙂', '🙂', '🙂']"


def test_fill_values_missing_slot_in_template():
    template = Template("assert [STRING] * ... == LIST")
    with pytest.raises(TemplateException, match=r"no 'NUM' slot to fill with '3'"):
        template.fill_values(
            STRING="🙂",
            NUM=3,
            LIST=["🙂", "🙂", "🙂"],
        ).finish()


def test_fill_values_extra_slot_in_template():
    template = Template("CMD [STRING] * NUM == LIST")
    with pytest.raises(TemplateException, match=r"unfilled slots: CMD"):
        template.fill_values(
            STRING="🙂",
            NUM=3,
            LIST=["🙂", "🙂", "🙂"],
        ).finish()


def test_fill_blocks():
    # "OK" is less than three characters, so it is not a slot.
    template = Template(
        """# MixedCase is OK

FIRST

with fake:
    my_tuple = (
        # SECOND
        VALUE,
    )
    if True:
        THIRD
""",
    )
    filled = (
        template.fill_blocks(
            FIRST="\n".join(f"import {i}" for i in "abc"),
            THIRD="\n".join(f"{i}()" for i in "xyz"),
        )
        .fill_blocks(
            SECOND="This is a\nmulti-line comment",
        )
        .fill_values(VALUE=42)
        .finish()
    )
    assert (
        filled
        == """# MixedCase is OK

import a
import b
import c

with fake:
    my_tuple = (
        # This is a
        # multi-line comment
        42,
    )
    if True:
        x()
        y()
        z()
"""
    )


def test_fill_comment_block():
    template = Template("# SLOT")
    filled = template.fill_blocks(SLOT="placeholder").finish()
    assert filled == "# placeholder"


def test_finish_reformat():
    template = Template("print( 'messy','code!' )#comment")
    filled = template.finish(reformat=True)
    assert filled == 'print("messy", "code!")  # comment'


def test_fill_blocks_missing_slot_in_template_alone():
    template = Template("No block slot")
    with pytest.raises(TemplateException, match=r"no 'SLOT' slot"):
        template.fill_blocks(SLOT="placeholder").finish()


def test_fill_blocks_missing_slot_in_template_not_alone():
    template = Template("No block SLOT")
    with pytest.raises(
        TemplateException,
        match=r"In string template, expected prefix",
    ):
        template.fill_blocks(SLOT="placeholder").finish()


def test_fill_blocks_extra_slot_in_template():
    template = Template("EXTRA\nSLOT")
    with pytest.raises(TemplateException, match=r"unfilled slots: EXTRA"):
        template.fill_blocks(SLOT="placeholder").finish()


def test_no_root_kwarg_with_function_template():
    def template():
        pass

    with pytest.raises(
        TemplateException,
        match=r"If template is function, root kwarg not allowed",
    ):
        Template(template, root=Path("not-allowed"))


def test_lc_kwarg_error():
    def template(FILL_THIS):
        print(FILL_THIS)

    with pytest.raises(
        TemplateException,
        match=re.escape('kwarg "FILL_this" is not a valid slot name'),
    ):
        Template(template).fill_values(FILL_this="nope").finish()


def test_when_true():
    def template(FILL):
        print(FILL)

    assert (
        Template(template).fill_values(FILL="hello!", when=1).finish()
        == "print('hello!')"
    )


def test_when_false():
    def template(FILL):
        print(FILL)

    assert (
        Template(template)
        .fill_values(FILL="hello!", when=0)
        .fill_values(FILL="goodbye!")
        .fill_values(FILL="redundant!", when=0)
        .finish()
        == "print('goodbye!')"
    )


def test_user_slot_injection():
    def template(FILL_A, FILL_B):
        print(FILL_A)
        print(FILL_B)

    Template(template).fill_values(
        FILL_A="hello world",
        FILL_B="FILL_A",
    ).finish()


def test_deepcopy():
    def template(ARG):
        print(ARG)  # COMMENT

    orig = Template(template).fill_values(ARG="hello")
    from copy import deepcopy

    copy = deepcopy(orig)

    assert orig.fill_expressions(COMMENT="world").finish() == "print('hello')  # world"
    assert copy.fill_expressions(COMMENT="kitty").finish() == "print('hello')  # kitty"


def test_optional():
    def template():
        print(2 + 2)

    assert (
        Template(template).fill_expressions(VERSION="1.2.3.4", optional=True).finish()
        == "print(2 + 2)"
    )


def test_default_idiom():
    class TemplateWithDefaults(Template):
        def finish(self, reformat=False):
            self.fill_expressions(VERSION="0.1.2.3", optional=True)
            return super().finish(reformat=reformat)

    def template_without(ARG):
        print(ARG)

    def template_with(ARG):
        # Version: VERSION
        print(ARG)

    assert (
        TemplateWithDefaults(template_without).fill_values(ARG="hello").finish()
        == "print('hello')"
    )

    assert (
        TemplateWithDefaults(template_with).fill_values(ARG="hello").finish()
        == "# Version: 0.1.2.3\nprint('hello')"
    )

    assert (
        TemplateWithDefaults(template_with)
        .fill_values(ARG="hello")
        .fill_expressions(VERSION="1.0")
        .finish()
        == "# Version: 1.0\nprint('hello')"
    )


def test_fill_attributes_none():
    def template(old):
        new = old.DO_THIS.NOT_THAT  # noqa: F841

    assert (
        Template(template).fill_attributes(DO_THIS="do_this()", NOT_THAT=None).finish()
        == "new = old.do_this()"
    )


def test_fill_attributes_missing_slot():
    def template(old):
        new = old.DO_THIS  # noqa: F841

    with pytest.raises(
        TemplateException,
        match=re.escape(
            "In function template, no 'DO_THAT' slot to fill with '':\n"
            "new = old.DO_THIS"
        ),
    ):
        Template(template).fill_attributes(DO_THAT=None).finish()


def test_fill_attributes_start_of_line():
    def template(new):
        DO_THIS = new  # noqa: F841

    with pytest.raises(
        TemplateException,
        match=re.escape("No preceding period: slot_name='DO_THIS'"),
    ):
        Template(template).fill_attributes(DO_THIS=None).finish()
