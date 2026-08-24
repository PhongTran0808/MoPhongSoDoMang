/**
 * Property Panels & Toolbar Actions Controller
 */

function renderEmptyPropertyPanel() {
    const panel = document.getElementById("prop-panel-body");
    if (!panel) return;
    panel.innerHTML = `
        <div class="empty-prop">
            <i class="fa-solid fa-hand-pointer" style="font-size:2rem; color:#475569;"></i>
            <p>Nhấp vào thiết bị hoặc dây cáp nối trên sơ đồ để xem &amp; chỉnh sửa thông số.</p>
        </div>`;
}

function renderLinkPropertyPanel(link) {
    const panel = document.getElementById("prop-panel-body");
    if (!panel) return;

    const fromDev = (currentTopology.devices || []).find(d => d.id === link.from_id);
    const toDev = (currentTopology.devices || []).find(d => d.id === link.to_id);

    const fromName = fromDev ? `${fromDev.name} (${fromDev.ip})` : link.from_id;
    const toName = toDev ? `${toDev.name} (${toDev.ip})` : link.to_id;

    panel.innerHTML = `
        <div class="panel-header" style="padding:0 0 0.6rem 0; margin-bottom:0.8rem; border-bottom:1px solid #1e293b; color:#a78bfa;">
            <i class="fa-solid fa-route"></i> Thông Số Đường Nối Mạng
        </div>

        <div class="form-group">
            <label>Nối Từ Thiết Bị (From)</label>
            <input type="text" value="${fromName}" class="form-control" disabled readonly>
        </div>

        <div class="form-group">
            <label>Nối Đến Thiết Bị (To)</label>
            <input type="text" value="${toName}" class="form-control" disabled readonly>
        </div>

        <div class="form-group">
            <label>Tên Đường Nối / Nhãn (Label)</label>
            <input type="text" id="prop-link-label" value="${link.label || ''}" class="form-control">
        </div>

        <div class="form-group">
            <label>Băng Thông (Bandwidth)</label>
            <select id="prop-link-bandwidth" class="form-control">
                <option value="100M" ${link.bandwidth === '100M' ? 'selected' : ''}>⚡ 100 Mbps WAN</option>
                <option value="1G" ${link.bandwidth === '1G' ? 'selected' : ''}>🚀 1 Gbps LAN / Uplink</option>
                <option value="10G" ${link.bandwidth === '10G' ? 'selected' : ''}>🔥 10 Gbps Fiber / DCI</option>
                <option value="40G" ${link.bandwidth === '40G' ? 'selected' : ''}>💥 40 Gbps Fabric / Spine</option>
            </select>
        </div>

        <div class="form-group">
            <label>Kiểu Đường Nối (Link Style)</label>
            <select id="prop-link-type" class="form-control">
                <option value="ethernet" ${link.link_type === 'ethernet' ? 'selected' : ''}>────── Nét Liền (Ethernet / Fiber)</option>
                <option value="vpn" ${link.link_type === 'vpn' ? 'selected' : ''}>- - - - - Nét Đứt (VPN / SD-WAN Tunnel)</option>
            </select>
        </div>

        <div class="form-group">
            <label>Màu Sắc Đường Nối (Line Color)</label>
            <select id="prop-link-color" class="form-control">
                <option value="#38bdf8" ${link.color === '#38bdf8' || !link.color ? 'selected' : ''}>🩵 Xanh Cyan Neon (#38bdf8)</option>
                <option value="#a78bfa" ${link.color === '#a78bfa' ? 'selected' : ''}>💜 Tím VPN (#a78bfa)</option>
                <option value="#22c55e" ${link.color === '#22c55e' ? 'selected' : ''}>💚 Xanh Lá LAN (#22c55e)</option>
                <option value="#f97316" ${link.color === '#f97316' ? 'selected' : ''}>🧡 Cam Cảnh Báo (#f97316)</option>
                <option value="#ef4444" ${link.color === '#ef4444' ? 'selected' : ''}>❤️ Đỏ High Risk (#ef4444)</option>
                <option value="#eab308" ${link.color === '#eab308' ? 'selected' : ''}>💛 Vàng Sync (#eab308)</option>
            </select>
        </div>

        <div style="display:flex; gap:0.5rem; margin-top:1rem;">
            <button class="btn-action btn-primary" style="flex:1;" onclick="saveCurrentLink('${link.id}')">
                <i class="fa-solid fa-floppy-disk"></i> Lưu Thay Đổi
            </button>
            <button class="btn-action" style="background:#ef4444; border-color:#dc2626; color:#fff;" onclick="deleteCurrentLink('${link.id}')">
                <i class="fa-solid fa-trash"></i> Xóa Dây
            </button>
        </div>
    `;
}

