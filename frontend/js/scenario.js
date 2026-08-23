/**
 * Scenario Engine & Status Poller
 */

let isPollingInjector = false;

function populateScenarioDropdowns(devices) {
    const srcSel = document.getElementById("select-src-device");
    const targetSel = document.getElementById("select-target-device");
    if (!srcSel || !targetSel) return;

    srcSel.innerHTML = "";
    targetSel.innerHTML = "";

    (devices || []).forEach(d => {
        const opt1 = document.createElement("option");
        opt1.value = d.id;
        opt1.textContent = `${d.name} (${d.ip})`;
        srcSel.appendChild(opt1);

        const opt2 = document.createElement("option");
        opt2.value = d.id;
        opt2.textContent = `${d.name} (${d.ip})`;
        targetSel.appendChild(opt2);
    });

    // Default target to server if available
    const serverDev = devices.find(d => d.type === "server");
    if (serverDev) targetSel.value = serverDev.id;
}

async function loadScenariosList() {
    const scenarios = await API.getScenarios();
    const sel = document.getElementById("select-scenario");
    if (!sel) return;

    sel.innerHTML = "";
    scenarios.forEach(sc => {
        const opt = document.createElement("option");
        opt.value = sc.id;
        opt.textContent = `${sc.name} — ${sc.description.substring(0, 60)}...`;
        sel.appendChild(opt);
    });
}

async function triggerScenarioAction() {
    const scenarioId = document.getElementById("select-scenario").value;
    const srcId = document.getElementById("select-src-device").value;
    const targetId = document.getElementById("select-target-device").value;
    const wazuhHost = document.getElementById("input-wazuh-ip").value.trim() || "172.16.175.145";

    if (srcId === targetId) {
        alert("⚠️ Nguồn và Đích không nên là cùng 1 thiết bị!");
        return;
    }

    const payload = {
        scenario_id: scenarioId,
        source_device_id: srcId,
        target_device_id: targetId,
        wazuh_host: wazuhHost,
        wazuh_syslog_port: 514,
        burst_count: 30
    };

    const res = await API.runScenario(payload);
    if (res.status === "success") {
        startStatusPolling();
    } else {
        alert(`❌ Error: ${res.detail || res.message}`);
    }
}

async function stopScenarioAction() {
    await API.stopScenario();
}

function startStatusPolling() {
    if (isPollingInjector) return;
    isPollingInjector = true;

    const interval = setInterval(async () => {
        const status = await API.getInjectorStatus();
        const statusBox = document.getElementById("scenario-status-log");

        if (statusBox) {
            statusBox.textContent = `[${status.status}] Step: ${status.current_step}/${status.total_steps} | Last: ${status.last_log || "None"}`;
        }

        if (!status.is_running) {
            isPollingInjector = false;
            clearInterval(interval);
        }
    }, 500);
}
