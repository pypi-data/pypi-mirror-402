"""Raytracing DAG for point-in-time View-based."""

from pollination_dsl.dag import Inputs, DAG, task
from dataclasses import dataclass

from pollination.honeybee_radiance.view import SplitView, MergeImages
from pollination.honeybee_radiance.rpict import RayTracingPicture


@dataclass
class PointInTimeViewRayTracing(DAG):
    """Point-in-time View-based ray tracing."""
    # inputs

    metric = Inputs.str(
        description='Text for the type of metric to be output from the calculation. '
        'Choose from: illuminance, irradiance, luminance, radiance.',
        default='luminance',
        spec={'type': 'string',
              'enum': ['illuminance', 'irradiance', 'luminance', 'radiance']}
    )

    resolution = Inputs.int(
        description='An integer for the maximum dimension of each image in pixels '
        '(either width or height depending on the input view angle and type).',
        spec={'type': 'integer', 'minimum': 1}, default=800
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
        'rendering multiprocessors.', default='overture',
        spec={'type': 'string', 'enum': ['overture', 'skip-overture']}
    )

    view_count = Inputs.int(
        description='Number of views into which the input view will be subdivided.',
        spec={'type': 'integer', 'minimum': 1}
    )

    radiance_parameters = Inputs.str(
        description='The radiance parameters for ray tracing',
        default='-ab 2 -aa 0.25 -ad 512 -ar 16'
    )

    octree_file = Inputs.file(
        description='A Radiance octree file.',
        extensions=['oct']
    )

    view_name = Inputs.str(
        description='View file name. This is useful to rename the final result '
        'file to {view_name}.HDR'
    )

    view = Inputs.file(description='Input view file.', extensions=['vf'])

    bsdfs = Inputs.folder(
        description='Folder containing any BSDF files needed for ray tracing.',
        optional=True
    )

    ies = Inputs.folder(
        description='Folder containing any IES files needed for ray tracing.',
        optional=True
    )

    @task(template=SplitView)
    def split_view(
        self, input_view=view, view_count=view_count, resolution=resolution,
        overture=skip_overture, scene_file=octree_file,
        radiance_parameters=radiance_parameters, bsdf_folder=bsdfs, ies_folder=ies
    ):
        return [
            {'from': SplitView()._outputs.views_list},
            {'from': SplitView()._outputs.output_folder, 'to': 'sub_views'},
            {'from': SplitView()._outputs.ambient_cache, 'to': 'sub_views/view.amb'}
        ]

    @task(
        template=RayTracingPicture,
        needs=[split_view],
        loop=split_view._outputs.views_list,
        sub_folder='results',
        sub_paths={'view': '{{item.path}}'}
    )
    def ray_tracing(
        self, radiance_parameters=radiance_parameters, metric=metric,
        resolution=resolution, scale_factor=2,
        ambient_cache=split_view._outputs.ambient_cache,
        view=split_view._outputs.output_folder, scene_file=octree_file,
        bsdf_folder=bsdfs,  ies_folder=ies
    ):
        return [
            {
                'from': RayTracingPicture()._outputs.result_image,
                'to': '{{item.name}}.unf'
            }
        ]

    @task(
        template=MergeImages, needs=[ray_tracing]
    )
    def merge_results(
        self, name=view_name, extension='.unf', folder='results',
        scale_factor=2, original_view=view
    ):
        return [
            {
                'from': MergeImages()._outputs.result_image,
                'to': '../../results/{{self.name}}.HDR'
            }
        ]