async function saveCurrentLink(linkId) {
    const link = (currentTopology.links || []).find(l => l.id === linkId);
    if (!link) return;

    link.label = document.getElementById("prop-link-label").value.trim();
    link.bandwidth = document.getElementById("prop-link-bandwidth").value;
    link.link_type = document.getElementById("prop-link-type").value;
    link.color = document.getElementById("prop-link-color").value;

    await API.saveTopology(currentTopology);
    await initCanvas();
    alert(`✅ Đã lưu thay đổi đường nối: ${link.label}`);
}

async function deleteCurrentLink(linkId) {
    if (!confirm("Bạn có chắc chắn muốn xóa đường nối này?")) return;

    currentTopology.links = (currentTopology.links || []).filter(l => l.id !== linkId);
    await API.saveTopology(currentTopology);
    selectedLinkId = null;
    await initCanvas();
    renderEmptyPropertyPanel();
}

async function renderDevicePropertyPanel(dev) {
    const panel = document.getElementById("prop-panel-body");
    if (!panel) return;

    const globalWazuhIp = (document.getElementById("input-wazuh-ip") || {}).value || "172.16.175.145";
    const globalWazuhPass = (document.getElementById("input-wazuh-pass") || {}).value || "";

    const osStr = (dev.os || "").toLowerCase();
    const isWindows = osStr.includes("win") || dev.type === "pc";
    const isLinux = osStr.includes("ubuntu") || osStr.includes("linux") || osStr.includes("rhel") || osStr.includes("redhat") || dev.type === "server";
    
    let osBadgeHtml = "";
    if (isWindows) {
        osBadgeHtml = `
            <div style="margin-top:0.8rem; background:rgba(59,130,246,0.1); border:1px solid #3b82f6; border-radius:6px; padding:0.6rem; font-size:0.75rem; color:#60a5fa;">
                <div style="font-weight:700; margin-bottom:0.3rem;"><i class="fa-brands fa-windows"></i> HỆ ĐIỀU HÀNH: WINDOWS (${dev.os || 'Windows 11 / Server'})</div>
                <div>Khuyên dùng gói: <strong>MSI 32/64-bit</strong></div>
                <div style="margin-top:0.4rem; background:#020617; padding:0.4rem; border-radius:4px; font-family:monospace; font-size:0.7rem; color:#a78bfa; word-break:break-all;">
                    WAZUH_MANAGER='${globalWazuhIp}' WAZUH_AGENT_NAME='${dev.name}' msiexec /i wazuh-agent.msi /q
                </div>
            </div>`;
    } else if (isLinux) {
        osBadgeHtml = `
            <div style="margin-top:0.8rem; background:rgba(34,197,94,0.1); border:1px solid #22c55e; border-radius:6px; padding:0.6rem; font-size:0.75rem; color:#4ade80;">
                <div style="font-weight:700; margin-bottom:0.3rem;"><i class="fa-brands fa-linux"></i> HỆ ĐIỀU HÀNH: LINUX (${dev.os || 'Ubuntu / RHEL / Linux'})</div>
                <div>Khuyên dùng gói: <strong>RPM / DEB amd64</strong></div>
                <div style="margin-top:0.4rem; background:#020617; padding:0.4rem; border-radius:4px; font-family:monospace; font-size:0.7rem; color:#38bdf8; word-break:break-all;">
                    WAZUH_MANAGER='${globalWazuhIp}' WAZUH_AGENT_NAME='${dev.name}' rpm -ihv wazuh-agent-4.14.7.rpm
                </div>
            </div>`;
    } else {
        osBadgeHtml = `
            <div style="margin-top:0.8rem; background:rgba(234,179,8,0.1); border:1px solid #eab308; border-radius:6px; padding:0.6rem; font-size:0.75rem; color:#fde047;">
                <div style="font-weight:700;"><i class="fa-solid fa-microchip"></i> HỆ ĐIỀU HÀNH: APPLIANCE / SYSTEM (${dev.os || 'Enterprise OS'})</div>
            </div>`;
    }

    panel.innerHTML = `
        <div class="form-group">
            <label>ID Thiết Bị (Read-only)</label>
            <input type="text" value="${dev.id}" class="form-control" disabled readonly>
        </div>

        <div class="form-group">
            <label>Tên Thiết Bị (Name)</label>
            <input type="text" id="prop-dev-name" value="${dev.name}" class="form-control">
        </div>

        <div class="form-group">
            <label>Địa Chỉ IP (Primary IP)</label>
            <input type="text" id="prop-dev-ip" value="${dev.ip}" class="form-control">
        </div>

        <div class="form-group">
            <label>Loại Thiết Bị (Type)</label>
            <select id="prop-dev-type" class="form-control">
                <option value="firewall" ${dev.type === 'firewall' ? 'selected' : ''}>🔥 Firewall (FortiGate)</option>
                <option value="router" ${dev.type === 'router' ? 'selected' : ''}>🌐 Router (Cisco)</option>
                <option value="switch" ${dev.type === 'switch' ? 'selected' : ''}>🔀 Switch</option>
                <option value="server" ${dev.type === 'server' ? 'selected' : ''}>🖥️ Server (Linux/Windows)</option>
                <option value="pc" ${dev.type === 'pc' ? 'selected' : ''}>💻 User PC / Endpoint</option>
                <option value="cloud" ${dev.type === 'cloud' ? 'selected' : ''}>☁️ Cloud / Internet (WAN)</option>
                <option value="wazuh" ${dev.type === 'wazuh' || dev.type === 'siem' ? 'selected' : ''}>🛡️ Wazuh SIEM Server (172.16.175.145)</option>
            </select>
        </div>

        <div class="form-group">
            <label>Hệ Điều Hành / Firmware</label>
            <input type="text" id="prop-dev-os" value="${dev.os || ''}" class="form-control">
        </div>

        ${osBadgeHtml}

        <div class="form-group" style="margin-top:0.8rem;">
            <label>Mức Độ Quan Trọng (Asset Criticality 1-10)</label>
            <input type="number" id="prop-dev-crit" value="${dev.criticality}" min="1" max="10" class="form-control">
        </div>

        <!-- DOCKER CONTAINER CONTROLS FOR ALL NODES -->
        <div style="margin-top:1.2rem; padding:0.9rem; background:#0f172a; border:1px solid #1e293b; border-radius:8px;">
            <div style="font-weight:700; font-size:0.85rem; color:#38bdf8; margin-bottom:0.6rem; display:flex; align-items:center; justify-content:space-between;">
                <span><i class="fa-brands fa-docker"></i> 1. TRẠNG THÁI DOCKER OS</span>
                <span id="container-status-badge" style="font-size:0.75rem; font-weight:600; padding:2px 8px; border-radius:4px; background:#334155; color:#94a3b8;">
                    Đang kiểm tra...
                </span>
            </div>

            <div style="display:flex; flex-direction:column; gap:0.4rem; margin-bottom:0.8rem;" id="container-action-btns">
                <button class="btn-action btn-primary" id="btn-create-container" onclick="actionCreateContainer('${dev.name}', '${dev.ip}')" style="font-size:0.8rem; padding:0.4rem; background:#0284c7; border-color:#0369a1;">
                    <i class="fa-solid fa-cube"></i> ⚡ Khởi Tạo Docker (Clean Container)
                </button>
                <div style="display:flex; gap:0.4rem;">
                    <button class="btn-action" id="btn-toggle-container" onclick="actionToggleContainer('${dev.name}')" style="flex:1; font-size:0.8rem; padding:0.4rem; background:#3b82f6; border-color:#2563eb; color:#fff;">
                        <i class="fa-solid fa-power-off"></i> Bật / Tạm Dừng
                    </button>
                    <button class="btn-action" id="btn-remove-container" onclick="actionRemoveContainer('${dev.name}')" style="font-size:0.8rem; padding:0.4rem; background:#ef4444; border-color:#dc2626; color:#fff;">
                        <i class="fa-solid fa-trash"></i> Xóa
                    </button>
                </div>
            </div>

            <div style="border-top:1px dashed #334155; padding-top:0.6rem; margin-top:0.6rem;">
                <div style="font-weight:700; font-size:0.82rem; color:#f59e0b; margin-bottom:0.5rem; display:flex; justify-content:space-between; align-items:center;">
                    <span><i class="fa-solid fa-shield-halved"></i> 2. DEPLOY VÀO WAZUH SERVER</span>
                    <span id="deploy-status-badge" style="font-size:0.7rem; font-weight:600; padding:2px 6px; border-radius:4px; background:#475569; color:#cbd5e1;">
                        Chưa Deploy
                    </span>
                </div>

                <div class="form-group" style="margin-bottom:0.4rem;">
                    <label style="font-size:0.75rem; color:#94a3b8;"><i class="fa-solid fa-server"></i> IP Wazuh Server Target</label>
                    <input type="text" id="prop-container-wazuh-ip" value="${globalWazuhIp}" class="form-control" style="font-size:0.8rem; padding:0.3rem 0.5rem;" placeholder="192.168.1.234">
                </div>

                <div class="form-group" style="margin-bottom:0.6rem;">
                    <label style="font-size:0.75rem; color:#94a3b8;"><i class="fa-solid fa-key"></i> Mã / Pass Xác Thực Wazuh (nếu có)</label>
                    <input type="text" id="prop-container-wazuh-pass" value="${globalWazuhPass}" class="form-control" style="font-size:0.8rem; padding:0.3rem 0.5rem;" placeholder="Mã xác thực từ Wazuh UI">
                </div>

                <button class="btn-action" id="btn-deploy-agent" onclick="actionDeployAgent('${dev.name}', '${dev.ip}')" style="width:100%; font-size:0.82rem; padding:0.45rem; background:#16a34a; border-color:#15803d; color:#fff; font-weight:600;">
                    <i class="fa-solid fa-rocket"></i> 🚀 Deploy Agent Vào Wazuh Server
                </button>
            </div>
        </div>

        <div style="display:flex; gap:0.5rem; margin-top:1.2rem;">
            <button class="btn-action btn-primary" style="flex:1;" onclick="saveCurrentDevice('${dev.id}')">
                <i class="fa-solid fa-floppy-disk"></i> Lưu Thay Đổi
            </button>
            <button class="btn-action" style="background:#ef4444; border-color:#dc2626; color:#fff;" onclick="deleteCurrentDevice('${dev.id}')">
                <i class="fa-solid fa-trash"></i> Xóa
            </button>
        </div>
    `;

    refreshContainerBadge(dev.name);
}

