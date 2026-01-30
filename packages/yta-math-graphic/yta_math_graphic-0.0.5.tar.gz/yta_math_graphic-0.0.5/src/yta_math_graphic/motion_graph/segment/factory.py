from yta_math_graphic.motion_graph.node import MotionNode
from yta_math_graphic.motion_graph.segment.abstract import MotionSegment
from yta_math_graphic.motion_graph.segment import LinearMotionSegment, SmoothererMotionSegment


class MotionSegmentFactory:
    """
    A factory to create Motion Graph segments.
    """

    def create(
        self,
        node_start: MotionNode,
        node_end: MotionNode
    ) -> MotionSegment:
        """
        Create a new `CurveSegment` including the `left_node`
        and the `right_node` provided.
        """
        # TODO: Why is it only Linear here and how to
        # make it customizable (?)
        return SmoothererMotionSegment(
            node_start = node_start,
            node_end = node_end
        )
        # return LinearMotionSegment(
        #     node_start = node_start,
        #     node_end = node_end
        # )
