/**
 * WazuhSim API Client Helper — Defensive & Error-Handled
 */
const API = {
    async _fetch(url, options = {}) {
        try {
            const res = await fetch(url, options);
            if (!res.ok) {
                const text = await res.text();
                throw new Error(`HTTP ${res.status}: ${text}`);
            }
            return await res.json();
        } catch (err) {
            console.error(`[API Error] ${url}:`, err);
            return { status: "error", message: err.message };
        }
    },

    async getTopology() {
        return await this._fetch("/api/topology");
    },

    async saveTopology(topo) {
        return await this._fetch("/api/topology/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(topo)
        });
    },

    async addDevice(device) {
        return await this._fetch("/api/topology/device", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(device)
        });
    },

    async deleteDevice(deviceId) {
        return await this._fetch(`/api/topology/device/${deviceId}`, {
            method: "DELETE"
        });
    },

    async exportToAgentWazuh() {
        return await this._fetch("/api/topology/export-agent-wazuh", {
            method: "POST"
        });
    },

    async getScenarios() {
        return await this._fetch("/api/injector/scenarios");
    },

    async getInjectorStatus() {
        return await this._fetch("/api/injector/status");
    },

    async runScenario(payload) {
        return await this._fetch("/api/injector/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
    },

    async stopScenario() {
        return await this._fetch("/api/injector/stop", {
            method: "POST"
        });
    },

    async getContainerStatus(deviceName) {
        return await this._fetch(`/api/container/status/${encodeURIComponent(deviceName)}`);
    },

    async createContainer(deviceName, deviceIp) {
        return await this._fetch("/api/container/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ device_name: deviceName, device_ip: deviceIp })
        });
    },

    async deployAgent(deviceName, wazuhIp, deviceIp, enrollPass) {
        return await this._fetch("/api/container/deploy-agent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ device_name: deviceName, wazuh_manager_ip: wazuhIp, device_ip: deviceIp, enroll_pass: enrollPass })
        });
    },

    async toggleContainer(deviceName, action) {
        return await this._fetch("/api/container/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ device_name: deviceName, action: action })
        });
    }
};
