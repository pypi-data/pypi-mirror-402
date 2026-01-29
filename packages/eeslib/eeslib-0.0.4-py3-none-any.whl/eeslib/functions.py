import numpy as __np
import re 

# Constants
sigma = 5.67e-8   # W/m^2-K^4  Stefan-Boltzmann constant
g = 9.81          # m/s^2 gravity
R = 8314          # J/kmol-K ideal gas constant

__conversion_factors = {
#   unit        basis         scaling       offset
# -----------------------------------------------
    # Length
    'mm'    : ['m'          , 1e-3          , 0.], 
    'cm'    : ['m'          , 1e-2          , 0.],
    'um'    : ['m'          , 1e-6          , 0.],  #micron
    'micron': ['m'          , 1e-6          , 0.],  #micron
    'm'     : ['m'          , 1             , 0.],
    'km'    : ['m'          , 1e3           , 0.],
    'in'    : ['m'          , 0.0254        , 0.],
    'inch'  : ['m'          , 0.0254        , 0.],
    'ft'    : ['m'          , 0.3048        , 0.],
    'feet'  : ['m'          , 0.3048        , 0.],
    'yd'    : ['m'          , 0.9144        , 0.],
    'yard'  : ['m'          , 0.9144        , 0.],
    'mi'    : ['m'          , 1609.34       , 0.],
    'mile'  : ['m'          , 1609.34       , 0.],
    # Volume
    'L'     : ['m^3'        , 1e-3          , 0.],  # liter
    'mL'    : ['m^3'        , 1e-6          , 0.],  # milliliter
    'gal'   : ['m^3'        , 0.00378541    , 0.],  # us gallon
    'qt'    : ['m^3'        , 0.0009463525  , 0.],  # us quart
    'cup'   : ['m^3'        , 0.00024       , 0.],  # cup
    'oz'    : ['m^3'        , 2.9574e-5     , 0.],  # fl ounce
    'tbsp'  : ['m^3'        , 1.4787e-5     , 0.],  # tablespoon
    'tsp'   : ['m^3'        , 4.9289e-6     , 0.],  # teaspoon
    # Energy
    'J'     : ['J'          , 1             , 0.],  # Joules
    'kJ'    : ['J'          , 1e3           , 0.],  # Kilojoules
    'cal'   : ['J'          , 4.184         , 0.],  # Calories
    'kcal'  : ['J'          , 4184          , 0.],  # Kilocalories
    'Wh'    : ['J'          , 3600          , 0.],  # Watt-hours
    'kWh'   : ['J'          , 3.6e6         , 0.],  # Kilowatt-hours
    'btu'   : ['J'          , 1055.06       , 0.],  # british thermal unit
    'therm' : ['J'          , 1.055e+8      , 0.],  # US-therm
    'ft-lb' : ['J'          , 1.35582       , 0.],  # foot pound
    'eV'    : ['J'          , 1.6022e-19    , 0.],  # electron-volt
    # Power 
    'W'     : ['J/s'        , 1             , 0.],  # Watts
    'kW'    : ['J/s'        , 1e3           , 0.],  # Kilowatts
    'MW'    : ['J/s'        , 1e6           , 0.],  # Megawatts
    'hp'    : ['J/s'        , 745.7         , 0.],  # Horsepower
    # Time
    's'     : ['s'          , 1             , 0.],  # Seconds
    'sec'   : ['s'          , 1             , 0.],  # Seconds
    'min'   : ['s'          , 60            , 0.],  # Minutes
    'h'     : ['s'          , 3600          , 0.],  # Hours
    'hr'    : ['s'          , 3600          , 0.],  # Hours
    'hour'  : ['s'          , 3600          , 0.],  # Hours
    'day'   : ['s'          , 86400         , 0.],  # Days
    'week'  : ['s'          , 604800        , 0.],  # Weeks
    'month' : ['s'          , 2.63e6        , 0.],  # Months (average)
    'year'  : ['s'          , 3.154e7       , 0.],  # Years (average)
    # Mass 
    'mg'    : ['kg'         , 1e-6          , 0.],  # Milligrams
    'g'     : ['kg'         , 1e-3          , 0.],  # Grams
    'kg'    : ['kg'         , 1             , 0.],  # Kilograms
    'ton'   : ['kg'         , 1e3           , 0.],  # Metric tons
    'us-ton': ['kg'         , 907.185       , 0.],  # US ton
    'lb'    : ['kg'         , 0.453592      , 0.],  # Pounds
    'oz'    : ['kg'         , 0.0283495     , 0.],  # Ounces
    'stone' : ['kg'         , 6.35029       , 0.],  # stone
    # Pressure
    'bar'   : ['kg/m/s^2'   , 1e5           , 0.],
    'Pa'    : ['kg/m/s^2'   , 1.            , 0.],
    'kPa'   : ['kg/m/s^2'   , 1e3           , 0.],
    'MPa'   : ['kg/m/s^2'   , 1e6           , 0.],
    'psi'   : ['kg/m/s^2'   , 6894.76       , 0.],
    'atm'   : ['kg/m/s^2'   , 101325.       , 0.],
    'torr'  : ['kg/m/s^2'   , 133.322       , 0.],
    # Force
    'N'     : ['kg*m/s^2'   , 1.            , 0.],
    # Velocity 
    'm/s'   : ['m/s'        , 1.            , 0.],
    'mph'   : ['m/s'        , 0.44704       , 0.],
    'ft/s'  : ['m/s'        , 0.3048        , 0.],
    'kph'   : ['m/s'        , 0.277778      , 0.],
    'knot'  : ['m/s'        , 0.51444       , 0.],
    # Temperature
    'K'     : ['K'          , 1.            , 0.],
    'C'     : ['K'          , 1.            , -273.15],
    'F'     : ['K'          , 5/9           , 459.67 ],
    'R'     : ['K'          , 5/9           , 0.],
    # Currency
    '$'     : ['$'          , 1.            , 0.],
    'cent'  : ['$'          , 0.01          , 0.],
    'cents' : ['$'          , 0.01          , 0.],
}

