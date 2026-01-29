# ndx-franklab-novela Extension for NWB

# About

ndx-franklab-novela is a python package containing NWB custom extensions for Loren Frank's Lab.

# How to install

Add ndx-franklab-novela to your conda environment:

```
pip install ndx-franklab-novela
```

Or install the latest version from the repository:

```
pip install git+git://github.com/LorenFrankLab/ndx-franklab-novela
```

The original published extension maintained by NovelaNeuro can be installed using:

```
conda install -c conda-forge -c novelakrk ndx-franklab-novela
```

# Dependencies

This extension uses the [ndx-optogenetics](https://github.com/rly/ndx-optogenetics) extension.
Installing ndx-franklab-novela will install the latest version of ndx-optogenetics from PyPI.
Loading `ndx-franklab-novela` by importing `ndx_franklab_novela` will also load `ndx_optogenetics`.

# Extensions

## AssociatedFiles

Representation of associated files in NWB.

**Attributes:**

- **description**  `string`: description of associated file
- **content**  `string`: content of associated file
- **task_epochs**  `string`: id of epochs with task that is descripted by associated files

## HeaderDevice

Representation of HeaderDevice in NWB.

**Attributes:**

- **headstage_serial**  `string`: headstage_serial from header global configuration
- **headstage_smart_ref_on**  `string`: headstage_smart_ref_on from header global configuration
- **realtime_mode**  `string`: realtime_mode from header global configuration
- **headstage_auto_settle_on**  `string`: headstage_auto_settle_on from header global configuration
- **timestamp_at_creation**  `string`: timestamp_at_creation from header global configuration
- **controller_firmware_version**  `string`: conntroller_firmware_version from header global configuration
- **controller_serial**  `string`: conntroller_serial from header global configuration
- **save_displayed_chan_only**  `string`: save_displayed_chan_only from header global configuration
- **headstage_firmware_version**  `string`: headstage_firmware_version from header global configuration
- **qt_version**  `string`: qt_version from header global configuration
- **compile_date**  `string`: compile_date from header global configuration
- **compile_time**  `string`: compile_time from header global configuration
- **file_prefix**  `string`: file_prefix from header global configuration
- **headstage_gyro_sensor_on**  `string`: headstage_gyro_sensor_on from header global configuration
- **headstage_mag_sensor_on**  `string`: headstage_mag_sensor_on from header global configuration
- **trodes_version**  `string`: trodes_version from header global configuration
- **headstage_accel_sensor_on**  `string`: headstage_accel_sensor_on from header global configuration
- **commit_head**  `string`: commit_head from header global configuration
- **system_time_at_creation**  `string`: system_time_at_creation from header global configuration
- **file_path**  `string`: file_path from header global configuration

## ShanksElectrode

Representation of electrodes of a shank in NWB.

**Attributes:**

- **name**  `string`: name of the shank
- **rel_x**  `float`: the rel_x value of this electrode
- **rel_y**  `float`: the rel_y value of this electrode
- **rel_z**  `float`: the rel_z value of this electrode

## Shank

Representation of a shank in NWB.

**Attributes:**

- **name**  `string`: name of the shank
- **shanks_electrodes**  `dict`: electrodes in the shank

## Probe

Representation of a probe in NWB.

**Attributes:**

- **id**  `int`: unique id of the probe
- **probe_type**  `string`: type of probe
- **units**  `string`: units in device
- **probe_description**  `string`: description of probe
- **contact_side_numbering**  `bool`: Whether the electrodes were numbered in a scheme wherein the contacts were electrodes facing up toward the viewer (true) or if the numbering was based on the electrodes facing down (false). This is relevant when the goal is to determine where in the tissue each electrode contact is located. (optional)
- **contact_size**  `float`: value of contact size as float
- **shanks**  `dict`: shanks in the probe

## DataAcqDevice

Representation of data acquisition device in NWB.

**Attributes:**

- **system**  `string`: system of device
- **amplifier**  `string`: amplifier (optional)
- **adc_circuit**  `string`: adc_circuit (optional)

## CameraDevice

Representation of a camera device in NWB.

**Attributes:**

- **meters_per_pixel**  `float`: meters per pixel
- **lens**  `string`: info about lens in this camera
- **camera_name**  `string`: name of this camera
- **frame_rate**  `float`: frame rate of this camera (optional)

## FrankLabOptogeneticEpochsTable

An extension of the `OptogeneticEpochsTable` from [ndx-optogenetics](https://github.com/rly/ndx-optogenetics) with the following columns:

**Columns:**

- **epoch_name**  `string`: name of this epoch
- **epoch_number**  `int`: 1-indexed number of this epoch
- **convenience_code**  `string`: convenience code of this epoch
- **epoch_type**  `string`: type of this epoch
- **theta_filter_on**  `bool`: whether the theta filter was on (optional)
- **theta_filter_lockout_period_in_samples**  `int`: lockout period in samples for theta filter (optional)
- **theta_filter_phase_in_deg**  `float`: phase in degrees for theta filter (optional)
- **theta_filter_reference_ntrode**  `int`: reference ntrode for theta filter (optional)
- **spatial_filter_on**  `bool`: whether the spatial filter was on (optional)
- **spatial_filter_lockout_period_in_samples**  `int`: lockout period in samples for spatial filter (optional)
- **spatial_filter_region_node_coordinates_in_pixels** `float`, shape `(n_region, n_nodes, 2,)`: If the spatial filter was used, the (x, y) coordinate of each boundary-defining node for each region. _Note:_ all regions must have the same number of nodes. For regions with fewer nodes, use (-1, -1) to fill the additional xy values.'
- **spatial_filter_cameras_index**  `int`: index column for spatial filter cameras (optional)
- **spatial_filter_cameras** : references to `CameraDevice` objects used for spatial filter (optional)
- **spatial_filter_cameras_cm_per_pixel**  `float`: cm per pixel for spatial filter cameras (optional)
- **ripple_filter_on**  `bool`: whether the ripple filter was on (optional)
- **ripple_filter_lockout_period_in_samples**  `int`: lockout period in samples for ripple filter (optional)
- **ripple_filter_threshold_sd**  `float`: threshold in standard deviations for ripple filter (optional)
- **ripple_filter_num_above_threshold**  `int`: number of tetrodes above threshold for ripple filter (optional)
- **speed_filter_on** `bool`: Whether the speed filter was on. Closed-loop stimulation based on whether
      the animal is moving fast/slow enough. (optional)
- **speed_filter_threshold_in_cm_per_s** `float`: If the speed filter was used, the threshold for detecting a fast/slow animal (optional)
- **speed_filter_on_above_threshold** `bool`: If the speed filter was used, True if active when speed above threshold. (optional)
- **stimulus_signal** `TimeSeries`: Timeseries of the delivered stimulus. Can be continuous values or time of
      digital on/off events.

---
This extension was created using [ndx-template](https://github.com/nwb-extensions/ndx-template).
