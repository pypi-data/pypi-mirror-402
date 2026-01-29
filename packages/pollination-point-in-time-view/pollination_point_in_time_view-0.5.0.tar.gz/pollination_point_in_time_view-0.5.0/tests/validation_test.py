from pollination.point_in_time_view.entry import PointInTimeViewEntryPoint
from queenbee.recipe.dag import DAG


def test_point_in_time_view():
    recipe = PointInTimeViewEntryPoint().queenbee
    assert recipe.name == 'point-in-time-view-entry-point'
    assert isinstance(recipe, DAG)