async function refreshContainerBadge(deviceName) {
    const badge = document.getElementById("container-status-badge");
    const deployBadge = document.getElementById("deploy-status-badge");
    const btnToggle = document.getElementById("btn-toggle-container");
    const btnCreate = document.getElementById("btn-create-container");
    if (!badge) return;

    try {
        const res = await API.getContainerStatus(deviceName);
        if (res.status === "running") {
            badge.style.background = "rgba(34,197,94,0.2)";
            badge.style.color = "#22c55e";
            badge.innerHTML = `🟢 Running (OS Active)`;
            if (btnToggle) {
                btnToggle.innerHTML = `<i class="fa-solid fa-pause"></i> Tạm Dừng`;
                btnToggle.style.background = "#f59e0b";
                btnToggle.style.borderColor = "#d97706";
            }
            if (btnCreate) btnCreate.innerText = "🔄 Re-Create Clean Container";
        } else if (res.status === "stopped" || res.status === "paused") {
            badge.style.background = "rgba(239,68,68,0.2)";
            badge.style.color = "#ef4444";
            badge.innerHTML = `🔴 Stopped (Tạm dừng)`;
            if (btnToggle) {
                btnToggle.innerHTML = `<i class="fa-solid fa-play"></i> Bật Hoạt Động`;
                btnToggle.style.background = "#22c55e";
                btnToggle.style.borderColor = "#16a34a";
            }
            if (btnCreate) btnCreate.innerText = "🔄 Re-Create Clean Container";
        } else {
            badge.style.background = "#334155";
            badge.style.color = "#94a3b8";
            badge.innerHTML = `⚪ Chưa khởi tạo`;
            if (btnToggle) btnToggle.style.display = "none";
            if (btnCreate) btnCreate.innerText = "⚡ 1. Khởi Tạo Docker (Clean Container)";
        }

        if (deployBadge) {
            if (res.deployed) {
                deployBadge.style.background = "rgba(34,197,94,0.2)";
                deployBadge.style.color = "#22c55e";
                deployBadge.innerHTML = `✅ Registered Wazuh Server`;
            } else {
                deployBadge.style.background = "#475569";
                deployBadge.style.color = "#cbd5e1";
                deployBadge.innerHTML = `⏳ Chưa Deploy Agent`;
            }
        }
    } catch (e) {
        badge.style.background = "#334155";
        badge.style.color = "#94a3b8";
        badge.innerText = "Không rõ";
    }
}

