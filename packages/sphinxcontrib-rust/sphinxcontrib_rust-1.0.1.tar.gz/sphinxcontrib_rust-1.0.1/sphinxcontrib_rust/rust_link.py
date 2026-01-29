"""Module for enabling intra-doc links similar to Rustdoc"""

from markdown_it.common.utils import isStrSpace, normalizeReference
from markdown_it.rules_inline.state_inline import StateInline


def link(state: StateInline, silent: bool) -> bool:
    """This is a monkey patch used to replace the :py:func:`markdown_it.rules_inline.link.link`.

    The main difference here is that it will mark any text with brackets as a link, even if there
    is no reference for it. This allows us to inject links for Rust items in the docs similar to
    rustdoc. However, it will also make links out of text that is not a Rust item name.

    Returns:
        True, if it found a link, otherwise False.
    """
    # pylint: disable=too-many-branches,too-many-statements
    href = ""
    title = ""
    label = None
    maximum = state.posMax
    parse_reference = True

    if state.src[state.pos] != "[":
        return False

    label_start = state.pos + 1
    label_end = state.md.helpers.parseLinkLabel(state, state.pos, True)

    # parser failed to find ']', so it's not a valid link
    if label_end < 0:
        return False

    pos = label_end + 1

    if pos < maximum and state.src[pos] == "(":
        #
        # Inline link
        #

        # might have found a valid shortcut link, disable reference parsing
        parse_reference = False

        # [link](  <href>  "title"  )
        #        ^^ skipping these spaces
        pos += 1
        while pos < maximum:
            ch = state.src[pos]
            if not isStrSpace(ch) and ch != "\n":
                break
            pos += 1

        if pos >= maximum:
            return False

        # [link](  <href>  "title"  )
        #          ^^^^^^ parsing link destination
        res = state.md.helpers.parseLinkDestination(state.src, pos, state.posMax)
        if res.ok:
            href = state.md.normalizeLink(res.str)
            if state.md.validateLink(href):
                pos = res.pos
            else:
                href = ""

            # [link](  <href>  "title"  )
            #                ^^ skipping these spaces
            start = pos
            while pos < maximum:
                ch = state.src[pos]
                if not isStrSpace(ch) and ch != "\n":
                    break
                pos += 1

            # [link](  <href>  "title"  )
            #                  ^^^^^^^ parsing link title
            res = state.md.helpers.parseLinkTitle(state.src, pos, state.posMax)
            if maximum > pos != start and res.ok:
                title = res.str
                pos = res.pos

                # [link](  <href>  "title"  )
                #                         ^^ skipping these spaces
                while pos < maximum:
                    ch = state.src[pos]
                    if not isStrSpace(ch) and ch != "\n":
                        break
                    pos += 1

        if pos >= maximum or state.src[pos] != ")":
            # parsing a valid shortcut link failed, fallback to reference
            parse_reference = True

        pos += 1

    ### CHANGES BEGIN HERE
    if parse_reference:
        #
        # Link reference
        #
        if pos < maximum and state.src[pos] == "[":
            start = pos + 1
            pos = state.md.helpers.parseLinkLabel(state, pos)
            if pos >= 0:
                label = state.src[start:pos]
                pos += 1
            else:
                pos = label_end + 1

        else:
            pos = label_end + 1

        # covers label == '' and label == undefined
        # (collapsed reference link and shortcut reference link respectively)
        if not label:
            label = state.src[label_start:label_end]

        # Strip any backticks from the label for the reference. Keep them in the title.
        # Can't check whether the label resolves or not since the docs are still be parsed.
        ref = {"href": label.strip("`"), "title": label}

        if "references" in state.env:
            # Use the provided reference for the label, if it exists.
            ref = state.env["references"].get(normalizeReference(label), ref)

        href = ref["href"]
        title = ref["title"]
    ### CHANGES END HERE

    #
    # We found the end of the link, and know for a fact it's a valid link
    # so all that's left to do is to call tokenizer.
    #
    if not silent:
        state.pos = label_start
        state.posMax = label_end

        token = state.push("link_open", "a", 1)
        token.attrs = {"href": href}

        if title:
            token.attrSet("title", title)

        # note, this is not part of markdown-it JS, but is useful for renderers
        if label and state.md.options.get("store_labels", False):
            token.meta["label"] = label

        state.linkLevel += 1
        state.md.inline.tokenize(state)
        state.linkLevel -= 1

        state.push("link_close", "a", -1)

    state.pos = pos
    state.posMax = maximum
    return True
