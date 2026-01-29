from yta_math_graphic.curve.segment.distribution.abstract import WeightedSegmentDistribution
from yta_math_graphic.curve.segment.distribution.uniform import UniformWeightedSegmentDistribution
from yta_math_graphic.curve.segment.factory import SegmentFactory
from yta_math_graphic.curve.evaluator import CurveEvaluator
from yta_math_graphic.curve.definition import CurveDefinition
from yta_programming.decorators.requires_dependency import requires_dependency
from yta_validation.parameter import ParameterValidator
from typing import Union


class Curve:
    """
    A curve, representing both `x` and `y` axis in
    a normalized range (`[0.0, 1.0]`).
    """
    
    @property
    def nodes(
        self
    ) -> list['CurveNode']:
        """
        The list of nodes ordered by the `x` value.
        """
        return self._definition.nodes
    
    @property
    def segments(
        self
    ) -> list['CurveSegment']:
        """
        The list of segments ordered by the `x` value.
        """
        return self._evaluator._segments
    
    @property
    def x_min(
        self
    ) -> Union[float, None]:
        """
        The minimum `x` value. Useful value to use for
        the axis and because it is where the progress
        starts.
        """
        return self._definition.x_min
    
    @property
    def x_max(
        self
    ) -> Union[float, None]:
        """
        The maximum `x` value. Useful value to use for
        the axis and because it is where the progress
        ends.
        """
        return self._definition.x_max
    
    @property
    def y_min(
        self
    ) -> Union[float, None]:
        """
        The minimum `y` value.
        """
        return self._definition.y_min
    
    @property
    def y_max(
        self
    ) -> Union[float, None]:
        """
        The maximum `y` value.
        """
        return self._definition.y_max
    
    @property
    def distance(
        self
    ) -> Union[float, None]:
        """
        The distance (normalized) of the whole curve.
        """
        return self._definition.distance

    def __init__(
        self,
        distribution: WeightedSegmentDistribution = UniformWeightedSegmentDistribution(),
        segment_factory: SegmentFactory = SegmentFactory(),
    ):
        ParameterValidator.validate_mandatory_subclass_of('distribution', distribution, WeightedSegmentDistribution)
        ParameterValidator.validate_mandatory_instance_of('segment_factory', segment_factory, SegmentFactory)

        self._definition = CurveDefinition()
        """
        *For internal use only*

        The definition of the curve.
        """
        self._distribution = distribution
        """
        *For internal use only*

        The distribution of the curve.
        """
        self._segment_factory = segment_factory
        """
        *For internal use only*

        The segment factory of the curve.
        """
        self._evaluator: CurveEvaluator = None
        """
        *For internal use only*

        The evaluator of the curve.
        """

        self._reset_cache()

    def add_node(
        self,
        x: float,
        y: float
    ) -> 'Curve':
        """
        Add a new node to the `x` provided with the `y`
        associated value. The `x` and `y` parameters
        must be values in the `[0.0, 1.0]` range.
        """
        ParameterValidator.validate_mandatory_number_between('x', x, 0.0, 1.0)
        ParameterValidator.validate_mandatory_number_between('y', y, 0.0, 1.0)

        self._definition.add_node(x, y)
        # Invalidate cache
        self._evaluator = None
        self._reset_cache()

        return self

    def _reset_cache(
        self
    ) -> 'Curve':
        """
        *For internal use only*

        Reset the cache by reseting the evaluator.
        """
        self._evaluator = CurveEvaluator(
            self._definition,
            self._distribution,
            self._segment_factory
        )

        return self

    def evaluate(
        self,
        progress_normalized: float
    ) -> float:
        """
        Get the `y` value associated to the global
        `progress_normalized` provided, that will be
        transformed into the local progress for the
        specific segment it belongs to in order to
        obtain that value.
        """
        if self._evaluator is None:
            self._reset_cache()

        return self._evaluator.evaluate(progress_normalized)
    
    def evaluate_at(
        self,
        x: float
    ) -> float:
        """
        Get the `y` value associated to the normalized `x`
        provided, that will be transformed into the global
        `progress_normalized`, that will be turned into the
        local progress for the specific segment it belongs
        to.
        """
        if self._evaluator is None:
            self._reset_cache()

        return self._evaluator.evaluate_at(x)

    @requires_dependency('matplotlib', 'yta_math', 'matplotlib')
    def plot(
        self,
        number_of_samples_per_segment: int = 100,
        do_draw_nodes: bool = True,
        do_draw_segments: bool = True
    ) -> None:
        """
        *Requires optional dependency `matplotlib`*

        Displays the curve in a normalized space
        `[0.0, 1.0] -> [0.0, 1.0]`.
        """
        import matplotlib.pyplot as plt
        import numpy as np

        plt.xlim(0.0, 1.0)
        plt.ylim(0.0, 1.0)
        plt.axhline(0.0, linewidth = 1)
        plt.axvline(0.0, linewidth = 1)
        plt.grid(True)

        nodes = self.nodes

        if do_draw_segments:
            for node_left, node_right in zip(nodes[:-1], nodes[1:]):
                xs = np.linspace(node_left.x, node_right.x, number_of_samples_per_segment)
                ys = [
                    self.evaluate_at(x)
                    for x in xs
                ]
                plt.plot(xs, ys, linewidth = 2)

        if do_draw_nodes:
            x_nodes = [
                node.x
                for node in nodes
            ]
            y_nodes = [
                node.y
                for node in nodes
            ]

            plt.scatter(
                x_nodes,
                y_nodes,
                s = 80,
                facecolors = 'white',
                edgecolors = 'black',
                zorder = 3
            )

        plt.xlabel('Progress (normalized)')
        plt.ylabel('Value (normalized)')
        plt.title('Curve')

        plt.show()

"""
Hay un concepto que es 
"""
