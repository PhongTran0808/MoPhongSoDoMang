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

async function triggerNormalTrafficAction() {
    const srcId = document.getElementById("select-src-device").value;
    const targetId = document.getElementById("select-target-device").value;
    const wazuhHost = document.getElementById("input-wazuh-ip").value.trim() || "172.16.175.145";

    const payload = {
        scenario_id: "normal_traffic",
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

    const statusBox = document.getElementById("scenario-status-log");
    if (statusBox) {
        statusBox.style.borderColor = "#10b981";
        statusBox.style.boxShadow = "0 0 12px rgba(16, 185, 129, 0.4)";
    }

    const interval = setInterval(async () => {
        const status = await API.getInjectorStatus();
        const statusBox = document.getElementById("scenario-status-log");

        if (statusBox) {
            if (status.is_running) {
                statusBox.style.color = "#4ade80";
                statusBox.innerHTML = `🚀 <b>[ĐANG BẮN LOG THỜI GIAN THỰC UDP 514]</b> Progress: <b>${status.current_step}/${status.total_steps}</b> (Đã gửi ${status.logs_sent} logs)<br><span style="color:#94a3b8; font-size:0.78rem;">Log Gần Nhất: ${status.last_log || "Đang tạo gói UDP..."}</span>`;
            } else {
                statusBox.style.color = "#38bdf8";
                statusBox.style.borderColor = "#1e293b";
                statusBox.style.boxShadow = "none";
                statusBox.innerHTML = `✅ <b>[HOÀN TẤT BẮN LOG]</b> ${status.status} | Tổng số log đã bắn: <b>${status.logs_sent}</b>.<br><span style="color:#a78bfa; font-size:0.78rem;">Log cuối: ${status.last_log || "None"}</span>`;
            }
        }

        if (!status.is_running) {
            isPollingInjector = false;
            clearInterval(interval);
        }
    }, 400);
}