async function actionCreateContainer(deviceName, deviceIp) {
    const badge = document.getElementById("container-status-badge");
    if (badge) {
        badge.style.background = "rgba(56,189,248,0.2)";
        badge.style.color = "#38bdf8";
        badge.innerText = "⏳ Đang tạo clean container...";
    }

    try {
        const res = await API.createContainer(deviceName, deviceIp);
        alert(res.message);
        await refreshContainerBadge(deviceName);
    } catch (e) {
        alert(`❌ Lỗi khởi tạo container: ${e.message || e}`);
        await refreshContainerBadge(deviceName);
    }
}

async function actionDeployAgent(deviceName, deviceIp) {
    const wazuhIpInput = document.getElementById("prop-container-wazuh-ip") || document.getElementById("input-wazuh-ip");
    const wazuhPassInput = document.getElementById("prop-container-wazuh-pass") || document.getElementById("input-wazuh-pass");
    const wazuhIp = wazuhIpInput ? wazuhIpInput.value.trim() : "192.168.1.234";
    const wazuhPass = wazuhPassInput ? wazuhPassInput.value.trim() : "";

    const deployBadge = document.getElementById("deploy-status-badge");
    if (deployBadge) {
        deployBadge.style.background = "rgba(245,158,11,0.2)";
        deployBadge.style.color = "#f59e0b";
        deployBadge.innerText = "🚀 Đang thực thi Deploy...";
    }

    try {
        const res = await API.deployAgent(deviceName, wazuhIp, deviceIp, wazuhPass);
        alert(res.message);
        await refreshContainerBadge(deviceName);
    } catch (e) {
        alert(`❌ Lỗi Deploy Agent: ${e.message || e}`);
        await refreshContainerBadge(deviceName);
    }
}

