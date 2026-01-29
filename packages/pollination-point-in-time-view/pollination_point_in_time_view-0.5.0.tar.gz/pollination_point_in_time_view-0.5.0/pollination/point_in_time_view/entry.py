from pollination_dsl.dag import Inputs, DAG, task, Outputs
from dataclasses import dataclass
from pollination.honeybee_radiance.view import SplitViewCount

# input/output alias
from pollination.alias.inputs.model import hbjson_model_view_input
from pollination.alias.inputs.pit import point_in_time_view_metric_input
from pollination.alias.inputs.radiancepar import rad_par_view_input
from pollination.alias.inputs.bool_options import skip_overture_input
from pollination.alias.inputs.view import cpu_count
from pollination.alias.outputs.daylight import point_in_time_view_results

from ._prepare_folder import PointInTimeViewPrepareFolder
from ._raytracing import PointInTimeViewRayTracing


@dataclass
class PointInTimeViewEntryPoint(DAG):
    """Point-in-time View-based entry point."""

    # inputs
    model = Inputs.file(
        description='A Honeybee model in HBJSON file format.',
        extensions=['json', 'hbjson', 'pkl', 'hbplk', 'zip'],
        alias=hbjson_model_view_input
    )

    sky = Inputs.str(
        description='Sky string for any type of sky (cie, climate-based, irradiance, '
        'illuminance). This can be a minimal representation of the sky through '
        'altitude and azimuth (eg. "cie -alt 71.6 -az 185.2 -type 0"). Or it can be '
        'a detailed specification of time and location (eg. "climate-based 21 Jun 12:00 '
        '-lat 41.78 -lon -87.75 -tz 5 -dni 800 -dhi 120"). Both the altitude and '
        'azimuth must be specified for the minimal representation to be used. See the '
        'honeybee-radiance sky CLI group for a full list of options '
        '(https://www.ladybug.tools/honeybee-radiance/docs/cli/sky.html).'
    )

    metric = Inputs.str(
        description='Text for the type of metric to be output from the calculation. '
        'Choose from: illuminance, irradiance, luminance, radiance.',
        default='luminance', alias=point_in_time_view_metric_input,
        spec={'type': 'string',
              'enum': ['illuminance', 'irradiance', 'luminance', 'radiance']},
    )

    resolution = Inputs.int(
        description='An integer for the maximum dimension of each image in pixels '
        '(either width or height depending on the input view angle and type).',
        spec={'type': 'integer', 'minimum': 1}, default=800
    )

    view_filter = Inputs.str(
        description='Text for a view identifier or a pattern to filter the views '
        'of the model that are simulated. For instance, first_floor_* will simulate '
        'only the views that have an identifier that starts with first_floor_. By '
        'default, all views in the model will be simulated.',
        default='*'
    )

    skip_overture = Inputs.str(
        description='A switch to note whether an ambient file (.amb) should be '
        'generated for an overture calculation before the view is split into smaller '
        'views. With an overture calculation, the ambient file (aka ambient cache) is '
        'first populated with values. Thereby ensuring that - when reused to create '
        'an image - Radiance uses interpolation between already calculated values '
        'rather than less reliable extrapolation. The overture calculation has '
        'comparatively small computation time to full rendering but is single-core '
        'can become time consuming in situations with very high numbers of '
        'rendering multiprocessors.', default='overture', alias=skip_overture_input,
        spec={'type': 'string', 'enum': ['overture', 'skip-overture']}
    )

    cpu_count = Inputs.int(
        default=12,
        description='The number of CPUs for parallel execution. This will be '
        'used to determine the number of times that views are subdivided.',
        spec={'type': 'integer', 'minimum': 1},
        alias=cpu_count
    )

    radiance_parameters = Inputs.str(
        description='The radiance parameters for ray tracing',
        default='-ab 2 -aa 0.25 -ad 512 -ar 16',
        alias=rad_par_view_input
    )

    @task(template=PointInTimeViewPrepareFolder)
    def prepare_folder_point_in_time_view(
        self, model=model, sky=sky, metric=metric, resolution=resolution,
        view_filter=view_filter, cpu_count=cpu_count
    ):
        return [
            {
                'from': PointInTimeViewPrepareFolder()._outputs.model_folder,
                'to': 'model'
            },
            {
                'from': PointInTimeViewPrepareFolder()._outputs.resources,
                'to': 'resources'
            },
            {
                'from': PointInTimeViewPrepareFolder()._outputs.results,
                'to': 'results'
            },
            {
                'from': PointInTimeViewPrepareFolder()._outputs.views,
                'description': 'View information.'
            }
        ]

    @task(
        template=SplitViewCount,
        needs=[prepare_folder_point_in_time_view],
        sub_paths={'views_file': 'views_info.json'}
    )
    def compute_view_split_count(
        self, views_file=prepare_folder_point_in_time_view._outputs.results,
        cpu_count=cpu_count
    ):
        return [
            {
                'from': SplitViewCount()._outputs.split_count,
                'description': 'An integer for the number of times to split the view.'
            }
        ]

    @task(
        template=PointInTimeViewRayTracing,
        needs=[prepare_folder_point_in_time_view, compute_view_split_count],
        loop=prepare_folder_point_in_time_view._outputs.views,
        sub_folder='initial_results/{{item.name}}',  # create a subfolder for each view
        sub_paths={
            'view': 'view/{{item.full_id}}.vf',
            'octree_file': 'scene.oct',
            'bsdfs': 'bsdf',
            'ies': 'ies'
            }
    )
    def point_in_time_view_ray_tracing(
        self, metric=metric, resolution=resolution,
        skip_overture=skip_overture,
        radiance_parameters=radiance_parameters,
        view_count=compute_view_split_count._outputs.split_count,
        octree_file=prepare_folder_point_in_time_view._outputs.resources,
        view_name='{{item.full_id}}',
        view=prepare_folder_point_in_time_view._outputs.model_folder,
        bsdfs=prepare_folder_point_in_time_view._outputs.model_folder,
        ies=prepare_folder_point_in_time_view._outputs.model_folder
    ):
        # this task doesn't return a file for each loop.
        # instead we access the results folder directly as an output
        pass

    results = Outputs.folder(
        source='results', description='Folder with raw image files (.HDR) that contain '
        'images for each view.', alias=point_in_time_view_results
    )
