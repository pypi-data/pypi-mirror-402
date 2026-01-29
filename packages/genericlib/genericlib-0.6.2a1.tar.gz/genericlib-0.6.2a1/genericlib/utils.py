"""
genericlib.utils
================

General-purpose utility classes and functions for data formatting,
validation, platform inspection, object manipulation, and structured output.

This module consolidates a variety of reusable helpers designed to simplify
common programming tasks. It includes tools for formatted printing, type
checking, shell command execution, platform metadata retrieval, safe function
invocation, object manipulation, and tabular data presentation.

Use Cases
---------
- Improve readability of logs, reports, and console output.
- Validate and manipulate heterogeneous data structures safely.
- Execute shell commands with structured error handling.
- Retrieve environment metadata for debugging or reporting.
- Present structured data (e.g., query results) in tabular form.

"""

from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

from textwrap import wrap
from pprint import pprint

import genericlib.datatype as datatype

from genericlib.constant import STRING
from genericlib.text import Text
from genericlib.collection import DotObject


class Printer:
    """
    A utility class for formatted printing of data.

    The `Printer` class provides methods to format and display data
    with optional headers, footers, failure messages, and width
    constraints. It is designed to improve readability of structured
    output such as lists, dictionaries, or tabular data.

    Methods
    -------
    get(data, header='', footer='', failure_msg='', width=80, width_limit=20) -> str
        Format the given data into a string with optional header and footer.
        If the data is empty or invalid, return the `failure_msg`.
        - `width` specifies the maximum line width before wrapping.
        - `width_limit` controls the maximum width of individual items.

    print(data, header='', footer='', failure_msg='', width=80, width_limit=20, print_func=None) -> None
        Print the formatted data directly to standard output (or a custom
        print function if provided). Accepts the same arguments as `get`.
    """
    @classmethod
    def get(cls, data, header='', footer='',
            width=80, width_limit=20, failure_msg=''):
        """
        Format data into a readable string with optional header and footer.

        This method converts the given `data` into a formatted string,
        applying line wrapping and width constraints for readability.
        If the data is empty or invalid, the provided `failure_msg` is
        returned instead. It is useful for preparing structured output
        (lists, dicts, tabular data) for display or logging.

        Parameters
        ----------
        data : str, list
            a text or a list of text.
        header : str
            Text to prepend before the formatted data. Default is empty.
        footer : str
            Text to append after the formatted data. Default is empty.
        failure_msg : str
            Message to return if `data` is empty or invalid. Default is empty.
        width : int
            Maximum line width before wrapping. Default is 80.
        width_limit : int
            Maximum width of individual items before truncation. Default is 20.

        Returns
        -------
        str
            A formatted string representation of the data, including
            optional header and footer. If `data` is empty, returns
            `failure_msg`.

        Notes
        -----
        - Line wrapping ensures readability for long strings or lists.
        - Width limits prevent overly long items from breaking formatting.
        - This method does not print directly; use `Printer.print` for output.
        """
        lst = []
        result = []

        if width > 0:
            right_bound = width - 4
        else:
            right_bound = 76

        headers = []
        if header:
            if datatype.is_mutable_sequence(header):
                for item in header:
                    for line in str(item).splitlines():
                        headers.extend(wrap(line, width=right_bound))
            else:
                headers.extend(wrap(str(header), width=right_bound))

        footers = []
        if footer:
            if datatype.is_mutable_sequence(footer):
                for item in footer:
                    for line in str(item).splitlines():
                        footers.extend(wrap(line, width=right_bound))
            else:
                footers.extend(wrap(str(footer), width=right_bound))

        if data:
            data = data if datatype.is_mutable_sequence(data) else [data]
        else:
            data = []

        for item in data:
            if width > 0:
                if width >= width_limit:
                    for line in str(item).splitlines():
                        lst.extend(wrap(line, width=right_bound + 4))
                else:
                    lst.extend(line.rstrip() for line in str(item).splitlines())
            else:
                lst.append(str(item))
        length = max(len(str(i)) for i in lst + headers + footers)

        if width >= width_limit:
            length = right_bound if right_bound > length else length

        result.append(Text.format('+-{}-+', '-' * length))      # noqa
        if header:
            for item in headers:
                result.append(Text.format('| {} |', item.ljust(length)))    # noqa
            result.append(Text.format('+-{}-+', '-' * length))  # noqa

        for item in lst:
            result.append(item)
        result.append(Text.format('+-{}-+', '-' * length))      # noqa

        if footer:
            for item in footers:
                result.append(Text.format('| {} |', item.ljust(length)))    # noqa
            result.append(Text.format('+-{}-+', '-' * length))  # noqa

        if failure_msg:
            result.append(failure_msg)

        txt = str.join(STRING.NEWLINE, result)
        return txt

    @classmethod
    def print(cls, data, header='', footer='',
              width=80, width_limit=20, failure_msg='', print_func=None):
        """
        Print formatted data with optional header and footer.

        This method formats the given `data` into a readable string
        (using the same logic as `Printer.get`) and prints it directly
        to standard output or a custom print function. It is useful for
        displaying structured output such as lists, dictionaries, or
        tabular data in a human-readable way.

        Parameters
        ----------
        data : str, list
            a text or a list of text.
        header : str
            Text to prepend before the formatted data. Default is empty.
        footer : str
            Text to append after the formatted data. Default is empty.
        failure_msg : str
            Message to print if `data` is empty or invalid. Default is empty.
        width : int
            Maximum line width before wrapping. Default is 80.
        width_limit : int
            Maximum width of individual items before truncation. Default is 20.
        print_func : callable
            A custom print function to use instead of the built-in `print`.
            Must accept a single string argument. Default is None.

        Returns
        -------
        None
            This method prints the formatted output and does not return a value.

        Notes
        -----
        - Internally uses `Printer.get` to format the data before printing.
        - If `print_func` is provided, the formatted string is passed to it
          instead of being printed to stdout.
        """

        txt = Printer.get(data, header=header, footer=footer,
                          failure_msg=failure_msg, width=width,
                          width_limit=width_limit)

        print_func = print_func if callable(print_func) else print
        print_func(txt)

    @classmethod
    def get_message(cls, fmt, *args, style='format', prefix=''):
        """
        Construct a formatted message string with optional prefix.

        This method formats a message using either Python's new-style
        (`str.format`) or old-style (`%`) string interpolation. It allows
        flexible message construction with positional arguments and an
        optional prefix. If no arguments are provided, the format string
        itself is returned.

        Parameters
        ----------
        fmt : str
            The format string to interpolate. Can contain placeholders
            compatible with either `.format` or `%` depending on `style`.
        *args : arguments
            Positional arguments to substitute into the format string.
        style : str, optional
            The formatting style to use:
            - ``'format'`` : use `str.format` (default).
            - ``'%'``      : use old-style `%` interpolation.
        prefix : str, optional
            A string to prepend before the formatted message. If provided,
            it is followed by a space before the message. Default is empty.

        Returns
        -------
        str
            The formatted message string, optionally prefixed.
        """

        if args:
            message = fmt.format(*args) if style == 'format' else fmt % args
        else:
            message = fmt

        message = '{} {}'.format(prefix, message) if prefix else message
        return message

    @classmethod
    def print_message(cls, fmt, *args, style='format', prefix='', print_func=None):
        """
        Format and print a message with optional prefix.

        This method constructs a message string using either Python's
        new-style (`str.format`) or old-style (`%`) string interpolation,
        then prints it directly to standard output or a custom print
        function. It is useful for producing consistent, human-readable
        messages for logging, reporting, or user-facing output.

        Parameters
        ----------
        fmt : str
            The format string to interpolate. Can contain placeholders
            compatible with either `.format` or `%` depending on `style`.
        *args : arguments
            Positional arguments to substitute into the format string.
        style : str, optional
            The formatting style to use:
            - ``'format'`` : use `str.format` (default).
            - ``'%'``      : use old-style `%` interpolation.
        prefix : str, optional
            A string to prepend before the formatted message. If provided,
            it is followed by a space before the message. Default is empty.
        print_func : callable, optional
            A custom print function to use instead of the built-in `print`.
            Must accept a single string argument. Default is None.

        Returns
        -------
        None
            This method prints the formatted message and does not return a value.
        """
        message = cls.get_message(fmt, *args, style=style, prefix=prefix)
        print_func = print_func if callable(print_func) else print
        print_func(message)


