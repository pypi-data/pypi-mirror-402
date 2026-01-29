import { create } from "zustand";

const createSDRDeviceSlice = (set) => ({
  sdrDeviceCount: 0,

  updateSDRStatus({ data }) {
    const numDevices = parseInt(data.Devices);
    set({ sdrDeviceCount: numDevices });
  },
});

const createGPSDeviceSlice = (set) => ({
  gpsConnected: false,
  gpsSolution: "Not communicating",
  gpsAccuracy: 0,

  updateGPSStatus({ data }) {
    const gpsConnected = data.GPS_connected === true;
    const gpsSolution = data.GPS_solution || "Unknown";

    // Validate GPS accuracy - Stratux may send "999999" for invalid
    let gpsAccuracy = parseFloat(data.GPS_position_accuracy);
    if (isNaN(gpsAccuracy) || gpsAccuracy >= 999999) {
      gpsAccuracy = 0;
    }

    set({
      gpsConnected,
      gpsSolution,
      gpsAccuracy,
    });
  },
});

const useDevicesStore = create((...a) => ({
  ...createSDRDeviceSlice(...a),
  ...createGPSDeviceSlice(...a),
}));

export default useDevicesStore;
