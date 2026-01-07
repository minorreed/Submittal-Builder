import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageSequence
import threading
import time
import subprocess

root = tk.Tk()
root.title("Submittal Builder")
root.geometry("900x650")

# --- Header with Logo ---
header_frame = ttk.Frame(root)
header_frame.pack(fill="x", pady=5, padx=10)

try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(script_dir, "download.png")
    original_image = Image.open(logo_path).convert("RGBA")
    target_height = 70
    aspect_ratio = original_image.width / original_image.height
    target_width = int(target_height * aspect_ratio)
    resized_image = original_image.resize((target_width, target_height), Image.LANCZOS)
    logo_image = ImageTk.PhotoImage(resized_image)
    logo_label = tk.Label(header_frame, image=logo_image)
    logo_label.image = logo_image
    logo_label.pack(side="right")
except Exception as e:
    print(f"Failed to load or resize logo: {e}")

# --- Manufacturer Hierarchy Loader ---
MANUFACTURER_DIR = r"S:\Interns\Manufacturer Drawings"
drag_data = {"item": None, "index": None}

def start_drag(event):
    widget = event.widget
    index = widget.nearest(event.y)
    if index >= 0:
        drag_data["item"] = widget.get(index)
        drag_data["index"] = index

def do_drag(event):
    widget = event.widget
    index = widget.nearest(event.y)
    if drag_data["item"] and index != drag_data["index"]:
        widget.delete(drag_data["index"])
        widget.insert(index, drag_data["item"])
        drag_data["index"] = index
        widget.selection_clear(0, tk.END)
        widget.selection_set(index)

def end_drag(event):
    drag_data["item"] = None
    drag_data["index"] = None

def get_live_hierarchy():
    hierarchy = {}
    print(f"[DEBUG] Scanning base path: {MANUFACTURER_DIR}")
    for type_name in os.listdir(MANUFACTURER_DIR):
        type_path = os.path.join(MANUFACTURER_DIR, type_name)
        if os.path.isdir(type_path):
            print(f"[DEBUG] Found type: {type_name}")
            manufacturers = {}
            for manu in os.listdir(type_path):
                manu_path = os.path.join(type_path, manu)
                if os.path.isdir(manu_path):
                    print(f"   - Found manufacturer: {manu}")
                    manufacturers[manu] = manu_path
            hierarchy[type_name] = manufacturers
    return hierarchy


product_vars = {}
product_to_path = {}
all_selected_products = {}

selected_type = tk.StringVar()
selected_manufacturer = tk.StringVar()
selected_subfolder = tk.StringVar()
include_title_page_var = tk.BooleanVar(value=False)

# --- UI ---
top_control_frame = ttk.Frame(root)
top_control_frame.pack(pady=5)

type_dropdown = ttk.Combobox(top_control_frame, textvariable=selected_type, state="readonly")
manufacturer_dropdown = ttk.Combobox(top_control_frame, textvariable=selected_manufacturer, state="readonly")
subfolder_dropdown = ttk.Combobox(top_control_frame, textvariable=selected_subfolder, state="readonly")

ttk.Label(top_control_frame, text="Select Type:").pack()
type_dropdown.pack(pady=2)

ttk.Label(top_control_frame, text="Select Manufacturer:").pack()
manufacturer_dropdown.pack(pady=2)

ttk.Label(top_control_frame, text="Select Category:").pack()
subfolder_dropdown.pack(pady=2)

main_frame = ttk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=5)

canvas_frame = ttk.Frame(main_frame)
canvas_frame.pack(side="left", fill="both", expand=True)
canvas = tk.Canvas(canvas_frame)
scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

selection_listbox = tk.Listbox(main_frame, selectmode=tk.SINGLE, width=40)
selection_listbox.pack(side="right", fill="y", padx=(10, 0), pady=5)
selection_listbox.bind("<Button-1>", lambda e: start_drag(e))
selection_listbox.bind("<B1-Motion>", lambda e: do_drag(e))
selection_listbox.bind("<ButtonRelease-1>", lambda e: end_drag(e))