async function actionBatchCreateAllContainers() {
    const wazuhIpInput = document.getElementById("input-wazuh-ip");
    const wazuhPassInput = document.getElementById("input-wazuh-pass");
    const wazuhIp = wazuhIpInput ? wazuhIpInput.value.trim() : "172.16.175.145";
    const wazuhPass = wazuhPassInput ? wazuhPassInput.value.trim() : "";

    if (!confirm(`🚀 Bạn có chắc muốn Khởi Tạo Docker cho TẤT CẢ các Node trong sơ đồ?\n- IP Wazuh Server Target: ${wazuhIp}\n- Mã Xác Thực: ${wazuhPass || '(Không có)'}\n- 5 Node chính sẽ ở trạng thái BẬT, các node khác ở trạng thái TẠM DỪNG (0% RAM/CPU) để bạn bật khi cần.`)) return;

    try {
        let res;
        if (typeof API !== "undefined" && typeof API.batchCreateContainers === "function") {
            res = await API.batchCreateContainers(wazuhIp, wazuhPass);
        } else {
            // Fallback trực tiếp qua fetch nếu trình duyệt bị cache file api.js cũ
            const rawRes = await fetch("/api/container/batch-create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ wazuh_manager_ip: wazuhIp, enroll_pass: wazuhPass })
            });
            res = await rawRes.json();
        }
        alert(res.message);
        await initCanvas();
    } catch (e) {
        alert(`❌ Lỗi khởi tạo hàng loạt: ${e.message || e}`);
    }
}