class Tabular:
    """
    A utility class for constructing and displaying tabular data.

    The `Tabular` class formats dictionaries (or lists of dictionaries)
    into a human-readable table. It supports column selection, text
    justification, and handling of missing values. This is useful for
    presenting structured data such as query results, reports, or logs
    in a clear tabular format.

    Attributes
    ----------
    data : list of dict
        The input data to format. Can be a list of dictionaries or a
        single dictionary (which will be wrapped in a list).
    columns : list of str, optional
        A list of column headers to include in the table. If None,
        all keys from the dictionaries are used. Default is None.
    justify : str, optional
        Text alignment for columns. Must be one of:
        - ``'left'``   : left-align text (default).
        - ``'right'``  : right-align text.
        - ``'center'`` : center-align text.
    missing : str, optional
        Placeholder text for missing values when a column is not found
        in the data. Default is ``'not_found'``.

    Methods
    -------
    validate_argument_list_of_dict() -> None
        Validate that the input data is a list of dictionaries.
    build_width_table(columns) -> dict
        Compute the maximum width for each column based on the data.
    align_string(value, width) -> str
        Align a string within a given width according to `justify`.
    build_headers_string(columns, width_tbl) -> str
        Construct the header row as a formatted string.
    build_tabular_string(columns, width_tbl) -> str
        Construct the table body as a formatted string.
    process() -> None
        Process the input data and prepare the tabular representation.
    get() -> str or list
        Return the formatted table as a string, or raw data if not processed.
    print() -> None
        Print the formatted table directly to standard output.
    """
    def __init__(self, data, columns=None, justify='left', missing='not_found'):
        self.result = ''
        if isinstance(data, dict):
            self.data = [data]
        else:
            self.data = data
        self.columns = columns
        self.justify = str(justify).lower()
        self.missing = missing
        self.is_ready = True
        self.is_tabular = False
        self.failure = ''
        self.validate_argument_list_of_dict()
        self.process()

    def validate_argument_list_of_dict(self):
        """
        Validate that the input data is a list of dictionaries.

        This method ensures that the `data` attribute of the `Tabular`
        instance is properly structured as either:
        - A list of dictionaries, or
        - A single dictionary (which is automatically wrapped in a list
          during initialization).

        If the validation fails, the method sets internal flags to mark
        the tabular object as invalid and records an error message.

        Returns
        -------
        None
            This method does not return a value. It updates internal
            state (`is_ready`, `failure`) to reflect validation results.

        Raises
        ------
        TypeError
            If `data` is not a dictionary or a list of dictionaries.

        Notes
        -----
        - This method is called automatically during initialization.
        - Ensures that subsequent tabular processing methods can safely
          assume the input is valid.
        """
        if not isinstance(self.data, (list, tuple)):
            self.is_ready = False
            self.failure = 'data MUST be a list.'
            return

        if not self.data:
            self.is_ready = False
            self.failure = 'data MUST be NOT an empty list.'
            return

        chk_keys = list()
        for a_dict in self.data:
            if isinstance(a_dict, dict):
                if not a_dict:
                    self.is_ready = False
                    self.failure = 'all dict elements MUST be NOT empty.'
                    return

                keys = list(a_dict.keys())
                if not chk_keys:
                    chk_keys = keys
                else:
                    if keys != chk_keys:
                        self.is_ready = False
                        self.failure = 'dict element MUST have same keys.'
                        return
            else:
                self.is_ready = False
                self.failure = 'all elements of list MUST be dictionary.'
                return

    def build_width_table(self, columns):
        """
        Compute the maximum width for each column in the tabular data.

        This method analyzes the provided `columns` and the instance's `data`
        to determine the maximum string length required for each column. The
        result is a mapping of column names to their respective widths, which
        can be used to align and format tabular output consistently.

        Parameters
        ----------
        columns : list of str
            A list of column headers to include in the width calculation.
            Each column name is checked against the data to determine the
            longest string value.

        Returns
        -------
        dict
            A dictionary mapping each column name to its maximum string
            length (including the header itself).

        Notes
        -----
        - The width of each column is the maximum of:
            * The length of the column header.
            * The length of the longest value in that column across all rows.
        - Missing values are replaced with the `missing` attribute before
          measuring length.
        """
        width_tbl = dict(zip(columns, (len(str(k)) for k in columns)))

        for a_dict in self.data:
            for col, width in width_tbl.items():
                curr_width = len(str(a_dict.get(col, self.missing)))
                new_width = max(width, curr_width)
                width_tbl[col] = new_width
        return width_tbl

    def align_string(self, value, width):
        """
        Align a string within a given width according to the justification setting.

        This method takes a value, converts it to a string, and aligns it
        within the specified width based on the `justify` attribute of the
        `Tabular` instance. Supported justifications are left, right, and
        center alignment.

        Parameters
        ----------
        value : Any
            The data to align. It will be converted to a string before alignment.
        width : int
            The target width for alignment. If the string is shorter than
            `width`, padding is added according to the justification.

        Returns
        -------
        str
            The aligned string, padded with spaces as needed to fit the
            specified width.

        Notes
        -----
        - The `justify` attribute of the `Tabular` instance determines
          alignment:
            * ``'left'``   : pad on the right.
            * ``'right'``  : pad on the left.
            * ``'center'`` : pad evenly on both sides.
        - If `value` is longer than `width`, it is returned unchanged.
        """
        value = str(value)
        if self.justify == 'center':
            return str.center(value, width)
        elif self.justify == 'right':
            return str.rjust(value, width)
        else:
            return str.ljust(value, width)

    def build_headers_string(self, columns, width_tbl):
        """
        Construct the header row of the tabular output as a formatted string.

        This method takes a list of column headers and a width mapping table,
        then aligns each header according to the `justify` setting of the
        `Tabular` instance. The result is a single string representing the
        header row of the table.

        Parameters
        ----------
        columns : list of str
            A list of column names to include in the header row.
        width_tbl : dict
            A dictionary mapping each column name to its maximum width
            (as computed by `build_width_table`). Used to align headers
            consistently with the table body.

        Returns
        -------
        str
            A formatted string containing the aligned column headers,
            separated by spaces.

        Notes
        -----
        - Each header is padded or aligned based on the width specified
          in `width_tbl`.
        - Alignment is controlled by the `justify` attribute of the
          `Tabular` instance (left, right, or center).
        - The resulting string is typically used as the first row of
          the tabular output.
        """
        lst = []
        for col in columns:
            width = width_tbl.get(col)
            new_col = self.align_string(col, width)
            lst.append(new_col)
        return '| {} |'.format(str.join(' | ', lst))

    def build_tabular_string(self, columns, width_tbl):
        """
        Construct the body of the tabular output as a formatted string.

        This method iterates over the instance's `data` and builds a
        tabular representation row by row. Each value is aligned according
        to the `justify` setting of the `Tabular` instance and padded to
        the width specified in `width_tbl`. The result is a multi-line
        string representing the table body.

        Parameters
        ----------
        columns : list of str
            A list of column headers that define the order of values in
            each row.
        width_tbl : dict
            A dictionary mapping each column name to its maximum width
            (as computed by `build_width_table`). Used to align values
            consistently across rows.

        Returns
        -------
        str
            A formatted string containing the tabular data rows, with
            values aligned and separated by spaces.

        Notes
        -----
        - Missing values are replaced with the `missing` attribute of
          the `Tabular` instance.
        - Alignment is controlled by the `justify` attribute (left,
          right, or center).
        - The resulting string does not include headers; use
          `build_headers_string` for the header row.
        """
        lst_of_str = []
        for a_dict in self.data:
            lst = []
            for col in columns:
                val = a_dict.get(col, self.missing)
                width = width_tbl.get(col)
                new_val = self.align_string(val, width)
                lst.append(new_val)
            lst_of_str.append('| {} |'.format(str.join(' | ', lst)))

        return str.join(STRING.NEWLINE, lst_of_str)

    def process(self):
        """
        Prepare the input data for tabular formatting.

        This method validates the input `data` and constructs the internal
        structures required to generate a tabular representation. It ensures
        that the data is properly normalized (list of dictionaries), computes
        column widths, and builds both the header and body strings. After
        calling `process`, the table is ready to be retrieved with `get()` or
        printed with `print()`.

        Returns
        -------
        None
            This method updates internal state and does not return a value.

        Notes
        -----
        - Calls `validate_argument_list_of_dict()` to ensure data integrity.
        - Uses `build_width_table()` to compute column widths.
        - Relies on `build_headers_string()` and `build_tabular_string()` to
          construct the formatted output.
        - Must be executed before calling `get()` or `print()` if the table
          has not yet been processed.
        """
        if not self.is_ready:
            return

        try:
            keys = list(self.data[0].keys())
            columns = self.columns or keys
            width_tbl = self.build_width_table(columns)
            deco = ['-' * width_tbl.get(c) for c in columns]
            deco_str = '+-{}-+'.format(str.join('-+-', deco))
            headers_str = self.build_headers_string(columns, width_tbl)
            tabular_data = self.build_tabular_string(columns, width_tbl)

            lst = [deco_str, headers_str, deco_str, tabular_data, deco_str]
            self.result = str.join(STRING.NEWLINE, lst)
            self.is_tabular = True
        except Exception as ex:
            self.failure = '{}: {}'.format(type(ex).__name__, ex)
            self.is_tabular = False

    def get(self):
        """
        Retrieve the processed tabular output or the raw data.

        This method returns the formatted tabular string if the instance
        has successfully processed the input data into tabular format.
        Otherwise, it falls back to returning the original `data` attribute.

        Returns
        -------
        str or Any
            - If `is_tabular` is True, returns the formatted tabular string
              stored in `result`.
            - If `is_tabular` is False, returns the original `data`.

        Notes
        -----
        - Typically called after `process()` to retrieve the final tabular
          representation.
        - Provides a safe way to access either the formatted output or the
          raw data depending on processing status.
        """
        tabular_data = self.result if self.is_tabular else self.data
        return tabular_data

    def print(self):
        """
        Print the tabular content or raw data.

        This method retrieves the current output from `get()` and prints it
        in a human-readable format. If the result is a structured object
        (e.g., dict, list, tuple, or set), it uses `pprint` for pretty-printing.
        Otherwise, it prints the string representation directly.

        Returns
        -------
        None
            This method prints the output and does not return a value.

        Notes
        -----
        - If the data has been processed into tabular format, the formatted
          string is printed.
        - If the data is still raw (e.g., a dictionary or list), it is
          pretty-printed for readability.
        - Acts as a convenience wrapper around `get()` and `pprint`.
        """
        tabular_data = self.get()
        if isinstance(tabular_data, (dict, list, tuple, set)):
            pprint(tabular_data)
        else:
            print(tabular_data)


