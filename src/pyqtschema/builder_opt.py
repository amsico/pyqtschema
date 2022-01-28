from abc import abstractmethod


class IBuilder:
    """ Defines a builder-interface """

    @abstractmethod
    def create_widget(self, schema: dict, ui_schema: dict, state=None) -> 'SchemaWidgetMixin':
        raise NotImplementedError()