async function actionToggleContainer(deviceName) {
    const statusRes = await API.getContainerStatus(deviceName);
    const nextAction = statusRes.status === "running" ? "stop" : "start";

    try {
        const res = await API.toggleContainer(deviceName, nextAction);
        alert(res.message);
        await refreshContainerBadge(deviceName);
    } catch (e) {
        alert(`❌ Lỗi thao tác container: ${e.message || e}`);
        await refreshContainerBadge(deviceName);
    }
}

async function actionRemoveContainer(deviceName) {
    if (!confirm(`Bạn có chắc muốn XÓA container của ${deviceName}?`)) return;

    try {
        const res = await API.toggleContainer(deviceName, "remove");
        alert(res.message);
        await refreshContainerBadge(deviceName);
    } catch (e) {
        alert(`❌ Lỗi xóa container: ${e.message || e}`);
        await refreshContainerBadge(deviceName);
    }
}

async function saveCurrentDevice(devId) {
    const dev = currentTopology.devices.find(d => d.id === devId);
    if (!dev) return;

    dev.name = document.getElementById("prop-dev-name").value.trim();
    dev.ip = document.getElementById("prop-dev-ip").value.trim();
    dev.type = document.getElementById("prop-dev-type").value;
    dev.os = document.getElementById("prop-dev-os").value.trim();
    dev.criticality = parseInt(document.getElementById("prop-dev-crit").value) || 5;

    await API.addDevice(dev);
    await initCanvas();
    alert(`✅ Đã lưu thông tin thiết bị ${dev.name} (${dev.ip})`);
}

async function deleteCurrentDevice(devId) {
    if (!confirm("Bạn có chắc chắn muốn xóa thiết bị này khỏi sơ đồ?")) return;

    await API.deleteDevice(devId);
    selectedDeviceId = null;
    await initCanvas();
    renderEmptyPropertyPanel();
}

async function exportToAgentWazuhAction() {
    const res = await API.exportToAgentWazuh();
    if (res.status === "success") {
        alert(`🎉 1-CLICK EXPORT THÀNH CÔNG!\n\nĐã đồng bộ ${res.count} thiết bị từ WazuhSim sang config/known_devices.json của AgentWazuh.\nAgentWazuh AI sẽ nhận diện đúng IP & Risk Score!`);
    } else {
        alert(`❌ Lỗi Export: ${res.message}`);
    }
}

function openConnectModal() {
    const modal = document.getElementById("connect-modal");
    const fromSel = document.getElementById("modal-conn-from");
    const toSel = document.getElementById("modal-conn-to");
    if (!modal || !fromSel || !toSel) return;

    fromSel.innerHTML = "";
    toSel.innerHTML = "";

    (currentTopology.devices || []).forEach(d => {
        const opt1 = document.createElement("option");
        opt1.value = d.id;
        opt1.textContent = `${d.name} (${d.ip})`;
        fromSel.appendChild(opt1);

        const opt2 = document.createElement("option");
        opt2.value = d.id;
        opt2.textContent = `${d.name} (${d.ip})`;
        toSel.appendChild(opt2);
    });

    if (currentTopology.devices.length > 1) {
        toSel.selectedIndex = 1;
    }

    modal.style.display = "flex";
}

function closeConnectModal() {
    const modal = document.getElementById("connect-modal");
    if (modal) modal.style.display = "none";
}

async function submitConnectModal() {
    const fromId = document.getElementById("modal-conn-from").value;
    const toId = document.getElementById("modal-conn-to").value;
    const label = document.getElementById("modal-conn-label").value.trim() || "1Gbps LAN Link";

    if (fromId === toId) {
        alert("⚠️ Không thể nối dây từ 1 thiết bị vào chính nó!");
        return;
    }

    const newLinkId = "link_" + Math.random().toString(36).substr(2, 6);
    const newLink = {
        id: newLinkId,
        from_id: fromId,
        to_id: toId,
        label: label,
        bandwidth: "1G",
        link_type: "ethernet"
    };

    currentTopology.links.push(newLink);
    await API.saveTopology(currentTopology);
    closeConnectModal();
    await initCanvas();
}