def bind_mousewheel(event):
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

def unbind_mousewheel(event):
    canvas.unbind_all("<MouseWheel>")
    canvas.unbind_all("<Button-4>")
    canvas.unbind_all("<Button-5>")

scrollable_frame.bind("<Enter>", bind_mousewheel)
scrollable_frame.bind("<Leave>", unbind_mousewheel)

def load_products(base_override=None):
    for widget in scrollable_frame.winfo_children():
        widget.destroy()
    product_to_path.clear()
    canvas.yview_moveto(0)
    type_selected = selected_type.get()
    manu = selected_manufacturer.get()
    if type_selected not in live_type_hierarchy or manu not in live_type_hierarchy[type_selected]:
        return
    manu_base = live_type_hierarchy[type_selected][manu]
    base_path = os.path.join(manu_base, selected_subfolder.get()) if not base_override else base_override
    if not os.path.exists(base_path):
        messagebox.showerror("Error", f"Folder does not exist:\n{base_path}")
        return
    for filename in os.listdir(base_path):
        if filename.lower().endswith(".pdf"):
            name = os.path.splitext(filename)[0]
            full_path = os.path.join(base_path, filename)
            product_to_path[name] = full_path
    for product in sorted(product_to_path.keys()):
        full_path = product_to_path[product]
        var = product_vars.get(product)
        if not var:
            var = tk.BooleanVar(value=(full_path in all_selected_products.values()))
            product_vars[product] = var
            def make_callback(p=product, path=full_path, v=var):
                def callback(*_):
                    if v.get():
                        all_selected_products[p] = path
                        if p not in selection_listbox.get(0, tk.END):
                            selection_listbox.insert(tk.END, p)
                    else:
                        all_selected_products.pop(p, None)
                        try:
                            idx = selection_listbox.get(0, tk.END).index(p)
                            selection_listbox.delete(idx)
                        except ValueError:
                            pass
                return callback
            var.trace_add("write", make_callback())
        cb = tk.Checkbutton(scrollable_frame, text=product, variable=var)
        cb.pack(anchor="w")

def load_manufacturers(event=None):
    global live_type_hierarchy
    live_type_hierarchy = get_live_hierarchy()
    selected = selected_type.get()
    if selected in live_type_hierarchy:
        manufacturers = list(live_type_hierarchy[selected].keys())
        manufacturer_dropdown["values"] = manufacturers
        if manufacturers:
            selected_manufacturer.set(manufacturers[0])
            load_subfolders()
    else:
        manufacturer_dropdown["values"] = []
        selected_manufacturer.set("")

def load_subfolders(event=None):
    type_selected = selected_type.get()
    manu = selected_manufacturer.get()
    if type_selected not in live_type_hierarchy or manu not in live_type_hierarchy[type_selected]:
        return
    base_path = live_type_hierarchy[type_selected][manu]
    selected_subfolder.set("")
    subfolder_dropdown["values"] = []
    if not os.path.exists(base_path):
        messagebox.showerror("Error", f"Path not found for {manu}:\n{base_path}")
        return
    subfolders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    if subfolders:
        subfolder_dropdown["values"] = subfolders
        subfolder_dropdown.configure(state="readonly")
        subfolder_dropdown.set(subfolders[0])
        load_products()
    else:
        subfolder_dropdown["values"] = []
        subfolder_dropdown.set("")
        subfolder_dropdown.configure(state="disabled")
        load_products(base_override=base_path)

def clear_all_selections():
    for var in product_vars.values():
        var.set(False)
    all_selected_products.clear()
    selection_listbox.delete(0, tk.END)
    include_title_page_var.set(False)