# def __print_markdown_table(array, max_rows=50, max_cols=20, sig_figs=5):
#     # Get the shape of the array
#     rows, cols = array.shape
    
#     # Determine the rows and columns to display
#     if rows > max_rows:
#         row_indices = [0] + list(range((rows - max_rows) // 2, (rows + max_rows) // 2)) + [rows - 1]
#     else:
#         row_indices = list(range(rows))
    
#     if cols > max_cols:
#         col_indices = [0] + list(range((cols - max_cols) // 2, (cols + max_cols) // 2)) + [cols - 1]
#     else:
#         col_indices = list(range(cols))
    
#     # Create the header row
#     header = "| " + " | ".join([f"Col {i+1}" for i in col_indices]) + " |"
#     separator = "| " + " | ".join(["---" for _ in col_indices]) + " |"
    
#     # Create the data rows
#     data_rows = []
#     for i in row_indices:
#         data_row = "| " + " | ".join(map(lambda v: f'{v:.{sig_figs}g}', array[i, col_indices])) + " |"
#         data_rows.append(data_row)
    
#     # Combine all parts into the markdown table
#     markdown_table = "\n".join([header, separator] + data_rows)
    
#     return markdown_table

def print_results_table(results_dict, sig_figs=5, file_save_path=None, 
                        array_print_maxsize=60, file_save_note=None, 
                        file_save_images=None, fig_width=75, file_save_code=None,
                        highlight_vars=[]):
    """
    Print key-value contents of a results dictionary and optionally create a PDF report.

    The function prints scalars, arrays (NumPy), and SymPy expressions to the console,
    and when ``file_save_path`` is provided, it constructs a styled PDF containing
    scalar tables, arrays (formatted), figures, and optional code listings.

    Parameters
    ----------
    results_dict : dict
        Dictionary of values to print. Floats and NumPy arrays are formatted; other
        types (e.g., SymPy) are supported in the PDF export.
    sig_figs : int, optional
        Number of significant digits for formatting (default is 5).
    file_save_path : str, optional
        Destination PDF path. If provided, a report is saved (e.g., ``'my_report.pdf'``).
    array_print_maxsize : int, optional
        Preferred maximum number of array elements printed (default is 60).
    file_save_note : str, optional
        A note inserted at the top of the PDF report. If the first character is ``'#'``,
        it is treated as a Markdown heading.
    file_save_images : list of [str, str], optional
        List of ``[image_path, caption]`` pairs to append to the report.
    fig_width : int, optional
        Percentage page width used for images (default is 75).
    file_save_code : str or list of str, optional
        Path(s) to Python code files to embed as listings in a companion PDF.
    highlight_vars : list of str, optional
        Names of variables to highlight in the scalar table.

    Notes
    -----
    - The console output uses ANSI color codes.
    - PDF generation requires optional dependencies (e.g., ``markdown_pdf``, ``pylatex``).

    Examples
    --------
    Minimal usage:

    >>> print_results_table({'a': 1.2345, 'vec': __np.array([1.0, 2.0])})

    With PDF export:

    >>> print_results_table({'a': 1.2345}, file_save_path='report.pdf')  # doctest: +SKIP
    """
    def __colorform(s,c):
        cm = {'r':'31', 'g':'32','m':'35','v':'90','end':'0','hl':'42'}[c]
        return f'\033[{cm}m{s}\033[0m'
        
    pstr = " \n"
    keys = results_dict.keys()
    keys = sorted(keys, key=lambda x: x.lower())
    
    value_items = []
    array_items = []
    sympy_items = []

    collected_pdfs = []

    nl=15
    nb=nl+3
    formatter = lambda x: f'{x:{sig_figs+5}.{sig_figs}g}'
    formatter_short = lambda x: f'{x:.{sig_figs}g}'

    __np.set_printoptions(formatter={'all': formatter }, threshold=array_print_maxsize, edgeitems=10)
    for k in keys:
        kf = __colorform(k,'hl' if k in highlight_vars else 'g')
        try:
            formatted_number = f'{results_dict[k]:.{sig_figs}g}'
            pstr += f'{kf:>{nl+9}s}{" = ":3s}{__colorform(formatted_number,"m")}\n'
            value_items.append([k,formatted_number])

        except:
            try:
                results_dict[k] = results_dict[k].toarray()  #this will work if it's a numpy sparse matrix 
            except:
                pass
            if type(results_dict[k]) == type(__np.array([])):
                try:
                    pstr += f'{kf:>{nl+9}s}{" = ":3s}'+__colorform(__np.array2string(results_dict[k]).replace('\n','\n'+' '*nb),'v') + '\n'
                    array_items.append([k,results_dict[k]])
                except:
                    pass
            elif 'sympy' in str(type(results_dict[k])):
                sympy_items.append([k,results_dict[k]])
                
    print(pstr)
    
    if file_save_path:
        css = """
                body {font-family: 'Courier New', Courier, monospace; font-size:8pt;} 
                h2 {font-family: 'Arial', sans-serif;}
                h1 {font-family: 'Arial', sans-serif;}
                table {width: 100%; border-spacing: 0; border-collapse: collapse; margin: 5px 0; text-align: left;} 
                td { padding: 3px 3px; border: 0.5px solid #ddd;}
                th { padding: 3px 3px; border: 0.6px solid black;}
                """

        try:
            import markdown_pdf as md
            import platform
            import datetime
            pdf = md.MarkdownPdf()

            header_info = f"Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} on {platform.node()}"
            
            pstrnf = f'*_{header_info}_*\n'
            pref = ''
            if file_save_note:
                if file_save_note[0] != '#':
                    pref = '# ' + file_save_note
                else:
                    pref = file_save_note
            else:
                pref = '# Results printout'

            pstrnf += pref +'\n'
            # Print variables section
            if len(value_items)>0:
                pstrnf += "\n## Scalar results\n\n"
                # How many column groups should we break the table into?
                nscalar = len(value_items)
                ncolgroups = int(min(nscalar/5.,3))

                if ncolgroups > 1:
                    # Table header
                    bl = 'border-left: 0.5px solid gray; '
                    br = 'border-right: 0.5px solid gray; '
                    # Header
                    pstrnf += \
                        f'<table>'+\
                        f'<tr>'+\
                        f'<th style="padding-left:25px">&nbsp;</th>'.join([f'<th>Variable</th><th>Value</th>' for i in range(ncolgroups)])+'</tr>\n'

                    asmat = lambda arr,n: [arr[i:i+n] for i in range(0, len(arr), n)]
                    # Reshape 
                    value_items_fit = asmat(value_items, ncolgroups)

                    for row in value_items_fit:
                        pstrnf += '<tr>'
                        row_groups = []
                        for it in row:
                            if it[0] in highlight_vars:
                                cc = 'color:#0cc000; font-weight:bold;'
                            else:
                                cc = ''
                            row_groups.append(\
                                f'<td style="border: none; {bl} text-align:right;{cc}">{it[0]}</td>'+\
                                f'<td style="border: none; {br}{cc}">{it[1]}</td>')
                        pstrnf += f'<td style="border: none;"></td>'.join(row_groups) + '</tr>\n'
                    pstrnf += '</table>\n'

                else:
                    pstrnf += '|Variable|Value|\n|--|--|\n' 
                    for it in value_items:
                        pstrnf += '|' + '|'.join(it)+'|\n'
            if len(array_items)>0:
                pstrnf += "\n## Array results\n\n"

                for arr_key,arr_it in array_items:
                    # How many columns should the table have? 
                    ncolmax = arr_it.shape[-1]
                    max_width = 120

                    try:
                        if arr_it.ndim > 2: raise Exception

                        # Convert all elements in the array to formatted strings
                        arr_f = __np.vectorize(formatter_short)(arr_it)
                        # Find the longest character string in the array 
                        el_max = __np.vectorize(lambda v: len(v))(arr_f).max()

                        ncol = min(int(max_width / (el_max + 3)), ncolmax)
                        nrow_max = array_print_maxsize // ncol
                        if arr_it.ndim == 1:
                            # Divide into an appropriate number of rows based on the character length
                            nrow = int(__np.ceil(arr_f.size/ncol))
                            if nrow > nrow_max:
                                # remove rows if it's a huge array
                                n_el_remove = arr_f.size - nrow_max*ncol + 1
                                break_index = (arr_f.size - n_el_remove)/2
                                arr_f = __np.concatenate((arr_f[:int(__np.ceil(break_index))],__np.array(['...']),arr_f[-int(__np.floor(break_index)):]))
                                nrow = nrow_max

                            arr_f = __np.pad(arr_f, (0,nrow*ncol-arr_f.size), constant_values='').reshape((nrow,ncol))
                        else:
                            # dim 2
                            if ncol < arr_it.shape[1]:
                                ncolpad = ncol - arr_it.shape[1] % ncol
                                arr_f = __np.pad(arr_f, ((0,0),(0,ncolpad)), constant_values='').reshape((-1,ncol))
                            if arr_f.shape[0] > nrow_max:
                                arr_f[nrow_max//2-1,-1] = '...'
                                arr_f[-nrow_max//2,0] = '...'
                                arr_f = __np.concatenate((arr_f[:nrow_max//2], arr_f[-nrow_max//2:]))
                            nrow = arr_f.shape[0]
                                
                        rowstr = f'<table style="border-spacing:0px;"><tr><th colspan="{ncol}">{arr_key}</th></tr>'
                        rowstr += '<tr><td>' + '</td></tr><tr><td>'.join(['</td><td>'.join(arr_f[i]) for i in range(nrow)]) + '</td></tr>'
                        rowstr += '</table>\n'

                        pstrnf += rowstr
                    except:
                        pstrnf += f'\n*_{arr_key}_*, dimension {str(arr_it.shape)}\n\n'
                        pstrnf += __np.array2string(arr_it) + '\n'
                    

            if len(sympy_items)>0:
                try:
                    print("Genering symbolic equations report...")
                    import sympy
                    import pylatex 
                    sympy_pdf = file_save_path.replace('.pdf','_sympy')
                    doc = pylatex.Document(default_filepath=file_save_path.replace('.pdf','_sympy'), geometry_options={'margin':'1in'},document_options=['letterpaper'], page_numbers=False)
                    doc.packages.append(pylatex.Package('breqn'))
                    doc.packages.append(pylatex.Package('xcolor'))
                    with doc.create(pylatex.Section("Symbolic Results", numbering=False)):
                        doc.append(header_info + '\n')
                        for k,s in sympy_items:
                            if k in highlight_vars:
                                doc.append(pylatex.Command('colorbox',('green',k)))
                            else:
                                doc.append(f'{k}')
                            doc.append(pylatex.Command('quad'))
                            doc.append(pylatex.Command('hrulefill'))
                            doc.append(pylatex.NoEscape(r'\begin{equation*}'))
                            doc.append(pylatex.NoEscape(sympy.latex(s)))
                            doc.append(pylatex.NoEscape(r'\end{equation*}'))

                    doc.generate_pdf(clean=True, clean_tex=True)
                    print("\t\tSymbolic report complete.")
                    collected_pdfs.append(sympy_pdf + '.pdf')
                except:
                    print("Unable to create symbolic math report.")

            
            if file_save_images:
                import os
                imstr = '\n\n# Figures\n'
                for img,cap in file_save_images:
                    if not os.path.exists(img):
                        imstr += f"Missing file: {img}\n"
                        continue
                    
                    # imstr += f'\n**{cap}**\n'
                    imstr += f'<div style="text-align:center;"><img src="{img}" style="width:{fig_width:d}%; height:auto; "><br><b>{cap}</b></div>'
                pstrnf += imstr

            if len(array_items) > 0 or len(value_items)>0:
                pdf.add_section(md.Section(pstrnf,paper_size='letter'), user_css=css)
                file_save_path_locals = file_save_path.replace('.pdf','_locals.pdf')
                pdf.save(file_save_path_locals)
                collected_pdfs.insert(0,file_save_path_locals)

            if file_save_code:
                try:
                    print("Generating code listing PDF report...")
                    import pylatex 
                    import os 
                    
                    if type(file_save_code) == type(''):
                        file_save_code_arr = [file_save_code]
                    elif type(file_save_code) == type([]):
                        file_save_code_arr = file_save_code
                    else:
                        raise ValueError("file_save_code must be a string or list of strings that correspond to code files to be saved.")

                    code_pdf = file_save_code[0].replace('.py','_code')
                    doc = pylatex.Document(default_filepath=code_pdf, geometry_options={'margin':'0.6in'}, page_numbers=False)
                    doc.packages.append(pylatex.Package('listings'))
                    doc.packages.append(pylatex.Package('xcolor'))
                    # Define the Python code style
                    doc.preamble.append(pylatex.NoEscape(r'''
                                                \lstset{
                                                    language=Python,
                                                    basicstyle=\ttfamily\small,
                                                    keywordstyle=\color{blue},
                                                    commentstyle=\color{green!70!black},
                                                    stringstyle=\color{red},
                                                    showstringspaces=false,
                                                    breaklines=true,
                                                    numbers=left,
                                                    numberstyle=\tiny\color{gray},
                                                    stepnumber=1,
                                                    numbersep=10pt
                                                }
                                                '''))

                    with doc.create(pylatex.Section('Code listing', numbering=False)):
                        for file in file_save_code_arr:
                            if not os.path.exists(file):
                                print(f"Specified code file not found: {file}")
                            with doc.create(pylatex.Subsection(file,numbering=False)):
                                code = open(file, 'r').read()
                                doc.append(pylatex.NoEscape(r'\begin{lstlisting}'))
                                doc.append(pylatex.NoEscape('\n'))
                                doc.append(pylatex.NoEscape(code))
                                doc.append(pylatex.NoEscape(r'\end{lstlisting}'))
                    doc.generate_pdf(clean=True, clean_tex=True)
                    
                    collected_pdfs.append(code_pdf+'.pdf')
                    print("\t\tCode report generation complete.")
                except Exception as e:
                    print(f"Unable to save code as PDF. Error message: {e}")

            # Combine all PDFs
            if len(collected_pdfs)>1:
                combine_pdfs(collected_pdfs, file_save_path, True)
            else:
                import os
                if os.path.exists(file_save_path):
                    os.remove(file_save_path)
                os.rename(collected_pdfs[0], file_save_path)

        except Exception as e:
            print(e)
            print(f"Unable to save to specified file: {str(file_save_path)}")

# -------------------------------------
            
def combine_pdfs(file_names, destination_name, delete_originals=False):
    """
    Combine multiple PDFs into a single output file.

    Parameters
    ----------
    file_names : list of str
        Paths to source PDFs; must contain at least two items.
    destination_name : str
        Output PDF path.
    delete_originals : bool, optional
        If True, delete the source PDFs after combining (default False).

    Returns
    -------
    None

    Notes
    -----
    - Uses ``fitz`` (PyMuPDF). All input files must exist.

    Examples
    --------
    >>> combine_pdfs(['a.pdf', 'b.pdf'], 'combined.pdf')  # doctest: +SKIP
    """

    # Combine all PDFs
    if len(file_names)<2:
        print("Could not combine PDF's: at least two PDF's must be provided to this function.")
        return 

    import fitz, os

    for pdf in file_names:
        if not os.path.exists(pdf):
            print(f"PDF name provided does not exist: {pdf}")
            return

    try:
        cdoc = fitz.open()
        for pdf in file_names:
            with fitz.open(pdf) as idoc:
                cdoc.insert_pdf(idoc)
        cdoc.save(destination_name)
        cdoc.close()
    except Exception as e:
        print(f"PDF creation failed: {e}")
        return 
    
    if delete_originals:
        for pdf in file_names:
            os.remove(pdf)


def converttemp(original_unit, final_unit, value):
    """
    Convert temperature among C, F, K, and R.

    Parameters
    ----------
    original_unit : {'C', 'F', 'K', 'R'}
        Source unit.
    final_unit : {'C', 'F', 'K', 'R'}
        Target unit.
    value : float
        Temperature value in the source unit.

    Returns
    -------
    float
        Temperature in the target unit.

    Raises
    ------
    ValueError
        If an invalid unit is provided.

    Examples
    --------
    >>> converttemp('C', 'F', 0.0)
    32.0
    >>> round(converttemp('F', 'K', 32.0), 2)
    273.15
    """

    if original_unit == 'C':
        temp_c = value
    elif original_unit == 'F':
        temp_c = (value - 32) * 5/9
    elif original_unit == 'K':
        temp_c = value - 273.15
    elif original_unit == 'R':
        temp_c = (value - 491.67) * 5/9
    else:
        raise ValueError("Invalid original unit")
    
    # Convert from Celsius to the final unit
    if final_unit == 'C':
        return temp_c
    elif final_unit == 'F':
        return temp_c * 9/5 + 32
    elif final_unit == 'K':
        return temp_c + 273.15
    elif final_unit == 'R':
        return (temp_c + 273.15) * 9/5
    else:
        raise ValueError("Invalid final unit")

# def convert(original_unit, final_unit):
#     # Define conversion factors relative to base units

#     def parse_unit(unit):
#         if '^' in unit:
#             base_unit, exponent = unit.split('^')
#             exponent = int(exponent)
#         else:
#             base_unit, exponent = unit, 1
#         return base_unit, exponent
    
#     # Parse the units
#     original_base, original_exp = parse_unit(original_unit)
#     final_base, final_exp = parse_unit(final_unit)
    
#     # Check if the units are valid and have the same exponent
#     if original_base not in __conversion_factors or final_base not in __conversion_factors:
#         raise ValueError("Invalid units")
#     if original_exp != final_exp:
#         raise ValueError("Incompatible units")
    
#     # Calculate the conversion factor
#     factor = (__conversion_factors[original_base] / __conversion_factors[final_base]) ** original_exp
#     return factor
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
def __units_parse_factor(tokens):
    token = tokens.pop(0)
    if token == "(":
        result = __units_parse_term(tokens)
        tokens.pop(0)  # Discard ")"
        return result
    else:
        try:
            return float(token)
        except:
            return __conversion_factors[token][1]

def __units_parse_term(tokens):
    left = __units_parse_factor(tokens)
    while tokens and tokens[0] in "^*/":
        op = tokens.pop(0)
        right = __units_parse_factor(tokens)
        if op == "^":
            left = left**right
        elif op == "*":
            left *= right
        else:
            left /= right
    return left

def __units_parse_expression(expression):
    token_pattern = re.compile(r'\d+(?:\.\d+)?|[a-zA-Z\$]+|[*/()^]')
    tokens = re.findall(token_pattern, expression)
    result = __units_parse_term(tokens)
    return result

def convert(original_unit, final_unit):
    """
    Compute a multiplicative conversion factor from ``original_unit`` to ``final_unit``.

    The parser supports products, divisions, exponents, and parentheses.
    Temperature offsets (additive) are **not** handled by this function; use
    :func:`converttemp` for C/F/K/R conversions.

    Parameters
    ----------
    original_unit : str
        Original unit expression (e.g., ``'m^2'``, ``'W*hr'``, ``'kg*m/s^2'``).
    final_unit : str
        Final unit expression (e.g., ``'in^2'``, ``'J'``, ``'N'``).

    Returns
    -------
    float
        Conversion factor such that ``value_in_final = value_in_original * factor``.

    Examples
    --------
    >>> round(convert('m^2', 'in^2'), 4)
    1550.0031
    >>> convert('W*hr', 'J')
    3600.0
    """

    original_f = __units_parse_expression(original_unit)
    final_f = __units_parse_expression(final_unit)
    return original_f/final_f



# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
        

def current_file():
    """
    Returns the name of the local python file
    """
    import os, inspect
    return os.path.basename(inspect.stack()[1].filename )

if __name__ == "__main__":

    # test
    print(convert('m^2','in^2'))
    print(convert('in^2','m^2'))
    print(convert('W*hr','J'))
    print(convert('tsp','m^3'))
