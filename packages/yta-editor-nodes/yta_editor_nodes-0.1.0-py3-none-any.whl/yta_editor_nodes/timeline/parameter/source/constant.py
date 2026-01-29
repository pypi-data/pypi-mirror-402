from yta_editor_nodes.timeline.parameter.evaluation_context import EvaluationContext
from yta_editor_nodes.timeline.parameter.abstract import ParameterSource


class ConstantValue(ParameterSource):
    """
    The parameter source in which the value is always
    the same. It is constant.
    """

    def __init__(
        self,
        value: any
    ):
        self.value: any = value
        """
        The constant value itself.
        """

    def evaluate(
        self,
        context: EvaluationContext
    ) -> any:
        # As it is always the same value, we don't care
        # about the context
        return self.value
