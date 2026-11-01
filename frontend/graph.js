// Renders the PayDrishti network graph with vis-network.
// Colours encode node kind; the persistent cores are large and red so the
// "funnel into reused infrastructure" pattern is visible at a glance.

const COLORS = {
  core:        { bg: "#e24b4a", border: "#a32d2d" },
  front:       { bg: "#ef9f27", border: "#ba7517" },
  victim:      { bg: "#9aa0ad", border: "#6b7280" },
  legit:       { bg: "#1d9e75", border: "#0f6e56" },
  legit_payer: { bg: "#6bbfa3", border: "#1d9e75" },
};

async function load() {
  const res = await fetch("/api/graph");
  const g = await res.json();

  const nodes = g.nodes.map((n) => {
    const c = COLORS[n.kind] || COLORS.victim;
    return {
      id: n.id,
      label: n.kind === "core" ? "CASH-OUT" : "",
      title: n.label + (n.score != null ? ` · risk ${n.score}` : ""),
      value: n.size,
      shape: "dot",
      color: { background: c.bg, border: c.border,
               highlight: { background: c.bg, border: "#fff" } },
      font: { color: "#fff", size: 13, face: "-apple-system, sans-serif" },
      borderWidth: n.kind === "core" ? 3 : 1,
    };
  });

  const edges = g.edges.map((e) => ({
    from: e.from, to: e.to,
    color: { color: e.kind === "funnel" ? "#e24b4a" : "#3a3f55",
             highlight: "#fff" },
    width: e.kind === "funnel" ? 2.5 : 0.7,
    arrows: { to: { enabled: true, scaleFactor: 0.45 } },
    smooth: { type: "continuous" },
  }));

  const data = {
    nodes: new vis.DataSet(nodes),
    edges: new vis.DataSet(edges),
  };

  const options = {
    physics: {
      solver: "forceAtlas2Based",
      forceAtlas2Based: { gravitationalConstant: -45, springLength: 90,
                          springConstant: 0.05, avoidOverlap: 0.6 },
      stabilization: { iterations: 220 },
    },
    interaction: { hover: true, tooltipDelay: 120, zoomView: true, dragView: true },
    nodes: { scaling: { min: 8, max: 40 } },
  };

  new vis.Network(document.getElementById("net"), data, options);
}

load().catch((e) => {
  document.getElementById("net").innerHTML =
    '<p style="color:#fff;padding:20px">Could not load graph: ' + e.message + "</p>";
});
