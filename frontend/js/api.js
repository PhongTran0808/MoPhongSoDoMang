/**
 * WazuhSim API Client Helper
 */
const API = {
    async getTopology() {
        const res = await fetch("/api/topology");
        return await res.json();
    },

    async saveTopology(topo) {
        const res = await fetch("/api/topology/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(topo)
        });
        return await res.json();
    },

    async addDevice(device) {
        const res = await fetch("/api/topology/device", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(device)
        });
        return await res.json();
    },

    async deleteDevice(deviceId) {
        const res = await fetch(`/api/topology/device/${deviceId}`, {
            method: "DELETE"
        });
        return await res.json();
    },

    async exportToAgentWazuh() {
        const res = await fetch("/api/topology/export-agent-wazuh", {
            method: "POST"
        });
        return await res.json();
    },

    async getScenarios() {
        const res = await fetch("/api/injector/scenarios");
        return await res.json();
    },

    async getInjectorStatus() {
        const res = await fetch("/api/injector/status");
        return await res.json();
    },

    async runScenario(payload) {
        const res = await fetch("/api/injector/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        return await res.json();
    },

    async stopScenario() {
        const res = await fetch("/api/injector/stop", {
            method: "POST"
        });
        return await res.json();
    },

    async getContainerStatus(deviceName) {
        const res = await fetch(`/api/container/status/${encodeURIComponent(deviceName)}`);
        return await res.json();
    },

    async createContainer(deviceName, wazuhIp, deviceIp, enrollPass) {
        const res = await fetch("/api/container/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ device_name: deviceName, wazuh_manager_ip: wazuhIp, device_ip: deviceIp, enroll_pass: enrollPass })
        });
        return await res.json();
    },

    async batchCreateContainers(wazuhIp, enrollPass) {
        const res = await fetch("/api/container/batch-create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ wazuh_manager_ip: wazuhIp, enroll_pass: enrollPass })
        });
        return await res.json();
    },

    async toggleContainer(deviceName, action) {
        const res = await fetch("/api/container/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ device_name: deviceName, action: action })
        });
        return await res.json();
    }
};
