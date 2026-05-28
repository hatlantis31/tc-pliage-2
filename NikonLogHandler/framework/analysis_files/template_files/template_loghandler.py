"""
This is a template for a log handler
"""

from pandas import DataFrame, read_table, concat
from main_app_files.core_script_files.log_handler_class import LogHandlerBaseClass, LogHandlerParameters
from main_app_files.core_script_files import custom_graphs


class TemplateLogHandler(LogHandlerBaseClass):
    """
    This class is used to handle the log file of the  log.
    """
    # ============ Editable required variable ============
    handler_parameters = LogHandlerParameters(log_handler_name=" name of the parser",
                                              version="x.y",
                                              description=" what is the use of the parser",
                                              log_pattern=r"log pattern",
                                              supported_machine_types=['32x ? ', '62x ? '],
                                              supported_logs=["log name"],
                                              logs_locations=["unknown"],
                                              analysis_options={"plot the data": "plot_graph"},
                                              log_handler_group="GRP")

    # mandatory
    @classmethod
    def parser(cls, file_location: str, **kwargs) -> DataFrame:
        """
        parse a Raw log parser handle one file a time
        :param file_location: expect file full path
        """
        df = read_table(file_location, sep='\t', header=None, skiprows=1)
        return df

    # optional
    @classmethod
    def join_tables(cls, data_tables: dict, **kwargs):
        """
        join all data tables into one table
        :param data_tables:
        :return:
        """
        df_joined = DataFrame()
        for file, table in data_tables.items():
            df_joined = concat([df_joined, table])
        df_joined.sort_values(by=['date'])
        df_joined = df_joined.reset_index(drop=True)
        return {'joined_data_name': df_joined}

    # optional
    @classmethod
    def plot_graph(cls, gui_container, file_name: str, data: DataFrame):
        """
        plot graph of the  data
        :param gui_container: gui container
        :param file_name: file name
        :param data: data
        """
        # plot function to modify to the need of the class
        graph_name = custom_graphs.CustomLineGraph(gui_container,
                                                   data_table=data,
                                                   x_axis="",
                                                   x_label="",
                                                   y_left_label="",
                                                   graph_title="",
                                                   y_left_axis=[""])
        graph_name.pack(fill="both", expand=1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)