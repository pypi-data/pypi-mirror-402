// Wrap in anonymous function to avoid global pollution.
// TODO: Convert to ESM.
(() => {
    const prefix = "celltag_"
    var tags = new Set();
    $(`div[class*='${prefix}']`).each((i, el) => {
        const el_tags = new Set(
            $(el)
            .attr("class")
            .split(" ")
            .filter((class_name) => class_name.startsWith(prefix))
            .map((class_name) => class_name.replace(prefix, ""))
        );
        tags = tags.union(el_tags)
    });

    const tag_values = tags.values().toArray().sort();

    if (tag_values.length === 0) {
        // Do not inject HTML if there will be no options:
        return;
    }

    const options_html = (
        tag_values
        // Don't need to escape because tag is from a class name:
        .map((tag) => `<option value="${tag}">${tag.replaceAll("_", " ")}</option>`)
        .join("\n")
    ) + '<option value="">(none)</option>';  // Empty value is falsy in show_only().

    // HTML skeleton is just copy-paste from notebook source:
    // Looks ok, but the semantics aren't correct.
    $("main").prepend(`
        <div class="jp-Cell jp-MarkdownCell jp-Notebook-cell">
            <div class="jp-Cell-inputWrapper">
                <div class="jp-Collapser jp-InputCollapser jp-Cell-inputCollapser">
                </div>
                <div class="jp-InputArea jp-Cell-inputArea"><div class="jp-InputPrompt jp-InputArea-prompt">
                    Show:
                </div>
                <div class="jp-RenderedHTMLCommon jp-RenderedMarkdown jp-MarkdownOutput" data-mime-type="text/markdown">
                    <select>
                        ${options_html}
                    <select>
                </div>
            </div>
        </div>
    `);

    function show_only(tag) {
        $(`div[class*='${prefix}']`).hide();
        if (tag) {
            $(`div.${prefix}${tag}`).show();
        }
    }

    const default_tag = tag_values[0];
    show_only(default_tag);

    $("select").on("change", (event) => {
        const tag = event.target.value;
        show_only(tag);
    })
})();