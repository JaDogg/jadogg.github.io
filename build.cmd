rem run this in virtual env so we can import markdown
py docbox.py
rem install html-minifier and node, this is lot more capable
html-minifier --collapse-whitespace --remove-comments --remove-optional-tags --remove-redundant-attributes --remove-script-type-attributes --remove-tag-whitespace --use-short-doctype --minify-css true --minify-js true -o index.html index.html
