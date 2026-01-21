Submittal Builder

Overview:
Submittal Builder is a Python desktop application that helps quickly assemble HVAC manufacturer submittals into a single merged PDF. The app scans a shared manufacturer drawings directory, lets the user browse by type, manufacturer, and category, then select and order product PDFs before building a final submittal package. An optional title page workflow can copy a manufacturer-specific Word title page template for editing.

Key features
Browse a live folder hierarchy
The app scans a base directory and builds a live hierarchy:
Type folder
Manufacturer folder
Category subfolder
PDFs in the selected folder populate as selectable items.

Checkbox-based product selection
Each PDF in the selected category appears as a checkbox. Checking adds it to the selection list, unchecking removes it.

Reorder output with drag and drop
A selection list on the right shows chosen products. Items can be reordered by dragging so the merged PDF follows the desired sequence.

Build a merged PDF
Creates a single PDF by appending all pages from the selected PDFs in the list order. Uses pypdf for reading and writing.

Optional title page workflow
If enabled, the app looks up a manufacturer-specific Word title page template, prompts the user to save a copy, copies it, and opens it for editing.

Loading animation and background merging
A popup with an animated GIF displays while merging runs in a background thread to keep the UI responsive.

How it works
1. On startup the app scans the base manufacturer directory and discovers available types and manufacturers.
2. The user selects:
Type
Manufacturer
Category
3. The app lists all PDF files found in that folder as selectable products.
4. The user selects products, optionally reorders them, then clicks Build Submittal.
5. The app prompts for an output PDF path, merges PDFs in order, then opens the finished file.
=