def get_data_as_tabular(data, columns=None, justify='left', missing='not_found'):
    """
    Convert structured data into a tabular string representation.

    This function wraps the `Tabular` class to provide a simple interface
    for translating dictionaries or lists of dictionaries into a formatted
    table. It supports optional column selection, text justification, and
    handling of missing values.

    Parameters
    ----------
    data : list of dict or dict
        The input data to format. Can be:
        - A list of dictionaries (multiple rows).
        - A single dictionary (treated as one row).
    columns : list of str, optional
        A list of column headers to include in the table. If None, all keys
        from the dictionaries are used. Default is None.
    justify : str, optional
        Text alignment for columns. Must be one of:
        - ``'left'``   : left-align text (default).
        - ``'right'``  : right-align text.
        - ``'center'`` : center-align text.
    missing : str, optional
        Placeholder text for missing values when a column is not found in
        the data. Default is ``'not_found'``.

    Returns
    -------
    str
        A formatted string representing the tabular data.

    Notes
    -----
    - Internally creates a `Tabular` instance and calls its `get()` method.
    - Useful for quickly converting structured data into a human-readable
      table without manually instantiating `Tabular`.
    """
    node = Tabular(data, columns=columns, justify=justify, missing=missing)
    result = node.get()
    return result


def print_data_as_tabular(data, columns=None, justify='left', missing='not_found'):
    """
    Print structured data in a tabular format.

    This function wraps the `Tabular` class to provide a simple interface
    for displaying dictionaries or lists of dictionaries as a formatted
    table. It supports optional column selection, text justification, and
    handling of missing values. The formatted table is printed directly
    to standard output.

    Parameters
    ----------
    data : list of dict or dict
        The input data to format. Can be:
        - A list of dictionaries (multiple rows).
        - A single dictionary (treated as one row).
    columns : list of str, optional
        A list of column headers to include in the table. If None, all keys
        from the dictionaries are used. Default is None.
    justify : str, optional
        Text alignment for columns. Must be one of:
        - ``'left'``   : left-align text (default).
        - ``'right'``  : right-align text.
        - ``'center'`` : center-align text.
    missing : str, optional
        Placeholder text for missing values when a column is not found in
        the data. Default is ``'not_found'``.

    Returns
    -------
    None
        This function prints the formatted table and does not return a value.

    Notes
    -----
    - Internally creates a `Tabular` instance and calls its `print()` method.
    - Useful for quickly displaying structured data without manually
      instantiating `Tabular`.
    """
    node = Tabular(data, columns=columns, justify=justify, missing=missing)
    node.print()


