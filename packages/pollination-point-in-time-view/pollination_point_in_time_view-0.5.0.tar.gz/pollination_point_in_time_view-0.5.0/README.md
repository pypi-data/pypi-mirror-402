# point_in_time_view

Point-in-time view-based recipe for Pollination.

Use this recipe to get a High Dynamic Range (HDR) view of illuminance, irradiance,
luminance or radiance for a single point in time, given a HBJSON model.

The `view-count` input can be used to split each view for parallel processing, producing
multiple images that are recombined into a single .HDR for the view at the end of the
recipe. The recombination process automatically includes an anti-aliasing pass that
smooths and improves the quality of the image.

By default, the recipe will also perform an overture calculation prior to splitting
each view, which results in an image with better interpolation between neighboring pixels.
However, for parallelized simulations with a high `view-count`, this overture calculation
can account for a significant fraction of the run time. Accordingly the `skip-overture`
input can be used to skip the overture calculation in these circumstances.