def submit_selection():
    if selection_listbox.size() == 0:
        messagebox.showwarning("No Selection", "Please select at least one product.")
        return

    output_file = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save Final Submittal As"
    )
    if not output_file:
        return

    def show_loading_popup():
        popup = tk.Toplevel(root)
        popup.title("Building Submittal...")
        popup.geometry("250x250")
        popup.resizable(False, False)
        popup.grab_set()
        gif_path = os.path.join(os.path.dirname(__file__), "water_fill_tank.gif")
        gif = Image.open(gif_path)
        gif_label = tk.Label(popup)
        gif_label.pack()
        frames = [ImageTk.PhotoImage(frame.copy().convert("RGBA")) for frame in ImageSequence.Iterator(gif)]
        def animate(index=0):
            gif_label.configure(image=frames[index])
            popup.after(100, animate, (index + 1) % len(frames))
        animate()
        return popup

    loading_popup = show_loading_popup()

    import shutil
    if include_title_page_var.get():
        try:
            manu = selected_manufacturer.get()
            if manu == "Twin City Hose":
                manu = "Mason"
            title_page_path = os.path.join(r"S:\\Interns\\New Title Pages", f"New Title Page {manu}.docx")
            if os.path.isfile(title_page_path):
                copied_path = filedialog.asksaveasfilename(
                    defaultextension=".docx",
                    filetypes=[("Word Documents", "*.docx")],
                    title="Save Title Page Copy As",
                    initialfile=f"New Title Page {manu}.docx"
                )
                if copied_path:
                    shutil.copyfile(title_page_path, copied_path)
                    subprocess.Popen(["start", "", copied_path], shell=True)
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"Something went wrong:\n{e}")

    def do_merge():
        from pypdf import PdfWriter, PdfReader
        writer = PdfWriter()
        missing_files = []
        for i in range(selection_listbox.size()):
            prod = selection_listbox.get(i)
            pdf_path = all_selected_products.get(prod)
            if os.path.exists(pdf_path):
                try:
                    reader = PdfReader(pdf_path)
                    for page in reader.pages:
                        writer.add_page(page)
                except Exception as e:
                    missing_files.append(prod)
            else:
                missing_files.append(prod)
        try:
            with open(output_file, "wb") as f_out:
                writer.write(f_out)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write PDF:\n{e}")
            return
        def on_done():
            loading_popup.destroy()
            if missing_files:
                messagebox.showerror("Missing or Failed Files", "\n".join(missing_files))
            else:
                messagebox.showinfo("Success", f"Submittal created: {output_file}")
                try:
                    os.startfile(output_file)
                except Exception as e:
                    messagebox.showwarning("Open Failed", f"Couldn't open file:\n{e}")
        root.after(0, on_done)

    threading.Thread(target=do_merge).start()

submit_frame = ttk.Frame(root)
submit_frame.pack(pady=5)

ttk.Checkbutton(submit_frame, text="Include Title Page", variable=include_title_page_var).pack(side="top", pady=(0, 5))

ttk.Button(submit_frame, text="Build Submittal", command=submit_selection).pack(side="left", padx=(0, 10))
ttk.Button(submit_frame, text="Clear All Selections", command=clear_all_selections).pack(side="right")

footer_frame = ttk.Frame(root)
footer_frame.pack(fill="x", side="bottom", padx=10, pady=(5, 10), anchor="se")

ttk.Label(
    footer_frame,
    text="Developed by the Best Interns of All Time",
    font=("Segoe UI", 9, "italic"),
    anchor="e",
    justify="right"
).pack(side="right")

live_type_hierarchy = get_live_hierarchy()
# NEW
type_dropdown["values"] = list(live_type_hierarchy.keys())

type_dropdown.bind("<<ComboboxSelected>>", load_manufacturers)
manufacturer_dropdown.bind("<<ComboboxSelected>>", load_subfolders)
subfolder_dropdown.bind("<<ComboboxSelected>>", lambda e: load_products())

if type_dropdown["values"]:
    selected_type.set(type_dropdown["values"][0])
    load_manufacturers()

root.mainloop()