def do_silent_invoke(callable_obj, *args, filename='', **kwargs):
    """
    Invoke a callable while capturing and suppressing its stdout/stderr output.

    This method executes the given callable object with the provided arguments,
    redirecting `sys.stdout` and `sys.stderr` to in-memory buffers so that any
    printed output or error messages are captured instead of displayed. The
    captured streams, along with the callable's return value, are packaged into
    a `DotObject` for convenient access.

    Optionally, the combined output and error text can be written to a file.

    Parameters
    ----------
    callable_obj : Callable
        The function or callable object to be invoked.
    *args : arguments
        Positional arguments to pass to the callable.
    filename : str, optional
        Path to a file where the combined stdout and stderr output will be
        written. Defaults to an empty string (no file written).
    **kwargs : keyword arguments
        Keyword arguments to pass to the callable.

    Returns
    -------
    DotObject
        An object containing:
        - result : The return value of the callable.
        - output : Captured stdout text.
        - error : Captured stderr text.
        - output_and_error : Combined stdout and stderr text.

    Notes
    -----
    - Standard output and error streams are restored to their original state
      after invocation.
    - If `filename` is provided, the combined output and error are written
      to that file.
    - This method is useful for safely invoking functions that produce
      console output, allowing you to capture and inspect their output
      programmatically.
    """
    stdout_buffer, stderr_buffer = StringIO(), StringIO()

    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        ret_result = callable_obj(*args, **kwargs)

    stdout_result = stdout_buffer.getvalue()
    stderr_result = stderr_buffer.getvalue()

    output_and_error = (
        f"{stdout_result}\n{stderr_result}" if stderr_result else stdout_result
    )

    result = DotObject(
        result=ret_result,
        output=stdout_result,
        error=stderr_result,
        output_and_error=output_and_error,
    )

    if filename:
        with open(filename, "w", encoding="utf-8") as stream:
            stream.write(result.output_and_error)

    return result