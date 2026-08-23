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

function renderDevicePropertyPanel(dev) {
    const panel = document.getElementById("prop-panel-body");
    if (!panel) return;

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
            </select>
        </div>

        <div class="form-group">
            <label>Hệ Điều Hành / Firmware</label>
            <input type="text" id="prop-dev-os" value="${dev.os || ''}" class="form-control">
        </div>

        <div class="form-group">
            <label>Mức Độ Quan Trọng (Asset Criticality 1-10)</label>
            <input type="number" id="prop-dev-crit" value="${dev.criticality}" min="1" max="10" class="form-control">
        </div>

        <div style="display:flex; gap:0.5rem; margin-top:1rem;">
            <button class="btn-action btn-primary" style="flex:1;" onclick="saveCurrentDevice('${dev.id}')">
                <i class="fa-solid fa-floppy-disk"></i> Lưu Thay Đổi
            </button>
            <button class="btn-action" style="background:#ef4444; border-color:#dc2626; color:#fff;" onclick="deleteCurrentDevice('${dev.id}')">
                <i class="fa-solid fa-trash"></i> Xóa
            </button>
        </div>
    `;
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
