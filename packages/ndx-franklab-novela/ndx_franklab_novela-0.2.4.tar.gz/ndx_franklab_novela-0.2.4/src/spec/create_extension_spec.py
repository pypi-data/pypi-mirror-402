# -*- coding: utf-8 -*-
import os.path

from pynwb.spec import (
    NWBNamespaceBuilder,
    export_spec,
    NWBGroupSpec,
    NWBAttributeSpec,
    NWBDatasetSpec,
    NWBRefSpec,
)


def main():
    # these arguments were auto-generated from your cookiecutter inputs
    ns_builder = NWBNamespaceBuilder(
        name="""ndx-franklab-novela""",
        version="""0.2.4""",
        doc="""NWB extension to store additional metadata and data types for Loren Frank's Lab""",
        author=[
            "NovelaNeurotechnologies",
            "Loren Frank",
            "Eric Denovellis",
            "Ryan Ly",
        ],
        contact=[
            "devops@novelaneuro.com",
            "loren.frank@ucsf.edu",
            "eric.denovellis@ucsf.edu",
            "rly@lbl.gov",
        ],
    )
    ns_builder.include_namespace("core")
    ns_builder.include_namespace(namespace="ndx-optogenetics")

    shanks_electrode = NWBGroupSpec(
        neurodata_type_def="ShanksElectrode",
        neurodata_type_inc="NWBDataInterface",
        doc="electrode in the probe",
        attributes=[
            NWBAttributeSpec(name="name", doc="name of the electrode", dtype="text"),
            NWBAttributeSpec(name="rel_x", doc="the rel_x value of the electrode", dtype="float"),
            NWBAttributeSpec(name="rel_y", doc="the rel_y value of the electrode", dtype="float"),
            NWBAttributeSpec(name="rel_z", doc="the rel_z value of the electrode", dtype="float"),
        ],
    )

    shanks = NWBGroupSpec(
        neurodata_type_def="Shank",
        neurodata_type_inc="NWBDataInterface",
        doc="shank in the probe",
        groups=[NWBGroupSpec(neurodata_type_inc="ShanksElectrode", doc="electrode in the probe", quantity="*")],
        attributes=[
            NWBAttributeSpec(name="name", doc="name of the shank", dtype="text"),
        ],
    )

    probe = NWBGroupSpec(
        doc="A custom Probes interface",
        neurodata_type_def="Probe",
        neurodata_type_inc="Device",
        groups=[NWBGroupSpec(neurodata_type_inc="Shank", doc="shank in the probe", quantity="*")],
        attributes=[
            NWBAttributeSpec(name="id", doc="unique id of the probe", dtype="int"),
            NWBAttributeSpec(name="probe_type", doc="type of the probe", dtype="text"),
            NWBAttributeSpec(name="units", doc="units in probe, acceptable values um or mm", dtype="text"),
            NWBAttributeSpec(name="probe_description", doc="description of the probe", dtype="text"),
            NWBAttributeSpec(
                name="contact_side_numbering",
                doc=(
                    "Whether the electrodes were numbered in a scheme wherein the contacts were "
                    "electrodes facing up toward the viewer (true) or if the numbering was based "
                    "on the electrodes facing down (false). This is relevant when the goal is to "
                    "determine where in the tissue each electrode contact is located."
                ),
                dtype="bool",
                required=False,
            ),
            NWBAttributeSpec(name="contact_size", doc="value of contact size in float", dtype="float"),
        ],
    )

    data_acq_device = NWBGroupSpec(
        doc="A custom Device interface",
        neurodata_type_def="DataAcqDevice",
        neurodata_type_inc="Device",
        attributes=[
            NWBAttributeSpec(name="system", doc="system of device", dtype="text"),
            NWBAttributeSpec(name="amplifier", doc="amplifier", dtype="text", required=False),
            NWBAttributeSpec(name="adc_circuit", doc="adc_circuit", dtype="text", required=False),
        ],
    )

    camera_device = NWBGroupSpec(
        neurodata_type_def="CameraDevice",
        neurodata_type_inc="Device",
        doc="A custom Device interface",
        attributes=[
            NWBAttributeSpec(name="meters_per_pixel", doc="meters per pixel", dtype="float"),
            NWBAttributeSpec(name="camera_name", doc="name of the camera", dtype="text"),
            NWBAttributeSpec(name="lens", doc="lens info", dtype="text"),
            NWBAttributeSpec(
                name="frame_rate",
                doc="Frame rate of the camera, in frames per second.",
                dtype="float",
                required=False,
            ),
        ],
    )

    associated_files = NWBGroupSpec(
        neurodata_type_def="AssociatedFiles",
        neurodata_type_inc="NWBDataInterface",
        doc="content of files linked with nwb",
        attributes=[
            NWBAttributeSpec(name="description", doc="description of file", dtype="text"),
            NWBAttributeSpec(name="content", doc="content of file", dtype="text"),
            NWBAttributeSpec(name="task_epochs", doc="epochs this task belongs to", dtype="text"),
        ],
    )

    header_device = NWBGroupSpec(
        doc="metadata from global configuration from header",
        neurodata_type_def="HeaderDevice",
        neurodata_type_inc="Device",
        attributes=[
            NWBAttributeSpec(name="headstage_serial", doc="headstage_serial from global configuration", dtype="text"),
            NWBAttributeSpec(
                name="headstage_smart_ref_on", doc="headstage_smart_ref_on from global configuration", dtype="text"
            ),
            NWBAttributeSpec(name="realtime_mode", doc="realtime_mode from global configuration", dtype="text"),
            NWBAttributeSpec(
                name="headstage_auto_settle_on", doc="headstage_auto_settle_on from global configuration", dtype="text"
            ),
            NWBAttributeSpec(
                name="timestamp_at_creation", doc="timestamp_at_creation from global configuration", dtype="text"
            ),
            NWBAttributeSpec(
                name="controller_firmware_version",
                doc="conntroller_firmware_version from global configuration",
                dtype="text",
            ),
            NWBAttributeSpec(name="controller_serial", doc="controller_serial from global configuration", dtype="text"),
            NWBAttributeSpec(
                name="save_displayed_chan_only", doc="save_displayed_chan_only from global configuration", dtype="text"
            ),
            NWBAttributeSpec(
                name="headstage_firmware_version",
                doc="headstage_firmware_version from global configuration",
                dtype="text",
            ),
            NWBAttributeSpec(name="qt_version", doc="qt_version_version from global configuration", dtype="text"),
            NWBAttributeSpec(name="compile_date", doc="compile_date_version from global configuration", dtype="text"),
            NWBAttributeSpec(name="compile_time", doc="compile_time_version from global configuration", dtype="text"),
            NWBAttributeSpec(name="file_prefix", doc="file_prefix_version from global configuration", dtype="text"),
            NWBAttributeSpec(
                name="headstage_gyro_sensor_on",
                doc="headstage_gyro_sensor_on_version from global configuration",
                dtype="text",
            ),
            NWBAttributeSpec(
                name="headstage_mag_sensor_on",
                doc="headstage_mag_sensor_on_version from global configuration",
                dtype="text",
            ),
            NWBAttributeSpec(
                name="trodes_version", doc="trodes_versionversion from global configuration", dtype="text"
            ),
            NWBAttributeSpec(
                name="headstage_accel_sensor_on",
                doc="headstage_accel_sensor_on from global configuration",
                dtype="text",
            ),
            NWBAttributeSpec(name="commit_head", doc="commit_head from global configuration", dtype="text"),
            NWBAttributeSpec(
                name="system_time_at_creation", doc="system_time_at_creation from global configuration", dtype="text"
            ),
            NWBAttributeSpec(name="file_path", doc="file_path from global configuration", dtype="text"),
        ],
    )

    nwb_electrode_group = NWBGroupSpec(
        neurodata_type_def="NwbElectrodeGroup",
        neurodata_type_inc="ElectrodeGroup",
        doc="Custom nwb ElectrodeGroup",
        attributes=[
            NWBAttributeSpec(name="targeted_location", doc="predicted location", dtype="text"),
            NWBAttributeSpec(name="targeted_x", doc="predicted x coordinates", dtype="float"),
            NWBAttributeSpec(name="targeted_y", doc="predicted y coordinates", dtype="float"),
            NWBAttributeSpec(name="targeted_z", doc="predicted z coordinates", dtype="float"),
            NWBAttributeSpec(name="units", doc="units of fields, acceptable values: um or mm", dtype="text"),
        ],
    )

    frank_lab_optogenetic_epochs_table = NWBGroupSpec(
        neurodata_type_def="FrankLabOptogeneticEpochsTable",
        neurodata_type_inc="OptogeneticEpochsTable",
        doc=(
            "General metadata about the optogenetic stimulation that may change per epoch, with fields "
            "specific to Loren Frank Lab experiments. If the spatial filter is ON, then the experimenter "
            "can stimulate in either open (frequency-based) or closed loop (theta-based), only when animal is in "
            "a particular position. If the spatial filter is OFF, then ignore the position "
            "(this is not common / doesn't happen). If the spatial filter is ON and the experimenter is "
            "stimulating in open loop mode and the animal enters the spatial filter rectangle, then "
            "immediately apply one and only one stimulation bout. If stimulating in closed loop mode and the animal "
            "enters the rectangle, then every time the particular theta phase is detected, "
            "immediately apply one stimulation bout (accounting for the lockout period)."
        ),
        # TODO some lab members have other filters. Add those parameters below.
        datasets=[
            NWBDatasetSpec(
                name="epoch_name",
                neurodata_type_inc="VectorData",
                doc=("Name of the epoch."),
                dtype="text",
            ),
            NWBDatasetSpec(
                name="epoch_number",
                neurodata_type_inc="VectorData",
                doc=("1-indexed number of the epoch."),
                dtype="int",
            ),
            NWBDatasetSpec(
                name="convenience_code",
                neurodata_type_inc="VectorData",
                doc=("Convenience code of the epoch."),
                dtype="text",
            ),
            NWBDatasetSpec(
                name="epoch_type",
                neurodata_type_inc="VectorData",
                doc=("Type of the epoch."),
                dtype="text",
            ),
            NWBDatasetSpec(
                name="theta_filter_on",
                neurodata_type_inc="VectorData",
                doc=(
                    "Whether the theta filter was on. A theta filter is closed-loop stimulation - read one "
                    "tetrode and calculate the phase. Depending on the phase of theta, apply stimulation "
                    "immediately. "
                    "If this column is not present, then the theta filter was not used."
                ),
                dtype="bool",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="theta_filter_lockout_period_in_samples",
                neurodata_type_inc="VectorData",
                doc=(
                    "If the theta filter was used, lockout period in the number of samples (based on the "
                    "clock of the SpikeGadgets hardware) needed between stimulations, start to start. "
                    "Use -1 if the theta filter was not used."
                ),
                dtype="int",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="theta_filter_phase_in_deg",
                neurodata_type_inc="VectorData",
                doc=(
                    "If the theta filter was used, phase in degrees during closed-loop theta phase-specific "
                    "stimulation experiments. 0 is defined as the trough. 90 is ascending phase. Options are: "
                    "0, 90, 180, 270, 360, NaN. Use NaN if the theta filter was not used."
                ),
                dtype="float",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="theta_filter_reference_ntrode",
                neurodata_type_inc="VectorData",
                doc=(
                    "If the theta filter was used, reference electrode that used used for theta phase-specific "
                    "stimulation. ntrode is related to SpikeGadgets. ntrodes are specified in the electrode groups. "
                    "(note that ntrodes are 1-indexed.) mapping from ntrode to electrode ID is in the electrode "
                    "metadata files. Use -1 if the theta filter was not used."
                ),
                dtype="int",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="spatial_filter_on",
                neurodata_type_inc="VectorData",
                doc=(
                    "Whether the spatial filter was on. Closed-loop stimulation based on whether the position of "
                    "the animal is within a specified rectangular region of the video. "
                    "If this column is not present, then the spatial filter was not used."
                ),
                dtype="bool",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="spatial_filter_lockout_period_in_samples",
                neurodata_type_inc="VectorData",
                doc=(
                    "If the spatial filter was used, lockout period in the number of samples. "
                    "Uses trodes time (samplecount). Use -1 if the spatial filter was not used."
                ),
                dtype="int",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="spatial_filter_region_node_coordinates_in_pixels",
                neurodata_type_inc="VectorData",
                doc=(
                    "If the spatial filter was used, the (x, y) coordinate of each "
                    "boundary-defining node for each region. NOTE: all regions must have the same "
                    "number of nodes. For regions with fewer nodes, use (-1, -1) "
                    "to fill the additional xy values."
                ),
                dtype="int",
                shape=(None, None, None, 2),
                dims=("n_epochs", "n_regions", "n_nodes", "x y"),
                quantity="?",
            ),
            NWBDatasetSpec(
                name="spatial_filter_cameras_index",
                neurodata_type_inc="VectorIndex",
                doc=("Index column for `spatial_filter_cameras` so that each epoch can have multiple cameras."),
                quantity="?",
            ),
            NWBDatasetSpec(
                name="spatial_filter_cameras",
                neurodata_type_inc="VectorData",
                doc=("References to camera objects used for the spatial filter."),
                dtype=NWBRefSpec(
                    target_type="CameraDevice",
                    reftype="object",
                ),
                quantity="?",
            ),
            NWBDatasetSpec(
                name="spatial_filter_cameras_cm_per_pixel_index",
                neurodata_type_inc="VectorIndex",
                doc=(
                    "Index column for `spatial_filter_cameras_cm_per_pixel` so that each epoch can have "
                    "multiple cameras."
                ),
                quantity="?",
            ),
            NWBDatasetSpec(
                name="spatial_filter_cameras_cm_per_pixel",
                neurodata_type_inc="VectorData",
                doc=(
                    "The cm/pixel values for each spatial filter camera used in this epoch, in the same order "
                    "as `spatial_filter_cameras`. Use this if the cm/pixel values change per epoch. Otherwise, "
                    "use the `meters_per_pixel` attribute of `CameraDevice`."
                ),
                dtype="float",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="ripple_filter_on",
                neurodata_type_inc="VectorData",
                doc=(
                    "Whether the ripple filter was on. Closed-loop stimulation based on whether a ripple was "
                    "detected - whether N tetrodes have their signal cross the standard deviation threshold. "
                    "If this column is not present, then the ripple filter was not used."
                ),
                dtype="bool",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="ripple_filter_lockout_period_in_samples",
                neurodata_type_inc="VectorData",
                doc=(
                    "If the ripple filter was used, lockout period in the number of samples. "
                    "Uses trodes time (samplecount)."
                ),
                dtype="int",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="ripple_filter_threshold_sd",
                neurodata_type_inc="VectorData",
                doc=(
                    "If the ripple filter was used, the threshold for detecting a ripple, in number of "
                    "standard deviations."
                ),
                dtype="float",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="ripple_filter_num_above_threshold",
                neurodata_type_inc="VectorData",
                doc=(
                    "If the ripple filter was used, the number of tetrodes that have their signal cross "
                    "the standard deviation threshold."
                ),
                dtype="int",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="speed_filter_on",
                neurodata_type_inc="VectorData",
                doc=(
                    "Whether the speed filter was on. Closed-loop stimulation based on whether the animal "
                    "is moving fast/slow enough. If this column is not present, then the speed filter was not used."
                ),
                dtype="bool",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="speed_filter_threshold_in_cm_per_s",
                neurodata_type_inc="VectorData",
                doc=("If the speed filter was used, the threshold for detecting a fast/slow animal, in cm/s."),
                dtype="float",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="speed_filter_on_above_threshold",
                neurodata_type_inc="VectorData",
                doc=("If the speed filter was used, True if active when speed above threshold."),
                dtype="bool",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="stimulus_signal",
                neurodata_type_inc="VectorData",
                doc=(
                    "Timeseries of the delivered stimulus. Can be continuous values or time of digital on/off events."
                ),
                dtype=NWBRefSpec(
                    target_type="TimeSeries",
                    reftype="object",
                ),
                quantity="?",
            ),
        ],
    )

    new_data_types = [
        shanks_electrode,
        shanks,
        probe,
        data_acq_device,
        camera_device,
        header_device,
        associated_files,
        nwb_electrode_group,
        frank_lab_optogenetic_epochs_table,
    ]

    # export the spec to yaml files in the spec folder
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "spec"))
    export_spec(ns_builder, new_data_types, output_dir)


if __name__ == "__main__":
    # usage: python create_extension_spec.py
    main()
