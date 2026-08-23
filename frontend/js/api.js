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
    }
};
