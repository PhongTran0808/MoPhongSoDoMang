/**
 * WazuhSim Canvas Controller using official network-automation/networking-icons
 */

const DEVICE_ICONS = {
    "firewall":  "/static/assets/icons/firewall.svg",
    "router":    "/static/assets/icons/router.svg",
    "switch":    "/static/assets/icons/switch.svg",
    "server":    "/static/assets/icons/server.svg",
    "siem":      "/static/assets/icons/siem.svg",
    "pc":        "/static/assets/icons/pc.svg",
    "endpoint":  "/static/assets/icons/pc.svg",
    "cloud":     "/static/assets/icons/cloud.svg",
    "internet":  "/static/assets/icons/internet.svg",
    "unknown":   "/static/assets/icons/unknown.svg"
};

const BORDER_COLORS = {
    "firewall":  "#f97316",
    "router":    "#38bdf8",
    "switch":    "#a78bfa",
    "server":    "#34d399",
    "pc":        "#60a5fa",
    "endpoint":  "#60a5fa",
    "cloud":     "#38bdf8",
    "internet":  "#38bdf8",
    "unknown":   "#94a3b8"
};

let network = null;
let nodesDataSet = null;
let edgesDataSet = null;
let currentTopology = { devices: [], links: [] };
let selectedDeviceId = null;

async function initCanvas() {
    const container = document.getElementById("canvas-pane");
    if (!container) return;

    currentTopology = await API.getTopology();
    renderNetwork(container, currentTopology);
    populateScenarioDropdowns(currentTopology.devices);
}

function renderNetwork(container, topo) {
    const nodes = (topo.devices || []).map(dev => {
        const typeKey = (dev.type || "unknown").toLowerCase();
        const iconSrc = DEVICE_ICONS[typeKey] || DEVICE_ICONS["unknown"];
        const borderColor = BORDER_COLORS[typeKey] || BORDER_COLORS["unknown"];

        const portsStr = (dev.open_ports || [22, 80, 443]).join(",");
        const osStr = dev.os || "Linux";

        // Multi-line detailed label displayed below the icon image
        const label = `${dev.name}\nIP: ${dev.ip}\nPorts: ${portsStr} | OS: ${osStr}`;

        return {
            id: dev.id,
            label: label,
            shape: "image",
            image: iconSrc,
            size: 48,
            borderWidth: 2,
            borderWidthSelected: 4,
            color: {
                border: borderColor,
                background: "#0f172a",
                highlight: { border: "#f43f5e", background: "#1e293b" }
            },
            font: {
                color: "#f8fafc",
                face: "Inter, sans-serif",
                size: 11,
                strokeWidth: 4,
                strokeColor: "#020617"
            },
            shadow: { enabled: true, color: borderColor, size: 14 },
            x: dev.x,
            y: dev.y,
            _raw: dev
        };
    });

    const edges = (topo.links || []).map(link => {
        const isVpn = link.link_type === "vpn";
        return {
            id: link.id,
            from: link.from_id,
            to: link.to_id,
            label: link.label || link.bandwidth || "1G Link",
            color: { color: isVpn ? "#a78bfa" : "#38bdf8", highlight: "#f43f5e" },
            dashes: isVpn,
            width: isVpn ? 2.5 : 2,
            smooth: isVpn ? { type: "curvedCW", roundness: 0.15 } : { type: "continuous" },
            arrows: { to: { enabled: false } },
            font: { color: isVpn ? "#a78bfa" : "#38bdf8", face: "Inter, sans-serif", size: 10, align: "middle", strokeWidth: 3, strokeColor: "#020617" }
        };
    });

    nodesDataSet = new vis.DataSet(nodes);
    edgesDataSet = new vis.DataSet(edges);

    const options = {
        nodes: { shadow: true },
        edges: { shadow: true, smooth: false },
        physics: {
            enabled: false
        },
        interaction: {
            hover: true,
            dragNodes: true,
            zoomView: true,
            multiselect: true
        },
        manipulation: {
            enabled: true,
            initiallyActive: true,
            addNode: false,
            addEdge: function(edgeData, callback) {
                if (edgeData.from && edgeData.to && edgeData.from !== edgeData.to) {
                    const newLinkId = "link_" + Math.random().toString(36).substr(2, 6);
                    edgeData.id = newLinkId;
                    edgeData.label = "1Gbps Link";
                    edgeData.color = { color: "#38bdf8", highlight: "#f43f5e" };
                    edgeData.width = 2.5;

                    callback(edgeData);

                    const newLink = {
                        id: newLinkId,
                        from_id: edgeData.from,
                        to_id: edgeData.to,
                        label: "1Gbps Link",
                        bandwidth: "1G",
                        link_type: "ethernet"
                    };
                    currentTopology.links.push(newLink);
                    API.saveTopology(currentTopology);
                } else {
                    callback(null);
                }
            },
            deleteEdge: function(edgeData, callback) {
                const linkId = edgeData.edges[0];
                currentTopology.links = (currentTopology.links || []).filter(l => l.id !== linkId);
                API.saveTopology(currentTopology);
                callback(edgeData);
            }
        }
    };

    container.innerHTML = "";
    network = new vis.Network(container, { nodes: nodesDataSet, edges: edgesDataSet }, options);

    // Click handler -> open property panel for node or edge
    network.on("click", params => {
        if (params.nodes.length > 0) {
            selectedDeviceId = params.nodes[0];
            selectedLinkId = null;
            const dev = currentTopology.devices.find(d => d.id === selectedDeviceId);
            if (dev) renderDevicePropertyPanel(dev);
        } else if (params.edges.length > 0) {
            selectedLinkId = params.edges[0];
            selectedDeviceId = null;
            const link = (currentTopology.links || []).find(l => l.id === selectedLinkId);
            if (link) renderLinkPropertyPanel(link);
        } else {
            selectedDeviceId = null;
            selectedLinkId = null;
            renderEmptyPropertyPanel();
        }
    });

    // Drag end handler -> update x, y coordinates
    network.on("dragEnd", params => {
        if (params.nodes.length > 0) {
            const positions = network.getPositions(params.nodes);
            Object.keys(positions).forEach(id => {
                const dev = currentTopology.devices.find(d => d.id === id);
                if (dev) {
                    dev.x = positions[id].x;
                    dev.y = positions[id].y;
                }
            });
            API.saveTopology(currentTopology);
        }
    });

    // Automatically center & fit view
    setTimeout(() => {
        if (network) {
            network.redraw();
            network.fit({ animation: { duration: 300, easingFunction: "easeInOutQuad" } });
        }
    }, 150);
}

async function addNewDevice(type) {
    const id = "dev_" + Math.random().toString(36).substr(2, 6);
    const count = currentTopology.devices.length + 1;
    const subnetIp = `172.16.175.${200 + count}`;

    const newDev = {
        id: id,
        name: `${type.toUpperCase()}-${count}`,
        ip: subnetIp,
        type: type,
        os: type === "pc" ? "Windows 11" : type === "firewall" ? "FortiOS 7.2" : "Linux",
        criticality: type === "firewall" ? 9 : 5,
        syslog_format: "auto",
        x: (Math.random() - 0.5) * 250,
        y: (Math.random() - 0.5) * 250,
        verified: true,
        open_ports: [22, 80, 443]
    };

    currentTopology.devices.push(newDev);
    await API.addDevice(newDev);
    await initCanvas();
    renderDevicePropertyPanel(newDev);
}
