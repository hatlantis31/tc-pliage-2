import codecs

from pandas import DataFrame


def csv_to_dataframe(csv_file, header_row=None, data_start_row=None):
    """
    Reads a CSV file, removes null characters from all columns,
    and returns a pandas DataFrame.

    :param str csv_file: Path to the CSV file.
    :param header_row: Row number(s) to use as the header row(s).
        If None, the header row(s) will be automatically inferred.
    :type header_row: int optional
    :param int data_start_row: Row number to start reading data from.
        If None, data will be read from the first row after the header row(s).
    :returns: DataFrame containing the data from the CSV file,
        with null characters removed from all columns.
    :rtype: pandas.DataFrame

    """
    # Open the file in read mode with UTF-8 encoding, ignoring any decoding errors
    with codecs.open(csv_file, 'r', encoding='utf-8', errors='ignore') as file:
        data = []  # List to store the data rows
        header = None  # Variable to store the header row(s)
        line_number = 0  # Variable to keep track of the line number

        # Iterate over each line in the file
        for line in file:
            line_number += 1
            # Remove null characters from each value in the line
            row = [value.replace('\x00', '') for value in line.strip().split(',')]

            # If header_rows is specified and the current line number is in header_rows
            if header_row is not None and line_number == header_row:
                header = row  # Store the row as the header

            # If start_row is None (not specified) or the line number is greater than or equal to start_row
            elif data_start_row is None or line_number >= data_start_row:
                data.append(row)  # Append the row to the data list

        # Create the DataFrame from the data list, using the header as the column names and return it
        return DataFrame(data, columns=header)