import numpy as np
from pynwb import NWBHDF5IO
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.base import mock_TimeSeries
from pynwb.device import DeviceModel
from unittest import TestCase

from ndx_ophys_devices import (
    ViralVector,
    ViralVectorInjection,
    Effector,
    ExcitationSourceModel,
    ExcitationSource,
    OpticalFiberModel,
    OpticalFiber,
    FiberInsertion,
)
from ndx_optogenetics import (
    OptogeneticSitesTable,
    OptogeneticViruses,
    OptogeneticVirusInjections,
    OptogeneticEffectors,
    OptogeneticExperimentMetadata,
)

from ndx_franklab_novela import FrankLabOptogeneticEpochsTable, CameraDevice


class TestFrankLabOptogeneticsEpochsTable(TestCase):

    def test_roundtrip(self):
        nwbfile = mock_NWBFile()

        stimulus = mock_TimeSeries()
        nwbfile.add_stimulus(stimulus)

        camera_model = DeviceModel(name="ndx2000", manufacturer="sony", model_number="ndx2000")
        nwbfile.add_device_model(camera_model)

        camera1 = CameraDevice(
            name="overhead_run_camera 1",
            description="Camera used for tracking running",
            meters_per_pixel=0.20,
            camera_name="test name",
            model=camera_model,
            lens="500dpt",
            frame_rate=30.0,
        )
        nwbfile.add_device(camera1)

        camera2 = CameraDevice(
            name="overhead_run_camera 2",
            description="Camera used for tracking running",
            meters_per_pixel=0.20,
            camera_name="test name",
            model=camera_model,
            lens="500dpt",
            frame_rate=30.0,
        )
        nwbfile.add_device(camera2)

        # Create and add excitation source devices
        excitation_source_model = ExcitationSourceModel(
            name="Omicron LuxX+ 488-100 Model",
            description="Laser for optogenetic stimulation.",
            manufacturer="Omicron",
            source_type="laser",
            excitation_mode="one-photon",
            wavelength_range_in_nm=[488.0, 488.0],
        )
        excitation_source = ExcitationSource(
            name="Omicron LuxX+ 488-100",
            model=excitation_source_model,
            power_in_W=0.077,
            intensity_in_W_per_m2=1.0e10,
        )
        nwbfile.add_device_model(excitation_source_model)
        nwbfile.add_device(excitation_source)

        # Create and add optical fiber devices
        optical_fiber_model = OpticalFiberModel(
            name="Lambda Model",
            description="Lambda fiber (tapered fiber) from Optogenix.",
            model_number="lambda_b5",
            manufacturer="Optogenix",
            numerical_aperture=0.39,
            core_diameter_in_um=200.0,
            active_length_in_mm=2.0,
            ferrule_name="cFCF - ∅2.5mm Ceramic Ferrule",
            ferrule_diameter_in_mm=2.5,
        )
        fiber_insertion = FiberInsertion(
            name="fiber_insertion",
            depth_in_mm=2.0,
            insertion_position_ap_in_mm=-1.5,
            insertion_position_ml_in_mm=3.2,
            insertion_position_dv_in_mm=-5.8,
            position_reference="Bregma at the cortical surface",
            hemisphere="right",
            insertion_angle_pitch_in_deg=0.0,
        )
        optical_fiber = OpticalFiber(
            name="Lambda",
            description="Lambda fiber implanted into right GPe.",
            serial_number="123456",
            model=optical_fiber_model,
            fiber_insertion=fiber_insertion,
        )
        nwbfile.add_device_model(optical_fiber_model)
        nwbfile.add_device(optical_fiber)

        # Create virus and injection metadata
        virus = ViralVector(
            name="AAV-EF1a-DIO-hChR2(H134R)-EYFP",
            construct_name="AAV-EF1a-DIO-hChR2(H134R)-EYFP",
            description="Excitatory optogenetic construct for ChR2-EYFP expression",
            manufacturer="UNC Vector Core",
            titer_in_vg_per_ml=1.0e12,
        )
        optogenetic_viruses = OptogeneticViruses(viral_vectors=[virus])

        virus_injection = ViralVectorInjection(
            name="AAV-EF1a-DIO-hChR2(H134R)-EYFP Injection",
            description="AAV-EF1a-DIO-hChR2(H134R)-EYFP injection into GPe.",
            hemisphere="right",
            location="GPe",
            ap_in_mm=-1.5,
            ml_in_mm=3.2,
            dv_in_mm=-6.0,
            roll_in_deg=0.0,
            pitch_in_deg=0.0,
            yaw_in_deg=0.0,
            reference="Bregma at the cortical surface",
            viral_vector=virus,
            volume_in_uL=0.45,
            injection_date="1970-01-01T00:00:00+00:00",
        )
        optogenetic_virus_injections = OptogeneticVirusInjections(viral_vector_injections=[virus_injection])

        effector = Effector(
            name="effector",
            description="Excitatory opsin",
            label="hChR2-EYFP",
            viral_vector_injection=virus_injection,
        )
        optogenetic_effectors = OptogeneticEffectors(effectors=[effector])

        # Create OptogeneticSitesTable
        optogenetic_sites_table = OptogeneticSitesTable(
            description="Information about the optogenetic stimulation sites."
        )
        optogenetic_sites_table.add_row(
            excitation_source=excitation_source,
            optical_fiber=optical_fiber,
            effector=effector,
        )

        # Create experiment metadata container
        optogenetic_experiment_metadata = OptogeneticExperimentMetadata(
            optogenetic_sites_table=optogenetic_sites_table,
            optogenetic_viruses=optogenetic_viruses,
            optogenetic_virus_injections=optogenetic_virus_injections,
            optogenetic_effectors=optogenetic_effectors,
            stimulation_software="FSGUI 2.0",
        )
        nwbfile.add_lab_meta_data(optogenetic_experiment_metadata)

        opto_epochs = FrankLabOptogeneticEpochsTable(
            name="optogenetic_epochs",
            description="Metadata about the optogenetic stimulation parameters that change per epoch.",
            target_tables={"optogenetic_sites": optogenetic_sites_table},
        )

        # test add one epoch
        opto_epochs.add_row(
            start_time=0.0,
            stop_time=100.0,
            stimulation_on=True,
            power_in_mW=100.0,
            pulse_length_in_ms=40.0,
            period_in_ms=250.0,
            number_pulses_per_pulse_train=100,
            number_trains=1,
            intertrain_interval_in_ms=0.0,
            epoch_name="20220911_Wallie_01_sleep",
            epoch_number=1,
            convenience_code="a1",
            epoch_type="sleep",
            theta_filter_on=True,
            theta_filter_lockout_period_in_samples=10,
            theta_filter_phase_in_deg=180.0,
            theta_filter_reference_ntrode=1,
            spatial_filter_on=True,
            spatial_filter_lockout_period_in_samples=10,
            # below is an example of a single rectangular spatial filter region defined by the pixel coordinates of the
            # four corners
            spatial_filter_region_node_coordinates_in_pixels=(((260, 920), (260, 800), (800, 1050), (800, 920)),),
            spatial_filter_cameras=[camera1, camera2],
            spatial_filter_cameras_cm_per_pixel=[0.3, 0.18],
            ripple_filter_on=True,
            ripple_filter_lockout_period_in_samples=10,
            ripple_filter_threshold_sd=5.0,
            ripple_filter_num_above_threshold=4,
            speed_filter_on=True,
            speed_filter_threshold_in_cm_per_s=10.0,
            speed_filter_on_above_threshold=True,
            stimulus_signal=stimulus,
            wavelength_in_nm=450.0,
            optogenetic_sites=[0],
        )
        nwbfile.add_time_intervals(opto_epochs)

        # write the NWBFile to disk
        path = "test_optogenetics.nwb"
        with NWBHDF5IO(path, mode="w") as io:
            io.write(nwbfile)

        # read the NWBFile from disk
        with NWBHDF5IO(path, mode="r") as io:
            read_nwbfile = io.read()

            read_camera1 = read_nwbfile.devices["overhead_run_camera 1"]
            read_camera2 = read_nwbfile.devices["overhead_run_camera 2"]

            read_epochs = read_nwbfile.intervals["optogenetic_epochs"]
            assert read_epochs[0, "start_time"] == 0.0
            assert read_epochs[0, "stop_time"] == 100.0
            assert read_epochs[0, "stimulation_on"]
            assert read_epochs[0, "power_in_mW"] == 100.0
            assert read_epochs[0, "pulse_length_in_ms"] == 40.0
            assert read_epochs[0, "period_in_ms"] == 250.0
            assert read_epochs[0, "number_pulses_per_pulse_train"] == 100
            assert read_epochs[0, "number_trains"] == 1
            assert read_epochs[0, "intertrain_interval_in_ms"] == 0.0
            assert read_epochs[0, "epoch_name"] == "20220911_Wallie_01_sleep"
            assert read_epochs[0, "epoch_number"] == 1
            assert read_epochs[0, "convenience_code"] == "a1"
            assert read_epochs[0, "epoch_type"] == "sleep"
            assert read_epochs[0, "theta_filter_on"]
            assert read_epochs[0, "theta_filter_lockout_period_in_samples"] == 10
            assert read_epochs[0, "theta_filter_phase_in_deg"] == 180.0
            assert read_epochs[0, "theta_filter_reference_ntrode"] == 1
            assert read_epochs[0, "spatial_filter_on"]
            assert read_epochs[0, "spatial_filter_lockout_period_in_samples"] == 10
            assert np.array_equal(
                read_epochs[0, "spatial_filter_region_node_coordinates_in_pixels"],
                np.array((((260, 920), (260, 800), (800, 1050), (800, 920)),)),
            )
            assert read_epochs[0, "spatial_filter_cameras"] == [read_camera1, read_camera2]
            assert all(read_epochs[0, "spatial_filter_cameras_cm_per_pixel"] == [0.3, 0.18])
            assert read_epochs[0, "ripple_filter_on"]
            assert read_epochs[0, "ripple_filter_lockout_period_in_samples"] == 10
            assert read_epochs[0, "ripple_filter_threshold_sd"] == 5.0
            assert read_epochs[0, "ripple_filter_num_above_threshold"] == 4
            assert read_epochs[0, "speed_filter_on"]
            assert read_epochs[0, "speed_filter_threshold_in_cm_per_s"] == 10.0
            assert read_epochs[0, "speed_filter_on_above_threshold"]
            assert read_epochs[0, "stimulus_signal"].object_id == stimulus.object_id
