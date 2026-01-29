from yta_math_graphic.curve.definition import CurveDefinition
from yta_math_graphic.curve.segment.distribution.abstract import WeightedSegmentDistribution
from yta_math_graphic.curve.segment.factory import SegmentFactory


class CurveEvaluator:
    """
    The evaluator of a curve.

    TODO: Explain better
    """

    @property
    def _nodes(
        self
    ) -> list['CurveNode']:
        """
        The nodes of the curve, ordered by the `x` value.
        """
        return self._definition.nodes

    def __init__(
        self,
        definition: CurveDefinition,
        distribution: WeightedSegmentDistribution,
        segment_factory: SegmentFactory
    ):
        self._definition = definition
        """
        *For internal use only*

        The definition of the curve.
        """
        self._segments = [
            segment_factory.create(self._nodes[i], self._nodes[i + 1])
            for i in range(len(self._nodes) - 1)
        ]
        """
        *For internal use only*

        The segments of the curve, created based on the
        `segment_factory` provided, and including the
        nodes ordered by the `x` value.
        """
        # TODO: Maybe rename to '_weighted_distribution'
        self._distribution = distribution
        """
        *For internal use only*

        The distribution of the segments to apply in the
        curve.
        """

    def evaluate(
        self,
        progress_normalized: float
    ) -> float:
        """
        Get the value associated to the global
        `progress_normalized` provided, that will be
        transformed into the local progress for the specific
        segment it belongs to.
        """
        return self._distribution.get_y_from_progress(
            progress_normalized = progress_normalized,
            segments = self._segments
        )

        segment, progress_local = (
            self._distribution.map_progress(
                progress_normalized = progress_normalized,
                segments = self._segments
            )
        )

        return segment.evaluate(
            progress_local = progress_local
        )
    
    def evaluate_at(
        self,
        x: float
    ) -> float:
        """
        Get the value associated to the normalized `x` value
        provided, that will be transformed into the local
        progress of the specific segment it belongs to and
        then into its value.

        The `x` value must be normalized.
        """
        return self._distribution.get_y_from_x(
            x = x,
            segments = self._segments
        )

        return self.evaluate(
            progress_normalized = self._distribution.get_y_from_x(
                x = x,
                segments = self._segments
            )
        )
