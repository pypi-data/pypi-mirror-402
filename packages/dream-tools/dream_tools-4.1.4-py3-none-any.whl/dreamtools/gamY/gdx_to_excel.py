import os
import sys
import xlwings as xw
import pandas as pd
import dreamtools as dt
import re


# workbook_path = "../Konjunktur/konjunktur.xlsx"
# gdx_path = "../Konjunktur/Gdx/OER23August_nominal.gdx"
# sheet_name = "data"

def gdx_to_excel(gdx_path, workbook_path, sheet_name):
    """
    Fill an Excel worksheet with data from a GDX file.

    Parameters
    ----------
    gdx_path : str
        Path to GDX file
    workbook_path : str
        Path to an Excel workbook
    sheet_name : str
        Name of a sheet in the workbook
        In that sheet, the script expects a table with variables as index and years as column headers,
        starting in cell A1.
        The function will then fill the table with data from the GDX file.
        The function assumes that the time index is always last.
    """

    assert os.path.isfile(gdx_path), f"{gdx_path} not found"
    db = dt.Gdx(gdx_path)

    assert os.path.isfile(workbook_path), f"{workbook_path} not found"
    wb = xw.Book(workbook_path)

    assert sheet_name in wb.sheet_names, f'"{sheet_name}" not found in {workbook_path}'
    sheet = wb.sheets[sheet_name]

    data_range = sheet.range("A1", "B2").expand()
    df = data_range.options(pd.DataFrame, index=True).value
    try:
        fill_dataframe(df, db)
        data_range.offset(1, 1).resize(*df.shape).value = df.values
    except Exception as e:
        data_range.offset(1, 1).resize(*df.shape).value = None
        raise e
    
    wb.save()

def get_variable_name(variable_key):
    """Returns the variable name from a variable key, e.g. "qY[tje]" -> "qY" """
    return variable_key.split("[")[0]

def get_index(variable_key):
    """Returns the index from a variable key, e.g. "qY[tje]" -> "tje" """
    if "[" in variable_key:
        index_str = variable_key.split("[")[1][:-1]
        return index_str.split(",")

def index_to_lowercase(idx):
    """Change a pandas multiindex to lower case only"""
    return idx.set_levels([x.lower() if isinstance(x, str) else x for x in level] for level in idx.levels)

def remove_time_index(variable_key):
    """
    Remove time index from variable key.
    Examples:
    remove_time_index("qY[tje,t]") -> "qY[tje]"
    remove_time_index("qBNP[t]") -> "qBNP"
    """
    variable_key = re.sub(r"\[t\]", "", variable_key)
    variable_key = re.sub(r",t\]", "]", variable_key)
    return variable_key  

def remove_quotes(variable_key):
    """
    Remove quotes from variable key.
    Examples:
    remove_quotes("qY['tje']") -> "qY[tje]"
    """
    return variable_key.replace("'", "").replace('"', "")

def fill_dataframe(df, db):
    """
    Fills a dataframe with data from a GDX database
    The dataframe needs to have variables as index and years as column headers.
    E.g.
                    2016	2050
    vC[cTot]	    833 	1089
    pI_s[iM,tje]	None	None
    pI_s[iB,tje]	None	None
    """
    years = df.columns.astype(int)
    variable_keys = df.index
    for variable_key in variable_keys:
        error_message = None
        try:
            variable_name = get_variable_name(variable_key)
            index = get_index(remove_quotes(remove_time_index(variable_key)))

            if variable_name in db:
                variable = db[variable_name]
            else:
                error_message = "Variable not found"
                continue
            if len(variable) == 0:
                error_message = "Variable empty"
                continue

            try:
                if index is None:
                    df.loc[variable_key] = variable.reindex(years).values
                else:
                    variable.index = index_to_lowercase(variable.index)
                    index = tuple(x.lower() if isinstance(x, str) else x for x in index)
                    df.loc[variable_key] = variable.loc[index].reindex(years).values
            except KeyError:
                error_message = "Index not found"
        except Exception as e:
            error_message = f"{e}"
            print(f"Error getting {variable_key}: {error_message}")
        if error_message is not None:
            df.loc[variable_key] = error_message

    return df
